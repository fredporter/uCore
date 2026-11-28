"""Scheduler administration: create, revise and remove reviewed schedules."""
from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest
from aiohttp.test_utils import make_mocked_request

from app.api import observation_api
from app.services import identity as identity_module
from app.services import timing as timing_module


@pytest.fixture()
def schedules_file(tmp_path, monkeypatch):
    path = tmp_path / "config" / "schedules.json"
    monkeypatch.setattr(timing_module, "schedules_path", lambda: path)
    # Planning touches the timing database; the API tests only care about the file.
    monkeypatch.setattr(observation_api, "_plan_new_schedule", lambda schedule: None)
    return path


@pytest.fixture()
def owner(monkeypatch):
    monkeypatch.setattr(
        identity_module,
        "get_full_identity",
        lambda: {"active_profile_id": "default", "active_profile": {"role": "owner"}},
    )
    monkeypatch.setattr("app.api.connections_api.profile", lambda request: "default")


@pytest.fixture()
def workflows(monkeypatch):
    class Manager:
        def get_workflow(self, workflow_id, owner=None):
            return {"id": workflow_id} if workflow_id.startswith("wf-") else None

    monkeypatch.setattr("app.flow.workflow_api.get_workflow_manager", lambda: Manager())


def _async_return(value):
    async def _inner():
        return value

    return _inner


def _request(method: str, path: str, *, body: dict | None = None, confirm: bool = True, match=None):
    headers = {"x-ucore-confirm": "true"} if confirm else {}
    request = make_mocked_request(method, path, headers=headers, match_info=match or {})
    if body is not None:
        request.json = _async_return(body)  # type: ignore[assignment]
    return request


async def test_create_writes_a_validated_schedule(schedules_file, owner, workflows):
    response = await observation_api.handle_schedule_create(
        _request(
            "POST",
            "/api/host/schedules",
            body={
                "schedule_id": "sched-pilot",
                "workflow_id": "wf-pilot",
                "kind": "calendar",
                "timezone": "Australia/Perth",
                "local_time": "20:00",
                "enabled": True,
            },
        )
    )

    assert response.status == 201
    payload = json.loads(response.text)["schedule"]
    assert payload["schedule_id"] == "sched-pilot"
    assert payload["revision"] == 1

    saved = json.loads(schedules_file.read_text())["schedules"]
    assert [item["schedule_id"] for item in saved] == ["sched-pilot"]
    assert saved[0]["owner"] == "default"


async def test_create_rejects_unknown_timezone_and_workflow(schedules_file, owner, workflows):
    bad_zone = await observation_api.handle_schedule_create(
        _request(
            "POST",
            "/api/host/schedules",
            body={
                "schedule_id": "sched-1",
                "workflow_id": "wf-1",
                "timezone": "Mars/Olympus",
                "local_time": "20:00",
            },
        )
    )
    assert bad_zone.status == 400
    assert "timezone" in json.loads(bad_zone.text)["error"]

    bad_workflow = await observation_api.handle_schedule_create(
        _request(
            "POST",
            "/api/host/schedules",
            body={"schedule_id": "sched-1", "workflow_id": "nope", "local_time": "20:00"},
        )
    )
    assert bad_workflow.status == 400
    assert "workflow not found" in json.loads(bad_workflow.text)["error"]


async def test_create_rejects_duplicates_and_missing_confirmation(
    schedules_file, owner, workflows
):
    body = {"schedule_id": "sched-1", "workflow_id": "wf-1", "local_time": "20:00"}
    first = await observation_api.handle_schedule_create(
        _request("POST", "/api/host/schedules", body=body)
    )
    assert first.status == 201

    duplicate = await observation_api.handle_schedule_create(
        _request("POST", "/api/host/schedules", body=body)
    )
    assert duplicate.status == 409

    unconfirmed = await observation_api.handle_schedule_create(
        _request(
            "POST",
            "/api/host/schedules",
            body={**body, "schedule_id": "sched-2"},
            confirm=False,
        )
    )
    assert unconfirmed.status == 409




async def test_update_bumps_revision_and_can_disable(schedules_file, owner, workflows):
    await observation_api.handle_schedule_create(
        _request(
            "POST",
            "/api/host/schedules",
            body={"schedule_id": "sched-1", "workflow_id": "wf-1", "local_time": "20:00"},
        )
    )

    response = await observation_api.handle_schedule_update(
        _request(
            "PATCH",
            "/api/host/schedules/sched-1",
            body={"local_time": "21:30", "enabled": False},
            match={"schedule_id": "sched-1"},
        )
    )

    assert response.status == 200
    payload = json.loads(response.text)["schedule"]
    assert payload["revision"] == 2
    assert payload["local_time"] == "21:30"
    assert payload["enabled"] is False
    assert payload["workflow_id"] == "wf-1"  # untouched fields survive

    saved = json.loads(schedules_file.read_text())["schedules"][0]
    assert saved["revision"] == 2 and saved["local_time"] == "21:30"


async def test_update_and_delete_report_missing_rows(schedules_file, owner, workflows):
    missing = await observation_api.handle_schedule_update(
        _request(
            "PATCH",
            "/api/host/schedules/nope",
            body={"enabled": False},
            match={"schedule_id": "nope"},
        )
    )
    assert missing.status == 404

    gone = await observation_api.handle_schedule_delete(
        _request("DELETE", "/api/host/schedules/nope", match={"schedule_id": "nope"})
    )
    assert gone.status == 404


async def test_delete_removes_the_row_and_disarms_pending_occurrences(
    schedules_file, owner, workflows, tmp_path, monkeypatch
):
    await observation_api.handle_schedule_create(
        _request(
            "POST",
            "/api/host/schedules",
            body={
                "schedule_id": "sched-1",
                "workflow_id": "wf-1",
                "timezone": "UTC",
                "local_time": "09:00",
            },
        )
    )

    store = timing_module.TimingStore(tmp_path / "timing.db")
    schedule = timing_module.load_schedules()[0]
    store.upsert_schedule(schedule)
    occurrence = store.plan_calendar(schedule, date(2026, 11, 27))
    monkeypatch.setattr(timing_module, "TimingStore", lambda *a, **k: store)

    response = await observation_api.handle_schedule_delete(
        _request("DELETE", "/api/host/schedules/sched-1", match={"schedule_id": "sched-1"})
    )
    assert response.status == 200
    body = json.loads(response.text)
    assert body["remaining"] == 0
    assert body["skipped_occurrences"] == 1

    assert json.loads(schedules_file.read_text())["schedules"] == []
    assert store.get_schedule("sched-1") is None
    row = store.get_occurrence(occurrence)
    assert row["status"] == "skipped" and row["reason"] == "schedule-deleted"

    # With the planned schedule gone, admission has nothing to claim.
    assert await timing_module.admit_due(
        store, manager=None, now=datetime(2026, 11, 27, 9, 0, tzinfo=UTC)
    ) == []


async def test_admin_endpoints_refuse_non_administrators(schedules_file, monkeypatch):
    monkeypatch.setattr(
        identity_module,
        "get_full_identity",
        lambda: {"active_profile_id": "guest", "active_profile": {"role": "viewer"}},
    )
    monkeypatch.setattr("app.api.connections_api.profile", lambda request: "guest")

    response = await observation_api.handle_schedule_create(
        _request(
            "POST",
            "/api/host/schedules",
            body={"schedule_id": "x", "workflow_id": "wf-1"},
        )
    )
    assert response.status == 403
