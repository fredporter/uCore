from __future__ import annotations

import asyncio
import copy

import pytest

from app.services.connections.engine import SyncEngine
from app.services.connections.reconcile import (
    combine_records,
    duplicate_candidates,
    merge_fields,
    selected,
)
from app.services.connections.store import CollectionStore


class Adapter:
    writable = {"contacts": {"title", "body", "emails", "phones", "starred"}}

    def __init__(self):
        self.rows = [
            {
                "id": "remote-1",
                "version": "1",
                "data": {"title": "Alice", "body": "Original", "emails": ["a@example.com"]},
            }
        ]
        self.writes = []

    def pull(self, *args):
        return copy.deepcopy(self.rows)

    def push(self, connection, kind, scope, record, mapping):
        self.writes.append(copy.deepcopy(record))
        return {
            "id": mapping["remote"].split(":", 1)[1] if mapping else "new-remote",
            "version": "2",
        }


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    store = CollectionStore(tmp_path / "collection.sqlite3")
    adapter = Adapter()
    connection = store.configure(
        "default",
        "google",
        {
            "enabled": True,
            "collections": {
                "contacts": {"lists": ["people/me"], "direction": "both", "target": "people/me"}
            },
        },
    )
    engine = SyncEngine(store, {"google": adapter})
    monkeypatch.setattr(engine, "project_feed", lambda *a: None)
    monkeypatch.setattr(engine, "project", lambda *a, **kw: None)
    monkeypatch.setattr(engine, "refresh_tasks", lambda *a: None)
    monkeypatch.setattr(engine, "refresh_notes", lambda *a: None)
    return store, adapter, connection, engine


def sync(fixture):
    store, adapter, connection, engine = fixture
    return asyncio.run(engine.sync("default", connection["id"]))


def test_repeated_pull_has_stable_identity_and_no_unnecessary_writes(fixture):
    sync(fixture)
    sync(fixture)
    store, adapter, *_ = fixture
    assert len(store.records("default")) == 1
    assert not adapter.writes


def test_independent_edits_merge_but_competing_edits_are_reviewed(fixture):
    sync(fixture)
    store, adapter, connection, engine = fixture
    record = store.records("default")[0]
    store.save("default", "contacts", {**record["data"], "title": "Alice Local"}, record["id"])
    adapter.rows[0]["data"]["body"] = "Remote note"
    result = sync(fixture)
    assert result["pushed"] == 1
    assert adapter.writes[-1]["data"]["body"] == "Remote note"
    assert adapter.writes[-1]["data"]["title"] == "Alice Local"
    # Next remote edit conflicts with a subsequent local edit.
    record = store.records("default")[0]
    store.save("default", "contacts", {**record["data"], "title": "Local Two"}, record["id"])
    adapter.rows[0]["data"]["title"] = "Remote Two"
    count = len(adapter.writes)
    assert sync(fixture)["state"] == "conflict"
    assert len(adapter.writes) == count
    engine.resolve("default", connection["id"], "contacts:remote-1", "combine")
    assert store.records("default")[0]["data"]["alternatives"]["title"] == ["Remote Two"]
    assert not store.conflicts("default")


def test_deselected_remote_records_are_not_pushed(fixture):
    sync(fixture)
    store, adapter, connection, _ = fixture
    record = store.records("default")[0]
    store.save("default", "contacts", {**record["data"], "body": "Local edit"}, record["id"])
    config = connection["config"]
    config["collections"]["contacts"].update(selection="records", records=["other"])
    store.configure("default", "google", config, connection["id"])
    sync(fixture)
    assert not adapter.writes


def test_explicit_sharing_and_profile_isolation(fixture):
    store, adapter, connection, engine = fixture
    local = store.save("default", "contacts", {"title": "Bob", "body": ""})
    store.save(
        "other", "contacts", {"title": "Private", "body": "", "destinations": [connection["id"]]}
    )
    sync(fixture)
    assert not adapter.writes
    store.save(
        "default", "contacts", {**local["data"], "destinations": [connection["id"]]}, local["id"]
    )
    sync(fixture)
    assert [r["data"]["title"] for r in adapter.writes] == ["Bob"]
    assert not store.connection("other", connection["id"])
    with pytest.raises(ValueError):
        store.save("other", "contacts", {"title": "Hijack"}, local["id"])


