"""BitChat & Decentralized Mesh Transport API.

Endpoints:
- GET  /api/network/mesh/peers          — List discovered LAN peers & services
- POST /api/network/mesh/announce       — Trigger local subnet UDP beacon announcement
- GET  /api/network/bitchat/messages    — Fetch recent chat history by channel
- POST /api/network/bitchat/send        — Send chat message, alert Feed Activity Pod, broadcast
- POST /api/network/bitchat/save-to-binder — Save selected messages as markdown evidence into binder
- POST /api/network/bitchat/convert-to-task — Promote message to sovereign task
- GET  /api/network/bitchat/ws          — Real-time WebSocket conduit
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Set

import aiohttp
from aiohttp import web

from app.services.bitchat_store import get_bitchat_store
from app.services.mesh_transport import get_mesh_discovery, get_mesh_registry

log = logging.getLogger("ucore.bitchat_api")

# Set of active WebSocket connections for real-time chat broadcasts
_active_websockets: Set[web.WebSocketResponse] = set()


async def broadcast_ws(event: Dict[str, Any]) -> None:
    """Broadcast an event dictionary to all active WebSocket clients."""
    if not _active_websockets:
        return
    payload_str = json.dumps(event)
    stale = []
    for ws in list(_active_websockets):
        try:
            if not ws.closed:
                await ws.send_str(payload_str)
            else:
                stale.append(ws)
        except Exception as exc:
            log.debug("WebSocket broadcast error: %s", exc)
            stale.append(ws)

    for ws in stale:
        _active_websockets.discard(ws)


async def handle_get_peers(request: web.Request) -> web.Response:
    """GET /api/network/mesh/peers — Get discovered mesh peers."""
    service_type = request.query.get("service_type")
    include_stale = request.query.get("include_stale", "false").lower() in ("true", "1")
    registry = get_mesh_registry()
    peers = registry.get_peers(service_type=service_type, include_stale=include_stale)
    return web.json_response({
        "status": "ok",
        "local_peer_id": registry.local_peer_id,
        "local_node_name": registry.local_node_name,
        "peers": peers,
    })


async def handle_mesh_announce(request: web.Request) -> web.Response:
    """POST /api/network/mesh/announce — Send broadcast beacon to local subnet."""
    discovery = get_mesh_discovery()
    success = discovery.send_broadcast_beacon()
    return web.json_response({
        "status": "ok",
        "announced": success,
        "peer_id": discovery.registry.local_peer_id,
        "node_name": discovery.registry.local_node_name,
    })


async def handle_get_messages(request: web.Request) -> web.Response:
    """GET /api/network/bitchat/messages — Retrieve messages for a channel."""
    channel = request.query.get("channel", "#general")
    limit_str = request.query.get("limit", "50")
    since = request.query.get("since")
    try:
        limit = int(limit_str)
    except ValueError:
        limit = 50

    store = get_bitchat_store()
    messages = store.get_messages(channel=channel, limit=limit, since=since)
    return web.json_response({
        "status": "ok",
        "channel": channel,
        "messages": messages,
    })


async def handle_send_message(request: web.Request) -> web.Response:
    """POST /api/network/bitchat/send — Record message and broadcast to peers."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    sender_name = data.get("sender_name", "").strip() or "Anonymous"
    content = data.get("content", "").strip()
    if not content:
        return web.json_response({"error": "Content cannot be empty"}, status=400)

    channel = data.get("channel", "#general").strip() or "#general"
    sender_peer_id = data.get("sender_peer_id")
    recipient_id = data.get("recipient_id")
    metadata = data.get("metadata", {})

    store = get_bitchat_store()
    record = store.send_message(
        sender_name=sender_name,
        content=content,
        channel=channel,
        sender_peer_id=sender_peer_id,
        recipient_id=recipient_id,
        metadata=metadata,
    )

    # Real-time WebSocket broadcast
    await broadcast_ws({
        "type": "chat_message",
        "channel": channel,
        "message": record,
    })

    return web.json_response({
        "status": "ok",
        "message": record,
    })


