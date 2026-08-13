#!/usr/bin/env python3
"""Verify uCore documentation route contract used by Documentation surface."""

from __future__ import annotations

import sys
from pathlib import Path

from collections.abc import Iterable

from aiohttp import web

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if _BACKEND.exists() and str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.surfaces.documentation_api import register_documentation_routes

EXPECTED: set[tuple[str, str]] = {
    ("GET", "/api/docs"),
    ("GET", "/api/docs/sites"),
    ("GET", "/api/docs/global-knowledge"),
    ("GET", "/api/docs/serve/{site}/"),
    ("GET", "/api/docs/global-knowledge/{section}/"),
    ("GET", "/api/docs/export"),
    ("POST", "/api/docs/export"),
    ("GET", "/api/docs/courses"),
    ("GET", "/api/docs/notebooks"),
    ("GET", "/api/docs/repo-docs"),
    ("POST", "/api/docs/mirror/sync"),
    ("GET", "/api/docs/mirror/status"),
    ("POST", "/api/docs/mirror/push"),
    ("GET", "/api/docs/mirror/diff/{repo}/{path}"),
}


def _iter_routes(app: web.Application) -> Iterable[tuple[str, str]]:
    for route in app.router.routes():
        info = route.get_info()
        path = info.get("path")
        if not path:
            resource = getattr(route, "resource", None)
            canonical = getattr(resource, "canonical", None)
            path = canonical if canonical else ""
        method = str(getattr(route, "method", "")).upper()
        if method == "HEAD":
            continue
        yield method, str(path)


def main() -> int:
    app = web.Application()
    register_documentation_routes(app)

    actual = set(_iter_routes(app))
    missing = sorted(EXPECTED - actual)
    extra = sorted(actual - EXPECTED)

    print(f"Expected routes: {len(EXPECTED)}")
    print(f"Actual routes:   {len(actual)}")

    if not missing and not extra:
        print("Documentation route contract check passed.")
        return 0

    if missing:
        print("[FAIL] Missing routes:")
        for method, path in missing:
            print(f"- {method} {path}")

    if extra:
        print("[FAIL] Unexpected extra routes:")
        for method, path in extra:
            print(f"- {method} {path}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
