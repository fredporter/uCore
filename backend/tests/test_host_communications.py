from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.host_api import (
    handle_imessage_intake,
    handle_mail_intake,
    handle_reminders_sync_outbound,
    handle_sync_status,
    register_host_routes,
    set_host_pim_service,
)
from app.services.host_pim import HostPIMService


@pytest.fixture(autouse=True)
def reset_pim():
    yield
    set_host_pim_service(None)


def test_intake_apple_mail(monkeypatch):
    monkeypatch.setattr(HostPIMService, "is_macos", lambda self: True)

    sample_mail = {
        "ok": True,
        "count": 2,
        "items": [
            {
                "id": "msg_001",
                "subject": "Sprint Alignment Update",
                "sender": "lead@zenos.local",
                "date": "2026-09-15T12:00:00Z",
                "read": False,
                "flagged": True,
                "flag_index": 0,
                "snippet": "Here is the summary of the continuous sprint plan.",
            },
            {
                "id": "msg_002",
                "subject": "Hardware delivery confirmed",
                "sender": "logistics@cmmint.org",
                "date": "2026-09-15T13:30:00Z",
                "read": False,
                "flagged": False,
                "flag_index": -1,
                "snippet": "USB keys prepared with Sonic Screwdriver ready for boot.",
            },
        ],
    }

    def mock_runner(cmd: list[str], timeout: float = 10.0, input_data: str | None = None) -> str:
        return json.dumps(sample_mail)

    svc = HostPIMService(runner=mock_runner)
    result = svc.intake_apple_mail(limit=10, unread_only=True)

    assert result["ok"] is True
    assert result["count"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["subject"] == "Sprint Alignment Update"
    assert result["items"][0]["flagged"] is True
    assert result["items"][1]["sender"] == "logistics@cmmint.org"


def test_intake_imessage(monkeypatch):
    monkeypatch.setattr(HostPIMService, "is_macos", lambda self: True)

    sample_chats = {
        "ok": True,
        "count": 2,
        "items": [
            {
                "id": "chat_001",
                "name": "Design Team",
                "last_message": "Lattice quantization specs are approved!",
                "date": "2026-09-15T14:15:00Z",
            },
            {
                "id": "chat_002",
                "name": "Alex",
                "last_message": "See you at the hackathon tomorrow.",
                "date": "2026-09-15T14:20:00Z",
            },
        ],
    }

    def mock_runner(cmd: list[str], timeout: float = 10.0, input_data: str | None = None) -> str:
        return json.dumps(sample_chats)

    svc = HostPIMService(runner=mock_runner)
    result = svc.intake_imessage(limit=5)

    assert result["ok"] is True
    assert result["count"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "Design Team"
    assert "Lattice" in result["items"][0]["last_message"]


def test_sync_apple_reminders_outbound(monkeypatch):
    monkeypatch.setattr(HostPIMService, "is_macos", lambda self: True)

    exported_calls = []

    def mock_export(title: str, notes: str = "", list_name: str | None = None, due_date: str | None = None):
        exported_calls.append({"title": title, "notes": notes, "list_name": list_name, "due_date": due_date})
        return {"ok": True, "title": title, "list": list_name or "Default", "app": "com.apple.reminders"}

    svc = HostPIMService()
    monkeypatch.setattr(svc, "export_to_apple_reminders", mock_export)

    tasks = [
        {
            "id": "task_1",
            "title": "Review Vector Lattice Spec",
            "description": "Ensure 1 dot = 4x4px invariant holds across all scales",
            "due": "2026-09-16T18:00:00Z",
            "binder": "GridCore",
        },
        {
            "id": "task_2",
            "name": "Sync Mesh Peers",
            "notes": "Verify UDP broadcast on port 53535",
            "due_date": "2026-09-17T09:00:00Z",
            "list": "uDos",
        },
    ]

    res = svc.sync_apple_reminders_outbound(tasks=tasks, default_list="uDos")

    assert res["ok"] is True
    assert res["synced_count"] == 2
    assert len(res["errors"]) == 0
    assert len(exported_calls) == 2
    assert exported_calls[0]["title"] == "Review Vector Lattice Spec"
    assert exported_calls[0]["list_name"] == "GridCore"
    assert exported_calls[0]["due_date"] == "2026-09-16T18:00:00Z"
    assert exported_calls[1]["title"] == "Sync Mesh Peers"
    assert exported_calls[1]["due_date"] == "2026-09-17T09:00:00Z"


def test_get_sync_status(monkeypatch):
    monkeypatch.setattr(HostPIMService, "is_macos", lambda self: True)

    def mock_probe():
        return {
            "os": "darwin",
            "host_native": {
                "reminders": {"available": True},
                "notes": {"available": True},
                "mail": {"available": True},
                "messages": {"available": True},
            },
        }

    svc = HostPIMService()
    monkeypatch.setattr(svc, "probe_capabilities", mock_probe)

    status = svc.get_sync_status()

    assert status["ok"] is True
    assert "apple_sync" in status
    assert status["apple_sync"]["reminders"]["available"] is True
    assert status["apple_sync"]["reminders"]["bidirectional"] is True
    assert status["apple_sync"]["mail"]["available"] is True
    assert "google_drive" in status
    assert "vault_path" in status["google_drive"]
    assert "bitchat_mesh" in status
    assert status["bitchat_mesh"]["active"] is True


@pytest.mark.asyncio
async def test_api_host_communication_routes(monkeypatch):
    monkeypatch.setattr(HostPIMService, "is_macos", lambda self: True)

    mock_svc = MagicMock(spec=HostPIMService)
    mock_svc.intake_apple_mail.return_value = {
        "ok": True,
        "count": 1,
        "items": [{"id": "m1", "subject": "Test Mail", "read": False}],
    }
    mock_svc.intake_imessage.return_value = {
        "ok": True,
        "count": 1,
        "items": [{"id": "c1", "name": "Test Chat", "last_message": "Hi"}],
    }
    mock_svc.sync_apple_reminders_outbound.return_value = {
        "ok": True,
        "synced_count": 1,
        "items": [{"id": "t1", "title": "Test Task", "status": "exported"}],
        "errors": [],
    }
    mock_svc.get_sync_status.return_value = {
        "ok": True,
        "platform": "darwin",
        "apple_sync": {"reminders": {"available": True}},
        "google_drive": {"configured": False},
        "bitchat_mesh": {"active": True, "online_peers": 1},
    }

    set_host_pim_service(mock_svc)

    app = web.Application()
    register_host_routes(app)

    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()

    try:
        # POST /api/host/mail/intake
        resp = await client.post("/api/host/mail/intake", json={"limit": 10, "unread_only": True})
        assert resp.status == 200
        data = await resp.json()
        assert data["ok"] is True
        assert data["count"] == 1
        mock_svc.intake_apple_mail.assert_called_once_with(limit=10, unread_only=True)

        # POST /api/host/imessage/intake
        resp = await client.post("/api/host/imessage/intake", json={"limit": 5})
        assert resp.status == 200
        data = await resp.json()
        assert data["ok"] is True
        assert data["count"] == 1
        mock_svc.intake_imessage.assert_called_once_with(limit=5)

        # POST /api/host/reminders/sync-outbound
        resp = await client.post(
            "/api/host/reminders/sync-outbound",
            json={"tasks": [{"id": "t1", "title": "Test Task"}], "default_list": "uDos"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["ok"] is True
        assert data["synced_count"] == 1

        # GET /api/host/sync/status
        resp = await client.get("/api/host/sync/status")
        assert resp.status == 200
        data = await resp.json()
        assert data["ok"] is True
        assert data["bitchat_mesh"]["online_peers"] == 1
    finally:
        await client.close()
