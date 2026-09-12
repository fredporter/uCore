"""Integration tests for Runtime Device Delivery and Capsule Governance API."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.runtime_device_api import (
    handle_authorize_capsule,
    handle_get_profiles,
    handle_inspect_device,
    handle_list_capsules,
    handle_revoke_capsule,
    register_runtime_device_routes,
)
from app.api import runtime_device_api


class RuntimeDeviceDeliveryAPITest(AioHTTPTestCase):
    async def get_application(self):
        self._temp_dir = Path(tempfile.mkdtemp(prefix="ucore_runtime_test_"))
        programs_dir = self._temp_dir / "programs"
        programs_dir.mkdir(parents=True)

        # Create a sample capsule
        capsule_dir = programs_dir / "test-capsule"
        capsule_dir.mkdir()
        (capsule_dir / "capsule.yaml").write_text("format: ucode-capsule/1\nid: test-capsule\n", encoding="utf-8")
        (capsule_dir / ".capsule_state.json").write_text(
            json.dumps({"capsule_id": "test-capsule", "authorized": False}),
            encoding="utf-8",
        )

        # Patch get_ucode_programs_dir
        runtime_device_api.get_ucode_programs_dir = lambda: programs_dir

        app = web.Application()
        register_runtime_device_routes(app)
        return app

    async def tearDownAsync(self):
        await super().tearDownAsync()
        if hasattr(self, "_temp_dir") and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    async def test_get_profiles(self):
        resp = await self.client.get("/api/runtime/profiles")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        spec = data["spec"]
        assert spec["baseline"]["distribution"] == "Linux Mint"
        assert spec["baseline"]["version"] == "22"
        assert "cinnamon-full" in spec["profiles"]
        assert "xfce-light" in spec["profiles"]
        assert "inspect" in spec["safety_gates"]
        assert "provision" in spec["safety_gates"]

    async def test_inspect_device(self):
        payload = {
            "device": {
                "vendor": "Lenovo",
                "model": "ThinkPad T480",
                "arch": "x86_64",
                "ram_mb": 16384,
                "storage_gb": 256,
            }
        }
        resp = await self.client.post("/api/runtime/profiles/inspect", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assessment = data["assessment"]
        assert "inspect" in assessment["safety_gate"]
        assert assessment["profiles"]["cinnamon-full"]["compatible"] is True
        assert assessment["preferred_profile"] == "cinnamon-full"

    async def test_list_capsules_and_anti_autorun(self):
        resp = await self.client.get("/api/runtime/capsules")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert data["count"] == 1
        capsule = data["capsules"][0]
        assert capsule["id"] == "test-capsule"
        assert capsule["authorized"] is False
        assert capsule["has_anti_autorun_gate"] is True

    async def test_authorize_and_revoke_capsule(self):
        # Authorize
        resp = await self.client.post("/api/runtime/capsules/test-capsule/authorize")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert data["state"]["authorized"] is True

        # Verify listed status is now authorized
        list_resp = await self.client.get("/api/runtime/capsules")
        list_data = await list_resp.json()
        assert list_data["capsules"][0]["authorized"] is True

        # Revoke
        rev_resp = await self.client.post("/api/runtime/capsules/test-capsule/revoke")
        assert rev_resp.status == 200
        rev_data = await rev_resp.json()
        assert rev_data["status"] == "ok"
        assert rev_data["state"]["authorized"] is False
