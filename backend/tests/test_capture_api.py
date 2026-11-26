"""Capture admission: bounded, profile-scoped and idempotent."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import make_mocked_request

from app.api import capture_api
from app.core.settings import settings
from app.services import identity


def _request(body: dict):
    request = make_mocked_request("POST", "/api/host/capture")
    request.json = AsyncMock(return_value=body)
    return request


def _identity(role: str = "developer", authenticated: bool = True) -> dict:
    return {
        "authenticated": authenticated,
        "active_profile_id": role or "default",
        "active_profile": {"id": role, "role": role},
    }


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_root", tmp_path / "Vault")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.mark.asyncio
async def test_capture_writes_a_vault_file_and_receipt(monkeypatch):
    monkeypatch.setattr(identity, "get_full_identity", lambda: _identity())

    response = await capture_api.handle_capture(
        _request({"text": "Remember the milk", "request_id": "req-1", "title": "Note"})
    )

    payload = json.loads(response.text)
    assert response.status == 201
    assert payload["status"] == "completed"
    files = list((settings.vault_root / "Captures").glob("*.md"))
    assert len(files) == 1
    assert "Remember the milk" in files[0].read_text(encoding="utf-8")
    receipts = json.loads((settings.data_dir / "captures" / "receipts.json").read_text())
    assert receipts[payload["run_id"]]["path"] == payload["path"]


@pytest.mark.asyncio
async def test_replay_returns_the_same_receipt(monkeypatch):
    monkeypatch.setattr(identity, "get_full_identity", lambda: _identity())

    first = await capture_api.handle_capture(
        _request({"text": "One", "request_id": "req-2"})
    )
    second = await capture_api.handle_capture(
        _request({"text": "One", "request_id": "req-2"})
    )

    original, replay = json.loads(first.text), json.loads(second.text)
    assert original["run_id"] == replay["run_id"]
    assert replay["deduplicated"] is True
    assert len(list((settings.vault_root / "Captures").glob("*.md"))) == 1


@pytest.mark.asyncio
async def test_rejects_oversize_and_unsafe_request_ids(monkeypatch):
    monkeypatch.setattr(identity, "get_full_identity", lambda: _identity())

    oversize = await capture_api.handle_capture(
        _request({"text": "x" * (capture_api.MAX_CAPTURE_BYTES + 1), "request_id": "req-3"})
    )
    traversal = await capture_api.handle_capture(
        _request({"text": "note", "request_id": "../../escape"})
    )

    assert oversize.status == 400
    assert "exceeds" in json.loads(oversize.text)["error"]
    assert traversal.status == 400
    assert "request_id" in json.loads(traversal.text)["error"]
    assert not (settings.vault_root / "Captures").exists() or not list(
        (settings.vault_root / "Captures").glob("*")
    )


@pytest.mark.asyncio
async def test_guest_and_unauthenticated_callers_are_refused(monkeypatch):
    monkeypatch.setattr(identity, "get_full_identity", lambda: _identity("guest"))
    guest = await capture_api.handle_capture(
        _request({"text": "note", "request_id": "req-4"})
    )

    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: _identity("guest", authenticated=False),
    )
    anonymous = await capture_api.handle_capture(
        _request({"text": "note", "request_id": "req-5"})
    )

    assert guest.status == 403
    assert "Guest profiles" in json.loads(guest.text)["error"]
    assert anonymous.status == 403
    assert "Authenticate" in json.loads(anonymous.text)["error"]
