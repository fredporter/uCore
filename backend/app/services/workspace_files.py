"""Bounded file operations for the editor workspace tree."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.services.library_index import EXCLUDE_DIRS, SUPPORTED_EXTENSIONS, workspace_root


def _root(source: str) -> Path:
    root = workspace_root(source)
    if root is None or not root.exists() or not root.is_dir():
        raise ValueError(f"Unknown or unavailable workspace: {source}")
    return root.resolve()


def _target(source: str, relative_path: str, *, allow_root: bool = False) -> Path:
    root = _root(source)
    raw = str(relative_path or "").strip().lstrip("/")
    if not raw and allow_root:
        return root
    if not raw:
        raise ValueError("path is required")
    target = (root / raw).resolve()
    if target == root and allow_root:
        return target
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
    return {"path": f"/{target.relative_to(root).as_posix()}", "content": target.read_text(encoding="utf-8")}


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


def write_file(source: str, path: str, content: str) -> dict[str, Any]:
    target = _target(source, path)
    if not target.is_file() or target.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("file is unavailable or unsupported")
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "path": f"/{target.relative_to(_root(source)).as_posix()}"}


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


def delete_entry(source: str, path: str) -> dict[str, Any]:
    target = _target(source, path)
    if not target.exists():
        raise ValueError("entry does not exist")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"ok": True, "path": path}
