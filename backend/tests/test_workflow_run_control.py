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