async def handle_save_to_binder(request: web.Request) -> web.Response:
    """POST /api/network/bitchat/save-to-binder — Save messages as markdown evidence."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    msg_ids = data.get("msg_ids")
    if not msg_ids or not isinstance(msg_ids, list):
        return web.json_response({"error": "msg_ids list is required"}, status=400)

    binder_name = data.get("binder", "").strip() or "Sandbox"
    title = data.get("title", "").strip() or "Discussion Evidence"

    store = get_bitchat_store()
    result = store.save_to_binder(
        msg_ids=msg_ids,
        binder_name=binder_name,
        title=title,
    )

    if not result.get("ok"):
        return web.json_response(result, status=400)

    return web.json_response(result)


async def handle_convert_to_task(request: web.Request) -> web.Response:
    """POST /api/network/bitchat/convert-to-task — Promote message to sovereign task."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    msg_id = data.get("msg_id", "").strip()
    if not msg_id:
        return web.json_response({"error": "msg_id is required"}, status=400)

    board = str(data.get("board") or "inbox")
    priority = str(data.get("priority") or "medium")
    binder = str(data.get("binder") or "Sandbox")
    due_date = data.get("due_date")
    sync_apple_reminders = bool(data.get("sync_apple_reminders", False))

    store = get_bitchat_store()
    result = store.convert_message_to_task(
        msg_id=msg_id,
        board=board,
        priority=priority,
        binder=binder,
        due_date=due_date,
        sync_apple_reminders=sync_apple_reminders,
    )

    if not result.get("ok"):
        return web.json_response(result, status=404 if "not found" in result.get("error", "").lower() else 400)

    return web.json_response(result)


async def handle_bitchat_ws(request: web.Request) -> web.WebSocketResponse:
    """GET /api/network/bitchat/ws — WebSocket connection for real-time BitChat."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    _active_websockets.add(ws)
    log.info("BitChat WebSocket connected (total: %d)", len(_active_websockets))

    # Send initial welcome / handshake
    registry = get_mesh_registry()
    await ws.send_str(json.dumps({
        "type": "handshake",
        "peer_id": registry.local_peer_id,
        "node_name": registry.local_node_name,
        "timestamp": asyncio.get_event_loop().time(),
    }))

    store = get_bitchat_store()

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                except Exception:
                    continue

                msg_type = payload.get("type")
                if msg_type == "ping":
                    await ws.send_str(json.dumps({"type": "pong"}))
                elif msg_type in ("chat_message", "send_message"):
                    content = str(payload.get("content") or "").strip()
                    if content:
                        sender_name = str(payload.get("sender_name") or registry.local_node_name)
                        channel = str(payload.get("channel") or "#general")
                        record = store.send_message(
                            sender_name=sender_name,
                            content=content,
                            channel=channel,
                            sender_peer_id=registry.local_peer_id,
                            recipient_id=payload.get("recipient_id"),
                            metadata=payload.get("metadata") or {},
                        )
                        await broadcast_ws({
                            "type": "chat_message",
                            "channel": channel,
                            "message": record,
                        })
                elif msg_type == "announce":
                    discovery = get_mesh_discovery()
                    discovery.send_broadcast_beacon()
                    peers = registry.get_peers()
                    await ws.send_str(json.dumps({
                        "type": "peer_list",
                        "peers": peers,
                    }))
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                break
    finally:
        _active_websockets.discard(ws)
        log.info("BitChat WebSocket disconnected (remaining: %d)", len(_active_websockets))

    return ws


def register_bitchat_routes(app: web.Application) -> None:
    """Register BitChat & Mesh discovery routes."""
    app.router.add_get("/api/network/mesh/peers", handle_get_peers)
    app.router.add_post("/api/network/mesh/announce", handle_mesh_announce)
    app.router.add_get("/api/network/bitchat/messages", handle_get_messages)
    app.router.add_post("/api/network/bitchat/send", handle_send_message)
    app.router.add_post("/api/network/bitchat/save-to-binder", handle_save_to_binder)
    app.router.add_post("/api/network/bitchat/convert-to-task", handle_convert_to_task)
    app.router.add_get("/api/network/bitchat/ws", handle_bitchat_ws)
