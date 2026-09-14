"""Dispatch Store & Ephemeral Token Manager.

Manages interactive story dispatches, ephemeral access tokens (/p/:token),
RSVP submission records, and preserves raw originals under ~/Vault/dispatches/<id>/originals/.
"""
from __future__ import annotations

import json
import logging
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.settings import settings

log = logging.getLogger("ucore.dispatch_store")


class DispatchStore:
    """Sovereign store for interactive dispatches and RSVPs."""

    def __init__(self, root_dir: Optional[Path] = None, token_index_path: Optional[Path] = None):
        self.root_dir = root_dir or (settings.vault_root / "dispatches")
        self.token_index_path = token_index_path or (settings.data_dir / "dispatch_tokens.json")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.token_index_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_tokens()

    def _load_tokens(self) -> Dict[str, str]:
        if not self.token_index_path.exists():
            return {}
        try:
            data = json.loads(self.token_index_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception as exc:
            log.warning("Could not read dispatch token index: %s", exc)
        return {}

    def _save_tokens(self, tokens: Dict[str, str]) -> None:
        try:
            self.token_index_path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
        except Exception as exc:
            log.error("Failed to write dispatch token index: %s", exc)

    def create_dispatch(
        self,
        title: str,
        story_markdown: str,
        lead_text: str = "",
        hero_gif_bytes: Optional[bytes] = None,
        hero_gif_name: Optional[str] = None,
        expires_in_seconds: Optional[int] = None,
        burn_after_read: bool = False,
        mode_default: str = "card",
        binder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new dispatch, generate an ephemeral token, and preserve originals."""
        timestamp = int(time.time())
        dispatch_id = f"disp_{timestamp}_{secrets.token_hex(4)}"
        token = secrets.token_urlsafe(16)

        dispatch_dir = self.root_dir / dispatch_id
        originals_dir = dispatch_dir / "originals"
        originals_dir.mkdir(parents=True, exist_ok=True)

        # Preserve original markdown
        (originals_dir / "source.story.md").write_text(story_markdown, encoding="utf-8")

        # Save hero GIF if provided
        hero_rel_path: Optional[str] = None
        if hero_gif_bytes:
            hero_file = originals_dir / "hero.gif"
            hero_file.write_bytes(hero_gif_bytes)
            hero_rel_path = f"/api/dispatch/asset/{dispatch_id}/hero.gif"
        elif hero_gif_name:
            hero_rel_path = f"/api/dispatch/catalog/asset/{hero_gif_name}"

        expires_at: Optional[int] = None
        if expires_in_seconds and expires_in_seconds > 0:
            expires_at = timestamp + expires_in_seconds

        manifest = {
            "id": dispatch_id,
            "token": token,
            "title": title,
            "lead_text": lead_text,
            "created_at": timestamp,
            "created_iso": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "burn_after_read": bool(burn_after_read),
            "mode_default": mode_default,
            "hero_asset": hero_rel_path,
            "binder_id": binder_id,
            "view_count": 0,
            "status": "active",
        }

        (dispatch_dir / "dispatch.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (dispatch_dir / "responses.json").write_text("[]", encoding="utf-8")

        # Update token index
        tokens = self._load_tokens()
        tokens[token] = dispatch_id
        self._save_tokens(tokens)

        # Ingest into Feed Activity Pod (Snackbar)
        try:
            from app.services.feed_store import FeedServer
            FeedServer().ingest_activity_sync(
                source="dispatch",
                external_id=dispatch_id,
                type="dispatch_published",
                title=f"Published: {title}",
                content=lead_text or title,
                url=f"/p/{token}",
                importance=0.6,
                metadata={
                    "dispatch_id": dispatch_id,
                    "token": token,
                    "binder_id": binder_id,
                    "mode_default": mode_default,
                },
            )
        except Exception as exc:
            log.warning("Could not ingest dispatch creation into feed: %s", exc)

        # Update syndicated feeds in ~/Vault/feeds/
        try:
            from app.services.dispatch_feed import dispatch_feed_service
            dispatch_feed_service.sync_to_vault()
        except Exception as exc:
            log.warning("Could not sync feeds: %s", exc)

        return manifest

    def get_dispatch_by_token(self, token: str, record_view: bool = True) -> Dict[str, Any]:
        """Retrieve dispatch by guest token, evaluating expiration and burn status."""
        tokens = self._load_tokens()
        dispatch_id = tokens.get(token)
        if not dispatch_id:
            return {"status": "not_found", "error": "Dispatch not found"}

        dispatch_dir = self.root_dir / dispatch_id
        manifest_path = dispatch_dir / "dispatch.json"
        if not manifest_path.exists():
            return {"status": "not_found", "error": "Dispatch manifest missing"}

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        # Check burn status
        if manifest.get("status") == "burned":
            return {
                "status": "burned",
                "tombstone": "This dispatch was ephemeral and has dissolved into the ether.",
            }

        # Check expiration
        expires_at = manifest.get("expires_at")
        now = int(time.time())
        if expires_at and now > expires_at:
            manifest["status"] = "expired"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            return {
                "status": "expired",
                "tombstone": "This dispatch has expired and dissolved into the ether.",
            }

        # Record view count
        if record_view:
            manifest["view_count"] = manifest.get("view_count", 0) + 1
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Read story markdown
        story_path = dispatch_dir / "originals" / "source.story.md"
        story_md = story_path.read_text(encoding="utf-8") if story_path.exists() else ""

        return {
            "status": "active",
            "dispatch": manifest,
            "story_markdown": story_md,
        }

    def submit_rsvp(self, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit response to a dispatch, updating responses.json and burning if configured."""
        record = self.get_dispatch_by_token(token, record_view=False)
        if record.get("status") != "active":
            return record

        manifest = record["dispatch"]
        dispatch_id = manifest["id"]
        dispatch_dir = self.root_dir / dispatch_id
        responses_path = dispatch_dir / "responses.json"

        responses: List[Dict[str, Any]] = []
        if responses_path.exists():
            try:
                responses = json.loads(responses_path.read_text(encoding="utf-8"))
            except Exception:
                responses = []

        entry = {
            "timestamp": int(time.time()),
            "submitted_iso": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }
        responses.append(entry)
        responses_path.write_text(json.dumps(responses, indent=2), encoding="utf-8")

        # Burn token if configured
        if manifest.get("burn_after_read"):
            manifest["status"] = "burned"
            (dispatch_dir / "dispatch.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Ingest RSVP into Feed Activity Pod (notifies Snackbar)
        contact_name = payload.get("name") or payload.get("contact_name") or "Anonymous Sovereign Guest"
        try:
            from app.services.feed_store import FeedServer
            FeedServer().ingest_activity_sync(
                source="dispatch",
                external_id=f"{dispatch_id}_rsvp_{len(responses)}",
                type="dispatch_rsvp_received",
                title=f"RSVP Received: {manifest.get('title')}",
                content=f"Response from {contact_name}",
                url=f"/p/{token}",
                contact_name=contact_name,
                importance=0.8,
                metadata={
                    "dispatch_id": dispatch_id,
                    "binder_id": manifest.get("binder_id"),
                    "submission": payload,
                },
            )
        except Exception as exc:
            log.warning("Could not ingest RSVP into feed: %s", exc)

        return {
            "status": "success",
            "message": "Response recorded peacefully",
            "burned": manifest.get("burn_after_read", False),
        }

    def get_responses(self, dispatch_id: str) -> List[Dict[str, Any]]:
        """Host query for all collected responses."""
        responses_path = self.root_dir / dispatch_id / "responses.json"
        if not responses_path.exists():
            return []
        try:
            return json.loads(responses_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def convert_rsvp_to_task(
        self,
        dispatch_id: str,
        rsvp_index: int,
        board: str = "inbox",
        priority: str = "medium",
        binder: Optional[str] = None,
        mission: Optional[str] = None,
        due_date: Optional[str] = None,
        sync_apple_reminders: bool = False,
    ) -> Dict[str, Any]:
        """Convert a collected RSVP submission into a sovereign .tasker task."""
        dispatch_dir = self.root_dir / dispatch_id
        responses_path = dispatch_dir / "responses.json"
        manifest_path = dispatch_dir / "dispatch.json"

        if not responses_path.exists() or not manifest_path.exists():
            return {"status": "not_found", "error": "Dispatch or responses not found"}

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        responses = json.loads(responses_path.read_text(encoding="utf-8"))

        if rsvp_index < 0 or rsvp_index >= len(responses):
            return {"status": "not_found", "error": f"RSVP index {rsvp_index} out of range"}

        entry = responses[rsvp_index]
        payload = entry.get("data") or {}
        contact_name = payload.get("name") or payload.get("contact_name") or payload.get("attendee_name") or "Anonymous Guest"
        answers = payload.get("answers") or {}
        answers_str = "\n".join(f"- **{k}**: {v}" for k, v in answers.items()) if answers else ""
        notes = payload.get("notes") or payload.get("email") or ""

        target_binder = binder or manifest.get("binder_id") or "Sandbox"
        dispatch_title = manifest.get("title") or dispatch_id
        task_title = f"RSVP Follow-up: {contact_name} ({dispatch_title})"

        body_lines = [
            f"RSVP submission for dispatch **{dispatch_title}** (`{dispatch_id}`).",
            f"- **Respondent**: {contact_name}",
            f"- **Submitted**: {entry.get('submitted_iso', '')}",
        ]
        if notes:
            body_lines.append(f"- **Notes/Email**: {notes}")
        if answers_str:
            body_lines.append("\n### Form Responses\n" + answers_str)

        body_content = "\n".join(body_lines)

        from app.services.feed_workflow import promote_activity_to_task
        mock_activity = {
            "id": int(time.time()),
            "source": "dispatch",
            "title": task_title,
            "content": body_content,
        }
        promoted = promote_activity_to_task(
            mock_activity,
            title=task_title,
            board=board,
            priority=priority,
            binder=target_binder,
            mission=mission,
            due_date=due_date,
            sync_apple_reminders=sync_apple_reminders,
        )

        task_id = promoted["task_id"]
        entry["task_id"] = task_id
        responses_path.write_text(json.dumps(responses, indent=2), encoding="utf-8")

        # Link in Activity Pod if possible
        try:
            from app.services.feed_store import FeedServer
            feed = FeedServer()
            ext_id = f"{dispatch_id}_rsvp_{rsvp_index + 1}"
            rows = feed._conn.execute(
                "SELECT id FROM user_activity WHERE source = 'dispatch' AND external_id = ?",
                (ext_id,),
            ).fetchall()
            if rows:
                act_id = rows[0]["id"]
                feed._conn.execute(
                    "INSERT INTO task_activity_links (task_id, activity_id, link_type) VALUES (?, ?, 'dispatch_rsvp')",
                    (task_id, act_id),
                )
                feed._conn.execute("UPDATE user_activity SET processed = 1 WHERE id = ?", (act_id,))
                feed._conn.commit()
        except Exception as exc:
            log.debug("Could not link task in activity pod: %s", exc)

        return {
            "status": "ok",
            "task_id": task_id,
            "path": promoted["path"],
            "reminders_sync": promoted.get("reminders_sync"),
        }

    def get_dispatches_by_binder(self, binder_id: str) -> List[Dict[str, Any]]:
        """Find all dispatches associated with a specific binder."""
        results: List[Dict[str, Any]] = []
        if not self.root_dir.exists():
            return results

        for child in self.root_dir.iterdir():
            if child.is_dir():
                manifest_path = child / "dispatch.json"
                if manifest_path.exists():
                    try:
                        m = json.loads(manifest_path.read_text(encoding="utf-8"))
                        if m.get("binder_id") == binder_id:
                            # Attach response count
                            resps = self.get_responses(m["id"])
                            m["response_count"] = len(resps)
                            results.append(m)
                    except Exception:
                        pass
        # Sort newest first
        results.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return results

    def list_dispatches(self) -> List[Dict[str, Any]]:
        """List all dispatches sorted newest first."""
        results: List[Dict[str, Any]] = []
        if not self.root_dir.exists():
            return results

        for child in self.root_dir.iterdir():
            if child.is_dir():
                manifest_path = child / "dispatch.json"
                if manifest_path.exists():
                    try:
                        m = json.loads(manifest_path.read_text(encoding="utf-8"))
                        resps = self.get_responses(m["id"])
                        m["response_count"] = len(resps)
                        results.append(m)
                    except Exception:
                        pass
        results.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return results

    def get_dispatch(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        """Get dispatch record and source markdown by dispatch ID."""
        dispatch_dir = self.root_dir / dispatch_id
        manifest_path = dispatch_dir / "dispatch.json"
        if not manifest_path.exists():
            return None
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            story_path = dispatch_dir / "originals" / "source.story.md"
            story_md = story_path.read_text(encoding="utf-8") if story_path.exists() else ""
            return {
                "dispatch": manifest,
                "story_markdown": story_md,
            }
        except Exception:
            return None

    def load_catalog(self) -> Dict[str, Any]:
        """Load curated standard element library from global-knowledge."""
        catalog_path = settings.public_vault_root / "global-knowledge" / "elements" / "catalog.json"
        if catalog_path.exists():
            try:
                return json.loads(catalog_path.read_text(encoding="utf-8"))
            except Exception as exc:
                log.warning("Could not read element catalog: %s", exc)

        # Fallback empty catalog
        return {
            "title": "uDos Curated Standard Element Library",
            "version": "1.0.0",
            "categories": {"cards": [], "bobs": [], "dividers": []},
        }


# Global singleton
dispatch_store = DispatchStore()

