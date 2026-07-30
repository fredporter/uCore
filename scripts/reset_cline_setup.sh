#!/usr/bin/env bash
set -euo pipefail

# Reset Cline config with backups. Default mode preserves API secrets.
# Use --full to also archive and clear secrets.

FULL_RESET="false"
if [[ "${1:-}" == "--full" ]]; then
  FULL_RESET="true"
fi

CLINE_DIR="$HOME/.cline"
DATA_DIR="$CLINE_DIR/data"
BACKUP_ROOT="$CLINE_DIR/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

mkdir -p "$BACKUP_DIR"
mkdir -p "$DATA_DIR"

backup_if_exists() {
  local src="$1"
  if [[ -f "$src" ]]; then
    cp "$src" "$BACKUP_DIR/$(basename "$src")"
  fi
}

backup_if_exists "$CLINE_DIR/mcp_settings.json"
backup_if_exists "$DATA_DIR/globalState.json"
if [[ "$FULL_RESET" == "true" ]]; then
  backup_if_exists "$DATA_DIR/secrets.json"
fi

rm -f "$DATA_DIR/globalState.json"
if [[ "$FULL_RESET" == "true" ]]; then
  rm -f "$DATA_DIR/secrets.json"
fi

cat > "$CLINE_DIR/mcp_settings.json" <<'JSON'
{
  "mcpServers": {
    "uCore": {
      "command": "node",
      "args": [
        "$HOME/Code/uDev/mcp-bridge/build/index.js"
      ],
      "env": {
        "UCORE_URL": "http://127.0.0.1:8484"
      },
      "description": "uCore MCP stdio bridge",
      "disabled": false,
      "alwaysAllow": [
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
        "ucore_list_repos"
      ]
    }
  }
}
JSON

if [[ ! -f "$HOME/Code/uDev/mcp-bridge/build/index.js" ]]; then
  echo "WARN: MCP bridge missing at $HOME/Code/uDev/mcp-bridge/build/index.js"
fi

echo "Cline reset complete"
echo "Backup: $BACKUP_DIR"
echo "Full reset: $FULL_RESET"
