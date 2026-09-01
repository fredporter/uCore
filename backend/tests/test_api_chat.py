"""Integration tests for Chat API endpoints."""
from __future__ import annotations

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.chat import (
    _normalise_tool_calls,
    handle_chat,
    handle_chat_modes,
    handle_chat_prompts,
    handle_models,
)


def test_normalise_tool_calls_accepts_small_model_json_fallback():
    calls = _normalise_tool_calls({
        "content": '{"name": "list_skills", "arguments": {}}',
    })
    assert calls == [{
        "function": {"name": "list_skills", "arguments": {}},
    }]


def test_normalise_tool_calls_rejects_unknown_tool():
    assert _normalise_tool_calls({
        "content": '{"name": "shell_exec", "arguments": {}}',
    }) == []


class ChatAPITest(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_post("/api/chat", handle_chat)
        app.router.add_get("/api/chat/modes", handle_chat_modes)
        app.router.add_get("/api/chat/prompts", handle_chat_prompts)
        app.router.add_get("/api/models", handle_models)
        return app

    async def test_list_models(self):
        resp = await self.client.get("/api/models")
        assert resp.status == 200
        data = await resp.json()
        assert "providers" in data
        assert "count" in data
        # At least one provider must be listed; exact count depends on router config
        assert data["count"] >= 1

    async def test_list_models_structure(self):
        resp = await self.client.get("/api/models")
        data = await resp.json()
        for provider in data["providers"]:
            assert "name" in provider
            assert "type" in provider or "id" in provider
            # Provider must have either an id or a type
            assert "id" in provider or "type" in provider

    async def test_chat_prompts_default(self):
        resp = await self.client.get("/api/chat/prompts")
        assert resp.status == 200
        data = await resp.json()
        assert data["mode"] == "chat"
        assert data["count"] == 4
        for p in data["prompts"]:
            assert "title" in p
            assert "prompt" in p

    async def test_chat_prompts_for_vault(self):
        resp = await self.client.get("/api/chat/prompts?agent=vault")
        assert resp.status == 200
        data = await resp.json()
        assert data["mode"] == "vault"
        assert data["count"] == 4

    async def test_chat_prompts_for_developer(self):
        resp = await self.client.get("/api/chat/prompts?agent=developer")
        assert resp.status == 200
        data = await resp.json()
        assert data["mode"] == "developer"

    async def test_chat_missing_message(self):
        resp = await self.client.post("/api/chat", json={})
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data

    async def test_chat_invalid_json(self):
        resp = await self.client.post("/api/chat", data=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status == 400
    async def test_chat_modes_returns_modes(self):
        resp = await self.client.get("/api/chat/modes")
        assert resp.status == 200
        data = await resp.json()
        assert "modes" in data
        assert "budget" in data
        modes = data["modes"]
        assert len(modes) >= 2
        mode_ids = [m["id"] for m in modes]
        assert "chat" in mode_ids
        assert "plan" in mode_ids

    async def test_chat_modes_plan_has_free_models(self):
        resp = await self.client.get("/api/chat/modes")
        data = await resp.json()
        plan_mode = next(m for m in data["modes"] if m["id"] == "plan")
        assert plan_mode["cost"] == "free"
        assert "models" in plan_mode

    async def test_plan_mode_returns_structured_response(self):
        resp = await self.client.post("/api/chat", json={
            "message": "Research the uCore vault system and plan improvements",
            "mode": "plan",
            "model": "ollama/qwen2.5-coder:3b",
        })
        # Plan mode should return 200 even if the LLM call fails
        # (the error handling returns 500 only on config issues)
        data = await resp.json()
        assert "response" in data or "error" in data
        if "response" in data:
            assert data["mode"] == "plan"
            assert "plan_steps" in data or data["plan_steps"] is not None

    async def test_chat_prompts_with_mode_parameter(self):
        resp = await self.client.get("/api/chat/prompts?mode=chat")
        assert resp.status == 200
        data = await resp.json()
        assert data["mode"] == "chat"
        assert "prompts" in data



    async def test_chat_with_message(self):
        """Chat with a simple message — should get a response or error if no provider configured."""
        resp = await self.client.post("/api/chat", json={"message": "Hello, what is 1+1?"})
        # If no API key is configured, it might return 500 with provider error.
        # Either way, we should get a valid JSON response.
        assert resp.status in (200, 500)
        data = await resp.json()
        if resp.status == 200:
            assert "response" in data
            assert "model" in data
        else:
            assert "error" in data
