#!/usr/bin/env python3
"""Validate SnackMachine extension contract compatibility with uCore.

This check is intended for CI and local verification.
It validates the SnackMachine capability payload shape and ensures
uCore routing/menu wiring still points at the canonical SnackMachine surface.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNACKMACHINE_PATH = Path.home() / "Code" / "SnackMachine"

EXPECTED_ID = "snackmachine-extension"
REQUIRED_KEYS = {"id", "version", "display_name", "provides", "requires_ucore", "status"}
REQUIRED_CAPABILITIES = {
    "snacks.catalog",
    "snacks.packages.install",
    "snacks.packages.uninstall",
    "snacks.packages.list",
}


def _fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def _load_capability_manifest(repo_path: Path) -> dict:
    capability_file = repo_path / "examples" / "capability_response.json"
    if capability_file.exists():
        return _read_json(capability_file)

    # Fallback for environments without examples file.
    manifest_module = repo_path / "src" / "snackmachine_ext" / "manifest.py"
    if not manifest_module.exists():
        raise FileNotFoundError(
            "missing both examples/capability_response.json and src/snackmachine_ext/manifest.py",
        )

    if str(repo_path / "src") not in sys.path:
        sys.path.insert(0, str(repo_path / "src"))
    from snackmachine_ext.manifest import capability_manifest  # type: ignore

    manifest = capability_manifest()
    if not isinstance(manifest, dict):
        raise ValueError("capability_manifest() must return a dict")
    return manifest


def _validate_manifest_payload(payload: dict) -> list[str]:
    errors: list[str] = []

    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        errors.append(f"missing required keys: {sorted(missing)}")

    if payload.get("id") != EXPECTED_ID:
        errors.append(f"id must equal '{EXPECTED_ID}'")

    provides = payload.get("provides")
    if not isinstance(provides, list) or not all(isinstance(v, str) for v in provides):
        errors.append("provides must be a list[str]")
        provides_set: set[str] = set()
    else:
        provides_set = set(provides)

    missing_caps = sorted(REQUIRED_CAPABILITIES - provides_set)
    if missing_caps:
        errors.append(f"missing required capabilities: {missing_caps}")

    if not isinstance(payload.get("version"), str) or not payload.get("version"):
        errors.append("version must be a non-empty string")

    if not isinstance(payload.get("display_name"), str) or not payload.get("display_name"):
        errors.append("display_name must be a non-empty string")

    if not isinstance(payload.get("requires_ucore"), str) or not payload.get("requires_ucore"):
        errors.append("requires_ucore must be a non-empty string")

    if payload.get("status") not in {"active", "disabled", "deprecated"}:
        errors.append("status must be one of: active, disabled, deprecated")

    return errors


def _validate_ucore_wiring() -> list[str]:
    errors: list[str] = []

    menu_file = ROOT / "backend" / "app" / "menu" / "unified_menu_simple.py"
    menu_text = menu_file.read_text(encoding="utf-8")
    if '"snackmachine-extension": "http://localhost:5175/server?tab=snacks"' not in menu_text:
        errors.append(
            "backend menu extension link for snackmachine-extension must target "
            "http://localhost:5175/server?tab=snacks",
        )

    router_file = ROOT / "frontend-vue" / "src" / "router" / "index.ts"
    router_text = router_file.read_text(encoding="utf-8")
    if "path: '/snackmachine/:pathMatch(.*)*'" not in router_text:
        errors.append("frontend router must define /snackmachine route")
    if "return '/server?tab=snacks'" not in router_text:
        errors.append("/snackmachine router redirect must resolve to /server?tab=snacks")

    return errors


def main() -> int:
    repo_path = Path(
        os.environ.get("UCORE_SNACKMACHINE_PATH", str(DEFAULT_SNACKMACHINE_PATH)),
    ).expanduser()

    if not repo_path.exists():
        return _fail(
            "SnackMachine repository not found at "
            f"{repo_path}. Set UCORE_SNACKMACHINE_PATH to override.",
        )

    try:
        payload = _load_capability_manifest(repo_path)
    except Exception as exc:
        return _fail(f"unable to load SnackMachine capability payload: {exc}")

    errors = _validate_manifest_payload(payload)
    errors.extend(_validate_ucore_wiring())

    print(f"SnackMachine path: {repo_path}")
    print(f"Capability id: {payload.get('id')}")
    print(f"Capabilities count: {len(payload.get('provides', []))}")

    if errors:
        print("\nSnackMachine contract validation FAILED:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("SnackMachine contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
