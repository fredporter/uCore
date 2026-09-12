"""Snackbar Launchers & Apple Activity module.

Exposes REST endpoints:
- GET  /api/snackbar/launchers     — dynamic list of installed ecosystem products (absent hidden)
- GET  /api/snackbar/activity      — recent activity events and markdown view
- POST /api/snackbar/activity/sync — trigger bounded capture of Apple Calendar, Reminders, Notes, Mail
"""
from __future__ import annotations

import json
import logging
import platform
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiohttp import web

from app.core.settings import settings
from app.services.activity_markdown import (
    append_activity_events,
    get_activity_dir,
    update_daily_activity_markdown,
)
from app.services.apple_feed_sync import AppleFeedSync

log = logging.getLogger("ucore.snackbar.launchers")

APPLICATIONS_DIRS = [
    Path("/Applications"),
    Path("/System/Applications"),
    Path.home() / "Applications",
]


def _app_bundle_exists(app_name: str) -> Optional[Path]:
    bundle_name = f"{app_name}.app" if not app_name.endswith(".app") else app_name
    for app_dir in APPLICATIONS_DIRS:
        candidate = app_dir / bundle_name
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def get_active_launchers(include_absent: bool = False) -> List[Dict[str, Any]]:
    """Discover installed ecosystem products and host applications, hiding absent products."""
    is_mac = platform.system().lower() == "darwin"
    code_root = settings.udos_root

    defs = [
        {
            "id": "obsidian",
            "name": "Obsidian Vault",
            "category": "vault",
            "icon": "folder_special",
            "description": "Personal knowledge base & Markdown vault",
            "type": "host_app",
            "app_names": ["Obsidian"],
            "launch_command": ["open", "-a", "Obsidian"],
            "open_target": str(Path.home() / "Vault"),
        },
        {
            "id": "ucore",
            "name": "uCore Desktop",
            "category": "ecosystem",
            "icon": "desktop_windows",
            "description": "Sovereign desktop host & notebook production pipeline",
            "type": "repo",
            "repo_path": code_root / "uCore",
        },
        {
            "id": "ucode",
            "name": "uCode Studio",
            "category": "ecosystem",
            "icon": "terminal",
            "description": "GridCore 2D BASIC & Amiga NetHack pod",
            "type": "repo",
            "repo_path": code_root / "uCode",
            "launch_command": ["python3", "-m", "ucode_runtime"],
        },
        {
            "id": "ucode2",
            "name": "uCode 2 (Spatial)",
            "category": "ecosystem",
            "icon": "view_in_ar",
            "description": "3D spatial scene interpreter & Minecraft voxel lifter",
            "type": "repo",
            "repo_path": code_root / "uCode2",
            "launch_command": ["python3", "-m", "ucode2.cli", "lift"],
        },
        {
            "id": "udos-publishing",
            "name": "Publishing Compiler",
            "category": "ecosystem",
            "icon": "publish",
            "description": "Clean edition static compiler and WordPress publisher",
            "type": "repo",
            "repo_path": code_root / "udos-publishing",
        },
        {
            "id": "homenest",
            "name": "HomeNest",
            "category": "ecosystem",
            "icon": "tv",
            "description": "Living-room media server & entertainment hub",
            "type": "repo",
            "repo_path": code_root / "HomeNest",
        },
        {
            "id": "uvector",
            "name": "uVector Studio",
            "category": "ecosystem",
            "icon": "draw",
            "description": "Vector illustration & SVG optimization engine",
            "type": "repo",
            "repo_path": code_root / "uVector",
        },
        {
            "id": "groovebox",
            "name": "Groovebox",
            "category": "ecosystem",
            "icon": "music_note",
            "description": "Standalone pattern music synthesis suite",
            "type": "repo",
            "repo_path": code_root / "Groovebox",
        },
        {
            "id": "sonicscrewdriver",
            "name": "Sonic Screwdriver",
            "category": "ecosystem",
            "icon": "build",
            "description": "Hardware diagnostics, device revival, and provisioning",
            "type": "repo",
            "repo_path": code_root / "SonicScrewdriver",
        },
        {
            "id": "snackmachine",
            "name": "SnackMachine",
            "category": "tool",
            "icon": "fastfood",
            "description": "Standalone action runner and Apple activity capture",
            "type": "repo",
            "repo_path": code_root / "SnackMachine",
        },
        {
            "id": "apple-notes",
            "name": "Apple Notes",
            "category": "host_pim",
            "icon": "note",
            "description": "Host-native quick notes and clip storage",
            "type": "host_app",
            "app_names": ["Notes"],
            "launch_command": ["open", "-a", "Notes"],
        },
        {
            "id": "apple-reminders",
            "name": "Apple Reminders",
            "category": "host_pim",
            "icon": "checklist",
            "description": "Host-native task and reminder checklists",
            "type": "host_app",
            "app_names": ["Reminders"],
            "launch_command": ["open", "-a", "Reminders"],
        },
        {
            "id": "apple-calendar",
            "name": "Apple Calendar",
            "category": "host_pim",
            "icon": "calendar_month",
            "description": "Host-native calendar schedules and events",
            "type": "host_app",
            "app_names": ["Calendar"],
            "launch_command": ["open", "-a", "Calendar"],
        },
        {
            "id": "apple-mail",
            "name": "Apple Mail",
            "category": "host_pim",
            "icon": "mail",
            "description": "Host-native email communications",
            "type": "host_app",
            "app_names": ["Mail"],
            "launch_command": ["open", "-a", "Mail"],
        },
    ]

    launchers = []
    for item in defs:
        installed = False
        resolved_path = None

        if item["type"] == "repo":
            rpath: Path = item["repo_path"]
            if rpath.is_dir() and (rpath / ".git").exists():
                installed = True
                resolved_path = str(rpath)
        elif item["type"] == "host_app":
            if is_mac:
                for name in item.get("app_names", []):
                    bundle = _app_bundle_exists(name)
                    if bundle:
                        installed = True
                        resolved_path = str(bundle)
                        break
            else:
                bin_name = item["id"].replace("apple-", "")
                if shutil.which(bin_name):
                    installed = True
                    resolved_path = shutil.which(bin_name)

        if installed or include_absent:
            entry = {
                "id": item["id"],
                "name": item["name"],
                "category": item["category"],
                "icon": item["icon"],
                "description": item["description"],
                "installed": installed,
                "path": resolved_path,
                "launch_command": item.get("launch_command", []),
            }
            if item.get("open_target"):
                entry["open_target"] = item["open_target"]
            launchers.append(entry)

    return launchers


