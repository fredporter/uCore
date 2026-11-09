"""The production route map must never dispatch retired development mutations."""
import ast
import json
from pathlib import Path

import pytest
from aiohttp.test_utils import make_mocked_request

from app.api.developer_api import handle_retired_development


@pytest.mark.asyncio
async def test_retired_response_has_no_runtime_or_repository_side_effects(monkeypatch):
    from app.api import developer_api
    def unexpected():
        raise AssertionError('Retired route initialised an execution manager')
    monkeypatch.setattr(developer_api, 'get_developer_command_manager', unexpected)
    monkeypatch.setattr(developer_api, 'get_developer_operation_manager', unexpected)
    response = await handle_retired_development(make_mocked_request('POST', '/api/developer/start'))
    assert response.status == 410
    assert json.loads(response.text)['error'] == 'internal_development_retired'


def test_production_bindings_retire_writes_and_keep_reads_and_cancellation():
    from app.api import routes
    tree = ast.parse(Path(routes.__file__).read_text())
    bindings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr.startswith('add_') and len(node.args) >= 2:
            path, handler = node.args[:2]
            if isinstance(path, ast.Constant) and isinstance(path.value, str) and path.value.startswith('/api/developer/') and isinstance(handler, ast.Name):
                bindings[(node.func.attr, path.value)] = handler.id
    mutations = {key: value for key, value in bindings.items() if key[0] in {'add_post', 'add_put', 'add_delete'} and not key[1].endswith(('/cancel', '/stop'))}
    assert len(mutations) == 15
    assert set(mutations.values()) == {'handle_retired_development'}
    assert bindings[('add_get', '/api/developer/chat/stream')] == 'handle_retired_development'
    assert bindings[('add_get', '/api/developer/repos')] == 'handle_list_repos'
    assert bindings[('add_get', '/api/developer/operations')] == 'handle_list_developer_operations'
    assert bindings[('add_post', '/api/developer/operations/{operation_id}/cancel')] == 'handle_cancel_developer_operation'
    assert bindings[('add_post', '/api/developer/stop')] == 'handle_stop_developer'


@pytest.mark.asyncio
async def test_retired_status_and_capabilities_do_not_start_managers(monkeypatch):
    from app.api import developer_api
    def unexpected():
        raise AssertionError("Status started a development runtime")
    monkeypatch.setattr(developer_api, 'get_developer_operation_manager', unexpected)
    request = make_mocked_request('GET', '/api/developer/status')
    status = json.loads((await developer_api.handle_developer_status(request)).text)
    capabilities = json.loads((await developer_api.handle_developer_operation_capabilities(request)).text)
    assert status['active'] is False
    assert status['status'] == 'retired'
    assert capabilities['available'] is False
    assert capabilities['actions'] == []


@pytest.mark.asyncio
async def test_dev_mode_reads_and_enable_attempts_never_load_saved_state(monkeypatch):
    from unittest.mock import AsyncMock

    from app.api import dev_layer_api
    def unexpected():
        raise AssertionError('Loaded persisted development state')
    monkeypatch.setattr(dev_layer_api, 'get_dev_layer', unexpected)
    request = make_mocked_request('PUT', '/api/dev-layer/state')
    request.json = AsyncMock(return_value={'mode': 'on'})
    assert (await dev_layer_api.handle_set_dev_state(request)).status == 410
    assert (await dev_layer_api.handle_toggle_dev_state(request)).status == 410
    state = json.loads((await dev_layer_api.handle_get_dev_state(request)).text)
    hud = json.loads((await dev_layer_api.handle_get_dev_hud(request)).text)
    assert state['mode'] == 'off'
    assert state['available'] is False
    assert hud['quick_actions'] == []


@pytest.mark.asyncio
async def test_explicit_dev_shutdown_keeps_cancellation_available(monkeypatch):
    from unittest.mock import AsyncMock, Mock

    from app.api import dev_layer_api
    layer = Mock()
    stop = AsyncMock()
    monkeypatch.setattr(dev_layer_api, 'get_dev_layer', lambda: layer)
    monkeypatch.setattr(dev_layer_api, 'stop_developer_work', stop)
    request = make_mocked_request('PUT', '/api/dev-layer/state')
    request.json = AsyncMock(return_value={'mode': 'off'})
    response = await dev_layer_api.handle_set_dev_state(request)
    assert response.status == 200
    assert layer.mode is dev_layer_api.DevMode.OFF
    layer._save.assert_called_once()
    stop.assert_awaited_once()
