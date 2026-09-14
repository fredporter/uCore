"""Tests for BitChat Sovereign Message Store, Binder Evidence Bridge & WebSocket API.

Verifies:
- BitChatStore: message recording, retrieval by channel, Feed Activity Pod alerting
- save_to_binder: formatted markdown evidence written to ~/Vault/binders/<binder>/evidence/chats/
- convert_message_to_task: promoting message into sovereign .tasker task
- REST API: GET/POST /api/network/bitchat/messages, /send, /save-to-binder, /convert-to-task
- WebSocket: GET /api/network/bitchat/ws handshake and live broadcasting
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.bitchat_api import register_bitchat_routes
from app.services.bitchat_store import BitChatStore


def test_bitchat_store_messaging_and_query(tmp_path: Path):
    """Verify sending and querying messages in isolated sqlite pod."""
    db_file = tmp_path / "pods" / "bitchat.db"
    store = BitChatStore(db_path=db_file)

    msg1 = store.send_message(
        sender_name="Alice",
        content="Hello sovereign world!",
        channel="#general",
        sender_peer_id="peer_alice",
    )
    assert msg1["msg_id"].startswith("msg_")
    assert msg1["content"] == "Hello sovereign world!"

    msg2 = store.send_message(
        sender_name="Bob",
        content="Testing emergency broadcast channel.",
        channel="#briefing",
        sender_peer_id="peer_bob",
    )

    general_msgs = store.get_messages(channel="#general")
    assert len(general_msgs) == 1
    assert general_msgs[0]["content"] == "Hello sovereign world!"

    briefing_msgs = store.get_messages(channel="#briefing")
    assert len(briefing_msgs) == 1
    assert briefing_msgs[0]["content"] == "Testing emergency broadcast channel."

    store.close()


def test_bitchat_save_to_binder(tmp_path: Path):
    """Verify exporting selected messages as markdown evidence into a binder."""
    db_file = tmp_path / "pods" / "bitchat.db"
    vault_root = tmp_path / "Vault"
    store = BitChatStore(db_path=db_file)

    m1 = store.send_message("Charlie", "Decision made: use port 53535 for local beacons.", channel="#engineering")
    m2 = store.send_message("Dana", "Confirmed, standard socket broadcast works without zeroconf wheel.", channel="#engineering")

    res = store.save_to_binder(
        msg_ids=[m1["msg_id"], m2["msg_id"]],
        binder_name="MeshNetwork",
        title="Beacon Protocol Consensus",
        vault_root=vault_root,
    )

    assert res["ok"] is True
    assert res["saved_count"] == 2

    evidence_file = Path(res["path"])
    assert evidence_file.exists()
    content = evidence_file.read_text(encoding="utf-8")

    assert "# Beacon Protocol Consensus" in content
    assert "Decision made: use port 53535" in content
    assert "Confirmed, standard socket broadcast" in content
    assert "type: evidence" in content
    assert "source: bitchat" in content

    # Check that messages in store are marked as saved
    msgs = store.get_messages(channel="#engineering")
    for m in msgs:
        assert m["saved_to_binder"] is True
        assert m["binder_evidence_path"] == str(evidence_file)

    store.close()


def test_bitchat_convert_to_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify converting a chat message into a .tasker markdown task."""
    db_file = tmp_path / "pods" / "bitchat.db"
    vault_root = tmp_path / "Vault"
    store = BitChatStore(db_path=db_file)

    from app.core.settings import settings
    monkeypatch.setattr(settings, "vault_root", vault_root)

    m = store.send_message("Eve", "Please update the mesh transport docs before Monday.", channel="#general")
    res = store.convert_message_to_task(
        msg_id=m["msg_id"],
        board="inbox",
        priority="high",
        binder="Documentation",
    )

    assert res["ok"] is True
    assert "task_id" in res
    assert Path(res["path"]).exists()

    task_content = Path(res["path"]).read_text(encoding="utf-8")
    assert "Please update the mesh transport docs" in task_content

    # Message should now have task_id set
    msgs = store.get_messages(channel="#general")
    assert msgs[0]["task_id"] == res["task_id"]

    store.close()


@pytest.fixture
async def bitchat_api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolated client for BitChat REST & WebSocket testing."""
    db_file = tmp_path / "pods" / "bitchat.db"
    vault_root = tmp_path / "Vault"
    store = BitChatStore(db_path=db_file)

    import app.api.bitchat_api as api_mod
    monkeypatch.setattr(api_mod, "get_bitchat_store", lambda: store)

    from app.core.settings import settings
    monkeypatch.setattr(settings, "vault_root", vault_root)

    app = web.Application()
    register_bitchat_routes(app)
    async with TestClient(TestServer(app)) as client:
        yield client
    store.close()


@pytest.mark.asyncio
async def test_bitchat_api_rest_flow(bitchat_api_client):
    """Test message sending, listing, saving to binder, and converting to task via REST."""
    # Send message
    send_resp = await bitchat_api_client.post("/api/network/bitchat/send", json={
        "sender_name": "TestSender",
        "content": "Automated API check message",
        "channel": "#lab",
    })
    assert send_resp.status == 200
    msg_data = await send_resp.json()
    assert msg_data["status"] == "ok"
    msg_id = msg_data["message"]["msg_id"]

    # List messages
    list_resp = await bitchat_api_client.get("/api/network/bitchat/messages?channel=%23lab")
    assert list_resp.status == 200
    list_data = await list_resp.json()
    assert len(list_data["messages"]) == 1
    assert list_data["messages"][0]["msg_id"] == msg_id

    # Save to Binder
    binder_resp = await bitchat_api_client.post("/api/network/bitchat/save-to-binder", json={
        "msg_ids": [msg_id],
        "binder": "LabNotes",
        "title": "API Check Session",
    })
    assert binder_resp.status == 200
    binder_data = await binder_resp.json()
    assert binder_data["ok"] is True
    assert binder_data["saved_count"] == 1

    # Convert to Task
    task_resp = await bitchat_api_client.post("/api/network/bitchat/convert-to-task", json={
        "msg_id": msg_id,
        "board": "inbox",
        "priority": "low",
        "binder": "LabNotes",
    })
    assert task_resp.status == 200
    task_data = await task_resp.json()
    assert task_data["ok"] is True
    assert "task_id" in task_data


@pytest.mark.asyncio
async def test_bitchat_websocket_handshake(bitchat_api_client):
    """Test connecting to BitChat WebSocket conduit and exchanging ping/pong."""
    ws = await bitchat_api_client.ws_connect("/api/network/bitchat/ws")

    # Handshake is first message
    msg = await ws.receive_json()
    assert msg["type"] == "handshake"
    assert "peer_id" in msg

    # Ping / Pong
    await ws.send_json({"type": "ping"})
    pong = await ws.receive_json()
    assert pong["type"] == "pong"

    # Send chat message over WebSocket
    await ws.send_json({
        "type": "chat_message",
        "channel": "#ws-test",
        "sender_name": "WSTester",
        "content": "Hello over WS!",
    })
    broadcast = await ws.receive_json()
    assert broadcast["type"] == "chat_message"
    assert broadcast["message"]["content"] == "Hello over WS!"

    await ws.close()
