from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.api import feed_api
from app.services.feed_store import FeedServer
from app.services.spool_reader import read_spool
from app.services.spool_writer import write_spool_batch


class StubRequest:
    def __init__(self, json_data):
        self._json_data = json_data

    async def json(self):
        return self._json_data


@pytest.mark.asyncio
async def test_rss_ingestion_endpoint_success(monkeypatch, tmp_path):
    db_path = tmp_path / "pods" / "activity.db"
    server = FeedServer(str(db_path))
    monkeypatch.setattr(feed_api, "_get_feed_server", lambda: server)

    payload = {
        "guid": "urn:uds:fixture:generic:rss-oakhaven-01",
        "title": "Whispers of Oakhaven: The Hidden Canopy",
        "topic": "fictional-places",
        "url": "https://lore.example.org/oakhaven/canopy",
        "summary": "Dispatches from the ancient hollows of Oakhaven Sanctuary.",
        "provenance": {
            "origin_url": "https://lore.example.org/oakhaven/canopy",
            "ingested_at": "2026-11-19T12:00:00Z",
            "revision": "rev-1",
            "author": "Archivist Eldon"
        }
    }

    req = StubRequest(payload)
    resp = await feed_api.handle_feed_rss(req)
    assert resp.status == 200
    data = json.loads(resp.text)
    assert data["ok"] is True
    assert "activity_id" in data
    assert isinstance(data["activity_id"], int)


@pytest.mark.asyncio
async def test_feed_workflow_proposal_and_spool(monkeypatch, tmp_path):
    db_path = tmp_path / "pods" / "activity.db"
    server = FeedServer(str(db_path))
    monkeypatch.setattr(feed_api, "_get_feed_server", lambda: server)

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.spool_writer.LOG_DIR", logs_dir)

    payload = {
        "guid": "urn:uds:fixture:generic:rss-oakhaven-alert",
        "title": "Alert: Canopy anomaly detected in Oakhaven",
        "summary": "High priority anomaly in sector 7.",
        "importance": 0.9,
        "topic": "alerts"
    }

    req = StubRequest(payload)
    resp = await feed_api.handle_feed_rss(req)
    assert resp.status == 200
    data = json.loads(resp.text)
    assert data["ok"] is True

    spool_file = logs_dir / "spool.log"
    assert spool_file.exists()
    content = spool_file.read_text(encoding="utf-8")
    assert "RSS item ingested" in content or "feed" in content or "uflow" in content


@pytest.mark.asyncio
async def test_rss_ingestion_invalid_payload():
    req = StubRequest({"guid": "invalid"})
    resp = await feed_api.handle_feed_rss(req)
    assert resp.status == 400
    data = json.loads(resp.text)
    assert "error" in data


@pytest.mark.asyncio
async def test_review_rss_and_explicit_promotion_return_written_receipts(monkeypatch, tmp_path):
    server = FeedServer(str(tmp_path / "activity.db"))
    monkeypatch.setattr(feed_api, "_get_feed_server", lambda: server)
    monkeypatch.setattr("app.services.spool_writer.LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr("app.flow.task_store.default_tasker_dir", lambda: tmp_path / "tasks")
    monkeypatch.setattr("app.services.identity.get_full_identity", lambda: {"active_profile_id": "default"})

    payload = {
        "guid": "urn:example:review",
        "title": "Ready for review",
        "summary": "Saved RSS item",
        "review_only": True,
    }
    first = json.loads((await feed_api.handle_feed_rss(StubRequest(payload))).text)
    repeated = json.loads((await feed_api.handle_feed_rss(StubRequest(payload))).text)
    assert first["activity_id"] == repeated["activity_id"]
    assert not list((tmp_path / "tasks").glob("*/*.md"))

    request = StubRequest({"activity_id": first["activity_id"]})
    promotion = json.loads((await feed_api.handle_feed_promote(request)).text)
    retry = json.loads((await feed_api.handle_feed_promote(request)).text)
    assert retry["existing"] is True
    assert retry["task_id"] == promotion["task_id"]
    refreshed = json.loads((await feed_api.handle_feed_rss(StubRequest(payload))).text)
    assert refreshed["processed"] is True
    assert len(list((tmp_path / "tasks").glob("*/*.md"))) == 1
    write_spool_batch([{"module": "test", "message": "A later event"}])
    for result in [first, repeated, promotion, retry, refreshed]:
        entries = read_spool(tmp_path / "logs", search=result["spool_receipt"])
        assert any(entry.source == "spool.log" for entry in entries)


@pytest.mark.asyncio
async def test_rule_rejection_case(monkeypatch, tmp_path):
    db_path = tmp_path / "pods" / "activity.db"
    server = FeedServer(str(db_path))
    monkeypatch.setattr(feed_api, "_get_feed_server", lambda: server)

    payload = {
        "guid": "urn:uds:fixture:generic:rss-noise",
        "title": "Ordinary daily weather update",
        "summary": "Nothing to report.",
        "importance": 0.1
    }

    req = StubRequest(payload)
    resp = await feed_api.handle_feed_rss(req)
    assert resp.status == 200
    data = json.loads(resp.text)
    assert data["ok"] is True
    assert data["proposals"] == []
    assert data["promoted_task"] is None
