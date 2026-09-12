"""Persistent story-form and profile-variable storage for udos-identity."""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _default_data_file() -> Path:
    override = os.environ.get("UDOS_IDENTITY_DATA_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    udos_home = os.environ.get("UDOS_HOME", "").strip()
    if udos_home:
        return Path(udos_home).expanduser() / "identity-story.json"
    default_udos = Path.home() / "Code" / ".udos"
    if default_udos.exists():
        return default_udos / "identity-story.json"
    return Path.home() / ".local" / "share" / "udos" / "identity-story.json"


class IdentityStoryStore:
    """JSON-backed store for profile variables and story progression."""

    def __init__(self, data_file: Path | None = None) -> None:
        self.data_file = data_file or _default_data_file()

    def _load(self) -> dict[str, Any]:
        if not self.data_file.exists():
            return {"variables": {}, "stories": {}, "privacy": {}}
        try:
            payload = json.loads(self.data_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"variables": {}, "stories": {}, "privacy": {}}
        if not isinstance(payload, dict):
            return {"variables": {}, "stories": {}, "privacy": {}}
        payload.setdefault("variables", {})
        payload.setdefault("stories", {})
        payload.setdefault("privacy", {})
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.data_file.with_suffix(f"{self.data_file.suffix}.tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.data_file)

    def get_variables(self) -> dict[str, Any]:
        variables = self._load().get("variables", {})
        return dict(variables) if isinstance(variables, dict) else {}

    def update_variables(self, updates: dict[str, Any]) -> dict[str, Any]:
        payload = self._load()
        variables = payload.get("variables", {})
        if not isinstance(variables, dict):
            variables = {}
        variables.update(updates)
        payload["variables"] = variables
        self._save(payload)
        return dict(variables)

    def create_story(self, form_id: str, responses: dict[str, Any]) -> dict[str, Any]:
        payload = self._load()
        stories = payload.get("stories", {})
        if not isinstance(stories, dict):
            stories = {}

        now = datetime.now(UTC).isoformat()
        story_id = str(uuid.uuid4())
        story = {
            "id": story_id,
            "form_id": form_id,
            "status": "draft",
            "step": 0,
            "responses": responses,
            "created_at": now,
            "updated_at": now,
        }
        stories[story_id] = story
        payload["stories"] = stories
        self._save(payload)
        return dict(story)

    def get_story(self, story_id: str) -> dict[str, Any] | None:
        stories = self._load().get("stories", {})
        if not isinstance(stories, dict):
            return None
        story = stories.get(story_id)
        return dict(story) if isinstance(story, dict) else None

    def update_story(
        self,
        story_id: str,
        *,
        step: int | None = None,
        status: str | None = None,
        responses: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        payload = self._load()
        stories = payload.get("stories", {})
        if not isinstance(stories, dict):
            return None
        story = stories.get(story_id)
        if not isinstance(story, dict):
            return None

        if step is not None:
            story["step"] = step
        if status is not None:
            story["status"] = status
        if responses:
            current = story.get("responses", {})
            if not isinstance(current, dict):
                current = {}
            current.update(responses)
            story["responses"] = current
        story["updated_at"] = datetime.now(UTC).isoformat()
        stories[story_id] = story
        payload["stories"] = stories
        self._save(payload)
        return dict(story)

    def set_privacy(
        self,
        resource_id: str,
        *,
        visibility: str,
        expires_at: str | None,
    ) -> dict[str, Any]:
        payload = self._load()
        policies = payload.get("privacy", {})
        if not isinstance(policies, dict):
            policies = {}
        policy = {
            "resource_id": resource_id,
            "visibility": visibility,
            "expires_at": expires_at,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        policies[resource_id] = policy
        payload["privacy"] = policies
        self._save(payload)
        return self._evaluate_privacy(policy)

    def get_privacy(self, resource_id: str) -> dict[str, Any]:
        policies = self._load().get("privacy", {})
        if not isinstance(policies, dict):
            policies = {}
        policy = policies.get(resource_id)
        if not isinstance(policy, dict):
            policy = {
                "resource_id": resource_id,
                "visibility": "private",
                "expires_at": None,
                "updated_at": None,
            }
        return self._evaluate_privacy(policy)

    @staticmethod
    def _evaluate_privacy(policy: dict[str, Any]) -> dict[str, Any]:
        expires_at = policy.get("expires_at")
        expired = False
        if isinstance(expires_at, str) and expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=UTC)
                expired = expiry <= datetime.now(UTC)
            except ValueError:
                expired = True
        visibility = str(policy.get("visibility", "private"))
        return {
            **policy,
            "expired": expired,
            "effective_visibility": "private" if expired else visibility,
            "share_active": visibility != "private" and not expired,
        }
