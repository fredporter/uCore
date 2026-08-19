"""Diagnostics for uCore's self-hosted MCP bridge.

Client-specific configuration belongs to the external client. uCore owns the
bridge source, its package metadata, and the backend tool registry.
"""

from __future__ import annotations

import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _bridge_root() -> Path:
    return _repo_root() / "backend" / "app" / "mcp" / "mcp_bridge"


def list_tools() -> list[str]:
    """Static tool names exposed by the self-hosted bridge."""
    return [
        "ucore_ecosystem_audit",
        "ucore_list_skills",
        "ucore_run_skill",
        "ucore_surface_registry",
        "ucore_ollama_status",
        "ucore_list_agents",
        "ucore_chat",
        "ucore_search_knowledge",
        "ucore_autonomy_state",
        "ucore_list_secrets",
        "ucore_workflow_status",
        "ucore_config",
        "ucore_list_repos",
    ]


def health() -> dict[str, object]:
    bridge_root = _bridge_root()
    checks = {
        "bridge_source_exists": (bridge_root / "index.ts").exists(),
        "bridge_package_exists": (bridge_root / "package.json").exists(),
        "bridge_build_exists": (bridge_root / "build" / "index.js").exists(),
    }
    return {
        "health": "ok" if all(checks.values()) else "degraded",
        "checks": checks,
        "bridge_root": str(bridge_root),
        "tool_count": len(list_tools()),
        "client_configuration": "external",
    }


if __name__ == "__main__":
    print(json.dumps(health(), indent=2))
