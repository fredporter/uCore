"""Gate B milestone 2 — Python timing adapter (fixture scope).

Occurrences have stable identities derived from schedule, revision and due time,
so replanning, restart and repeated ticks converge on one occurrence and one run.
Obsolete revisions and disabled schedules are never admitted.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.core.settings import settings
from app.utils.sqlite_helpers import get_sqlite_connection

SUPPORTED_KINDS = {"calendar", "delay"}
DEFAULT_GRACE_SECONDS = 300


class ScheduleError(ValueError):
    """Raised when a schedule definition is not usable."""


@dataclass(frozen=True)
class Schedule:
    schedule_id: str
    workflow_id: str
    owner: str
    kind: str = "calendar"
    revision: int = 1
    timezone: str = "UTC"
    local_time: str = "09:00"
    delay_seconds: int = 0
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.kind not in SUPPORTED_KINDS:
            raise ScheduleError(f"kind must be one of {sorted(SUPPORTED_KINDS)}")
        try:
            ZoneInfo(self.timezone)
        except Exception as exc:  # noqa: BLE001 - zoneinfo raises several types
            raise ScheduleError(f"unknown timezone: {self.timezone}") from exc
        if self.kind == "calendar":
            hour, _, minute = self.local_time.partition(":")
            if not (hour.isdigit() and minute.isdigit()):
                raise ScheduleError("local_time must be HH:MM")


def resolve_local(day: date, local_time: str, timezone: str) -> datetime | None:
    """Resolve a wall time; None when the time does not exist (spring forward)."""
    hour, _, minute = local_time.partition(":")
    naive = datetime.combine(day, time(int(hour), int(minute)))
    zone = ZoneInfo(timezone)
    candidate = naive.replace(tzinfo=zone)
    roundtrip = candidate.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
    if roundtrip != naive:
        return None
    return candidate


def occurrence_id_for(schedule_id: str, revision: int, due_at: datetime) -> str:
    key = f"{schedule_id}|{revision}|{due_at.astimezone(UTC).isoformat()}"
    return "occ-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class TimingStore:
    """Durable schedules and occurrences; no authority lives here."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or (settings.data_dir / "timing.db")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return get_sqlite_connection(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule (
                    schedule_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    timezone TEXT NOT NULL,
                    local_time TEXT NOT NULL,
                    delay_seconds INTEGER NOT NULL,
                    enabled INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS occurrence (
                    occurrence_id TEXT PRIMARY KEY,
                    schedule_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    run_id TEXT,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def upsert_schedule(self, schedule: Schedule, *, now: datetime | None = None) -> bool:
        """Store the schedule; a lower revision never overwrites a higher one."""
        stamp = (now or datetime.now(UTC)).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT revision FROM schedule WHERE schedule_id = ?",
                (schedule.schedule_id,),
            ).fetchone()
            if row is not None and schedule.revision < row["revision"]:
                return False
            conn.execute(
                """
                INSERT INTO schedule
                (schedule_id, workflow_id, owner, kind, revision, timezone,
                 local_time, delay_seconds, enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (schedule_id) DO UPDATE SET
                    workflow_id = excluded.workflow_id,
                    owner = excluded.owner,
                    kind = excluded.kind,
                    revision = excluded.revision,
                    timezone = excluded.timezone,
                    local_time = excluded.local_time,
                    delay_seconds = excluded.delay_seconds,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    schedule.schedule_id,
                    schedule.workflow_id,
                    schedule.owner,
                    schedule.kind,
                    schedule.revision,
                    schedule.timezone,
                    schedule.local_time,
                    schedule.delay_seconds,
                    1 if schedule.enabled else 0,
                    stamp,
                ),
            )
            conn.commit()
        return True

    def get_schedule(self, schedule_id: str) -> Schedule | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM schedule WHERE schedule_id = ?", (schedule_id,)
            ).fetchone()
        if row is None:
            return None
        return Schedule(
            schedule_id=row["schedule_id"],
            workflow_id=row["workflow_id"],
            owner=row["owner"],
            kind=row["kind"],
            revision=row["revision"],
            timezone=row["timezone"],
            local_time=row["local_time"],
            delay_seconds=row["delay_seconds"],
            enabled=bool(row["enabled"]),
        )

    def plan_calendar(self, schedule: Schedule, day: date) -> str | None:
        """Insert the occurrence for one local day; None when the time is invalid."""
        due = resolve_local(day, schedule.local_time, schedule.timezone)
        if due is None:
            return None
        return self._insert_occurrence(schedule, due)

    def plan_delay(self, schedule: Schedule, *, now: datetime | None = None) -> str:
        base = now or datetime.now(UTC)
        due = base.astimezone(UTC) + timedelta(seconds=schedule.delay_seconds)
        occurrence_id = self._insert_occurrence(schedule, due)
        assert occurrence_id is not None
        return occurrence_id

    def _insert_occurrence(self, schedule: Schedule, due: datetime) -> str | None:
        occurrence_id = occurrence_id_for(schedule.schedule_id, schedule.revision, due)
        stamp = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO occurrence
                (occurrence_id, schedule_id, revision, due_at, status, run_id,
                 reason, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', NULL, NULL, ?, ?)
                """,
                (
                    occurrence_id,
                    schedule.schedule_id,
                    schedule.revision,
                    due.astimezone(UTC).isoformat(),
                    stamp,
                    stamp,
                ),
            )
            conn.commit()
        return occurrence_id

    def claim_due(
        self,
        *,
        now: datetime,
        grace_seconds: int = DEFAULT_GRACE_SECONDS,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Claim due occurrences; expire missed windows and skip overlapping runs."""
        stamp = now.astimezone(UTC).isoformat()
        claimed: list[dict[str, Any]] = []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT o.occurrence_id, o.schedule_id, o.due_at
                FROM occurrence o
                JOIN schedule s ON s.schedule_id = o.schedule_id
                WHERE o.status = 'pending'
                  AND o.revision = s.revision
                  AND s.enabled = 1
                  AND o.due_at <= ?
                ORDER BY o.due_at ASC
                LIMIT ?
                """,
                (stamp, max(1, min(limit, 100))),
            ).fetchall()

            for row in rows:
                due = datetime.fromisoformat(row["due_at"])
                if due + timedelta(seconds=grace_seconds) < now:
                    conn.execute(
                        "UPDATE occurrence SET status='missed', reason=?, updated_at=? WHERE occurrence_id=?",
                        ("missed-window", stamp, row["occurrence_id"]),
                    )
                    continue
                overlap = conn.execute(
                    "SELECT 1 FROM occurrence WHERE schedule_id = ? AND status = 'claimed' LIMIT 1",
                    (row["schedule_id"],),
                ).fetchone()
                if overlap:
                    conn.execute(
                        "UPDATE occurrence SET status='skipped', reason=?, updated_at=? WHERE occurrence_id=?",
                        ("overlap", stamp, row["occurrence_id"]),
                    )
                    continue
                conn.execute(
                    "UPDATE occurrence SET status='claimed', updated_at=? WHERE occurrence_id=?",
                    (stamp, row["occurrence_id"]),
                )
                claimed.append(dict(row))
            conn.commit()
        return claimed

    def reconcile(self, *, now: datetime | None = None) -> int:
        """Return claimed occurrences to pending after a restart."""
        stamp = (now or datetime.now(UTC)).astimezone(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE occurrence SET status='pending', updated_at=? WHERE status='claimed'",
                (stamp,),
            )
            conn.commit()
            return cursor.rowcount

    def complete(self, occurrence_id: str, run_id: str, *, now: datetime | None = None) -> None:
        stamp = (now or datetime.now(UTC)).astimezone(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE occurrence SET status='completed', run_id=?, reason=NULL, updated_at=? WHERE occurrence_id=?",
                (run_id, stamp, occurrence_id),
            )
            conn.commit()

    def skip(self, occurrence_id: str, reason: str, *, now: datetime | None = None) -> None:
        stamp = (now or datetime.now(UTC)).astimezone(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE occurrence SET status='skipped', reason=?, updated_at=? WHERE occurrence_id=?",
                (reason, stamp, occurrence_id),
            )
            conn.commit()

    def get_occurrence(self, occurrence_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM occurrence WHERE occurrence_id = ?", (occurrence_id,)
            ).fetchone()
        return dict(row) if row else None

    def remove_schedule(self, schedule_id: str, *, now: datetime | None = None) -> int:
        """Forget a schedule and skip its unfinished occurrences.

        Returns the number of occurrences skipped. History is kept: completed,
        skipped and missed rows stay for receipts until retention prunes them.
        """
        stamp = (now or datetime.now(UTC)).astimezone(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE occurrence
                SET status='skipped', reason='schedule-deleted', updated_at=?
                WHERE schedule_id = ? AND status IN ('pending', 'claimed')
                """,
                (stamp, schedule_id),
            )
            conn.execute("DELETE FROM schedule WHERE schedule_id = ?", (schedule_id,))
            conn.commit()
            return cursor.rowcount

    def list_schedules(self) -> list[dict[str, Any]]:
        """Reviewed schedules as planned, oldest id first. Read-only."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM schedule ORDER BY schedule_id").fetchall()
        return [dict(row) for row in rows]

    def list_occurrences(
        self, schedule_id: str | None = None, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Most recent occurrences, newest due first. Read-only, bounded by limit."""
        bounded = max(1, min(int(limit), 50))
        with self._connect() as conn:
            if schedule_id:
                rows = conn.execute(
                    "SELECT * FROM occurrence WHERE schedule_id = ? "
                    "ORDER BY due_at DESC LIMIT ?",
                    (schedule_id, bounded),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM occurrence ORDER BY due_at DESC LIMIT ?", (bounded,)
                ).fetchall()
        return [dict(row) for row in rows]

    def prune_occurrences(self, *, days: int = 30, now: datetime | None = None) -> int:
        """Delete expired finished occurrences; pending and claimed survive."""
        cutoff = ((now or datetime.now(UTC)) - timedelta(days=days)).astimezone(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM occurrence
                WHERE status IN ('completed', 'skipped', 'missed') AND due_at < ?
                """,
                (cutoff,),
            )
            conn.commit()
            return cursor.rowcount



