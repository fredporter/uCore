"""Runtime Device Delivery and Capsule Governance API.

Per uDOS Product Refactor Plan Section 11:
- Hardware profiles: Pinned Linux Mint 22 baseline (cinnamon-full, xfce-light).
- Safety gates: read-only inspect, disk write provision, and firmware flash.
- Capsule governance: anti-autorun quarantine, explicit authorization gate, permissions boundary.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiohttp import web

log = logging.getLogger("ucore.runtime_device")

def get_udos_home() -> Path:
    return Path(os.environ.get("UDOS_HOME", Path.home() / "Code" / ".udos")).expanduser()


def get_ucode_programs_dir() -> Path:
    # Standard repository location: ~/Code/uCode/programs
    code_dir = Path.home() / "Code"
    ucode_programs = code_dir / "uCode" / "programs"
    if ucode_programs.exists():
        return ucode_programs
    # Fallback to local capsules under UDOS_HOME
    return get_udos_home() / "capsules"


def get_sonic_profiles() -> Dict[str, Any]:
    """Retrieve Linux Mint profile specifications from Sonic or bundled fallback."""
    try:
        # Try import from SonicScrewdriver
        sonic_cli_path = (Path.home() / "Code" / "SonicScrewdriver" / "cli").resolve()
        if str(sonic_cli_path) not in sys.path and sonic_cli_path.exists():
            sys.path.insert(0, str(sonic_cli_path))
        from sonic.lib.mint_profiler import load_profile_spec
        return load_profile_spec()
    except Exception as e:
        log.warning("Could not load profiles directly from Sonic: %s. Using pinned baseline.", e)
        return {
            "schema_version": 1,
            "baseline": {
                "distribution": "Linux Mint",
                "version": "22",
                "codename": "wilma",
                "kernel_baseline": "6.8.0-generic",
            },
            "profiles": {
                "cinnamon-full": {
                    "id": "cinnamon-full",
                    "title": "Linux Mint 22 Cinnamon (Full Workstation)",
                    "desktop_environment": "cinnamon",
                    "min_ram_mb": 4096,
                    "supported_hardware_tiers": ["pc-x86_64", "intel-mac"],
                },
                "xfce-light": {
                    "id": "xfce-light",
                    "title": "Linux Mint 22 Xfce (Lightweight Revival)",
                    "desktop_environment": "xfce",
                    "min_ram_mb": 2048,
                    "supported_hardware_tiers": ["pc-x86_64", "intel-mac", "arm-sbc"],
                },
            },
            "hardware_tiers": {
                "pc-x86_64": {"name": "Standard PC x86-64", "arch": "x86_64"},
                "intel-mac": {"name": "Intel Mac (2012-2015)", "arch": "x86_64"},
                "arm-sbc": {"name": "ARM64 Single Board Computer", "arch": "aarch64"},
            },
            "safety_gates": {
                "inspect": {"level": "read_only", "destructive": False},
                "provision": {"level": "disk_write", "destructive": True},
                "flash": {"level": "firmware_write", "destructive": True},
            },
        }


async def handle_get_profiles(request: web.Request) -> web.Response:
    """GET /api/runtime/profiles — Retrieve qualified Linux Mint profiles and specifications."""
    spec = get_sonic_profiles()
    return web.json_response({"status": "ok", "spec": spec})


async def handle_inspect_device(request: web.Request) -> web.Response:
    """POST /api/runtime/profiles/inspect — Read-only hardware profile compatibility check."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    device_info = body.get("device", {})
    if not device_info:
        # Default fallback to host info
        device_info = {
            "vendor": "Generic",
            "model": "Host",
            "arch": "x86_64",
            "ram_mb": 8192,
            "storage_gb": 128,
        }

    try:
        sonic_cli_path = (Path.home() / "Code" / "SonicScrewdriver" / "cli").resolve()
        if str(sonic_cli_path) not in sys.path and sonic_cli_path.exists():
            sys.path.insert(0, str(sonic_cli_path))
        from sonic.lib.mint_profiler import inspect_hardware_compatibility
        report = inspect_hardware_compatibility(device_info)
    except Exception as e:
        log.warning("Falling back for inspect: %s", e)
        ram = int(device_info.get("ram_mb", 0))
        cinnamon_ok = ram >= 4096
        xfce_ok = ram >= 2048
        preferred = "cinnamon-full" if cinnamon_ok else ("xfce-light" if xfce_ok else None)
        report = {
            "device": device_info,
            "hardware_tier": {
                "id": "pc-x86_64",
                "name": "Standard PC x86-64",
            },
            "safety_gate": "inspect (read-only, non-destructive)",
            "profiles": {
                "cinnamon-full": {"compatible": cinnamon_ok, "status": "COMPATIBLE" if cinnamon_ok else "INCOMPATIBLE"},
                "xfce-light": {"compatible": xfce_ok, "status": "COMPATIBLE" if xfce_ok else "INCOMPATIBLE"},
            },
            "preferred_profile": preferred,
            "warnings": [],
        }

    return web.json_response({"status": "ok", "assessment": report})