def test_merge_keeps_replicas_and_alternative_values(fixture):
    store, _, connection, engine = fixture
    sync(fixture)
    first = store.records("default")[0]
    second = store.save(
        "default",
        "contacts",
        {
            "title": "A. Example",
            "emails": ["a@example.com", "other@example.com"],
            "body": "Other note",
        },
    )
    store.acknowledge(connection["id"], "contacts:remote-2", second["id"], second["data"])
    assert duplicate_candidates(store.records("default"))[0]["reason"] == "email"
    merged = engine.merge("default", first["id"], second["id"])
    assert merged["data"]["emails"] == ["a@example.com", "other@example.com"]
    assert merged["data"]["alternatives"]["body"] == ["Other note"]
    assert {r["record"] for r in store.replicas(connection["id"])} == {first["id"]}
    assert store.record("default", second["id"])["data"]["merged_into"] == first["id"]


def test_filters_do_not_equate_vip_flags_and_stars():
    assert not selected({"flags": ["red"]}, {"filter": "vip"}, "1")
    assert not selected({"vip": True}, {"filter": "starred"}, "1")
    assert selected({"starred": True}, {"filter": "starred"}, "1")
    assert not selected({"starred": True}, {"selection": "records", "records": []}, "1")
    merged, collision = merge_fields(
        {"body": "old"}, {"body": "ours", "flags": ["blue"]}, {"body": "old"}
    )
    assert merged["flags"] == ["blue"]
    assert not collision


def test_validation_and_setup_are_profile_owned(tmp_path):
    store = CollectionStore(tmp_path / "collection.sqlite3")
    store.setup("a", {"display_name": "Alice", "completed": True})
    assert store.setup("a")["completed"]
    assert not store.setup("b")["completed"]
    with pytest.raises(ValueError):
        store.configure("a", "apple", {"collections": {"mail": {"filter": "vip"}}})
    with pytest.raises(ValueError):
        store.save("a", "contacts", {"title": "Bad", "flags": ["unknown"]})
    assert combine_records({"body": "left"}, {"body": "right"})["alternatives"]["body"] == ["right"]


def test_failures_keep_records_and_expose_backoff(fixture):
    store, adapter, connection, _ = fixture

    def fail(*args):
        raise RuntimeError("Permission required")

    adapter.pull = fail
    assert sync(fixture)["state"] == "error"
    health = store.connection("default", connection["id"])["health"]
    assert health["failures"] == 1 and health["next_attempt"]
    assert health.get("last_success") is None


def test_uncertain_create_is_not_retried_as_another_creation(fixture):
    store, adapter, connection, _ = fixture
    store.save("default", "contacts", {"title": "New", "destinations": [connection["id"]]})

    def uncertain(*args):
        raise RuntimeError("Network dropped after request")

    adapter.push = uncertain
    assert sync(fixture)["state"] == "error"
    assert len(store.pending_exports("default")) == 1
    assert "uncertain outcome" in sync(fixture)["error"]


def test_task_projection_uses_existing_uflow_record(tmp_path, monkeypatch):
    from app.flow.task_store import write_task_markdown

    monkeypatch.setenv("UFLOW_TASKS_DIR", str(tmp_path / "flow"))
    write_task_markdown(
        title="Local task",
        board="inbox",
        body="Original",
        task="original",
        metadata={"id": "local-task"},
    )
    store = CollectionStore(tmp_path / "collection.sqlite3")
    engine = SyncEngine(store, {})
    engine.refresh_tasks("default")
    record = store.records("default", "tasks")[0]
    changed = store.save(
        "default", "tasks", {**record["data"], "status": "completed"}, record["id"]
    )
    engine.project("default", changed)
    engine.refresh_tasks("default")
    assert store.records("default", "tasks")[0]["data"]["status"] == "completed"
    assert len(list((tmp_path / "flow").glob("*/*.md"))) == 1
    assert store.records("other") == []


