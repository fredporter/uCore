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
