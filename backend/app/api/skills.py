"""Skills API — execute governed internal uDos capabilities.

POST /api/skills/{skill_id}/run — execute a skill by ID
POST /api/skills/run — run a skill by directory path
"""
from __future__ import annotations

import logging

from aiohttp import web

from app.services.health import get_health_summary
from app.skills.registry import get_skill, run_skill_by_id
from app.skills.state import read_state

log = logging.getLogger("ucore.skills")

async def handle_run_skill(request: web.Request) -> web.Response:
    """POST /api/skills/{skill_id}/run — execute a skill by ID.

    Body (optional): { "args": [...], "env": {...}, "timeout": 60 }
    Returns: { "stdout": "...", "stderr": "...", "exit_code": 0 }
    """
    skill_id = request.match_info.get("skill_id", "")
    return await _run_skill_by_id(skill_id, request)


async def handle_run_named_skill(request: web.Request) -> web.Response:
    """POST /api/skills/run — run a skill by path/name.

    Body: { "skill": "skill-name", "args": [...], "timeout": 60 }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    skill_name = body.get("skill", "").strip()
    if not skill_name:
        return web.json_response({"error": "skill name is required"}, status=400)

    return await _run_skill_by_id(skill_name, request, body)


async def _run_skill_by_id(
    skill_id: str, request: web.Request, body: dict | None = None,
) -> web.Response:
    """Internal: find and execute a skill (tries Python registry first)."""
    if body is None:
        try:
            body = await request.json() if request.body_exists else {}
        except Exception:
            body = {}

    # Try Python skill registry first (for builtin skills)
    skill = get_skill(skill_id)
    if skill:
        # Merge params dict with top-level body keys (for flexibility)
        kwargs = body.get("params", {})
        if isinstance(kwargs, dict):
            for k, v in body.items():
                if k != "params":
                    kwargs.setdefault(k, v)
        else:
            kwargs = body
        # Enforce confirmation for skills that require explicit user approval
        requires_confirm = getattr(skill.meta, "requires_confirmation", False) or skill.meta.category in ("mutating", "destructive", "write")
        # Confirmation can be provided via JSON body {"confirm": true} or header X-User-Confirm: true
        confirmed = False
        if (isinstance(body, dict) and body.get("confirm") is True) or request.headers.get("X-User-Confirm", "").lower() == "true":
            confirmed = True

        if requires_confirm and not confirmed:
            return web.json_response({
                "error": "Skill requires explicit confirmation. Re-submit with {\"confirm\": true} in the body or header 'X-User-Confirm: true'.",
                "skill_id": skill_id,
                "requires_confirmation": True,
            }, status=403)

        result = await run_skill_by_id(
            skill_id,
            execution_authorized=confirmed,
            **kwargs,
        )
        # Broadcast completion to SSE subscribers
        try:
            from app.api.render_api import publish_event
            from app.services.render import render_markdown
            payload = result if isinstance(result, dict) else {"result": str(result)}
            payload["skill"] = skill_id
            publish_event("skill_complete", {**payload, "rendered": render_markdown(payload)})
        except Exception:
            pass
        return web.json_response(result)

    return web.json_response({"error": f"Skill '{skill_id}' not found"}, status=404)


async def handle_list_skills(request: web.Request) -> web.Response:
    """GET /api/skills — list all available skills."""
    from app.skills.registry import list_skills as ls
    skills = ls()
    # Sort by category priority, then by name
    skills.sort(key=lambda s: (s.get("category_priority", 7), s.get("name", "")))
    return web.json_response({"skills": skills, "count": len(skills)})


async def handle_skill_source(request: web.Request) -> web.Response:
    """GET /api/skills/{skill_id}/source — return skill source code for editor viewing."""
    skill_id = request.match_info.get("skill_id", "")

    # Try Python registry (builtin skills are .py files)
    skill = get_skill(skill_id)
    if skill:
        try:
            import inspect
            source = inspect.getsource(type(skill))
            return web.json_response({
                "skill_id": skill_id,
                "source": source,
                "language": "python",
                "filename": f"{skill_id}.py",
            })
        except (OSError, TypeError):
            pass

    return web.json_response({"error": f"Skill '{skill_id}' not found"}, status=404)


async def handle_skill_state(request: web.Request) -> web.Response:
    """GET /api/skills/state — return persisted skill run state."""
    try:
        state = read_state()
        return web.json_response({"state": state})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_health(request: web.Request) -> web.Response:
    try:
        summary = get_health_summary()
        return web.json_response({"health": summary})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
