from pathlib import Path

import pytest

from app.services import workspace_files


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(workspace_files, "workspace_root", lambda source: tmp_path if source == "user" else None)
    return tmp_path


def test_workspace_file_lifecycle(workspace: Path):
    folder = workspace_files.create_entry("user", "", "Notes", "folder")
    created = workspace_files.create_entry("user", "/Notes", "Today.md", "file")
    workspace_files.write_file("user", created["path"], "# Today\n")

    assert folder["type"] == "folder"
    assert workspace_files.read_file("user", created["path"])["content"] == "# Today\n"
    assert workspace_files.list_tree("user")[0]["children"][0]["name"] == "Today.md"

    renamed = workspace_files.rename_entry("user", created["path"], "Plan.md")
    assert renamed["path"] == "/Notes/Plan.md"
    workspace_files.delete_entry("user", renamed["path"])
    assert not (workspace / "Notes" / "Plan.md").exists()


@pytest.mark.parametrize("path", ["../outside.md", "/../../outside.md"])
def test_workspace_rejects_traversal(workspace: Path, path: str):
    with pytest.raises(ValueError, match="inside the workspace"):
        workspace_files.read_file("user", path)


def test_workspace_rejects_unsupported_files(workspace: Path):
    with pytest.raises(ValueError, match="unsupported file extension"):
        workspace_files.create_entry("user", "", "payload.exe", "file")


def test_workspace_tree_excludes_hidden_and_runtime_directories(workspace: Path):
    (workspace / ".secret.md").write_text("secret", encoding="utf-8")
    (workspace / "node_modules").mkdir()
    (workspace / "Visible.md").write_text("visible", encoding="utf-8")

    tree = workspace_files.list_tree("user")

    assert [node["name"] for node in tree] == ["Visible.md"]
