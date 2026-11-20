"""Variables API — user, installation, and system variable store.
Extends /api/config with editable user variables and installation metadata.

Endpoints:
  GET  /api/variables          — all variables (user + installation)
  GET  /api/variables/user     — user variables only
  PUT  /api/variables/user     — update user variables
  GET  /api/variables/install  — installation variables (read-only)
"""
from __future__ import annotations

import json
import os
import platform
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from aiohttp import web

from app.core.settings import settings

# ─── Variable Store Path ─────────────────────────────────────────────
_VARIABLE_STORE_DIR = settings.data_dir
_VARIABLE_STORE_FILE = _VARIABLE_STORE_DIR / "variables.json"
_INSTALL_META_FILE = _VARIABLE_STORE_DIR / "install_meta.json"


def _write_object(path: Path, value: dict) -> None:
    """Replace a complete document so other readers never see a partial write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temp_path = Path(stream.name)
            json.dump(value, stream, indent=2)
            stream.write("\n")
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Variable store must contain a JSON object")
    return value


def _load_variables() -> dict:
    """Create defaults only for a missing file and preserve unreadable state."""
    try:
        return _read_object(_VARIABLE_STORE_FILE)
    except FileNotFoundError:
        default_vars = {
            "username": os.environ.get("USER", "user"),
            "role": "developer",
            "location": "unknown",
            "timezone": str(
                datetime.now(UTC).astimezone().tzinfo,
            ) or "UTC",
            "uid": str(uuid.uuid4()),
            "model_routing": "automatic",
            "local_model": os.environ.get(
                "UCORE_OLLAMA_MODEL", "qwen2.5-coder:3b",
            ),
        }
        _write_object(_VARIABLE_STORE_FILE, default_vars)
        return default_vars

def _load_install_meta() -> dict:
    try:
        return _read_object(_INSTALL_META_FILE)
    except FileNotFoundError:
        install_meta = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "install_date": datetime.now(UTC).isoformat(),
            "udos_root": str(
                Path(
                    os.environ.get(
                        "UDOS_ROOT",
                        os.path.expanduser("~/Code"),
                    ),
                ).resolve(),
            ),
        }
        _write_object(_INSTALL_META_FILE, install_meta)
        return install_meta


def _store_unavailable() -> web.Response:
    return web.json_response(
        {"error": "Local variables are unavailable. Check the local variable store and retry."},
        status=503,
    )


# ─── Handlers ────────────────────────────────────────────────────────

async def handle_get_variables(request: web.Request) -> web.Response:
    """GET /api/variables — return all variables (user + install)."""
    try:
        user_vars = _load_variables()
        install_vars = _load_install_meta()
    except (OSError, ValueError):
        return _store_unavailable()
    return web.json_response({
        "user": user_vars,
        "installation": install_vars,
    })


async def handle_get_user_variables(request: web.Request) -> web.Response:
    """GET /api/variables/user — return user variables."""
    try:
        return web.json_response(_load_variables())
    except (OSError, ValueError):
        return _store_unavailable()


async def handle_update_user_variables(request: web.Request) -> web.Response:
    """PUT /api/variables/user — update user variables (merge)."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    if not isinstance(body, dict):
        return web.json_response(
            {"error": "Body must be a JSON object"},
            status=400,
        )

    # Only allow known user variable keys
    allowed_keys = {
        "username", "role", "location",
        "timezone", "uid", "email",
        "model_routing", "local_model", "openrouter_model",
    }
    updates = {key: value for key, value in body.items() if key in allowed_keys}
    if any(not isinstance(value, str) for value in updates.values()):
        return web.json_response({"error": "Local variable values must be strings."}, status=400)
    try:
        current = _load_variables()
        if updates:
            current.update(updates)
            _write_object(_VARIABLE_STORE_FILE, current)
    except (OSError, ValueError):
        return _store_unavailable()
    return web.json_response({"status": "ok", "variables": current})


async def handle_get_install_variables(
    request: web.Request,
) -> web.Response:
    """GET /api/variables/install — return installation (read-only)."""
    try:
        return web.json_response(_load_install_meta())
    except (OSError, ValueError):
        return _store_unavailable()
