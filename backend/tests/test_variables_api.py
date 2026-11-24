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
    assert saved["$USERID"]

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


@pytest.mark.asyncio
async def test_registry_enforces_three_to_eight_character_caps_names(tmp_path, monkeypatch):
    variables = tmp_path / "variables.json"
    install_meta = tmp_path / "install_meta.json"
    monkeypatch.setattr(variables_api, "_VARIABLE_STORE_FILE", variables)
    monkeypatch.setattr(variables_api, "_INSTALL_META_FILE", install_meta)

    # Every registry key (minus the `$`) is 3–8 chars, CAPS A-Z0-9.
    for key in variables_api._REGISTRY:
        name = key.lstrip("$")
        assert 3 <= len(name) <= 8, key
        assert name[0].isalpha() and name.isupper() and name.isalnum(), key

    # An eight-character identity variable is writable.
    request = SimpleNamespace(json=AsyncMock(return_value={"$USERNAME": "Sovereign"}))
    response = await variables_api.handle_update_user_variables(request)
    assert response.status == 200
    assert json.loads(variables.read_text())["$USERNAME"] == "Sovereign"

    # A genuinely unknown variable name is rejected.
    request.json.return_value = {"$USERNAM": "x"}
    assert (await variables_api.handle_update_user_variables(request)).status == 400

    # A non-registry variable name is rejected.
    request.json.return_value = {"$NOTAVARX": "x"}
    assert (await variables_api.handle_update_user_variables(request)).status == 400

    # An old padded name writes to the shorter canonical ID.
    request.json.return_value = {"$ROLEXXXX": "Wizard"}
    response = await variables_api.handle_update_user_variables(request)
    assert response.status == 200
    assert json.loads(variables.read_text())["$ROLE"] == "Wizard"


@pytest.mark.asyncio
async def test_role_variable_validation_accepts_selector_values(tmp_path, monkeypatch):
    variables = tmp_path / "variables.json"
    install_meta = tmp_path / "install_meta.json"
    monkeypatch.setattr(variables_api, "_VARIABLE_STORE_FILE", variables)
    monkeypatch.setattr(variables_api, "_INSTALL_META_FILE", install_meta)

    for role in ("Wizard", "Sorceror", "Knight", "Crypt", "Drone", "Tomb", "Ghost"):
        request = SimpleNamespace(json=AsyncMock(return_value={"$ROLE": role}))
        response = await variables_api.handle_update_user_variables(request)
        assert response.status == 200
        assert json.loads(variables.read_text())["$ROLE"] == role


@pytest.mark.asyncio
async def test_canonical_variables_migrate_legacy_state(tmp_path, monkeypatch):
    variables = tmp_path / "variables.json"
    install_meta = tmp_path / "install_meta.json"
    monkeypatch.setattr(variables_api, "_VARIABLE_STORE_FILE", variables)
    monkeypatch.setattr(variables_api, "_INSTALL_META_FILE", install_meta)
    legacy = {"uid": "existing-id", "$ROLEXXX": "Wizard", "username": "Alice",
              "local_model": "existing-model", "custom_setting": "preserved"}
    variables.write_text(json.dumps(legacy))
    install_meta.write_text(json.dumps({"install_date": "2025-01-01T00:00:00+00:00"}))

    response = await variables_api.handle_get_user_variables(None)
    user = json.loads(response.text)
    assert user["$ROLE"] == "Wizard"
    assert user["$BLANK01"] == ""
    assert user["$USERID"] == "existing-id"
    assert json.loads(variables.read_text()) == legacy

    request = SimpleNamespace(json=AsyncMock(return_value={"$USERNAME": "Bob"}))
    response = await variables_api.handle_update_user_variables(request)
    assert response.status == 200
    saved = json.loads(variables.read_text())
    assert saved == {"$USERID": "existing-id", "$ROLE": "Wizard", "$USERNAME": "Bob",
                     "$INSTALLD": "2025-01-01", "local_model": "existing-model",
                     "custom_setting": "preserved"}
    assert json.loads(response.text)["variables"]["username"] == "Bob"

    for invalid in ({"$SYSVER": "spoofed"}, {"$USERID": "replacement"},
                    {"username": "Alice", "$USERNAME": "Bob"}, {"$USERNAME\n": "Bob"}, {"$AB": "x"}, {"$ABCDEFGHI": "x"}):
        request.json.return_value = invalid
        assert (await variables_api.handle_update_user_variables(request)).status == 400
        assert json.loads(variables.read_text()) == saved
