"""Unified Services API — server services and host tools.

This endpoint presents one typed list so the UI renders infrastructure
processes and installed host runtimes side by side. The local stdio MCP gateway
is launched by external clients and is not an internal service daemon.

GET /api/services — merged services list with summary.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.services")


async def handle_list_services(request: web.Request) -> web.Response:
    """GET /api/services — merged services and host tools."""
    store = request.app.get("_server_store")
    services: list[dict[str, Any]] = []
    # 1. Server services — probed infra processes
    if store is not None:
        try:
            from app.surfaces.server import _probe_all

            for svc in await _probe_all(store):
                services.append(
                    {
                        "id": svc.get("name", ""),
                        "name": svc.get("name", ""),
                        "kind": "service",
                        "description": svc.get("description", ""),
                        "status": svc.get("status", "down"),
                        "port": svc.get("port", 0),
                        "type": svc.get("type", "system"),
                        "actions": svc.get("recoveryActions", []),
                        "meta": {"uptime": svc.get("uptime", 0)},
                    }
                )
        except Exception as exc:
            log.warning("Server services gather failed: %s", exc)

    # 2. Host tools — installed runtimes (git, docker, node, python, ...)
    try:
        from app.tools.registry import list_tools as list_host_tools

        for tool in await list_host_tools():
            ti = tool.model_dump()
            services.append(
                {
                    "id": ti.get("id", ""),
                    "name": ti.get("name", ti.get("id", "")),
                    "kind": "tool",
                    "description": ti.get("description", ""),
                    "status": "up" if ti.get("installed") else "down",
                    "port": 0,
                    "type": "host",
                    "meta": {
                        "installed": ti.get("installed"),
                        "version": ti.get("version", ""),
                        "running": ti.get("running"),
                    },
                }
            )
    except Exception as exc:
        log.warning("Host tools gather failed: %s", exc)

    statuses = [s["status"] for s in services]
    kinds: dict[str, int] = {}
    for s in services:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1

    return web.json_response(
        {
            "services": services,
            "count": len(services),
            "summary": {
                "total": len(services),
                "up": statuses.count("up"),
                "degraded": statuses.count("degraded"),
                "down": statuses.count("down"),
            },
            "by_kind": kinds,
        }
    )


def register_services_routes(app: web.Application) -> None:
    """Register unified Services API routes."""
    app.router.add_get("/api/services", handle_list_services)
    log.debug("Services API routes registered")
