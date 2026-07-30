> Canonical runbook is in uDocs; this local copy reflects only the active implementation.

# uCore MCP Setup

uCore now uses one MCP JSON-RPC stdio server in workspace config.

## Canonical MCP Server

- Config file: .vscode/mcp.json
- Server id: ucore-bridge
- Command: node ../uDev/mcp-bridge/build/index.js
- Env: UCORE_URL=http://127.0.0.1:8484

## Start Sequence

```bash
cd /Users/fredbook/Code/uCore
pnpm run dev:backend
cd /Users/fredbook/Code/uDev/mcp-bridge && npm run build
```

## Diagnostics

```bash
cd /Users/fredbook/Code/uCore/backend
python3 -m mcp.mcp_diagnostics
```

Expected checks:

- .vscode/mcp.json exists
- ucore-bridge is declared
- no HTTP MCP servers exist in active config
- bridge binary exists
