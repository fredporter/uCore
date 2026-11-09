from app.services.workflow_starters import STARTERS, install_starter


def test_starter_is_optional_profile_owned_and_preserves_edits(tmp_path, monkeypatch):
    monkeypatch.setenv("UFLOW_TASKS_DIR", str(tmp_path))
    assert len(STARTERS) == 3
    assert install_starter("alice", "daily") == 4
    files = list(tmp_path.rglob("*.md"))
    assert all("profile: alice" in p.read_text() for p in files)
    edited = files[0]
    edited.write_text(edited.read_text() + "\nMy personal note\n")
    moved = tmp_path / "another-list" / edited.name
    moved.parent.mkdir()
    edited.rename(moved)
    assert install_starter("alice", "daily") == 0
    assert "My personal note" in moved.read_text()
    assert install_starter("bob", "daily") == 4
    assert len(list(tmp_path.rglob("*.md"))) == 8
