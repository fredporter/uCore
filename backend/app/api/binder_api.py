"""Binder API — CRUD for BrowserUI binder metadata.

GET    /api/binder/list   — list all binders with metadata
POST   /api/binder/add    — create a new binder
PATCH  /api/binder/update — update binder metadata
PATCH  /api/binder/score  — set quality score
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from aiohttp import web

log = logging.getLogger("ucore.binder_api")

VAULT_ROOT = Path.home() / "Vault"


def _binder_path(binder_name: str) -> Path:
    return VAULT_ROOT / binder_name.strip().replace("/", "-")


def _meta_path(binder_name: str) -> Path:
    return _binder_path(binder_name) / "binder.json"


def _load_meta(binder_name: str) -> dict:
    mp = _meta_path(binder_name)
    if mp.exists():
        try:
            return json.loads(mp.read_text())
        except Exception:
            pass
    return {
        "name": binder_name,
        "description": "",
        "created": datetime.now(UTC).isoformat(),
        "updated": datetime.now(UTC).isoformat(),
        "score": 0,
        "tags": [],
        "sources": [],
    }


def _save_meta(binder_name: str, meta: dict) -> None:
    mp = _meta_path(binder_name)
    mp.parent.mkdir(parents=True, exist_ok=True)
    meta["updated"] = datetime.now(UTC).isoformat()
    mp.write_text(json.dumps(meta, indent=2))


def _scan_binders() -> list[dict]:
    binders = []
    if not VAULT_ROOT.exists():
        return binders
    for d in sorted(VAULT_ROOT.iterdir()):
        if d.is_dir() and (d / "binder.json").exists():
            binders.append(_load_meta(d.name))
    return binders


async def handle_binder_list(request: web.Request) -> web.Response:
    """GET /api/binder/list — list all binders."""
    binders = _scan_binders()
    return web.json_response({"binders": binders, "count": len(binders)})


async def handle_binder_add(request: web.Request) -> web.Response:
    """POST /api/binder/add — create a new binder."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    name = body.get("name", "").strip()
    if not name:
        return web.json_response({"error": "name required"}, status=400)
    bp = _binder_path(name)
    if bp.exists() and (bp / "binder.json").exists():
        return web.json_response({"error": "Binder already exists"}, status=409)
    meta = {
        "name": name,
        "description": body.get("description", ""),
        "created": datetime.now(UTC).isoformat(),
        "updated": datetime.now(UTC).isoformat(),
        "score": body.get("score", 0),
        "tags": body.get("tags", []),
        "sources": body.get("sources", []),
    }
    _save_meta(name, meta)
    return web.json_response({"created": True, "binder": meta})


async def handle_binder_update(request: web.Request) -> web.Response:
    """PATCH /api/binder/update — update binder metadata."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    name = body.get("name", "").strip()
    if not name:
        return web.json_response({"error": "name required"}, status=400)
    mp = _meta_path(name)
    if not mp.exists():
        return web.json_response({"error": "Binder not found"}, status=404)
    meta = _load_meta(name)
    for key in ("description", "tags", "sources", "score"):
        if key in body:
            meta[key] = body[key]
    _save_meta(name, meta)
    return web.json_response({"updated": True, "binder": meta})


async def handle_binder_score(request: web.Request) -> web.Response:
    """PATCH /api/binder/score — set quality score (0-5)."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    name = body.get("name", "").strip()
    score = body.get("score", 0)
    if not name:
        return web.json_response({"error": "name required"}, status=400)
    score = max(0, min(5, int(score)))
    mp = _meta_path(name)
    if not mp.exists():
        return web.json_response({"error": "Binder not found"}, status=404)
    meta = _load_meta(name)
    meta["score"] = score
    _save_meta(name, meta)
    return web.json_response({"scored": True, "score": score, "binder": meta})
