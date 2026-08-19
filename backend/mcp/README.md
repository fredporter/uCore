# uCore MCP

Canonical implementation uses one self-hosted MCP stdio gateway:

- Server id: `udos-mcp`
- Source: `backend/app/mcp/udos_mcp/`
- Command: `node backend/app/mcp/udos_mcp/build/index.js`
- Backend target: `UCORE_URL=http://127.0.0.1:8484`

Client-specific MCP configuration is external. uCore does not depend on an
editor-owned configuration directory. The old multi-manifest layout is retired.

## Diagnostics

```bash
cd backend/app/mcp/udos_mcp && npm test
```

This compiles the gateway and exercises it through the official MCP client.
The remaining scripts in this directory are legacy migration targets and are
not MCP servers in the canonical architecture.
