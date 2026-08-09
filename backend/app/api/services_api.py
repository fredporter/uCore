"""Unified Services API — server services + host tools + MCP servers.

Consolidated model (2026-08-08): Tools + MCP == Services. This endpoint
presents one merged, typed list so the UI renders infra processes, installed
host runtimes, and MCP servers side by side.

GET /api/services — merged services list with summary.
"""
from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

log = logging.getLogger("ucore.api.services")


async def handle_list_services(request: web.Request) -> web.Response:
    """GET /api/services — merged services + tools + MCP servers."""
    store = request.app.get("_server_store")
    services: list[dict[str, Any]] = []
    # 1. Server services — probed infra processes
    if store is not None:
        try:
            from app.surfaces.server import _probe_all
            for svc in await _probe_all(store):
                services.append({
                    "id": svc.get("name", ""),
                    "name": svc.get("name", ""),
                    "kind": "service",
                    "description": svc.get("description", ""),
                    "status": svc.get("status", "down"),
                    "port": svc.get("port", 0),
                    "type": svc.get("type", "system"),
                    "meta": {"uptime": svc.get("uptime", 0)},
                })
        except Exception as exc:
            log.warning("Server services gather failed: %s", exc)

    # 2. Host tools — installed runtimes (git, docker, node, python, ...)
    try:
        from app.tools.registry import list_tools as list_host_tools
        for tool in await list_host_tools():
            ti = tool.model_dump()
            services.append({
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
            })
    except Exception as exc:
        log.warning("Host tools gather failed: %s", exc)

    # 3. MCP servers
    try:
        from app.services.control_service import get_mcp_servers
        mcp_list = await get_mcp_servers()
        if not mcp_list:
            mcp_list = await _probe_known_mcp()
        for mcp in mcp_list:
            services.append({
                "id": mcp.get("name", ""),
                "name": mcp.get("name", ""),
                "kind": "mcp",
                "description": "MCP server",
                "status": "up" if mcp.get("online") else "down",
                "port": 0,
                "type": "mcp",
                "meta": {
                    "endpoint": mcp.get("endpoint", ""),
                    "tools": mcp.get("tools", 0),
                },
            })
    except Exception as exc:
        log.warning("MCP servers gather failed: %s", exc)

    statuses = [s["status"] for s in services]
    kinds: dict[str, int] = {}
    for s in services:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1

    return web.json_response({
        "services": services,
        "count": len(services),
        "summary": {
            "total": len(services),
            "up": statuses.count("up"),
            "degraded": statuses.count("degraded"),
            "down": statuses.count("down"),
        },
        "by_kind": kinds,
    })


def register_services_routes(app: web.Application) -> None:
    """Register unified Services API routes."""
    app.router.add_get("/api/services", handle_list_services)
    log.debug("Services API routes registered")


async def _probe_known_mcp() -> list[dict]:
    """Fallback MCP server probe when the tools registry is empty."""
    import asyncio

    from aiohttp import ClientSession, ClientTimeout

    known = [
        {"name": "snackbar", "url": "http://localhost:8484/health", "endpoint": "localhost:8484"},
        {"name": "hivemind", "url": "http://localhost:8490/health", "endpoint": "localhost:8490"},
        {"name": "vault-mcp", "url": "http://localhost:8765/health", "endpoint": "localhost:8765"},
        {"name": "gridsmith", "url": "http://localhost:8888/health", "endpoint": "localhost:8888"},
    ]

    async def _check(s: dict) -> dict:
        try:
            async with ClientSession(timeout=ClientTimeout(total=2)) as session:
                async with session.get(s["url"]) as resp:
                    online = resp.status < 400
        except Exception:
            online = False
        return {"name": s["name"], "online": online, "endpoint": s["endpoint"], "tools": 0}

    return list(await asyncio.gather(*[_check(s) for s in known]))
