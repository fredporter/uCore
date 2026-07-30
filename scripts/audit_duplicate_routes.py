#!/usr/bin/env python3
"""Audit duplicate HTTP route registrations across backend API modules.

Usage:
  python scripts/audit_duplicate_routes.py
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = [ROOT / "backend" / "app" / "api", ROOT / "backend" / "app" / "extensions"]

PATTERN = re.compile(
    r"app\.router\.add_(get|post|put|delete|patch)\(\s*\"([^\"]+)\"",
    re.IGNORECASE,
)


def main() -> int:
    seen: dict[tuple[str, str], list[str]] = defaultdict(list)

    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for py_file in base.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8", errors="replace")
            rel = py_file.relative_to(ROOT)
            for i, line in enumerate(text.splitlines(), start=1):
                m = PATTERN.search(line)
                if not m:
                    continue
                method = m.group(1).upper()
                route = m.group(2)
                seen[(method, route)].append(f"{rel}:{i}")

    duplicates = {k: v for k, v in seen.items() if len(v) > 1}

    print("Route audit summary")
    print(f"- total unique routes: {len(seen)}")
    print(f"- duplicate routes: {len(duplicates)}")

    if not duplicates:
        print("No duplicate routes detected.")
        return 0

    print("\nDuplicates:")
    for (method, route), refs in sorted(duplicates.items()):
        print(f"- {method} {route}")
        for ref in refs:
            print(f"  - {ref}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
