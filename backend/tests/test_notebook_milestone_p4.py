"""Comprehensive Verification Suite for Milestone P4: Notebook Binder & Durable Run.

Implements the complete Section 15 and Section 8 refactor plan acceptance criteria:
1. Ingest a mixed document collection with originals co-located directly inside the binder.
2. Verify all 8 canonical durable records exist on disk.
3. Authorize bounded uFlow run and execute assembly with checkpointing.
4. Test interrupted run restart and task state reconciliation.
5. Test concurrency conflict rejection and targeted section-level editing.
6. Run deterministic anti-drift coverage and provenance audit.
7. Record architectural decisions in decisions.json.
8. Verify Gemini Notebooks (NotebookLM) and Obsidian universal export bridges.
9. Freeze immutable edition snapshot with manifest.
10. Compile offline static bundle and verify zero external CDN dependencies.
"""

from __future__ import annotations

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


def test_milestone_p4_complete_lifecycle(temp_environment):
    # ── 1. Create Binder with 8 Canonical Records ───
    binder_id = "climate-resilience-spec"
    binder = binder_engine.create_binder(
        binder_id=binder_id,
        title="Urban Climate Resilience Specification",
        outcome="Standardized municipal adaptation architecture for coastal zones",
        audience="Civil Engineers & Policy Directors",
        document_type="Specification",
        requirements=[
            {"id": "REQ-001", "title": "Executive Summary", "description": "High-level summary of risks and intervention targets", "status": "pending"},
            {"id": "REQ-002", "title": "Hydrological Modeling & Flood Barriers", "description": "Design criteria for surge barriers and permeable drainage", "status": "pending"},
            {"id": "REQ-003", "title": "Telemetry & Sensor Deployment", "description": "IoT tidal telemetry and local mDNS mesh communication", "status": "pending"},
        ],
        non_goals=["Commercial proprietary cloud dependencies", "Unverified climate projections"],
    )

    bdir = temp_environment["binders"] / binder_id
    assert bdir.is_dir()
    assert (bdir / "brief.md").exists()
    assert (bdir / "requirements.json").exists()
    assert (bdir / "sources.json").exists()
    assert (bdir / "plan.json").exists()
    assert (bdir / "decisions.json").exists()
    assert (bdir / "draft.md").exists()
    assert (bdir / "evidence.json").exists()
    assert (bdir / "editions").is_dir()
    assert (bdir / "binder.json").exists()

    meta = binder["metadata"]
    assert meta["state"] == "draft_brief"
    assert len(binder["decisions"]) == 0

    # ── 2. Ingest Mixed-Document Collection Co-located inside Binder ───
    doc1_content = b"# Coastal Hydrodynamics\nPeak storm surge modeled at +3.2m above baseline.\nPermeable drainage absorbs 45% runoff."
    doc2_content = b"{\"sensor_mesh\": \"LoRaWAN-915\", \"sample_interval_sec\": 30, \"local_mdns\": \"coastal.local\"}"

    r1 = intake_service.intake_binder_source(
        binder_dir=bdir,
        file_name="hydro_modeling.md",
        content_bytes=doc1_content,
        author="Marine Institute",
    )
    r2 = intake_service.intake_binder_source(
        binder_dir=bdir,
        file_name="telemetry_config.json",
        content_bytes=doc2_content,
        author="Sensor Lab",
    )

    # Verify co-location: originals and markdown live inside binder's sources folder
    assert Path(r1["original_path"]).is_file()
    assert Path(r1["markdown_path"]).is_file()
    assert bdir / "sources" in Path(r1["original_path"]).parents
    assert (bdir / "sources" / r1["doc_id"] / "meta.json").is_file()

    # Attach to binder provenance ledger
    s1 = binder_engine.attach_source_to_binder(
        binder_id=binder_id,
        doc_id=r1["doc_id"],
        file_name=r1["file_name"],
        source_sha256=r1["source_sha256"],
        markdown_path=r1["markdown_path"],
        original_path=r1["original_path"],
    )
    s2 = binder_engine.attach_source_to_binder(
        binder_id=binder_id,
        doc_id=r2["doc_id"],
        file_name=r2["file_name"],
        source_sha256=r2["source_sha256"],
        markdown_path=r2["markdown_path"],
        original_path=r2["original_path"],
    )

    assert s1["citation_tag"] == "[SRC-1]"
    assert s2["citation_tag"] == "[SRC-2]"
    assert s1["original_path"] == r1["original_path"]

    bdata = binder_engine.get_binder(binder_id)
    assert bdata["metadata"]["state"] == "planned"
    assert len(bdata["sources"]) == 2

    # ── 3. Record Project Decisions ───
    d1 = binder_engine.record_decision(
        binder_id=binder_id,
        title="Adopt local mDNS over centralized DNS",
        status="accepted",
        rationale="Eliminates external WAN dependency during network outages.",
    )
    assert d1["id"] == "DEC-001"
    assert d1["status"] == "accepted"

    decisions = binder_engine.list_decisions(binder_id)
    assert len(decisions) == 1
    assert decisions[0]["title"] == "Adopt local mDNS over centralized DNS"

    # ── 4. Authorize Execution Run ───
    auth_receipt = binder_engine.authorise_run(
        binder_id=binder_id,
        run_budget={"max_tasks": 5, "max_tokens": 20000},
        network_allowed=False,
    )
    assert auth_receipt["requirements_count"] == 3
    assert (bdir / "auth_receipt.json").exists()

    bdata = binder_engine.get_binder(binder_id)
    assert bdata["metadata"]["state"] == "authorised"

    # ── 5. Assemble Draft with Checkpointing ───
    assembled = binder_engine.assemble_draft(binder_id)
    assert assembled["metadata"]["state"] == "ready_for_review"
    assert (bdir / "run_checkpoint.json").exists()

    cp = json.loads((bdir / "run_checkpoint.json").read_text(encoding="utf-8"))
    assert len(cp["completed_task_ids"]) == 3

    # All plan tasks should now be done
    plan = json.loads((bdir / "plan.json").read_text(encoding="utf-8"))
    assert all(t["status"] == "done" for t in plan)

    # ── 6. Test Interrupted Run Resumption ───
    # Append a new pending task
    plan.append({"task_id": "T-4", "title": "Finalize risk appendix", "req_id": "REQ-003", "status": "todo"})
    (bdir / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")

    resumed = binder_engine.resume_or_reconcile_run(binder_id)
    assert resumed["metadata"]["state"] == "ready_for_review"
    plan_after = json.loads((bdir / "plan.json").read_text(encoding="utf-8"))
    assert all(t["status"] == "done" for t in plan_after)

    # ── 7. Deterministic Anti-Drift Audit ───
    audit = binder_engine.audit_binder(binder_id)
    assert audit["coverage_percentage"] == 100.0
    assert audit["requirements_total"] == 3
    assert audit["requirements_mapped"] == 3
    assert len(audit["missing_requirements"]) == 0
    assert len(audit["unverified_citations"]) == 0
    assert audit["passed"] is True

    # ── 8. Concurrency Protection & Targeted Section Editing ───
    initial_draft_hash = resumed["draft_sha256"]

    # Full draft stale update must fail
    with pytest.raises(ConcurrencyConflictError):
        binder_engine.update_draft(
            binder_id=binder_id,
            new_content="Conflicting blind overwrite",
            expected_base_hash="invalid_or_stale_hash_0000",
        )

    # Targeted section update succeeds and recalculates hash
    sec_res = binder_engine.update_section(
        binder_id=binder_id,
        req_id="REQ-002",
        new_section_body="## Hydrological Modeling & Flood Barriers\n\nReinforced surge barrier rated to +4.5m with automated telemetry controls [SRC-1].",
    )
    assert sec_res["saved"] is True
    assert sec_res["draft_sha256"] != initial_draft_hash

    # Stale targeted section update fails
    with pytest.raises(ConcurrencyConflictError):
        binder_engine.update_section(
            binder_id=binder_id,
            req_id="REQ-002",
            new_section_body="Conflicting section edit",
            expected_section_hash="stale_section_hash_1111",
        )

    # ── 9. Universal Export Bridges ───
    # A. Gemini Notebooks (NotebookLM) Export
    gemini_pkg = binder_engine.export_gemini_notebook(binder_id)
    assert "<!-- section:" not in gemini_pkg["content"]
    assert "[^1]" in gemini_pkg["content"]
    assert "## References & Sources" in gemini_pkg["content"]
    assert "hydro_modeling.md" in gemini_pkg["content"]

    # B. Obsidian Vault Export
    obsidian_pkg = binder_engine.export_obsidian_binder(binder_id)
    assert (bdir / "index.md").is_file()
    assert "[[brief|Project Brief]]" in obsidian_pkg["content"]
    assert "[[sources/" in obsidian_pkg["content"]

    # ── 10. Accept Edition & Offline Static Publishing ───
    manifest = binder_engine.accept_edition(
        binder_id=binder_id,
        reviewer_notes="Approved for municipal council review.",
    )
    assert manifest["edition"] == 1
    assert manifest["requirements_verified"] is True
    assert (bdir / "editions" / "edition_1.md").is_file()
    assert (bdir / "editions" / "edition_1.manifest.json").is_file()

    pub_receipt = binder_engine.publish_edition(binder_id, edition_num=1, target="local_static")
    assert pub_receipt["target"] == "local_static"
    output_html = Path(pub_receipt["output_path"])
    assert output_html.is_file()

    html_content = output_html.read_text(encoding="utf-8")
    assert "Urban Climate Resilience Specification — Edition 1" in html_content
    # Offline guarantee: Zero external CDN script or link tags
    assert "http://" not in html_content
    assert "https://" not in html_content
    assert "cdn." not in html_content
    assert "unpkg.com" not in html_content

    bdata_final = binder_engine.get_binder(binder_id)
    assert bdata_final["metadata"]["state"] == "published"
    assert bdata_final["metadata"]["latest_published_edition"] == 1
