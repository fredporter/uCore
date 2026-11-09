from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import pytest

from app.services.connections.apple import AppleAdapter
from app.services.connections.google_auth import _PENDING, finish, start
from app.services.connections.providers import GoogleAdapter


def test_apple_uses_declared_calendar_dictionary_and_bounded_runner():
    scripts = []

    def runner(script):
        scripts.append(script)
        return []

    adapter = AppleAdapter(runner)
    adapter.discover({"config": {"collections": {"calendar": {}}}})
    adapter.pull({}, "calendar", {"lists": ["cal-1"]})
    assert "calendarIdentifier()" in scripts[0]
    assert "stampDate()" in scripts[1]
    assert "1000" in scripts[1]


def test_apple_rejects_lossy_multi_colour_mail_write():
    adapter = AppleAdapter(lambda _: pytest.fail("No native execution expected"))
    with pytest.raises(ValueError, match="one colour"):
        adapter.push(
            {},
            "mail",
            {"target": "inbox"},
            {"id": "a" * 32, "data": {"flags": ["red", "blue"]}},
            {"remote": "mail:1", "version": ""},
        )


def test_apple_read_strips_own_sync_marker_without_exposing_it_as_content():
    adapter = AppleAdapter(
        lambda _: [
            {
                "id": "1",
                "data": {"title": "Note", "body": "Note\nBody\n\nuCore record: " + "a" * 32},
            }
        ]
    )
    assert adapter.pull({}, "notes", {"lists": ["folder"]})[0]["data"]["body"] == "Body"


def test_google_mail_maps_colour_labels_without_removing_other_labels(monkeypatch):
    adapter = GoogleAdapter()
    requests = []

    def api(connection, url, **kwargs):
        requests.append((url, kwargs))
        return {"id": "message", "historyId": "new"}

    monkeypatch.setattr(adapter, "api", api)
    adapter.push(
        {},
        "mail",
        {"target": "INBOX", "flag_labels": {"red": "Label_1", "blue": "Label_2", "grey": ""}},
        {
            "id": "a" * 32,
            "data": {"title": "Message", "flags": ["blue"], "starred": True, "read": False},
        },
        {"remote": "mail:message", "version": "old"},
    )
    payload = requests[0][1]["data"]
    assert set(payload["addLabelIds"]) == {"Label_2", "STARRED", "UNREAD"}
    assert payload["removeLabelIds"] == ["Label_1"]
    assert "INBOX" not in payload["removeLabelIds"]


def test_google_task_reuses_marked_creation_after_lost_ack(monkeypatch):
    adapter = GoogleAdapter()
    monkeypatch.setattr(
        adapter,
        "pages",
        lambda *a: [{"id": "existing", "etag": "e", "notes": "uCore record: " + "a" * 32}],
    )
    requests = []

    def api(connection, url, **kw):
        requests.append((url, kw))
        return {"id": "existing", "etag": "new"}

    monkeypatch.setattr(adapter, "api", api)
    result = adapter.push(
        {},
        "tasks",
        {"target": "list"},
        {"id": "a" * 32, "data": {"title": "Task", "body": "Note", "status": "completed"}},
        None,
    )
    assert requests[0][1]["method"] == "PATCH"
    assert requests[0][1]["version"] == "e"
    assert result["id"] == "list/existing"


def test_google_sign_in_state_pkce_and_scope_choice(monkeypatch):
    import app.services.connections.google_auth as auth

    monkeypatch.setattr(auth, "AESGCM", object())
    monkeypatch.setattr(auth, "client", lambda: {"client_id": "configured", "client_secret": ""})
    connection = {"id": "c", "profile": "alice", "config": {"collections": {"tasks": {}}}}
    url = start(connection, "http://127.0.0.1:8484/api/connections/google/callback")
    query = parse_qs(urlparse(url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert "tasks" in query["scope"][0]
    assert "contacts" not in query["scope"][0]
    state = query["state"][0]
    assert _PENDING[state]["connection"]["profile"] == "alice"
    with pytest.raises(ValueError):
        finish("unknown", "code")
    _PENDING[state]["expires"] = 0
    with pytest.raises(ValueError, match="expired"):
        finish(state, "code")
    assert state not in _PENDING


def test_native_workflow_status_remains_local_detail():
    adapter = GoogleAdapter()
    assert adapter.representation(
        "tasks", {"title": "Task", "status": "blocked", "flags": ["blue"]}
    ) == {"title": "Task", "status": "todo"}
    assert json.loads(json.dumps({"flags": ["blue"]}))["flags"] == ["blue"]