async def admit_due(
    store: TimingStore,
    manager,
    *,
    now: datetime | None = None,
    grace_seconds: int = DEFAULT_GRACE_SECONDS,
) -> list[dict[str, Any]]:
    """Claim due occurrences and admit each as one deterministic Gate A run."""
    from app.flow.workflow_api import start_workflow_run

    moment = (now or datetime.now(UTC)).astimezone(UTC)
    results: list[dict[str, Any]] = []
    for occurrence in store.claim_due(now=moment, grace_seconds=grace_seconds):
        occurrence_id = occurrence["occurrence_id"]
        schedule = store.get_schedule(occurrence["schedule_id"])
        if schedule is None:
            store.skip(occurrence_id, "schedule-missing")
            results.append({"occurrence_id": occurrence_id, "status": "skipped", "reason": "schedule-missing"})
            continue

        workflow = manager.get_workflow(schedule.workflow_id, owner=schedule.owner)
        if workflow is None:
            store.skip(occurrence_id, "workflow-not-found")
            results.append({"occurrence_id": occurrence_id, "status": "skipped", "reason": "workflow-not-found"})
            continue

        run_id = "run-" + hashlib.sha256(occurrence_id.encode("utf-8")).hexdigest()[:10]
        try:
            await start_workflow_run(
                manager,
                workflow,
                schedule.workflow_id,
                schedule.owner,
                run_id=run_id,
            )
        except Exception as exc:  # noqa: BLE001 - recorded on the occurrence
            store.skip(occurrence_id, f"admission-error:{exc}")
            results.append({"occurrence_id": occurrence_id, "status": "skipped", "reason": str(exc)})
            continue

        store.complete(occurrence_id, run_id)
        results.append({"occurrence_id": occurrence_id, "status": "admitted", "run_id": run_id})
    return results


