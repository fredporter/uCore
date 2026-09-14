"""BitChat Sovereign Message Store & Binder Evidence Bridge.

Provides:
- Sovereign local SQLite message archive at $UDOS_HOME/pods/bitchat.db
- Real-time Activity Pod ingestion into activity.db (Snackbar notification)
- "Save to Binder": formats discussions into Markdown evidence in ~/Vault/binders/<binder>/evidence/chats/
- "Convert to Task": promotes chat action items into sovereign .tasker markdown tasks
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.settings import settings

log = logging.getLogger("ucore.bitchat_store")

DEFAULT_BITCHAT_POD = settings.udos_home / "pods" / "bitchat.db"


class BitChatStore:
    """Sovereign local SQLite store for BitChat messages and evidence exports."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_BITCHAT_POD
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS bitchat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_id TEXT UNIQUE NOT NULL,
            channel TEXT NOT NULL DEFAULT '#general',
            sender_name TEXT NOT NULL,
            sender_peer_id TEXT,
            recipient_id TEXT,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            saved_to_binder BOOLEAN DEFAULT 0,
            binder_evidence_path TEXT,
            task_id TEXT,
            metadata JSON
        );
        CREATE INDEX IF NOT EXISTS idx_bitchat_channel ON bitchat_messages(channel);
        CREATE INDEX IF NOT EXISTS idx_bitchat_ts ON bitchat_messages(timestamp);
        """
        self._conn.executescript(ddl)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def send_message(
        self,
        sender_name: str,
        content: str,
        channel: str = "#general",
        sender_peer_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record and broadcast a message, alerting the Feed Activity Pod."""
        msg_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO bitchat_messages
               (msg_id, channel, sender_name, sender_peer_id, recipient_id, content, timestamp, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                msg_id,
                channel,
                sender_name,
                sender_peer_id or "local",
                recipient_id or channel,
                content,
                now_iso,
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()

        record = {
            "msg_id": msg_id,
            "channel": channel,
            "sender_name": sender_name,
            "sender_peer_id": sender_peer_id or "local",
            "recipient_id": recipient_id or channel,
            "content": content,
            "timestamp": now_iso,
            "saved_to_binder": False,
            "task_id": None,
            "metadata": metadata or {},
        }

        # Synchronously alert Feed Activity Pod (Snackbar)
        try:
            from app.services.feed_store import FeedServer
            FeedServer().ingest_activity_sync(
                source="bitchat",
                external_id=msg_id,
                type="bitchat_message",
                title=f"[{channel}] {sender_name}",
                content=content,
                importance=0.6,
                metadata={
                    "msg_id": msg_id,
                    "channel": channel,
                    "sender_name": sender_name,
                    "sender_peer_id": sender_peer_id,
                },
            )
        except Exception as exc:
            log.debug("Could not ingest bitchat message into Feed Activity Pod: %s", exc)

        return record

    def get_messages(
        self,
        channel: str = "#general",
        limit: int = 50,
        since: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent chat history for a channel."""
        cursor = self._conn.cursor()
        query = "SELECT * FROM bitchat_messages WHERE channel = ?"
        params: List[Any] = [channel]
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for r in reversed(rows):
            meta = {}
            if r["metadata"]:
                try:
                    meta = json.loads(r["metadata"])
                except Exception:
                    pass
            results.append({
                "id": r["id"],
                "msg_id": r["msg_id"],
                "channel": r["channel"],
                "sender_name": r["sender_name"],
                "sender_peer_id": r["sender_peer_id"],
                "recipient_id": r["recipient_id"],
                "content": r["content"],
                "timestamp": r["timestamp"],
                "saved_to_binder": bool(r["saved_to_binder"]),
                "binder_evidence_path": r["binder_evidence_path"],
                "task_id": r["task_id"],
                "metadata": meta,
            })
        return results

    def save_to_binder(
        self,
        msg_ids: List[str],
        binder_name: str,
        title: str = "Discussion Evidence",
        vault_root: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Format selected messages as Markdown evidence and save into binder."""
        if not msg_ids:
            return {"ok": False, "error": "No messages selected"}

        cursor = self._conn.cursor()
        placeholders = ",".join("?" for _ in msg_ids)
        cursor.execute(
            f"SELECT * FROM bitchat_messages WHERE msg_id IN ({placeholders}) ORDER BY id ASC",
            msg_ids,
        )
        rows = cursor.fetchall()
        if not rows:
            return {"ok": False, "error": "None of the specified messages were found"}

        root = vault_root or settings.vault_root
        channel = rows[0]["channel"]
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        slug_title = "".join(c if c.isalnum() else "-" for c in title.lower()).strip("-")[:40]

        evidence_dir = root / "binders" / binder_name / "evidence" / "chats"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{date_str}-{slug_title}.md"
        target_path = evidence_dir / filename

        # Format markdown
        lines = [
            "---",
            "type: evidence",
            "source: bitchat",
            f"channel: '{channel}'",
            f"binder: '{binder_name}'",
            f"created: '{datetime.now(timezone.utc).isoformat()}'",
            "tags: [evidence, bitchat, chat, discussion]",
            "---",
            "",
            f"# {title}",
            "",
            f"Captured discussion from BitChat channel **{channel}** on `{date_str}`:",
            "",
        ]

        for r in rows:
            t_str = str(r["timestamp"])
            if "T" in t_str:
                time_only = t_str.split("T")[1][:8]
            elif " " in t_str:
                time_only = t_str.split(" ")[1][:8]
            else:
                time_only = t_str[:8]
            lines.append(f"- **{time_only}** `{r['sender_name']}`: {r['content']}")

        lines.append("")
        target_path.write_text("\n".join(lines), encoding="utf-8")

        # Mark messages as saved
        cursor.execute(
            f"UPDATE bitchat_messages SET saved_to_binder = 1, binder_evidence_path = ? WHERE msg_id IN ({placeholders})",
            [str(target_path)] + msg_ids,
        )
        self._conn.commit()

        return {
            "ok": True,
            "path": str(target_path),
            "filename": filename,
            "binder": binder_name,
            "saved_count": len(rows),
        }

    def convert_message_to_task(
        self,
        msg_id: str,
        board: str = "inbox",
        priority: str = "medium",
        binder: str = "Sandbox",
        due_date: Optional[str] = None,
        sync_apple_reminders: bool = False,
    ) -> Dict[str, Any]:
        """Convert a chat message into a sovereign .tasker markdown task."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM bitchat_messages WHERE msg_id = ?", (msg_id,))
        row = cursor.fetchone()
        if not row:
            return {"ok": False, "error": f"Message {msg_id} not found"}

        from app.services.feed_workflow import promote_activity_to_task

        sender = row["sender_name"]
        content = row["content"]
        channel = row["channel"]
        task_title = f"Action from {sender}: {content[:50].strip()}"

        mock_activity = {
            "id": int(time.time()),
            "source": "bitchat",
            "title": task_title,
            "content": f"Originated from BitChat `{channel}` by **{sender}**:\n\n> {content}",
        }

        promoted = promote_activity_to_task(
            mock_activity,
            title=task_title,
            board=board,
            priority=priority,
            binder=binder,
            due_date=due_date,
            sync_apple_reminders=sync_apple_reminders,
        )

        task_id = promoted["task_id"]
        cursor.execute(
            "UPDATE bitchat_messages SET task_id = ? WHERE msg_id = ?",
            (task_id, msg_id),
        )
        self._conn.commit()

        return {
            "ok": True,
            "task_id": task_id,
            "path": promoted["path"],
            "reminders_sync": promoted.get("reminders_sync"),
        }


# Singleton instance
_global_bitchat_store = BitChatStore()


def get_bitchat_store() -> BitChatStore:
    return _global_bitchat_store
