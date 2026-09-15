"""Comprehensive tests for Knowledge Overlay Federation Engine & REST API.

Verifies:
1. Three-Tier Cascading Precedence (Layer 2 > Layer 1 > Layer 0).
2. Fail-Closed Protection: Layer 0 (Base Canon) cannot be mutated at runtime (PermissionError / HTTP 403).
3. Non-Destructive Overlays: Layer 2 overrides Layer 0 without corrupting Layer 0.
4. Diff Generation: Accurate unified diff vs canonical baseline.
5. Reversion: Deleting Layer 2 overlay instantly restores Layer 0 baseline.
6. AI Preflight Linter: Sanitizes privacy leaks (/Users/..., credentials), checks Prose & USX standards.
7. Submission Packaging: Cryptographic bundle (manifest.json, diff.patch, provenance.json) in ~/Vault/dispatches/submissions/.
8. REST API Endpoints: /summary, /overlays, /resolve, /overlay, /revert, /preflight, /export-submission, /submissions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.federation_api import register_federation_routes, set_resolver
from app.services.knowledge_overlay import KnowledgeOverlayResolver


@pytest.fixture
def mock_fed_env(tmp_path: Path):
    canon_dir = tmp_path / "Public" / "global-knowledge"
    shared_dir = tmp_path / "Shared" / "knowledge"
    vault_dir = tmp_path / "Vault" / "knowledge"
    submissions_dir = tmp_path / "Vault" / "dispatches" / "submissions"

    canon_dir.mkdir(parents=True, exist_ok=True)
    shared_dir.mkdir(parents=True, exist_ok=True)
    vault_dir.mkdir(parents=True, exist_ok=True)
    submissions_dir.mkdir(parents=True, exist_ok=True)

    # Populate canonical base article
    canon_file = canon_dir / "survival" / "water-purification.md"
    canon_file.parent.mkdir(parents=True, exist_ok=True)
    canon_file.write_text(
        "# Water Purification\n\nBoil water for at least 1 minute.\nAlways filter sediment first.\n",
        encoding="utf-8",
    )

    resolver = KnowledgeOverlayResolver(
        canon_root=canon_dir,
        shared_knowledge_root=shared_dir,
        vault_knowledge_root=vault_dir,
        submissions_root=submissions_dir,
    )
    return {
        "resolver": resolver,
        "canon_dir": canon_dir,
        "shared_dir": shared_dir,
        "vault_dir": vault_dir,
        "submissions_dir": submissions_dir,
        "canon_file": canon_file,
    }


def test_cascading_resolution_precedence(mock_fed_env):
    """Test priority resolution: Layer 2 > Layer 1 > Layer 0."""
    res: KnowledgeOverlayResolver = mock_fed_env["resolver"]
    shared_dir: Path = mock_fed_env["shared_dir"]
    vault_dir: Path = mock_fed_env["vault_dir"]

    # 1. Initially only Layer 0 exists
    r0 = res.resolve("survival/water-purification.md")
    assert r0["found"] is True
    assert r0["effective_layer"] == 0
    assert r0["effective_layer_name"] == "canon"
    assert r0["is_overlaid"] is False
    assert "Boil water for at least 1 minute" in r0["content"]

    # 2. Add Layer 1 (Shared / Community) overlay
    shared_file = shared_dir / "survival" / "water-purification.md"
    shared_file.parent.mkdir(parents=True, exist_ok=True)
    shared_file.write_text(
        "# Water Purification (Community Guide)\n\nBoil water for 3 minutes at high altitude.\n",
        encoding="utf-8",
    )

    r1 = res.resolve("survival/water-purification.md")
    assert r1["found"] is True
    assert r1["effective_layer"] == 1
    assert r1["effective_layer_name"] == "community"
    assert r1["is_overlaid"] is True
    assert r1["has_diff"] is True
    assert "Community Guide" in r1["content"]

    # 3. Add Layer 2 (Personal Sovereign) overlay -> Layer 2 wins over Layer 1 and Layer 0
    vault_file = vault_dir / "survival" / "water-purification.md"
    vault_file.parent.mkdir(parents=True, exist_ok=True)
    vault_file.write_text(
        "# Water Purification (My Secret Recipe)\n\nBoil with solar still.\n",
        encoding="utf-8",
    )

    r2 = res.resolve("survival/water-purification.md")
    assert r2["found"] is True
    assert r2["effective_layer"] == 2
    assert r2["effective_layer_name"] == "personal"
    assert r2["is_overlaid"] is True
    assert "My Secret Recipe" in r2["content"]

    # 4. Request with prefer_canon=True to view untouched canonical baseline
    r_canon = res.resolve("survival/water-purification.md", prefer_canon=True)
    assert r_canon["effective_layer"] == 0
    assert "Boil water for at least 1 minute" in r_canon["content"]


def test_fail_closed_layer_0_immutability(mock_fed_env):
    """Writing to Layer 0 must raise PermissionError."""
    res: KnowledgeOverlayResolver = mock_fed_env["resolver"]
    with pytest.raises(PermissionError, match="Layer 0 .* is immutable"):
        res.create_or_update_overlay(
            "survival/water-purification.md",
            "Tampered content",
            layer=0,
        )


def test_revert_overlay_restores_canon(mock_fed_env):
    """Reverting Layer 2 overlay immediately restores Layer 0."""
    res: KnowledgeOverlayResolver = mock_fed_env["resolver"]

    # Create personal overlay
    res.create_or_update_overlay(
        "survival/water-purification.md",
        "# Personal note\nOnly use ceramic filters.\n",
        layer=2,
    )
    assert res.resolve("survival/water-purification.md")["effective_layer"] == 2

    # Revert
    reverted = res.revert_overlay("survival/water-purification.md", layer=2)
    assert reverted["effective_layer"] == 0
    assert reverted["is_overlaid"] is False
    assert "Boil water for at least 1 minute" in reverted["content"]


def test_preflight_linter_checks(mock_fed_env):
    """Preflight linter detects privacy leaks, secrets, and style issues."""
    res: KnowledgeOverlayResolver = mock_fed_env["resolver"]

    # 1. Text with privacy leak
    leaky_text = "See my notes at /Users/alice/Documents/secret.txt"
    p1 = res.lint_preflight(leaky_text)
    assert p1["passed"] is False
    assert any("Privacy leak detected" in err for err in p1["errors"])
    assert p1["checks"]["privacy_clean"] is False

    # 2. Text with API key
    key_text = "API Key: sk-1234567890abcdef1234567890"
    p2 = res.lint_preflight(key_text)
    assert p2["passed"] is False
    assert any("Security hazard" in err for err in p2["errors"])

    # 3. Clean compliant markdown
    clean_text = "# Water purification\n\nAlways filter sediment using clean cotton mesh.\n"
    p3 = res.lint_preflight(clean_text)
    assert p3["passed"] is True
    assert len(p3["errors"]) == 0


def test_export_submission_package(mock_fed_env):
    """Exporting a submission produces manifest.json, diff.patch, provenance.json in submissions_root."""
    res: KnowledgeOverlayResolver = mock_fed_env["resolver"]

    # Create an overlay first
    res.create_or_update_overlay(
        "survival/water-purification.md",
        "# Water Purification\n\nBoil water for at least 2 minutes (updated guidance).\nAlways filter sediment first.\n",
        layer=2,
    )

    pkg = res.export_submission_package(
        rel_path="survival/water-purification.md",
        author="alice-sovereign",
        notes="Updated boil time based on field altitude testing.",
        submission_type="canonical_patch",
    )

    assert pkg["submission_id"].startswith("sub-")
    pkg_dir = Path(pkg["package_path"])
    assert pkg_dir.is_dir()
    assert (pkg_dir / "manifest.json").is_file()
    assert (pkg_dir / "diff.patch").is_file()
    assert (pkg_dir / "provenance.json").is_file()

    manifest = json.loads((pkg_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["author"] == "alice-sovereign"
    assert manifest["rel_path"] == "survival/water-purification.md"
    assert manifest["preflight"]["passed"] is True

    diff_content = (pkg_dir / "diff.patch").read_text(encoding="utf-8")
    assert "+Boil water for at least 2 minutes (updated guidance)." in diff_content
    assert "-Boil water for at least 1 minute." in diff_content

    provenance = json.loads((pkg_dir / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["origin_layer"] == 2
    assert provenance["status"] == "pending_wizard_review"

    submissions = res.list_submissions()
    assert len(submissions) == 1
    assert submissions[0]["submission_id"] == pkg["submission_id"]


@pytest.mark.asyncio
async def test_federation_api_endpoints(mock_fed_env):
    """Test full REST API surface using TestClient."""
    set_resolver(mock_fed_env["resolver"])

    app = web.Application()
    register_federation_routes(app)

    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()

    try:
        # 1. GET /api/knowledge/federation/summary
        resp = await client.get("/api/knowledge/federation/summary")
        assert resp.status == 200
        summary = await resp.json()
        assert summary["status"] == "ready"
        assert summary["layers"]["layer_0_canon"]["articles_count"] >= 1

        # 2. GET /api/knowledge/federation/resolve
        resp = await client.get("/api/knowledge/federation/resolve?path=survival/water-purification.md")
        assert resp.status == 200
        resolved = await resp.json()
        assert resolved["effective_layer"] == 0
        assert resolved["is_overlaid"] is False

        # 3. POST /api/knowledge/federation/overlay (Layer 0 fail-closed test)
        resp = await client.post(
            "/api/knowledge/federation/overlay",
            json={"path": "survival/water-purification.md", "content": "tamper", "layer": 0},
        )
        assert resp.status == 403

        # 4. POST /api/knowledge/federation/overlay (Layer 2 success)
        resp = await client.post(
            "/api/knowledge/federation/overlay",
            json={
                "path": "survival/water-purification.md",
                "content": "# Water Purification\n\nBoil for 5 minutes.\n",
                "layer": 2,
            },
        )
        assert resp.status == 200
        saved = await resp.json()
        assert saved["success"] is True
        assert saved["overlay"]["effective_layer"] == 2
        assert saved["overlay"]["is_overlaid"] is True
        assert saved["overlay"]["has_diff"] is True

        # 5. GET /api/knowledge/federation/overlays
        resp = await client.get("/api/knowledge/federation/overlays")
        assert resp.status == 200
        overlays_data = await resp.json()
        assert overlays_data["count"] == 1
        assert overlays_data["overlays"][0]["rel_path"] == "survival/water-purification.md"

        # 6. POST /api/knowledge/federation/preflight
        resp = await client.post(
            "/api/knowledge/federation/preflight",
            json={"content": "Leaking /Users/bob/private.md", "path": "test.md"},
        )
        assert resp.status == 200
        preflight = await resp.json()
        assert preflight["passed"] is False

        # 7. POST /api/knowledge/federation/export-submission
        resp = await client.post(
            "/api/knowledge/federation/export-submission",
            json={
                "path": "survival/water-purification.md",
                "author": "tester",
                "notes": "Verified at elevation.",
            },
        )
        assert resp.status == 201
        exp = await resp.json()
        assert exp["success"] is True
        sub_id = exp["package"]["submission_id"]

        # 8. GET /api/knowledge/federation/submissions
        resp = await client.get("/api/knowledge/federation/submissions")
        assert resp.status == 200
        subs_data = await resp.json()
        assert subs_data["count"] == 1
        assert subs_data["submissions"][0]["submission_id"] == sub_id

        # 9. POST /api/knowledge/federation/revert
        resp = await client.post(
            "/api/knowledge/federation/revert",
            json={"path": "survival/water-purification.md", "layer": 2},
        )
        assert resp.status == 200
        reverted_data = await resp.json()
        assert reverted_data["resolved"]["effective_layer"] == 0
        assert reverted_data["resolved"]["is_overlaid"] is False

    finally:
        await client.close()
