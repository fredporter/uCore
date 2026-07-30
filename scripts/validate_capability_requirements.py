#!/usr/bin/env python3
"""Fail CI when preflighted capability keys are missing requirements entries.

This script enforces a one-way coverage rule:
- Any capability key referenced by preflight call sites must exist in
  config/capability_requirements.json.

It intentionally does not fail on extra entries in the requirements file,
which are allowed for upcoming capability rollout work.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
REQ_FILE = ROOT / "config" / "capability_requirements.json"

# Scan only runtime code paths where preflight capability keys are expected.
SCAN_GLOBS: tuple[str, ...] = (
    "frontend-vue/src/**/*.ts",
    "frontend-vue/src/**/*.vue",
    "backend/app/**/*.py",
)

# Direct call sites that should carry canonical capability keys.
DIRECT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ensureCapabilityReady\(\s*[\"']([a-z0-9_.-]+)[\"']"),
    re.compile(r"getCapabilityPreflight\(\s*[\"']([a-z0-9_.-]+)[\"']"),
    re.compile(r"_evaluate_capability\(\s*[\"']([a-z0-9_.-]+)[\"']"),
)

# Array call shape: getCapabilitiesReadiness(["a", "b", ...])
READINESS_ARRAY_PATTERN = re.compile(
    r"getCapabilitiesReadiness\(\s*\[(.*?)\]", re.DOTALL
)
QUOTED_STRING_PATTERN = re.compile(r"[\"']([a-z0-9_.-]+)[\"']")


def _iter_files() -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in SCAN_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def _load_requirements() -> set[str]:
    if not REQ_FILE.exists():
        print(f"[FAIL] Requirements file missing: {REQ_FILE}")
        raise SystemExit(1)

    try:
        payload = json.loads(REQ_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[FAIL] Invalid JSON in {REQ_FILE}: {exc}")
        raise SystemExit(1) from exc

    if not isinstance(payload, dict):
        print(f"[FAIL] Expected top-level object in {REQ_FILE}")
        raise SystemExit(1)

    return set(payload.keys())


def _discover_capabilities() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}

    for path in _iter_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="ignore")

        for pattern in DIRECT_PATTERNS:
            for match in pattern.finditer(text):
                key = match.group(1).strip()
                if key:
                    found.setdefault(key, set()).add(str(rel))

        for call in READINESS_ARRAY_PATTERN.finditer(text):
            array_body = call.group(1)
            for item in QUOTED_STRING_PATTERN.finditer(array_body):
                key = item.group(1).strip()
                if key:
                    found.setdefault(key, set()).add(str(rel))

    return found


def main() -> int:
    declared = _load_requirements()
    discovered = _discover_capabilities()

    if not discovered:
        print("[WARN] No capability keys discovered in preflight call sites.")
        print("Capability requirements check skipped.")
        return 0

    missing = sorted(key for key in discovered if key not in declared)

    print(f"Discovered capability keys: {len(discovered)}")
    print(f"Declared capability requirements: {len(declared)}")

    if not missing:
        print("Capability requirements coverage check passed.")
        return 0

    print("[FAIL] Missing capability requirement entries:")
    for key in missing:
        refs = ", ".join(sorted(discovered[key]))
        print(f"- {key} (referenced in: {refs})")

    print("---")
    print("Add missing keys to config/capability_requirements.json before merge.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
