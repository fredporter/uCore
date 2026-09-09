"""Identity Module — uDos Identity System
=======================================
Every running instance needs a unique identity so services, surfaces, and skills
know who they're talking to.

Concepts:
  - User ID: Auto-generated uDos format ID (UDOS-YYYYMMDD-XXXXXX)
    Unique per device, generated once. Stable across restarts.
  - Codeword: Local human-readable name for network identification.
  - Installation ID: Which device/instance, e.g. "macbook-pro-m1"
  - Session ID: Current running session (ephemeral), auto-generated at server start
  - Profiles: Local sovereign profiles to prevent cross-user data leaks

Storage:
  - settings.data_dir / "identity.json" — Machine ID + Profiles + Codeword
  - settings.data_dir / "session.json" — Current session state

Spec: UDN-IDENTITY-API-001
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import settings

log = logging.getLogger("ucore.identity")


def _identity_file() -> Path:
    return settings.data_dir / "identity.json"


def _session_file() -> Path:
    return settings.data_dir / "session.json"


def generate_udos_id() -> str:
    """Generate a uDos format User ID:
      UDOS-YYYYMMDD-XXXXXX

    Where XXXXXX is a 6-char hex fingerprint derived from hostname + machine.
    Deterministic for a given device.
    """
    today = datetime.now(UTC).strftime("%Y%m%d")
    hostname = socket.gethostname().lower()
    machine = __import__("platform").machine().lower()
    fingerprint = hashlib.sha256(f"{hostname}-{machine}".encode()).hexdigest()[:6].upper()
    return f"UDOS-{today}-{fingerprint}"


def generate_install_id() -> str:
    """Generate an installation ID from hostname + platform + machine."""
    import platform as _platform

    hostname = socket.gethostname().lower().replace(" ", "-")
    machine = _platform.machine().lower()
    system = _platform.system().lower()
    unique_suffix = uuid.uuid5(uuid.NAMESPACE_DNS, f"{hostname}-{machine}-{system}").hex[:8]
    return f"{hostname}-{machine}-{unique_suffix}"


# ─── Data Classes ───────────────────────────────────────────────────────

class Profile:
    """A distinct local user profile to ensure complete data isolation."""

    def __init__(self, id: str = "default", name: str = "Local User", role: str = "owner"):
        self.id = id
        self.name = name
        self.role = role

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name, "role": self.role}

    @classmethod
    def from_dict(cls, data: dict) -> Profile:
        return cls(
            id=data.get("id", "default"),
            name=data.get("name", "Local User"),
            role=data.get("role", "owner"),
        )


class Identity:
    """Persistent identity — User ID + Codeword + Installation ID + Profiles."""

    def __init__(
        self,
        user_id: str = "",
        codeword: str = "",
        install_id: str = "",
        active_profile_id: str = "default",
        profiles: list[Profile] | None = None,
        authenticated: bool = True,
    ):
        self.user_id = user_id
        self.codeword = codeword
        self.install_id = install_id
        self.active_profile_id = active_profile_id
        self.authenticated = authenticated
        if profiles:
            self.profiles = profiles
        else:
            default_name = codeword or "Local User"
            self.profiles = [Profile(id="default", name=default_name, role="owner")]

    @property
    def active_profile(self) -> Profile | None:
        if not self.authenticated:
            return None
        for p in self.profiles:
            if p.id == self.active_profile_id:
                return p
        return self.profiles[0] if self.profiles else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "codeword": self.codeword,
            "install_id": self.install_id,
            "active_profile_id": self.active_profile_id,
            "authenticated": self.authenticated,
            "profiles": [p.to_dict() for p in self.profiles],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Identity:
        raw_profiles = data.get("profiles", [])
        profiles = [Profile.from_dict(p) for p in raw_profiles] if raw_profiles else None
        return cls(
            user_id=data.get("user_id", ""),
            codeword=data.get("codeword", ""),
            install_id=data.get("install_id", ""),
            active_profile_id=data.get("active_profile_id", "default"),
            profiles=profiles,
            authenticated=data.get("authenticated", True),
        )

    def is_valid(self) -> bool:
        return bool(self.user_id) and bool(self.install_id)


class Session:
    """Ephemeral session — created at server start and tied to active profile."""

    def __init__(
        self,
        session_id: str = "",
        started_at: str = "",
        active_profile_id: str = "default",
        authenticated: bool = True,
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.started_at = started_at or datetime.now(UTC).isoformat()
        self.active_profile_id = active_profile_id
        self.authenticated = authenticated

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "active_profile_id": self.active_profile_id,
            "authenticated": self.authenticated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        return cls(
            session_id=data.get("session_id", ""),
            started_at=data.get("started_at", ""),
            active_profile_id=data.get("active_profile_id", "default"),
            authenticated=data.get("authenticated", True),
        )


# ─── Load / Save ────────────────────────────────────────────────────────

def _find_legacy_identity_file() -> Path | None:
    """Check for migration from earlier storage locations."""
    candidates = [
        settings.udos_home / "identity.json",
        settings.udos_home / "config" / "identity.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def load_identity() -> Identity:
    primary = _identity_file()
    if primary.exists():
        try:
            return Identity.from_dict(json.loads(primary.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Failed to parse identity file %s: %s", primary, exc)

    legacy = _find_legacy_identity_file()
    if legacy and legacy.exists():
        try:
            ident = Identity.from_dict(json.loads(legacy.read_text(encoding="utf-8")))
            save_identity(ident)
            return ident
        except (json.JSONDecodeError, OSError):
            pass

    return Identity()


def save_identity(identity: Identity) -> bool:
    target = _identity_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(identity.to_dict(), indent=2), encoding="utf-8")
        temp.replace(target)
        return True
    except OSError as exc:
        log.error("Failed to save identity: %s", exc)
        if temp.exists():
            temp.unlink(missing_ok=True)
        return False


def load_session() -> Session | None:
    session_file = _session_file()
    if not session_file.exists():
        return None
    try:
        return Session.from_dict(json.loads(session_file.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def save_session(session: Session) -> bool:
    session_file = _session_file()
    session_file.parent.mkdir(parents=True, exist_ok=True)
    temp = session_file.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
        temp.replace(session_file)
        return True
    except OSError as exc:
        log.error("Failed to save session: %s", exc)
        if temp.exists():
            temp.unlink(missing_ok=True)
        return False


def create_session(active_profile_id: str = "default", authenticated: bool = True) -> Session:
    return Session(
        session_id=str(uuid.uuid4()),
        started_at=datetime.now(UTC).isoformat(),
        active_profile_id=active_profile_id,
        authenticated=authenticated,
    )


def get_or_create_session() -> Session:
    session = load_session()
    if not session:
        ident = load_identity()
        session = create_session(
            active_profile_id=ident.active_profile_id or "default",
            authenticated=ident.authenticated,
        )
        save_session(session)
    return session


# ─── Public API ─────────────────────────────────────────────────────────

def get_full_identity() -> dict[str, Any]:
    """Return the complete identity info for API responses and log tagging."""
    import platform as _platform

    identity = ensure_identity()
    session = get_or_create_session()
    active_profile = identity.active_profile.to_dict() if identity.active_profile else None
    return {
        "user_id": identity.user_id,
        "codeword": identity.codeword,
        "install_id": identity.install_id,
        "session_id": session.session_id,
        "started_at": session.started_at,
        "authenticated": identity.authenticated and session.authenticated,
        "active_profile_id": identity.active_profile_id if (identity.authenticated and session.authenticated) else "",
        "active_profile": active_profile,
        "profiles": [p.to_dict() for p in identity.profiles],
        "hostname": socket.gethostname(),
        "platform": _platform.system().lower(),
        "platform_version": _platform.version(),
        "machine": _platform.machine(),
    }


def ensure_identity() -> Identity:
    """Ensure identity exists, auto-initializing if needed."""
    identity = load_identity()
    if not identity.is_valid():
        default_codeword = os.environ.get("USER", "uCore")
        identity = Identity(
            user_id=generate_udos_id(),
            codeword=default_codeword,
            install_id=generate_install_id(),
            active_profile_id="default",
            profiles=[Profile(id="default", name=default_codeword, role="owner")],
            authenticated=True,
        )
        save_identity(identity)
    return identity


def switch_profile(profile_id: str) -> dict[str, Any]:
    """Switch active profile, updating identity and session."""
    identity = ensure_identity()
    matching = [p for p in identity.profiles if p.id == profile_id]
    if not matching:
        new_profile = Profile(id=profile_id, name=profile_id.capitalize(), role="developer" if profile_id == "developer" else "guest")
        identity.profiles.append(new_profile)

    identity.active_profile_id = profile_id
    identity.authenticated = True
    save_identity(identity)

    session = create_session(active_profile_id=profile_id, authenticated=True)
    save_session(session)
    return get_full_identity()


def logout() -> dict[str, Any]:
    """Clear active session and enter unauthenticated state."""
    identity = ensure_identity()
    identity.authenticated = False
    save_identity(identity)

    session = create_session(active_profile_id="", authenticated=False)
    save_session(session)
    return get_full_identity()


def login(profile_id: str = "default") -> dict[str, Any]:
    """Log in to a specified profile."""
    return switch_profile(profile_id)


def update_profile(profile_id: str, name: str | None = None, role: str | None = None) -> dict[str, Any]:
    """Update profile metadata or add a new profile."""
    identity = ensure_identity()
    target = None
    for p in identity.profiles:
        if p.id == profile_id:
            target = p
            break
    if not target:
        target = Profile(id=profile_id, name=name or profile_id, role=role or "user")
        identity.profiles.append(target)
    else:
        if name:
            target.name = name
        if role:
            target.role = role
    save_identity(identity)
    return get_full_identity()
