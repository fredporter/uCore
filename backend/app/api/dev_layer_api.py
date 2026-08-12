"""Dev Layer API — REST endpoints for Dev Mode toggle and Dev HUD.

GET  /api/dev-layer/state   — Get current Dev Mode state
PUT  /api/dev-layer/state   — Set Dev Mode state
POST /api/dev-layer/toggle  — Cycle through OFF → MINIMAL → ON → OFF
GET  /api/dev-layer/hud     — Aggregate Dev HUD data (tasks + vars + capabilities + actions)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from aiohttp import web

from app.services.dev_layer import DevMode, get_dev_layer

log = logging.getLogger("ucore.api.dev_layer")


async def handle_get_dev_state(request: web.Request) -> web.Response:
    """GET /api/dev-layer/state — get current Dev Mode state."""
    return web.json_response(get_dev_layer().get_status())


async def handle_set_dev_state(request: web.Request) -> web.Response:
    """PUT /api/dev-layer/state — set Dev Mode state.

    Body: { "mode": "on" | "off" | "minimal" }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    mode_str = str(body.get("mode", "")).strip().lower()
    if mode_str not in ("on", "off", "minimal"):
        return web.json_response({
            "error": "Invalid mode. Use: on, off, or minimal",
        }, status=400)

    layer = get_dev_layer()
    layer.mode = DevMode(mode_str)
    layer._save()
    log.info("Dev Mode → %s (by %s)", mode_str, request.remote or "unknown")
    return web.json_response(layer.get_status())


async def handle_toggle_dev_state(request: web.Request) -> web.Response:
    """POST /api/dev-layer/toggle — cycle dev mode."""
    layer = get_dev_layer()
    new_mode = layer.toggle()
    log.info("Dev Mode toggled → %s (by %s)", new_mode.value, request.remote or "unknown")
    return web.json_response(layer.get_status())


# ── Dev HUD Aggregate ─────────────────────────────────────────────

async def handle_get_dev_hud(request: web.Request) -> web.Response:
    """GET /api/dev-layer/hud — aggregate Dev HUD data.

    Returns a single payload with: dev_mode, tasks (tasker summary),
    variables (user vars), capabilities (key readiness), quick_actions.
    Used by the Dev Mode floating overlay in the uCore UI.
    """
    hud: dict = {
        "dev_mode": get_dev_layer().get_status(),
        "tasks": _get_tasker_hud(),
        "variables": _get_variables_hud(),
        "capabilities": _get_capabilities_hud(),
        "quick_actions": _QUICK_ACTIONS,
    }
    return web.json_response(hud)


# ── HUD sub-collectors ─────────────────────────────────────────────

def _get_tasker_hud() -> dict:
    """Collect tasker summary from the .tasker markdown boards."""
    try:
        from app.services.workflow_status import default_tasker_dir
        base = default_tasker_dir()
    except Exception:
        return {"error": "tasker not available"}

    status_counts: dict[str, int] = {}
    board_counts: dict[str, int] = {}
    total = 0

    try:
        if base.exists():
            for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
                count = 0
                for md_file in board_dir.glob("*.md"):
                    if md_file.name == "README.md":
                        continue
                    task = _parse_markdown_task_inline(md_file)
                    status = task.get("status", "todo") or "todo"
                    status_counts[status] = status_counts.get(status, 0) + 1
                    total += 1
                    count += 1
                if count > 0:
                    board_counts[board_dir.name] = count
    except Exception as exc:
        return {"error": str(exc)}

    return {
        "total": total,
        "by_status": status_counts,
        "by_board": board_counts,
    }


def _parse_markdown_task_inline(path: Path) -> dict:
    """Minimal inline markdown task parser (avoids heavy imports)."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {"status": "todo"}

    task: dict = {"title": path.stem, "status": "todo", "lane": "ecosystem"}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("status:"):
            task["status"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("lane:"):
            task["lane"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("# "):
            task["title"] = line[2:].strip()
    return task


def _get_variables_hud() -> dict:
    """Collect user variables for the Dev HUD."""
    try:
        var_file = Path.home() / ".ucore" / "data" / "variables.json"
        if var_file.exists():
            return {"user": json.loads(var_file.read_text(encoding="utf-8"))}
    except Exception:
        pass
    return {"user": {}}


def _get_capabilities_hud() -> dict:
    """Check key dev capabilities readiness."""
    caps: dict = {}
    try:
        from app.extensions.registry import registry
        ext = registry.get_extensions()
        running = {e.get("id", "") for e in ext if isinstance(e, dict) and e.get("status") == "online"}
    except Exception:
        running = set()

    caps["developer"] = "online" if "ucore-developer" in running else "offline"
    caps["ollama"] = "online" if "ollama" in running else "offline"
    caps["hivemind"] = "online" if "hivemind" in running else "offline"
    return caps


_QUICK_ACTIONS: list[dict] = [
    {"id": "ecosystem-audit", "label": "Run Ecosystem Audit", "icon": "monitoring"},
    {"id": "system-health", "label": "System Health Check", "icon": "favorite"},
    {"id": "binder-refresh", "label": "Refresh Binder Context", "icon": "folder"},
    {"id": "spool-prune", "label": "Prune Spool Logs", "icon": "cleaning_services"},
    {"id": "vault-sync", "label": "Sync Vault", "icon": "sync"},
    {"id": "tasker-sync", "label": "Sync Tasker", "icon": "assignment"},
    {"id": "snapshot", "label": "Take Snapshot", "icon": "camera"},
]


def register_dev_layer_routes(app: web.Application) -> None:
    """Register Dev Layer API routes."""
    app.router.add_get("/api/dev-layer/state", handle_get_dev_state)
    app.router.add_put("/api/dev-layer/state", handle_set_dev_state)
    app.router.add_post("/api/dev-layer/toggle", handle_toggle_dev_state)
    app.router.add_get("/api/dev-layer/hud", handle_get_dev_hud)
    log.debug("Dev Layer API routes registered")
