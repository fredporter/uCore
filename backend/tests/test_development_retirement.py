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
