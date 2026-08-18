#!/usr/bin/env python3
"""Read-only inventory for consolidating uDOS runtime state into UDOS_HOME."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


LEGACY_ROOTS = (
    Path("~/.ucore"),
    Path("~/.udos"),
    Path("~/.config/udos"),
    Path("~/.local/share/udos"),
)
VAULT_ROOTS = (Path("~/Vault"), Path("~/Shared"), Path("~/Public"))


def directory_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        for name in files:
            try:
                total += (root_path / name).stat(follow_symlinks=False).st_size
            except (FileNotFoundError, PermissionError):
                continue
    return total


def describe(path: Path) -> dict[str, object]:
    resolved = path.expanduser()
    exists = resolved.exists()
    return {
        "path": str(resolved),
        "exists": exists,
        "kind": "symlink" if resolved.is_symlink() else "directory" if resolved.is_dir() else "file" if resolved.is_file() else "missing",
        "bytes": directory_size(resolved) if resolved.is_dir() else resolved.stat().st_size if exists else 0,
    }


def inventory(target: Path) -> dict[str, object]:
    return {
        "target": describe(target),
        "legacy_runtime_roots": [describe(path) for path in LEGACY_ROOTS],
        "portable_vault_roots": [describe(path) for path in VAULT_ROOTS],
        "policy": {
            "move": "runtime state only, after collision review and backup",
            "keep": [str(path) for path in VAULT_ROOTS],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(os.environ.get("UDOS_HOME", "~/Code/.udos")),
        help="proposed canonical runtime home (default: UDOS_HOME or ~/Code/.udos)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = inventory(args.target.expanduser())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Proposed UDOS_HOME: {report['target']['path']}")
        for group in ("legacy_runtime_roots", "portable_vault_roots"):
            print(f"\n{group.replace('_', ' ').title()}:")
            for item in report[group]:
                print(f"  {item['path']}: {item['kind']}, {item['bytes']} bytes")
        print("\nNo files were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