def schedules_path() -> Path:
    return settings.udos_home / "config" / "schedules.json"


def schedule_to_payload(schedule: Schedule) -> dict[str, Any]:
    """Round-trip form of one reviewed schedule."""
    return {
        "schedule_id": schedule.schedule_id,
        "workflow_id": schedule.workflow_id,
        "owner": schedule.owner,
        "kind": schedule.kind,
        "revision": schedule.revision,
        "timezone": schedule.timezone,
        "local_time": schedule.local_time,
        "delay_seconds": schedule.delay_seconds,
        "enabled": schedule.enabled,
    }


def write_schedules(schedules: list[Schedule], path: Path | None = None) -> None:
    """Replace the reviewed schedule file atomically; validation is the caller's."""
    target = path or schedules_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schedules": [schedule_to_payload(item) for item in schedules]}
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    temporary.replace(target)


def load_schedules(path: Path | None = None) -> list[Schedule]:
    """Load reviewed schedules; a missing file means none are configured."""
    target = path or schedules_path()
    if not target.exists():
        return []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ScheduleError(f"schedules unreadable: {exc}") from exc

    entries = payload.get("schedules") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise ScheduleError("schedules file must contain a 'schedules' list")

    schedules: list[Schedule] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ScheduleError("each schedule must be an object")
        schedule_id = str(entry.get("schedule_id", "")).strip()
        workflow_id = str(entry.get("workflow_id", "")).strip()
        if not schedule_id or not workflow_id:
            raise ScheduleError("schedule_id and workflow_id are required")
        schedules.append(
            Schedule(
                schedule_id=schedule_id,
                workflow_id=workflow_id,
                owner=str(entry.get("owner", "default")),
                kind=str(entry.get("kind", "calendar")),
                revision=int(entry.get("revision", 1)),
                timezone=str(entry.get("timezone", "UTC")),
                local_time=str(entry.get("local_time", "09:00")),
                delay_seconds=int(entry.get("delay_seconds", 0)),
                enabled=bool(entry.get("enabled", True)),
            )
        )
    return schedules


def plan_calendar_window(
    store: TimingStore,
    schedules: list[Schedule],
    *,
    now: datetime | None = None,
    days: int = 2,
) -> list[str]:
    """Upsert schedules and plan one occurrence per local day in the window."""
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    planned: list[str] = []
    for schedule in schedules:
        store.upsert_schedule(schedule, now=moment)
        if schedule.kind != "calendar" or not schedule.enabled:
            continue
        zone = ZoneInfo(schedule.timezone)
        first_day = moment.astimezone(zone).date()
        for offset in range(max(1, min(days, 14))):
            occurrence = store.plan_calendar(schedule, first_day + timedelta(days=offset))
            if occurrence:
                planned.append(occurrence)
    return planned




