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
    rule_id: str | None = None,
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
    target.write_text(
        render_task_markdown(
            title=task_title,
            source=f"feed:{source}",
            source_id=str(activity_id),
            status="todo",
            body=str(activity.get("content") or ""),
            metadata={"priority": priority, "binder": binder, "tags": tags},
        ),
        encoding="utf-8",
    )
    return {"task_id": target.stem, "path": str(target)}
