"""Executables API — unified Skills + Snack plugins.

GET  /api/executables            — list all executables (skills + snacks)
GET  /api/executables/{exe_id}   — get a single executable
POST /api/executables/{exe_id}/run — run an executable (body: {action?, ...})
"""
from __future__ import annotations

import logging

from aiohttp import web

from app.services.executable_registry import (
    get_executable,
    list_executables,
    run_executable,
)

log = logging.getLogger("ucore.api.executables")


async def handle_list_executables(request: web.Request) -> web.Response:
    """GET /api/executables — merged skills + snack plugins."""
    return web.json_response({"executables": list_executables()})


async def handle_get_executable(request: web.Request) -> web.Response:
    """GET /api/executables/{exe_id} — single executable detail."""
    exe_id = request.match_info["exe_id"]
    exe = get_executable(exe_id)
    if not exe:
        return web.json_response(
            {"error": f"Executable '{exe_id}' not found"}, status=404,
        )
    return web.json_response(exe)


async def handle_run_executable(request: web.Request) -> web.Response:
    """POST /api/executables/{exe_id}/run — run a skill or snack plugin."""
    exe_id = request.match_info["exe_id"]
    try:
        body = await request.json()
    except Exception:
        body = {}

    action = body.get("action")
    kwargs = {key: value for key, value in body.items() if key != "action"}
    result = await run_executable(exe_id, action=action, **kwargs)
    return web.json_response(result)


def register_executables_routes(app: web.Application) -> None:
    """Register Executables API routes."""
    app.router.add_get("/api/executables", handle_list_executables)
    app.router.add_get("/api/executables/{exe_id}", handle_get_executable)
    app.router.add_post(
        "/api/executables/{exe_id}/run", handle_run_executable,
    )
    log.debug("Executables API routes registered")
