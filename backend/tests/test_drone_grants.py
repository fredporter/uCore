from types import SimpleNamespace

import pytest

from app.services import identity
from app.services.connections import drone, google_auth, providers
from app.services.connections.store import CollectionStore


@pytest.fixture
def gateway(tmp_path, monkeypatch):
    owner = SimpleNamespace(id="owner", role="wizard")
    knight = SimpleNamespace(id="knight", role="knight")
    profiles = SimpleNamespace(profiles=[owner, knight])
    monkeypatch.setattr(identity, "load_identity", lambda: profiles)
    monkeypatch.setattr(drone, "load_identity", lambda: profiles)
    store = CollectionStore(tmp_path / "connections.sqlite3")
    connection = store.configure(owner.id, "google", {
        "collections": {"tasks": {"lists": ["approved/list", "private"], "direction": "both", "target": "private"}}
    })
    credential = {
        "account_subject": "approved-account", "access_token": "fixture-secret",
        "scope": google_auth.SCOPES["tasks"], "expires_at": float("inf"),
    }
    monkeypatch.setattr(google_auth, "token_data", lambda connection: credential.copy())
    monkeypatch.setattr(drone, "token_data", lambda connection: credential.copy())
    calls = []

    def fake_google(url, **options):
        calls.append((url, options))
        if "/users/@me/lists/" in url:
            return {"title": "Approved list"}
        return {"items": [{"id": "task-1", "title": "Shared task"}]}

    monkeypatch.setattr(providers, "request_json", fake_google)
    grant = drone.enroll(store, owner.id, recipient=knight.id, connection_id=connection["id"],
                         list_id="approved/list", duration=900)
    return store, owner, knight, grant, connection, credential, calls


def test_preview_uses_one_list_and_never_exposes_credentials(gateway):
    store, owner, knight, grant, connection, credential, calls = gateway
    with pytest.raises(PermissionError):
        drone.preview(store, "another-profile", grant)
    assert not calls
    result = drone.preview(store, knight.id, grant)
    assert result["provenance"]["grant"] == grant
    assert result["records"][0]["data"]["title"] == "Shared task"
    assert "fixture-secret" not in str(result)
    assert len(calls) == 2
    assert all("approved%2Flist" in url and options["method"] == "GET" and
               options["follow_redirects"] is False for url, options in calls)
    with pytest.raises(PermissionError, match="last minute"):
        drone.preview(store, knight.id, grant)


@pytest.mark.parametrize("reason", ["expiry", "revoke", "owner-role", "account", "scope", "disconnect"])
def test_grant_changes_block_provider_calls(gateway, reason):
    store, owner, knight, grant, connection, credential, calls = gateway
    if reason == "expiry":
        with store.db() as db:
            db.execute("UPDATE drone_grants SET expires=0 WHERE id=?", (grant,))
    elif reason == "revoke":
        drone.revoke(store, owner.id, grant)
    elif reason == "owner-role":
        owner.role = "knight"
    elif reason == "account":
        credential["account_subject"] = "different-account"
    elif reason == "scope":
        store.configure(owner.id, "google", {"collections": {"tasks": {"lists": ["private"]}}}, connection["id"])
    else:
        drone.revoke_connection(store, owner.id, connection["id"])
    with pytest.raises(PermissionError):
        drone.preview(store, knight.id, grant)
    assert calls == []


def test_revocation_between_requests_stops_preview(gateway, monkeypatch):
    store, owner, knight, grant, connection, credential, calls = gateway
    original = providers.request_json

    def revoke_after_first_request(url, **options):
        response = original(url, **options)
        drone.revoke(store, owner.id, grant)
        return response

    monkeypatch.setattr(providers, "request_json", revoke_after_first_request)
    with pytest.raises(PermissionError, match="revoked"):
        drone.preview(store, knight.id, grant)
    assert len(calls) == 1


def test_knight_cannot_enroll_or_revoke(gateway):
    store, owner, knight, grant, connection, credential, calls = gateway
    with pytest.raises(PermissionError):
        drone.enroll(store, knight.id, recipient=owner.id, connection_id=connection["id"],
                     list_id="approved/list", duration=900)
    with pytest.raises(PermissionError):
        drone.revoke(store, knight.id, grant)
