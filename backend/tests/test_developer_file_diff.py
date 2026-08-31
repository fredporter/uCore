from __future__ import annotations

from app.api import developer_api


def test_file_diff_returns_index_baseline_for_unstaged_change(monkeypatch, tmp_path):
    file_path = tmp_path / "example.py"
    file_path.write_text("working tree\n", encoding="utf-8")
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_safe_file_path", lambda _repo, _path: file_path)

    def git_output(_repo, *args):
        if args[:2] == ("status", "--porcelain"):
            return " M example.py"
        if args[:2] == ("diff", "--"):
            return "diff --git a/example.py b/example.py"
        if args == ("show", ":example.py"):
            return "index baseline\n"
        return ""

    monkeypatch.setattr(developer_api, "_git_output", git_output)

    payload = developer_api._get_repo_file_diff("repo", "example.py")

    assert payload["status"] == "modified"
    assert payload["hasDiff"] is True
    assert payload["baseline"] == "index baseline\n"


def test_file_diff_returns_head_baseline_for_staged_and_clean_files(monkeypatch, tmp_path):
    file_path = tmp_path / "example.py"
    file_path.write_text("working tree\n", encoding="utf-8")
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_safe_file_path", lambda _repo, _path: file_path)

    status = {"value": "M  example.py"}

    def git_output(_repo, *args):
        if args[:2] == ("status", "--porcelain"):
            return status["value"]
        if args[:2] in {("diff", "--"), ("diff", "--cached")}:
            return "diff --git a/example.py b/example.py" if status["value"].strip() else ""
        if args == ("show", "HEAD:example.py"):
            return "head baseline\n"
        return ""

    monkeypatch.setattr(developer_api, "_git_output", git_output)

    staged = developer_api._get_repo_file_diff("repo", "example.py")
    status["value"] = ""
    clean = developer_api._get_repo_file_diff("repo", "example.py")

    assert staged["baseline"] == "head baseline\n"
    assert staged["status"] == "modified"
    assert clean == {
        "repo": "repo",
        "path": "example.py",
        "status": "clean",
        "diff": "",
        "hasDiff": False,
        "baseline": "head baseline\n",
    }


def test_file_diff_returns_empty_baseline_for_untracked_file(monkeypatch, tmp_path):
    file_path = tmp_path / "new.py"
    file_path.write_text("new file\n", encoding="utf-8")
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    monkeypatch.setattr(developer_api, "_safe_file_path", lambda _repo, _path: file_path)
    monkeypatch.setattr(
        developer_api,
        "_git_output",
        lambda _repo, *args: "?? new.py" if args[:2] == ("status", "--porcelain") else "",
    )

    payload = developer_api._get_repo_file_diff("repo", "new.py")

    assert payload["status"] == "added"
    assert payload["hasDiff"] is True
    assert payload["baseline"] == ""
