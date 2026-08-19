> Canonical runbook is in uDocs; this local copy reflects only the active implementation.

# uCore MCP Setup

uCore exposes one self-hosted MCP JSON-RPC stdio server. External developer
clients may connect to it, but their configuration is not part of uCore.

## Canonical MCP Server

- Server id: ucore-bridge
- Source: backend/app/mcp/mcp_bridge
- Command: node backend/app/mcp/mcp_bridge/build/index.js
- Env: UCORE_URL=http://127.0.0.1:8484

## Start Sequence

```bash
cd /Users/fredbook/Code/uCore
pnpm run dev:backend
cd /Users/fredbook/Code/uCore/backend/app/mcp/mcp_bridge && npm run build
```

## Diagnostics

```bash
cd /Users/fredbook/Code/uCore/backend
python3 -m mcp.mcp_diagnostics
```

Expected checks:

- bridge source and package metadata exist
- the local bridge build exists
