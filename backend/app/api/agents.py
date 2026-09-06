"""Agents compatibility API.

Provides a stable `agent-router`-like schema for frontend tabs while the
standalone router service is not deployed. Merges config agents from
agents.yaml with dynamic skill/tool registrations.
"""
from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import yaml
from aiohttp import web

from app.services.spool_reader import read_spool
from app.skills.registry import list_skills
from app.tools.registry import list_tools


def _load_config_agents() -> list[dict]:
    """Read the canonical agent registry; configuration is not runtime activity."""
    from app.services.agent_specialization import SpecializedAgentRegistry
    return [{"id": agent.id, "name": agent.name, "capabilities": agent.capabilities,
             "status": "configured", "load": None, "costPerTask": agent.cost_per_task,
             "avgLatencyMs": None, "successRate": None, "provider": agent.provider,
             "model": agent.model, "description": agent.description,
             "config": True, "kind": "agent"}
            for agent in SpecializedAgentRegistry().list_agents()]


def _skill_to_agent(skill: dict) -> dict:
    category = str(skill.get("category") or "skill")
    skill_id = str(skill.get("id") or "unknown-skill")
    name = str(skill.get("name") or skill_id)
    return {
        "id": skill_id,
        "name": name,
        "capabilities": [category],
        "status": "online",
        "load": "0/1",
        "costPerTask": 0.0,
        "avgLatencyMs": 0,
        "successRate": 1.0,
        "kind": "skill",
    }


def _tool_to_agent(tool: dict) -> dict:
    tool_id = str(tool.get("id") or "unknown-tool")
    name = str(tool.get("name") or tool_id)
    installed = bool(tool.get("installed", False))
    status = "online" if installed else "offline"
    capability = str(tool.get("category") or "tool")
    return {
        "id": tool_id,
        "name": name,
        "capabilities": [capability],
        "status": status,
        "load": "0/1",
        "costPerTask": 0.0,
        "avgLatencyMs": 0,
        "successRate": 1.0,
        "kind": "tool",
    }


async def handle_list_agents(request: web.Request) -> web.Response:
    """GET /api/agents.

    Merge config agents (agents.yaml) with dynamic skills and tools.
    """
    skills = list_skills()
    tools = await list_tools()
    config_agents = _load_config_agents()

    agents: list[dict] = []
    # Config agents first (highest priority)
    agents.extend(config_agents)
    # Then skills and tools
    agents.extend(_skill_to_agent(skill) for skill in skills)
    agents.extend(_tool_to_agent(tool.model_dump()) for tool in tools)

    return web.json_response({
        "agents": agents,
        "count": len(agents),
    })


async def handle_agents_stats(request: web.Request) -> web.Response:
    """GET /api/agents/stats.

    Derive light-weight stats from spool activity.
    """
    entries = read_spool(max_entries=200)

    by_agent: Counter[str] = Counter()
    by_capability: Counter[str] = Counter()
    total_errors = 0
    recent_routes: list[dict] = []

    for entry in entries:
        if entry.level in ("ERROR", "CRITICAL"):
            total_errors += 1

        module = entry.module or "unknown"
        by_agent[module] += 1

        if entry.tags:
            for tag in entry.tags:
                by_capability[tag] += 1
        else:
            by_capability["general"] += 1

        recent_routes.append({
            "task": entry.message,
            "agent": module,
            "capability": entry.tags[0] if entry.tags else "general",
            "timestamp": entry.timestamp,
        })

    return web.json_response({
        "totalRouted": len(entries),
        "totalErrors": total_errors,
        "byAgent": dict(by_agent),
        "byCapability": dict(by_capability),
        "recentRoutes": recent_routes[:25],
    })
