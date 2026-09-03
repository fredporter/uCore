"""Integration tests for System Surface API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.surfaces.system_api import register_system_api_routes


class SystemSurfaceAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        register_system_api_routes(app)
        return app

    async def test_list_pages(self):
        resp = await self.client.get("/api/system/pages")
        assert resp.status == 200
        data = await resp.json()
        assert "pages" in data
        assert data["count"] >= 1
        ids = [p["id"] for p in data["pages"]]
        assert "S100" in ids
        assert "S600" in ids

    async def test_list_services(self):
        resp = await self.client.get("/api/system/services")
        assert resp.status == 200
        data = await resp.json()
        assert "services" in data
        assert isinstance(data["services"], list)

    async def test_get_settings(self):
        resp = await self.client.get("/api/system/settings")
        assert resp.status == 200
        data = await resp.json()
        assert "settings" in data
        assert isinstance(data["settings"], dict)

    async def test_update_settings(self):
        resp = await self.client.post(
            "/api/system/settings",
            json={
                "scope": "global",
                "values": {"theme": "dark", "fontSize": 16},
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert "global" in data["settings"]
        assert data["settings"]["global"]["theme"] == "dark"

    async def test_update_settings_user_scope(self):
        resp = await self.client.post(
            "/api/system/settings",
            json={
                "scope": "user",
                "values": {"displayName": "Test User"},
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert "user" in data["settings"]
        assert data["settings"]["user"]["displayName"] == "Test User"

    async def test_user_preferences_roundtrip(self):
        update = await self.client.post(
            "/api/user/preferences",
            json={"preferences": {"themeMode": "light", "fontSize": 18, "unknown": "ignored"}},
        )
        assert update.status == 200
        updated = await update.json()
        assert updated["preferences"]["themeMode"] == "light"
        assert "unknown" not in updated["preferences"]
        response = await self.client.get("/api/user/preferences")
        assert response.status == 200
        assert (await response.json())["preferences"]["fontSize"] == 18
