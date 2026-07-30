#!/usr/bin/env python3
"""Validate canonical MCP workspace configuration.

Fails when active config drifts from the required stdio bridge model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    mcp_path = repo_root / ".vscode" / "mcp.json"
    bridge_path = repo_root.parent / "uDev" / "mcp-bridge" / "build" / "index.js"

    if not mcp_path.exists():
        fail(f"Missing MCP config: {mcp_path}")

    try:
        data = json.loads(mcp_path.read_text())
    except Exception as exc:
        fail(f"Invalid JSON in {mcp_path}: {exc}")

    if not isinstance(data, dict):
        fail("MCP config root must be an object")

    servers = data.get("servers")
    if not isinstance(servers, dict):
        fail("MCP config must contain object key: servers")

    if "ucore-bridge" not in servers:
        fail("Missing required MCP server: ucore-bridge")

    bridge = servers["ucore-bridge"]
    if not isinstance(bridge, dict):
        fail("ucore-bridge config must be an object")

    disallowed_http = [
        name
        for name, cfg in servers.items()
        if isinstance(cfg, dict) and cfg.get("type") == "http"
    ]
    if disallowed_http:
        fail(f"HTTP MCP servers are not allowed: {', '.join(disallowed_http)}")

    if bridge.get("type") != "stdio":
        fail("ucore-bridge type must be stdio")

    if bridge.get("command") != "node":
        fail("ucore-bridge command must be node")

    args = bridge.get("args")
    if args != ["../uDev/mcp-bridge/build/index.js"]:
        fail("ucore-bridge args must be exactly [\"../uDev/mcp-bridge/build/index.js\"]")

    env = bridge.get("env")
    if not isinstance(env, dict):
        fail("ucore-bridge env must be an object")

    if env.get("UCORE_URL") != "http://localhost:8484" and env.get("UCORE_URL") != "http://127.0.0.1:8484":
        fail("ucore-bridge env.UCORE_URL must be localhost:8484 or 127.0.0.1:8484")

    if not bridge_path.exists():
        print(f"[WARN] Bridge binary missing at {bridge_path} (run npm run build in uDev/mcp-bridge)")

    print("[OK] MCP config validated")


if __name__ == "__main__":
    main()
