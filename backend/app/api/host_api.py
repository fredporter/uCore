"""Host PIM and OS automation API endpoints for uCore.

Provides endpoints for:
- Host capability discovery (/api/host/capabilities)
- Active Safari tab discovery and research intake (/api/host/safari/*)
- Apple Notes export (/api/host/notes/export)
- Apple Reminders export (/api/host/reminders/export)
- Host notification and speech (/api/host/notify, /api/host/say)
"""

from __future__ import annotations

import logging

from aiohttp import web

from app.services.host_pim import HostPIMService

log = logging.getLogger("ucore.api.host")

_pim_service: HostPIMService | None = None


def get_host_pim_service() -> HostPIMService:
    global _pim_service
    if _pim_service is None:
        _pim_service = HostPIMService()
    return _pim_service


def set_host_pim_service(service: HostPIMService | None) -> None:
    global _pim_service
    _pim_service = service


async def handle_host_capabilities(request: web.Request) -> web.Response:
    """GET /api/host/capabilities — Discover host OS capabilities non-invasively."""
    svc = get_host_pim_service()
    caps = svc.probe_capabilities()
    return web.json_response(caps)


async def handle_safari_active(request: web.Request) -> web.Response:
    """GET /api/host/safari/active — Query the URL and title of Safari's active tab."""
    svc = get_host_pim_service()
    data = svc.get_active_safari_tab()
    status = 200 if data.get("ok") else (200 if not data.get("running") else 500)
    return web.json_response(data, status=status)


async def handle_safari_intake(request: web.Request) -> web.Response:
    """POST /api/host/safari/intake — Ingest active Safari tab into research / feed."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    notes = body.get("notes", "")
    svc = get_host_pim_service()
    result = svc.intake_safari_to_research(notes=notes)

    if not result.get("ok"):
        return web.json_response(result, status=400)

    # Optionally ingest into feed if available
    try:
        from app.services.feed_store import FeedServer
        feed = FeedServer()
        card = result.get("card", {})
        await feed.ingest_activity(
            source="safari",
            type="research-card",
            title=card.get("title", ""),
            content=card.get("summary", ""),
            url=card.get("url", ""),
            importance=0.6,
            metadata=card,
        )
    except Exception as exc:
        log.debug("Could not record Safari intake to feed: %s", exc)

    return web.json_response(result)


async def handle_notes_export(request: web.Request) -> web.Response:
    """POST /api/host/notes/export — Export Markdown content to Apple Notes."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON body"}, status=400)

    title = body.get("title", "").strip()
    if not title:
        return web.json_response({"ok": False, "error": "title is required"}, status=400)

    body_md = body.get("body", "")
    folder = body.get("folder")

    svc = get_host_pim_service()
    res = svc.export_to_apple_notes(title=title, body_markdown=body_md, folder=folder)
    return web.json_response(res, status=200 if res.get("ok") else 500)


async def handle_reminders_export(request: web.Request) -> web.Response:
    """POST /api/host/reminders/export — Export a task to Apple Reminders."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON body"}, status=400)

    title = body.get("title", "").strip()
    if not title:
        return web.json_response({"ok": False, "error": "title is required"}, status=400)

    notes = body.get("notes", "")
    list_name = body.get("list_name")
    due_date = body.get("due_date")

    svc = get_host_pim_service()
    res = svc.export_to_apple_reminders(
        title=title, notes=notes, list_name=list_name, due_date=due_date
    )
    return web.json_response(res, status=200 if res.get("ok") else 500)


async def handle_reminders_intake(request: web.Request) -> web.Response:
    """GET /api/host/reminders/intake — Query reminders from Apple Reminders."""
    list_name = request.query.get("list")
    limit_str = request.query.get("limit", "25")
    completed_str = request.query.get("completed", "false").lower()
    completed = completed_str in ("true", "1", "yes")

    try:
        limit = int(limit_str)
    except ValueError:
        limit = 25

    svc = get_host_pim_service()
    res = svc.intake_apple_reminders(list_name=list_name, limit=limit, completed=completed)
    status = 200 if res.get("ok") else 500
    return web.json_response(res, status=status)


async def handle_notes_intake(request: web.Request) -> web.Response:
    """GET /api/host/notes/intake — Query notes from Apple Notes."""
    folder = request.query.get("folder")
    limit_str = request.query.get("limit", "15")
    search = request.query.get("search")

    try:
        limit = int(limit_str)
    except ValueError:
        limit = 15

    svc = get_host_pim_service()
    res = svc.intake_apple_notes(folder=folder, limit=limit, search=search)
    status = 200 if res.get("ok") else 500
    return web.json_response(res, status=status)


async def handle_host_notify(request: web.Request) -> web.Response:
    """POST /api/host/notify — Dispatch a native host notification."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON body"}, status=400)

    title = body.get("title", "uCore").strip()
    message = body.get("message", "").strip()
    subtitle = body.get("subtitle", "")

    if not message:
        return web.json_response({"ok": False, "error": "message is required"}, status=400)

    svc = get_host_pim_service()
    res = svc.notify(title=title, message=message, subtitle=subtitle)
    return web.json_response(res, status=200 if res.get("ok") else 500)


async def handle_host_say(request: web.Request) -> web.Response:
    """POST /api/host/say — Host OS speech synthesis."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON body"}, status=400)

    text = body.get("text", "").strip()
    voice = body.get("voice")

    if not text:
        return web.json_response({"ok": False, "error": "text is required"}, status=400)

    svc = get_host_pim_service()
    res = svc.say(text=text, voice=voice)
    return web.json_response(res, status=200 if res.get("ok") else 500)


def register_host_routes(app: web.Application) -> None:
    """Register all host PIM and automation routes."""
    app.router.add_get("/api/host/capabilities", handle_host_capabilities)
    app.router.add_get("/api/host/safari/active", handle_safari_active)
    app.router.add_post("/api/host/safari/intake", handle_safari_intake)
    app.router.add_post("/api/host/notes/export", handle_notes_export)
    app.router.add_get("/api/host/notes/intake", handle_notes_intake)
    app.router.add_post("/api/host/reminders/export", handle_reminders_export)
    app.router.add_get("/api/host/reminders/intake", handle_reminders_intake)
    app.router.add_post("/api/host/notify", handle_host_notify)
    app.router.add_post("/api/host/say", handle_host_say)
    log.info("Host PIM routes registered: capabilities, safari, notes, reminders, notify, say")

