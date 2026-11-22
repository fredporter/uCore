import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api import variables_api


@pytest.mark.asyncio
async def test_local_variables_preserve_unreadable_state(tmp_path, monkeypatch):
    variables = tmp_path / "variables.json"
    install_meta = tmp_path / "install_meta.json"
    monkeypatch.setattr(variables_api, "_VARIABLE_STORE_FILE", variables)
    monkeypatch.setattr(variables_api, "_INSTALL_META_FILE", install_meta)
    request = SimpleNamespace(json=AsyncMock(return_value={"openrouter_model": "owner/model"}))

    response = await variables_api.handle_update_user_variables(request)
    assert response.status == 200
    saved = json.loads(variables.read_text())
    assert saved["openrouter_model"] == "owner/model"
    assert saved["uid"]

    request.json.return_value = {"openrouter_model": ["owner/model"]}
    assert (await variables_api.handle_update_user_variables(request)).status == 400
    assert json.loads(variables.read_text()) == saved

    variables.write_text("[]")
    request.json.return_value = {"openrouter_model": "owner/model"}
    assert (await variables_api.handle_update_user_variables(request)).status == 503
    assert (await variables_api.handle_get_user_variables(request)).status == 503
    assert variables.read_text() == "[]"
    assert (await variables_api.handle_get_install_variables(request)).status == 200
    assert install_meta.exists()
