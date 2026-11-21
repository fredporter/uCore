"""Preferences and assistant capabilities derived from the active uDOS profile."""

from app.identity.story_store import IdentityStoryStore

PREFERENCE_KEY = "ok_assistant"
MODEL_ROLES = {"owner", "wizard", "sorcerer", "sorceror", "knight", "user", "developer"}


def assistant_capabilities(identity: dict) -> dict[str, bool]:
    signed_in = bool(identity.get("authenticated") and identity.get("active_profile_id"))
    role = str((identity.get("active_profile") or {}).get("role", "")).strip().casefold()
    return {
        "local_input": True,
        "edit_preferences": signed_in,
        "local_models": signed_in and role in MODEL_ROLES,
        "manage_models": signed_in and role in {"owner", "wizard"},
    }


def preferences(owner: str) -> dict:
    value = IdentityStoryStore(profile_id=owner).get_variables().get(PREFERENCE_KEY)
    value = value if isinstance(value, dict) else {}
    return {
        "verbose": value.get("verbose") is True,
        "chat_mode": "ollama" if value.get("chat_mode") == "ollama" else "offline",
        "model": value["model"] if isinstance(value.get("model"), str) else "",
    }


def save_preferences(owner: str, value: dict) -> None:
    IdentityStoryStore(profile_id=owner).update_variables({PREFERENCE_KEY: value})
