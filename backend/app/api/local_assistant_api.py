"""Authenticated local assistant management; no arbitrary installer commands."""
from __future__ import annotations

import asyncio
import json

import httpx
from aiohttp import web

from app.api.connections_api import profile
from app.services import local_assistant as service


async def library(request):
    profile(request)
    try:
        return web.json_response(await service.inventory())
    except (httpx.HTTPError, ValueError) as exc:
        return web.json_response({"online": False, "models": [], "library": [], "error": str(exc)}, status=503)


async def body(request):
    profile(request)
    value = await request.json()
    if not isinstance(value, dict):
        raise web.HTTPBadRequest(text="Expected an object")
    return value


async def pull(request):
    value = await body(request)
    name = value.get("model")
    if value.get("confirm") is not True:
        raise web.HTTPBadRequest(text="Choose and confirm a curated model download first")
    try:
        service.validate_model_reference(name)
        service.local_url()
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None
    response = web.StreamResponse(headers={"Content-Type": "application/x-ndjson", "Cache-Control": "no-store", "X-Accel-Buffering": "no"})
    await response.prepare(request)
    try:
        async for line in service.pull_events(name):
            await response.write((line + "\n").encode())
    except (httpx.HTTPError, ValueError, TimeoutError) as exc:
        await response.write((json.dumps({"error": str(exc)}) + "\n").encode())
    except (ConnectionResetError, asyncio.CancelledError):
        # Disconnect stops this observer; Ollama may retain partial blobs.
        raise
    await response.write_eof()
    return response


async def roundtable(request):
    value = await body(request)
    try:
        return web.json_response(await service.roundtable(str(value.get("goal", "")), str(value.get("material", "")), str(value.get("model", "")), str(value.get("purpose", "project"))))
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None
    except (httpx.HTTPError, TimeoutError) as exc:
        raise web.HTTPServiceUnavailable(text=f"Local assistant unavailable: {exc}") from None


def register(app):
    app.router.add_get("/api/assistant/library", library)
    app.router.add_post("/api/assistant/models/pull", pull)
    app.router.add_post("/api/assistant/roundtable", roundtable)
