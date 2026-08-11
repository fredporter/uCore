#!/usr/bin/env python3
"""Runtime probe for documentation endpoints against a running uCore backend."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENDPOINTS: list[tuple[str, str]] = [
    ("GET", "/api/docs"),
    ("GET", "/api/docs/sites"),
    ("GET", "/api/docs/global-knowledge"),
    ("GET", "/api/docs/export"),
    ("GET", "/api/docs/courses"),
    ("GET", "/api/docs/notebooks"),
    ("GET", "/api/docs/repo-docs"),
]


def _probe(base_url: str, method: str, path: str, timeout: float) -> tuple[int, str]:
    url = f"{base_url.rstrip('/')}{path}"
    req = Request(url=url, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(256).decode("utf-8", errors="replace")
            return int(resp.status), body
    except HTTPError as exc:
        body = exc.read(256).decode("utf-8", errors="replace")
        return int(exc.code), body
    except URLError as exc:
        return 0, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe documentation endpoints")
    parser.add_argument("--base-url", default="http://127.0.0.1:8484", help="uCore base URL")
    parser.add_argument("--timeout", type=float, default=3.0, help="Request timeout seconds")
    args = parser.parse_args()

    results: list[dict[str, object]] = []
    failed = False

    for method, path in ENDPOINTS:
        status, body = _probe(args.base_url, method, path, args.timeout)
        ok = status == 200
        if not ok:
            failed = True
        results.append({
            "method": method,
            "path": path,
            "status": status,
            "ok": ok,
            "sample": body,
        })

    print(json.dumps({"base_url": args.base_url, "results": results}, indent=2))
    if failed:
        print("[FAIL] One or more documentation endpoints are unavailable.")
        return 1

    print("Documentation runtime probe passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
