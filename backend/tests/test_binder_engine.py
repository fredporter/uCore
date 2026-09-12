"""Tests for Durable Binder Engine & Anti-Drift Pipeline (Milestone P4).

Verifies:
1. Creation of all 7 canonical binder records.
2. Source attachment and citation tag assignment ([SRC-1]).
3. State machine transitions: draft_brief -> planned -> ready_for_review -> accepted -> published.
4. Concurrency conflict detection on draft updates (base_hash check).
5. Edition freezing and manifest creation.
6. Offline static publishing into ~/Public/editions/.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from app.flow import binder_engine
from app.flow.binder_engine import ConcurrencyConflictError
from app.services import intake_service


@pytest.fixture
def temp_environment(tmp_path, monkeypatch):
    vault = tmp_path / "Vault"
    binders = vault / "Binders"
    orig = vault / "Originals"
    docs = vault / "Documents"
    pub = tmp_path / "Public"

    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", binders)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    monkeypatch.setattr(intake_service, "VAULT_ROOT", vault)
    monkeypatch.setattr(intake_service, "ORIGINALS_ROOT", orig)
    monkeypatch.setattr(intake_service, "DOCUMENTS_ROOT", docs)

    return {"vault": vault, "binders": binders, "public": pub, "home": tmp_path}


def test_create_binder_canonical_records(temp_environment):
    binder = binder_engine.create_binder(
        binder_id="proj-alpha",
        title="Project Alpha System Spec",
        outcome="Deploy verified micro-kernel architecture",
        audience="Engineers & Leadership",
        document_type="Specification",
    )

    bdir = temp_environment["binders"] / "proj-alpha"
    assert bdir.is_dir()
    assert (bdir / "brief.md").exists()
    assert (bdir / "requirements.json").exists()
    assert (bdir / "sources.json").exists()
    assert (bdir / "plan.json").exists()
    assert (bdir / "draft.md").exists()
    assert (bdir / "evidence.json").exists()
    assert (bdir / "editions").is_dir()
    assert (bdir / "binder.json").exists()

    meta = binder["metadata"]
    assert meta["id"] == "proj-alpha"
    assert meta["state"] == "draft_brief"
    assert len(binder["requirements"]) == 3


def test_source_intake_and_attachment(temp_environment):
    binder_engine.create_binder(
        binder_id="proj-beta",
        title="Project Beta",
        outcome="Integrate external references",
    )

    content = b"# Raw Reference\nDetails of subsystem APIs and latencies."
    receipt = intake_service.intake_file(
        file_name="ref.md",
        content_bytes=content,
        author="Analyst",
    )

    source_entry = binder_engine.attach_source_to_binder(
        binder_id="proj-beta",
        doc_id=receipt["doc_id"],
        file_name=receipt["file_name"],
        source_sha256=receipt["source_sha256"],
        markdown_path=receipt["markdown_path"],
    )

    assert source_entry["citation_tag"] == "[SRC-1]"
    assert source_entry["file_name"] == "ref.md"

    bdata = binder_engine.get_binder("proj-beta")
    assert bdata["metadata"]["state"] == "planned"
    assert len(bdata["sources"]) == 1


def test_assemble_draft_and_evidence_citations(temp_environment):
    binder_engine.create_binder(
        binder_id="proj-gamma",
        title="Project Gamma",
        outcome="Synthesize verified findings",
    )

    receipt = intake_service.intake_file(
        file_name="data.md",
        content_bytes=b"Performance metrics: latency < 10ms in all benchmarks.",
    )
    binder_engine.attach_source_to_binder(
        binder_id="proj-gamma",
        doc_id=receipt["doc_id"],
        file_name=receipt["file_name"],
        source_sha256=receipt["source_sha256"],
        markdown_path=receipt["markdown_path"],
    )

    assembled = binder_engine.assemble_draft("proj-gamma")
    assert assembled["metadata"]["state"] == "ready_for_review"
    assert "<!-- section: REQ-001 -->" in assembled["draft"]
    assert "[SRC-1]" in assembled["draft"]

    # Verify evidence chain
    assert len(assembled["evidence"]) > 0
    assert assembled["evidence"][0]["citation"] == "[SRC-1]"


def test_anti_drift_concurrency_conflict(temp_environment):
    binder = binder_engine.create_binder(
        binder_id="proj-delta",
        title="Project Delta",
        outcome="Test revision conflict guardrail",
    )

    initial_hash = binder["draft_sha256"]

    # Legitimate save with matching base hash
    res = binder_engine.update_draft(
        binder_id="proj-delta",
        new_content="# Project Delta\n\nUpdated paragraph 1.",
        expected_base_hash=initial_hash,
    )
    assert res["saved"] is True
    new_hash = res["draft_sha256"]
    assert new_hash != initial_hash

    # Stale save attempt using initial_hash should fail with ConcurrencyConflictError
    with pytest.raises(ConcurrencyConflictError) as exc_info:
        binder_engine.update_draft(
            binder_id="proj-delta",
            new_content="# Project Delta\n\nConflicting stale rewrite.",
            expected_base_hash=initial_hash,
        )
    assert "Draft conflict" in str(exc_info.value)


def test_accept_and_publish_edition(temp_environment):
    binder_engine.create_binder(
        binder_id="proj-epsilon",
        title="Project Epsilon",
        outcome="Test full freeze and publication pipeline",
    )

    # 1. Assemble draft
    binder_engine.assemble_draft("proj-epsilon")

    # 2. Accept edition
    manifest = binder_engine.accept_edition(
        binder_id="proj-epsilon",
        reviewer_notes="Approved for public distribution.",
    )
    assert manifest["edition"] == 1
    assert manifest["requirements_verified"] is True

    bdata = binder_engine.get_binder("proj-epsilon")
    assert bdata["metadata"]["state"] == "accepted"
    assert len(bdata["editions"]) == 1

    # 3. Publish edition
    pub_receipt = binder_engine.publish_edition("proj-epsilon", edition_num=1)
    assert pub_receipt["target"] == "local_static"
    assert Path(pub_receipt["output_path"]).is_file()

    # Verify generated HTML
    html_content = Path(pub_receipt["output_path"]).read_text(encoding="utf-8")
    assert "Edition 1 • Sovereign Publication" in html_content
    # Internal section markers should be stripped in published edition
    assert "<!-- section:" not in html_content

    bdata = binder_engine.get_binder("proj-epsilon")
    assert bdata["metadata"]["state"] == "published"
