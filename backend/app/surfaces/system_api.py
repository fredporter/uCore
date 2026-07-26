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

from app.utils.config_loader import (
    load_service_registry,
    load_system_pages_registry,
)

log = logging.getLogger("ucore")

# ─── Settings Store Path ──────────────────────────────────────────

_SETTINGS_STORE_DIR = Path(
    os.environ.get(
        "UCORE_DATA_DIR",
        os.path.expanduser("~/.ucore/data"),
    ),
)
_SETTINGS_STORE_FILE = _SETTINGS_STORE_DIR / "system_settings.json"


def _ensure_settings_store() -> None:
    """Ensure the data directory and default settings store exist."""
    _SETTINGS_STORE_DIR.mkdir(parents=True, exist_ok=True)
    if not _SETTINGS_STORE_FILE.exists():
        defaults = {
            "global": {
                "theme": "dark",
                "fontSize": 16,
                "palette": "default",
            },
            "user": {
                "displayName": "uDos Developer",
                "email": "",
                "defaultModel": "Llama 3.2",
            },
        }
        _SETTINGS_STORE_FILE.write_text(json.dumps(defaults, indent=2))


def _load_settings() -> dict:
    """Load system settings from disk."""
    _ensure_settings_store()
    try:
        return json.loads(_SETTINGS_STORE_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_settings(data: dict) -> None:
    """Persist system settings to disk."""
    _ensure_settings_store()
    _SETTINGS_STORE_FILE.write_text(json.dumps(data, indent=2))


# ─── S-Pages Registry ──────────────────────────────────────────────
# Lazily loaded from config; module-level defaults for quick access.

_S_PAGES_DEFAULT: list[dict] = [
    {"id": "S100", "title": "Tool Builder", "icon": "build"},
    {"id": "S101", "title": "Story Builder", "icon": "auto_stories"},
    {"id": "S300", "title": "Workflow Builder", "icon": "account_tree"},
    {"id": "S310", "title": "Clipboard Orchestration", "icon": "content_paste"},
    {"id": "S320", "title": "Knowledge Tools", "icon": "psychology"},
    {"id": "S330", "title": "Migration Dashboard", "icon": "migration"},
    {"id": "S600", "title": "Learning Hub", "icon": "school"},
]

_P_PAGES_DEFAULT: list[dict] = [
    {"id": "P001", "title": "System Health", "icon": "monitor_heart"},
    {"id": "P002", "title": "Configuration Audit", "icon": "checklist"},
    {"id": "P003", "title": "Service Graph", "icon": "bubble_chart"},
    {"id": "P004", "title": "Secret Audit Trail", "icon": "security"},
    {"id": "P005", "title": "Variable Inspector", "icon": "data_object"},
]


def _get_pages() -> tuple[list[dict], list[dict]]:
    """Load pages from config; fall back to built-in defaults."""
    return load_system_pages_registry()


# Backward-compatible module-level accessors (deprecated, kept for
# any code that may import S_PAGES/P_PAGES directly).
S_PAGES: list[dict] = _S_PAGES_DEFAULT  # noqa: N816
P_PAGES: list[dict] = _P_PAGES_DEFAULT  # noqa: N816


def register_system_api_routes(app: web.Application) -> None:  # noqa: C901
    """Register system surface API routes."""

    # ── Pages ──────────────────────────────────────────────────
    async def handle_pages(request: web.Request) -> web.Response:
        s_pages, p_pages = _get_pages()
        page_type = request.query.get("type", "all")
        pages: list[dict] = []
        if page_type in ("all", "s"):
            pages.extend(s_pages)
        if page_type in ("all", "p"):
            pages.extend(p_pages)
        return web.json_response({
            "pages": pages,
            "count": len(pages),
            "s_count": len(s_pages),
            "p_count": len(p_pages),
        })

    # ── Settings (disk-persisted) ───────────────────────────────
    async def handle_get_settings(_request: web.Request) -> web.Response:
        data = _load_settings()
        return web.json_response({"settings": data})

    async def handle_update_settings(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        scope = body.get("scope", "global")
        current = _load_settings()
        if scope not in current:
            current[scope] = {}
        for key, value in body.get("values", {}).items():
            current[scope][key] = value
        _save_settings(current)
        return web.json_response({"status": "ok", "settings": current})

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
                        status = (
                            "up"
                            if resp.status in accept_status
                            else "degraded"
                        )
                        return _build_result(svc, status, resp.status)
            except Exception:
                return _build_result(svc, "down", None)

        tasks = [_probe(s) for s in service_defs]
        results = list(await asyncio.gather(*tasks))

        up = sum(1 for s in results if s["status"] == "up")
        degraded = sum(1 for s in results if s["status"] == "degraded")
        down = sum(1 for s in results if s["status"] == "down")

        return web.json_response({
            "services": results,
            "count": len(results),
            "up": up,
            "degraded": degraded,
            "down": down,
            "health_pct": round((up / max(len(results), 1)) * 100),
        })

    app.router.add_get("/api/system/pages", handle_pages)
    app.router.add_get("/api/system/services", handle_system_services)
    app.router.add_get("/api/system/settings", handle_get_settings)
    app.router.add_post("/api/system/settings", handle_update_settings)
