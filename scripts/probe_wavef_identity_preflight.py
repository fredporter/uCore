#!/usr/bin/env python3
"""Probe Wave F capability preflight endpoints on a running uCore instance."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CAPABILITIES: tuple[str, ...] = (
    "identity_gateway",
    "wordpress_gateway",
)


def _request_json(url: str, timeout: float) -> tuple[int, dict[str, object] | None, str]:
    req = Request(url=url, method="GET")
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body else None
            if not isinstance(payload, dict):
                payload = None
            return int(resp.status), payload, body[:300]
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        payload = json.loads(body) if body else None
        if not isinstance(payload, dict):
            payload = None
        return int(exc.code), payload, body[:300]
    except URLError as exc:
        return 0, None, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Wave F capability preflight")
    parser.add_argument("--base-url", default="http://127.0.0.1:8484", help="uCore base URL")
    parser.add_argument("--timeout", type=float, default=3.0, help="Request timeout seconds")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    failures: list[str] = []
    results: list[dict[str, object]] = []

    for capability in CAPABILITIES:
        status, payload, sample = _request_json(
            f"{base}/api/capabilities/{capability}/preflight",
            args.timeout,
        )
        ok_status = status in (200, 412)
        ok_shape = bool(payload) and payload.get("capability") == capability
        if not ok_status:
            failures.append(f"{capability}: expected HTTP 200/412, got {status}")
        if not ok_shape:
            failures.append(f"{capability}: response payload missing expected capability field")

        results.append({
            "capability": capability,
            "status": status,
            "ok_status": ok_status,
            "ok_shape": ok_shape,
            "payload": payload,
            "sample": sample,
        })

    print(json.dumps({"base_url": base, "results": results}, indent=2))

    if failures:
        print("[FAIL] Wave F capability preflight probe failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Wave F capability preflight probe passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
