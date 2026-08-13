"""Diagnostics and self-healing routes."""
from __future__ import annotations

import json

from aiohttp import web


async def diagnostics_handler(request: web.Request) -> web.Response:
    """GET /api/diagnostics — system diagnostics."""
    try:
        from app.services.process_manager import get_process_manager

        pm = get_process_manager()
        diag = pm.get_system_diagnostics()
        diag_str = json.dumps(diag, default=str)
        return web.Response(
            text=diag_str, content_type="application/json",
        )
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def ports_handler(request: web.Request) -> web.Response:
    """GET /api/diagnostics/ports — port conflict report."""
    try:
        from app.services.process_manager import get_process_manager

        pm = get_process_manager()
        report = pm.get_port_conflict_report()
        return web.json_response(report)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def register(app: web.Application) -> None:
    app.router.add_get("/api/diagnostics", diagnostics_handler)
    app.router.add_get("/api/diagnostics/ports", ports_handler)
