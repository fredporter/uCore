"""Safe local SQLite helpers for uDos (no external apps).

Discovers uDos-managed SQLite databases on disk and provides
read/write-guarded query helpers.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SPOOL_PATH = Path(
    os.getenv("UCORE_SNACKS_REPLIES", "~/.local/share/snackmachine/replies.jsonl"),
).expanduser()
BACKUP_DIR = Path(os.getenv("UCORE_DB_BACKUPS", "~/.ucore/backups/db")).expanduser()

UCORE_DIR = Path.home() / ".ucore"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def _spool_lock_file():
    lock_path = SPOOL_PATH.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as f:
        try:
            import fcntl  # POSIX only

            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            yield


def spool_event(event: dict[str, Any]) -> None:
    SPOOL_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": _utc_now(), **event}
    with _spool_lock_file(), SPOOL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=True) + "\n")


def discover_databases() -> dict[str, str]:
    """Discover uDos-managed local SQLite databases on disk.

    ``database`` is an alias for the unified library index so existing
    callers that pass ``db="database"`` keep working.
    """
    found: dict[str, str] = {}

    library_db = UCORE_DIR / "indices" / "library.db"
    if library_db.exists():
        found["library"] = str(library_db)
        found["database"] = str(library_db)

    budget_db = UCORE_DIR / "indices" / "budget.db"
    if budget_db.exists():
        found["budget"] = str(budget_db)

    knowledge_db = UCORE_DIR / "knowledge" / "shared.db"
    if knowledge_db.exists():
        found["knowledge"] = str(knowledge_db)

    return found


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(db_path: str) -> list[str]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        ).fetchall()
        return [r["name"] for r in rows]


def _is_safe_read_sql(sql: str) -> bool:
    s = sql.strip().lower()
    return s.startswith("select") or s.startswith("pragma") or s.startswith("with")


def _is_safe_write_sql(sql: str) -> bool:
    s = sql.strip().lower()
    return s.startswith("insert") or s.startswith("update") or s.startswith("delete")


def _backup_db(db_path: str) -> str:
    src = Path(db_path)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dst = BACKUP_DIR / f"{src.stem}-{stamp}{src.suffix}"
    shutil.copy2(src, dst)
    return str(dst)


def run_query(
    db_path: str,
    sql: str,
    params: list[Any] | None = None,
    write: bool = False,
) -> dict[str, Any]:
    params = params or []

    if write:
        if not _is_safe_write_sql(sql):
            raise ValueError("Only INSERT/UPDATE/DELETE statements are allowed in write mode")
    elif not _is_safe_read_sql(sql):
        raise ValueError("Only SELECT/PRAGMA/WITH statements are allowed in read mode")

    backup_file = None
    with _connect(db_path) as conn:
        if write:
            backup_file = _backup_db(db_path)
            cur = conn.execute(sql, params)
            conn.commit()
            rowcount = cur.rowcount
            result = {"write": True, "rowcount": rowcount, "backup": backup_file}
        else:
            cur = conn.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            result = {"write": False, "rows": rows, "count": len(rows)}

    spool_event(
        {
            "type": "sqlite_query",
            "status": "success",
            "db_path": db_path,
            "write": write,
            "sql": re.sub(r"\s+", " ", sql).strip()[:500],
            "params": params,
            "result_count": result.get("count", result.get("rowcount", 0)),
            "backup": backup_file,
        },
    )
    return result
