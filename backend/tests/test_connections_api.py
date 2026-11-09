from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from aiohttp import web

from app.api import connections_api as api
from app.services.connections.store import CollectionStore


def request(method="GET", body=None, headers=None, connection=None):
    async def read():
        return body or {}

    return SimpleNamespace(
        method=method,
        headers=headers or {},
        json=read,
        body_exists=body is not None,
        query={},
        match_info={"connection": connection, "action": "sync"},
    )


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(api.platform, "system", lambda: "Darwin")
    result = CollectionStore(tmp_path / "connections.sqlite3")
    monkeypatch.setattr(api, "CollectionStore", lambda: result)
    monkeypatch.setattr(
        api, "get_full_identity", lambda: {"authenticated": True, "active_profile_id": "alice"}
    )
    monkeypatch.setattr(api.SyncEngine, "refresh_tasks", lambda *a: None)
    monkeypatch.setattr(api.SyncEngine, "refresh_notes", lambda *a: None)
    return result


@pytest.mark.asyncio
async def test_api_cannot_select_another_profile(store):
    other = store.configure("bob", "apple", {"collections": {}})
    store.save("bob", "contacts", {"title": "Private"})
    response = await api.state(request(headers={"X-Udos-Profile": "bob"}))
    assert json.loads(response.text)["connections"] == []
    with pytest.raises(web.HTTPNotFound):
        await api.action(request("POST", {}, connection=other["id"]))
    assert json.loads((await api.records(request())).text)["records"] == []


@pytest.mark.asyncio
async def test_origin_and_auth_are_checked(store, monkeypatch):
    with pytest.raises(web.HTTPForbidden):
        await api.configure(request("POST", {}, headers={"Origin": "https://untrusted.example"}))
    monkeypatch.setattr(api, "get_full_identity", lambda: {"authenticated": False})
    with pytest.raises(web.HTTPUnauthorized):
        await api.state(request())


@pytest.mark.asyncio
async def test_creation_starts_disabled_without_native_access(store):
    response = await api.configure(
        request(
            "POST", {"provider": "apple", "config": {"collections": {"contacts": {"lists": []}}}}
        )
    )
    result = json.loads(response.text)
    assert result["config"]["enabled"] is False
    assert await api.SyncEngine(store).sync("alice", result["id"]) == {"state": "disabled"}


@pytest.mark.asyncio
async def test_setup_draft_resume_and_finish_are_profile_owned(store, tmp_path, monkeypatch):
    import app.services.identity as identity
    from app.identity.story_store import IdentityStoryStore

    monkeypatch.setenv("UDOS_IDENTITY_DATA_FILE", str(tmp_path / "stories.json"))
    updates = []
    monkeypatch.setattr(
        identity, "update_profile", lambda owner, **data: updates.append((owner, data))
    )
    body = {
        "display_name": "Alice",
        "step": 3,
        "answers": {
            "city": "Perth",
            "host_timezone": "Australia/Perth",
            "theme_mode": "light",
            "font_size": "18",
        },
    }
    await api.setup(request("POST", body))
    draft = store.setup("alice")
    stories = IdentityStoryStore(profile_id="alice")
    assert stories.get_story(draft["story_id"])["responses"]["font_size"] == "18"
    assert stories.get_variables() == {}
    assert updates == []
    assert IdentityStoryStore(profile_id="bob").get_story(draft["story_id"]) is None
    await api.setup(request("POST", {**body, "completed": True, "step": 6}))
    assert updates == [("alice", {"name": "Alice"})]
    assert stories.get_variables()["timezone_source"] == "host"
    assert "theme_mode" not in stories.get_variables()
    assert store.setup("alice")["completed"] is True


@pytest.mark.asyncio
async def test_setup_rejects_invalid_draft_without_writes(store):
    for body in [
        {"step": "bad"},
        {"answers": {"host_timezone": "not/a-zone"}},
        {"answers": {"font_size": "90"}},
        {"self_contact": "someone-else"},
    ]:
        with pytest.raises(web.HTTPBadRequest):
            await api.setup(request("POST", body))
    assert store.setup("alice") == {"completed": False, "display_name": ""}


@pytest.mark.asyncio
async def test_oauth_settings_never_returns_credentials(store, monkeypatch):
    from app.services.connections import google_auth as auth

    secrets = {}
    vault = SimpleNamespace(
        get=lambda key: secrets.get(key),
        set=lambda key, value: secrets.update({key: value}),
        save=lambda: None,
    )
    monkeypatch.setattr(auth, "get_store", lambda: vault)
    monkeypatch.setattr(auth, "AESGCM", object())
    for key in [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_OAUTH_CLIENT_SECRET",
    ]:
        monkeypatch.delenv(key, raising=False)
    body = {"client_id": "example.apps.googleusercontent.com", "client_secret": "private-value"}
    response = await api.oauth_settings(request("POST", body))
    result = json.loads(response.text)
    assert result["configured"] and result["client_secret_present"]
    assert body["client_id"] not in response.text
    assert body["client_secret"] not in response.text
    await api.oauth_settings(request("POST", {**body, "client_secret": ""}))
    assert secrets["GOOGLE_OAUTH_CLIENT_SECRET"] == "private-value"
    with pytest.raises(web.HTTPBadRequest):
        await api.oauth_settings(
            request("POST", {**body, "client_id": "different.apps.googleusercontent.com"})
        )
    monkeypatch.setattr(auth, "AESGCM", None)
    with pytest.raises(web.HTTPBadRequest):
        await api.oauth_settings(request("POST", body))
    with pytest.raises(web.HTTPForbidden):
        await api.oauth_settings(
            request("POST", body, headers={"Origin": "https://elsewhere.example"})
        )
