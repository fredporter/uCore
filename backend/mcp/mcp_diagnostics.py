"""MCP diagnostics for the canonical uCore stdio bridge setup.

Source of truth:
  - Workspace config: .vscode/mcp.json
  - Bridge binary: discovered from multiple candidate paths (uDev retired,
    bridge may live in uCore itself or a sibling repo)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _mcp_config_path() -> Path:
    return _repo_root() / ".vscode" / "mcp.json"


def _load_mcp_config() -> dict[str, Any]:
    path = _mcp_config_path()
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return {"error": "mcp_config_not_object", "path": str(path)}
        return data
    except Exception as exc:
        return {"error": f"mcp_config_unreadable: {exc}", "path": str(path)}


def _get_servers() -> dict[str, Any]:
    data = _load_mcp_config()
    if "error" in data:
        return {}
    servers = data.get("servers", {})
    return servers if isinstance(servers, dict) else {}


def list_servers() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, cfg in _get_servers().items():
        if not isinstance(cfg, dict):
            continue
        rows.append(
            {
                "name": name,
                "type": cfg.get("type", ""),
                "command": cfg.get("command", ""),
                "args": cfg.get("args", []),
                "cwd": cfg.get("cwd", ""),
            }
        )
    return rows


def list_tools() -> list[str]:
    """Static tool names exposed by the canonical uCore bridge."""
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


def health() -> dict[str, Any]:
    repo_root = _repo_root()
    mcp_path = _mcp_config_path()
    servers = _get_servers()

    has_ucore_bridge = "ucore-bridge" in servers
    stale_http = [
        name
        for name, cfg in servers.items()
        if isinstance(cfg, dict) and cfg.get("type") == "http"
    ]

    # Discover bridge binary — uDev has been retired, check multiple candidates.
    candidates = [
        repo_root / "bmcp" / "mcp-bridge" / "build" / "index.js",
        repo_root.parent / "uDev" / "mcp-bridge" / "build" / "index.js",
    ]
    bridge_bin = None
    for cand in candidates:
        if cand.exists():
            bridge_bin = cand
            break
    if bridge_bin is None:
        bridge_bin = candidates[0]  # report the first candidate for diagnostics

    checks = {
        "mcp_config_exists": mcp_path.exists(),
        "ucore_bridge_declared": has_ucore_bridge,
        "no_http_servers": len(stale_http) == 0,
        "bridge_binary_exists": bridge_bin.exists(),
    }
    ok = all(checks.values())

    return {
        "health": "ok" if ok else "degraded",
        "checks": checks,
        "stale_http_servers": stale_http,
        "servers": list_servers(),
        "tool_count": len(list_tools()),
    }


if __name__ == "__main__":
    print(json.dumps(health(), indent=2))
