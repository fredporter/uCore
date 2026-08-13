from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_spool_prune_rotates_and_prunes(
    tmp_path: Path,
    monkeypatch,
):
    from app.core.settings import settings
    from app.skills.builtin.skill_nuggets_and_spool import SpoolPruneSkill

    monkeypatch.setattr(settings, "logs_dir", tmp_path)

    active = tmp_path / "snackbar.log"
    active.write_text("X" * 32, encoding="utf-8")

    rotated_1 = tmp_path / "snackbar.log.1"
    rotated_1.write_text("old-1", encoding="utf-8")

    rotated_3 = tmp_path / "snackbar.log.3"
    rotated_3.write_text("old-3", encoding="utf-8")

    old_ts = (datetime.now(UTC) - timedelta(days=30)).timestamp()
    rotated_3.touch()
    rotated_3.chmod(0o644)
    import os
    os.utime(rotated_3, (old_ts, old_ts))

    result = await SpoolPruneSkill().run(
        max_bytes=8,
        backup_count=2,
        max_age_days=14,
        archive_completed_tasks=False,
    )

    assert result["success"] is True
    assert result["rotated_logs"] == 1
    assert active.exists()
    assert (tmp_path / "snackbar.log.1").exists()


@pytest.mark.asyncio
async def test_spool_prune_creates_logs_dir(
    tmp_path: Path,
    monkeypatch,
):
    from app.core.settings import settings
    from app.skills.builtin.skill_nuggets_and_spool import SpoolPruneSkill

    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(settings, "logs_dir", logs_dir)

    result = await SpoolPruneSkill().run(max_bytes=1024, archive_completed_tasks=False)

    assert result["success"] is True
    assert logs_dir.exists()
    assert result["rotated_logs"] == 0
