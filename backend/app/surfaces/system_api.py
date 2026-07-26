"""System Surface — pages, services, and settings backend."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from aiohttp import web

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

S_PAGES: list[dict] = [
    {"id": "S100", "title": "Tool Builder", "icon": "build"},
    {"id": "S101", "title": "Story Builder", "icon": "auto_stories"},
    {"id": "S300", "title": "Workflow Builder", "icon": "account_tree"},
    {
        "id": "S310",
        "title": "Clipboard Orchestration",
        "icon": "content_paste",
    },
    {"id": "S320", "title": "Knowledge Tools", "icon": "psychology"},
    {"id": "S330", "title": "Migration Dashboard", "icon": "migration"},
    {"id": "S600", "title": "Learning Hub", "icon": "school"},
]

P_PAGES: list[dict] = [
    {"id": "P001", "title": "System Health", "icon": "monitor_heart"},
    {"id": "P002", "title": "Configuration Audit", "icon": "checklist"},
    {"id": "P003", "title": "Service Graph", "icon": "bubble_chart"},
    {"id": "P004", "title": "Secret Audit Trail", "icon": "security"},
    {"id": "P005", "title": "Variable Inspector", "icon": "data_object"},
]


def register_system_api_routes(app: web.Application) -> None:  # noqa: C901
    """Register system surface API routes."""

    # ── Pages ──────────────────────────────────────────────────
    async def handle_pages(request: web.Request) -> web.Response:
        page_type = request.query.get("type", "all")
        pages: list[dict] = []
        if page_type in ("all", "s"):
            pages.extend(S_PAGES)
        if page_type in ("all", "p"):
            pages.extend(P_PAGES)
        return web.json_response({
            "pages": pages,
            "count": len(pages),
            "s_count": len(S_PAGES),
            "p_count": len(P_PAGES),
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
    async def handle_system_services(request: web.Request) -> web.Response:
        """Probe known system services and return statuses."""
        services = [
            {"name": "snackbar", "port": 8484, "type": "system",
             "description": "Container orchestrator & workflow runner"},
            {"name": "hivemind", "port": 8490, "type": "system",
             "description": "AI agent routing gateway"},
            {"name": "ollama", "port": 11434, "type": "system",
             "description": "Local LLM inference runtime"},
            {"name": "vault-mcp", "port": 8765, "type": "user",
             "description": "Vault MCP bridge for knowledge import"},
            {"name": "feed-spool", "port": 8486, "type": "system",
             "description": "Feed spooler & transport layer"},
            {"name": "secret-server", "port": 30001, "type": "user",
             "description": "AES-256-GCM encrypted secret vault"},
        ]

        async def _probe(svc: dict) -> dict:
            import aiohttp
            port = svc.get("port", 0)
            if not port:
                return {**svc, "status": "down", "uptime": 0}
            url = f"http://localhost:{port}/health"
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=2),
                ) as session:
                    async with session.get(url) as resp:
                        return {
                            **svc,
                            "status": "up" if resp.status == 200 else "degraded",
                            "status_code": resp.status,
                        }
            except Exception:
                return {**svc, "status": "down"}

        tasks = [_probe(s) for s in services]
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
