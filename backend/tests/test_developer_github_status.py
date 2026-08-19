from __future__ import annotations

import json
from types import SimpleNamespace

from app.api import developer_api


def test_repo_github_status_reports_actions_and_pr(monkeypatch, tmp_path):
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

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps(responses.pop(0)), stderr="")

    monkeypatch.setattr(developer_api.subprocess, "run", fake_run)

    payload = developer_api._repo_github_status("uCore")

    assert payload["configured"] is True
    assert payload["repository"]["nameWithOwner"] == "fredporter/uCore"
    assert payload["runs"][0]["conclusion"] == "success"
    assert payload["pull_request"]["number"] == 3


def test_repo_github_status_degrades_when_gh_is_unavailable(monkeypatch, tmp_path):
    repo = tmp_path / "uCore"
    repo.mkdir()
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: repo)
    monkeypatch.setattr(developer_api, "_git_output", lambda _repo, *_args: "main")
    monkeypatch.setattr(
        developer_api.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="no auth"),
    )

    payload = developer_api._repo_github_status("uCore")

    assert payload["configured"] is False
    assert payload["branch"] == "main"
