from pathlib import Path

from app.api import chat_history_api


def test_chat_history_roundtrip(tmp_path: Path, monkeypatch):
    target = tmp_path / "chat.json"
    monkeypatch.setattr(chat_history_api, "_history_file", lambda: target)
    conversations = [{"id": "one", "title": "Test", "messages": []}]
    chat_history_api._write_history(conversations)
    assert chat_history_api._read_history() == conversations


def test_chat_history_is_bounded(tmp_path: Path, monkeypatch):
    target = tmp_path / "chat.json"
    monkeypatch.setattr(chat_history_api, "_history_file", lambda: target)
    chat_history_api._write_history([{"id": str(index)} for index in range(110)])
    stored = chat_history_api._read_history()
    assert len(stored) == 100
    assert stored[0]["id"] == "10"


async def _post_history(payload, monkeypatch, tmp_path):
    from aiohttp import web
    from aiohttp.test_utils import TestClient, TestServer

    monkeypatch.setattr(chat_history_api, "_history_file", lambda: tmp_path / "chat.json")
    monkeypatch.setattr(chat_history_api, "_MAX_BYTES", 100)
    app = web.Application()
    chat_history_api.register_chat_history_routes(app)
    async with TestClient(TestServer(app)) as client:
        async def chunks():
            for chunk in payload:
                yield chunk
        response = await client.post("/api/chat/history", data=chunks())
        return response.status


def test_chunked_history_limit(monkeypatch, tmp_path):
    import asyncio

    status = asyncio.run(_post_history([b'{"conversations": [', b' ' * 101, b']}'], monkeypatch, tmp_path))
    assert status == 413
    assert not (tmp_path / "chat.json").exists()


def test_chunked_history_valid_body(monkeypatch, tmp_path):
    import asyncio

    status = asyncio.run(_post_history([b'{"conversations":', b' []}'], monkeypatch, tmp_path))
    assert status == 200
    assert (tmp_path / "chat.json").read_text() == "[]"
