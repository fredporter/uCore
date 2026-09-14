"""Permission-aware macOS source adapters for the user Feed.

Sync is always explicit: constructing this service or reading status never opens
an app or triggers a macOS Automation permission prompt.
"""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

from app.services.feed_store import FeedServer


@dataclass(frozen=True)
class AppleSource:
    id: str
    label: str
    app: str
    state: str = "available"
    note: str = ""


SOURCES = (
    AppleSource("mail", "Apple Mail", "Mail"),
    AppleSource("calendar", "Apple Calendar", "Calendar"),
    AppleSource("messages", "Apple Messages", "Messages"),
    AppleSource("reminders", "Apple Reminders", "Reminders"),
    AppleSource("notes", "Apple Notes (Scratchpad)", "Notes"),
    AppleSource("contacts-notes-rules", "Contacts · Notes · Rules", "Contacts"),
    AppleSource(
        "whatsapp",
        "WhatsApp",
        "WhatsApp",
        "planned",
        "Awaiting an approved export/share-sheet or MCP adapter; UI scraping is not used.",
    ),
)

SCRIPT_BY_SOURCE = {
    "mail": '''const app = Application("Mail");
const rows = []; const items = app.inbox.messages();
for (const m of items) {
    if (!m.readStatus()) {
        let flagged = false; let flagIdx = -1;
        try { flagged = Boolean(m.flaggedStatus()); flagIdx = flagged ? m.flagIndex() : -1; } catch(e){}
        rows.push({
            external_id: String(m.messageId()),
            title: String(m.subject()),
            content: String(m.content()),
            contact_name: String(m.sender()),
            is_flagged: flagged,
            flag_index: flagIdx
        });
    }
    if (rows.length >= __LIMIT__) break;
}
JSON.stringify(rows);''',
    "calendar": '''const app = Application("Calendar"); const rows = []; const cutoff = new Date(Date.now() - 7 * 86400000);
for (const calendar of app.calendars()) { for (const e of calendar.events()) { const start=e.startDate(); if (start >= cutoff) rows.push({external_id:String(e.uid()), title:String(e.summary()), content:String(e.description() || ""), timestamp:start.toISOString()}); if (rows.length >= __LIMIT__) break; } if (rows.length >= __LIMIT__) break; }
JSON.stringify(rows);''',
    "messages": '''const app = Application("Messages"); const rows = [];
for (const chat of app.chats()) { const name=String(chat.name() || chat.id()); rows.push({external_id:String(chat.id()), title:name, content:"Conversation available in Messages", contact_name:name}); if (rows.length >= __LIMIT__) break; }
JSON.stringify(rows);''',
    "reminders": '''const app = Application("Reminders"); const rows = [];
for (const list of app.lists()) {
    for (const r of list.reminders.whose({completed: false})()) {
        let dueStr = null;
        try { const d = r.dueDate(); if (d) dueStr = d.toISOString(); } catch(e){}
        rows.push({
            external_id: String(r.id()),
            title: String(r.name() || "Reminder"),
            content: String(r.body() || ""),
            timestamp: dueStr || new Date().toISOString(),
            list: String(list.name())
        });
        if (rows.length >= __LIMIT__) break;
    }
    if (rows.length >= __LIMIT__) break;
}
JSON.stringify(rows);''',
    "notes": '''const app = Application("Notes"); const rows = [];
let targetNotes = [];
try {
    const f = app.folders.whose({name: "uDos"})();
    targetNotes = (f && f.length > 0) ? f[0].notes() : app.defaultAccount().notes();
} catch(e) { targetNotes = app.defaultAccount().notes(); }
for (const n of targetNotes) {
    rows.push({
        external_id: String(n.id()),
        title: String(n.name() || "Note"),
        content: String(n.plaintext ? n.plaintext() : ""),
        timestamp: n.modificationDate() ? n.modificationDate().toISOString() : new Date().toISOString()
    });
    if (rows.length >= __LIMIT__) break;
}
JSON.stringify(rows);''',
    "contacts-notes-rules": '''const app = Application("Contacts"); const rows = [];
for (const p of app.people()) { const note=String(p.note() || ""); if (note) rows.push({external_id:String(p.id()), title:String(p.name()), content:note}); if (rows.length >= __LIMIT__) break; }
JSON.stringify(rows);''',
}


def _run_jxa(script: str) -> list[dict[str, Any]]:
    """Execute a JSON-producing JavaScript for Automation adapter."""
    proc = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "macOS Automation request failed")
    try:
        value = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Apple adapter did not return structured JSON") from exc
    return value if isinstance(value, list) else []


