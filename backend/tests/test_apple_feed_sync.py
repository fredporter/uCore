from __future__ import annotations

import platform
from pathlib import Path

import pytest

from app.services.apple_feed_sync import AppleFeedSync
from app.services.feed_store import FeedServer


@pytest.mark.asyncio
async def test_sync_deduplicates_external_items(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr("app.services.apple_feed_sync.shutil.which", lambda _: "/usr/bin/osascript")
    feed = FeedServer(str(tmp_path / "activity.db"))
    def runner(_script: str):
        return [
            {"external_id": "mail-1", "title": "Project note", "content": "Next action"}
        ]
    sync = AppleFeedSync(feed, runner=runner)

    first = await sync.sync("mail")
    second = await sync.sync("mail")
    rows = await feed.query_feed(source="mail")

    assert first["ok"] is True
    assert second["ok"] is True
    assert len(rows) == 1
    assert rows[0]["external_id"] == "mail-1"


@pytest.mark.asyncio
async def test_planned_whatsapp_adapter_does_not_run(tmp_path: Path):
    feed = FeedServer(str(tmp_path / "activity.db"))
    sync = AppleFeedSync(feed, runner=lambda _: (_ for _ in ()).throw(AssertionError()))

    result = await sync.sync("whatsapp")

    assert result["ok"] is False
    assert result["state"] == "planned"
