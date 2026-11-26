"""Tests for Backup skill."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_backup_creates_file(tmp_path: Path, monkeypatch):
    """Backup skill copies the database to the destination."""
    from app.skills.builtin.backup import BackupData

    # Create a fake database to back up
    fake_db = tmp_path / "ucore.db"
    fake_db.write_text("fake sqlite content", encoding="utf-8")

    # Patch get_db_path inside the BackupData.run method
    import app.core.database as db_mod
    monkeypatch.setattr(db_mod, "get_db_path", lambda: str(fake_db))

    dest = tmp_path / "backups"
    dest.mkdir()

    skill = BackupData()
    result = await skill.run(destination=str(dest))
    assert result["success"] is True
    assert result["count"] > 0
    assert any("ucore-backup" in f["file"] for f in result["files"])


@pytest.mark.asyncio
async def test_backup_full(tmp_path: Path, monkeypatch):
    """Full backup runs without error."""
    from app.skills.builtin.backup import BackupData

    dest = tmp_path / "backups"
    dest.mkdir()

    skill = BackupData()
    result = await skill.run(type="full", destination=str(dest), retention_days=999)
    assert result["success"] is True
    assert result["type"] == "full"


@pytest.mark.asyncio
async def test_backup_database_only(tmp_path: Path, monkeypatch):
    """Database-only backup runs without error."""
    from app.skills.builtin.backup import BackupData

    fake_db = tmp_path / "ucore.db"
    fake_db.write_text("fake sqlite content", encoding="utf-8")

    import app.core.database as db_mod
    monkeypatch.setattr(db_mod, "get_db_path", lambda: str(fake_db))

    dest = tmp_path / "backups"
    dest.mkdir()

    skill = BackupData()
    result = await skill.run(type="database", destination=str(dest))
    assert result["success"] is True
    assert result["type"] == "database"


@pytest.mark.asyncio
async def test_backup_reports_missing_components_honestly(tmp_path: Path, monkeypatch):
    """A backup that finds nothing must not report success."""
    import app.core.database as db_mod
    import app.skills.builtin.backup as mod
    from app.core.settings import settings

    monkeypatch.setattr(db_mod, "get_db_path", lambda: None)
    monkeypatch.setattr(mod, "readable_wisdom_path", lambda: tmp_path / "missing-wisdom.md")
    monkeypatch.setattr(settings, "secrets_dir", tmp_path / "missing-secrets")
    monkeypatch.setattr(settings, "config_dir", tmp_path / "missing-config")
    monkeypatch.setattr(settings, "udos_root", tmp_path)

    dest = tmp_path / "backups"
    dest.mkdir()

    result = await mod.BackupData().run(type="full", destination=str(dest))

    assert result["success"] is False
    assert result["count"] == 0
    assert "No backup components" in result["error"]


@pytest.mark.asyncio
async def test_retention_only_prunes_its_own_artifacts(tmp_path: Path, monkeypatch):
    """Expired cleanup must not remove files another owner placed in the destination."""
    import os
    import time

    import app.core.database as db_mod
    import app.skills.builtin.backup as mod

    monkeypatch.setattr(db_mod, "get_db_path", lambda: None)

    dest = tmp_path / "backups"
    dest.mkdir()
    expired = dest / "ucore-backup-20200101-000000.db"
    expired.write_text("old", encoding="utf-8")
    foreign_file = dest / "canon-export.tar.gz"
    foreign_file.write_text("keep", encoding="utf-8")
    foreign_dir = dest / "canon-c02-2026-11-24"
    foreign_dir.mkdir()
    (foreign_dir / "keep.txt").write_text("keep", encoding="utf-8")

    stale = time.time() - 40 * 86400
    for target in (expired, foreign_file, foreign_dir):
        os.utime(target, (stale, stale))

    result = await mod.BackupData().run(
        type="database",
        destination=str(dest),
        retention_days=14,
    )

    assert not expired.exists()
    assert foreign_file.exists()
    assert (foreign_dir / "keep.txt").exists()
    assert result["old_backups_removed"] >= 1
