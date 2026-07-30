# uCore MCP

Canonical implementation uses one MCP JSON-RPC stdio bridge:

- Server id: `ucore-bridge`
- Config source: `.vscode/mcp.json`
- Command: `node ../uDev/mcp-bridge/build/index.js`
- Backend target: `UCORE_URL=http://127.0.0.1:8484`

The old multi-manifest MCP layout is deprecated.

## Diagnostics

```bash
cd backend && python3 -m mcp.mcp_diagnostics
```

This validates:

- `.vscode/mcp.json` exists
- `ucore-bridge` is declared
- no HTTP-type MCP servers are configured
- bridge binary exists at `../uDev/mcp-bridge/build/index.js`
