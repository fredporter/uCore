import asyncio
import json

import pytest

from app.api import developer_api
from app.services import developer_chat, developer_operations
from app.services.dev_layer import DevMode
from app.services.developer_chat import DeveloperChat
from tests.test_developer_operations import init_repo


@pytest.fixture
def chat(monkeypatch, tmp_path):
    repo = tmp_path / 'demo'
    init_repo(repo)
    layer = type('Layer', (), {'mode': DevMode.ON})()
    monkeypatch.setattr(developer_chat, 'get_dev_layer', lambda: layer)
    monkeypatch.setattr(developer_operations, 'get_dev_layer', lambda: layer)
    monkeypatch.setattr(developer_api.settings, 'udos_root', tmp_path)
    manager = developer_operations.DeveloperOperationManager(tmp_path / 'operations.json')
    monkeypatch.setattr(developer_chat, 'get_developer_operation_manager', lambda: manager)
    service = DeveloperChat(tmp_path / 'conversations.json')
    return service, repo, layer, manager


@pytest.mark.asyncio
async def test_read_scope_and_write_gate(chat):
    service, repo, layer, _ = chat
    record = {'repository': 'demo', 'mode': 'ask'}
    result = await service.execute(record, 'read_file', {'path': 'example.py'})
    assert result['content'] == 'value = 1\n'
    with pytest.raises(PermissionError):
        await service.execute(record, 'propose_changes', {'request': 'write'})
    with pytest.raises(ValueError):
        await service.execute(record, 'read_file', {'path': '../outside.py'})
    layer.mode = DevMode.OFF
    with pytest.raises(PermissionError):
        await service.execute(record, 'list_files', {})
    assert (repo / 'example.py').read_text() == 'value = 1\n'


@pytest.mark.asyncio
async def test_continuity_idempotency_and_scope_lock(chat, monkeypatch):
    service, repo, layer, _ = chat
    async def noop(record):
        record['status'] = 'completed'
        service.save()
    monkeypatch.setattr(service, 'run', noop)
    first = service.submit({'workspace': 'demo', 'mode': 'plan', 'message': 'explain', 'requestId': 'one'})
    await service.tasks[first['id']]
    second = service.submit({'conversationId': first['id'], 'workspace': 'demo', 'mode': 'act', 'message': 'implement', 'requestId': 'two'})
    await service.tasks[first['id']]
    repeat = service.submit({'conversationId': first['id'], 'workspace': 'demo', 'mode': 'act', 'message': 'implement', 'requestId': 'two'})
    assert [m['content'] for m in repeat['messages']] == ['explain', 'implement']
    assert DeveloperChat(service.path).get(first['id'])['messages'] == second['messages']
    init_repo(repo.parent / 'other')
    with pytest.raises(ValueError, match='change repository'):
        service.submit({'conversationId': first['id'], 'workspace': 'other', 'message': 'write'})
    layer.mode = DevMode.OFF
    with pytest.raises(PermissionError):
        service.submit({'workspace': 'demo', 'message': 'hello'})
    await service.delete(first['id'])
    assert not DeveloperChat(service.path).records


@pytest.mark.asyncio
async def test_local_json_tool_envelope_executes_and_provider_error_is_failure(chat, monkeypatch):
    service, _, _, _ = chat
    from app.services.budget_manager import BudgetManager
    from app.services.provider_router import ProviderRouter
    class Budget:
        def can_spend(self, *args, **kwargs): return True
        def record_spend(self, *args, **kwargs): pass
    monkeypatch.setattr(BudgetManager, 'get', lambda: Budget())
    responses = iter([
        {'content': '```json\n{"name":"read_file","arguments":{"path":"example.py"}}\n```'},
        {'content': 'The file defines value as 1.'},
        {'error': 'model unavailable'},
    ])
    async def respond(*args, **kwargs): return next(responses)
    monkeypatch.setattr(ProviderRouter, 'chat', respond)
    first = service.submit({'workspace': 'demo', 'message': 'Explain the file'})
    await service.tasks[first['id']]
    record = service.get(first['id'])
    assert record['status'] == 'completed'
    assert any(e.get('name') == 'read_file' and e.get('result', {}).get('content') == 'value = 1\n' for e in record['events'])
    service.submit({'conversationId': first['id'], 'workspace': 'demo', 'message': 'continue'})
    await service.tasks[first['id']]
    assert record['status'] == 'failed'
    assert 'model unavailable' in record['messages'][-1]['content']


def test_repo_root_rejects_absolute_traversal_and_symlink(chat, tmp_path):
    _, repo, _, _ = chat
    for name in ('..', str(repo), '../demo', '.udos'):
        with pytest.raises((ValueError, FileNotFoundError)):
            developer_api._repo_path(name)
    (tmp_path / 'outside').mkdir()
    (repo.parent / 'escape').symlink_to(tmp_path / 'outside')
    with pytest.raises(ValueError):
        developer_api._repo_path('escape')


def test_restart_marks_inflight_turn_interrupted(chat):
    service, _, _, _ = chat
    service.path.write_text(json.dumps([{'id': 'test', 'status': 'running'}]))
    restored = DeveloperChat(service.path)
    assert restored.get('test')['status'] == 'interrupted'
    assert not restored.tasks


@pytest.mark.asyncio
async def test_stream_has_cors_before_prepare_and_never_submits(chat, monkeypatch):
    from aiohttp import web
    from aiohttp.test_utils import TestClient, TestServer

    from app.api import developer_chat_api
    service, _, _, _ = chat
    service.records['stream-test'] = {
        'id': 'stream-test', 'status': 'completed', 'operations': [],
        'messages': [], 'events': [], 'revision': 1,
    }
    monkeypatch.setattr(developer_chat_api, 'get_developer_chat', lambda: service)
    monkeypatch.setattr(developer_chat_api.settings, 'enable_cors', True)
    app = web.Application()
    developer_chat_api.register(app)
    async with TestClient(TestServer(app)) as client:
        response = await client.get('/api/developer/conversations/stream-test/events')
        assert response.headers['Access-Control-Allow-Origin'] == '*'
        assert response.headers['Content-Type'] == 'text/event-stream'
        line = await response.content.readline()
        assert json.loads(line.removeprefix(b'data: '))['status'] == 'completed'
        response.close()
        assert not service.tasks
