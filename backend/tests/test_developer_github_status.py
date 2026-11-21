from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.api import developer_api


@pytest.mark.parametrize(("branch_view", "branch"), [("default", "main"), ("working", "codex/github-alignment")])
def test_repo_github_status_reports_actions_and_pr(monkeypatch, tmp_path, branch_view, branch):
    repo = tmp_path / "uCore"
    repo.mkdir()
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: repo)
    monkeypatch.setattr(
        developer_api,
        "_git_output",
        lambda _repo, *_args: "codex/github-alignment",
    )

    responses = [
        {"nameWithOwner": "fredporter/uCore", "url": "https://github.com/fredporter/uCore", "defaultBranchRef": {"name": "main"}},
        [{"workflowName": "CI", "status": "completed", "conclusion": "success"}],
        [{"number": 3, "title": "Align GitHub", "state": "OPEN", "isDraft": False, "url": "https://github.com/fredporter/uCore/pull/3", "statusCheckRollup": []}],
    ]

    def fake_run(command, **_kwargs):
        for flag in ("--branch", "--head"):
            if flag in command:
                assert command[command.index(flag) + 1] == branch
        return SimpleNamespace(returncode=0, stdout=json.dumps(responses.pop(0)), stderr="")

    monkeypatch.setattr(developer_api.subprocess, "run", fake_run)

    payload = developer_api._repo_github_status("uCore", branch_view)

    assert payload["branch"] == branch

    assert payload["configured"] is True
    assert payload["repository"]["nameWithOwner"] == "fredporter/uCore"
    assert payload["runs"][0]["conclusion"] == "success"
    assert payload["pull_request"]["number"] == 3
    assert "error_code" not in payload


@pytest.mark.parametrize(("failure", "error_code"), [
    (FileNotFoundError(), "cli_missing"),
    (developer_api.subprocess.TimeoutExpired("gh", 10), "timeout"),
    (SimpleNamespace(returncode=4, stdout="", stderr="credential sentinel"), "auth"),
    (SimpleNamespace(returncode=1, stdout="", stderr="HTTP 401: credential sentinel"), "auth"),
    (SimpleNamespace(returncode=1, stdout="", stderr="lookup api.github.com: no such host"), "network"),
    (SimpleNamespace(returncode=1, stdout="", stderr="error connecting to api.github.com: i/o timeout"), "timeout"),
    (SimpleNamespace(returncode=1, stdout="", stderr="unexpected diagnostic sentinel"), "unknown"),
    (SimpleNamespace(returncode=0, stdout="invalid JSON sentinel", stderr=""), "unknown"),
])
def test_repo_github_status_classifies_unavailable_repository(monkeypatch, tmp_path, failure, error_code):
    repo = tmp_path / "uCore"
    repo.mkdir()
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: repo)
    monkeypatch.setattr(developer_api, "_git_output", lambda _repo, *_args: "main")

    def fake_run(*_args, **_kwargs):
        if isinstance(failure, Exception):
            raise failure
        return failure

    monkeypatch.setattr(developer_api.subprocess, "run", fake_run)

    payload = developer_api._repo_github_status("uCore")

    assert payload["configured"] is False
    assert payload["branch"] == "main"
    assert payload["error_code"] == error_code
    assert "sentinel" not in json.dumps(payload)


@pytest.mark.parametrize("failing_query", ["run", "pr"])
def test_repo_github_status_keeps_independent_query_results(monkeypatch, tmp_path, failing_query):
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_git_output", lambda _repo, *_args: "main")

    responses = {
        "repo": {"nameWithOwner": "fredporter/uCore", "defaultBranchRef": {"name": "main"}},
        "run": [{"conclusion": "failure"}],
        "pr": [{"number": 3}],
    }

    def fake_run(command, **_kwargs):
        query = command[1]
        if query == failing_query:
            return SimpleNamespace(returncode=1, stdout="", stderr="could not resolve host")
        return SimpleNamespace(returncode=0, stdout=json.dumps(responses[query]), stderr="")

    monkeypatch.setattr(developer_api.subprocess, "run", fake_run)

    payload = developer_api._repo_github_status("uCore")

    assert payload["configured"] is True
    if failing_query == "run":
        assert payload["error_code"] == "network"
        assert payload["runs_available"] is False
        assert payload["pull_request"]["number"] == 3
    else:
        assert "error_code" not in payload
        assert payload["runs_available"] is True
        assert payload["runs"][0]["conclusion"] == "failure"
        assert payload["pull_request"] is None


def test_repo_github_status_reports_missing_default_branch(monkeypatch, tmp_path):
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_git_output", lambda _repo, *_args: "main")

    def fake_run(command, **_kwargs):
        assert command[1] == "repo"
        return SimpleNamespace(returncode=0, stdout='{"defaultBranchRef": null}', stderr="")

    monkeypatch.setattr(developer_api.subprocess, "run", fake_run)

    payload = developer_api._repo_github_status("uCore", "default")

    assert payload["configured"] is True
    assert payload["branch"] == "unknown"
    assert payload["runs_available"] is False
    assert payload["error_code"] == "branch_unavailable"


@pytest.mark.asyncio
async def test_follow_up_is_idempotent_and_profile_scoped(monkeypatch, tmp_path):
    from app.api import tasker_api
    from app.services import identity

    profile = "default"
    monkeypatch.setattr(identity, "get_full_identity", lambda: {"active_profile_id": profile})
    monkeypatch.setattr(tasker_api, "default_tasker_dir", lambda: tmp_path)

    async def payload():
        return {
            "url": "https://github.com/fredporter/uCore/actions/runs/123",
            "branch": "main",
            "commit": "a" * 40,
        }

    request = SimpleNamespace(json=payload)
    first = await tasker_api.handle_github_follow_up(request)
    repeat = await tasker_api.handle_github_follow_up(request)
    assert (first.status, repeat.status) == (201, 200)
    task = json.loads(first.body)["updated"]
    assert json.loads(repeat.body)["updated"]["id"] == task["id"]
    assert "Repository: fredporter/uCore" in task["body"]
    assert "Commit: " + "a" * 40 in task["body"]

    profile = "second"
    other = await tasker_api.handle_github_follow_up(request)
    assert other.status == 201
    assert json.loads(other.body)["updated"]["id"] != task["id"]
    assert len(list(tmp_path.glob("inbox/*.md"))) == 2
