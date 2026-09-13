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
        expires_in_seconds: Optional[int] = None,
        burn_after_read: bool = False,
        mode_default: str = "card",
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
            "view_count": 0,
            "status": "active",
        }

        (dispatch_dir / "dispatch.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (dispatch_dir / "responses.json").write_text("[]", encoding="utf-8")

        # Update token index
        tokens = self._load_tokens()
        tokens[token] = dispatch_id
        self._save_tokens(tokens)

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


# Global singleton
dispatch_store = DispatchStore()
