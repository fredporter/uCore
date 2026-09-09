"""Settings Manager — Scoped configuration backed by UDOS_HOME.

Provides unified management for global, user (profile-scoped), developer,
and surface configuration with atomic writes and offline resilience.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.settings import settings

log = logging.getLogger("ucore.settings")

_DEFAULT_SETTINGS: dict[str, Any] = {
    "global": {
        "theme": "dark",
        "fontSize": 16,
        "palette": "default",
    },
    "user": {
        "displayName": "uDos Developer",
        "email": "",
        "defaultModel": "Llama 3.2",
    },
    "users": {},
    "developer": {
        "diagnostics": True,
        "formatOnSave": False,
        "showHiddenFiles": False,
    },
    "surface": {
        "sidebarOpen": True,
        "tabOrientation": "horizontal",
    },
}


class SettingsManager:
    """Manages scoped settings stored under settings.data_dir."""

    def __init__(self, path: Path | None = None):
        self.path = path or (settings.data_dir / "system_settings.json")
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save(_DEFAULT_SETTINGS)

    def _load(self) -> dict[str, Any]:
        self._ensure_store()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Failed reading settings from %s: %s", self.path, exc)
        return dict(_DEFAULT_SETTINGS)

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        try:
            temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            temp.replace(self.path)
        except OSError as exc:
            log.error("Failed saving settings to %s: %s", self.path, exc)
            if temp.exists():
                temp.unlink(missing_ok=True)

    def get_all(self, profile_id: str = "default") -> dict[str, Any]:
        """Return all settings merged with active profile-scoped user settings."""
        data = self._load()
        result = dict(data)
        users = data.get("users", {})
        if profile_id and profile_id in users:
            result["user"] = {**data.get("user", {}), **users[profile_id]}
        return result

    def get_scope(self, scope: str, profile_id: str = "default") -> dict[str, Any]:
        """Get settings for a specific scope."""
        all_data = self.get_all(profile_id=profile_id)
        return dict(all_data.get(scope, {}))

    def update_scope(self, scope: str, values: dict[str, Any], profile_id: str = "default") -> dict[str, Any]:
        """Update a specific settings scope."""
        data = self._load()
        if scope == "user" and profile_id and profile_id != "default":
            data.setdefault("users", {})
            data["users"].setdefault(profile_id, {})
            data["users"][profile_id].update(values)
        else:
            data.setdefault(scope, {})
            data[scope].update(values)

        self._save(data)
        return self.get_all(profile_id=profile_id)

    def get_user_preferences(self, profile_id: str = "default") -> dict[str, Any]:
        """Get preferences for the active profile."""
        all_data = self.get_all(profile_id=profile_id)
        prefs = all_data.get("preferences", {})
        users = all_data.get("users", {})
        if profile_id and profile_id in users and "preferences" in users[profile_id]:
            return dict(users[profile_id]["preferences"])
        return dict(prefs)

    def update_user_preferences(self, preferences: dict[str, Any], profile_id: str = "default") -> dict[str, Any]:
        """Update user preferences for the active profile."""
        allowed = {"themeMode", "fontStyle", "fontSize", "palette", "defaultModel"}
        filtered = {k: v for k, v in preferences.items() if k in allowed}
        data = self._load()
        if profile_id and profile_id != "default":
            data.setdefault("users", {})
            data["users"].setdefault(profile_id, {})
            current = data["users"][profile_id].get("preferences", {})
            current.update(filtered)
            data["users"][profile_id]["preferences"] = current
            self._save(data)
            return current
        else:
            current = data.get("preferences", {})
            current.update(filtered)
            data["preferences"] = current
            self._save(data)
            return current


_instance: SettingsManager | None = None


def get_settings_manager() -> SettingsManager:
    global _instance
    if _instance is None:
        _instance = SettingsManager()
    return _instance
