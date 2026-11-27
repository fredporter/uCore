"""Gate B step 1 — observation intake, baseline and change detection.

Fixtures only: no sidecar is contacted. A transition is data and grants no
authority; admitting one is a separate, reviewed step.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.utils.sqlite_helpers import get_sqlite_connection

SUPPORTED_SCHEMA = 1
MAX_FIELDS = 32
MAX_VALUE_CHARS = 2000
IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
FIELD_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


class ObservationError(ValueError):
    """Raised when an observation cannot be admitted as data."""


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_id: str
    subject_id: str
    observed_at: str
    values: dict[str, Any]
    source_url: str = ""
    schema_version: int = SUPPORTED_SCHEMA


def _require_identifier(name: str, value: Any) -> str:
    text = str(value or "")
    if not IDENTIFIER.match(text):
        raise ObservationError(
            f"{name} must be 1-128 chars of letters, digits, dot, colon, underscore or hyphen"
        )
    return text


def _normalise_timestamp(value: Any) -> str:
    text = str(value or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationError("observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ObservationError("observed_at must include a timezone")
    return parsed.astimezone(UTC).isoformat()


def parse_observation(payload: dict[str, Any]) -> Observation:
    """Validate one bounded observation; reject anything unusable as data."""
    if not isinstance(payload, dict):
        raise ObservationError("observation must be an object")
    if payload.get("schema_version", SUPPORTED_SCHEMA) != SUPPORTED_SCHEMA:
        raise ObservationError(f"unsupported schema_version, expected {SUPPORTED_SCHEMA}")

    values = payload.get("values")
    if not isinstance(values, dict) or not values:
        raise ObservationError("values must be a non-empty object")
    if len(values) > MAX_FIELDS:
        raise ObservationError(f"values may hold at most {MAX_FIELDS} fields")

    cleaned: dict[str, Any] = {}
    for key, value in values.items():
        if not FIELD_NAME.match(str(key)):
            raise ObservationError(f"invalid field name: {key!r}")
        if isinstance(value, bool) or isinstance(value, (int, float)):
            cleaned[str(key)] = value
            continue
        if isinstance(value, str):
            if len(value) > MAX_VALUE_CHARS:
                raise ObservationError(f"value for {key!r} exceeds {MAX_VALUE_CHARS} chars")
            cleaned[str(key)] = value
            continue
        raise ObservationError(f"value for {key!r} must be a string, number or boolean")

    source_url = str(payload.get("source_url") or "")
    if source_url and not source_url.startswith(("http://", "https://")):
        raise ObservationError("source_url must be http(s) when supplied")

    return Observation(
        observation_id=_require_identifier("observation_id", payload.get("observation_id")),
        source_id=_require_identifier("source_id", payload.get("source_id")),
        subject_id=_require_identifier("subject_id", payload.get("subject_id")),
        observed_at=_normalise_timestamp(payload.get("observed_at")),
        values=cleaned,
        source_url=source_url,
    )


def transition_id_for(observation: Observation, changed: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "source": observation.source_id,
            "subject": observation.subject_id,
            "observed_at": observation.observed_at,
            "changed": changed,
        },
        sort_keys=True,
    )
    return "tr-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class ObservationStore:
    """Baselines, transitions and seen markers in one SQLite store."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or (settings.data_dir / "observations.db")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return get_sqlite_connection(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS obs_seen (
                    observation_id TEXT PRIMARY KEY,
                    seen_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS obs_baseline (
                    source_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    pipeline_version TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (source_id, subject_id, pipeline_version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS obs_transition (
                    transition_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    changed TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    run_id TEXT
                )
                """
            )
            conn.commit()

    def ingest(self, observation: Observation, *, pipeline_version: str = "v1") -> dict[str, Any]:
        """Admit one observation; return the outcome without granting authority."""
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            if conn.execute(
                "SELECT 1 FROM obs_seen WHERE observation_id = ?",
                (observation.observation_id,),
            ).fetchone():
                return {"accepted": True, "outcome": "duplicate"}

            conn.execute(
                "INSERT INTO obs_seen (observation_id, seen_at) VALUES (?, ?)",
                (observation.observation_id, now),
            )

            baseline = conn.execute(
                """
                SELECT observed_at, payload FROM obs_baseline
                WHERE source_id = ? AND subject_id = ? AND pipeline_version = ?
                """,
                (observation.source_id, observation.subject_id, pipeline_version),
            ).fetchone()

            if baseline is None:
                self._store_baseline(conn, observation, pipeline_version)
                conn.commit()
                return {"accepted": True, "outcome": "baseline"}

            if observation.observed_at <= baseline["observed_at"]:
                conn.commit()
                return {"accepted": False, "outcome": "stale"}

            previous = json.loads(baseline["payload"])
            changed = {
                key: value
                for key, value in observation.values.items()
                if previous.get(key) != value
            }
            removed = [key for key in previous if key not in observation.values]

            self._store_baseline(conn, observation, pipeline_version)
            if not changed and not removed:
                conn.commit()
                return {"accepted": True, "outcome": "suppressed"}

            transition = transition_id_for(observation, changed)
            conn.execute(
                """
                INSERT OR IGNORE INTO obs_transition
                (transition_id, source_id, subject_id, observed_at, changed,
                 status, created_at, run_id)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, NULL)
                """,
                (
                    transition,
                    observation.source_id,
                    observation.subject_id,
                    observation.observed_at,
                    json.dumps({"changed": changed, "removed": removed}, sort_keys=True),
                    now,
                ),
            )
            conn.commit()

        return {
            "accepted": True,
            "outcome": "transition",
            "transition_id": transition,
            "changed": changed,
            "removed": removed,
        }

    @staticmethod
    def _store_baseline(
        conn: sqlite3.Connection,
        observation: Observation,
        pipeline_version: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO obs_baseline
            (source_id, subject_id, pipeline_version, observed_at, payload)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (source_id, subject_id, pipeline_version)
            DO UPDATE SET observed_at = excluded.observed_at, payload = excluded.payload
            """,
            (
                observation.source_id,
                observation.subject_id,
                pipeline_version,
                observation.observed_at,
                json.dumps(observation.values, sort_keys=True),
            ),
        )

    def pending_transitions(self, limit: int = 50) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT transition_id, source_id, subject_id, observed_at, changed,
                       created_at
                FROM obs_transition
                WHERE status = 'pending'
                ORDER BY observed_at ASC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "transition_id": row["transition_id"],
                "source_id": row["source_id"],
                "subject_id": row["subject_id"],
                "observed_at": row["observed_at"],
                "change": json.loads(row["changed"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def mark_delivered(self, transition_id: str, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE obs_transition
                SET status = 'delivered', run_id = ?
                WHERE transition_id = ? AND status = 'pending'
                """,
                (run_id, transition_id),
            )
            conn.commit()


