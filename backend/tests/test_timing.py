"""Gate B milestone 2: durable timing adapter."""
from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, timedelta

import pytest

from app.services import identity
from app.services.timing import (
    Schedule,
    ScheduleError,
    TimingStore,
    admit_due,
    load_schedules,
    occurrence_id_for,
    plan_calendar_window,
    resolve_local,
)
from app.services.workflow_manager import WorkflowManager


def _store(tmp_path) -> TimingStore:
    return TimingStore(tmp_path / "timing.db")


def _calendar(**overrides) -> Schedule:
    values = {
        "schedule_id": "s-1",
        "workflow_id": "wf-1",
        "owner": "alice",
        "kind": "calendar",
        "timezone": "UTC",
        "local_time": "09:00",
    }
    values.update(overrides)
    return Schedule(**values)


def _delay(seconds: int = 60, **overrides) -> Schedule:
    values = {
        "schedule_id": "s-delay",
        "workflow_id": "wf-1",
        "owner": "alice",
        "kind": "delay",
        "delay_seconds": seconds,
    }
    values.update(overrides)
    return Schedule(**values)


def _manager(tmp_path, monkeypatch):
    manager = WorkflowManager()
    manager._db_path = tmp_path / "workflows.db"
    manager._init_db()
    manager.create_workflow(
        "wf-1",
        "Workflow",
        [{"type": "skill", "skill_id": "local", "params": {}}],
        owner="alice",
    )
    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: {
            "authenticated": True,
            "active_profile_id": "alice",
            "active_profile": {"id": "alice", "role": "developer"},
        },
    )
    return manager


@pytest.fixture(autouse=True)
def _fake_skill(monkeypatch):
    from app.skills import registry

    async def fake_run(skill_id, **_kwargs):
        return {"success": True, "skill_id": skill_id}

    monkeypatch.setattr(registry, "run_skill_by_id", fake_run)


def test_resolve_local_skips_gaps_and_picks_the_first_ambiguous_occurrence():
    noon = resolve_local(date(2026, 11, 27), "09:00", "UTC")
    assert noon == datetime(2026, 11, 27, 9, 0, tzinfo=UTC)

    # 02:30 does not exist on the US spring-forward date.
    assert resolve_local(date(2026, 3, 8), "02:30", "America/New_York") is None

    ambiguous = resolve_local(date(2026, 11, 1), "01:30", "America/New_York")
    assert ambiguous is not None
    assert ambiguous.utcoffset() == timedelta(hours=-4)


def test_calendar_occurrence_identity_is_stable(tmp_path):
    store = _store(tmp_path)
    schedule = _calendar()
    store.upsert_schedule(schedule)

    first = store.plan_calendar(schedule, date(2026, 11, 27))
    second = store.plan_calendar(schedule, date(2026, 11, 27))

    expected = occurrence_id_for(
        "s-1", 1, datetime(2026, 11, 27, 9, 0, tzinfo=UTC)
    )
    assert first == second == expected
    occurrence = store.get_occurrence(first)
    assert occurrence["due_at"] == "2026-11-27T09:00:00+00:00"
    assert occurrence["status"] == "pending"


def test_occurrences_are_listed_newest_first_and_bounded(tmp_path):
    store = _store(tmp_path)
    schedule = _calendar()
    store.upsert_schedule(schedule)
    for day in (date(2026, 11, 26), date(2026, 11, 27), date(2026, 11, 28)):
        store.plan_calendar(schedule, day)

    rows = store.list_occurrences("s-1")
    assert [row["due_at"] for row in rows] == [
        "2026-11-28T09:00:00+00:00",
        "2026-11-27T09:00:00+00:00",
        "2026-11-26T09:00:00+00:00",
    ]

    assert len(store.list_occurrences("s-1", limit=2)) == 2
    assert store.list_occurrences("s-1", limit=0)  # clamped, never empty by request
    assert store.list_occurrences("missing") == []
    assert [row["schedule_id"] for row in store.list_schedules()] == ["s-1"]


def test_an_obsolete_revision_is_never_claimed(tmp_path):
    store = _store(tmp_path)
    store.upsert_schedule(_calendar())
    old = store.plan_calendar(_calendar(), date(2026, 11, 27))

    revised = _calendar(revision=2, local_time="10:00")
    store.upsert_schedule(revised)
    new = store.plan_calendar(revised, date(2026, 11, 27))

    at_0930 = datetime(2026, 11, 27, 9, 30, tzinfo=UTC)
    assert store.claim_due(now=at_0930) == []
    assert store.get_occurrence(old)["status"] == "pending"

    at_1000 = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    assert [row["occurrence_id"] for row in store.claim_due(now=at_1000)] == [new]


def test_a_missed_window_is_receipted_not_run(tmp_path):
    store = _store(tmp_path)
    schedule = _calendar()
    store.upsert_schedule(schedule)
    occurrence = store.plan_calendar(schedule, date(2026, 11, 27))

    late = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    assert store.claim_due(now=late, grace_seconds=300) == []

    stored = store.get_occurrence(occurrence)
    assert stored["status"] == "missed"
    assert stored["reason"] == "missed-window"


