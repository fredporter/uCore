"""Comprehensive tests for the Outgoing Sync & Task Loop:
- Action-to-Task Pipeline (.tasker markdown generation, due dates, provenance linking)
- Task-to-Action Bridge (Shortcuts execution, Apple Reminders, Apple Notes, Mail Archiving)
- Bi-directional Apple Sync (Reminders list creation, due dates, Notes, Mail archiving)
- Activity Pod Resolution & Auto-Archival Rules
- Dispatch RSVP to Sovereign Task conversion
"""
from __future__ import annotations

import json
import platform
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.feed_api import (
    handle_feed_bulk_resolve,
    handle_feed_export_notes,
    handle_feed_export_reminders,
    handle_feed_promote,
    handle_feed_resolve,
    handle_feed_rules_apply,
)
from app.services.apple_feed_sync import AppleFeedSync
from app.services.dispatch_store import DispatchStore
from app.services.feed_rules import FeedRule, evaluate_feed_rules
from app.services.feed_store import FeedServer
from app.services.feed_workflow import promote_activity_to_task
from app.services.host_pim import HostPIMService
from app.services.task_action_bridge import TaskActionBridge


@pytest.fixture
def mock_pim(monkeypatch):
    executed = []

    def mock_runner(cmd: list[str], timeout: float = 10.0, input_data: str | None = None) -> str:
        executed.append((cmd, input_data))
        cmd_str = " ".join(cmd)
        if "shortcuts list" in cmd_str:
            return "Summarize Action\nQuick Capture\n"
        if "shortcuts run" in cmd_str:
            return "Shortcut executed successfully"
        if "Reminders" in cmd_str:
            return "reminder-id-xyz"
        if "Notes" in cmd_str:
            return "note-id-123"
        if "Mail" in cmd_str:
            return json.dumps({"ok": True, "count": 1, "archived": True})
        return "ok"

    pim = HostPIMService(runner=mock_runner)
    monkeypatch.setattr(pim, "is_macos", lambda: True)
    monkeypatch.setattr("shutil.which", lambda prog: f"/usr/bin/{prog}")
    return pim, executed


def test_export_reminder_with_due_date_and_list(mock_pim):
    pim, executed = mock_pim
    res = pim.export_to_apple_reminders(
        title="Follow up on Sovereign RSVP",
        notes="Guest requested vegan option",
        list_name="Launch Event",
        due_date="2026-09-25",
    )
    assert res["ok"] is True
    assert res["list"] == "Launch Event"
    assert len(executed) == 1
    script = executed[0][0][-1]
    assert 'list "Launch Event"' in script
    assert 'due date:date "2026-09-25"' in script


def test_shortcuts_execution(mock_pim):
    pim, executed = mock_pim
    shortcuts = pim.list_shortcuts()
    assert shortcuts == ["Summarize Action", "Quick Capture"]

    run_res = pim.run_shortcut("Summarize Action", input_text="Long report text")
    assert run_res["ok"] is True
    assert run_res["output"] == "Shortcut executed successfully"


def test_mail_archive_and_flag(mock_pim):
    pim, executed = mock_pim
    arch_res = pim.archive_apple_mail("test-msg-123")
    assert arch_res["ok"] is True
    assert arch_res["archived"] is True

    flag_res = pim.flag_apple_mail("test-msg-123", flag_index=1)
    assert flag_res["ok"] is True


@pytest.mark.asyncio
async def test_mail_ingest_with_flags_sets_high_importance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr("app.services.apple_feed_sync.shutil.which", lambda _: "/usr/bin/osascript")

    feed = FeedServer(str(tmp_path / "activity.db"))
    def runner(_script: str):
        return [
            {
                "external_id": "flagged-mail-1",
                "title": "Urgent Contract",
                "content": "Sign by tomorrow",
                "is_flagged": True,
                "flag_index": 0,
            }
        ]
    sync = AppleFeedSync(feed, runner=runner)
    result = await sync.sync("mail")
    assert result["ok"] is True
    assert result["imported"] == 1

    rows = await feed.query_feed(source="mail")
    assert len(rows) == 1
    assert rows[0]["importance"] == 0.85
    meta = json.loads(rows[0]["metadata"])
    assert meta.get("is_flagged") is True


@pytest.mark.asyncio
async def test_promote_activity_to_task_with_reminders_and_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_pim):
    pim, executed = mock_pim
    monkeypatch.setattr("app.services.host_pim.HostPIMService", lambda *args, **kwargs: pim)
    monkeypatch.setattr("app.flow.task_store.default_tasker_dir", lambda: tmp_path / "tasks")

    activity = {
        "id": 42,
        "source": "mail",
        "external_id": "mail-msg-99",
        "title": "Review Exhibition Specs",
        "content": "Ensure Mode 7 Teletext compatibility",
    }

    promoted = promote_activity_to_task(
        activity,
        board="inbox",
        priority="high",
        binder="Exhibition",
        mission="Universal OS",
        due_date="2026-10-01",
        sync_apple_reminders=True,
        archive_source_mail=True,
    )

    assert Path(promoted["path"]).exists()
    task_text = Path(promoted["path"]).read_text(encoding="utf-8")
    assert "due: '2026-10-01'" in task_text or "due: 2026-10-01" in task_text
    assert "binder: Exhibition" in task_text
    assert "mission: Universal OS" in task_text
    assert "synced:apple-reminders" in task_text

    assert promoted["reminders_sync"] is not None
    assert promoted["reminders_sync"]["ok"] is True
    assert promoted["mail_archived"] is not None
    assert promoted["mail_archived"]["archived"] is True


