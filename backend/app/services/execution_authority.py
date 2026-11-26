"""Server-owned execution authority for skill entry points.

Every entry point derives the profile and scope from uCore's session identity.
Callers may request an operation; they never choose their own authority.
"""
from __future__ import annotations

from app.core.execution_context import ExecutionContext

DEVELOPER_ROLES = {"developer", "owner", "wizard"}
GUEST_ROLES = {"guest", ""}


def active_identity() -> dict:
    from app.services.identity import get_full_identity

    return get_full_identity() or {}


def active_profile(identity: dict | None = None) -> tuple[str, str]:
    """Return the server-resolved (profile_id, role) for this request."""
    identity = identity if identity is not None else active_identity()
    profile = identity.get("active_profile") or {}
    owner = str(identity.get("active_profile_id") or "default")
    role = str(profile.get("role") or "").lower()
    return owner, role


def scope_for_role(role: str) -> str:
    return "developer" if role in DEVELOPER_ROLES else "user"


def build_context(
    *,
    lane: str,
    surface: str,
    owner: str | None = None,
    role: str | None = None,
) -> ExecutionContext:
    """Build the context for a run; unresolved values come from the server identity."""
    if owner is None or role is None:
        resolved_owner, resolved_role = active_profile()
        owner = resolved_owner if owner is None else owner
        role = resolved_role if role is None else role
    scope = scope_for_role(role)
    return ExecutionContext(
        task_id=f"{surface}:{owner}",
        scope=scope,
        lane=lane,
        network_policy="local_only",
        provider_eligibility=(
            ["ollama"] if scope == "user" else ["ollama", "openrouter"]
        ),
        metadata={"profile": owner, "role": role, "surface": surface},
    )
