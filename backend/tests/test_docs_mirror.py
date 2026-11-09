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


@pytest.mark.parametrize("legacy_flag", [True, False])
def test_push_to_repo_is_retired_even_with_legacy_bypass(tmp_path, legacy_flag):
    repo, mirror = _setup_repo(tmp_path)
    before = (repo / "guide.md").read_bytes()
    result = mod.push_to_repo("uCore", "guide.md", "# New\n", require_dev_mode=legacy_flag,
                              mirror_root=mirror, roots={"uCore": repo})
    assert result["success"] is False
    assert result["error"] == "repository_writeback_retired"
    assert (repo / "guide.md").read_bytes() == before


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


def test_refresh_rejects_symlink_that_would_overwrite_source(tmp_path):
    repo, mirror = _setup_repo(tmp_path)
    cached = mirror / "uCore" / "guide.md"
    cached.unlink()
    cached.symlink_to(repo / "guide.md")
    with pytest.raises(ValueError, match="destination"):
        mod.sync_from_repos(roots={"uCore": repo}, mirror_root=mirror)
    assert (repo / "guide.md").read_text() == "# Old\n"


def test_refresh_rejects_source_symlink_outside_repository_docs(tmp_path):
    repo, mirror = _setup_repo(tmp_path)
    private = tmp_path / "private.md"
    private.write_text("Private material")
    (repo / "linked.md").symlink_to(private)
    with pytest.raises(ValueError, match="source escapes"):
        mod.sync_from_repos(roots={"uCore": repo}, mirror_root=mirror)
    assert not (mirror / "uCore" / "linked.md").exists()


@pytest.mark.asyncio
async def test_writeback_api_does_not_parse_or_dispatch_content(monkeypatch):
    from unittest.mock import AsyncMock

    from aiohttp.test_utils import make_mocked_request

    from app.surfaces.documentation_api import handle_docs_mirror_push
    request = make_mocked_request("POST", "/api/docs/mirror/push")
    request.json = AsyncMock(side_effect=AssertionError("Read a retired mutation payload"))
    response = await handle_docs_mirror_push(request)
    assert response.status == 410
    request.json.assert_not_called()


def test_diff_rejects_tampered_provenance_paths(tmp_path):
    import json
    repo, mirror = _setup_repo(tmp_path)
    index_path = mirror / '_mirror.json'
    index = json.loads(index_path.read_text())
    index['entries'][0]['mirrored_path'] = '../outside.md'
    index_path.write_text(json.dumps(index))
    with pytest.raises(ValueError, match='entry escapes'):
        mod.diff_entry('uCore', 'guide.md', mirror_root=mirror, roots={'uCore': repo})
