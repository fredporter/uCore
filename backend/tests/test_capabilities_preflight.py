"""Integration tests for Capabilities Preflight and Readiness API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.extensions_api import (
    handle_capabilities_readiness,
    handle_capability_preflight,
)
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

    async def test_developer_guided_preflight_ready(self):
        resp = await self.client.get("/api/capabilities/developer.guided/preflight")
        assert resp.status == 200
        data = await resp.json()
        assert data["capability"] == "developer.guided"
        assert data["ready"] is True
        assert data["repair_required"] is False
        assert data["repair"] == []

    async def test_capabilities_readiness_batch_ready(self):
        resp = await self.client.get(
            "/api/capabilities/readiness?capabilities=workflow.run,knowledge.search,developer.guided"
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["ready"] is True
        assert data["count"] == 3
        caps = {c["capability"]: c for c in data["capabilities"]}
        assert "workflow.run" in caps
        assert caps["workflow.run"]["ready"] is True
        assert "knowledge.search" in caps
        assert caps["knowledge.search"]["ready"] is True
        assert "developer.guided" in caps
        assert caps["developer.guided"]["ready"] is True

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
