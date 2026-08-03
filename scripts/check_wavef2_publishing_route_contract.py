#!/usr/bin/env python3
"""Validate Wave F2 publishing route contract scaffold in udos-publishing."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

EXPECTED_METHODS = {
    "create_story",
    "get_story",
    "list_visible",
    "get_stats",
    "get_contract",
    "health",
}

EXPECTED_CONTRACT_KEYS = {
    "guide_name",
    "place_name",
    "frontmatter_keys",
    "tag_keys",
    "location_keys",
    "beacon_keys",
    "portal_keys",
}


def _collect_methods(routes_file: Path) -> set[str]:
    module = ast.parse(routes_file.read_text(encoding="utf-8"), filename=str(routes_file))
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "PublishingRoutes":
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()


def _collect_contract_fields(contract_file: Path) -> set[str]:
    module = ast.parse(contract_file.read_text(encoding="utf-8"), filename=str(contract_file))
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "PublishingMirrorContract":
            fields: set[str] = set()
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    fields.add(child.target.id)
            return fields
    return set()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Wave F2 publishing route contract scaffold")
    parser.add_argument(
        "--repo",
        default="/Users/fredbook/Code/udos-publishing",
        help="Path to udos-publishing repository",
    )
    args = parser.parse_args()

    repo = Path(args.repo)
    routes_file = repo / "udos_publishing" / "src" / "routes.py"
    contract_file = repo / "udos_publishing" / "src" / "contracts.py"

    failures: list[str] = []
    if not routes_file.exists():
        failures.append(f"missing routes file: {routes_file}")
    if not contract_file.exists():
        failures.append(f"missing contract file: {contract_file}")

    methods = _collect_methods(routes_file) if routes_file.exists() else set()
    contract_fields = _collect_contract_fields(contract_file) if contract_file.exists() else set()

    missing_methods = sorted(EXPECTED_METHODS - methods)
    missing_contract_fields = sorted(EXPECTED_CONTRACT_KEYS - contract_fields)

    if missing_methods:
        failures.append(f"missing route methods: {', '.join(missing_methods)}")
    if missing_contract_fields:
        failures.append(
            f"missing contract keys: {', '.join(missing_contract_fields)}"
        )

    payload = {
        "repo": str(repo),
        "routes_file": str(routes_file),
        "contract_file": str(contract_file),
        "found_methods": sorted(methods),
        "found_contract_fields": sorted(contract_fields),
        "missing_methods": missing_methods,
        "missing_contract_fields": missing_contract_fields,
        "ok": not failures,
    }
    print(json.dumps(payload, indent=2))

    if failures:
        print("[FAIL] Wave F2 publishing route contract check failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Wave F2 publishing route contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
