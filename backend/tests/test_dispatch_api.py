"""Tests for Sovereign Dispatch and Device Capability API.

Verifies:
- POST /api/dispatch/calculate-display
- POST /api/dispatch/calculate-storage
- POST /api/dispatch/create
- GET  /api/dispatch/token/{token}
- POST /api/dispatch/rsvp/{token}
- GET  /api/dispatch/responses/{id}
- GET  /api/dispatch/preview-email/{id}
- Ephemeral lifecycle: expires_at, burn_after_read dissolution
- Preservation of raw originals in ~/Vault/dispatches/<id>/originals/
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.dispatch_api import register_dispatch_routes
from app.services.dispatch_store import dispatch_store


@pytest.fixture
async def dispatch_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create test client with isolated dispatch store."""
    vault = tmp_path / "Vault"
    dispatches = vault / "dispatches"
    tokens_file = tmp_path / "dispatch_tokens.json"

    monkeypatch.setattr(dispatch_store, "root_dir", dispatches)
    monkeypatch.setattr(dispatch_store, "token_index_path", tokens_file)
    dispatches.mkdir(parents=True, exist_ok=True)

    app = web.Application()
    register_dispatch_routes(app)

    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.mark.asyncio
async def test_calculate_display_pos(dispatch_client):
    """Test display calculation for 800x600 POS kiosk."""
    resp = await dispatch_client.post("/api/dispatch/calculate-display", json={
        "width": 800,
        "height": 600,
        "device_type": "pos_kiosk",
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["aspect_ratio"] == "4:3"
    assert data["gridcore"]["square_register"]["cols"] == 100
    assert data["gridcore"]["square_register"]["rows"] == 75
    assert data["gridcore"]["tall_register"]["cols"] == 66
    assert data["gridcore"]["tall_register"]["rows"] == 30
    assert data["gridcore"]["super_cells"]["cols"] == 33
    assert data["gridcore"]["super_cells"]["rows"] == 15
    assert data["gridcore"]["teletext_standard"]["fits_1x"] is True
    assert data["zen_viewport"]["scale_factor"] == 1.0


@pytest.mark.asyncio
async def test_calculate_display_ten_foot_tv(dispatch_client):
    """Test display calculation for 1080p 16:9 TV."""
    resp = await dispatch_client.post("/api/dispatch/calculate-display", json={
        "width": 1920,
        "height": 1080,
        "device_type": "ten_foot_tv",
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["aspect_ratio"] == "16:9"
    assert data["prose"]["layout_mode"] == "optimal_zen"
    assert data["prose"]["recommended_measure_ch"] == 72
    assert data["prose"]["max_width_px"] == 680
    assert data["zen_viewport"]["target_aspect"] == "16:9"
    assert data["zen_viewport"]["scale_factor"] == 1.5


@pytest.mark.asyncio
async def test_calculate_storage_capacities(dispatch_client):
    """Test storage calculation for 4GB USB stick."""
    resp = await dispatch_client.post("/api/dispatch/calculate-storage", json={
        "total_bytes": 4_000_000_000,
        "sys_bytes": 2_500_000_000,
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["storage_vault_usable_bytes"] == 1_500_000_000
    assert data["knowledge_capacity"]["plain_prose_notes"] > 400_000
    assert data["knowledge_capacity"]["indexed_notes_fts5"] > 300_000
    assert data["knowledge_capacity"]["encyclopedia_zim_capsules_1gb"] == 1


@pytest.mark.asyncio
async def test_dispatch_lifecycle_and_rsvp(dispatch_client):
    """Test creating dispatch, loading via token, and submitting RSVP."""
    create_resp = await dispatch_client.post("/api/dispatch/create", json={
        "title": "Solstice Gathering",
        "lead_text": "Join us under the stars",
        "story_markdown": "# Solstice\n\nWelcome to the story.\n\n---\n\n? (Dietary): [text]\n\n---\n\nThank you!",
        "burn_after_read": False,
    })
    assert create_resp.status == 200
    created = await create_resp.json()
    token = created["token"]
    dispatch_id = created["dispatch"]["id"]

    # Verify originals preserved
    orig_file = dispatch_store.root_dir / dispatch_id / "originals" / "source.story.md"
    assert orig_file.exists()
    assert "Solstice" in orig_file.read_text(encoding="utf-8")

    # Load via token
    get_resp = await dispatch_client.get(f"/api/dispatch/token/{token}")
    assert get_resp.status == 200
    get_data = await get_resp.json()
    assert get_data["status"] == "active"
    assert get_data["dispatch"]["title"] == "Solstice Gathering"
    assert get_data["dispatch"]["view_count"] == 1

    # Submit RSVP
    rsvp_resp = await dispatch_client.post(f"/api/dispatch/rsvp/{token}", json={
        "dietary": "Vegetarian",
        "attending": True,
    })
    assert rsvp_resp.status == 200
    rsvp_data = await rsvp_resp.json()
    assert rsvp_data["status"] == "success"

    # Host fetches responses
    resp_list = await dispatch_client.get(f"/api/dispatch/responses/{dispatch_id}")
    assert resp_list.status == 200
    resps = await resp_list.json()
    assert len(resps["responses"]) == 1
    assert resps["responses"][0]["data"]["dietary"] == "Vegetarian"


@pytest.mark.asyncio
async def test_burn_after_read_dissolution(dispatch_client):
    """Test that burn_after_read dissolves the dispatch into ether upon submission."""
    create_resp = await dispatch_client.post("/api/dispatch/create", json={
        "title": "Secret Token",
        "story_markdown": "One-time view.\n---\n? Confirm: [ ]",
        "burn_after_read": True,
    })
    created = await create_resp.json()
    token = created["token"]

    # First view succeeds
    resp1 = await dispatch_client.get(f"/api/dispatch/token/{token}")
    assert resp1.status == 200

    # Submit RSVP triggers burn
    rsvp_resp = await dispatch_client.post(f"/api/dispatch/rsvp/{token}", json={"confirmed": True})
    assert rsvp_resp.status == 200

    # Subsequent access is burned / dissolved
    resp2 = await dispatch_client.get(f"/api/dispatch/token/{token}")
    assert resp2.status == 200
    data2 = await resp2.json()
    assert data2["status"] == "burned"
    assert "dissolved into the ether" in data2["tombstone"]


@pytest.mark.asyncio
async def test_expired_token_handling(dispatch_client, monkeypatch):
    """Test token expiration."""
    create_resp = await dispatch_client.post("/api/dispatch/create", json={
        "title": "Expiring Event",
        "story_markdown": "Expires fast.",
        "expires_in_seconds": 1,
    })
    created = await create_resp.json()
    token = created["token"]

    # Advance time artificially
    future_time = int(time.time()) + 10
    monkeypatch.setattr(time, "time", lambda: future_time)

    resp = await dispatch_client.get(f"/api/dispatch/token/{token}")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "expired"
    assert "expired and dissolved" in data["tombstone"]


@pytest.mark.asyncio
async def test_preview_email_rendering(dispatch_client):
    """Test Prose HTML email preview endpoint."""
    create_resp = await dispatch_client.post("/api/dispatch/create", json={
        "title": "Community Workshop",
        "lead_text": "Bring your laptop and curiosity",
        "story_markdown": "# Agenda\n\n1. Introduction\n2. Hands-on coding",
    })
    created = await create_resp.json()
    dispatch_id = created["dispatch"]["id"]

    email_resp = await dispatch_client.get(f"/api/dispatch/preview-email/{dispatch_id}")
    assert email_resp.status == 200
    assert email_resp.content_type == "text/html"
    html_text = await email_resp.text()

    assert "Community Workshop" in html_text
    assert "Bring your laptop and curiosity" in html_text
    assert "Open Interactive Story" in html_text
    assert "Zero tracking pixels" in html_text
