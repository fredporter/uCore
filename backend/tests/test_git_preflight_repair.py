"""Git probe failures must provide actionable preflight repairs."""
from unittest.mock import AsyncMock, patch

import pytest

from app.api.extensions_api import _evaluate_capability
from app.tools.git_tool import GitTool


@pytest.mark.asyncio
async def test_xcode_licence_error_reaches_repair_card():
    process = AsyncMock()
    process.returncode = 69
    process.communicate.return_value = (
        b"", b"You have not agreed to the Xcode license agreements."
    )
    with patch("app.tools.git_tool.asyncio.create_subprocess_exec", return_value=process):
        result = await GitTool().check()
    assert not result.installed
    assert "Xcode license" in result.error
    with patch("app.api.extensions_api.check_tool", return_value=result):
        payload, status = await _evaluate_capability(
            "workflow.run", {"workflow.run": {"tools": ["git"]}}, "test"
        )
    assert status == 412
    assert payload["repair"][0]["details"] == result.error
    assert "sudo xcodebuild -license" in payload["repair"][0]["action"]


@pytest.mark.asyncio
async def test_working_git_clears_repair():
    process = AsyncMock()
    process.returncode = 0
    process.communicate.return_value = (b"git version 2.50.0", b"")
    with patch("app.tools.git_tool.asyncio.create_subprocess_exec", return_value=process):
        result = await GitTool().check()
    with patch("app.api.extensions_api.check_tool", return_value=result):
        payload, status = await _evaluate_capability(
            "workflow.run", {"workflow.run": {"tools": ["git"]}}, "test"
        )
    assert status == 200
    assert payload["repair"] == []
