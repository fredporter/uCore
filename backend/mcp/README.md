# uCore MCP

Canonical implementation uses one self-hosted MCP JSON-RPC stdio bridge:

- Server id: `ucore-bridge`
- Source: `backend/app/mcp/mcp_bridge/`
- Command: `node backend/app/mcp/mcp_bridge/build/index.js`
- Backend target: `UCORE_URL=http://127.0.0.1:8484`

Client-specific MCP configuration is external. uCore does not depend on an
editor-owned configuration directory. The old multi-manifest layout is retired.

## Diagnostics

```bash
cd backend && python3 -m mcp.mcp_diagnostics
```

This validates:

- bridge source and package metadata exist
- the local bridge build exists
