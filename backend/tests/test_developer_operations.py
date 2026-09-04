from __future__ import annotations

import asyncio

import pytest

from app.services import developer_operations
from app.services.dev_layer import DevMode
from app.services.developer_operations import DeveloperOperationManager


def enable_dev_mode(monkeypatch):
    layer = type("Layer", (), {"mode": DevMode.ON})()
    monkeypatch.setattr(developer_operations, "get_dev_layer", lambda: layer)


def test_capabilities_expose_bounded_action_contract(monkeypatch):
    manager = DeveloperOperationManager()
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


def test_write_operation_waits_for_explicit_approval(monkeypatch):
    enable_dev_mode(monkeypatch)
    manager = DeveloperOperationManager()
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


def test_operations_require_full_dev_mode(monkeypatch):
    layer = type("Layer", (), {"mode": DevMode.MINIMAL})()
    monkeypatch.setattr(developer_operations, "get_dev_layer", lambda: layer)
    with pytest.raises(PermissionError, match="Dev Mode on"):
        DeveloperOperationManager().create(
            action="review-working-tree", repository="uCore", prompt="Review", context={}
        )


@pytest.mark.asyncio
async def test_read_operation_runs_and_records_normalized_events(monkeypatch, tmp_path):
    enable_dev_mode(monkeypatch)
    repo = tmp_path / "uCore"
    repo.mkdir()
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
    manager = DeveloperOperationManager()
    monkeypatch.setattr(manager, "_command", lambda: ["fake", "--acp"])
    operation = manager.create(
        action="review-working-tree", repository="uCore", prompt="Review it", context={}
    )
    await operation.task
    assert operation.status == "completed"
    assert operation.session_id == "session-1"
    assert any(event.get("type") == "acp" for event in operation.events)
