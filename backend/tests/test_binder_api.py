"""Integration tests for Durable Binder API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.binder_api import (
    handle_binder_accept,
    handle_binder_audit,
    handle_binder_authorise,
    handle_binder_create,
    handle_binder_decisions_get,
    handle_binder_decisions_post,
    handle_binder_draft_update,
    handle_binder_export_gemini,
    handle_binder_export_obsidian,
    handle_binder_get,
    handle_binder_intake,
    handle_binder_list,
    handle_binder_publish,
    handle_binder_resume,
    handle_binder_run,
    handle_binder_section_update,
)
from app.flow import binder_engine
from app.services import intake_service


class BinderAPITest(AioHTTPTestCase):
    async def get_application(self):
        self._temp_dir = Path("/tmp/ucore_binder_test")
        import shutil
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
        self._temp_dir.mkdir(parents=True, exist_ok=True)

        vault = self._temp_dir / "Vault"
        binders = vault / "Binders"
        orig = vault / "Originals"
        docs = vault / "Documents"
        pub = self._temp_dir / "Public"

        binder_engine.VAULT_ROOT = vault
        binder_engine.BINDERS_ROOT = binders
        intake_service.VAULT_ROOT = vault
        intake_service.ORIGINALS_ROOT = orig
        intake_service.DOCUMENTS_ROOT = docs

        self._home_backup = Path.home
        Path.home = lambda: self._temp_dir

        app = web.Application()
        app.router.add_get("/api/binder/list", handle_binder_list)
        app.router.add_post("/api/binder/create", handle_binder_create)
        app.router.add_get("/api/binder/{binder_id}", handle_binder_get)
        app.router.add_post("/api/binder/{binder_id}/intake", handle_binder_intake)
        app.router.add_post("/api/binder/{binder_id}/authorise", handle_binder_authorise)
        app.router.add_post("/api/binder/{binder_id}/run", handle_binder_run)
        app.router.add_post("/api/binder/{binder_id}/resume", handle_binder_resume)
        app.router.add_get("/api/binder/{binder_id}/audit", handle_binder_audit)
        app.router.add_get("/api/binder/{binder_id}/decisions", handle_binder_decisions_get)
        app.router.add_post("/api/binder/{binder_id}/decisions", handle_binder_decisions_post)
        app.router.add_patch("/api/binder/{binder_id}/draft", handle_binder_draft_update)
        app.router.add_patch("/api/binder/{binder_id}/section/{req_id}", handle_binder_section_update)
        app.router.add_post("/api/binder/{binder_id}/accept", handle_binder_accept)
        app.router.add_post("/api/binder/{binder_id}/publish", handle_binder_publish)
        app.router.add_get("/api/binder/{binder_id}/export/gemini", handle_binder_export_gemini)
        app.router.add_get("/api/binder/{binder_id}/export/obsidian", handle_binder_export_obsidian)
        return app

    async def asyncTearDown(self):
        Path.home = self._home_backup
        import shutil
        if self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
        await super().asyncTearDown()

    async def test_full_binder_api_lifecycle(self):
        # 1. Create binder
        resp = await self.client.post("/api/binder/create", json={
            "id": "b-system-spec",
            "title": "System Specification",
            "outcome": "Complete offline pipeline",
        })
        assert resp.status == 200
        data = await resp.json()
        assert data["created"] is True
        assert data["binder"]["metadata"]["state"] == "draft_brief"

        # 2. Get binder
        resp = await self.client.get("/api/binder/b-system-spec")
        assert resp.status == 200
        bdata = await resp.json()
        assert bdata["binder"]["metadata"]["title"] == "System Specification"
        orig_hash = bdata["binder"]["draft_sha256"]

        # 3. Intake document as source
        resp = await self.client.post("/api/binder/b-system-spec/intake", json={
            "file_name": "network_contract.md",
            "content": "# Network Contract\nAll nodes communicate over local socket.",
            "author": "SecOps",
        })
        assert resp.status == 200
        intake_res = await resp.json()
        assert intake_res["success"] is True
        assert intake_res["source"]["citation_tag"] == "[SRC-1]"

        # 3b. Record architectural decision
        resp = await self.client.post("/api/binder/b-system-spec/decisions", json={
            "title": "Use Unix domain sockets for local IPC",
            "rationale": "High throughput and no WAN attack surface",
        })
        assert resp.status == 200
        dec_res = await resp.json()
        assert dec_res["success"] is True
        assert dec_res["decision"]["id"] == "DEC-001"

        # List decisions
        resp = await self.client.get("/api/binder/b-system-spec/decisions")
        assert resp.status == 200
        dec_list = await resp.json()
        assert len(dec_list["decisions"]) == 1

        # 3c. Authorize execution run
        resp = await self.client.post("/api/binder/b-system-spec/authorise", json={
            "run_budget": {"max_tasks": 3},
            "network_allowed": False,
        })
        assert resp.status == 200
        auth_res = await resp.json()
        assert auth_res["authorised"] is True

        # 4. Assembly run
        resp = await self.client.post("/api/binder/b-system-spec/run")
        assert resp.status == 200
        run_res = await resp.json()
        assert run_res["binder"]["metadata"]["state"] == "ready_for_review"
        draft_hash = run_res["binder"]["draft_sha256"]

        # 4b. Audit binder
        resp = await self.client.get("/api/binder/b-system-spec/audit")
        assert resp.status == 200
        audit_res = await resp.json()
        assert audit_res["audit"]["coverage_percentage"] == 100.0
        assert audit_res["audit"]["passed"] is True

        # 4c. Targeted section update
        resp = await self.client.patch("/api/binder/b-system-spec/section/REQ-001", json={
            "content": "## 1. Executive Summary\n\nTailored summary for engineers [SRC-1].",
        })
        assert resp.status == 200
        sec_res = await resp.json()
        assert sec_res["saved"] is True
        draft_hash = sec_res["draft_sha256"]

        # 5. Concurrency conflict check on draft
        resp = await self.client.patch("/api/binder/b-system-spec/draft", json={
            "content": "# Conflicting Edit",
            "expected_base_hash": "wrong_hash_123",
        })
        assert resp.status == 409
        conflict_err = await resp.json()
        assert conflict_err["error"] == "concurrency_conflict"

        # Legitimate draft edit
        resp = await self.client.patch("/api/binder/b-system-spec/draft", json={
            "content": "# System Specification\n\nReviewed and edited content [SRC-1].",
            "expected_base_hash": draft_hash,
        })
        assert resp.status == 200
        saved_res = await resp.json()
        assert saved_res["saved"] is True

        # 5b. Export for Gemini Notebooks & Obsidian
        resp = await self.client.get("/api/binder/b-system-spec/export/gemini")
        assert resp.status == 200
        gem_res = await resp.json()
        assert gem_res["success"] is True
        assert "[^1]" in gem_res["package"]["content"]

        resp = await self.client.get("/api/binder/b-system-spec/export/obsidian")
        assert resp.status == 200
        obs_res = await resp.json()
        assert obs_res["success"] is True
        assert "[[brief|Project Brief]]" in obs_res["content"]

        # 6. Accept edition
        resp = await self.client.post("/api/binder/b-system-spec/accept", json={
            "notes": "Peer reviewed and signed off",
        })
        assert resp.status == 200
        accept_res = await resp.json()
        assert accept_res["accepted"] is True
        assert accept_res["edition"]["edition"] == 1

        # 7. Publish edition
        resp = await self.client.post("/api/binder/b-system-spec/publish", json={
            "target": "local_static",
        })
        assert resp.status == 200
        pub_res = await resp.json()
        assert pub_res["published"] is True
        assert "index.html" in pub_res["receipt"]["output_path"]

        # 8. Verify in binder list
        resp = await self.client.get("/api/binder/list")
        assert resp.status == 200
        list_res = await resp.json()
        assert list_res["count"] >= 1
        assert any(b["id"] == "b-system-spec" for b in list_res["binders"])
