"""Canonical bridge from Feed activities to markdown-backed user workflow tasks."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.tasker_bridge import render_task_markdown, slugify
from app.services.workflow_status import default_tasker_dir


def promote_activity_to_task(
    activity: dict[str, Any],
    *,
    title: str | None = None,
    board: str = "inbox",
    priority: str = "medium",
    binder: str = "Sandbox",
    mission: str | None = None,
    due_date: str | None = None,
    rule_id: str | None = None,
    sync_apple_reminders: bool = False,
    archive_source_mail: bool = False,
) -> dict[str, Any]:
    activity_id = int(activity["id"])
    task_title = str(title or activity.get("title") or "Feed item").strip()
    source = str(activity.get("source") or "feed")
    source_id = f"feed-{activity_id}"
    target_dir = default_tasker_dir() / slugify(board or "inbox")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"todo-{slugify(task_title)}-{source_id}.md"
    tags = ["user", "feed", source]
    if rule_id:
        tags.append(f"rule-{slugify(rule_id)}")

    metadata: dict[str, Any] = {
        "priority": priority,
        "binder": binder,
        "tags": tags,
    }
    if mission:
        metadata["mission"] = mission
    if due_date:
        metadata["due"] = due_date

    reminders_result = None
    if sync_apple_reminders:
        try:
            from app.services.apple_feed_sync import AppleFeedSync

            target_list = binder if binder and binder != "Sandbox" else "uDos"
            reminders_result = AppleFeedSync().export_reminder(
                title=task_title,
                notes=str(activity.get("content") or ""),
                list_name=target_list,
                due_date=due_date,
            )
            if reminders_result.get("ok"):
                tags.append("synced:apple-reminders")
        except Exception:
            pass

    mail_archived_result = None
    if archive_source_mail and source == "mail":
        try:
            from app.services.apple_feed_sync import AppleFeedSync

            ext_id = str(activity.get("external_id") or "")
            if ext_id:
                mail_archived_result = AppleFeedSync().archive_email(ext_id)
        except Exception:
            pass

    target.write_text(
        render_task_markdown(
            title=task_title,
            source=f"feed:{source}",
            source_id=str(activity_id),
            status="todo",
            body=str(activity.get("content") or ""),
            metadata=metadata,
        ),
        encoding="utf-8",
    )
    return {
        "task_id": target.stem,
        "path": str(target),
        "reminders_sync": reminders_result,
        "mail_archived": mail_archived_result,
    }
