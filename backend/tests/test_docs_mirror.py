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


def _setup_repo(tmp_path: Path):
    repo = tmp_path / "Code" / "uCore" / "docs"
    repo.mkdir(parents=True)
    (repo / "guide.md").write_text("# Old\n", encoding="utf-8")
    mirror = tmp_path / "mirror"
    mod.sync_from_repos(roots={"uCore": repo}, mirror_root=mirror)
    return repo, mirror


def test_push_to_repo_requires_dev_mode(tmp_path, monkeypatch):
    repo, mirror = _setup_repo(tmp_path)

    monkeypatch.setattr(mod, "is_dev_mode_active", lambda: False)
    result = mod.push_to_repo(
        "uCore", "guide.md", "# New\n",
        mirror_root=mirror, roots={"uCore": repo},
    )

    assert result["success"] is False
    assert "Dev Mode" in result["error"]
    assert (repo / "guide.md").read_text(encoding="utf-8") == "# Old\n"


def test_push_to_repo_writes_back_in_dev_mode(tmp_path, monkeypatch):
    repo, mirror = _setup_repo(tmp_path)

    monkeypatch.setattr(mod, "is_dev_mode_active", lambda: True)
    result = mod.push_to_repo(
        "uCore", "guide.md", "# New\n",
        mirror_root=mirror, roots={"uCore": repo},
    )

    assert result["success"] is True
    assert (repo / "guide.md").read_text(encoding="utf-8") == "# New\n"


def test_diff_entry_detects_drift(tmp_path):
    repo, mirror = _setup_repo(tmp_path)

    no_drift = mod.diff_entry(
        "uCore", "guide.md", mirror_root=mirror, roots={"uCore": repo},
    )
    assert no_drift["has_diff"] is False

    (mirror / "uCore" / "guide.md").write_text("# Changed\n", encoding="utf-8")
    drift = mod.diff_entry(
        "uCore", "guide.md", mirror_root=mirror, roots={"uCore": repo},
    )
    assert drift["has_diff"] is True
    assert drift["source_status"] == "ok"
