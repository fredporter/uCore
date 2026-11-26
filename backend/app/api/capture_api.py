"""Capture admission — bounded text from a local client into the profile Vault.

The client (SnackMachine / a macOS Shortcut) supplies text and a request ID; the
server decides the profile, the destination and the receipt. Replays return the
original receipt instead of writing again.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from aiohttp import web

from app.core.settings import settings

MAX_CAPTURE_BYTES = 10_000
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_SAFE_TITLE = re.compile(r"[^A-Za-z0-9._ -]+")

_lock = asyncio.Lock()


def _capture_dir() -> Path:
    directory = (settings.vault_root / "Captures").expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _receipt_path() -> Path:
    directory = settings.data_dir / "captures"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "receipts.json"


def _load_receipts() -> dict:
    path = _receipt_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_receipts(receipts: dict) -> None:
    path = _receipt_path()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipts, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


async def handle_capture(request: web.Request) -> web.Response:
    """POST /api/host/capture — admit one bounded, profile-scoped capture."""
    from app.services.execution_authority import (
        GUEST_ROLES,
        active_identity,
        active_profile,
    )

    identity = active_identity()
    if not identity.get("authenticated", True):
        return web.json_response(
            {"error": "Authenticate a local profile to capture"}, status=403
        )
    owner, role = active_profile(identity)
    if role in GUEST_ROLES:
        return web.json_response(
            {"error": "Guest profiles cannot capture into the Vault"}, status=403
        )

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "Expected an object"}, status=400)

    text = body.get("text")
    request_id = str(body.get("request_id") or "")
    if not isinstance(text, str) or not text.strip():
        return web.json_response({"error": "text is required"}, status=400)
    size = len(text.encode("utf-8"))
    if size > MAX_CAPTURE_BYTES:
        return web.json_response(
            {"error": f"text exceeds {MAX_CAPTURE_BYTES} bytes"}, status=400
        )
    if not REQUEST_ID_PATTERN.match(request_id):
        return web.json_response(
            {"error": "request_id must be 1-64 chars of letters, digits, dot, underscore or hyphen"},
            status=400,
        )

    digest = hashlib.sha256(f"{owner}:{request_id}".encode("utf-8")).hexdigest()[:16]
    run_id = f"cap-{digest}"
    directory = _capture_dir()

    async with _lock:
        receipts = _load_receipts()
        existing = receipts.get(run_id)
        if existing and Path(existing["path"]).is_file():
            return web.json_response({**existing, "deduplicated": True})

        title = str(body.get("title") or "capture").strip() or "capture"
        safe_title = _SAFE_TITLE.sub("-", title)[:60].strip() or "capture"
        stamp = datetime.now(UTC)
        filename = f"{stamp.strftime('%Y%m%d-%H%M%S')}-{safe_title}-{digest}.md"
        path = (directory / filename).resolve()
        if directory not in path.parents:
            return web.json_response({"error": "capture path escapes the Vault"}, status=400)

        content = (
            "---\n"
            f"uid: {run_id}\n"
            f"title: {json.dumps(title)}\n"
            f"captured: {stamp.isoformat()}\n"
            f"profile: {owner}\n"
            f"request_id: {request_id}\n"
            "source: snackmachine\n"
            "---\n\n"
            f"{text.strip()}\n"
        )
        path.write_text(content, encoding="utf-8")

        receipt = {
            "run_id": run_id,
            "path": str(path),
            "bytes": size,
            "profile": owner,
            "status": "completed",
            "created": stamp.isoformat(),
        }
        receipts[run_id] = receipt
        _save_receipts(receipts)

    return web.json_response(receipt, status=201)


def register_capture_routes(app: web.Application) -> None:
    app.router.add_post("/api/host/capture", handle_capture)
