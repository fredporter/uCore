"""
Render API — human-readable skill output + SSE stream for real-time events.

POST /api/render         — convert JSON to markdown or html
GET  /api/render/stream  — SSE endpoint for real-time skill events
POST /api/render/event   — publish an event (internal use by skill runner)
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aiohttp import web

from app.services.render import render_markdown, render_html

log = logging.getLogger("ucore.render")

# ─── In-process event bus (subscribers keyed by asyncio.Queue) ──────
_subscribers: list[asyncio.Queue[dict[str, Any]]] = []


def _publish_local(event: dict[str, Any]) -> None:
    """Push event to all active SSE subscribers (fire-and-forget)."""
    dead: list[asyncio.Queue] = []
    for q in _subscribers:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.remove(q)


# ─── Handlers ────────────────────────────────────────────────────────


async def handle_render(request: web.Request) -> web.Response:
    """POST /api/render — convert skill JSON to markdown or html.

    Body: { "data": {...}, "format": "markdown" | "html" }
    Returns: { "output": "...", "format": "markdown" }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    data = body.get("data")
    if not isinstance(data, dict):
        return web.json_response({"error": "'data' must be an object"}, status=400)

    fmt = body.get("format", "markdown")
    if fmt == "html":
        output = render_html(data)
    else:
        output = render_markdown(data)

    return web.json_response({"output": output, "format": fmt})


async def handle_stream(request: web.Request) -> web.StreamResponse:
    """GET /api/render/stream — SSE endpoint for real-time skill events.

    Emits: text/event-stream with JSON data lines.
    Client reconnects automatically via EventSource.
    """
    resp = web.StreamResponse(
        status=200,
        reason="OK",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
    await resp.prepare(request)

    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=128)
    _subscribers.append(queue)

    # Send initial ping so the client knows it's connected
    await resp.write(b"event: connected\ndata: {}\n\n")

    try:
        while not request.transport.is_closing():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=25.0)
            except asyncio.TimeoutError:
                # Keepalive comment every 25 s
                await resp.write(b": keepalive\n\n")
                continue

            event_type = event.get("type", "event")
            payload = json.dumps(event.get("data", {}))
            await resp.write(
                f"event: {event_type}\ndata: {payload}\n\n".encode()
            )
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    finally:
        if queue in _subscribers:
            _subscribers.remove(queue)

    return resp


async def handle_publish_event(request: web.Request) -> web.Response:
    """POST /api/render/event — publish an event to all SSE subscribers.

    Body: { "type": "skill_complete", "data": {...} }
    Used by skill runner to broadcast results.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    event_type = body.get("type", "event")
    data = body.get("data", {})
    _publish_local({"type": event_type, "data": data})
    return web.json_response({"ok": True, "subscribers": len(_subscribers)})


def publish_event(event_type: str, data: dict[str, Any]) -> None:
    """Publish an event from Python code (e.g., after skill completes)."""
    _publish_local({"type": event_type, "data": data})
