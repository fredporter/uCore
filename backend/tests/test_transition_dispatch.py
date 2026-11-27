"""Gate B milestone 1: reviewed transition-to-run admission."""
from __future__ import annotations

import sqlite3

import pytest

from app.services import identity
from app.services.observation_intake import ObservationStore, parse_observation
from app.services.transition_bindings import Binding
from app.services.transition_dispatch import dispatch_transitions, run_id_for
from app.services.workflow_manager import WorkflowManager


@pytest.fixture(autouse=True)
def _fake_skill(monkeypatch):
    from app.skills import registry

    async def fake_run(skill_id, **_kwargs):
        return {"success": True, "skill_id": skill_id}

    monkeypatch.setattr(registry, "run_skill_by_id", fake_run)


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


def _binding(**overrides) -> Binding:
    values = {
        "binding_id": "b-1",
        "source_id": "feed.example",
        "subject_id": "notice",
        "workflow_id": "wf-1",
        "owner": "alice",
        "allowed_changes": frozenset({"status"}),
    }
    values.update(overrides)
    return Binding(**values)


def _transition(store: ObservationStore) -> dict:
    store.ingest(
        parse_observation(
            {
                "observation_id": "obs-1",
                "source_id": "feed.example",
                "subject_id": "notice",
                "observed_at": "2026-11-26T10:00:00Z",
                "values": {"status": "open"},
            }
        )
    )
    return store.ingest(
        parse_observation(
            {
                "observation_id": "obs-2",
                "source_id": "feed.example",
                "subject_id": "notice",
                "observed_at": "2026-11-26T11:00:00Z",
                "values": {"status": "closed"},
            }
        )
    )


def _reopen_transition(path, transition_id: str) -> None:
    """Emulate a crash before acknowledgement."""
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE obs_transition SET status = 'pending', run_id = NULL WHERE transition_id = ?",
            (transition_id,),
        )


@pytest.mark.asyncio
async def test_unmatched_transition_is_suppressed_with_a_receipt(tmp_path, monkeypatch):
    store = ObservationStore(tmp_path / "observations.db")
    manager = _manager(tmp_path, monkeypatch)
    transition = _transition(store)

    results = await dispatch_transitions(store, manager, [])

    assert results[0]["status"] == "suppressed"
    assert results[0]["reason"] == "unmatched"
    receipt = store.get_receipt(transition["transition_id"])
    assert receipt is not None and receipt["status"] == "suppressed"
    assert manager.get_all_runs(owner="alice") == []


@pytest.mark.asyncio
async def test_disabled_binding_is_suppressed(tmp_path, monkeypatch):
    store = ObservationStore(tmp_path / "observations.db")
    manager = _manager(tmp_path, monkeypatch)
    _transition(store)

    results = await dispatch_transitions(store, manager, [_binding(enabled=False)])

    assert results[0]["reason"] == "disabled"
    assert manager.get_all_runs(owner="alice") == []


@pytest.mark.asyncio
async def test_change_outside_the_predicate_is_suppressed(tmp_path, monkeypatch):
    store = ObservationStore(tmp_path / "observations.db")
    manager = _manager(tmp_path, monkeypatch)
    _transition(store)

    results = await dispatch_transitions(
        store, manager, [_binding(allowed_changes=frozenset({"count"}))]
    )

    assert results[0]["reason"] == "predicate:status"
    assert manager.get_all_runs(owner="alice") == []


@pytest.mark.asyncio
async def test_matched_transition_admits_one_run_with_a_linked_receipt(tmp_path, monkeypatch):
    store = ObservationStore(tmp_path / "observations.db")
    manager = _manager(tmp_path, monkeypatch)
    transition = _transition(store)

    results = await dispatch_transitions(store, manager, [_binding()])

    expected_run = run_id_for("b-1", transition["transition_id"])
    assert results[0] == {
        "transition_id": transition["transition_id"],
        "status": "admitted",
        "binding_id": "b-1",
        "workflow_id": "wf-1",
        "run_id": expected_run,
    }
    run = manager.get_run(expected_run, owner="alice")
    assert run is not None and run["status"] == "completed"
    receipt = store.get_receipt(transition["transition_id"])
    assert receipt["status"] == "admitted"
    assert receipt["run_id"] == expected_run
    assert store.pending_transitions() == []


@pytest.mark.asyncio
async def test_replay_after_a_crash_does_not_create_a_second_run(tmp_path, monkeypatch):
    store = ObservationStore(tmp_path / "observations.db")
    manager = _manager(tmp_path, monkeypatch)
    transition = _transition(store)
    await dispatch_transitions(store, manager, [_binding()])

    _reopen_transition(store._db_path, transition["transition_id"])
    results = await dispatch_transitions(store, manager, [_binding()])

    assert results[0]["status"] == "already-admitted"
    assert len(manager.get_all_runs(owner="alice")) == 1


@pytest.mark.asyncio
async def test_restart_converges_on_the_same_run(tmp_path, monkeypatch):
    db = tmp_path / "observations.db"
    store = ObservationStore(db)
    manager = _manager(tmp_path, monkeypatch)
    transition = _transition(store)
    admitted = await dispatch_transitions(store, manager, [_binding()])

    restarted_store = ObservationStore(db)
    restarted_manager = _manager(tmp_path, monkeypatch)
    _reopen_transition(db, transition["transition_id"])
    replay = await dispatch_transitions(restarted_store, restarted_manager, [_binding()])

    assert replay[0]["run_id"] == admitted[0]["run_id"]
    assert len(restarted_manager.get_all_runs(owner="alice")) == 1

