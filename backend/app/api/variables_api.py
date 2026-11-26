"""Variables API — user, installation, and system variable store.
Extends /api/config with editable user variables and installation metadata.

Endpoints:
  GET  /api/variables          — all variables (user + installation)
  GET  /api/variables/user     — user variables only
  PUT  /api/variables/user     — update user variables
  GET  /api/variables/install  — installation variables (read-only)
"""
from __future__ import annotations

import asyncio
import json
import os
import platform
import re
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
        defaults = {
            "$USERNAME": os.environ.get("USER", "user"),
            "$ROLE": "Wizard",
            "$LOCATION": "unknown",
            "$TIMEZONE": str(datetime.now(UTC).astimezone().tzinfo) or "UTC",
            "$USERID": str(uuid.uuid4()),
            "model_routing": "automatic",
            "local_model": os.environ.get("UCORE_OLLAMA_MODEL", "qwen2.5-coder:3b"),
        }
        install_date = _load_install_meta().get("install_date")
        if isinstance(install_date, str):
            defaults["$INSTALLD"] = install_date[:10]
        _write_object(_VARIABLE_STORE_FILE, defaults)
        return defaults


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


_VARIABLE_NAME_PATTERN = re.compile(r"[A-Z][A-Z0-9]{2,7}")
_USER_DOMAINS = {"identity", "personal", "organization", "address", "communication", "scratch"}
_MANAGED_KEYS = {"$USERID", "$INSTALLD"}
_LEGACY_KEYS = {
    "username": "$USERNAME",
    "role": "$ROLE",
    "location": "$LOCATION",
    "timezone": "$TIMEZONE",
    "uid": "$USERID",
    "email": "$USERMAIL",
    "$UID": "$USERID",
    "$ROLEXXX": "$ROLE",
}
_PREFERENCES = {"model_routing", "local_model", "openrouter_model"}

_TRUE_VALUES = {"true", "1", "yes", "on"}
_FALSE_VALUES = {"false", "0", "no", "off"}
_NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")
_STORE_LOCK = asyncio.Lock()


def _coerce_value(key: str, value: str) -> str | None:
    """Apply the registry kind to a submitted value; None means rejected.

    The registry declares each variable as string, number or boolean. Values are
    stored as strings, so number and boolean are normalised here rather than
    trusted as free text. Keys outside the registry are preferences and stay
    strings.
    """
    kind = _REGISTRY_KINDS.get(key, "string")
    if kind == "number":
        return value.strip() if _NUMBER_PATTERN.fullmatch(value.strip()) else None
    if kind == "boolean":
        lowered = value.strip().lower()
        if lowered in _TRUE_VALUES:
            return "true"
        if lowered in _FALSE_VALUES:
            return "false"
        return None
    return value


def _rejection(key: str) -> web.Response:
    kind = _REGISTRY_KINDS.get(key, "string")
    return web.json_response(
        {"error": f"Variable {key!r} expects a {kind} value."},
        status=400,
    )


def _load_registry() -> dict[str, tuple[str, str]]:
    """Parse the fixed-width registry into {key: (kind, domain)}."""
    registry: dict[str, tuple[str, str]] = {}
    definition = Path(__file__).resolve().parents[1] / "core" / "vars.def"
    for line in definition.read_text(encoding="utf-8").splitlines():
        # Tolerate trailing whitespace so a hand-edited definition file cannot
        # brick the daemon at import time; the field count stays strict.
        entry = line.rstrip()
        if not entry or entry.startswith("#"):
            continue
        parts = entry.split("\t")
        if len(parts) != 4:
            raise ValueError(f"Invalid variable registry line: {line!r}")
        key, kind, default, domain = parts
        if kind not in {"string", "number", "boolean"} or default:
            raise ValueError(f"Invalid variable registry definition: {key!r}")
        if not key.startswith("$") or not _VARIABLE_NAME_PATTERN.fullmatch(key[1:]):
            raise ValueError(f"Invalid variable registry key: {key!r}")
        if key in registry:
            raise ValueError(f"Duplicate variable registry key: {key!r}")
        registry[key] = (kind, domain)
    return registry


_REGISTRY_ENTRIES = _load_registry()
_REGISTRY = {key: domain for key, (_kind, domain) in _REGISTRY_ENTRIES.items()}
_REGISTRY_KINDS = {key: kind for key, (kind, _domain) in _REGISTRY_ENTRIES.items()}
_WRITABLE_KEYS = {key for key, domain in _REGISTRY.items() if domain in _USER_DOMAINS}
_WRITABLE_KEYS -= _MANAGED_KEYS
# Accept names from the fixed-width registry when reading old stores and API requests.
_LEGACY_KEYS.update({key.ljust(9, "X"): key for key in _REGISTRY if len(key) < 9})
_LEGACY_KEYS["$LOCATIOX"] = "$LOCATION"
_LEGACY_KEYS["$LOCATIO"] = "$LOCATION"


def _canonicalize(values: dict) -> dict:
    result = {key: value for key, value in values.items() if key not in _LEGACY_KEYS}
    for key, canonical in _LEGACY_KEYS.items():
        if key in values:
            result.setdefault(canonical, values[key])
    return result


def _user_view(values: dict) -> dict:
    """Project stored values for the API.

    Legacy aliases (``username`` alongside ``$USERNAME``) are emitted for existing
    consumers; canonical keys win on conflict, and new callers should read only
    the ``$``-prefixed names.
    """
    result = {
        key: value
        for key, value in _canonicalize(values).items()
        if not key.startswith("$") or key in _WRITABLE_KEYS or key in _MANAGED_KEYS
    }
    for key, domain in _REGISTRY.items():
        if domain == "scratch":
            result.setdefault(key, "")
    for key, canonical in _LEGACY_KEYS.items():
        if canonical in result:
            result[key] = result[canonical]
    return result


# ─── Handlers ────────────────────────────────────────────────────────

async def handle_get_variables(request: web.Request) -> web.Response:
    """GET /api/variables — return all variables (user + install)."""
    try:
        user_vars = _user_view(_load_variables())
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
        return web.json_response(_user_view(_load_variables()))
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

    updates = {}
    for key, value in body.items():
        canonical = _LEGACY_KEYS.get(key, key)
        if canonical not in _WRITABLE_KEYS and canonical not in _PREFERENCES:
            return web.json_response({"error": f"Variable {key!r} is not writable."}, status=400)
        if not isinstance(value, str):
            return web.json_response({"error": "Variable values must be strings."}, status=400)
        coerced = _coerce_value(canonical, value)
        if coerced is None:
            return _rejection(canonical)
        if canonical in updates and updates[canonical] != coerced:
            return web.json_response({"error": f"Conflicting values for {canonical}."}, status=400)
        updates[canonical] = coerced

    # Serialise the read-merge-write so two concurrent PUTs cannot drop an update.
    async with _STORE_LOCK:
        try:
            current = _canonicalize(_load_variables())
            if updates:
                if "$INSTALLD" not in current:
                    install_date = _load_install_meta().get("install_date")
                    if isinstance(install_date, str):
                        current["$INSTALLD"] = install_date[:10]
                current.update(updates)
                _write_object(_VARIABLE_STORE_FILE, current)
        except (OSError, ValueError):
            return _store_unavailable()
    return web.json_response({"status": "ok", "variables": _user_view(current)})


async def handle_get_install_variables(
    request: web.Request,
) -> web.Response:
    """GET /api/variables/install — return installation (read-only)."""
    try:
        return web.json_response(_load_install_meta())
    except (OSError, ValueError):
        return _store_unavailable()
