#!/usr/bin/env python3
"""Fail when forbidden legacy settings or removed host modules reappear.

This enforces the hard-cut direction:
- no stale fallback env toggles in active docs/code/config
- no restored in-core modules that were intentionally removed
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_GLOBS: tuple[str, ...] = (
    "backend/**/*.py",
    "config/**/*.json",
    "config/**/*.yaml",
    "config/**/*.yml",
    "docs/**/*.md",
    "scripts/**/*.py",
)

EXCLUDE_PARTS: tuple[str, ...] = (
    "/docs/archive/",
    "/docs/archived/",
    "/docs/legacy/",
    "/frontend-vue/src/vendor/",
    "/.tasker/archive/",
)

FORBIDDEN_SETTINGS: tuple[str, ...] = (
    "UCORE_UCODE_RUNTIME_REQUIRE_EXTERNAL",
    "UCORE_WORKFLOW_FALLBACK_TO_CORE",
    "UCORE_KNOWLEDGE_FALLBACK_TO_CORE",
)

REMOVED_MODULES: tuple[str, ...] = (
    "backend/app/api/workflows.py",
    "backend/app/api/knowledge.py",
    "backend/app/api/terminal_runtime.py",
    "backend/app/ucode/ceefax.py",
    "backend/app/ucode/bbcsdl.py",
    "backend/app/menu/snackbar_menu.py",
)


def _iter_active_files() -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for pattern in SCAN_GLOBS:
        for path in ROOT.glob(pattern):
            if not path.is_file() or path in seen:
                continue
            p = str(path)
            if any(part in p for part in EXCLUDE_PARTS):
                continue
            seen.add(path)
            out.append(path)
    return out


def main() -> int:
    failures: list[str] = []
    self_rel = Path("scripts/validate_legacy_settings_cleanup.py")

    files = _iter_active_files()
    for path in files:
        rel = path.relative_to(ROOT)
        if rel == self_rel:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for key in FORBIDDEN_SETTINGS:
            if key in text:
                msg = f"forbidden legacy setting '{key}' found in {rel}"
                failures.append(msg)

    for rel_path in REMOVED_MODULES:
        if (ROOT / rel_path).exists():
            failures.append(f"removed host module reintroduced: {rel_path}")

    if failures:
        print("[FAIL] Legacy cleanup validation failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Legacy cleanup validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
