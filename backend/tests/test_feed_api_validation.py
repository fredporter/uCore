import json
from types import SimpleNamespace

import pytest

from app.api import feed_api


class StubFeedServer:
    def __init__(self):
        self.query_kwargs = None

    async def query_feed(self, **kwargs):
        self.query_kwargs = kwargs
        return []


@pytest.mark.asyncio
async def test_query_rejects_invalid_numeric_parameters():
    request = SimpleNamespace(query={"limit": "many"})

    response = await feed_api.handle_feed_query(request)

    assert response.status == 400
    assert json.loads(response.text)["error"] == "limit and importance_min must be numeric"


@pytest.mark.asyncio
async def test_query_passes_pending_filter(monkeypatch: pytest.MonkeyPatch):
    server = StubFeedServer()
    monkeypatch.setattr(feed_api, "_get_feed_server", lambda: server)
    request = SimpleNamespace(query={"processed": "false", "limit": "999"})

    response = await feed_api.handle_feed_query(request)

    assert response.status == 200
    assert server.query_kwargs == {
        "source": None,
        "since": None,
        "limit": 500,
        "importance_min": 0.0,
        "processed": False,
    }


@pytest.mark.asyncio
async def test_query_rejects_ambiguous_processed_filter():
    request = SimpleNamespace(query={"processed": "pending"})

    response = await feed_api.handle_feed_query(request)

    assert response.status == 400
    assert json.loads(response.text)["error"] == "processed must be true or false"


@pytest.mark.asyncio
async def test_ingest_rejects_out_of_range_importance():
    class Request:
        async def json(self):
            return {"source": "mail", "type": "message", "importance": 2}

    response = await feed_api.handle_feed_ingest(Request())

    assert response.status == 400
    assert json.loads(response.text)["error"] == "importance must be between 0 and 1"