def test_dispatch_convert_rsvp_to_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_pim):
    pim, executed = mock_pim
    monkeypatch.setattr("app.services.host_pim.HostPIMService", lambda *args, **kwargs: pim)
    monkeypatch.setattr("app.flow.task_store.default_tasker_dir", lambda: tmp_path / "tasks")

    store = DispatchStore(root_dir=tmp_path / "dispatches", token_index_path=tmp_path / "tokens.json")
    disp = store.create_dispatch(title="Zen Gathering", story_markdown="# Welcome to the Tea Ceremony")
    token = disp["token"]

    store.submit_rsvp(token, {
        "name": "Lady Ada",
        "email": "ada@lovelace.org",
        "answers": {"Attending": "Yes", "Dietary": "Matcha Only"},
    })

    res = store.convert_rsvp_to_task(
        dispatch_id=disp["id"],
        rsvp_index=0,
        board="inbox",
        priority="high",
        binder="Ceremony",
        due_date="2026-11-05",
        sync_apple_reminders=True,
    )

    assert res["status"] == "ok"
    assert Path(res["path"]).exists()
    content = Path(res["path"]).read_text(encoding="utf-8")
    assert "Lady Ada" in content
    assert "Matcha Only" in content

    # Verify responses.json was updated with task_id
    responses = store.get_responses(disp["id"])
    assert responses[0].get("task_id") == res["task_id"]


def test_task_action_bridge_execution(tmp_path: Path, mock_pim, monkeypatch: pytest.MonkeyPatch):
    pim, executed = mock_pim
    task_dir = tmp_path / "tasks" / "inbox"
    task_dir.mkdir(parents=True, exist_ok=True)
    task_file = task_dir / "todo-run-report-1.md"
    task_file.write_text(
        "---\ntitle: Run Report\nstatus: todo\nbinder: Analytics\n---\n# Run Report\nGenerate monthly summary\n",
        encoding="utf-8",
    )

    bridge = TaskActionBridge(pim=pim)
    res = bridge.execute_action(
        task_id="todo-run-report-1",
        action_type="shortcut",
        payload={"name": "Summarize Action"},
        tasker_dir=tmp_path / "tasks",
    )
    assert res["ok"] is True
    assert res["result"]["ok"] is True


def test_feed_server_resolve_activity(tmp_path: Path):
    feed = FeedServer(str(tmp_path / "activity.db"))
    ingest = feed.ingest_activity_sync(
        source="dispatch",
        type="dispatch_rsvp_received",
        title="RSVP from John",
        content="Will be there",
    )
    act_id = ingest["id"]

    # Activity is initially unprocessed
    cursor = feed._conn.execute("SELECT processed FROM user_activity WHERE id = ?", (act_id,))
    assert cursor.fetchone()["processed"] == 0

    # Resolve activity
    res = feed.resolve_activity(activity_id=act_id, note="Follow-up completed via phone")
    assert res["ok"] is True
    assert res["processed"] == 1

    cursor = feed._conn.execute("SELECT processed, metadata FROM user_activity WHERE id = ?", (act_id,))
    row = cursor.fetchone()
    assert row["processed"] == 1
    meta = json.loads(row["metadata"])
    assert meta["resolution_note"] == "Follow-up completed via phone"
    assert meta["archived"] is True

    # Bulk resolve
    ingest2 = feed.ingest_activity_sync(source="mail", type="mail", title="Item 2")
    bulk_res = feed.bulk_resolve([ingest2["id"]], note="Bulk cleared")
    assert bulk_res["ok"] is True
    assert bulk_res["resolved_count"] == 1


def test_feed_rules_with_flagged_and_auto_archive(tmp_path: Path):
    rule_flagged = FeedRule(
        id="flagged-rule",
        enabled=True,
        sources=("mail",),
        contains=(),
        min_importance=0.6,
        require_flagged=True,
        action="create-task",
        board="inbox",
        priority="high",
        binder="Urgent",
        sync_reminders=True,
        archive_mail=True,
    )
    rule_normal = FeedRule(
        id="normal-rule",
        enabled=True,
        sources=("mail",),
        contains=("newsletter",),
        min_importance=0.4,
        require_flagged=False,
        action="auto-archive",
        board="inbox",
        priority="low",
        binder="Sandbox",
    )

    activities = [
        {
            "id": 1,
            "source": "mail",
            "title": "Flagged urgent email",
            "importance": 0.85,
            "metadata": {"is_flagged": True},
        },
        {
            "id": 2,
            "source": "mail",
            "title": "Routine newsletter",
            "importance": 0.5,
            "metadata": {"is_flagged": False},
        },
    ]

    proposals = evaluate_feed_rules(activities, [rule_flagged, rule_normal])
    assert len(proposals) == 2

    # Proposal 1 matched flagged-rule
    prop1 = next(p for p in proposals if p["activity_id"] == 1)
    assert prop1["rule_id"] == "flagged-rule"
    assert prop1["sync_reminders"] is True
    assert prop1["archive_mail"] is True

    # Proposal 2 matched normal-rule
    prop2 = next(p for p in proposals if p["activity_id"] == 2)
    assert prop2["rule_id"] == "normal-rule"
    assert prop2["action"] == "auto-archive"
