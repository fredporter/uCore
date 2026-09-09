from __future__ import annotations

import asyncio
import importlib.util
import inspect
import json
import logging
import sys
from pathlib import Path

from app.skills.base import BaseSkill

log = logging.getLogger("ucore.skills.registry")
_registry: dict[str, BaseSkill] = {}
_loaded = False
BUILTIN_SKILL_PATH = Path(__file__).parent / "builtin"
CATALOGUE_PATH = Path(__file__).parent / "catalogue.json"


def _catalogue_modules() -> list[dict]:
    data = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    modules = data.get("modules")
    if data.get("version") != 1 or not isinstance(modules, list):
        raise RuntimeError("Invalid internal capability catalogue")
    required = {"module", "owner", "lifecycle", "risk", "lane", "allowed_roots"}
    for item in modules:
        if not isinstance(item, dict) or required - set(item):
            raise RuntimeError("Incomplete internal capability catalogue entry")
    names = [item["module"] for item in modules]
    if len(names) != len(set(names)):
        raise RuntimeError("Duplicate internal capability catalogue module")
    discovered = sorted(
        path.name
        for path in BUILTIN_SKILL_PATH.glob("*.py")
        if not path.name.startswith("_")
    )
    if sorted(names) != discovered:
        raise RuntimeError("Internal capability catalogue does not match builtin modules")
    return modules


def _discover():
    skills = {}
    sd = BUILTIN_SKILL_PATH
    if not sd.exists():
        return skills
    sys.path.insert(0, str(sd.parent))
    for entry in _catalogue_modules():
        f = sd / entry["module"]
        try:
            spec = importlib.util.spec_from_file_location(f"skills_{f.stem}", f)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                for _, obj in inspect.getmembers(mod):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseSkill)
                        and obj is not BaseSkill
                    ):
                        inst = obj()
                        inst._catalogue_entry = entry
                        skills[inst.meta.id] = inst
        except Exception as e:
            log.warning("Skill load fail %s: %s", f.name, e)
    sys.path.pop(0)
    return skills


def _ensure():
    global _registry, _loaded
    if not _loaded:
        _registry = _discover()
        _loaded = True


def list_skills() -> list[dict]:
    _ensure()
    return [
        {
            "id": s.meta.id,
            "name": s.meta.name,
            "description": s.meta.description,
            "category": s.meta.category,
            "timeout": s.meta.timeout,
            "requires_confirmation": getattr(s.meta, "requires_confirmation", False),
            "category_priority": _get_category_priority(s.meta.category),
        }
        for s in _registry.values()
    ]


def _get_category_priority(category: str) -> int:
    """Return priority for sorting categories in UI."""
    priorities = {
        "system": 1,
        "mutating": 2,
        "destructive": 3,
        "maintenance": 4,
        "surfaces": 5,
        "containers": 6,
        "general": 7,
    }
    return priorities.get(category, 7)


def get_skill(skill_id: str) -> BaseSkill | None:
    _ensure()
    return _registry.get(skill_id)


async def run_skill_by_id(
    skill_id: str,
    *,
    execution_authorized: bool = False,
    context: Any | None = None,
    **kwargs,
) -> dict:
    skill = get_skill(skill_id)
    if not skill:
        return {"success": False, "error": f"Skill '{skill_id}' not found"}

    catalogue_entry = getattr(skill, "_catalogue_entry", {})
    lane = catalogue_entry.get("lane")
    allowed_roots = catalogue_entry.get("allowed_roots", [])

    if context is not None:
        if getattr(context, "scope", "") == "user" and lane == "developer":
            return {
                "success": False,
                "error": f"Skill '{skill_id}' belongs to developer lane and is denied in user scope",
            }

    requires_confirmation = getattr(
        skill.meta, "requires_confirmation", False
    ) or skill.meta.category in ("mutating", "destructive", "write")
    if requires_confirmation and not execution_authorized:
        return {
            "success": False,
            "error": "Skill requires explicit execution authorization",
            "skill_id": skill_id,
            "requires_confirmation": True,
        }

    for key in ("path", "target", "target_dir", "root_dir"):
        val = kwargs.get(key)
        if val and isinstance(val, (str, Path)):
            p = str(val)
            if ".." in p:
                return {
                    "success": False,
                    "error": f"Path traversal in '{p}' is denied",
                }

    errors = skill.validate(**kwargs)
    if errors:
        return {"success": False, "errors": errors}

    timeout = getattr(skill.meta, "timeout", 60) or 60
    try:
        return await asyncio.wait_for(skill.run(**kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": f"Skill '{skill_id}' execution timed out after {timeout}s",
            "timeout": timeout,
        }
