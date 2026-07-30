#!/usr/bin/env python3
"""Split-repo install/import smoke checks for CI and local development.

This script verifies that external repos are importable and that uCore can
register routes with discovered extension manifests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = Path(os.environ.get("UDOS_ROOT", str(Path.home() / "Code"))).expanduser()

REPO_PATHS = {
    "uCore-backend": ROOT / "backend",
    "uFlow": CODE_ROOT / "uFlow",
    "uKnowledge": CODE_ROOT / "uKnowledge",
    "uCode": CODE_ROOT / "uCode",
    "udos-budget": CODE_ROOT / "udos-budget",
    "udos-identity": CODE_ROOT / "udos-identity",
}

STRICT_MODE = os.environ.get("UCORE_SPLIT_REPO_SMOKE_STRICT", "0").lower() in {
    "1",
    "true",
    "yes",
}


def _ensure_path(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Required path missing: {path}")
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


def _missing_external_repo_paths() -> list[Path]:
    missing: list[Path] = []
    for name, path in REPO_PATHS.items():
        if name == "uCore-backend":
            continue
        if not path.exists():
            missing.append(path)
    return missing


def _check_imports() -> None:
    # External repos and uCore backend need to be importable from source.
    import uflow.routes  # noqa: F401
    import uknowledge.routes  # noqa: F401
    import ucode_runtime.ceefax  # noqa: F401
    import udos_budget.routes  # noqa: F401
    import udos_identity.routes  # noqa: F401


def _check_registry_routes() -> None:
    from aiohttp import web

    from app.api.routes import register_routes
    from app.extensions.registry import registry

    app = web.Application()
    register_routes(app)

    status = registry.status()
    ext_by_id = {e["id"]: e for e in status.get("extensions", [])}

    expected_extensions = [
        "uflow",
        "uknowledge",
        "udos-budget",
        "udos-identity",
    ]
    missing_ext = [
        ext for ext in expected_extensions
        if ext not in ext_by_id or not ext_by_id[ext].get("loaded")
    ]
    if missing_ext:
        raise RuntimeError(f"Expected loaded extensions missing: {missing_ext}")

    paths: set[str] = set()
    for route in app.router.routes():
        info = route.get_info()
        p = info.get("path") or info.get("formatter")
        if p:
            paths.add(p)

    required_routes = {
        "/api/workflows",
        "/api/knowledge/search",
        "/api/ceefax/pages",
        "/api/budget/plugin/status",
        "/api/identity/plugin/profile",
    }
    missing_routes = sorted(required_routes - paths)
    if missing_routes:
        raise RuntimeError(f"Expected routes missing: {missing_routes}")

    print(f"Registry route smoke passed (route_count={len(paths)})")


def main() -> int:
    missing_external = _missing_external_repo_paths()
    if missing_external and not STRICT_MODE:
        print("Split-repo smoke skipped: external repos unavailable in this environment")
        for p in missing_external:
            print(f"- missing: {p}")
        print("Set UCORE_SPLIT_REPO_SMOKE_STRICT=1 to enforce hard failure")
        return 0

    for name, path in REPO_PATHS.items():
        _ensure_path(path)
        print(f"Path OK: {name} -> {path}")

    os.environ.setdefault("UCORE_UFLOW_PATH", str(REPO_PATHS["uFlow"]))
    os.environ.setdefault("UCORE_UKNOWLEDGE_PATH", str(REPO_PATHS["uKnowledge"]))
    os.environ.setdefault("UCORE_UCODE_PATH", str(REPO_PATHS["uCode"]))
    os.environ.setdefault(
        "UCORE_EXTENSION_MANIFEST_PATHS",
        f"{REPO_PATHS['udos-budget']}:{REPO_PATHS['udos-identity']}",
    )

    _check_imports()
    print("External import smoke passed")

    _check_registry_routes()
    print("Split-repo smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
