"""Docs mirror — pull uDos component docs from in-repo docs/ directories.

Dev Lane only. The mirror reads from in-repo `docs/` directories in core and
extension repos. It must NEVER scan user-lane vault paths
(`~/Vault`, `~/Shared`, `~/Public`) — those belong to the User Lane and are
handled separately.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.logging import log

MIRROR_ROOT = Path.home() / ".ucore" / "docs-mirror"
MIRROR_INDEX = MIRROR_ROOT / "_mirror.json"

# Dev-lane component doc roots — in-repo docs/ only.
CORE_DOC_ROOTS: dict[str, Path] = {
    "uCore": Path.home() / "Code" / "uCore" / "docs",
    "uFlow": Path.home() / "Code" / "uFlow" / "docs",
    "uKnowledge": Path.home() / "Code" / "uKnowledge" / "docs",
    "uCode": Path.home() / "Code" / "uCode" / "docs",
    "uVector": Path.home() / "Code" / "uVector" / "docs",
}

# User-lane paths that must NEVER be mirrored.
FORBIDDEN_ROOTS: tuple[Path, ...] = (
    Path.home() / "Vault",
    Path.home() / "Shared",
    Path.home() / "Public",
)

# Excluded path segments (same policy as the repo-docs scanner).
EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "archive",
    "archived",
    "_site",
    "_compost",
}


def _git_sha(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""
    except Exception:
        return ""


def discover_extension_doc_roots(code_root: Path | None = None) -> dict[str, Path]:
    """Discover `udos-*` extension repos under ~/Code with a docs/ directory."""
    code = code_root or (Path.home() / "Code")
    roots: dict[str, Path] = {}
    if not code.is_dir():
        return roots
    for child in sorted(code.iterdir()):
        if not child.is_dir() or not child.name.startswith("udos-"):
            continue
        docs_dir = child / "docs"
        if docs_dir.is_dir():
            roots[child.name] = docs_dir
    return roots


def _ensure_allowed(path: Path) -> None:
    """Reject any path under a user-lane (forbidden) root."""
    resolved = path.resolve()
    for forbidden in FORBIDDEN_ROOTS:
        try:
            resolved.relative_to(forbidden.resolve())
        except ValueError:
            continue
        raise ValueError(f"Refusing to mirror user-lane path: {path}")


def sync_from_repos(
    roots: dict[str, Path] | None = None,
    mirror_root: Path | None = None,
) -> dict[str, Any]:
    """Pull markdown docs from dev-lane repos into the mirror.

    Copies `.md` files into `<mirror>/<repo>/...` and writes a
    `_mirror.json` index with provenance per file.
    """
    root = mirror_root or MIRROR_ROOT
    all_roots = dict(roots) if roots is not None else {
        **CORE_DOC_ROOTS,
        **discover_extension_doc_roots(),
    }

    root.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    source_stats: list[dict[str, Any]] = []
    total = 0

    for repo_name, docs_root in sorted(all_roots.items()):
        if not docs_root.is_dir():
            source_stats.append({
                "repo": repo_name,
                "path": str(docs_root),
                "status": "missing",
                "files": 0,
            })
            continue

        _ensure_allowed(docs_root)
        sha = _git_sha(docs_root.parent)

        files = 0
        for md_file in sorted(
            docs_root.rglob("*.md"),
            key=lambda p: str(p).lower(),
        ):
            if md_file.name.startswith("."):
                continue
            if EXCLUDED_PARTS.intersection(md_file.parts):
                continue
            _ensure_allowed(md_file)

            rel = md_file.relative_to(docs_root)
            dest = root / repo_name / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, dest)

            entries.append({
                "source_repo": repo_name,
                "source_path": str(rel),
                "mirrored_path": str(dest.relative_to(root)),
                "git_sha": sha,
                "size": md_file.stat().st_size,
            })
            files += 1
            total += 1

        source_stats.append({
            "repo": repo_name,
            "path": str(docs_root),
            "status": "ok",
            "files": files,
            "git_sha": sha,
        })

    synced_at = datetime.now(UTC).isoformat()
    index = {
        "synced_at": synced_at,
        "total_files": total,
        "sources": source_stats,
        "entries": entries,
    }
    (root / "_mirror.json").write_text(
        json.dumps(index, indent=2, default=str),
        encoding="utf-8",
    )

    log.info(
        "Docs mirror synced: %d files across %d repos",
        total,
        len(source_stats),
    )

    return {
        "status": "completed",
        "mirror_root": str(root),
        "total_files": total,
        "sources": source_stats,
        "synced_at": synced_at,
    }


def mirror_status(mirror_root: Path | None = None) -> dict[str, Any]:
    """Return the current mirror index status."""
    root = mirror_root or MIRROR_ROOT
    index_file = root / "_mirror.json"
    if not index_file.exists():
        return {
            "status": "empty",
            "mirror_root": str(root),
            "total_files": 0,
            "sources": [],
        }
    try:
        index = json.loads(index_file.read_text(encoding="utf-8"))
    except Exception:
        return {
            "status": "error",
            "mirror_root": str(root),
            "total_files": 0,
            "sources": [],
        }
    return {
        "status": "ok",
        "mirror_root": str(root),
        "synced_at": index.get("synced_at"),
        "total_files": index.get("total_files", 0),
        "sources": index.get("sources", []),
    }
