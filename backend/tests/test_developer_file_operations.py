from __future__ import annotations

import pytest

from app.api import developer_api


@pytest.fixture
def repo(monkeypatch, tmp_path):
    monkeypatch.setattr(developer_api, "_repo_path", lambda _name: tmp_path)
    return tmp_path


def test_create_move_and_delete_require_current_revision(repo):
    created = developer_api._create_repo_file("repo", "src/new.py", "value = 1\n")
    assert created["path"] == "src/new.py"
    moved = developer_api._move_repo_file("repo", "src/new.py", "src/renamed.py")
    assert moved["path"] == "src/renamed.py"
    with pytest.raises(developer_api.FileConflictError):
        developer_api._delete_repo_file("repo", "src/renamed.py", "stale")
    deleted = developer_api._delete_repo_file("repo", "src/renamed.py", moved["revision"])
    assert deleted["deleted"] is True


def test_save_rejects_external_change(repo):
    path = repo / "example.py"
    path.write_text("before\n", encoding="utf-8")
    revision = developer_api._file_revision(path)
    path.write_text("external update with different size\n", encoding="utf-8")
    with pytest.raises(developer_api.FileConflictError):
        developer_api._save_repo_file("repo", "example.py", "editor update\n", revision)
    assert path.read_text(encoding="utf-8").startswith("external")


def test_file_operations_reject_escape_and_overwrite(repo):
    (repo / "exists.py").write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="escapes"):
        developer_api._create_repo_file("repo", "../outside.py")
    with pytest.raises(FileExistsError):
        developer_api._create_repo_file("repo", "exists.py")


def test_diagnostics_are_real_or_explicitly_unsupported(repo):
    (repo / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    (repo / "notes.md").write_text("# Fine\n", encoding="utf-8")
    python_result = developer_api._diagnose_repo_file("repo", "broken.py")
    markdown_result = developer_api._diagnose_repo_file("repo", "notes.md")
    assert python_result["adapter"] == "python-ast"
    assert python_result["diagnostics"][0]["severity"] == "error"
    assert markdown_result == {
        "repo": "repo",
        "path": "notes.md",
        "supported": False,
        "adapter": None,
        "diagnostics": [],
    }