def test_overlapping_occurrences_are_skipped(tmp_path):
    store = _store(tmp_path)
    schedule = _delay(seconds=10)
    store.upsert_schedule(schedule)
    base = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    first = store.plan_delay(schedule, now=base)
    second = store.plan_delay(schedule, now=base + timedelta(seconds=20))

    claimed = store.claim_due(now=base + timedelta(seconds=60))

    assert [row["occurrence_id"] for row in claimed] == [first]
    assert store.get_occurrence(second)["status"] == "skipped"
    assert store.get_occurrence(second)["reason"] == "overlap"


def test_reconcile_returns_claims_to_pending(tmp_path):
    store = _store(tmp_path)
    schedule = _delay(seconds=10)
    store.upsert_schedule(schedule)
    base = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    occurrence = store.plan_delay(schedule, now=base)

    store.claim_due(now=base + timedelta(seconds=30))
    assert store.get_occurrence(occurrence)["status"] == "claimed"

    assert store.reconcile() == 1
    assert store.get_occurrence(occurrence)["status"] == "pending"
    assert [row["occurrence_id"] for row in store.claim_due(now=base + timedelta(seconds=30))] == [
        occurrence
    ]


def test_disabled_schedule_is_not_claimed(tmp_path):
    store = _store(tmp_path)
    schedule = _delay(seconds=10, enabled=False)
    store.upsert_schedule(schedule)
    base = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    occurrence = store.plan_delay(schedule, now=base)

    assert store.claim_due(now=base + timedelta(seconds=30)) == []
    assert store.get_occurrence(occurrence)["status"] == "pending"


@pytest.mark.asyncio
async def test_admission_is_deterministic_and_idempotent(tmp_path, monkeypatch):
    store = _store(tmp_path)
    manager = _manager(tmp_path, monkeypatch)
    schedule = _delay(seconds=10)
    store.upsert_schedule(schedule)
    base = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    occurrence = store.plan_delay(schedule, now=base)

    first = await admit_due(store, manager, now=base + timedelta(seconds=30))

    assert first[0]["status"] == "admitted"
    run_id = first[0]["run_id"]
    assert store.get_occurrence(occurrence)["status"] == "completed"
    assert store.get_occurrence(occurrence)["run_id"] == run_id
    assert manager.get_run(run_id, owner="alice")["status"] == "completed"

    # Emulate a crash after admission but before the occurrence was marked done.
    with sqlite3.connect(store._db_path) as conn:
        conn.execute(
            "UPDATE occurrence SET status='pending', run_id=NULL WHERE occurrence_id=?",
            (occurrence,),
        )
    replay = await admit_due(store, manager, now=base + timedelta(seconds=30))

    assert replay[0]["run_id"] == run_id
    assert len(manager.get_all_runs(owner="alice")) == 1



def test_prune_removes_finished_occurrences_only(tmp_path):
    store = _store(tmp_path)
    schedule = _delay(seconds=10)
    store.upsert_schedule(schedule)
    base = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    finished = store.plan_delay(schedule, now=base)
    store.claim_due(now=base + timedelta(seconds=30))
    store.complete(finished, "run-1")
    pending = store.plan_delay(schedule, now=base + timedelta(days=2))

    removed = store.prune_occurrences(days=30, now=base + timedelta(days=40))

    assert removed == 1
    assert store.get_occurrence(finished) is None
    assert store.get_occurrence(pending) is not None


def test_load_schedules_reads_reviewed_config(tmp_path):
    import json

    path = tmp_path / "schedules.json"
    path.write_text(
        json.dumps(
            {
                "schedules": [
                    {
                        "schedule_id": "s-1",
                        "workflow_id": "wf-1",
                        "owner": "alice",
                        "kind": "calendar",
                        "timezone": "UTC",
                        "local_time": "09:00",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    schedules = load_schedules(path)

    assert [schedule.schedule_id for schedule in schedules] == ["s-1"]
    assert schedules[0].owner == "alice"


def test_missing_schedule_file_means_none_configured(tmp_path):
    assert load_schedules(tmp_path / "absent.json") == []


def test_invalid_schedule_config_is_rejected(tmp_path):
    import json

    path = tmp_path / "schedules.json"
    path.write_text(json.dumps({"schedules": [{"workflow_id": "wf-1"}]}), encoding="utf-8")

    with pytest.raises(ScheduleError):
        load_schedules(path)


def test_calendar_window_plans_each_day_once(tmp_path):
    store = _store(tmp_path)
    schedule = _calendar()
    now = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)

    first = plan_calendar_window(store, [schedule], now=now, days=2)
    second = plan_calendar_window(store, [schedule], now=now, days=2)

    assert first == second
    assert len(first) == 2

