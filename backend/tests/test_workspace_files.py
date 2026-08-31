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
    opened = workspace_files.read_file("user", created["path"])
    saved = workspace_files.write_file(
        "user", created["path"], "# Today\n", opened["version"],
    )

    assert folder["type"] == "folder"
    assert workspace_files.read_file("user", created["path"])["content"] == "# Today\n"
    assert saved["version"] != opened["version"]
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


def test_workspace_moves_entries_between_folders(workspace: Path):
    workspace_files.create_entry("user", "", "From", "folder")
    workspace_files.create_entry("user", "", "To", "folder")
    created = workspace_files.create_entry("user", "/From", "Move.md", "file")

    moved = workspace_files.move_entry("user", created["path"], "/To")

    assert moved["path"] == "/To/Move.md"
    assert not (workspace / "From" / "Move.md").exists()
    assert (workspace / "To" / "Move.md").exists()


def test_workspace_rejects_moving_folder_inside_itself(workspace: Path):
    workspace_files.create_entry("user", "", "Parent", "folder")
    workspace_files.create_entry("user", "/Parent", "Child", "folder")

    with pytest.raises(ValueError, match="inside itself"):
        workspace_files.move_entry("user", "/Parent", "/Parent/Child")


def test_workspace_rejects_stale_write(workspace: Path):
    created = workspace_files.create_entry("user", "", "Conflict.md", "file")
    opened = workspace_files.read_file("user", created["path"])
    (workspace / "Conflict.md").write_text("external change", encoding="utf-8")

    with pytest.raises(workspace_files.WorkspaceConflictError, match="changed"):
        workspace_files.write_file(
            "user", created["path"], "client change", opened["version"],
        )
