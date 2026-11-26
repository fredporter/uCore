"""Both intake entry points converge on an existing Binder."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api import user_workflow
from app.flow import binder_engine
from app.services.doclang_bridge import extract_frontmatter
from app.services.research_queue import ResearchQueue


@pytest.mark.asyncio
async def test_existing_binder_intake_and_local_retry(tmp_path, monkeypatch):
    vault = tmp_path / "Vault"
    folder = vault / "Binders" / "fieldwork"
    folder.mkdir(parents=True)
    (folder / "binder.json").write_text('{"id":"fieldwork"}')
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", vault / "Binders")
    monkeypatch.setattr(user_workflow, "VAULT_LAYERS", [
        {"id": "user", "path": str(vault), "permissions": "read_write"},
    ])
    article = "---\nuid: original-map\ntags: [navigation]\n---\n\n# Map\n"
    request = SimpleNamespace(
        body_exists=True,
        json=AsyncMock(return_value={
            "content": article, "filename": "map.md",
            "binder": "fieldwork", "require_existing_binder": True,
        }),
    )
    imported = await user_workflow.handle_user_workflow_import_markdown(request)
    assert imported.status == 200
    front, _ = extract_frontmatter((folder / "docs" / "map.md").read_text())
    assert front["uid"] == "original-map"
    assert front["tags"] == ["navigation"]
    assert front["intake"]["payload_sha256"] == hashlib.sha256(article.encode()).hexdigest()

    retry = await user_workflow.handle_user_workflow_import_markdown(request)
    assert retry.status == 200
    assert json.loads(retry.text)["duplicate"] is True
    assert json.loads(retry.text)["bytes_written"] == 0
    request.json.return_value["content"] = "# Different document"
    assert (await user_workflow.handle_user_workflow_import_markdown(request)).status == 409

    job = SimpleNamespace(
        id="capture", url="https://example.org/source", binder="fieldwork", tags=[],
    )
    ResearchQueue._save_document(job, "Field Guide", "", "Summary", payload="Original page")
    web, _ = extract_frontmatter((folder / "docs" / "Field-Guide-capture.md").read_text())
    assert web["intake"].keys() == front["intake"].keys()
    assert web["intake"]["source"] == job.url
    assert web["intake"]["payload_sha256"] == hashlib.sha256(b"Original page").hexdigest()

    original_digest = json.loads(imported.text)["sha256"]
    request.json.return_value.update(
        expected_sha256=original_digest,
        content=article.replace("original-map", "different-uid"),
    )
    assert (await user_workflow.handle_user_workflow_import_markdown(request)).status == 409

    request.json.return_value["content"] = article + "\nFollow the [evidence](evidence.md).\n"
    revision = await user_workflow.handle_user_workflow_import_markdown(request)
    assert revision.status == 200
    revised_path = folder / "docs" / "map.md"
    revised_bytes = revised_path.read_bytes()
    assert json.loads(revision.text)["sha256"] == hashlib.sha256(revised_bytes).hexdigest()
    revised_front, revised_body = extract_frontmatter(revised_bytes.decode())
    assert revised_front["uid"] == "original-map"
    assert revised_front["tags"] == ["navigation"]
    assert "[evidence](evidence.md)" in revised_body

    request.json.return_value["content"] = article + "\nA stale edit.\n"
    assert (await user_workflow.handle_user_workflow_import_markdown(request)).status == 409
    assert revised_path.read_bytes() == revised_bytes


@pytest.mark.asyncio
async def test_saved_feed_retry_and_revision(tmp_path, monkeypatch):
    codec = pytest.importorskip("udos_publishing.src.feed_codec")
    vault = tmp_path / "Vault"
    folder = vault / "Binders" / "fieldwork"
    folder.mkdir(parents=True)
    (folder / "binder.json").write_text('{"id":"fieldwork"}')
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", vault / "Binders")
    monkeypatch.setattr(user_workflow, "VAULT_LAYERS", [
        {"id": "user", "path": str(vault), "permissions": "read_write"},
    ])
    item = {
        "id": "urn:source:map-1", "title": "Map", "content_text": "Original",
        "url": "https://example.org/map", "tags": ["navigation"],
    }
    body = {
        "source_format": "feed", "binder": "fieldwork",
        "feed_source": "https://example.org/feed.json",
    }
    request = SimpleNamespace(body_exists=True, json=AsyncMock(return_value=body))

    async def submit():
        body["content"] = json.dumps({"version": codec.JSON_FEED, "title": "Fieldwork", "items": [item]})
        return await user_workflow.handle_user_workflow_import_markdown(request)

    response = await submit()
    assert response.status == 200
    retry = await submit()
    assert json.loads(retry.text)["items"][0]["duplicate"] is True
    item["content_text"] = "Publisher edit"
    assert (await submit()).status == 200

    records = [extract_frontmatter(path.read_text()) for path in (folder / "docs").glob("*.md")]
    assert len(records) == 2
    assert {content.strip() for _, content in records} == {"Original", "Publisher edit"}
    assert len({front["uid"] for front, _ in records}) == 1
    assert len({front["source_revision"] for front, _ in records}) == 2
    assert all(front["intake"]["source"] == body["feed_source"] for front, _ in records)
    assert all(front["intake"]["source_kind"] == "feed" for front, _ in records)

    body["vault_layer"] = "public"
    assert (await submit()).status == 400


def test_user_seed_uses_runtime_binder_and_preserves_existing_work(tmp_path, monkeypatch):
    vault = tmp_path / "Vault"
    monkeypatch.setattr(user_workflow.settings, "vault_root", vault)
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", vault / "Binders")

    (vault / "binders" / "active" / "Sandbox").mkdir(parents=True)
    first = user_workflow._seed_user_vault_docs()
    binder = binder_engine.get_binder("Sandbox")
    assert binder["metadata"]["id"] == "Sandbox"
    docs = binder_engine.get_binder_documents_dir("Sandbox")
    welcome = docs / "welcome-to-ucode.md"
    assert first["created_count"] == 3
    welcome.write_text("Personal edits")
    notebook = docs / "working-note.md"
    notebook_bytes = b"---\nuid: sandbox-notebook-1\ntags: [pilot]\n---\n\nPersonal notebook edits.\n"
    notebook.write_bytes(notebook_bytes)

    legacy = vault / "binders" / "active" / "Sandbox" / "docs" / "welcome-to-ucode.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("Legacy edits")
    second = user_workflow._seed_user_vault_docs()
    assert second["created_count"] == 0
    assert second["legacy_review"][0]["status"] == "conflict"
    assert welcome.read_text() == "Personal edits"
    assert notebook.read_bytes() == notebook_bytes
    assert any(item["filename"] == notebook.name for item in binder_engine.get_binder("Sandbox")["documents"])
    assert legacy.read_text() == "Legacy edits"

    welcome.unlink()
    third = user_workflow._seed_user_vault_docs()
    assert third["legacy_review"][0]["status"] == "move_candidate"
    assert not welcome.exists()

    variant = docs / "WELCOME-TO-UCODE.md"
    variant.write_text("Case variant edits")
    fourth = user_workflow._seed_user_vault_docs()
    assert fourth["created_count"] == 0
    assert fourth["legacy_review"][0]["status"] == "conflict"
    assert str(variant) in fourth["existing"]
    assert variant.read_text() == "Case variant edits"
    assert legacy.read_text() == "Legacy edits"
    assert [entry.name for entry in docs.iterdir() if entry.name.casefold() == welcome.name] == [variant.name]


@pytest.mark.asyncio
async def test_activity_capture_uses_profile_and_existing_binder(tmp_path, monkeypatch):
    from app.api import connections_api, feed_api
    from app.services.feed_store import FeedServer

    vault = tmp_path / "Vault"
    binder = vault / "Binders" / "fieldwork"
    binder.mkdir(parents=True)
    (binder / "binder.json").write_text('{"id":"fieldwork"}')
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", vault / "Binders")
    monkeypatch.setattr(user_workflow, "VAULT_LAYERS", [
        {"id": "user", "path": str(vault), "permissions": "read_write"},
    ])
    feed = FeedServer(str(tmp_path / "activity.db"))
    try:
        activity = await feed.ingest_activity(
            source="research", type="article", title="Map", content="Source notes",
            url="https://example.org/map", external_id="map-1",
        )
        monkeypatch.setattr(connections_api, "profile", lambda request: "test-profile")

        def profile_feed(owner):
            assert owner == "test-profile"
            return feed

        monkeypatch.setattr(feed_api, "_get_feed_server", profile_feed)
        body = {"activity_id": activity["id"], "binder": "fieldwork"}
        request = SimpleNamespace(json=AsyncMock(return_value=body))
        saved = await feed_api.handle_feed_send_to_binder(request)
        assert saved.status == 200
        path = json.loads(saved.text)["path"]
        document, content = extract_frontmatter((binder / "docs" / path.split("/")[-1]).read_text())
        assert content.strip() == "Source notes"
        assert document["intake"]["source_kind"] == "feed"
        assert document["feed_entry_id"] == "map-1"
        assert document["source_url"] == "https://example.org/map"
        duplicate = await feed_api.handle_feed_send_to_binder(request)
        assert json.loads(duplicate.text)["duplicate"] is True
        assert len(await feed.query_feed(processed=False)) == 1

        body["binder"] = "missing"
        assert (await feed_api.handle_feed_send_to_binder(request)).status == 404
    finally:
        feed.close()


@pytest.mark.asyncio
async def test_binder_intake_check_reports_provenance_without_editing(tmp_path, monkeypatch):
    from app.api import binder_api, connections_api
    from app.services.markdown_import_pipeline import render_intake_markdown

    docs = tmp_path / "Binders" / "fieldwork" / "docs"
    docs.mkdir(parents=True)
    (docs.parent / "binder.json").write_text('{"id":"fieldwork"}')
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", tmp_path)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", tmp_path / "Binders")
    monkeypatch.setattr(connections_api, "profile", lambda request: "test-profile")
    capture = render_intake_markdown(
        "# Field notes", {}, source="local-feed", source_kind="feed",
        captured_at="2026-11-14T00:00:00+00:00", payload="source",
    )
    originals = {
        "capture.md": capture,
        "manual.md": "# Handwritten note",
        "invalid.md": capture.replace("schema_version: 1", "schema_version: true"),
    }
    for name, content in originals.items():
        (docs / name).write_text(content)
    (docs / "other.md").symlink_to(docs / "capture.md")
    request = SimpleNamespace(match_info={"binder_id": "fieldwork"})
    response = await binder_api.handle_binder_intake_check(request)
    assert response.status == 200
    rows = {row["filename"]: row for row in json.loads(response.text)["documents"]}
    assert {name: row["status"] for name, row in rows.items()} == {
        "capture.md": "complete", "manual.md": "untracked", "invalid.md": "invalid",
    }
    assert rows["invalid.md"]["issues"]
    assert all((docs / name).read_text() == content for name, content in originals.items())


@pytest.mark.asyncio
async def test_sandbox_mission_feed_and_linked_notebook(tmp_path, monkeypatch):
    from app.api import binder_api, feed_api
    from app.api.tasker_api import _parse_markdown_task
    from app.flow import workflow_api
    from app.services import workflow_manager
    from app.services.feed_store import FeedServer

    vault = tmp_path / "Vault"
    binder = vault / "Binders" / "Sandbox"
    binder.mkdir(parents=True)
    (binder / "binder.json").write_text('{"id":"Sandbox","title":"Sandbox"}')
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", binder.parent)
    monkeypatch.setattr(user_workflow, "VAULT_LAYERS", [
        {"id": "user", "path": str(vault), "permissions": "read_write"},
    ])
    monkeypatch.setattr(workflow_manager, "settings", SimpleNamespace(data_dir=tmp_path))
    monkeypatch.setattr(
        "app.services.identity.get_full_identity", lambda: {"active_profile_id": "pilot"},
    )
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("UFLOW_TASKS_DIR", str(tasks))
    feed = FeedServer(str(tmp_path / "feed.db"))
    monkeypatch.setattr(feed_api, "_get_feed_server", lambda: feed)
    manager = workflow_manager.WorkflowManager()
    mission = manager.create_mission("pilot", "Review notebook evidence", "Sandbox")
    activity = await feed.ingest_activity(
        source="pilot", type="note", title="Review the evidence", content="Synthetic intake",
    )
    request = SimpleNamespace(json=AsyncMock(return_value={
        "activity_id": activity["id"], "binder": "Sandbox", "mission": mission["id"],
    }))
    with monkeypatch.context() as other_profile:
        other_profile.setattr(
            "app.services.identity.get_full_identity",
            lambda: {"active_profile_id": "other-profile"},
        )
        assert (await feed_api.handle_feed_promote(request)).status == 400
        assert not list(tasks.glob("*/*.md"))

    first = await feed_api.handle_feed_promote(request)
    assert first.status == 200
    promoted = json.loads(first.text)
    task = _parse_markdown_task(next(tasks.glob("*/*.md")))
    assert task["id"] == promoted["task_id"]
    assert task["binder"] == "Sandbox"
    assert task["mission"] == mission["id"]
    assert task["source"] == "feed:pilot"
    assert not await feed.query_feed(processed=False)
    retry = json.loads((await feed_api.handle_feed_promote(request)).text)
    assert retry["task_id"] == task["id"] and retry["existing"]
    assert len(list(tasks.glob("*/*.md"))) == 1

    monkeypatch.setattr(workflow_api, "get_workflow_manager", lambda: manager)
    from app.skills.registry import get_skill

    discovery = get_skill("vault_discovery")
    assert discovery is not None
    monkeypatch.setitem(discovery.run.__func__.__globals__, "VAULT_PATHS", {"user": vault})
    monkeypatch.setitem(discovery.run.__func__.__globals__, "UCORE_PATHS", {})
    manager.create_workflow(
        "notebook-pilot", "Review notebook evidence",
        [{"skill_id": "vault_discovery", "params": {"dry_run": True, "vault_layers": "user"}}],
        owner="pilot",
    )
    response = await workflow_api.handle_run_workflow(
        SimpleNamespace(match_info={"workflow_id": "notebook-pilot"}),
    )
    run = json.loads(response.text)
    assert response.status == 200 and run["status"] == "completed"
    step, = run["steps"]
    assert step["skill_id"] == "vault_discovery" and step["success"]
    assert step["result"]["dry_run"]
    assert step["result"]["vaults"]["user"]["files"] > 0
    queue = await workflow_api.handle_workflow_runs(SimpleNamespace(query={"limit": "20"}))
    assert any(
        row["run_id"] == run["run_id"] and row["status"] == "completed"
        for row in json.loads(queue.text)["runs"]
    )

    pages = {
        "working-note.md": "Review the [evidence](evidence.md).",
        "evidence.md": f"Task ID: `{task['id']}`. Queue run: `{run['run_id']}`. Return to the [working note](working-note.md).",
    }
    for filename, body in pages.items():
        request = SimpleNamespace(body_exists=True, json=AsyncMock(return_value={
            "binder": "Sandbox", "require_existing_binder": True, "filename": filename,
            "content": f"---\nuid: {filename}\ntags: [pilot]\n---\n\n{body}\n",
        }))
        assert (await user_workflow.handle_user_workflow_import_markdown(request)).status == 200
        frontmatter, stored = extract_frontmatter((binder / "docs" / filename).read_text())
        assert frontmatter["uid"] == filename
        assert frontmatter["tags"] == ["pilot"]
        assert body in stored
    assert {item["filename"] for item in binder_engine.get_binder("Sandbox")["documents"]} == set(pages)
    assert manager.list_missions("other-profile") == []

    binder_request = SimpleNamespace(
        match_info={"binder_id": "Sandbox"},
        json=AsyncMock(return_value={"title": "Notebook Pilot"}),
    )
    docs = binder_engine.get_binder_documents_dir("Sandbox")
    original_pages = {name: (docs / name).read_bytes() for name in pages}
    assert (await binder_api.handle_binder_rename(binder_request)).status == 200
    assert binder_engine.get_binder_documents_dir("Sandbox") == docs
    assert (await binder_api.handle_binder_delete(binder_request)).status == 200
    assert not docs.exists()

    trash = vault / "Trash" / "Binders" / "Sandbox"
    assert {name: (trash / "docs" / name).read_bytes() for name in pages} == original_pages
    trash.rename(binder)
    assert {name: (docs / name).read_bytes() for name in pages} == original_pages
    restored = json.loads((await binder_api.handle_binder_get(binder_request)).text)["binder"]
    assert restored["metadata"]["title"] == "Notebook Pilot"
    assert {item["filename"] for item in restored["documents"]} == set(pages)

    from app.api.editor_api import handle_workspace_file
    from app.services import workspace_files

    monkeypatch.setattr(workspace_files, "workspace_root", lambda source: vault if source == "user" else None)
    evidence_path = "/Binders/Sandbox/docs/evidence.md"
    rename_request = SimpleNamespace(
        method="PUT", query={},
        json=AsyncMock(return_value={"path": evidence_path, "name": "review.md"}),
    )
    assert (await handle_workspace_file(rename_request)).status == 200
    assert (docs / "review.md").read_bytes() == original_pages["evidence.md"]
    assert not (docs / "evidence.md").exists()
    assert (docs / "working-note.md").read_bytes() == original_pages["working-note.md"]

    delete_request = SimpleNamespace(
        method="DELETE", query={},
        json=AsyncMock(return_value={"path": "/Binders/Sandbox/docs/review.md"}),
    )
    assert (await handle_workspace_file(delete_request)).status == 200
    remaining = binder_engine.get_binder("Sandbox")["documents"]
    assert {item["filename"] for item in remaining} == {"working-note.md"}
    assert (docs / "working-note.md").read_bytes() == original_pages["working-note.md"]


def test_sandbox_preview_inventories_custom_legacy_content(tmp_path, monkeypatch):
    vault = tmp_path / "Vault"
    monkeypatch.setattr(user_workflow.settings, "vault_root", vault)
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", vault / "Binders")
    (vault / "binders" / "active" / "Sandbox").mkdir(parents=True)
    user_workflow._seed_user_vault_docs()
    target = binder_engine.get_binder_documents_dir("Sandbox").parent
    legacy = vault / "binders" / "active" / "Sandbox"
    cases = {
        "docs/project/new.md": (b"custom", None, "move_candidate"),
        "docs/project/same.md": (b"same", b"same", "retained"),
        "docs/project/edited.md": (b"old", b"new", "conflict"),
        "docs/Case/child.md": (b"legacy", None, "conflict"),
        "binder.json": (b"legacy metadata", None, "manual_review"),
        "_binder.yaml": (b"legacy seed metadata", None, "manual_review"),
    }
    (target / "docs" / "case").mkdir()
    for name, (source, destination, _) in cases.items():
        (legacy / name).parent.mkdir(parents=True, exist_ok=True)
        (legacy / name).write_bytes(source)
        if destination is not None:
            (target / name).parent.mkdir(parents=True, exist_ok=True)
            (target / name).write_bytes(destination)

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.md").write_text("outside the vault")
    (legacy / "linked").symlink_to(outside, target_is_directory=True)

    preview = user_workflow._seed_user_vault_docs()
    rows = {Path(row["source"]).relative_to(legacy).as_posix(): row for row in preview["legacy_review"]}
    assert set(rows) == set(cases) | {"linked"}
    assert preview["created_count"] == 0
    for name, (source, destination, status) in cases.items():
        assert rows[name]["status"] == status
        assert rows[name]["target"] == str(target / name)
        assert (legacy / name).read_bytes() == source
        if destination is not None:
            assert (target / name).read_bytes() == destination
    assert rows["linked"]["status"] == "manual_review"
    assert not (target / "docs/project/new.md").exists()


def test_fresh_seed_creates_plain_sandbox_and_preserves_readme(tmp_path, monkeypatch):
    vault = tmp_path / "Vault"
    monkeypatch.setattr(user_workflow.settings, "vault_root", vault)
    monkeypatch.setattr(binder_engine, "VAULT_ROOT", vault)
    monkeypatch.setattr(binder_engine, "BINDERS_ROOT", vault / "Binders")

    assert user_workflow._seed_user_vault_docs()["created_count"] == 2
    assert {path.name for path in vault.iterdir()} == {"Memory", "Sandbox"}
    assert binder_engine.list_binders() == []
    readme = vault / "Sandbox" / "README.md"
    readme.write_text("My drafts", encoding="utf-8")
    assert user_workflow._seed_user_vault_docs()["created_count"] == 0
    assert readme.read_text(encoding="utf-8") == "My drafts"
