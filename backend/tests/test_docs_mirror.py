"""Tests for the docs mirror sync engine."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services import docs_mirror as mod


def test_sync_from_repos_copies_markdown(tmp_path: Path):
    repo = tmp_path / "Code" / "uCore" / "docs"
    repo.mkdir(parents=True)
    (repo / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (repo / "nested").mkdir(parents=True, exist_ok=True)
    (repo / "nested" / "deep.md").write_text("# Deep\n", encoding="utf-8")
    (repo / "archive").mkdir(parents=True, exist_ok=True)
    (repo / "archive" / "old.md").write_text("# Old\n", encoding="utf-8")

    roots = {"uCore": repo}
    mirror = tmp_path / "mirror"
    result = mod.sync_from_repos(roots=roots, mirror_root=mirror)

    assert result["status"] == "completed"
    assert result["total_files"] == 2
    assert (mirror / "uCore" / "guide.md").exists()
    assert (mirror / "uCore" / "nested" / "deep.md").exists()
    assert not (mirror / "uCore" / "archive" / "old.md").exists()

    index = mod.mirror_status(mirror_root=mirror)
    assert index["status"] == "ok"
    assert index["total_files"] == 2


def test_sync_refuses_user_lane_paths(tmp_path: Path, monkeypatch):
    vault = tmp_path / "Vault"
    vault.mkdir(parents=True)
    (vault / "note.md").write_text("# Note\n", encoding="utf-8")

    monkeypatch.setattr(mod, "FORBIDDEN_ROOTS", (vault,))
    roots = {"user": vault}
    with pytest.raises(ValueError):
        mod.sync_from_repos(roots=roots, mirror_root=tmp_path / "mirror")


def test_mirror_status_empty(tmp_path: Path):
    status = mod.mirror_status(mirror_root=tmp_path / "nope")
    assert status["status"] == "empty"
    assert status["total_files"] == 0
