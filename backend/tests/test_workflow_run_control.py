"""Bounded run control: cancellation, checkpoints and the overall budget."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import make_mocked_request

from app.core.settings import settings
from app.flow import workflow_api
from app.services import identity, run_control
from app.services.workflow_manager import WorkflowManager


def _setup(tmp_path, monkeypatch, steps):
    manager = WorkflowManager()
    manager._db_path = tmp_path / "workflows.db"
    manager._init_db()
    manager.create_workflow("wf-1", "Workflow", steps, owner="alice")
    monkeypatch.setattr(workflow_api, "_manager", manager)
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


def _request(run_id: str | None = None):
    if run_id is None:
        return make_mocked_request(
            "POST", "/api/workflows/wf-1/run", match_info={"workflow_id": "wf-1"}
        )
    return make_mocked_request(
        "POST",
        f"/api/workflows/runs/{run_id}/cancel",
        match_info={"run_id": run_id},
    )


@pytest.mark.asyncio
async def test_run_stops_when_the_budget_is_exhausted(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [{"type": "skill", "skill_id": "safe", "params": {}}])
    monkeypatch.setattr(workflow_api, "RUN_BUDGET_SECONDS", 0)

    response = await workflow_api.handle_run_workflow(_request())

    payload = json.loads(response.text)
    assert payload["status"] == "timed_out"
    assert payload["steps"] == []


@pytest.mark.asyncio
async def test_run_stops_when_cancellation_is_requested(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, [{"type": "skill", "skill_id": "safe", "params": {}}])
    monkeypatch.setattr(run_control, "is_cancelled", lambda _run_id: True)

    response = await workflow_api.handle_run_workflow(_request())

    payload = json.loads(response.text)
    assert payload["status"] == "cancelled"
    assert payload["steps"] == []


def test_checkpoint_records_progress_while_running(tmp_path):
    manager = WorkflowManager()
    manager._db_path = tmp_path / "workflows.db"
    manager._init_db()
    manager.start_run(
        run_id="run-cp",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        owner="alice",
    )

    manager.checkpoint_run(
        run_id="run-cp", steps=[{"index": 1, "success": True}], owner="alice"
    )

    run = manager.get_run("run-cp", owner="alice")
    assert run is not None
    assert run["status"] == "running"
    assert run["steps"] == [{"index": 1, "success": True}]


@pytest.mark.asyncio
async def test_resume_runs_only_the_remaining_steps(tmp_path, monkeypatch):
    from app.skills import registry as skill_registry

    manager = _setup(
        tmp_path,
        monkeypatch,
        [
            {"type": "skill", "skill_id": "first", "params": {}},
            {"type": "skill", "skill_id": "second", "params": {}},
        ],
    )
    manager.save_run(
        run_id="run-old",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        finished_at="t1",
        status="interrupted",
        steps=[{"index": 1, "skill_id": "first", "success": True}],
        owner="alice",
    )
    called: list[str] = []

    async def fake_run(skill_id, **_kwargs):
        called.append(skill_id)
        return {"success": True}

    monkeypatch.setattr(skill_registry, "run_skill_by_id", fake_run)
    request = make_mocked_request(
        "POST",
        "/api/workflows/runs/run-old/resume",
        match_info={"run_id": "run-old"},
    )

    response = await workflow_api.handle_resume_run(request)

    payload = json.loads(response.text)
    assert payload["status"] == "completed"
    assert called == ["second"]
    assert [step["index"] for step in payload["steps"]] == [2]


@pytest.mark.asyncio
async def test_resume_rejects_running_and_finished_runs(tmp_path, monkeypatch):
    manager = _setup(
        tmp_path, monkeypatch, [{"type": "skill", "skill_id": "one", "params": {}}]
    )
    manager.start_run(
        run_id="run-live",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        owner="alice",
    )
    live = await workflow_api.handle_resume_run(
        make_mocked_request(
            "POST",
            "/api/workflows/runs/run-live/resume",
            match_info={"run_id": "run-live"},
        )
    )
    assert live.status == 409

    manager.save_run(
        run_id="run-complete",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        finished_at="t1",
        status="completed",
        steps=[{"index": 1, "success": True}],
        owner="alice",
    )
    nothing_left = await workflow_api.handle_resume_run(
        make_mocked_request(
            "POST",
            "/api/workflows/runs/run-complete/resume",
            match_info={"run_id": "run-complete"},
        )
    )
    assert nothing_left.status == 409

    missing = await workflow_api.handle_resume_run(
        make_mocked_request(
            "POST",
            "/api/workflows/runs/run-absent/resume",
            match_info={"run_id": "run-absent"},
        )
    )
    assert missing.status == 404


@pytest.mark.asyncio
async def test_run_completes_with_networking_disabled(tmp_path, monkeypatch):
    """A local-skill run must not need a network socket (Gate A acceptance)."""
    import socket

    from app.skills import registry as skill_registry

    _setup(tmp_path, monkeypatch, [{"type": "skill", "skill_id": "local", "params": {}}])

    def _blocked(*_args, **_kwargs):
        raise OSError("network disabled for acceptance")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)

    async def fake_run(skill_id, **_kwargs):
        return {"success": True, "skill_id": skill_id}

    monkeypatch.setattr(skill_registry, "run_skill_by_id", fake_run)

    response = await workflow_api.handle_run_workflow(_request())

    payload = json.loads(response.text)
    assert payload["status"] == "completed"
    assert [step["skill_id"] for step in payload["steps"]] == ["local"]


@pytest.mark.asyncio
async def test_cancel_endpoint_reports_state(tmp_path, monkeypatch):
    manager = _setup(
        tmp_path, monkeypatch, [{"type": "skill", "skill_id": "safe", "params": {}}]
    )
    manager.start_run(
        run_id="run-live",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        owner="alice",
    )

    accepted = await workflow_api.handle_cancel_run(_request("run-live"))
    assert accepted.status == 202
    assert json.loads(accepted.text)["status"] == "cancelling"
    run_control.clear("run-live")

    manager.save_run(
        run_id="run-done",
        workflow_id="wf-1",
        workflow_name="Workflow",
        started_at="t0",
        finished_at="t1",
        status="completed",
        steps=[],
        owner="alice",
    )
    rejected = await workflow_api.handle_cancel_run(_request("run-done"))
    assert rejected.status == 409

    missing = await workflow_api.handle_cancel_run(_request("run-absent"))
    assert missing.status == 404
