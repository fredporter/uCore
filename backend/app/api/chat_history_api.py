"""Per-install chat history persistence for the single global chat widget."""
from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web

from app.core.settings import settings
from app.services.identity import get_full_identity

_MAX_CONVERSATIONS = 100
_MAX_BYTES = 2_000_000


def _history_file() -> Path:
    identity = get_full_identity()
    owner = str(identity.get("user_id") or identity.get("install_id") or "local")
    safe_owner = "".join(char for char in owner if char.isalnum() or char in "-_")[:80] or "local"
    return settings.data_dir / "chat" / f"{safe_owner}.json"


def _read_history() -> list[dict]:
    try:
        value = json.loads(_history_file().read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _write_history(conversations: list[dict]) -> None:
    target = _history_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(conversations[-_MAX_CONVERSATIONS:], indent=2), encoding="utf-8")


async def handle_get_chat_history(_request: web.Request) -> web.Response:
    return web.json_response({"conversations": _read_history()})


async def handle_save_chat_history(request: web.Request) -> web.Response:
    if request.content_length and request.content_length > _MAX_BYTES:
        return web.json_response({"error": "Chat history payload is too large"}, status=413)
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    conversations = body.get("conversations")
    if not isinstance(conversations, list) or any(not isinstance(item, dict) for item in conversations):
        return web.json_response({"error": "conversations must be an array of objects"}, status=400)
    _write_history(conversations)
    return web.json_response({"status": "ok", "count": min(len(conversations), _MAX_CONVERSATIONS)})


async def handle_clear_chat_history(_request: web.Request) -> web.Response:
    _write_history([])
    return web.json_response({"status": "ok"})


def register_chat_history_routes(app: web.Application) -> None:
    app.router.add_get("/api/chat/history", handle_get_chat_history)
    app.router.add_post("/api/chat/history", handle_save_chat_history)
    app.router.add_delete("/api/chat/history", handle_clear_chat_history)
