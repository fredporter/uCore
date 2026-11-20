"""Authenticated local assistant management; no arbitrary installer commands."""
from __future__ import annotations

import asyncio
import json

import httpx
from aiohttp import web

from app.api.connections_api import profile
from app.extensions.adapters.ucode_runtime_adapter import _resolve_callable
from app.services import assistant_profile
from app.services import local_assistant as service
from app.services.identity import get_full_identity


def active_assistant_profile(request, capability="edit_preferences"):
    identity = get_full_identity()
    owner = profile(request, identity=identity)
    capabilities = assistant_profile.assistant_capabilities(identity)
    if not capabilities[capability]:
        raise web.HTTPForbidden(text="Your active profile does not have this OK Assistant capability.")
    return owner, capabilities


async def settings(request):
    owner, capabilities = active_assistant_profile(request)
    value = assistant_profile.preferences(owner)
    if not capabilities["local_models"]:
        value.update(chat_mode="offline", model="")
    return web.json_response({"preferences": value, "capabilities": capabilities})


async def update_settings(request):
    owner, capabilities = active_assistant_profile(request)
    value = await read_body(request)
    mode = value.get("chat_mode")
    verbose = value.get("verbose")
    model = value.get("model")
    if mode not in ("offline", "ollama") or type(verbose) is not bool or not isinstance(model, str):
        raise web.HTTPBadRequest(text="Choose a chat mode, a reply detail setting and a model preference.")
    if (model or mode == "ollama") and not capabilities["local_models"]:
        raise web.HTTPForbidden(text="Your active profile can use offline input.")
    if len(model) > 161 or (model and not service.is_local_chat({"name": model})):
        raise web.HTTPBadRequest(text="Choose a local chat model.")
    value = {"chat_mode": mode, "verbose": verbose, "model": model}
    assistant_profile.save_preferences(owner, value)
    return web.json_response({"preferences": value, "capabilities": capabilities})


async def library(request):
    active_assistant_profile(request, "local_models")
    try:
        return web.json_response(await service.inventory())
    except (httpx.HTTPError, ValueError) as exc:
        return web.json_response({"online": False, "models": [], "library": [], "error": str(exc)}, status=503)


async def read_body(request):
    try:
        value = await request.json()
    except ValueError:
        raise web.HTTPBadRequest(text="Expected JSON") from None
    if not isinstance(value, dict):
        raise web.HTTPBadRequest(text="Expected an object")
    return value


async def pull(request):
    active_assistant_profile(request, "manage_models")
    value = await read_body(request)
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


async def model_snack(request):
    active_assistant_profile(request, "manage_models")
    value = await read_body(request)
    if value.get("confirm") is not True:
        raise web.HTTPBadRequest(text="Confirm the models to pull or update")
    response = web.StreamResponse(headers={
        "Content-Type": "application/x-ndjson", "Cache-Control": "no-store", "X-Accel-Buffering": "no",
    })
    await response.prepare(request)
    try:
        async for event in service.maintain_models(request.match_info["action"], value.get("models")):
            await response.write((json.dumps(event) + "\n").encode())
    except ConnectionResetError:
        return response
    except (httpx.HTTPError, ValueError, TimeoutError) as exc:
        await response.write((json.dumps({"error": str(exc)}) + "\n").encode())
    await response.write_eof()
    return response


async def roundtable(request):
    owner, _ = active_assistant_profile(request, "local_models")
    value = await read_body(request)
    model = value.get("model", assistant_profile.preferences(owner)["model"])
    try:
        return web.json_response(await service.roundtable(str(value.get("goal", "")), str(value.get("material", "")), str(model), str(value.get("purpose", "project"))))
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None
    except (httpx.HTTPError, TimeoutError) as exc:
        raise web.HTTPServiceUnavailable(text=f"Local assistant unavailable: {exc}") from None


async def chat(request):
    owner, capabilities = active_assistant_profile(request)
    value = await read_body(request)
    preferences = assistant_profile.preferences(owner)
    try:
        messages = service.validate_messages(value.get("messages"))
        if preferences["chat_mode"] == "ollama" and capabilities["local_models"]:
            return web.json_response(await service.chat(messages, preferences["model"]))
        reply = _resolve_callable("ucode_runtime.offline_assistant.reply")
        if reply is None:
            raise web.HTTPServiceUnavailable(text="The uCode offline input runtime is unavailable.")
        content = reply(messages[-1]["content"], verbose=preferences["verbose"])
        return web.json_response({"content": content, "mode": "offline", "model": None})
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None
    except (httpx.HTTPError, TimeoutError):
        raise web.HTTPServiceUnavailable(text="Ollama is unavailable. Check the local service.") from None


def register(app):
    app.router.add_get("/api/assistant/settings", settings)
    app.router.add_post("/api/assistant/settings", update_settings)
    app.router.add_get("/api/assistant/library", library)
    app.router.add_post("/api/assistant/models/pull", pull)
    app.router.add_post("/api/snacks/roundtable-models/{action}", model_snack)
    app.router.add_post("/api/assistant/roundtable", roundtable)
    app.router.add_post("/api/assistant/chat", chat)
