"""Knowledge bridge — filesystem vault search (no external apps).

Reads the uDos vault topology:

  ~/Vault   — master user vault (one only)
  ~/Shared  — shared vaults
  ~/Public  — public vaults (incl. ~/Public/global-knowledge)

Search is backed by the unified library index (FTS5) at
``~/.ucore/indices/library.db``, with a direct filesystem fallback
when the index has not been built yet.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from app.services import library_index

log = logging.getLogger("ucore.knowledge.vault")

VAULT_LAYERS: tuple[dict[str, Any], ...] = (
    {"id": "user", "name": "Vault", "path": Path.home() / "Vault"},
    {"id": "shared", "name": "Shared", "path": Path.home() / "Shared"},
    {"id": "public", "name": "Public", "path": Path.home() / "Public"},
)

_FTS_SPECIAL = re.compile(r'["()*:^\-~]')


def _safe_fts(query: str) -> str:
    """Sanitize a query for SQLite FTS5 MATCH syntax."""
    cleaned = _FTS_SPECIAL.sub(" ", query)
    tokens = [t for t in cleaned.split() if t]
    return " ".join(tokens) or "*"


def _layer_path(workspace_id: str | None) -> Path | None:
    if not workspace_id:
        return None
    for layer in VAULT_LAYERS:
        if layer["id"] == workspace_id:
            return layer["path"]
    return library_index.workspace_root(workspace_id)


def list_workspaces() -> list[dict[str, Any]]:
    """List the vault layers plus any user-registered workspaces."""
    workspaces: list[dict[str, Any]] = []
    for layer in VAULT_LAYERS:
        exists = layer["path"].exists() and layer["path"].is_dir()
        workspaces.append({
            "id": layer["id"],
            "name": layer["name"],
            "icon": None,
            "member_count": 0,
            "source": layer["id"],
            "path": str(layer["path"]),
            "exists": exists,
        })
    for ws in library_index.list_workspaces():
        workspaces.append({
            "id": ws.get("source") or ws.get("name"),
            "name": ws.get("name", "Workspace"),
            "icon": None,
            "member_count": 0,
            "source": ws.get("source") or ws.get("name"),
            "path": ws.get("path"),
            "exists": bool(ws.get("exists")),
        })
    return workspaces


def list_documents(
    workspace_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List markdown documents in a vault layer (or across all layers)."""
    rows = _index_search("", workspace_id, max(1, limit))
    if not rows:
        rows = _fallback_list(workspace_id, max(1, limit))
    docs: list[dict[str, Any]] = []
    for r in rows:
        docs.append({
            "id": r.get("id"),
            "title": r.get("filename") or Path(r.get("path", "")).name,
            "type": "markdown",
            "updated_at": r.get("modified_at"),
            "workspace_id": r.get("source"),
            "source": r.get("source"),
            "rel_path": r.get("path"),
            "path": r.get("path"),
        })
    return docs


def semantic_search(
    query: str,
    workspace_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search the vault library index (FTS5), with a filesystem fallback."""
    if not query or not query.strip():
        return []
    rows = _index_search(query, workspace_id, max(1, limit))
    if not rows:
        rows = _fallback_search(query, workspace_id, max(1, limit))
    results: list[dict[str, Any]] = []
    for r in rows:
        results.append({
            "id": r.get("id"),
            "title": r.get("filename") or Path(r.get("path", "")).name,
            "path": r.get("path"),
            "content": r.get("preview") or "",
            "source": r.get("source"),
            "score": r.get("score"),
        })
    return results[:limit]


def _index_search(
    query: str,
    source: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    try:
        fts = _safe_fts(query) if query.strip() else ""
        return library_index.search(fts, source=source, limit=limit)
    except Exception as exc:
        log.warning("Library index search failed: %s", exc)
        return []


def _fallback_list(
    workspace_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    roots = (
        [_layer_path(workspace_id)]
        if workspace_id
        else [layer["path"] for layer in VAULT_LAYERS]
    )
    out: list[dict[str, Any]] = []
    for root in roots:
        if not root or not root.exists():
            continue
        for md in root.rglob("*.md"):
            if len(out) >= limit:
                break
            rel = str(md.relative_to(root))
            out.append({
                "id": f"{root.name}:{rel}",
                "filename": md.name,
                "path": str(md),
                "source": root.name,
                "modified_at": None,
                "preview": "",
            })
    return out


def _fallback_search(
    query: str,
    workspace_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    q = query.strip().lower()
    roots = (
        [_layer_path(workspace_id)]
        if workspace_id
        else [layer["path"] for layer in VAULT_LAYERS]
    )
    out: list[dict[str, Any]] = []
    for root in roots:
        if not root or not root.exists():
            continue
        for md in root.rglob("*.md"):
            if len(out) >= limit:
                break
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if q not in text.lower() and q not in md.name.lower():
                continue
            rel = str(md.relative_to(root))
            out.append({
                "id": f"{root.name}:{rel}",
                "filename": md.name,
                "path": str(md),
                "source": root.name,
                "modified_at": None,
                "preview": text[:500],
            })
    return out


def get_document(
    object_id: str,
    workspace_id: str | None = None,
) -> dict[str, Any] | None:
    path = _resolve_path(object_id, workspace_id)
    if not path or not path.is_file():
        return None
    stat = path.stat()
    return {
        "id": object_id,
        "title": path.name,
        "type": "markdown",
        "description": None,
        "updated_at": stat.st_mtime,
        "path": str(path),
        "data_size": stat.st_size,
    }


def get_document_content(
    object_id: str,
    workspace_id: str | None = None,
) -> str | None:
    path = _resolve_path(object_id, workspace_id)
    if not path or not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:10000]
    except Exception:
        return None


def _resolve_path(object_id: str, workspace_id: str | None) -> Path | None:
    if not object_id:
        return None
    direct = Path(object_id).expanduser()
    if direct.is_file():
        return direct
    root = _layer_path(workspace_id)
    if root:
        candidate = root / object_id
        if candidate.is_file():
            return candidate
    return None
