#!/usr/bin/env python3
"""Validate split-repo publishable Python package layouts.

Checks package metadata/layout for:
- uFlow (`uflow`)
- uKnowledge (`uknowledge`)
- uCode runtime (`ucode_runtime`)
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

CODE_ROOT = Path(os.environ.get("UDOS_ROOT", str(Path.home() / "Code"))).expanduser()
STRICT_MODE = os.environ.get("UCORE_SPLIT_REPO_PACKAGING_STRICT", "0").lower() in {
    "1",
    "true",
    "yes",
}


@dataclass(frozen=True)
class PackageSpec:
    repo: str
    pyproject: str
    package_dir: str


SPECS = [
    PackageSpec("uFlow", "uflow", "uflow"),
    PackageSpec("uKnowledge", "uknowledge", "uknowledge"),
    PackageSpec("uCode", "ucode-runtime", "ucode_runtime"),
]


def _load_pyproject(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def _validate_spec(spec: PackageSpec) -> list[str]:
    errors: list[str] = []
    repo_root = CODE_ROOT / spec.repo
    pyproject_path = repo_root / "pyproject.toml"
    package_path = repo_root / spec.package_dir

    if not repo_root.exists():
        return [f"{spec.repo}: repo path missing: {repo_root}"]
    if not pyproject_path.exists():
        return [f"{spec.repo}: missing pyproject.toml"]
    if not package_path.exists() or not package_path.is_dir():
        errors.append(f"{spec.repo}: missing package directory {spec.package_dir}")

    init_file = package_path / "__init__.py"
    if not init_file.exists():
        errors.append(f"{spec.repo}: missing {spec.package_dir}/__init__.py")

    data = _load_pyproject(pyproject_path)
    project = data.get("project")
    if not isinstance(project, dict):
        errors.append(f"{spec.repo}: pyproject missing [project] table")
        return errors

    name = project.get("name")
    if name != spec.pyproject:
        errors.append(
            f"{spec.repo}: project.name mismatch (expected '{spec.pyproject}', got '{name}')"
        )

    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        errors.append(f"{spec.repo}: project.version missing or invalid")

    readme = project.get("readme")
    if not isinstance(readme, str):
        errors.append(f"{spec.repo}: project.readme missing or invalid")

    requires_python = project.get("requires-python")
    if not isinstance(requires_python, str):
        errors.append(f"{spec.repo}: project.requires-python missing or invalid")

    return errors


def main() -> int:
    missing_repos = [spec.repo for spec in SPECS if not (CODE_ROOT / spec.repo).exists()]
    if missing_repos and not STRICT_MODE:
        print("Split-repo packaging validation skipped: external repos unavailable")
        for repo in missing_repos:
            print(f"- missing repo: {CODE_ROOT / repo}")
        print("Set UCORE_SPLIT_REPO_PACKAGING_STRICT=1 to enforce hard failure")
        return 0

    all_errors: list[str] = []

    for spec in SPECS:
        errs = _validate_spec(spec)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK: {spec.repo} ({spec.pyproject})")

    if all_errors:
        print("\nSplit-repo packaging validation FAILED:")
        for err in all_errors:
            print(f"- {err}")
        return 1

    print("Split-repo packaging validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
