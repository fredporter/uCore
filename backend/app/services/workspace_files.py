"""Bounded file operations for the editor workspace tree."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from app.core.settings import settings

from app.services.library_index import EXCLUDE_DIRS, SUPPORTED_EXTENSIONS, workspace_root


class WorkspaceConflictError(ValueError):
    """Raised when a client saves against a stale file version."""


def _version(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _root(source: str, *, include_shared: bool = False) -> Path:
    root = settings.shared_vault_root if include_shared and source == "shared" else workspace_root(source)
    if root is None or not root.exists() or not root.is_dir():
        raise ValueError(f"Unknown or unavailable workspace: {source}")
    return root.resolve()


def _target(source: str, relative_path: str, *, allow_root: bool = False, root: Path | None = None) -> Path:
    root = root if root is not None else _root(source)
    raw = str(relative_path or "").strip().lstrip("/")
    if not raw and allow_root:
        return root
    if not raw:
        raise ValueError("path is required")
    supplied = Path(str(relative_path or "").strip()).expanduser()
    target = supplied.resolve() if supplied.is_absolute() and supplied.is_relative_to(root) else (root / raw).resolve()
    if target == root and not allow_root:
        raise ValueError("Choose an entry inside the workspace")
    if not target.is_relative_to(root):
        raise ValueError("path must remain inside the workspace")
    return target


def _node(path: Path, root: Path, *, depth: int, max_depth: int) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    item: dict[str, Any] = {
        "id": relative,
        "name": path.name,
        "type": "folder" if path.is_dir() else "file",
        "path": f"/{relative}",
    }
    if path.is_file():
        item["extension"] = path.suffix.lstrip(".").lower()
        item["version"] = _version(path)
    elif depth < max_depth:
        children = [
            child for child in path.iterdir()
            if not child.name.startswith(".") and child.name not in EXCLUDE_DIRS
            and (child.is_dir() or child.suffix.lower() in SUPPORTED_EXTENSIONS)
        ]
        item["children"] = [
            _node(child, root, depth=depth + 1, max_depth=max_depth)
            for child in sorted(children, key=lambda value: (value.is_file(), value.name.lower()))
        ]
    return item


def list_tree(source: str = "user", *, max_depth: int = 8) -> list[dict[str, Any]]:
    root = _root(source)
    children = [
        child for child in root.iterdir()
        if not child.name.startswith(".") and child.name not in EXCLUDE_DIRS
        and (child.is_dir() or child.suffix.lower() in SUPPORTED_EXTENSIONS)
    ]
    return [
        _node(child, root, depth=0, max_depth=max(1, min(max_depth, 12)))
        for child in sorted(children, key=lambda value: (value.is_file(), value.name.lower()))
    ]


def read_file(source: str, path: str) -> dict[str, Any]:
    target = _target(source, path)
    if not target.is_file() or target.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("file is unavailable or unsupported")
    root = _root(source)
    return {
        "path": f"/{target.relative_to(root).as_posix()}",
        "content": target.read_text(encoding="utf-8"),
        "version": _version(target),
    }


def create_entry(source: str, parent: str, name: str, kind: str) -> dict[str, Any]:
    if kind not in {"file", "folder"}:
        raise ValueError("type must be file or folder")
    clean_name = str(name or "").strip()
    if not clean_name or clean_name in {".", ".."} or any(char in clean_name for char in "/\\"):
        raise ValueError("invalid name")
    parent_path = _target(source, parent, allow_root=True)
    if not parent_path.is_dir():
        raise ValueError("parent must be a folder")
    target = parent_path / clean_name
    if target.exists():
        raise ValueError("an entry with that name already exists")
    if kind == "folder":
        target.mkdir()
    else:
        if target.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError("unsupported file extension")
        target.write_text("", encoding="utf-8")
    return _node(target, _root(source), depth=0, max_depth=1)


def write_file(
    source: str, path: str, content: str, expected_version: str | None = None,
) -> dict[str, Any]:
    target = _target(source, path)
    if not target.is_file() or target.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("file is unavailable or unsupported")
    current_version = _version(target)
    if expected_version and expected_version != current_version:
        raise WorkspaceConflictError("file changed since it was opened")
    target.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "path": f"/{target.relative_to(_root(source)).as_posix()}",
        "version": _version(target),
    }


def rename_entry(source: str, path: str, name: str) -> dict[str, Any]:
    target = _target(source, path)
    clean_name = str(name or "").strip()
    if not clean_name or clean_name in {".", ".."} or any(char in clean_name for char in "/\\"):
        raise ValueError("invalid name")
    destination = target.with_name(clean_name)
    if destination.exists():
        raise ValueError("an entry with that name already exists")
    target.rename(destination)
    return _node(destination, _root(source), depth=0, max_depth=1)


def move_entry(
    source: str, path: str, parent: str, destination_source: str | None = None,
) -> dict[str, Any]:
    destination_source = destination_source or source
    across_vaults = source != destination_source
    if across_vaults and {source, destination_source} != {"user", "shared"}:
        raise ValueError("Moves between vaults require User Vault and Shared Vaults")
    source_root = _root(source, include_shared=across_vaults)
    destination_root = _root(destination_source, include_shared=across_vaults)
    target = _target(source, path, root=source_root)
    destination_parent = _target(destination_source, parent, allow_root=True, root=destination_root)
    if across_vaults:
        source_parts = target.relative_to(source_root).parts
        destination_parts = destination_parent.relative_to(destination_root).parts
        if any(parts and parts[0].casefold() in {"binders", "trash"} for parts in (source_parts, destination_parts)):
            raise ValueError("Binder and Trash paths require their own workflow")
        if not target.is_file() and not target.is_dir():
            raise ValueError("Entry is unavailable")
        if target.is_dir() and any(entry.is_symlink() or entry.name == "binder.json" for entry in target.rglob("*")):
            raise ValueError("Folders containing symbolic links or managed Binders cannot be moved between vaults")
    if not destination_parent.is_dir():
        raise ValueError("destination must be a folder")
    destination = destination_parent / target.name
    if destination == target:
        return _node(target, _root(source), depth=0, max_depth=1)
    if destination.exists() or destination.is_symlink():
        raise ValueError("an entry with that name already exists")
    if target.is_dir() and destination_parent.is_relative_to(target):
        raise ValueError("a folder cannot be moved inside itself")
    target.rename(destination)
    return _node(destination, destination_root, depth=0, max_depth=0 if across_vaults else 1)


def delete_entry(source: str, path: str) -> dict[str, Any]:
    target = _target(source, path)
    if not target.exists():
        raise ValueError("entry does not exist")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"ok": True, "path": path}
