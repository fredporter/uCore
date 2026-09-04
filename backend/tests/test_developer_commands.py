from __future__ import annotations

import asyncio
import json

import pytest

from app.services import developer_commands
from app.services.developer_commands import MAX_OUTPUT, CommandRun, DeveloperCommandManager


def test_discovers_only_approved_repository_scripts(tmp_path):
    (tmp_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "vitest", "build": "vite build", "deploy": "unsafe"}}),
        encoding="utf-8",
    )
    actions = DeveloperCommandManager().discover("repo", tmp_path)
    assert [item["id"] for item in actions] == ["build", "test"]
    assert all(item["command"][0] == "pnpm" for item in actions)


@pytest.mark.asyncio
async def test_execution_redacts_and_bounds_output(monkeypatch, tmp_path):
    class Process:
        returncode = 0
        pid = 123

        async def communicate(self):
            return (("token=very-secret\n" + "x" * MAX_OUTPUT).encode(), None)

    monkeypatch.setattr(
        asyncio,
        "create_subprocess_exec",
        lambda *_args, **_kwargs: asyncio.sleep(0, result=Process()),
    )
    monkeypatch.setattr(developer_commands.settings, "logs_dir", tmp_path / "logs")
    run = CommandRun(id="run", repository="repo", action="test", command=("pnpm", "run", "test"))
    await DeveloperCommandManager()._execute(run, tmp_path, 5)
    assert run.status == "passed"
    assert "very-secret" not in run.output
    assert "[REDACTED]" in run.output
    assert len(run.output) == MAX_OUTPUT
    assert (tmp_path / "logs/developer-actions.jsonl").is_file()


@pytest.mark.asyncio
async def test_timeout_is_recorded_and_process_group_stopped(monkeypatch, tmp_path):
    class Process:
        returncode = None
        pid = 456

        async def communicate(self):
            await asyncio.sleep(1)
            return (b"", None)

    killed = []
    monkeypatch.setattr(
        asyncio,
        "create_subprocess_exec",
        lambda *_args, **_kwargs: asyncio.sleep(0, result=Process()),
    )
    monkeypatch.setattr(developer_commands.os, "killpg", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(developer_commands.settings, "logs_dir", tmp_path / "logs")
    run = CommandRun(id="run", repository="repo", action="test", command=("pnpm", "run", "test"))
    await DeveloperCommandManager()._execute(run, tmp_path, 0.01)
    assert run.status == "timed_out"
    assert killed and killed[0][0] == 456


def test_start_requires_dev_mode_and_known_action(monkeypatch, tmp_path):
    layer = type("Layer", (), {"mode": developer_commands.DevMode.OFF})()
    monkeypatch.setattr(developer_commands, "get_dev_layer", lambda: layer)
    with pytest.raises(PermissionError, match="Dev Mode"):
        DeveloperCommandManager().start("repo", tmp_path, "test")
