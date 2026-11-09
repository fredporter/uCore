"""Executable UI authorization and error transport contracts."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.test_utils import make_mocked_request

from app.api.executables_api import handle_run_executable


@pytest.mark.asyncio
async def test_executable_requires_explicit_confirmation():
    request = make_mocked_request(
        "POST", "/api/executables/write/run", match_info={"exe_id": "write"}
    )
    request.json = AsyncMock(return_value={})
    with (
        patch(
            "app.api.executables_api.get_executable", return_value={"requires_confirmation": True}
        ),
        patch("app.api.executables_api.run_executable", new_callable=AsyncMock) as run,
    ):
        response = await handle_run_executable(request)
    assert response.status == 409
    run.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirmed_executable_propagates_failure():
    request = make_mocked_request(
        "POST",
        "/api/executables/write/run",
        headers={"x-ucore-confirm": "true"},
        match_info={"exe_id": "write"},
    )
    request.json = AsyncMock(return_value={})
    with (
        patch(
            "app.api.executables_api.get_executable", return_value={"requires_confirmation": True}
        ),
        patch(
            "app.api.executables_api.run_executable",
            new_callable=AsyncMock,
            return_value={"success": False, "error": "Failed"},
        ) as run,
    ):
        response = await handle_run_executable(request)
    assert response.status == 422
    assert json.loads(response.text)["error"] == "Failed"
    run.assert_awaited_once_with("write", action=None, execution_authorized=True)
