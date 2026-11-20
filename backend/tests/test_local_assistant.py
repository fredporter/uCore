import json

import httpx
import pytest

from app.services import local_assistant as service


def test_local_only_model_and_endpoint_boundaries(monkeypatch):
    for value in ['https://example.com', 'http://127.0.0.1:11434/other', 'http://user:password@localhost:11434']:
        monkeypatch.setattr(service.settings, 'ollama_base_url', value)
        with pytest.raises(ValueError):
            service.local_url()
    assert not service.is_local_chat({'name': 'nomic-embed-text:latest'})
    assert not service.is_local_chat({'name': 'model:latest', 'remote_host': 'https://example.com'})
    for value in ['../bad', 'https://example.com/model', 'model:cloud', 'model;command']:
        with pytest.raises(ValueError):
            service.validate_model_reference(value)
    service.validate_model_reference('example:4b')


@pytest.mark.asyncio
async def test_roundtable_is_sequential_local_preview_without_saving(monkeypatch):
    requests = []
    def respond(request):
        requests.append(request)
        if request.url.path == '/api/tags':
            return httpx.Response(200, json={'models': [{'name': 'local:small', 'size': 123}]})
        data = json.loads(request.content)
        assert data['stream'] is False
        assert data['options']['num_predict'] == 512
        assert 'tools' not in data
        return httpx.Response(200, json={'message': {'content': f'Draft {len(requests)}'}})
    original = httpx.AsyncClient
    monkeypatch.setattr(service.httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))
    state = await service.inventory()
    assert state['library'] == []
    assert state['models'][0]['name'] == 'local:small'
    result = await service.roundtable('Plan a garden', 'Source: my notes', 'local:small')
    assert [r['role'] for r in result['outputs']] == ['research', 'create', 'review']
    assert result['saved'] is False
    assert result['knowledge_layer'] == 'personal-proposal'
    assert len([r for r in requests if r.url.path == '/api/chat']) == 3
    with pytest.raises(ValueError):
        await service.roundtable('Goal', '', 'uninstalled:small')


@pytest.mark.asyncio
async def test_chat_uses_installed_local_model_and_conversation(monkeypatch):
    requests = []

    def respond(request):
        requests.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [
                {"name": "remote:cloud"}, {"name": "local:small"},
            ]})
        return httpx.Response(200, json={"message": {"content": "A local reply"}})

    original = httpx.AsyncClient
    monkeypatch.setattr(service.httpx, "AsyncClient", lambda **kwargs: original(
        transport=httpx.MockTransport(respond), **kwargs,
    ))
    turns = [{"role": "user", "content": "Help me plan a garden."}]
    assert await service.chat(turns) == {"model": "local:small", "content": "A local reply"}
    payload = json.loads(requests[-1].content)
    assert payload["messages"][1:] == turns
    assert payload["model"] == "local:small"
    assert "tools" not in payload
    with pytest.raises(ValueError, match="installed"):
        await service.chat(turns, "remote:cloud")
    assert sum(request.url.path == "/api/chat" for request in requests) == 1


@pytest.mark.asyncio
async def test_model_snack_updates_explicit_installed_batch(monkeypatch):
    from app.services import local_assistant as service

    models = [
        {"name": "code:small", "local_chat": True, "coding_focused": True},
        {"name": "general:small", "local_chat": True, "coding_focused": False},
    ]

    async def inventory():
        return {"models": models}

    pulled = []

    async def pull_events(name):
        pulled.append(name)
        yield '{"status":"success"}'

    monkeypatch.setattr(service, "inventory", inventory)
    monkeypatch.setattr(service, "pull_events", pull_events)
    assert service.select_model(models, "creative") == "general:small"
    assert service.select_model(models, "ucode") == "code:small"
    events = [event async for event in service.maintain_models("update", ["code:small", "general:small"])]
    assert pulled == ["code:small", "general:small"]
    assert [event["model"] for event in events] == pulled
    with pytest.raises(ValueError, match="Only installed"):
        await anext(service.maintain_models("update", ["uninstalled:small"]))


@pytest.mark.asyncio
async def test_offline_chat_and_settings_follow_active_profile(monkeypatch, tmp_path):
    from aiohttp import web
    from aiohttp.test_utils import make_mocked_request

    from app.api import local_assistant_api as api
    from app.services import assistant_profile

    owner = "first"
    role = "user"
    monkeypatch.setenv("UDOS_IDENTITY_DATA_FILE", str(tmp_path / "profile.json"))
    monkeypatch.setattr(api, "get_full_identity", lambda: {
        "authenticated": True, "active_profile_id": owner, "active_profile": {"role": role},
    })

    def request(payload):
        req = make_mocked_request("POST", "/api/assistant/chat")
        async def read():
            return payload
        req.json = read
        return req

    async def no_model(*args, **kwargs):
        pytest.fail("Offline input attempted to use Ollama")

    monkeypatch.setattr(service, "chat", no_model)
    replies = []

    def offline_reply(message, *, verbose):
        replies.append((message, verbose))
        return f"Offline reply: {message}"

    monkeypatch.setattr(api, "_resolve_callable", lambda _path: offline_reply)
    settings = {"verbose": True, "chat_mode": "offline", "model": ""}
    await api.update_settings(request(settings))
    chat = {"messages": [{"role": "user", "content": "calculate 6 * 7"}]}
    response = await api.chat(request(chat))
    assert json.loads(response.text)["content"] == "Offline reply: calculate 6 * 7"

    owner = "second"
    role = "guest"
    response = await api.chat(request(chat))
    assert json.loads(response.text)["content"] == "Offline reply: calculate 6 * 7"
    assert replies == [("calculate 6 * 7", True), ("calculate 6 * 7", False)]
    with pytest.raises(web.HTTPForbidden):
        await api.update_settings(request({**settings, "chat_mode": "ollama"}))
    with pytest.raises(web.HTTPForbidden):
        await api.pull(request({"model": "example:small", "confirm": True}))
    assert assistant_profile.preferences("first") == settings
