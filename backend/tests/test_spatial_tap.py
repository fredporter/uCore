"""Tests for Spatial NFC Tap simulation and Peer Handshake."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from app.api.spatial import (
    handle_spatial_tap,
)
from app.services.spatial_service import SpatialService


@pytest.fixture
def test_spatial_svc(tmp_path: Path) -> SpatialService:
    fixture_data = {
        "fixture_revision": "fixture_rev_20231119_01",
        "type": "generic",
        "visibility": "public",
        "binder": {"binder_id": "binder-oakhaven-tomb"},
        "fictional_place": {
            "name": "Oakhaven Sanctuary",
            "waypoint_ref": "urn:uds:fixture:generic:waypoint-oakhaven-01",
            "coordinates": {"lat": -31.9505, "lon": 115.8605},
        },
        "tap": {
            "marker_envelope": {"version": "1.0", "marker_id": "marker-oakhaven-nfc-01"},
            "waypoint_ref": "urn:uds:fixture:generic:waypoint-oakhaven-01",
            "authorised_resources": ["urn:uds:fixture:generic:binder-oakhaven-tomb"],
        },
        "peer_handshake": {
            "test_peer_id": "peer-alpha-test",
            "audience": "ucore-spatial-service",
            "pre_enrolled_secret": "test-secret-key-32-bytes",
            "protocol_version": "1.0",
        },
    }
    fixture_file = tmp_path / "fixture.json"
    fixture_file.write_text(json.dumps(fixture_data), encoding="utf-8")
    return SpatialService(fixture_path=fixture_file, receipt_path=tmp_path / "receipts.sqlite3")


def test_tap_resolution_success_and_replay(test_spatial_svc: SpatialService):
    svc = test_spatial_svc
    envelope = {"version": "1.0", "marker_id": "marker-oakhaven-nfc-01"}

    receipt1 = svc.resolve_tap(
        profile_id="profile-user-1",
        event_id="evt-001",
        marker_payload=envelope,
        simulated_position={"lat": -31.9505, "lon": 115.8605},
    )

    assert receipt1["outcome"] == "success"
    assert receipt1["waypoint_ref"] == "urn:uds:fixture:generic:waypoint-oakhaven-01"
    assert receipt1["authorised_resource_refs"] == ["urn:uds:fixture:generic:binder-oakhaven-tomb"]
    assert receipt1["replayed"] is False

    # Second call with same event_id: idempotent replay
    restarted = SpatialService(svc.fixture_path, svc.receipt_path)
    receipt2 = restarted.resolve_tap(
        profile_id="profile-user-1",
        event_id="evt-001",
        marker_payload=envelope,
    )
    assert receipt2["outcome"] == "success"
    assert receipt2["replayed"] is True
    assert receipt2["processed_at"] == receipt1["processed_at"]

    fixture = svc.load_fixture()
    fixture["binder"].update(visibility="private", owner_profile_id="profile-user-2")
    svc.fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
    assert restarted.resolve_tap("profile-user-1", "evt-001", envelope)["authorised_resource_refs"] == []
    other = restarted.resolve_tap("profile-user-2", "evt-001", envelope)
    assert other["authorised_resource_refs"] == receipt1["authorised_resource_refs"]
    assert other["replayed"] is False


def test_tap_unauthorised_for_unknown_marker(test_spatial_svc: SpatialService):
    svc = test_spatial_svc
    envelope = {"version": "1.0", "marker_id": "unknown-marker"}

    receipt = svc.resolve_tap(
        profile_id="profile-user-1",
        event_id="evt-002",
        marker_payload=envelope,
    )
    assert receipt["outcome"] == "unauthorised"
    assert receipt["waypoint_ref"] is None


def test_tap_unauthorised_for_anonymous_profile(test_spatial_svc: SpatialService):
    svc = test_spatial_svc
    envelope = {"version": "1.0", "marker_id": "marker-oakhaven-nfc-01"}

    receipt = svc.resolve_tap(
        profile_id="signed-out",
        event_id="evt-003",
        marker_payload=envelope,
    )
    assert receipt["outcome"] == "unauthorised"


def test_peer_handshake_lifecycle(test_spatial_svc: SpatialService):
    svc = test_spatial_svc
    challenge = svc.generate_handshake_challenge("peer-alpha-test", "ucore-spatial-service")
    nonce = challenge["nonce"]
    expiry = challenge["expiry"]

    # Valid response computation
    secret = b"test-secret-key-32-bytes"
    msg = f"1.0:peer-alpha-test:ucore-spatial-service:{nonce}:{int(expiry)}".encode("utf-8")
    sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()

    # 1. First verification should be accepted
    res = svc.verify_handshake_response(
        peer_id="peer-alpha-test",
        audience="ucore-spatial-service",
        nonce=nonce,
        expiry=expiry,
        signature=sig,
    )
    assert res["outcome"] == "accepted"

    # 2. Replay with same nonce must be denied
    res_replay = svc.verify_handshake_response(
        peer_id="peer-alpha-test",
        audience="ucore-spatial-service",
        nonce=nonce,
        expiry=expiry,
        signature=sig,
    )
    assert res_replay["outcome"] == "denied"
    assert res_replay["reason"] == "nonce_replayed"


def test_peer_handshake_expired(test_spatial_svc: SpatialService):
    svc = test_spatial_svc
    res = svc.verify_handshake_response(
        peer_id="peer-alpha-test",
        audience="ucore-spatial-service",
        nonce="nonce-expired",
        expiry=time.time() - 10,
        signature="fake",
    )
    assert res["outcome"] == "denied"
    assert res["reason"] == "expired"


def test_peer_handshake_revocation(test_spatial_svc: SpatialService):
    svc = test_spatial_svc
    svc.revoke_peer("peer-alpha-test")
    res = svc.verify_handshake_response(
        peer_id="peer-alpha-test",
        audience="ucore-spatial-service",
        nonce="nonce-revoked",
        expiry=time.time() + 60,
        signature="fake",
    )
    assert res["outcome"] == "denied"
    assert res["reason"] == "peer_revoked"


@pytest.mark.asyncio
async def test_tap_endpoint_requires_profile_and_valid_envelope():
    request = make_mocked_request("POST", "/api/spatial/tap")
    with patch("app.api.spatial.profile", side_effect=web.HTTPUnauthorized):
        with pytest.raises(web.HTTPUnauthorized):
            await handle_spatial_tap(request)

    with (
        patch("app.api.spatial.profile", return_value="profile-user-1"),
        patch.object(request, "json", return_value={"marker_envelope": []}),
    ):
        with pytest.raises(web.HTTPBadRequest):
            await handle_spatial_tap(request)
