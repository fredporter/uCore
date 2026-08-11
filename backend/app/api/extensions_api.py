"""Extension and capability preflight API.

Provides strict readiness checks so S-pages can block execution when
requirements are missing and guide the user through repair steps.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aiohttp import web

from app.core.settings import settings
from app.extensions.registry import registry
from app.secret.store import get_store
from app.tools.registry import check_tool

_DEFAULT_CAPABILITY_REQ_FILE = (
    Path(__file__).resolve().parents[3] / "config" / "capability_requirements.json"
)


def _load_user_vars() -> dict[str, Any]:
    path = settings.data_dir / "variables.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _load_capability_requirements() -> tuple[dict[str, Any], str]:
    override = settings.config_dir / "capability_requirements.json"
    source = override if override.exists() else _DEFAULT_CAPABILITY_REQ_FILE
    if not source.exists():
        return {}, str(source)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception:
        return {}, str(source)
    if not isinstance(data, dict):
        return {}, str(source)
    return data, str(source)


def _repair_item(kind: str, item_id: str, details: str, action: str) -> dict[str, str]:
    return {
        "kind": kind,
        "id": item_id,
        "details": details,
        "action": action,
    }


async def handle_extensions_status(_request: web.Request) -> web.Response:
    """GET /api/extensions/status — extension registry health summary."""
    status = registry.status()
    return web.json_response(status)


async def _evaluate_capability(
    capability: str,
    reqs: dict[str, Any],
    source: str,
) -> tuple[dict[str, Any], int]:
    """Evaluate one capability and return payload + HTTP status."""
    spec = reqs.get(capability)
    if not isinstance(spec, dict):
        payload = {
            "capability": capability,
            "ready": False,
            "repair_required": True,
            "error": "No capability requirements found",
            "requirements_source": source,
            "repair": [
                _repair_item(
                    "config",
                    "capability_requirements",
                    f"Missing requirements entry for capability '{capability}'",
                    "Add capability entry to capability_requirements.json",
                ),
            ],
        }
        return payload, 412

    repair: list[dict[str, str]] = []

    # Extensions
    ext_reqs = spec.get("extensions", [])
    if isinstance(ext_reqs, list):
        status = registry.status()
        ext_loaded = {e.get("id"): bool(e.get("loaded")) for e in status.get("extensions", []) if isinstance(e, dict)}
        ext_known = set(ext_loaded.keys())
        for ext_id in ext_reqs:
            ext_id = str(ext_id)
            if ext_id not in ext_known:
                repair.append(_repair_item(
                    "extension",
                    ext_id,
                    "Extension is not registered",
                    "Install/enable extension manifest and restart uCore",
                ))
            elif not ext_loaded.get(ext_id, False):
                repair.append(_repair_item(
                    "extension",
                    ext_id,
                    "Extension is registered but not loaded",
                    "Inspect /api/extensions/status errors and fix dependency/import issues",
                ))

    # Tools
    tool_reqs = spec.get("tools", [])
    if isinstance(tool_reqs, list):
        for tool_id in tool_reqs:
            tool_id = str(tool_id)
            result = await check_tool(tool_id)
            ok = False
            if isinstance(result, dict):
                ok = bool(result.get("installed") or result.get("available") or result.get("ok"))
            else:
                # pydantic model fallback
                ok = bool(getattr(result, "installed", False) or getattr(result, "available", False))
            if not ok:
                repair.append(_repair_item(
                    "tool",
                    tool_id,
                    "Required tool is not available on this machine",
                    f"Install tool '{tool_id}' and rerun preflight",
                ))

    # Repos
    repo_reqs = spec.get("repos", [])
    if isinstance(repo_reqs, list):
        for repo in repo_reqs:
            repo = str(repo)
            repo_path = settings.udos_root / repo
            if not repo_path.exists():
                repair.append(_repair_item(
                    "repo",
                    repo,
                    f"Required repository not found at {repo_path}",
                    f"Clone/install repo '{repo}' into {settings.udos_root}",
                ))

    # Variables
    var_reqs = spec.get("variables", [])
    user_vars = _load_user_vars()
    if isinstance(var_reqs, list):
        for var in var_reqs:
            var = str(var)
            val = user_vars.get(var)
            if val is None or str(val).strip() == "":
                repair.append(_repair_item(
                    "variable",
                    var,
                    "Required variable is missing",
                    f"Set {var} via PUT /api/variables/user",
                ))

    # Secrets
    secret_reqs = spec.get("secrets", [])
    store = get_store()
    if isinstance(secret_reqs, list):
        for secret_name in secret_reqs:
            secret_name = str(secret_name)
            if not store.get(secret_name):
                repair.append(_repair_item(
                    "secret",
                    secret_name,
                    "Required secret is missing",
                    f"Set {secret_name} via /api/secrets or environment sync",
                ))

    ready = len(repair) == 0
    payload = {
        "capability": capability,
        "ready": ready,
        "repair_required": not ready,
        "requirements_source": source,
        "repair": repair,
    }
    return payload, 200 if ready else 412


async def handle_capability_preflight(request: web.Request) -> web.Response:
    """GET /api/capabilities/{capability}/preflight — strict readiness check.

    Returns repair_required=true when any prerequisite is missing.
    """
    capability = request.match_info.get("capability", "").strip()
    if not capability:
        return web.json_response({"error": "capability is required"}, status=400)

    reqs, source = _load_capability_requirements()
    payload, status = await _evaluate_capability(capability, reqs, source)
    return web.json_response(payload, status=status)


async def handle_capabilities_readiness(request: web.Request) -> web.Response:
    """GET /api/capabilities/readiness — batch readiness snapshot.

    Query:
      - capabilities=csv,list,optional
    """
    reqs, source = _load_capability_requirements()
    raw = request.query.get("capabilities", "").strip()

    if raw:
        capability_ids = [c.strip() for c in raw.split(",") if c.strip()]
    else:
        capability_ids = sorted(reqs.keys())

    results: list[dict[str, Any]] = []
    all_ready = True

    for capability in capability_ids:
        payload, status = await _evaluate_capability(capability, reqs, source)
        payload["status"] = status
        results.append(payload)
        if status != 200:
            all_ready = False

    return web.json_response(
        {
            "ready": all_ready,
            "count": len(results),
            "requirements_source": source,
            "capabilities": results,
        },
        status=200 if all_ready else 412,
    )
