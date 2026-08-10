"""Snackbar Extensions module — REST API for managing extensions.

Provides:
  GET  /api/extensions/catalogue   — full extension catalogue with status
  POST /api/extensions/{id}/toggle — enable/disable an extension
  POST /api/extensions/{id}/install — install (clone + setup) an extension
  POST /api/extensions/{id}/repair  — repair (re-clone, reinstall, fix deps)
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from aiohttp import web

from app.core.settings import settings

log = logging.getLogger("ucore.snackbar.extensions")

STATE_FILE = settings.data_dir / "extension_state.json"

# ── Known external extensions we expect in ~/Code/ ───────────────────

KNOWN_EXTERNAL: list[dict] = [
    {
        "id": "udos-budget",
        "name": "uDos Budget",
        "kind": "plugin",
        "icon": "savings",
        "description": "Budget policy & status plugin",
        "repo": "udos-budget",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
    {
        "id": "udos-identity",
        "name": "uDos Identity",
        "kind": "plugin",
        "icon": "fingerprint",
        "description": "Identity profile & session plugin",
        "repo": "udos-identity",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
    {
        "id": "udos-google",
        "name": "Google Bridge",
        "kind": "plugin",
        "icon": "cloud",
        "description": "Google OAuth, Gemini/Gems, Drive mirror",
        "repo": "udos-google",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
    {
        "id": "udos-dreamscape",
        "name": "Dreamscape",
        "kind": "plugin",
        "icon": "psychology",
        "description": "Mission scaffolding & daily briefing",
        "repo": "udos-dreamscape",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
    {
        "id": "udos-publishing",
        "name": "Publishing",
        "kind": "plugin",
        "icon": "publish",
        "description": "Cloud mirror for udo.guide/udo.place",
        "repo": "udos-publishing",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
    {
        "id": "udos-vaults",
        "name": "Vault Topology",
        "kind": "plugin",
        "icon": "folder_special",
        "description": "Vault topology & AppFlowy bridge",
        "repo": "udos-vaults",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
    {
        "id": "udos-agents",
        "name": "uDos Agents",
        "kind": "plugin",
        "icon": "smart_toy",
        "description": "Specialized agent scaffolding",
        "repo": "udos-agents",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
    {
        "id": "homenest",
        "name": "HomeNest",
        "kind": "plugin",
        "icon": "home",
        "description": "Home stream server — Jellyfin + Home Assistant bridge",
        "repo": "HomeNest",
        "manifest_path": "ucore-extension.json",
        "deps": [],
    },
]


# ── State persistence ────────────────────────────────────────────────


def _load_state() -> dict[str, dict]:
    """Load persisted extension state from disk."""
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict[str, dict]) -> None:
    """Persist extension state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, indent=2, default=str),
        encoding="utf-8",
    )


# ── Filesystem probes ────────────────────────────────────────────────


def _repo_exists(repo_name: str) -> bool:
    """Check if a repo directory exists under ~/Code/."""
    return (settings.udos_root / repo_name).is_dir()


def _check_manifest(repo_name: str, manifest_path: str) -> bool:
    """Check if the extension manifest file exists in the repo."""
    return (settings.udos_root / repo_name / manifest_path).is_file()


def _get_pyproject(repo_name: str) -> dict | None:
    """Read pyproject.toml from a repo (best-effort version extraction)."""
    pp = settings.udos_root / repo_name / "pyproject.toml"
    if not pp.is_file():
        return None
    try:
        text = pp.read_text(encoding="utf-8")
        # Quick regex-free parse for version
        version = None
        name = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("version"):
                version = (
                    stripped.split("=", 1)[1]
                    .strip()
                    .strip('"')
                    .strip("'")
                )
            if stripped.startswith("name"):
                name = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        return {"name": name, "version": version}
    except Exception:
        return None


def _probe_extension(ext: dict) -> dict:
    """Probe filesystem for extension presence and status."""
    result = dict(ext)
    repo = ext.get("repo", ext["id"])
    result["repo_exists"] = _repo_exists(repo)
    manifest_file = ext.get("manifest_path", "ucore-extension.json")
    result["manifest_exists"] = _check_manifest(repo, manifest_file)
    result["is_installed"] = (
        result["repo_exists"] and result["manifest_exists"]
    )

    # Try to get version from pyproject.toml
    pp = _get_pyproject(repo)
    if pp and pp.get("version"):
        result["version"] = pp["version"]

    return result


# ── Action helpers ───────────────────────────────────────────────────


def _toggle_extension(ext_id: str, enabled: bool) -> tuple[bool, str]:
    """Toggle an extension on or off in persisted state."""
    state = _load_state()
    entry = state.get(ext_id, {})
    entry["enabled"] = enabled
    entry["updated_at"] = str(subprocess.check_output(["date", "-Iseconds"]).decode().strip()) if False else ""
    state[ext_id] = entry
    _save_state(state)
    return True, f"Extension '{ext_id}' {'enabled' if enabled else 'disabled'}"


