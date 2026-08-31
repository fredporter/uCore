from pathlib import Path

import pytest

from app.services.feed_store import FeedServer


@pytest.mark.asyncio
async def test_query_feed_can_select_unprocessed_items(tmp_path: Path):
    feed = FeedServer(str(tmp_path / "activity.db"))
    first = await feed.ingest_activity(source="mail", type="message", title="First")
    await feed.ingest_activity(source="mail", type="message", title="Second")
    await feed.link_task_to_activity("todo-first", first["id"])

    pending = await feed.query_feed(processed=False)
    completed = await feed.query_feed(processed=True)

    assert [row["title"] for row in pending] == ["Second"]
    assert [row["title"] for row in completed] == ["First"]
