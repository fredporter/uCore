#!/usr/bin/env python3
"""Verify bundled host authorities and the required companion uCode runtime.

The historical filename is retained for CI compatibility. Missing required
packages fail; bundled uFlow/knowledge/identity never require sibling repos.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = Path(os.environ.get("UDOS_ROOT", str(Path.home() / "Code"))).expanduser()

REPO_PATHS = {
    "uCore-backend": ROOT / "backend",
    "uCode": Path(os.environ.get("UCORE_UCODE_PATH", str(CODE_ROOT / "uCode"))).expanduser(),
}


def _ensure_path(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Required path missing: {path}")
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


def _check_imports() -> None:
    import app.flow.routes
    import app.knowledge.routes
    import app.identity.routes
    import ucode_runtime.ceefax
    from ucode_runtime.runtime_info import runtime_info
    if "terminal.basic-immediate" not in runtime_info()["capabilities"]:
        raise RuntimeError("The companion uCode revision lacks the native BASIC Terminal contract")


def _check_registry_routes() -> None:
    from app.core.snackbar import create_app
    from app.extensions.registry import registry

    # Runtime-owned routes are mounted by the host, separately from optional APIs.
    app = create_app()

    status = registry.status()
    ext_by_id = {e["id"]: e for e in status.get("extensions", [])}

    expected_extensions = [
        "uflow",
        "uknowledge",
        "uidentity",
    ]
    missing_ext = [
        ext for ext in expected_extensions
        if ext not in ext_by_id or not ext_by_id[ext].get("loaded")
    ]
    if missing_ext:
        raise RuntimeError(f"Expected loaded extensions missing: {missing_ext}")

    paths: set[str] = set()
    route_pairs: set[tuple[str, str]] = set()
    for route in app.router.routes():
        info = route.get_info()
        p = info.get("path") or info.get("formatter")
        if p:
            paths.add(p)
            method = str(getattr(route, "method", "")).upper()
            if method != "HEAD":
                route_pairs.add((method, p))

    required_routes = {
        "/api/workflows",
        "/api/knowledge/search",
        "/api/ceefax/pages",
        "/api/budget/plugin/status",
        "/api/identity/plugin/profile",
        "/api/identity/variables",
        "/api/identity/stories",
        "/api/identity/stories/{story_id}",
        "/api/identity/privacy/{resource_id}",
        "/api/identity/wordpress/map-outbound",
        "/api/identity/wordpress/map-inbound",
    }
    missing_routes = sorted(required_routes - paths)
    if missing_routes:
        raise RuntimeError(f"Expected routes missing: {missing_routes}")

    required_identity_route_pairs = {
        ("GET", "/api/identity/plugin/profile"),
        ("GET", "/api/identity/plugin/session"),
        ("GET", "/api/identity/variables"),
        ("PUT", "/api/identity/variables"),
        ("POST", "/api/identity/stories"),
        ("GET", "/api/identity/stories/{story_id}"),
        ("PATCH", "/api/identity/stories/{story_id}"),
        ("GET", "/api/identity/privacy/{resource_id}"),
        ("PUT", "/api/identity/privacy/{resource_id}"),
        ("POST", "/api/identity/wordpress/map-outbound"),
        ("POST", "/api/identity/wordpress/map-inbound"),
    }
    missing_identity_pairs = sorted(required_identity_route_pairs - route_pairs)
    if missing_identity_pairs:
        raise RuntimeError(
            f"Expected identity method/path pairs missing: {missing_identity_pairs}"
        )

    print(
        "Registry route smoke passed "
        f"(route_count={len(paths)}, identity_pairs={len(required_identity_route_pairs)})"
    )


def main() -> int:
    for name, path in REPO_PATHS.items():
        _ensure_path(path)
        print(f"Path OK: {name} -> {path}")
    os.environ.setdefault("UCORE_UCODE_PATH", str(REPO_PATHS["uCode"]))

    _check_imports()
    print("Bundled authority and companion runtime imports passed")

    _check_registry_routes()
    print("Split-repo smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
