"""Integration tests for Capabilities Preflight and Readiness API endpoints."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.extensions_api import (
    handle_capabilities_readiness,
    handle_capability_preflight,
)
from app.core.settings import settings
from app.extensions.registry import registry


class CapabilitiesPreflightAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        registry.discover()
        registry.register_routes(app)
        app.router.add_get(
            "/api/capabilities/{capability}/preflight",
            handle_capability_preflight,
        )
        app.router.add_get(
            "/api/capabilities/readiness",
            handle_capabilities_readiness,
        )
        return app

    async def test_workflow_run_preflight_ready(self):
        resp = await self.client.get("/api/capabilities/workflow.run/preflight")
        assert resp.status == 200
        data = await resp.json()
        assert data["capability"] == "workflow.run"
        assert data["ready"] is True
        assert data["repair_required"] is False
        assert data["repair"] == []

    async def test_knowledge_search_preflight_ready(self):
        resp = await self.client.get("/api/capabilities/knowledge.search/preflight")
        assert resp.status == 200
        data = await resp.json()
        assert data["capability"] == "knowledge.search"
        assert data["ready"] is True
        assert data["repair_required"] is False
        assert data["repair"] == []

    async def test_developer_guided_preflight_excludes_uflow_and_uknowledge(self):
        resp = await self.client.get("/api/capabilities/developer.guided/preflight")
        data = await resp.json()
        assert data["capability"] == "developer.guided"
        repair_ids = [item.get("id") for item in data.get("repair", [])]
        assert "uFlow" not in repair_ids
        assert "uKnowledge" not in repair_ids

    async def test_developer_guided_preflight_ready_when_prereqs_met(self):
        async def fake_check_tool(tool_id: str):
            return {"installed": True, "ok": True}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "uCore").mkdir()
            (root / "uCode").mkdir()
            with patch.object(settings, "udos_root", root), \
                 patch("app.api.extensions_api.check_tool", side_effect=fake_check_tool):
                resp = await self.client.get("/api/capabilities/developer.guided/preflight")
                assert resp.status == 200
                data = await resp.json()
                assert data["capability"] == "developer.guided"
                assert data["ready"] is True
                assert data["repair_required"] is False
                assert data["repair"] == []

    async def test_capabilities_readiness_batch_ready(self):
        resp = await self.client.get(
            "/api/capabilities/readiness?capabilities=workflow.run,knowledge.search"
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["ready"] is True
        assert data["count"] == 2
        caps = {c["capability"]: c for c in data["capabilities"]}
        assert "workflow.run" in caps
        assert caps["workflow.run"]["ready"] is True
        assert "knowledge.search" in caps
        assert caps["knowledge.search"]["ready"] is True

    async def test_unknown_capability_preflight_missing(self):
        resp = await self.client.get("/api/capabilities/nonexistent.capability/preflight")
        assert resp.status == 412
        data = await resp.json()
        assert data["ready"] is False
        assert data["repair_required"] is True
        assert any(
            item.get("kind") == "config" and item.get("id") == "capability_requirements"
            for item in data["repair"]
        )