def test_explicit_flag_rule_creates_one_linked_task_per_source(fixture):
    store, adapter, connection, _ = fixture
    adapter.rows[0]["data"]["starred"] = True
    config = connection["config"]
    config["collections"]["contacts"]["flag_action"] = "create-task"
    store.configure("default", "google", config, connection["id"])
    assert sync(fixture)["automated_tasks"] == 1
    assert sync(fixture)["automated_tasks"] == 0
    tasks = store.records("default", "tasks")
    assert len(tasks) == 1
    assert tasks[0]["data"]["origin_record"]


def test_feed_promotion_is_idempotent_after_task_rename(tmp_path, monkeypatch):
    from app.api.tasker_api import _update_task_file
    from app.services.feed_workflow import promote_activity_to_task

    monkeypatch.setenv("UFLOW_TASKS_DIR", str(tmp_path / "flow"))
    monkeypatch.setattr(
        "app.services.identity.get_full_identity", lambda: {"active_profile_id": "default"}
    )
    activity = {"id": 42, "title": "Mail follow-up", "source": "mail", "content": "Notes"}
    first = promote_activity_to_task(activity)
    _update_task_file(
        base=tmp_path / "flow",
        task_id=first["task_id"],
        patch={"title": "My edited title", "status": "completed"},
    )
    again = promote_activity_to_task(activity)
    assert again["existing"]
    assert len(list((tmp_path / "flow").glob("*/*.md"))) == 1


def test_readme_documents_are_not_tasks(tmp_path, monkeypatch):
    monkeypatch.setenv("UFLOW_TASKS_DIR", str(tmp_path / "flow"))
    folder = tmp_path / "flow/inbox"
    folder.mkdir(parents=True)
    (folder / "README.md").write_text("# List guide\nThis is documentation")
    store = CollectionStore(tmp_path / "collection.sqlite3")
    artifact = store.save(
        "default", "tasks", {"title": "List guide", "body": "This is documentation"}
    )
    store.acknowledge("uflow:default", "inbox/README.md", artifact["id"], artifact["data"])
    SyncEngine(store, {}).refresh_tasks("default")
    assert store.records("default", "tasks") == []
    assert (folder / "README.md").read_text() == "# List guide\nThis is documentation"


def test_note_projection_preserves_competing_editor_changes(tmp_path, monkeypatch):
    import hashlib

    from app.core.settings import settings

    monkeypatch.setattr(settings, "vault_root", tmp_path / "Vault")
    store = CollectionStore(tmp_path / "collection.sqlite3")
    engine = SyncEngine(store, {})
    record = store.save("default", "notes", {"title": "Note", "body": "Original"})
    engine.project("default", record)
    path = (
        tmp_path
        / "Vault/Connections"
        / hashlib.sha256(b"default").hexdigest()[:10]
        / (record["id"] + ".md")
    )
    path.write_text("# Note\n\nEditor change")
    incoming = store.save(
        "default", "notes", {"title": "Note", "body": "Incoming change"}, record["id"]
    )
    with pytest.raises(ValueError, match="edited"):
        engine.project("default", incoming)
    assert path.read_text() == "# Note\n\nEditor change"
    assert store.record("default", record["id"])["data"]["body"] == "Editor change"


def test_manual_sync_does_not_require_scheduled_polling(fixture):
    store, adapter, connection, engine = fixture
    store.configure(
        "default", "google", {**connection["config"], "enabled": False}, connection["id"]
    )
    assert asyncio.run(engine.sync("default", connection["id"])) == {"state": "disabled"}
    assert store.records("default") == []
    result = asyncio.run(engine.sync("default", connection["id"], manual=True))
    assert result["pulled"] == 1
    assert len(store.records("default")) == 1
    assert store.connection("default", connection["id"])["config"]["enabled"] is False
