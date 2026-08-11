"""Integration tests for BrowserUI Research and Binder APIs."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.research_queue import ResearchQueue


class TestResearchQueue:
    """Test the research job queue."""

    @pytest.fixture(autouse=True)
    def _patch_db(self, monkeypatch, tmp_path):
        """Redirect DB_PATH to a temp directory."""
        db = tmp_path / "research_queue.db"
        monkeypatch.setattr(
            "app.services.research_queue.DB_PATH", db
        )

    async def test_enqueue_and_status(self):
        q = ResearchQueue()
        jid = await q.enqueue(url="https://example.com", binder="test", tags=["#test"])
        assert jid is not None
        status = await q.status(jid)
        assert status["state"] == "pending"
        assert status["url"] == "https://example.com"
        assert status["binder"] == "test"
        assert status["tags"] == ["#test"]

    async def test_list_jobs(self):
        q = ResearchQueue()
        await q.enqueue(url="https://a.com", binder="b1")
        await q.enqueue(url="https://b.com", binder="b2")
        jobs = await q.list_jobs()
        assert len(jobs) == 2

        jobs_b1 = await q.list_jobs(binder="b1")
        assert len(jobs_b1) == 1

    async def test_update_state(self):
        q = ResearchQueue()
        jid = await q.enqueue(url="https://x.com", binder="x")
        await q.update_state(jid, "scraping", progress=50)
        s = await q.status(jid)
        assert s["state"] == "scraping"
        assert s["progress"] == 50

    async def test_process_next_empty_queue(self):
        q = ResearchQueue()
        result = await q.process_next()
        assert result is None