class AppleFeedSync:
    def __init__(
        self,
        feed: FeedServer | None = None,
        runner: Callable[[str], list[dict[str, Any]]] = _run_jxa,
    ) -> None:
        self.feed = feed or FeedServer()
        self.runner = runner

    def source_status(self) -> list[dict[str, Any]]:
        mac = platform.system() == "Darwin"
        automation = mac and shutil.which("osascript") is not None
        return [
            {
                "id": item.id,
                "label": item.label,
                "app": item.app,
                "state": item.state if automation else "unavailable",
                "available": automation and item.state == "available",
                "requires_user_permission": item.state == "available",
                "bidirectional": item.id in {"reminders", "notes", "mail"},
                "note": item.note or ("Requires macOS Automation permission on first sync." if automation else "macOS only"),
            }
            for item in SOURCES
        ]

    async def sync(self, source: str, *, limit: int = 50) -> dict[str, Any]:
        known = {item.id: item for item in SOURCES}
        if source not in known:
            raise ValueError(f"Unknown feed source: {source}")
        item = known[source]
        if item.state != "available":
            return {"ok": False, "source": source, "state": item.state, "error": item.note}
        if platform.system() != "Darwin" or shutil.which("osascript") is None:
            return {"ok": False, "source": source, "state": "unavailable", "error": "macOS Automation is unavailable"}

        try:
            rows = self.runner(SCRIPT_BY_SOURCE[source].replace("__LIMIT__", str(limit)))
        except Exception as exc:
            return {"ok": False, "source": source, "state": "permission-or-adapter-error", "error": str(exc), "imported": 0}

        imported = 0
        for row in rows[:limit]:
            external_id = str(row.get("external_id") or "").strip()
            if not external_id:
                digest = json.dumps(row, sort_keys=True, default=str).encode()
                external_id = hashlib.sha256(digest).hexdigest()[:24]
            content = str(row.get("content") or "")
            metadata = {"apple_app": item.app, "synced_by": "snackmachine"}
            activity_type = "contact-note-rule" if source == "contacts-notes-rules" else source
            if source == "contacts-notes-rules":
                metadata["rules"] = [line.strip() for line in content.splitlines() if line.strip().lower().startswith(("rule:", "ucore:"))]
            importance = 0.65 if source in {"mail", "calendar"} else 0.5
            if row.get("is_flagged") or (row.get("flag_index", -1) >= 0):
                metadata["is_flagged"] = True
                metadata["flag_index"] = row.get("flag_index")
                importance = 0.85
            if row.get("list"):
                metadata["list"] = row.get("list")

            result = await self.feed.ingest_activity(
                source=source,
                external_id=external_id,
                type=activity_type,
                title=str(row.get("title") or item.label),
                content=content,
                contact_name=str(row.get("contact_name") or ""),
                importance=importance,
                metadata=metadata,
            )
            try:
                from app.services.feed_consumer import FeedConsumer

                FeedConsumer().consume_activity(
                    {
                        "id": result["id"],
                        "source": source,
                        "type": activity_type,
                        "title": str(row.get("title") or item.label),
                        "content": content,
                        "importance": importance,
                        "metadata": metadata,
                    }
                )
            except Exception:
                # Feed persistence is authoritative; spool projection is best-effort.
                pass
            imported += 1

        # Mirror to ~/Vault/Activity/events.jsonl and Daily_Activity.md
        try:
            from app.services.activity_markdown import (
                append_activity_events,
                update_daily_activity_markdown,
            )
            act_events = [
                {
                    "external_id": str(r.get("external_id") or hashlib.sha256(json.dumps(r, sort_keys=True, default=str).encode()).hexdigest()[:24]),
                    "source": source,
                    "title": str(r.get("title") or item.label),
                    "content": str(r.get("content") or ""),
                    "timestamp": str(r.get("timestamp") or ""),
                    "privacy": "private",
                }
                for r in rows[:limit]
            ]
            append_activity_events(act_events)
            update_daily_activity_markdown()
        except Exception:
            pass

        return {"ok": True, "source": source, "state": "synced", "imported": imported}

    def export_reminder(
        self,
        title: str,
        notes: str = "",
        list_name: str = "uDos",
        due_date: str | None = None,
    ) -> dict[str, Any]:
        """Export an approved task or action item into Apple Reminders."""
        from app.services.host_pim import HostPIMService

        pim = HostPIMService()
        return pim.export_to_apple_reminders(
            title=title, notes=notes, list_name=list_name, due_date=due_date
        )

    def export_note(
        self,
        title: str,
        body_markdown: str,
        folder: str = "uDos",
    ) -> dict[str, Any]:
        """Export an approved idea or scratchpad note to Apple Notes."""
        from app.services.host_pim import HostPIMService

        pim = HostPIMService()
        return pim.export_to_apple_notes(
            title=title, body_markdown=body_markdown, folder=folder
        )

    def archive_email(self, message_id: str) -> dict[str, Any]:
        """Archive an email in Apple Mail to maintain Inbox Zero."""
        from app.services.host_pim import HostPIMService

        pim = HostPIMService()
        return pim.archive_apple_mail(message_id=message_id)

    def run_shortcut(self, name: str, input_text: str = "") -> dict[str, Any]:
        """Run a native macOS shortcut."""
        from app.services.host_pim import HostPIMService

        pim = HostPIMService()
        return pim.run_shortcut(name=name, input_text=input_text)

    def list_shortcuts(self) -> list[str]:
        """List native macOS shortcuts."""
        from app.services.host_pim import HostPIMService

        pim = HostPIMService()
        return pim.list_shortcuts()
