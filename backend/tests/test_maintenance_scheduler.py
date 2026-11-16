"""Focused tests for maintenance scheduler and vault sync skill."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_maintenance_scheduler_runs_jobs_once_in_order(
    tmp_path: Path,
    monkeypatch,
):
    import app.services.maintenance_scheduler as mod

    calls: list[str] = []

    async def fake_run_skill_by_id(skill_id: str, **kwargs):
        calls.append(skill_id)
        return {"success": True, "skill_id": skill_id, "params": kwargs}

    monkeypatch.setattr(mod, "run_skill_by_id", fake_run_skill_by_id)

    jobs = (
        mod.MaintenanceJob("backup", "03:00", {"type": "full"}),
        mod.MaintenanceJob("vault_sync", "04:00", {"summary_only": True}),
        mod.MaintenanceJob(
            "tasker_sync",
            "04:05",
            {"db": "database", "board": "inbox"},
        ),
        mod.MaintenanceJob("brain_sync", "04:15", {"hours": 24}),
        mod.MaintenanceJob(
            "clipboard_maintenance",
            "04:30",
            {"capture_current": True},
        ),
        mod.MaintenanceJob(
            "spool_prune",
            "04:35",
            {"max_age_days": 14, "archive_completed_tasks": True},
        ),
    )
    scheduler = mod.MaintenanceScheduler(
        state_path=tmp_path / "maintenance-state.json",
        jobs=jobs,
        interval_seconds=60,
    )

    first = await scheduler.run_due(now=datetime(2026, 6, 21, 4, 35))
    second = await scheduler.run_due(now=datetime(2026, 6, 21, 4, 59))

    assert [entry["skill_id"] for entry in first] == [
        "backup",
        "vault_sync",
        "tasker_sync",
        "brain_sync",
        "clipboard_maintenance",
        "spool_prune",
    ]
    assert second == []
    assert calls == [
        "backup",
        "vault_sync",
        "tasker_sync",
        "brain_sync",
        "clipboard_maintenance",
        "spool_prune",
    ]


def test_default_jobs_include_tasker_sync():
    import app.services.maintenance_scheduler as mod

    assert any(job.skill_id == "tasker_sync" for job in mod.DEFAULT_JOBS)


def test_default_jobs_include_clipboard_maintenance():
    import app.services.maintenance_scheduler as mod

    assert any(
        job.skill_id == "clipboard_maintenance" for job in mod.DEFAULT_JOBS
    )


def test_default_jobs_include_spool_prune():
    import app.services.maintenance_scheduler as mod

    assert any(
        job.skill_id == "spool_prune" for job in mod.DEFAULT_JOBS
    )


@pytest.mark.asyncio
async def test_vault_sync_dry_run_reports_vault_roots():
    import app.skills.builtin.vault_sync as mod

    result = await mod.VaultSync().run(
        dry_run=True,
        summary_only=True,
    )

    assert result["success"] is True
    assert result["status"] == "dry-run"
    assert result["sources"]


@pytest.mark.asyncio
async def test_manual_run_uses_configured_arguments_and_records_outcome(tmp_path, monkeypatch):
    from app.services import maintenance_scheduler as mod

    calls = []

    async def run(skill_id, **params):
        calls.append((skill_id, params))
        return {"success": bool(params.get("execution_authorized")), "requires_confirmation": not params.get("execution_authorized")}

    monkeypatch.setattr(mod, "run_skill_by_id", run)
    now = datetime.now()
    scheduler = mod.MaintenanceScheduler(
        state_path=tmp_path / "state.json",
        jobs=(mod.MaintenanceJob("backup", "00:00", {"type": "full"}),),
    )
    await scheduler.run_due(now)
    assert scheduler.status()["jobs"][0]["last_result"]["state"] == "needs_approval"
    await scheduler.run_once("backup")
    assert scheduler.status()["jobs"][0]["last_result"]["state"] == "completed"
    assert await scheduler.run_due(now) == []
    assert calls == [
        ("backup", {"type": "full"}),
        ("backup", {"type": "full", "execution_authorized": True}),
    ]


@pytest.mark.asyncio
async def test_routine_route_requires_admin_and_confirmation(monkeypatch):
    from unittest.mock import AsyncMock

    from aiohttp import web
    from aiohttp.test_utils import make_mocked_request

    from app.api import connections_api, metadata
    from app.services import identity, maintenance_scheduler

    monkeypatch.setattr(connections_api, "profile", lambda request: "local")
    current = {"active_profile_id": "local", "active_profile": {"role": "knight"}}
    monkeypatch.setattr(identity, "get_full_identity", lambda: current)
    scheduler = AsyncMock()
    scheduler.run_once.return_value = {"result": {"success": True}}
    monkeypatch.setattr(maintenance_scheduler, "get_maintenance_scheduler", lambda: scheduler)

    def request(headers=None):
        return make_mocked_request(
            "POST", "/api/system/maintenance/backup/run",
            match_info={"skill_id": "backup"}, headers=headers,
        )

    with pytest.raises(web.HTTPForbidden):
        await metadata.maintenance_run_handler(request({"x-ucore-confirm": "true"}))
    current["active_profile"]["role"] = "wizard"
    assert (await metadata.maintenance_run_handler(request())).status == 409
    scheduler.run_once.assert_not_awaited()
    assert (await metadata.maintenance_run_handler(request({"x-ucore-confirm": "true"}))).status == 200
    scheduler.run_once.assert_awaited_once_with("backup")