async def handle_list_launchers(request: web.Request) -> web.Response:
    """GET /api/snackbar/launchers — list present launchers (absent hidden)."""
    include_absent = request.query.get("all", "false").lower() in ("true", "1")
    items = get_active_launchers(include_absent=include_absent)
    return web.json_response({
        "launchers": items,
        "count": len(items),
        "absent_hidden": not include_absent,
    })


async def handle_get_activity(request: web.Request) -> web.Response:
    """GET /api/snackbar/activity — return recent activity events and markdown."""
    act_dir = get_activity_dir()
    events_file = act_dir / "events.jsonl"
    md_file = act_dir / "Daily_Activity.md"

    events = []
    if events_file.is_file():
        try:
            for line in events_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        except Exception:
            pass

    events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    markdown_content = md_file.read_text(encoding="utf-8") if md_file.is_file() else ""

    return web.json_response({
        "events": events[:50],
        "total_events": len(events),
        "markdown": markdown_content,
        "events_path": str(events_file),
        "markdown_path": str(md_file),
    })


async def handle_sync_activity(request: web.Request) -> web.Response:
    """POST /api/snackbar/activity/sync — run Apple Activity sync."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    sources = body.get("sources") or ["calendar", "mail"]
    sync = AppleFeedSync()
    sync_results = {}

    for src in sources:
        try:
            res = await sync.sync(src)
            sync_results[src] = res
        except Exception as exc:
            sync_results[src] = {"ok": False, "error": str(exc)}

    # Regenerate markdown view with user annotation preservation
    doc = update_daily_activity_markdown()

    return web.json_response({
        "ok": True,
        "results": sync_results,
        "markdown": doc,
    })


def register(app: web.Application) -> None:
    app.router.add_get("/api/snackbar/launchers", handle_list_launchers)
    app.router.add_get("/api/snackbar/activity", handle_get_activity)
    app.router.add_post("/api/snackbar/activity/sync", handle_sync_activity)
    log.info("Snackbar launchers module registered (3 routes)")
