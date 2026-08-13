"""Tests for the VaultSync skill."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_vault_sync_dry_run_reports_roots():
    """Dry run should report vault roots without rebuilding the index."""
    from app.skills.builtin.vault_sync import VaultSync

    result = await VaultSync().run(dry_run=True)
    assert result["success"] is True
    assert result["status"] == "dry-run"
    assert result["sources"]


@pytest.mark.asyncio
async def test_vault_sync_build_index(monkeypatch):
    """Should rebuild the library index and summarize per-source counts."""
    from app.skills.builtin import vault_sync as mod

    monkeypatch.setattr(
        mod.library_index,
        "build_index",
        lambda: {
            "status": "completed",
            "total_indexed": 7,
            "sources": [
                {"source": "user", "files": 5, "status": "ok"},
                {"source": "shared", "files": 2, "status": "ok"},
            ],
        },
    )

    result = await mod.VaultSync().run(summary_only=True)
    assert result["success"] is True
    assert result["status"] == "ok"
    assert result["total_indexed"] == 7
    assert result["sources"][0]["files"] == 5
