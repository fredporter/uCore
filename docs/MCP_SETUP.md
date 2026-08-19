> Canonical runbook is in uDocs; this local copy reflects only the active implementation.

# uCore MCP Setup

uCore exposes one self-hosted MCP stdio server. External developer
clients may connect to it, but their configuration is not part of uCore.

## Canonical MCP Server

- Server id: udos-mcp
- Source: backend/app/mcp/udos_mcp
- Command: node backend/app/mcp/udos_mcp/build/index.js
- Env: UCORE_URL=http://127.0.0.1:8484

The gateway advertises six bounded read-only tools: system health, repository
list/status, workflow task list, knowledge search, and GridSmith tool list.

## Start Sequence

```bash
cd /Users/fredbook/Code/uCore
pnpm run dev:backend
cd /Users/fredbook/Code/uCore/backend/app/mcp/udos_mcp && npm ci
```

## Diagnostics

```bash
cd /Users/fredbook/Code/uCore/backend/app/mcp/udos_mcp
npm test
```

Expected checks:

- the official MCP client initializes the compiled stdio server
- the exact read-only tool catalogue is advertised
- calls reach the expected owned API routes
- invalid input is rejected by the SDK schema
