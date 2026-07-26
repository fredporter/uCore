"""vault_file_discovery — File discovery engine for uihub Filepicker.

Discovers and indexes files from all vault types (User, Shared, Public)
for the unified filepicker sidebar.

Note: ~/Code/ is NOT a vault — it is the Developer Lane codebase.

Spec: docs/UIHUB_FILEPICKER_SPEC.md
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


# Types --------------------------------------------------------------
@dataclass
class FileEntry:
    path: str
    filename: str
    source: str
    vault_layer: str
    binder: str | None = None
    mission: str | None = None
    tags: list[str] = field(default_factory=list)
    type: str = "file"
    extension: str = ""
    size: int = 0
    modified_at: str = ""
    created_at: str = ""
    is_readonly: bool = False
    is_shared: bool = False
    is_published: bool = False
    frontmatter: dict[str, Any] = field(default_factory=dict)
    preview: str = ""


# Vault Paths — 3 vault types only (see backend/app/api/vault_api.py)
VAULT_PATHS = {
    "user": Path("~/Vault/").expanduser(),
    "shared": Path("~/Shared/").expanduser(),
    "public": Path("~/Public/").expanduser(),
}

SUPPORTED_EXTENSIONS = {
    ".md", ".yaml", ".yml", ".json", ".txt", ".csv",
}
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".next",
    ".obsidian", ".vscode",
}


# Frontmatter Parser -------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from file content."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}

    try:
        import yaml
        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {}


def get_preview(content: str, max_chars: int = 200) -> str:
    """Get preview text from file content."""
    clean = FRONTMATTER_RE.sub("", content)
    lines = clean.split("\n")
    preview_lines = []
    for line in lines:
        if line.strip():
            preview_lines.append(line.strip())
        if len("\n".join(preview_lines)) > max_chars:
            break
    return "\n".join(preview_lines)[:max_chars]


# File Discovery -----------------------------------------------------

def discover_files(
    source: str = "all",
    vault_paths: dict[str, Path] | None = None,
) -> list[FileEntry]:
    """Discover all files from specified source or all sources."""
    vault_paths = vault_paths or VAULT_PATHS
    entries = []

    if source == "all":
        for src, path in vault_paths.items():
            entries.extend(_scan_directory(path, src))
    else:
        path = vault_paths.get(source)
        if path and path.exists():
            entries.extend(_scan_directory(path, source))

    return entries


def _scan_directory(path: Path, source: str) -> list[FileEntry]:
    """Recursively scan directory for supported files."""
    entries = []

    if not path.exists():
        return entries

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            file_path = Path(root) / file

            ext = file_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            entry = _create_entry(file_path, source)
            entries.append(entry)

    return entries


def _create_entry(file_path: Path, source: str) -> FileEntry:
    """Create FileEntry from file path."""
    try:
        stat = file_path.stat()
        content = file_path.read_text(
            encoding="utf-8", errors="replace",
        )
    except Exception:
        return FileEntry(
            path=str(file_path),
            filename=file_path.name,
            source=source,
            vault_layer=source.title(),
            extension=file_path.suffix[1:],
        )

    # Parse metadata
    frontmatter = parse_frontmatter(content)
    tags = frontmatter.get("tags", [])
    binder = frontmatter.get("binder")
    mission = frontmatter.get("mission")

    # Determine source layer label (3 types only)
    source_layer_map = {
        "user": "User",
        "shared": "Shared",
        "public": "Public",
    }
    source_layer = source_layer_map.get(source, "Unknown")

    return FileEntry(
        path=str(file_path),
        filename=file_path.name,
        source=source,
        vault_layer=source_layer,
        binder=str(binder) if binder else None,
        mission=str(mission) if mission else None,
        tags=[str(t) for t in tags] if isinstance(tags, list) else [],
        extension=file_path.suffix[1:],
        size=stat.st_size,
        modified_at=datetime.fromtimestamp(
            stat.st_mtime, tz=UTC,
        ).isoformat(),
        created_at=datetime.fromtimestamp(
            stat.st_ctime, tz=UTC,
        ).isoformat(),
        is_readonly=source == "public",
        is_shared=source == "shared",
        is_published=source == "public",
        frontmatter=frontmatter,
        preview=get_preview(content),
    )


# Filter Functions ---------------------------------------------------

def apply_filters(
    entries: list[FileEntry],
    workspace: str = "all",
    workspace_toggles: dict[str, bool] | None = None,
    binder: str | None = None,
    mission: str | None = None,
    tags: list[str] | None = None,
    search_query: str | None = None,
) -> list[FileEntry]:
    """Apply filters to file entries."""
    results = entries

    # Box 1: Workspace filter
    if workspace != "all":
        results = [e for e in results if e.source == workspace]
    elif workspace_toggles:
        enabled = [k for k, v in workspace_toggles.items() if v]
        results = [e for e in results if e.source in enabled]

    # Box 2: Binder/Mission filter
    if binder == "active":
        results = [
            e for e in results
            if e.binder and "active" in e.binder.lower()
        ]
    elif binder == "tasks":
        results = [
            e for e in results
            if e.mission or "task" in " ".join(e.tags).lower()
        ]
    elif binder == "inbox":
        results = [
            e for e in results
            if "@sandbox" in e.path or "inbox" in e.path.lower()
        ]
    elif binder == "archive":
        results = [e for e in results if "@legacy" in e.path]
    elif binder:
        results = [e for e in results if e.binder == binder]

    # Box 3: Search + Tags
    if search_query:
        query_lower = search_query.lower()
        results = [
            e for e in results
            if query_lower in e.filename.lower()
            or query_lower in e.preview.lower()
            or any(
                query_lower in tag.lower() for tag in e.tags
            )
        ]

    if tags:
        results = [
            e for e in results
            if any(tag in e.tags for tag in tags)
        ]

    return results


# Index Management ---------------------------------------------------

def build_index(
    output_path: Path | None = None,
    vault_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """Build file index for caching."""
    entries = discover_files("all", vault_paths)

    index = {
        "generated": datetime.now(UTC).isoformat(),
        "total_files": len(entries),
        "by_source": {},
        "entries": [
            {
                "path": e.path,
                "filename": e.filename,
                "source": e.source,
                "vault_layer": e.vault_layer,
                "binder": e.binder,
                "mission": e.mission,
                "tags": e.tags,
                "extension": e.extension,
                "size": e.size,
                "modified_at": e.modified_at,
            }
            for e in entries
        ],
    }

    # Count by source
    for entry in entries:
        key = entry.source
        index["by_source"][key] = index["by_source"].get(key, 0) + 1

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        output_path.write_text(
            json.dumps(index, indent=2), encoding="utf-8",
        )

    return index
