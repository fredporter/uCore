from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts import ucmd


def test_manifest_uses_fixed_argument_arrays():
    commands = ucmd.load_engineering_commands()
    assert {item["id"] for item in commands} >= {"status", "check-paths", "test"}
    assert all(isinstance(item["argv"], list) for item in commands)


def test_manifest_rejects_duplicate_and_shell_commands(tmp_path):
    path = tmp_path / "commands.json"
    path.write_text(json.dumps([
        {"id": "same", "name": "One", "description": "", "argv": ["pwd"]},
        {"id": "same", "name": "Two", "description": "", "argv": "echo unsafe"},
    ]), encoding="utf-8")
    with pytest.raises(ValueError):
        ucmd.load_engineering_commands(path)


def test_engineering_execution_never_uses_shell(monkeypatch):
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(ucmd.subprocess, "run", run)
    command = {"argv": ["git", "status", "--short"]}
    assert ucmd.run_engineering(command) == 0
    assert calls == [(command["argv"], {"cwd": ucmd.REPO_ROOT, "check": False})]


def test_fzf_cancellation_does_not_execute(monkeypatch):
    monkeypatch.setattr(ucmd.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=130, stdout=""))
    assert ucmd.choose([{"id": "test", "name": "Tests", "description": ""}], "Test", None) is None


def test_user_listing_comes_from_ucore(monkeypatch, capsys):
    monkeypatch.setattr(ucmd, "list_user_workflows", lambda base, timeout: [
        {"id": "wf-one", "name": "Daily review", "description": "Review notes"}
    ])
    assert ucmd.main(["--mode", "user", "--list"]) == 0
    assert "wf-one\tDaily review" in capsys.readouterr().out


def test_user_run_requires_confirmation(monkeypatch):
    workflow = {"id": "wf-one", "name": "Daily review", "description": ""}
    monkeypatch.setattr(ucmd, "list_user_workflows", lambda base, timeout: [workflow])
    monkeypatch.setattr("builtins.input", lambda prompt: "no")
    called = []
    monkeypatch.setattr(ucmd, "run_user_workflow", lambda *args: called.append(args) or 0)
    assert ucmd.main(["--mode", "user", "--select", "wf-one"]) == 0
    assert called == []


def test_confirmed_user_run_uses_workflow_id(monkeypatch):
    workflow = {"id": "wf-one", "name": "Daily review", "description": ""}
    monkeypatch.setattr(ucmd, "list_user_workflows", lambda base, timeout: [workflow])
    called = []
    monkeypatch.setattr(ucmd, "run_user_workflow", lambda *args: called.append(args) or 0)
    assert ucmd.main(["--mode", "user", "--select", "wf-one", "--yes"]) == 0
    assert called == [(ucmd.DEFAULT_BASE_URL, "wf-one", 300)]


def test_backend_errors_return_failure(monkeypatch):
    monkeypatch.setattr(ucmd, "list_user_workflows", lambda *args: (_ for _ in ()).throw(RuntimeError("offline")))
    assert ucmd.main(["--mode", "user", "--list"]) == 1
