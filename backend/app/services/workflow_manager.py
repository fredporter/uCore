"""Workflow manager with SQLite persistence for definitions, logs, and runs."""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.settings import settings
from app.utils.sqlite_helpers import get_sqlite_connection


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    schedule: str
    created_at: str
    steps: list[dict[str, Any]]


@dataclass
class WorkflowRun:
    run_id: str
    workflow_id: str
    workflow_name: str
    started_at: str
    finished_at: str
    status: str
    steps: list[dict[str, Any]]


class WorkflowManager:
    """Persistent workflow storage with SQLite backend."""

    def __init__(self):
        self._db_path = settings.data_dir / "workflows.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return get_sqlite_connection(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    schedule TEXT DEFAULT 'manual',
                    created_at TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    owner TEXT NOT NULL DEFAULT 'default'
                )
                """,
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT DEFAULT 'info',
                    event TEXT NOT NULL,
                    message TEXT DEFAULT '',
                    run_id TEXT,
                    step_index INTEGER,
                    skill_id TEXT,
                    FOREIGN KEY (workflow_id)
                        REFERENCES workflows(id)
                )
                """,
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    owner TEXT NOT NULL DEFAULT 'default',
                    FOREIGN KEY (workflow_id)
                        REFERENCES workflows(id)
                )
                """,
            )
            for table in ("workflows", "workflow_runs"):
                columns = {
                    row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
                }
                if "owner" not in columns:
                    conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN owner TEXT NOT NULL DEFAULT 'default'"
                    )
            conn.execute("""CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY, profile TEXT NOT NULL, title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active', binder TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )""")
            conn.commit()

    def list_missions(self, profile: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM missions WHERE profile = ? ORDER BY created_at DESC, id", (profile,)).fetchall()
        return [dict(row) for row in rows]

    def create_mission(self, profile: str, title: str, binder: str = "") -> dict[str, Any]:
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 500:
            raise ValueError("Describe the objective in 1–500 characters")
        ident, now = str(uuid.uuid4()), datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute("INSERT INTO missions VALUES (?, ?, ?, 'active', ?, ?, ?)", (ident, profile, title.strip(), binder, now, now))
        return next(item for item in self.list_missions(profile) if item['id'] == ident)

    def update_mission(self, profile: str, ident: str, patch: dict[str, Any]) -> dict[str, Any]:
        current = next((item for item in self.list_missions(profile) if item['id'] == ident), None)
        if current is None:
            raise KeyError("Mission not found")
        title = patch.get('title', current['title'])
        status = patch.get('status', current['status'])
        binder = patch.get('binder', current['binder'])
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 500:
            raise ValueError("Describe the objective in 1–500 characters")
        if status not in ('active', 'paused', 'completed', 'archived') or not isinstance(binder, str):
            raise ValueError("Invalid mission state")
        with self._connect() as conn:
            conn.execute("UPDATE missions SET title=?, status=?, binder=?, updated_at=? WHERE id=? AND profile=?", (title.strip(), status, binder, datetime.now(UTC).isoformat(), ident, profile))
        return next(item for item in self.list_missions(profile) if item['id'] == ident)

    def create_workflow(
        self,
        workflow_id: str,
        name: str,
        steps: list[dict[str, Any]],
        description: str = "",
        schedule: str = "manual",
        owner: str = "default",
    ) -> dict[str, Any]:
        """Create a workflow definition owned by one server-resolved profile."""
        created_at = datetime.now(UTC).isoformat()
        steps_json = json.dumps(steps)

        with self._connect() as conn:
            # If the workflow already exists, return it instead of attempting
            # a duplicate insert (keeps tests idempotent if DB pre-populated).
            existing = conn.execute("SELECT id FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
            if existing:
                # Return existing workflow payload
                row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
                steps_exist = json.loads(row["steps"] or "[]")
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "schedule": row["schedule"],
                    "created_at": row["created_at"],
                    "steps": steps_exist,
                    "step_count": len(steps_exist),
                    "owner": row["owner"],
                }

            conn.execute(
                """
                INSERT INTO workflows
                (id, name, description, schedule, created_at, steps, owner)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    name,
                    description,
                    schedule,
                    created_at,
                    steps_json,
                    owner,
                ),
            )
            conn.commit()

        return {
            "id": workflow_id,
            "name": name,
            "description": description,
            "schedule": schedule,
            "created_at": created_at,
            "steps": steps,
            "step_count": len(steps),
            "owner": owner,
        }

    def get_workflow(self, workflow_id: str, owner: str | None = None) -> dict[str, Any] | None:
        """Fetch a definition, optionally confined to its owning profile."""
        query = "SELECT * FROM workflows WHERE id = ?"
        params: tuple[Any, ...] = (workflow_id,)
        if owner is not None:
            query += " AND owner = ?"
            params = (workflow_id, owner)
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()

        if not row:
            return None

        steps = json.loads(row["steps"] or "[]")
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "schedule": row["schedule"],
            "created_at": row["created_at"],
            "steps": steps,
            "step_count": len(steps),
            "owner": row["owner"],
        }

    def list_workflows(self, owner: str | None = None) -> list[dict[str, Any]]:
        """List definitions for one profile, or all for internal maintenance."""
        query = """
                SELECT id, name, description, schedule, created_at, steps, owner
                FROM workflows
        """
        params: tuple[Any, ...] = ()
        if owner is not None:
            query += " WHERE owner = ?"
            params = (owner,)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        workflows = []
        for row in rows:
            steps = json.loads(row["steps"] or "[]")
            workflows.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "schedule": row["schedule"],
                    "created_at": row["created_at"],
                    "steps": steps,
                    "step_count": len(steps),
                    "owner": row["owner"],
                },
            )
        return workflows

    def record_log(
        self,
        workflow_id: str,
        event: str,
        message: str = "",
        level: str = "info",
        run_id: str = "",
        step_index: int = 0,
        skill_id: str = "",
    ) -> None:
        """Record a workflow log entry."""
        timestamp = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_logs
                (workflow_id, timestamp, level, event, message,
                 run_id, step_index, skill_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    timestamp,
                    level,
                    event,
                    message,
                    run_id or "",
                    step_index or 0,
                    skill_id or "",
                ),
            )
            conn.commit()

    def get_logs(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch recent logs for a workflow."""
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, level, event, message, run_id,
                       step_index, skill_id
                FROM workflow_logs
                WHERE workflow_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (workflow_id, safe_limit),
            ).fetchall()

        logs = []
        for row in rows:
            log_entry = {
                "timestamp": row["timestamp"],
                "level": row["level"],
                "event": row["event"],
                "message": row["message"],
            }
            if row["run_id"]:
                log_entry["run_id"] = row["run_id"]
            if row["step_index"]:
                log_entry["step_index"] = row["step_index"]
            if row["skill_id"]:
                log_entry["skill_id"] = row["skill_id"]
            logs.append(log_entry)

        # Reverse to ascending order (oldest first)
        logs.reverse()
        return logs

    def start_run(
        self,
        *,
        run_id: str,
        workflow_id: str,
        workflow_name: str,
        started_at: str,
        owner: str = "default",
    ) -> dict[str, Any]:
        """Persist admission before the first step so an interruption leaves a record."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO workflow_runs
                (run_id, workflow_id, workflow_name, started_at,
                 finished_at, status, steps, owner)
                VALUES (?, ?, ?, ?, '', 'running', '[]', ?)
                """,
                (run_id, workflow_id, workflow_name, started_at, owner),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        return {
            "run_id": row["run_id"],
            "workflow_id": row["workflow_id"],
            "workflow_name": row["workflow_name"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "status": row["status"],
            "steps": json.loads(row["steps"] or "[]"),
        }

    def recover_interrupted_runs(self, now: str | None = None) -> int:
        """Mark runs left in 'running' by a previous process as interrupted."""
        stamp = now or datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE workflow_runs
                SET status = 'interrupted', finished_at = ?
                WHERE status = 'running'
                """,
                (stamp,),
            )
            conn.commit()
            return cursor.rowcount

    def save_run(
        self,
        run_id: str,
        workflow_id: str,
        workflow_name: str,
        started_at: str,
        finished_at: str,
        status: str,
        steps: list[dict[str, Any]],
        owner: str = "default",
    ) -> dict[str, Any]:
        """Save a completed workflow run."""
        steps_json = json.dumps(steps)

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT owner, status FROM workflow_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            # A completed row is idempotent; an admitted 'running' row is updated.
            if existing and not (
                existing["status"] == "running" and existing["owner"] == owner
            ):
                row = conn.execute(
                    "SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,)
                ).fetchone()
                return {
                    "run_id": row["run_id"],
                    "workflow_id": row["workflow_id"],
                    "workflow_name": row["workflow_name"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "status": row["status"],
                    "steps": json.loads(row["steps"] or "[]"),
                }

            if existing:
                conn.execute(
                    """
                    UPDATE workflow_runs
                    SET finished_at = ?, status = ?, steps = ?, workflow_name = ?
                    WHERE run_id = ? AND owner = ?
                    """,
                    (
                        finished_at,
                        status,
                        steps_json,
                        workflow_name,
                        run_id,
                        owner,
                    ),
                )
                conn.commit()
            else:
                conn.execute(
                """
                INSERT INTO workflow_runs
                (run_id, workflow_id, workflow_name, started_at,
                 finished_at, status, steps, owner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    workflow_id,
                    workflow_name,
                    started_at,
                    finished_at,
                    status,
                    steps_json,
                    owner,
                ),
            )
            conn.commit()

        return {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "steps": steps,
        }

    def get_run_history(
        self,
        workflow_id: str,
        limit: int = 100,
        owner: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch recent run history within the requested ownership boundary."""
        safe_limit = max(1, min(limit, 500))
        query = """
                SELECT run_id, workflow_id, workflow_name, started_at,
                       finished_at, status, steps
                FROM workflow_runs
                WHERE workflow_id = ?
        """
        params: list[Any] = [workflow_id]
        if owner is not None:
            query += " AND owner = ?"
            params.append(owner)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(safe_limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        runs = []
        for row in rows:
            steps = json.loads(row["steps"] or "[]")
            runs.append(
                {
                    "run_id": row["run_id"],
                    "workflow_id": row["workflow_id"],
                    "workflow_name": row["workflow_name"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "status": row["status"],
                    "steps": steps,
                },
            )
        return runs

    def get_all_runs(
        self,
        limit: int = 100,
        owner: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch recent runs for one profile, or all for internal maintenance."""
        safe_limit = max(1, min(limit, 500))
        query = """
                SELECT run_id, workflow_id, workflow_name, started_at,
                       finished_at, status, steps
                FROM workflow_runs
        """
        params: list[Any] = []
        if owner is not None:
            query += " WHERE owner = ?"
            params.append(owner)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(safe_limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        runs = []
        for row in rows:
            steps = json.loads(row["steps"] or "[]")
            runs.append(
                {
                    "run_id": row["run_id"],
                    "workflow_id": row["workflow_id"],
                    "workflow_name": row["workflow_name"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "status": row["status"],
                    "steps": steps,
                },
            )
        return runs