def _install_extension(ext: dict) -> tuple[bool, str]:
    """Install an extension — clone repo if missing."""
    repo_name = ext.get("repo", ext["id"])
    repo_dir = settings.udos_root / repo_name

    if repo_dir.is_dir():
        # Already exists — run install
        return _run_install_commands(repo_dir, ext)

    # Clone from GitHub
    log.info("Installing extension %s — cloning repo %s", ext["id"], repo_name)
    result = subprocess.run(
        [
            "git", "clone",
            f"https://github.com/fredporter/{repo_name}.git",
            str(repo_dir),
        ],
        capture_output=True, text=True, timeout=60,
        cwd=str(settings.udos_root),
    )
    if result.returncode != 0:
        log.error("Clone failed for %s: %s", repo_name, result.stderr)
        # Try SSH fallback
        result2 = subprocess.run(
            [
                "git", "clone",
                f"git@github.com:fredporter/{repo_name}.git",
                str(repo_dir),
            ],
            capture_output=True, text=True, timeout=60,
            cwd=str(settings.udos_root),
        )
        if result2.returncode != 0:
            return False, f"Failed to clone {repo_name}: {result2.stderr.strip()}"

    return _run_install_commands(repo_dir, ext)


def _run_install_commands(repo_dir: Path, ext: dict) -> tuple[bool, str]:
    """Run pip install or npm install in the extension repo."""
    messages: list[str] = []

    # Python install
    if (repo_dir / "pyproject.toml").is_file() or (repo_dir / "setup.py").is_file() or (repo_dir / "requirements.txt").is_file():
        log.info("Running pip install in %s", repo_dir)
        result = subprocess.run(
            ["pip", "install", "-e", str(repo_dir)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            messages.append("pip install ✓")
        else:
            messages.append(f"pip install error: {result.stderr.strip()[-200:]}")

    # Node install
    if (repo_dir / "package.json").is_file():
        log.info("Running npm install in %s", repo_dir)
        result = subprocess.run(
            ["npm", "install"],
            capture_output=True, text=True, timeout=120,
            cwd=str(repo_dir),
        )
        if result.returncode == 0:
            messages.append("npm install ✓")
        else:
            messages.append(f"npm install error: {result.stderr.strip()[-200:]}")

    # Mark as enabled in state
    _toggle_extension(ext["id"], True)

    if messages:
        return True, "; ".join(messages)
    return True, "Install complete (no package manager files found)"


def _repair_extension(ext: dict) -> tuple[bool, str]:
    """Repair — re-clone repo + reinstall deps."""
    repo_name = ext.get("repo", ext["id"])
    repo_dir = settings.udos_root / repo_name

    # Re-clone: remove and re-clone
    if repo_dir.is_dir():
        log.info("Repairing %s — removing existing repo", repo_dir)
        subprocess.run(["rm", "-rf", str(repo_dir)], timeout=30)

    return _install_extension(ext)


# ── Route handlers ───────────────────────────────────────────────────


async def handle_extensions_catalogue(request: web.Request) -> web.Response:
    """GET /api/extensions/catalogue — full extension catalogue with filesystem status."""
    state = _load_state()
    catalogue = []
    for ext in KNOWN_EXTERNAL:
        entry = _probe_extension(ext)
        ext_state = state.get(entry["id"], {})
        entry["enabled"] = ext_state.get("enabled", entry["is_installed"])
        entry["status"] = _derive_status(entry)
        catalogue.append(entry)

    return web.json_response({
        "extensions": catalogue,
        "total": len(catalogue),
    })


def _derive_status(entry: dict) -> str:
    """Derive a human-readable status from probe results."""
    if entry.get("status"):
        return entry["status"]
    if entry.get("enabled") and entry.get("is_installed"):
        return "running"
    if entry.get("is_installed"):
        return "installed"
    return "available"


async def handle_extension_toggle(request: web.Request) -> web.Response:
    """POST /api/extensions/{id}/toggle — toggle extension on/off."""
    ext_id = request.match_info.get("id", "").strip()
    if not ext_id:
        return web.json_response({"error": "Extension id required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        body = {}
    enabled = bool(body.get("enabled", body.get("enable", True)))

    success, message = _toggle_extension(ext_id, enabled)
    payload = {
        "id": ext_id,
        "enabled": enabled,
        "success": success,
        "message": message,
    }
    return web.json_response(payload)


async def handle_extension_install(request: web.Request) -> web.Response:
    """POST /api/extensions/{id}/install — install an extension."""
    ext_id = request.match_info.get("id", "").strip()
    if not ext_id:
        return web.json_response({"error": "Extension id required"}, status=400)

    ext = next((e for e in KNOWN_EXTERNAL if e["id"] == ext_id), None)
    if not ext:
        return web.json_response({"error": f"Unknown extension: {ext_id}"}, status=404)

    success, message = _install_extension(ext)
    payload = {
        "id": ext_id,
        "installed": success,
        "success": success,
        "message": message,
    }
    return web.json_response(payload)


async def handle_extension_repair(request: web.Request) -> web.Response:
    """POST /api/extensions/{id}/repair — repair an extension."""
    ext_id = request.match_info.get("id", "").strip()
    if not ext_id:
        return web.json_response({"error": "Extension id required"}, status=400)

    ext = next((e for e in KNOWN_EXTERNAL if e["id"] == ext_id), None)
    if not ext:
        return web.json_response({"error": f"Unknown extension: {ext_id}"}, status=404)

    success, message = _repair_extension(ext)
    payload = {
        "id": ext_id,
        "repaired": success,
        "success": success,
        "message": message,
    }
    return web.json_response(payload)


def register(app: web.Application) -> None:
    """Register extension management routes on the snackbar app."""
    app.router.add_get("/api/extensions/catalogue", handle_extensions_catalogue)
    app.router.add_post("/api/extensions/{id}/toggle", handle_extension_toggle)
    app.router.add_post("/api/extensions/{id}/install", handle_extension_install)
    app.router.add_post("/api/extensions/{id}/repair", handle_extension_repair)
    log.info("Snackbar extensions module registered (4 routes)")
