from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.tasker_api import register_tasker_routes
from app.services.host_pim import HostPIMService
from app.services.task_action_bridge import TaskActionBridge, find_task_file


@pytest.fixture
def temp_tasker_dir(tmp_path: Path) -> Path:
    tasks_dir = tmp_path / "flow" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    return tasks_dir


def test_action_to_task_creation(temp_tasker_dir: Path):
    pim = MagicMock(spec=HostPIMService)
    bridge = TaskActionBridge(pim=pim)

    activity = {
        "title": "Review Vector Lattice Documentation",
        "content": "Confirm 4x4 px dot lattice invariant and export options.",
        "source": "activity_pod",
        "external_id": "act_999",
        "due": "2026-09-17T12:00:00Z",
        "binder": "GridCore",
        "priority": "high",
    }
    suggested_action = {
        "action_type": "apple_reminders",
        "payload": {"list_name": "GridCore"},
        "approval_status": "pending_approval",
    }

    res = bridge.action_to_task(
        activity_event=activity,
        board="inbox",
        suggested_action=suggested_action,
        tasker_dir=temp_tasker_dir,
    )

    assert res["ok"] is True
    assert res["metadata"]["due"] == "2026-09-17T12:00:00Z"
    assert res["metadata"]["action_type"] == "apple_reminders"
    assert res["metadata"]["approval_status"] == "pending_approval"

    # Verify written task file
    task_file = Path(res["task"]["path"])
    assert task_file.exists()
    content = task_file.read_text(encoding="utf-8")
    assert "action_type: apple_reminders" in content
    assert "approval_status: pending_approval" in content
    assert "2026-09-17T12:00:00Z" in content


def test_task_action_approval_gate_and_execution(temp_tasker_dir: Path):
    pim = MagicMock(spec=HostPIMService)
    pim.export_to_apple_reminders.return_value = {"ok": True, "title": "Test Task"}

    bridge = TaskActionBridge(pim=pim)

    # 1. Create a task with pending action
    created = bridge.action_to_task(
        activity_event={"title": "Automate Morning Briefing", "binder": "Productivity"},
        board="inbox",
        suggested_action={
            "action_type": "apple_reminders",
            "payload": {"list_name": "Productivity"},
            "approval_status": "pending_approval",
        },
        tasker_dir=temp_tasker_dir,
    )
    task_path = Path(created["task"]["path"])
    task_id = task_path.stem

    # 2. Executing without approval must fail with approval gate
    blocked_res = bridge.execute_action(
        task_id=task_id,
        action_type="apple_reminders",
        tasker_dir=temp_tasker_dir,
        force=False,
    )
    assert blocked_res["ok"] is False
    assert blocked_res["requires_approval"] is True

    # 3. Approve and execute
    approved_res = bridge.approve_task_action(
        task_id=task_id,
        execute_now=True,
        tasker_dir=temp_tasker_dir,
    )
    assert approved_res["ok"] is True
    assert approved_res["approval_status"] == "executed"
    pim.export_to_apple_reminders.assert_called_once()


def test_reject_task_action(temp_tasker_dir: Path):
    pim = MagicMock(spec=HostPIMService)
    bridge = TaskActionBridge(pim=pim)

    created = bridge.action_to_task(
        activity_event={"title": "Unwanted notification spam"},
        board="inbox",
        suggested_action={"action_type": "say", "approval_status": "pending_approval"},
        tasker_dir=temp_tasker_dir,
    )
    task_id = Path(created["task"]["path"]).stem

    res = bridge.reject_task_action(task_id=task_id, reason="Not appropriate for audio", tasker_dir=temp_tasker_dir)
    assert res["ok"] is True
    assert res["approval_status"] == "rejected"


def test_reminders_sync_inbound_and_outbound(temp_tasker_dir: Path):
    pim = MagicMock(spec=HostPIMService)
    pim.intake_apple_reminders.return_value = {
        "ok": True,
        "items": [
            {
                "id": "rem_1",
                "title": "Fix Teletext Mosaic Rendering",
                "notes": "Teletext G1 quantizer needs test coverage",
                "due_date": "2026-09-18T15:00:00Z",
                "list": "GridCore",
            }
        ],
    }
    pim.sync_apple_reminders_outbound.return_value = {
        "ok": True,
        "synced_count": 1,
        "items": [{"id": "rem_1", "title": "Fix Teletext Mosaic Rendering"}],
        "errors": [],
    }

    bridge = TaskActionBridge(pim=pim)

    # Inbound sync
    inbound_res = bridge.sync_inbound_reminders(
        list_name="GridCore",
        tasker_dir=temp_tasker_dir,
    )
    assert inbound_res["ok"] is True
    assert inbound_res["imported_count"] == 1

    # Outbound sync
    outbound_res = bridge.sync_outbound_binder(
        binder="GridCore",
        tasker_dir=temp_tasker_dir,
    )
    assert outbound_res["ok"] is True
    assert outbound_res["synced_count"] == 1


@pytest.mark.asyncio
async def test_workflow_tasker_autonomy_api(monkeypatch, temp_tasker_dir: Path):
    monkeypatch.setattr("app.flow.task_store.default_tasker_dir", lambda: temp_tasker_dir)
    monkeypatch.setattr("app.services.workflow_status.default_tasker_dir", lambda: temp_tasker_dir)
    monkeypatch.setattr("app.services.tasker_ops.default_tasker_dir", lambda: temp_tasker_dir)

    app = web.Application()
    register_tasker_routes(app)

    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()

    try:
        # 1. POST /api/workflow/tasks/action-to-task
        res = await client.post(
            "/api/workflow/tasks/action-to-task",
            json={
                "title": "API Autonomy Test Task",
                "content": "Verify autonomy API endpoints.",
                "binder": "TestBinder",
                "suggested_action": {
                    "action_type": "notify",
                    "payload": {"message": "Test Notification"},
                    "approval_status": "pending_approval",
                },
            },
        )
        assert res.status == 200
        data = await res.json()
        assert data["ok"] is True
        task_id = Path(data["task"]["path"]).stem

        # 2. POST /api/workflow/tasks/{task_id}/approve
        approve_res = await client.post(
            f"/api/workflow/tasks/{task_id}/approve",
            json={"execute_now": False},
        )
        assert approve_res.status == 200
        approve_data = await approve_res.json()
        assert approve_data["ok"] is True
        assert approve_data["approval_status"] == "approved"

        # 3. POST /api/workflow/tasks/{task_id}/reject
        reject_res = await client.post(
            f"/api/workflow/tasks/{task_id}/reject",
            json={"reason": "User cancelled"},
        )
        assert reject_res.status == 200
        reject_data = await reject_res.json()
        assert reject_data["ok"] is True
        assert reject_data["approval_status"] == "rejected"
    finally:
        await client.close()
