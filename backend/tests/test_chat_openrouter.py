"""Verify cloud stream fallback using a fixture provider."""
import asyncio
import json

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api import chat_openrouter
from app.services import provider_router


@pytest.mark.asyncio
@pytest.mark.parametrize("partial", [False, True])
async def test_cloud_failure_preserves_partial_response(monkeypatch, partial):
    calls = []

    class Router:
        def list_models(self):
            return [{"id": "example/format-model", "provider": "openrouter"}]

        async def chat_stream(self, *, messages, model=None, provider):
            calls.append((provider, model, messages[-1]["content"]))
            if provider == "ollama":
                yield "Local answer"
                return
            if partial:
                yield "Cloud draft"
            raise RuntimeError("HTTP 429")

    monkeypatch.setattr(provider_router, "ProviderRouter", Router)
    monkeypatch.setattr(chat_openrouter, "active_assistant_profile", lambda *_: None)
    app = web.Application()
    app.router.add_post("/api/chat/stream", chat_openrouter.handle_chat_stream)
    async with TestClient(TestServer(app)) as client:
        async with asyncio.timeout(5):
            response = await client.post(
                "/api/chat/stream", json={"message": "Format these notes", "model": "example/format-model"}
            )
            assert response.status == 200
            frames = [line.removeprefix("data: ") for line in (await response.text()).splitlines() if line]
    assert frames.pop() == "[DONE]"
    events = [json.loads(frame) for frame in frames]
    assert calls[0] == ("openrouter", "example/format-model", "Format these notes")
    if partial:
        assert len(calls) == 1
        assert events[0] == {"token": "Cloud draft"}
        assert "error" in events[1]
    else:
        assert calls[1] == ("ollama", None, "Format these notes")
        assert "system" in events[0]
        assert events[1] == {"token": "Local answer"}
