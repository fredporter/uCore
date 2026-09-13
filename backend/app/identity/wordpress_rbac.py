"""WordPress-Compatible Role-Based Access Control (RBAC) and Sovereign User Store.

Implements standard WordPress roles and granular capabilities backed by
sovereign local JSON storage under UDOS_HOME/identity/users.json.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.services.identity import get_full_identity

log = logging.getLogger("ucore.identity.rbac")

# Standard WordPress Roles and Default Capabilities
ROLE_CAPABILITIES: dict[str, set[str]] = {
    "administrator": {
        "manage_options",
        "manage_users",
        "manage_taxonomies",
        "publish_posts",
        "edit_posts",
        "edit_others_posts",
        "delete_posts",
        "delete_others_posts",
        "read_private_posts",
        "read",
        "read_public",
    },
    "editor": {
        "manage_taxonomies",
        "publish_posts",
        "edit_posts",
        "edit_others_posts",
        "delete_posts",
        "delete_others_posts",
        "read_private_posts",
        "read",
        "read_public",
    },
    "author": {
        "publish_posts",
        "edit_posts",
        "delete_posts",
        "read",
        "read_public",
    },
    "contributor": {
        "edit_posts",
        "delete_posts",
        "read",
        "read_public",
    },
    "subscriber": {
        "read",
        "read_public",
    },
    "guest": {
        "read_public",
    },
}

VALID_ROLES = set(ROLE_CAPABILITIES.keys())


def _hash_secret(secret: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{secret}".encode("utf-8")).hexdigest()
    return digest, salt


def _verify_secret(secret: str, salt: str, expected_hash: str) -> bool:
    digest, _ = _hash_secret(secret, salt)
    return secrets.compare_digest(digest, expected_hash)


class WordPressUserStore:
    """Sovereign local store for users with WordPress-standard roles."""

    def __init__(self, data_file: Path | None = None) -> None:
        self.data_file = data_file or (settings.udos_home / "identity" / "users.json")
        self._ensure_seed()

    def _load(self) -> dict[str, Any]:
        if not self.data_file.exists():
            return {"users": {}}
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("users", {})
                return data
        except (json.JSONDecodeError, OSError):
            pass
        return {"users": {}}

    def _save(self, data: dict[str, Any]) -> None:
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        temp = self.data_file.with_suffix(f"{self.data_file.suffix}.tmp")
        temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp.replace(self.data_file)

    def _ensure_seed(self) -> None:
        """Auto-seed default sovereign owner as administrator on first startup."""
        data = self._load()
        users = data.get("users", {})
        if not users:
            try:
                full_ident = get_full_identity()
                user_id = full_ident.get("user_id") or "admin"
                name = full_ident.get("codeword") or "Sovereign Administrator"
            except Exception:
                user_id = "admin"
                name = "Sovereign Administrator"

            now = datetime.now(UTC).isoformat()
            token = secrets.token_hex(24)
            hash_val, salt = _hash_secret(token)

            owner_user = {
                "id": user_id,
                "username": "admin",
                "display_name": name,
                "email": "owner@udos.local",
                "role": "administrator",
                "capabilities": sorted(ROLE_CAPABILITIES["administrator"]),
                "auth_hash": hash_val,
                "auth_salt": salt,
                "api_token": token,
                "meta": {
                    "udos_is_owner": True,
                    "udos_install_id": full_ident.get("install_id", "") if "full_ident" in locals() else "",
                },
                "created_at": now,
                "updated_at": now,
            }
            users[user_id] = owner_user
            data["users"] = users
            self._save(data)
            log.info("Seeded primary sovereign administrator: %s (%s)", user_id, name)

    def list_users(self, role: str | None = None) -> list[dict[str, Any]]:
        users = self._load().get("users", {})
        results: list[dict[str, Any]] = []
        for user in users.values():
            if not isinstance(user, dict):
                continue
            if role and user.get("role") != role:
                continue
            clean = dict(user)
            clean.pop("auth_hash", None)
            clean.pop("auth_salt", None)
            results.append(clean)
        return sorted(results, key=lambda u: u.get("display_name", ""))

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        users = self._load().get("users", {})
        user = users.get(user_id)
        if not isinstance(user, dict):
            return None
        clean = dict(user)
        clean.pop("auth_hash", None)
        clean.pop("auth_salt", None)
        return clean

    def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        if not token:
            return None
        users = self._load().get("users", {})
        for user in users.values():
            if isinstance(user, dict) and user.get("api_token") == token:
                clean = dict(user)
                clean.pop("auth_hash", None)
                clean.pop("auth_salt", None)
                return clean
        return None

    def create_user(
        self,
        username: str,
        display_name: str,
        email: str = "",
        role: str = "subscriber",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        role = role.lower()
        if role not in VALID_ROLES:
            role = "subscriber"

        data = self._load()
        users = data.get("users", {})
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        token = secrets.token_hex(24)
        hash_val, salt = _hash_secret(token)

        user = {
            "id": user_id,
            "username": username.strip().lower(),
            "display_name": display_name.strip() or username,
            "email": email.strip().lower(),
            "role": role,
            "capabilities": sorted(ROLE_CAPABILITIES.get(role, set())),
            "auth_hash": hash_val,
            "auth_salt": salt,
            "api_token": token,
            "meta": meta or {},
            "created_at": now,
            "updated_at": now,
        }
        users[user_id] = user
        data["users"] = users
        self._save(data)

        clean = dict(user)
        clean.pop("auth_hash", None)
        clean.pop("auth_salt", None)
        return clean

    def update_user(
        self,
        user_id: str,
        *,
        display_name: str | None = None,
        email: str | None = None,
        role: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        data = self._load()
        users = data.get("users", {})
        user = users.get(user_id)
        if not isinstance(user, dict):
            return None

        if display_name is not None:
            user["display_name"] = display_name.strip()
        if email is not None:
            user["email"] = email.strip().lower()
        if role is not None:
            r = role.lower()
            if r in VALID_ROLES:
                user["role"] = r
                user["capabilities"] = sorted(ROLE_CAPABILITIES.get(r, set()))
        if meta:
            current_meta = user.get("meta", {})
            if not isinstance(current_meta, dict):
                current_meta = {}
            current_meta.update(meta)
            user["meta"] = current_meta

        user["updated_at"] = datetime.now(UTC).isoformat()
        users[user_id] = user
        data["users"] = users
        self._save(data)

        clean = dict(user)
        clean.pop("auth_hash", None)
        clean.pop("auth_salt", None)
        return clean

    def delete_user(self, user_id: str) -> bool:
        data = self._load()
        users = data.get("users", {})
        if user_id in users:
            # Protect primary owner
            user = users[user_id]
            if isinstance(user, dict) and user.get("meta", {}).get("udos_is_owner"):
                return False
            del users[user_id]
            data["users"] = users
            self._save(data)
            return True
        return False

    def has_capability(self, user_or_id: dict[str, Any] | str, capability: str) -> bool:
        if isinstance(user_or_id, str):
            user = self.get_user(user_or_id)
        else:
            user = user_or_id
        if not user or not isinstance(user, dict):
            # Guest check
            return capability in ROLE_CAPABILITIES["guest"]
        role = user.get("role", "subscriber")
        allowed = ROLE_CAPABILITIES.get(role, set())
        return capability in allowed


_DEFAULT_USER_STORE: WordPressUserStore | None = None


def get_user_store(data_file: Path | None = None) -> WordPressUserStore:
    global _DEFAULT_USER_STORE
    if data_file is not None:
        return WordPressUserStore(data_file)
    if _DEFAULT_USER_STORE is None:
        _DEFAULT_USER_STORE = WordPressUserStore()
    return _DEFAULT_USER_STORE


def get_current_user(request: Any, store: WordPressUserStore | None = None) -> dict[str, Any]:
    """Resolve current user from HTTP request headers or session."""
    user_store = store or get_user_store()
    headers = getattr(request, "headers", {})

    # Explicit role or guest override for testing / anonymous requests
    if headers.get("X-Udos-User") == "guest" or headers.get("X-Udos-Role") == "guest" or headers.get("X-Anonymous"):
        return {
            "id": "guest",
            "username": "guest",
            "display_name": "Guest",
            "role": "guest",
            "capabilities": sorted(ROLE_CAPABILITIES["guest"]),
            "meta": {},
        }

    # 1. Bearer Token or X-Udos-User-Token
    auth_header = headers.get("Authorization", "").strip()
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = headers.get("X-Udos-User-Token", "").strip()
    if token:
        user = user_store.get_user_by_token(token)
        if user:
            return user
        # Provided invalid token -> unauthorized / guest
        return {
            "id": "guest",
            "username": "guest",
            "display_name": "Guest",
            "role": "guest",
            "capabilities": sorted(ROLE_CAPABILITIES["guest"]),
            "meta": {},
        }

    # 2. X-Udos-User ID header
    user_id = headers.get("X-Udos-User", "").strip()
    if user_id:
        user = user_store.get_user(user_id)
        if user:
            return user
        return {
            "id": "guest",
            "username": "guest",
            "display_name": "Guest",
            "role": "guest",
            "capabilities": sorted(ROLE_CAPABILITIES["guest"]),
            "meta": {},
        }

    # 3. Default to sovereign owner in local desktop environment
    try:
        full_ident = get_full_identity()
        owner_id = full_ident.get("user_id")
        if owner_id:
            user = user_store.get_user(owner_id)
            if user:
                return user
        for u in user_store.list_users():
            if u.get("meta", {}).get("udos_is_owner"):
                return u
    except Exception:
        pass

    return {
        "id": "guest",
        "username": "guest",
        "display_name": "Guest",
        "role": "guest",
        "capabilities": sorted(ROLE_CAPABILITIES["guest"]),
        "meta": {},
    }
