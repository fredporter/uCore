#!/usr/bin/env python3
"""Validate uCore's bundled authorities and companion uCode package metadata.

Historical script name retained; required packages never silently skip.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = Path(os.environ.get("UDOS_ROOT", str(Path.home() / "Code"))).expanduser()
@dataclass(frozen=True)
class PackageSpec:
    repo: str
    pyproject: str
    package_dir: str
    project_dir: str = ""


SPECS = [
    PackageSpec("uCore", "ucore", "app", "backend"),
    PackageSpec("uCode", "ucode-runtime", "ucode_runtime"),
]


def _load_pyproject(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def _validate_spec(spec: PackageSpec) -> list[str]:
    errors: list[str] = []
    base = ROOT if spec.repo == "uCore" else Path(os.environ.get("UCORE_UCODE_PATH", str(CODE_ROOT / spec.repo))).expanduser()
    repo_root = base / spec.project_dir
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
    if isinstance(readme, str):
        if not (repo_root / readme).is_file():
            errors.append(f"{spec.repo}: declared README is missing: {readme}")
    elif not isinstance(readme, dict) or not readme.get("text"):
        errors.append(f"{spec.repo}: project.readme missing or invalid")
    if spec.repo == "uCore":
        for authority in ("flow", "knowledge", "identity"):
            if not (package_path / authority / "__init__.py").is_file():
                errors.append(f"uCore: bundled authority missing: app.{authority}")

    requires_python = project.get("requires-python")
    if not isinstance(requires_python, str):
        errors.append(f"{spec.repo}: project.requires-python missing or invalid")

    return errors


def main() -> int:
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
