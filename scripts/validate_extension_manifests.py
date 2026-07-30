#!/usr/bin/env python3
"""Validate uCore extension manifests and dependency graph.

Checks:
- Required fields and allowed fields
- Field types and dotted-path syntax
- Duplicate extension IDs
- Dependency self-reference
- Dependency cycles across discovered manifests + built-ins
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.extensions.manifest import ExtensionManifest  # noqa: E402

MANIFEST_FILE_NAME = "ucore-extension.json"

# Built-ins are always valid dependency targets from manifest perspective.
BUILTIN_IDS = {
    "ucore-core",
    "ucore-skills",
    "ucore-surfaces",
    "ucore-secrets",
    "ucore-tools",
    "uflow",
    "uknowledge",
}


def _default_paths() -> list[Path]:
    return [
        ROOT / "backend" / "app" / "extensions" / "manifests",
        Path.home() / ".ucore" / "extensions",
    ]


def _extra_paths_from_env() -> list[Path]:
    raw = os.environ.get("UCORE_EXTENSION_MANIFEST_PATHS", "").strip()
    if not raw:
        return []
    paths = []
    for part in raw.split(":"):
        candidate = part.strip()
        if candidate:
            paths.append(Path(candidate).expanduser())
    return paths


def _discover_manifest_files() -> list[Path]:
    files: list[Path] = []
    for base in [*_default_paths(), *_extra_paths_from_env()]:
        if not base.exists():
            continue
        files.extend(sorted(base.rglob(MANIFEST_FILE_NAME)))
    return files


def _load_and_validate(files: list[Path]) -> tuple[dict[str, ExtensionManifest], list[str]]:
    manifests: dict[str, ExtensionManifest] = {}
    errors: list[str] = []

    for mf in files:
        try:
            raw = json.loads(mf.read_text(encoding="utf-8"))
            manifest = ExtensionManifest.from_dict(raw)
        except Exception as exc:
            errors.append(f"{mf}: invalid manifest: {exc}")
            continue

        existing = manifests.get(manifest.id)
        if existing is not None:
            errors.append(
                f"{mf}: duplicate extension id '{manifest.id}' "
                f"(already declared by another manifest)"
            )
            continue

        manifests[manifest.id] = manifest

    return manifests, errors


def _detect_cycles(manifests: dict[str, ExtensionManifest]) -> list[list[str]]:
    known_ids = set(manifests) | BUILTIN_IDS
    graph: dict[str, list[str]] = defaultdict(list)

    for ext_id, manifest in manifests.items():
        for dep in manifest.dependencies:
            if dep not in known_ids:
                # Unknown deps are treated as contract errors.
                graph[ext_id].append(f"__UNKNOWN__:{dep}")
            else:
                graph[ext_id].append(dep)

    cycles: list[list[str]] = []
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)

        for nxt in graph.get(node, []):
            if nxt.startswith("__UNKNOWN__:"):
                continue
            # Only traverse external manifests for cycle detection.
            if nxt not in manifests:
                continue
            st = state.get(nxt, 0)
            if st == 0:
                visit(nxt)
            elif st == 1:
                start = stack.index(nxt)
                cycles.append(stack[start:] + [nxt])

        stack.pop()
        state[node] = 2

    for node in manifests:
        if state.get(node, 0) == 0:
            visit(node)

    return cycles


def main() -> int:
    files = _discover_manifest_files()
    manifests, errors = _load_and_validate(files)

    # Unknown dependencies are surfaced as explicit errors.
    known_ids = set(manifests) | BUILTIN_IDS
    for ext_id, manifest in manifests.items():
        for dep in manifest.dependencies:
            if dep not in known_ids:
                errors.append(
                    f"{ext_id}: unknown dependency '{dep}' "
                    "(must reference a built-in or discovered extension id)"
                )

    cycles = _detect_cycles(manifests)
    for cycle in cycles:
        errors.append(f"dependency cycle detected: {' -> '.join(cycle)}")

    print(f"Manifest files discovered: {len(files)}")
    print(f"Extension manifests parsed: {len(manifests)}")

    if errors:
        print("\nExtension manifest validation FAILED:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Extension manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
