"""Task-to-Action Bridge — executes approved host automations for sovereign .tasker tasks.

Adheres to the Zen Ecosystem Contract:
1. Host OS Native (Shortcuts CLI, AppleScript/JXA, notify-send, say)
2. Ecosystem Service (uCore Feed / Activity Pod)
3. Zero surveillance, non-destructive, safe execution with explicit approval gates.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.flow import task_store
from app.services.host_pim import HostPIMService

log = logging.getLogger("ucore.task_action_bridge")


def find_task_file(task_id: str, tasker_dir: Path | None = None) -> Path | None:
    """Locate a .tasker markdown file by its stem or ID."""
    base = tasker_dir or task_store.default_tasker_dir()
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

    def action_to_task(
        self,
        activity_event: dict[str, Any],
        board: str = "inbox",
        suggested_action: dict[str, Any] | None = None,
        tasker_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Convert an inbound activity event (feed, email, note, notification) into a sovereign .tasker task."""
        from app.services.tasker_ops import resolve_tasker_dir, write_task_markdown

        base = resolve_tasker_dir(str(tasker_dir) if tasker_dir else None)
        title = str(activity_event.get("title") or "New Inbound Task").strip()
        body = str(activity_event.get("content") or activity_event.get("notes") or "").strip()
        source = str(activity_event.get("source") or "activity").strip()
        source_id = str(activity_event.get("external_id") or activity_event.get("id") or "").strip()
        due_date = activity_event.get("due") or activity_event.get("due_date") or activity_event.get("timestamp")
        binder = str(activity_event.get("binder") or activity_event.get("list") or "Inbox").strip()
        priority = str(activity_event.get("priority") or "medium").strip()

        metadata: dict[str, Any] = {
            "binder": binder,
            "board": board,
            "priority": priority,
        }
        if due_date:
            metadata["due"] = str(due_date)

        if suggested_action:
            metadata["action_type"] = suggested_action.get("action_type")
            metadata["action_payload"] = suggested_action.get("payload") or {}
            metadata["approval_status"] = suggested_action.get("approval_status", "pending_approval")

        result = write_task_markdown(
            title=title,
            board=board,
            status="todo",
            body=body,
            source=source,
            source_id=source_id or None,
            metadata=metadata,
            tasker_dir=str(base),
        )
        return {"ok": True, "task": result, "metadata": metadata}

    def link_action_to_task(
        self,
        task_id: str,
        action_type: str,
        payload: dict[str, Any] | None = None,
        requires_approval: bool = True,
        tasker_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Link an automation action to an existing task with an approval gate."""
        task_file = find_task_file(task_id, tasker_dir=tasker_dir)
        if not task_file or not task_file.exists():
            return {"ok": False, "error": f"Task '{task_id}' not found"}

        from app.api.tasker_api import _update_task_file
        base = task_file.parent.parent

        approval_status = "pending_approval" if requires_approval else "approved"
        patch = {
            "action_type": action_type,
            "action_payload": payload or {},
            "approval_status": approval_status,
        }
        res = _update_task_file(base=base, task_id=task_id, patch=patch)
        return {
            "ok": True,
            "task_id": task_id,
            "action_type": action_type,
            "approval_status": approval_status,
            "updated": res.get("updated"),
        }

    def approve_task_action(
        self,
        task_id: str,
        execute_now: bool = True,
        tasker_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Approve a pending task action, optionally executing it immediately."""
        task_file = find_task_file(task_id, tasker_dir=tasker_dir)
        if not task_file or not task_file.exists():
            return {"ok": False, "error": f"Task '{task_id}' not found"}

        from app.api.tasker_api import _parse_markdown_task, _update_task_file
        task_data = _parse_markdown_task(task_file)
        base = task_file.parent.parent

        action_type = task_data.get("action_type")
        if not action_type:
            return {"ok": False, "error": f"Task '{task_id}' has no linked action"}

        payload = task_data.get("action_payload") or {}

        if execute_now:
            exec_result = self.execute_action(
                task_id=task_id,
                action_type=action_type,
                payload=payload,
                tasker_dir=base,
                force=True,
            )
            new_approval_status = "executed" if exec_result.get("ok") else "failed"
            _update_task_file(base=base, task_id=task_id, patch={"approval_status": new_approval_status})
            return {
                "ok": exec_result.get("ok", False),
                "task_id": task_id,
                "action_type": action_type,
                "approval_status": new_approval_status,
                "execution": exec_result,
            }
        else:
            _update_task_file(base=base, task_id=task_id, patch={"approval_status": "approved"})
            return {
                "ok": True,
                "task_id": task_id,
                "action_type": action_type,
                "approval_status": "approved",
            }

    def reject_task_action(
        self,
        task_id: str,
        reason: str = "",
        tasker_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Reject a pending task action."""
        task_file = find_task_file(task_id, tasker_dir=tasker_dir)
        if not task_file or not task_file.exists():
            return {"ok": False, "error": f"Task '{task_id}' not found"}

        from app.api.tasker_api import _update_task_file
        base = task_file.parent.parent
        _update_task_file(
            base=base,
            task_id=task_id,
            patch={"approval_status": "rejected", "rejection_reason": reason},
        )
        return {"ok": True, "task_id": task_id, "approval_status": "rejected", "reason": reason}

    def execute_action(
        self,
        task_id: str,
        action_type: str,
        payload: dict[str, Any] | None = None,
        tasker_dir: Path | None = None,
        force: bool = False,
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

        # Approval gate check
        if task_data.get("approval_status") == "pending_approval" and not force:
            return {
                "ok": False,
                "requires_approval": True,
                "task_id": task_id,
                "action_type": action_type,
                "error": "Action requires explicit user approval before execution",
            }

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

        # If executed from an existing file, record approval status update to executed
        if task_file and task_file.exists():
            try:
                from app.api.tasker_api import _update_task_file
                base = task_file.parent.parent
                _update_task_file(base=base, task_id=task_id, patch={"approval_status": "executed"})
            except Exception:
                pass

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

    def sync_inbound_reminders(
        self,
        list_name: str | None = None,
        limit: int = 50,
        completed: bool = False,
        default_board: str = "inbox",
        tasker_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Intake Apple Reminders and mirror them as sovereign .tasker tasks."""
        res = self.pim.intake_apple_reminders(list_name=list_name, limit=limit, completed=completed)
        if not res.get("ok"):
            return {"ok": False, "error": res.get("error", "Reminders intake failed"), "imported": 0}

        items = res.get("items", [])
        imported = []
        for item in items:
            title = item.get("title") or "Untitled Reminder"
            body = item.get("notes") or ""
            due = item.get("due_date")
            target_list = item.get("list") or list_name or "uDos"
            source_id = str(item.get("id") or "")
            t_res = self.action_to_task(
                activity_event={
                    "title": title,
                    "content": body,
                    "source": "apple_reminders",
                    "external_id": source_id,
                    "due": due,
                    "binder": target_list,
                },
                board=default_board,
                tasker_dir=tasker_dir,
            )
            imported.append(t_res)

        return {"ok": True, "imported_count": len(imported), "items": imported}

    def sync_outbound_binder(
        self,
        binder: str,
        list_name: str | None = None,
        tasker_dir: Path | None = None,
    ) -> dict[str, Any]:
        """Push all active tasks in a binder out to Apple Reminders."""
        base = tasker_dir or task_store.default_tasker_dir()
        if not base.exists():
            return {"ok": False, "error": "Tasker directory does not exist", "synced_count": 0}

        from app.api.tasker_api import _parse_markdown_task
        tasks_to_sync = []
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            for f in sorted(board_dir.glob("*.md")):
                try:
                    t = _parse_markdown_task(f)
                    if t.get("status") in {"todo", "in-progress"}:
                        t_binder = str(t.get("binder") or "").strip().lower()
                        if t_binder == binder.strip().lower() or binder == "*":
                            tasks_to_sync.append({
                                "id": t.get("id"),
                                "title": t.get("title"),
                                "notes": t.get("description") or t.get("body"),
                                "due_date": t.get("due"),
                                "list": list_name or t.get("binder") or "uDos",
                            })
                except Exception:
                    continue

        target_list = list_name or binder if binder != "*" else "uDos"
        res = self.pim.sync_apple_reminders_outbound(tasks=tasks_to_sync, default_list=target_list)
        return res
