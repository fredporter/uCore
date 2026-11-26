"""Layer 0 canon is read-only for runtime code.

Generated assets belong under ``UDOS_HOME``. Any runtime write into the canon
tree raises :class:`CanonWriteDenied` so a stray save cannot alter published
knowledge.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.core.settings import settings


class CanonWriteDenied(PermissionError):
    """Raised when runtime code tries to write into Layer 0 canon."""


def canon_roots() -> list[Path]:
    """Canon locations, overridable for tests and non-default installs."""
    roots = [
        Path(os.environ.get("UDOS_CANON_ROOT", "~/Public/global-knowledge")).expanduser(),
    ]
    public_root = getattr(settings, "public_vault_root", None)
    if public_root:
        candidate = Path(public_root).expanduser() / "global-knowledge"
        if candidate not in roots:
            roots.append(candidate)
    return [root.resolve() for root in roots]


def is_canon_path(path: str | Path) -> bool:
    candidate = Path(path).expanduser().resolve()
    return any(candidate == root or root in candidate.parents for root in canon_roots())


def assert_writable(path: str | Path) -> Path:
    """Return the path unchanged, or refuse when it points into canon."""
    candidate = Path(path).expanduser().resolve()
    if is_canon_path(candidate):
        raise CanonWriteDenied(f"Layer 0 canon is read-only: {candidate}")
    return candidate


def generated_elements_dir() -> Path:
    """Runtime-owned home for generated element assets."""
    directory = settings.udos_home / "assets" / "elements"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def element_asset_dirs() -> list[Path]:
    """Generated assets first, then read-only canon for bundled material."""
    return [generated_elements_dir(), *(root / "elements" for root in canon_roots())]


def find_element_asset(name: str) -> Path | None:
    """Resolve a bare asset name; callers remain responsible for name checks."""
    for directory in element_asset_dirs():
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None
