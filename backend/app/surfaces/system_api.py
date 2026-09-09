"""System Surface — pages, services, and settings backend."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import ClientTimeout, web

from app.core.settings import settings
from app.services.settings_manager import get_settings_manager
from app.utils.config_loader import (
    load_service_registry,
    load_system_pages_registry,
)

log = logging.getLogger("ucore")


def _load_settings() -> dict:
    """Load system settings from disk."""
    return get_settings_manager().get_all()


def _save_settings(data: dict) -> None:
    """Persist system settings to disk."""
    get_settings_manager()._save(data)


# ─── S-Pages Registry ──────────────────────────────────────────────
# Lazily loaded from config; module-level defaults for quick access.

_S_PAGES_DEFAULT: list[dict] = [
    {"id": "S100", "title": "Page Not Found", "icon": "search_off"},
    {"id": "S101", "title": "Server Offline", "icon": "cloud_off"},
    {"id": "S300", "title": "Internal Server Error", "icon": "error"},
    {"id": "S310", "title": "Request Timed Out", "icon": "timer_off"},
    {"id": "S320", "title": "Access Restricted", "icon": "lock"},
    {"id": "S330", "title": "Configuration Missing", "icon": "settings"},
    {"id": "S340", "title": "Dependency Unavailable", "icon": "link_off"},
    {"id": "S600", "title": "Help and Recovery", "icon": "help"},
]


def _get_pages() -> list[dict]:
    """Load S-pages from config; fall back to built-in defaults."""
    return load_system_pages_registry()


# Backward-compatible module-level accessor (deprecated, kept for
# any code that may import S_PAGES directly).
S_PAGES: list[dict] = _S_PAGES_DEFAULT  # noqa: N816


def register_system_api_routes(app: web.Application) -> None:  # noqa: C901
    """Register system surface API routes."""

    # ── Pages ──────────────────────────────────────────────────
    async def handle_pages(request: web.Request) -> web.Response:
        s_pages = _get_pages()
        page_type = request.query.get("type", "all").lower()
        pages = s_pages if page_type in ("all", "s") else []
        return web.json_response(
            {
                "pages": pages,
                "count": len(pages),
                "s_count": len(s_pages),
                # Kept for backward compatibility with older frontend payload readers.
                "p_count": 0,
            }
        )

    # ── Settings (disk-persisted) ───────────────────────────────
    async def handle_get_settings(request: web.Request) -> web.Response:
        profile_id = request.headers.get("X-Udos-Profile") or request.query.get("profile") or "default"
        data = get_settings_manager().get_all(profile_id=profile_id)
        return web.json_response({"settings": data})

    async def handle_update_settings(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        scope = body.get("scope", "global")
        profile_id = request.headers.get("X-Udos-Profile") or request.query.get("profile") or body.get("profile_id") or "default"
        updated = get_settings_manager().update_scope(scope, body.get("values", {}), profile_id=profile_id)
        return web.json_response({"status": "ok", "settings": updated})

    async def handle_get_user_preferences(request: web.Request) -> web.Response:
        profile_id = request.headers.get("X-Udos-Profile") or request.query.get("profile") or "default"
        prefs = get_settings_manager().get_user_preferences(profile_id=profile_id)
        return web.json_response({"preferences": prefs})

    async def handle_update_user_preferences(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)
        values = body.get("preferences", body)
        if not isinstance(values, dict):
            return web.json_response({"error": "preferences must be an object"}, status=400)
        profile_id = request.headers.get("X-Udos-Profile") or request.query.get("profile") or body.get("profile_id") or "default"
        prefs = get_settings_manager().update_user_preferences(values, profile_id=profile_id)
        return web.json_response({"status": "ok", "preferences": prefs})

    # ── Services (dedicated system services endpoint) ──────────
    async def handle_system_services(request: web.Request) -> web.Response:  # noqa: C901
        """Probe known system services from shared registry."""
        service_defs, probe_cfg = load_service_registry()

        timeout = probe_cfg.get("timeout_seconds", 2)
        accept_status = probe_cfg.get("accept_status", 200)
        if not isinstance(accept_status, list):
            accept_status = [accept_status]

        def _build_result(
            svc_def: dict,
            status: str,
            status_code: int | None,
        ) -> dict[str, Any]:
            entry: dict[str, Any] = {
                "name": svc_def.get("id", svc_def.get("name", "")),
                "port": svc_def.get("port", 0),
                "type": svc_def.get("category", "system"),
                "description": svc_def.get("description", ""),
                "status": status,
            }
            if status_code is not None:
                entry["status_code"] = status_code
            return entry

        async def _probe(svc: dict) -> dict:
            host = svc.get("host", "localhost")
            port = svc.get("port", 0)
            health = svc.get("health", {})
            health_path = health.get("path", "/health")

            if not port:
                return _build_result(svc, "down", None)

            url = f"http://{host}:{port}{health_path}"
            try:
                async with aiohttp.ClientSession(
                    timeout=ClientTimeout(total=timeout),
                ) as session:
                    async with session.get(url) as resp:
                        status = "up" if resp.status in accept_status else "degraded"
                        return _build_result(svc, status, resp.status)
            except Exception:
                return _build_result(svc, "down", None)

        tasks = [_probe(s) for s in service_defs]
        results = list(await asyncio.gather(*tasks))

        up = sum(1 for s in results if s["status"] == "up")
        degraded = sum(1 for s in results if s["status"] == "degraded")
        down = sum(1 for s in results if s["status"] == "down")

        return web.json_response(
            {
                "services": results,
                "count": len(results),
                "up": up,
                "degraded": degraded,
                "down": down,
                "health_pct": round((up / max(len(results), 1)) * 100),
            }
        )

    app.router.add_get("/api/system/pages", handle_pages)
    app.router.add_get("/api/system/services", handle_system_services)
    app.router.add_get("/api/system/settings", handle_get_settings)
    app.router.add_post("/api/system/settings", handle_update_settings)
    app.router.add_get("/api/user/preferences", handle_get_user_preferences)
    app.router.add_post("/api/user/preferences", handle_update_user_preferences)
