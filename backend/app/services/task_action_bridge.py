"""Task-to-Action Bridge — executes approved host automations for sovereign .tasker tasks.

Adheres to the Zen Ecosystem Contract:
1. Host OS Native (Shortcuts CLI, AppleScript/JXA, notify-send, say)
2. Ecosystem Service (uCore Feed / Activity Pod)
3. Zero surveillance, non-destructive, safe execution
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.flow.task_store import default_tasker_dir
from app.services.host_pim import HostPIMService

log = logging.getLogger("ucore.task_action_bridge")


def find_task_file(task_id: str, tasker_dir: Path | None = None) -> Path | None:
    """Locate a .tasker markdown file by its stem or ID."""
    base = tasker_dir or default_tasker_dir()
    if not base.exists():
        return None
    for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        candidate = board_dir / f"{task_id}.md"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


class TaskActionBridge:
    """Bridges sovereign .tasker tasks to approved host automations."""

    def __init__(self, pim: HostPIMService | None = None) -> None:
        self.pim = pim or HostPIMService()

    def execute_action(
        self,
        task_id: str,
        action_type: str,
        payload: dict[str, Any] | None = None,
        tasker_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Execute an approved automation action for a given task.

        Supported action_types:
        - "shortcut": run a macOS shortcut (via /usr/bin/shortcuts)
        - "apple_reminders": export task to Apple Reminders
        - "apple_notes": export task body to Apple Notes
        - "archive_mail": archive linked email in Apple Mail
        - "notify": display native desktop notification
        - "say": speak task title/body
        """
        payload = payload or {}
        task_file = find_task_file(task_id, tasker_dir=tasker_dir)
        task_data: dict[str, Any] = {}
        if task_file and task_file.exists():
            from app.api.tasker_api import _parse_markdown_task
            task_data = _parse_markdown_task(task_file)

        title = payload.get("title") or task_data.get("title") or task_id
        body = payload.get("body") or task_data.get("body") or task_data.get("description") or ""
        binder = payload.get("binder") or task_data.get("binder") or "uDos"
        due_date = payload.get("due") or task_data.get("due")

        result: dict[str, Any] = {"ok": False, "action_type": action_type, "task_id": task_id}

        if action_type == "shortcut":
            shortcut_name = payload.get("name") or payload.get("shortcut")
            if not shortcut_name:
                return {"ok": False, "error": "Shortcut name is required in payload"}
            input_text = payload.get("input") or f"{title}\n\n{body}"
            result = self.pim.run_shortcut(shortcut_name, input_text=input_text)

        elif action_type == "apple_reminders":
            target_list = binder if binder and binder != "Sandbox" else "uDos"
            result = self.pim.export_to_apple_reminders(
                title=title,
                notes=body,
                list_name=target_list,
                due_date=due_date,
            )

        elif action_type == "apple_notes":
            target_folder = binder if binder and binder != "Sandbox" else "uDos"
            result = self.pim.export_to_apple_notes(
                title=title,
                body_markdown=body,
                folder=target_folder,
            )

        elif action_type == "archive_mail":
            message_id = payload.get("message_id") or task_data.get("source_id")
            if not message_id:
                return {"ok": False, "error": "message_id is required"}
            result = self.pim.archive_apple_mail(str(message_id))

        elif action_type == "notify":
            result = self.pim.notify(
                title=title,
                message=payload.get("message") or body or title,
                subtitle=binder,
            )

        elif action_type == "say":
            text = payload.get("text") or title
            result = self.pim.say(text=text, voice=payload.get("voice"))

        else:
            return {"ok": False, "error": f"Unsupported action_type: {action_type}"}

        # Record execution event in Feed Activity Pod
        try:
            from app.services.feed_store import FeedServer
            FeedServer().ingest_activity_sync(
                source="task_action",
                external_id=f"action_{task_id}_{int(datetime.now(UTC).timestamp())}",
                type=f"task_action_{action_type}",
                title=f"Executed Action: {action_type} for {title}",
                content=str(result),
                importance=0.4,
                metadata={
                    "task_id": task_id,
                    "action_type": action_type,
                    "result": result,
                },
            )
        except Exception:
            pass

        return {"ok": True, "task_id": task_id, "action_type": action_type, "result": result}
