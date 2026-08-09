"""Unified executable registry — Skills + Snack plugins as one concept.

Consolidated model (2026-08-08): Skills == Snacks == executable script
containers. This module presents a single, merged list of executables with a
shared shape so the UI can render skills and snack plugins side by side and
run either through one endpoint.
"""
from __future__ import annotations

import logging
from typing import Any

from app.menu.system_snacks import list_system_snacks, run_system_snack
from app.skills.registry import list_skills, run_skill_by_id

log = logging.getLogger("ucore.executables")


def list_executables() -> list[dict[str, Any]]:
    """Merge backend skills + system snack plugins into one list."""
    exes: list[dict[str, Any]] = []

    # ── Skills — backend capabilities ────────────────────────────
    for skill in list_skills():
        exes.append({
            "id": skill["id"],
            "name": skill["name"],
            "description": skill["description"],
            "category": skill["category"],
            "kind": "skill",
            "icon": "extension",
            "enabled": True,
            "requires_confirmation": bool(skill.get("requires_confirmation")),
            "actions": [],
        })

    # ── Snack plugins — menu-bar/system executable containers ────
    for snack in list_system_snacks():
        kind = str(snack.get("kind") or "action")
        exes.append({
            "id": snack["id"],
            "name": snack["name"],
            "description": f"System snack ({kind})",
            "category": "snacks",
            "kind": "snack",
            "icon": snack.get("icon") or "restaurant_menu",
            "enabled": True,
            "requires_confirmation": False,
            "actions": list(snack.get("actions") or []),
        })

    return exes


def get_executable(exe_id: str) -> dict[str, Any] | None:
    for exe in list_executables():
        if exe["id"] == exe_id:
            return exe
    return None


async def run_executable(
    exe_id: str,
    action: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run an executable by id, dispatching to skill.run or snack.execute."""
    exe = get_executable(exe_id)
    if not exe:
        return {"success": False, "error": f"Executable '{exe_id}' not found"}

    if exe["kind"] == "skill":
        return await run_skill_by_id(exe_id, **kwargs)

    # Snack plugins are synchronous; run in a thread to avoid blocking the loop.
    import asyncio
    from functools import partial
    return await asyncio.to_thread(
        partial(run_system_snack, exe_id, action),
    )