async def handle_list_capsules(request: web.Request) -> web.Response:
    """GET /api/runtime/capsules — List installed/staged capsules and anti-autorun authorization status."""
    programs_dir = get_ucode_programs_dir()
    capsules = []

    if programs_dir.exists():
        for candidate in sorted(programs_dir.iterdir()):
            if not candidate.is_dir():
                continue
            capsule_yaml = candidate / "capsule.yaml"
            if not capsule_yaml.exists():
                continue

            # Read capsule metadata
            state_file = candidate / ".capsule_state.json"
            state = {}
            if state_file.exists():
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                except Exception:
                    pass

            authorized = state.get("authorized", False)
            permissions = state.get("permissions", {
                "filesystem": "read_only",
                "network": False,
                "max_memory_mb": 64,
                "timeout_sec": 30.0,
            })

            capsules.append({
                "id": candidate.name,
                "path": str(candidate),
                "authorized": authorized,
                "permissions": permissions,
                "licensing": state.get("licensing", {
                    "runtime_license": "proprietary-retro-evaluation",
                    "redistributable": False,
                }),
                "has_anti_autorun_gate": True,
            })

    return web.json_response({"status": "ok", "capsules": capsules, "count": len(capsules)})


async def handle_authorize_capsule(request: web.Request) -> web.Response:
    """POST /api/runtime/capsules/{capsule_id}/authorize — Explicit authorization gate."""
    capsule_id = request.match_info.get("capsule_id")
    if not capsule_id:
        return web.json_response({"status": "error", "message": "capsule_id required"}, status=400)

    programs_dir = get_ucode_programs_dir()
    capsule_path = programs_dir / capsule_id
    if not capsule_path.exists() or not (capsule_path / "capsule.yaml").exists():
        return web.json_response({"status": "error", "message": f"Capsule '{capsule_id}' not found"}, status=404)

    try:
        ucode_path = (Path.home() / "Code" / "uCode").resolve()
        if str(ucode_path) not in sys.path and ucode_path.exists():
            sys.path.insert(0, str(ucode_path))
        from ucode_runtime.capsule_package import CapsulePackage
        auth_state = CapsulePackage.authorize_capsule(capsule_path, authorized_by="user")
    except Exception:
        # Fallback state file write
        state_file = capsule_path / ".capsule_state.json"
        auth_state = {"capsule_id": capsule_id, "authorized": True, "authorized_by": "user"}
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(auth_state, f, indent=2)

    return web.json_response({"status": "ok", "capsule_id": capsule_id, "state": auth_state})


async def handle_revoke_capsule(request: web.Request) -> web.Response:
    """POST /api/runtime/capsules/{capsule_id}/revoke — Revoke authorization."""
    capsule_id = request.match_info.get("capsule_id")
    if not capsule_id:
        return web.json_response({"status": "error", "message": "capsule_id required"}, status=400)

    programs_dir = get_ucode_programs_dir()
    capsule_path = programs_dir / capsule_id
    if not capsule_path.exists():
        return web.json_response({"status": "error", "message": f"Capsule '{capsule_id}' not found"}, status=404)

    state_file = capsule_path / ".capsule_state.json"
    state = {}
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    state["authorized"] = False
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    return web.json_response({"status": "ok", "capsule_id": capsule_id, "state": state})


def register_runtime_device_routes(app: web.Application) -> None:
    """Register runtime device delivery and capsule governance endpoints."""
    app.router.add_get("/api/runtime/profiles", handle_get_profiles)
    app.router.add_post("/api/runtime/profiles/inspect", handle_inspect_device)
    app.router.add_get("/api/runtime/capsules", handle_list_capsules)
    app.router.add_post("/api/runtime/capsules/{capsule_id}/authorize", handle_authorize_capsule)
    app.router.add_post("/api/runtime/capsules/{capsule_id}/revoke", handle_revoke_capsule)
    log.info("Runtime device delivery & capsule governance routes registered")
