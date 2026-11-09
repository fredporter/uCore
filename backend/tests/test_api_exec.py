"""Generic shell strings never reach a subprocess through the retired API."""
from unittest.mock import AsyncMock

import pytest
from aiohttp.test_utils import make_mocked_request

from app.api.exec import handle_exec


@pytest.mark.asyncio
@pytest.mark.parametrize('payload', [{'command': 'echo hello'}, {'command': 'which python3'}, {}, ['unexpected']])
async def test_exec_always_reports_retired_without_reading_or_running_commands(payload, monkeypatch):
    import asyncio
    shell = AsyncMock(side_effect=AssertionError('Shell started'))
    monkeypatch.setattr(asyncio, 'create_subprocess_shell', shell)
    request = make_mocked_request('POST', '/api/exec')
    request.json = AsyncMock(return_value=payload)
    response = await handle_exec(request)
    assert response.status == 410
    assert 'generic_execution_retired' in response.text
    request.json.assert_not_called()
    shell.assert_not_called()
