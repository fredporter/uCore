from __future__ import annotations

import json
import sqlite3
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import make_mocked_request

from app.core.settings import settings
from app.flow import workflow_api
from app.services import identity
from app.services.workflow_manager import WorkflowManager


def test_workflow_definitions_and_runs_are_profile_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    manager = WorkflowManager()
    manager.create_workflow("wf-alice", "Alice", [], owner="alice")
    manager.create_workflow("wf-bob", "Bob", [], owner="bob")
    manager.save_run("run-alice", "wf-alice", "Alice", "start", "end", "completed", [], owner="alice")
    manager.save_run("run-bob", "wf-bob", "Bob", "start", "end", "completed", [], owner="bob")

    assert [row["id"] for row in manager.list_workflows(owner="alice")] == ["wf-alice"]
    assert manager.get_workflow("wf-alice", owner="bob") is None
    assert [row["run_id"] for row in manager.get_all_runs(owner="bob")] == ["run-bob"]
    assert manager.get_run_history("wf-alice", owner="bob") == []


def test_legacy_records_migrate_to_default_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    with sqlite3.connect(tmp_path / "workflows.db") as conn:
        conn.execute("CREATE TABLE workflows (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, schedule TEXT, created_at TEXT NOT NULL, steps TEXT NOT NULL)")
        conn.execute("CREATE TABLE workflow_runs (run_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, workflow_name TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT NOT NULL, status TEXT NOT NULL, steps TEXT NOT NULL)")
        conn.execute("INSERT INTO workflows VALUES ('wf-legacy', 'Legacy', '', 'manual', 'before', '[]')")
        conn.execute("INSERT INTO workflow_runs VALUES ('run-legacy', 'wf-legacy', 'Legacy', 'before', 'before', 'completed', '[]')")

    manager = WorkflowManager()
    assert manager.get_workflow("wf-legacy", owner="default")["owner"] == "default"
    assert manager.get_workflow("wf-legacy", owner="other") is None
    assert manager.get_all_runs(owner="default")[0]["run_id"] == "run-legacy"


@pytest.mark.asyncio
async def test_list_api_uses_server_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    manager = WorkflowManager()
    manager.create_workflow("wf-alice", "Alice", [], owner="alice")
    manager.create_workflow("wf-bob", "Bob", [], owner="bob")
    monkeypatch.setattr(workflow_api, "_manager", manager)
    monkeypatch.setattr(identity, "get_full_identity", lambda: {"authenticated": True, "active_profile_id": "alice"})

    response = await workflow_api.handle_list_workflows(make_mocked_request("GET", "/api/workflows"))
    payload = json.loads(response.text)
    assert [row["id"] for row in payload["workflows"]] == ["wf-alice"]


@pytest.mark.asyncio
async def test_create_api_ignores_caller_owner(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    manager = WorkflowManager()
    monkeypatch.setattr(workflow_api, "_manager", manager)
    monkeypatch.setattr(identity, "get_full_identity", lambda: {"authenticated": True, "active_profile_id": "alice"})
    request = make_mocked_request("POST", "/api/workflows")
    request.json = AsyncMock(return_value={"name": "Mine", "owner": "bob", "steps": [{"type": "skill", "skill_id": "safe"}]})

    response = await workflow_api.handle_create_workflow(request)
    assert response.status == 201
    assert json.loads(response.text)["owner"] == "alice"
    assert manager.list_workflows(owner="bob") == []


@pytest.mark.asyncio
async def test_cross_profile_run_is_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    manager = WorkflowManager()
    manager.create_workflow("wf-alice", "Alice", [], owner="alice")
    monkeypatch.setattr(workflow_api, "_manager", manager)
    monkeypatch.setattr(identity, "get_full_identity", lambda: {"authenticated": True, "active_profile_id": "bob"})
    request = make_mocked_request("POST", "/api/workflows/wf-alice/run", match_info={"workflow_id": "wf-alice"})

    response = await workflow_api.handle_run_workflow(request)
    assert response.status == 404
    assert manager.get_all_runs() == []


@pytest.mark.asyncio
async def test_run_derives_user_scope_from_profile_role(tmp_path, monkeypatch):
    """A guest profile runs with user scope and local-only providers."""
    from app.skills import registry as skill_registry

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    manager = WorkflowManager()
    manager.create_workflow(
        "wf-guest",
        "Guest",
        [{"type": "skill", "skill_id": "safe", "params": {}}],
        owner="guest",
    )
    monkeypatch.setattr(workflow_api, "_manager", manager)
    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: {
            "authenticated": True,
            "active_profile_id": "guest",
            "active_profile": {"id": "guest", "role": "guest"},
        },
    )

    seen = {}

    async def fake_run(skill_id, **kwargs):
        seen["skill_id"] = skill_id
        seen["context"] = kwargs.get("context")
        return {"success": True}

    monkeypatch.setattr(skill_registry, "run_skill_by_id", fake_run)
    request = make_mocked_request("POST", "/api/workflows/wf-guest/run", match_info={"workflow_id": "wf-guest"})

    response = await workflow_api.handle_run_workflow(request)

    assert response.status == 200
    assert seen["skill_id"] == "safe"
    assert seen["context"].scope == "user"
    assert seen["context"].metadata == {"profile": "guest", "role": "guest", "surface": "workflow-run"}
    assert seen["context"].provider_eligibility == ["ollama"]


@pytest.mark.asyncio
async def test_run_grants_developer_scope_only_from_role(tmp_path, monkeypatch):
    """A developer profile receives developer scope; the step cannot ask for it."""
    from app.skills import registry as skill_registry

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    manager = WorkflowManager()
    manager.create_workflow(
        "wf-dev",
        "Dev",
        [{"type": "skill", "skill_id": "safe", "params": {}}],
        owner="dev",
    )
    monkeypatch.setattr(workflow_api, "_manager", manager)
    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: {
            "authenticated": True,
            "active_profile_id": "dev",
            "active_profile": {"id": "dev", "role": "developer"},
        },
    )

    seen = {}

    async def fake_run(skill_id, **kwargs):
        seen["context"] = kwargs.get("context")
        return {"success": True}

    monkeypatch.setattr(skill_registry, "run_skill_by_id", fake_run)
    request = make_mocked_request("POST", "/api/workflows/wf-dev/run", match_info={"workflow_id": "wf-dev"})

    response = await workflow_api.handle_run_workflow(request)

    assert response.status == 200
    assert seen["context"].scope == "developer"
    assert seen["context"].network_policy == "local_only"
