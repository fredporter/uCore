"""Conversation transport; mutations never run on a reconnecting GET."""
import asyncio
import json

from aiohttp import web

from app.core.settings import settings
from app.services.developer_chat import get_developer_chat


async def submit(request):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("Expected an object")
        return web.json_response(get_developer_chat().submit(body), status=202)
    except PermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)
    except (ValueError, TypeError, KeyError, FileNotFoundError) as exc:
        return web.json_response({"error": str(exc)}, status=400)


async def conversations(request):
    chat = get_developer_chat()
    return web.json_response({"conversations": [
        {key: record[key] for key in ("id", "title", "repository", "status")}
        for record in reversed(list(chat.records.values()))]})


async def conversation(request):
    try:
        return web.json_response(get_developer_chat().public(request.match_info["conversation_id"]))
    except KeyError as exc:
        return web.json_response({"error": str(exc)}, status=404)


async def cancel(request):
    try:
        await get_developer_chat().cancel(request.match_info["conversation_id"])
        return await conversation(request)
    except KeyError as exc:
        return web.json_response({"error": str(exc)}, status=404)


async def delete(request):
    try:
        await get_developer_chat().delete(request.match_info["conversation_id"])
        return web.json_response({"deleted": True})
    except KeyError as exc:
        return web.json_response({"error": str(exc)}, status=404)


async def events(request):
    chat = get_developer_chat()
    ident = request.match_info["conversation_id"]
    try:
        chat.get(ident)
    except KeyError as exc:
        return web.json_response({"error": str(exc)}, status=404)
    response = web.StreamResponse(headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"})
    # Streaming headers are committed before the ordinary middleware returns.
    if settings.enable_cors:
        response.headers["Access-Control-Allow-Origin"] = "*"
    await response.prepare(request)
    previous = ""
    try:
        for _ in range(120):
            snapshot = chat.public(ident)
            encoded = json.dumps(snapshot)
            if encoded != previous:
                await response.write(f"data: {encoded}\n\n".encode())
                previous = encoded
            else:
                await response.write(b": heartbeat\n\n")
            await asyncio.sleep(0.5)
    except (ConnectionResetError, asyncio.CancelledError, KeyError):
        pass
    return response


def register(app):
    root = "/api/developer/conversations"
    app.router.add_get(root, conversations)
    app.router.add_get(root + "/{conversation_id}", conversation)
    app.router.add_get(root + "/{conversation_id}/events", events)
    app.router.add_post(root + "/{conversation_id}/cancel", cancel)
    app.router.add_delete(root + "/{conversation_id}", delete)
