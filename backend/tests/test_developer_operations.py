from __future__ import annotations

import asyncio
import subprocess

import pytest

from app.services import developer_operations
from app.services.dev_layer import DevMode
from app.services.developer_operations import DeveloperOperationManager


def enable_dev_mode(monkeypatch):
    layer = type("Layer", (), {"mode": DevMode.ON})()
    monkeypatch.setattr(developer_operations, "get_dev_layer", lambda: layer)


def init_repo(path):
    path.mkdir()
    subprocess.run(["git", "init", "--quiet", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True)
    (path / "example.py").write_text("value = 1\n")
    subprocess.run(["git", "-C", str(path), "add", "example.py"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "--quiet", "-m", "base"], check=True)


def test_capabilities_expose_bounded_action_contract(monkeypatch, tmp_path):
    manager = DeveloperOperationManager(tmp_path / "operations.json")
    monkeypatch.setattr(manager, "_command", lambda: ["nanocoder", "--acp"])
    capabilities = manager.capabilities()
    assert capabilities["engine"] == "nanocoder-acp"
    assert capabilities["approvalPolicy"] == "explicit-write"
    assert {item["id"] for item in capabilities["actions"]} == {
        "explain-selection",
        "diagnose-failure",
        "propose-tests",
        "plan-refactor",
        "review-working-tree",
        "implement-reviewed-task",
    }


def test_write_operation_waits_for_explicit_approval(monkeypatch, tmp_path):
    enable_dev_mode(monkeypatch)
    repo = tmp_path / "uCore"
    init_repo(repo)
    monkeypatch.setattr(developer_operations.settings, "udos_root", tmp_path)
    manager = DeveloperOperationManager(tmp_path / "operations.json")
    scheduled = []
    monkeypatch.setattr(
        asyncio, "create_task", lambda coroutine: scheduled.append(coroutine) or None
    )
    operation = manager.create(
        action="implement-reviewed-task",
        repository="uCore",
        prompt="Implement the reviewed task",
        context={"taskReference": "UFLOW-42", "secret": "discard"},
    )
    assert operation.status == "awaiting_approval"
    assert operation.context == {"taskReference": "UFLOW-42"}
    assert scheduled == []
    manager.deny(operation.id)
    assert operation.status == "denied"


def test_operations_require_full_dev_mode(monkeypatch, tmp_path):
    layer = type("Layer", (), {"mode": DevMode.MINIMAL})()
    monkeypatch.setattr(developer_operations, "get_dev_layer", lambda: layer)
    with pytest.raises(PermissionError, match="Dev Mode on"):
        DeveloperOperationManager(tmp_path / "operations.json").create(
            action="review-working-tree", repository="uCore", prompt="Review", context={}
        )


@pytest.mark.asyncio
async def test_read_operation_runs_and_records_normalized_events(monkeypatch, tmp_path):
    enable_dev_mode(monkeypatch)
    repo = tmp_path / "uCore"
    init_repo(repo)
    monkeypatch.setattr(developer_operations.settings, "udos_root", tmp_path)
    monkeypatch.setattr(developer_operations.settings, "udos_home", tmp_path / ".udos")

    class FakeClient:
        def __init__(self, *_args, event_handler=None, **_kwargs):
            self.event_handler = event_handler

        def configure_local_provider(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def initialize(self):
            return {"protocolVersion": 1}

        async def new_session(self, *, mode):
            assert mode == "plan"
            return "session-1"

        async def prompt(self, _session, _prompt):
            await self.event_handler(
                {
                    "method": "session/update",
                    "params": {"update": {"sessionUpdate": "plan", "entries": []}},
                }
            )
            return {"stopReason": "end_turn"}

    monkeypatch.setattr(developer_operations, "NanocoderAcpClient", FakeClient)
    manager = DeveloperOperationManager(tmp_path / "operations.json")
    monkeypatch.setattr(manager, "_command", lambda: ["fake", "--acp"])
    operation = manager.create(
        action="review-working-tree", repository="uCore", prompt="Review it", context={}
    )
    await operation.task
    assert operation.status == "completed"
    assert operation.session_id == "session-1"
    assert any(event.get("type") == "acp" for event in operation.events)


@pytest.mark.asyncio
async def test_write_operation_captures_isolated_proposal_and_applies_explicitly(
    monkeypatch, tmp_path
):
    enable_dev_mode(monkeypatch)
    repo = tmp_path / "uCore"
    init_repo(repo)
    monkeypatch.setattr(developer_operations.settings, "udos_root", tmp_path)
    monkeypatch.setattr(developer_operations.settings, "udos_home", tmp_path / ".udos")

    class FakeClient:
        def __init__(self, *_args, repository, **_kwargs):
            self.repository = repository

        def configure_local_provider(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def initialize(self):
            return {}

        async def new_session(self, *, mode):
            assert mode == "normal"
            return "session-write"

        async def prompt(self, _session, _prompt):
            (self.repository / "example.py").write_text("value = 2\n")
            return {"stopReason": "end_turn"}

    monkeypatch.setattr(developer_operations, "NanocoderAcpClient", FakeClient)
    manager = DeveloperOperationManager(tmp_path / "operations.json")
    monkeypatch.setattr(manager, "_command", lambda: ["fake", "--acp"])
    operation = manager.create(
        action="implement-reviewed-task",
        repository="uCore",
        prompt="Change the value",
        context={"taskReference": "UFLOW-42"},
    )
    manager.approve(operation.id)
    await operation.task

    assert (repo / "example.py").read_text() == "value = 1\n"
    proposal_file = operation.proposal["files"][0]
    manager.apply_proposal(operation.id, proposal_file["path"], proposal_file["fingerprint"])
    assert (repo / "example.py").read_text() == "value = 2\n"
    assert proposal_file["applied"] is True

    restored = DeveloperOperationManager(tmp_path / "operations.json").get(operation.id)
    assert restored.context["taskReference"] == "UFLOW-42"
    assert restored.proposal["files"][0]["applied"] is True


def test_proposal_rejects_a_stale_worktree(monkeypatch, tmp_path):
    repo = tmp_path / "uCore"
    init_repo(repo)
    monkeypatch.setattr(developer_operations.settings, "udos_root", tmp_path)
    manager = DeveloperOperationManager(tmp_path / "operations.json")
    operation = developer_operations.DeveloperOperation(
        id="operation-1",
        action="implement-reviewed-task",
        repository="uCore",
        prompt="Change it",
        context={},
        write_capable=True,
        status="completed",
        repository_fingerprint=developer_operations._repository_fingerprint(repo),
        proposal={
            "files": [
                {
                    "path": "example.py",
                    "patch": "unused",
                    "fingerprint": "patch-1",
                    "applied": False,
                }
            ]
        },
    )
    manager.operations[operation.id] = operation
    (repo / "untracked.txt").write_text("changed")
    with pytest.raises(RuntimeError, match="Repository changed"):
        manager.apply_proposal(operation.id, "example.py", "patch-1")
