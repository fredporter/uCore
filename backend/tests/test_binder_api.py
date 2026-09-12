"""Integration tests for Durable Binder API endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.binder_api import (
    handle_binder_accept,
    handle_binder_create,
    handle_binder_draft_update,
    handle_binder_get,
    handle_binder_intake,
    handle_binder_list,
    handle_binder_publish,
    handle_binder_run,
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
        app.router.add_post("/api/binder/{binder_id}/run", handle_binder_run)
        app.router.add_patch("/api/binder/{binder_id}/draft", handle_binder_draft_update)
        app.router.add_post("/api/binder/{binder_id}/accept", handle_binder_accept)
        app.router.add_post("/api/binder/{binder_id}/publish", handle_binder_publish)
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

        # 4. Assembly run
        resp = await self.client.post("/api/binder/b-system-spec/run")
        assert resp.status == 200
        run_res = await resp.json()
        assert run_res["binder"]["metadata"]["state"] == "ready_for_review"
        draft_hash = run_res["binder"]["draft_sha256"]

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
