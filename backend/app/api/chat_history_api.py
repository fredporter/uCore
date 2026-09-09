"""Per-install and per-profile chat history persistence for the single global chat widget."""
from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web

from app.core.settings import settings
from app.services.identity import get_full_identity

_MAX_CONVERSATIONS = 100
_MAX_BYTES = 2_000_000


def _history_file(profile_id: str | None = None) -> Path:
    identity = get_full_identity()
    owner = str(identity.get("user_id") or identity.get("install_id") or "local")
    safe_owner = "".join(char for char in owner if char.isalnum() or char in "-_")[:80] or "local"
    if not profile_id:
        profile_id = str(identity.get("active_profile_id") or "default")
    safe_profile = "".join(char for char in profile_id if char.isalnum() or char in "-_")[:40] or "default"

    primary = settings.data_dir / "chat" / f"{safe_owner}_{safe_profile}.json"
    if not primary.exists() and safe_profile == "default":
        legacy = settings.data_dir / "chat" / f"{safe_owner}.json"
        if legacy.exists():
            return legacy
    return primary


def _read_history(profile_id: str | None = None) -> list[dict]:
    try:
        try:
            target = _history_file(profile_id)
        except TypeError:
            target = _history_file()  # Support legacy 0-arg mocks
        value = json.loads(target.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _write_history(conversations: list[dict], profile_id: str | None = None) -> None:
    try:
        target = _history_file(profile_id)
    except TypeError:
        target = _history_file()  # Support legacy 0-arg mocks
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(conversations[-_MAX_CONVERSATIONS:], indent=2), encoding="utf-8")
    temp.replace(target)


async def handle_get_chat_history(request: web.Request) -> web.Response:
    identity = get_full_identity()
    profile_id = request.headers.get("X-Udos-Profile") or request.query.get("profile") or identity.get("active_profile_id")
    if not identity.get("authenticated") and not request.headers.get("X-Udos-Profile"):
        return web.json_response({"conversations": []})
    return web.json_response({"conversations": _read_history(profile_id)})


async def handle_save_chat_history(request: web.Request) -> web.Response:
    if request.content_length and request.content_length > _MAX_BYTES:
        return web.json_response({"error": "Chat history payload is too large"}, status=413)
    try:
        raw = bytearray()
        async for chunk in request.content.iter_chunked(64 * 1024):
            raw.extend(chunk)
            if len(raw) > _MAX_BYTES:
                return web.json_response({"error": "Chat history payload is too large"}, status=413)
        body = json.loads(raw)
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "JSON body must be an object"}, status=400)
    conversations = body.get("conversations")
    if not isinstance(conversations, list) or any(not isinstance(item, dict) for item in conversations):
        return web.json_response({"error": "conversations must be an array of objects"}, status=400)

    identity = get_full_identity()
    if not identity.get("authenticated") and not request.headers.get("X-Udos-Profile"):
        return web.json_response({"error": "Authentication required to persist chat history"}, status=401)

    profile_id = request.headers.get("X-Udos-Profile") or request.query.get("profile") or identity.get("active_profile_id")
    _write_history(conversations, profile_id=profile_id)
    return web.json_response({"status": "ok", "count": min(len(conversations), _MAX_CONVERSATIONS)})


async def handle_clear_chat_history(request: web.Request) -> web.Response:
    identity = get_full_identity()
    if not identity.get("authenticated") and not request.headers.get("X-Udos-Profile"):
        return web.json_response({"error": "Authentication required to clear chat history"}, status=401)
    profile_id = request.headers.get("X-Udos-Profile") or request.query.get("profile") or identity.get("active_profile_id")
    _write_history([], profile_id=profile_id)
    return web.json_response({"status": "ok"})


def register_chat_history_routes(app: web.Application) -> None:
    app.router.add_get("/api/chat/history", handle_get_chat_history)
    app.router.add_post("/api/chat/history", handle_save_chat_history)
    app.router.add_delete("/api/chat/history", handle_clear_chat_history)
