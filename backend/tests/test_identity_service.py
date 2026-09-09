from pathlib import Path
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api import identity_api
from app.services import identity


def test_udos_id_generation():
    uid1 = identity.generate_udos_id()
    uid2 = identity.generate_udos_id()
    assert uid1.startswith("UDOS-")
    assert uid1 == uid2  # Deterministic for the same machine


def test_ensure_identity_initializes(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(identity.settings, "data_dir", data_dir)
    ident = identity.ensure_identity()
    assert ident.is_valid()
    assert ident.user_id.startswith("UDOS-")
    assert len(ident.profiles) >= 1
    assert ident.active_profile_id == "default"
    assert (data_dir / "identity.json").exists()


def test_multi_profile_isolation_and_switching(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(identity.settings, "data_dir", data_dir)
    
    # Initialize
    ident = identity.ensure_identity()
    assert ident.active_profile.id == "default"

    # Add second profile
    identity.update_profile("researcher", name="Alice Researcher", role="developer")
    full = identity.get_full_identity()
    profile_ids = [p["id"] for p in full["profiles"]]
    assert "default" in profile_ids
    assert "researcher" in profile_ids

    # Switch to second profile
    switched = identity.switch_profile("researcher")
    assert switched["active_profile_id"] == "researcher"
    assert switched["active_profile"]["name"] == "Alice Researcher"
    assert switched["authenticated"] is True

    # Check persistence
    reloaded = identity.load_identity()
    assert reloaded.active_profile_id == "researcher"


def test_logout_and_login_unauthenticated_state(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(identity.settings, "data_dir", data_dir)

    identity.ensure_identity()
    logged_out = identity.logout()
    assert logged_out["authenticated"] is False
    assert logged_out["active_profile_id"] == ""
    assert logged_out["active_profile"] is None

    logged_in = identity.login("default")
    assert logged_in["authenticated"] is True
    assert logged_in["active_profile_id"] == "default"
    assert logged_in["active_profile"] is not None


@pytest.mark.asyncio
async def test_identity_api_endpoints(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(identity.settings, "data_dir", data_dir)

    app = web.Application()
    identity_api.register_identity_routes(app)

    async with TestClient(TestServer(app)) as client:
        # GET /api/identity
        resp = await client.get("/api/identity")
        assert resp.status == 200
        assert "X-Udos-User" in resp.headers
        data = await resp.json()
        assert data["authenticated"] is True

        # POST /api/identity/profile
        resp = await client.post("/api/identity/profile", json={"profile_id": "team-lead", "name": "Lead", "role": "admin"})
        assert resp.status == 200
        data = await resp.json()
        assert any(p["id"] == "team-lead" for p in data["identity"]["profiles"])

        # POST /api/identity/switch
        resp = await client.post("/api/identity/switch", json={"profile_id": "team-lead"})
        assert resp.status == 200
        data = await resp.json()
        assert data["identity"]["active_profile_id"] == "team-lead"

        # POST /api/identity/logout
        resp = await client.post("/api/identity/logout")
        assert resp.status == 200
        data = await resp.json()
        assert data["identity"]["authenticated"] is False

        # POST /api/identity/login
        resp = await client.post("/api/identity/login", json={"profile_id": "team-lead"})
        assert resp.status == 200
        data = await resp.json()
        assert data["identity"]["authenticated"] is True
        assert data["identity"]["active_profile_id"] == "team-lead"
