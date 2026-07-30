# 📋 uCore Dev Plan — Tasker Boards

**Canonical Source:** `.tasker.dev-flow.yaml` (25 tasks: 20 maintenance, 5 UI)

This directory contains active tasker files. Completed tasks are archived to `.tasker.archived/`.

## Structure

| Directory  | Description                         |
| ---------- | ----------------------------------- |
| `backlog/` | Archived backlog items (superseded) |
| `phases/`  | Archived phase files (superseded)   |

## Template System

**Dev Mode templates:** `.dev/templates/` (default, fallback configurations)

## Recovery Scripts

**Reset scripts:** `.dev/scripts/`

- `backup-pre-reset.sh` — Backup before reset
- `reset-to-default.sh` — Full reset to template defaults
- `activate-openrouter-fallback.sh` — Emergency fallback activation

## MCP Integration

Use `tasker_devlog_bridge` skill for:

- `sync` — Sync .tasker with devlog.mcp.yaml and spool
- `read` — Read current tasker/devlog state
- `archive` — Archive completed tasks older than N days
- `purge` — Purge legacy completed documentation

## Capability Preflight Flow (Stop-The-Line)

For any feature task that depends on tools, plugins, repos, variables, or secrets:

1. Run capability preflight before implementation or runtime action.
2. If preflight fails (repair_required=true or HTTP 412), pause execution.
3. Complete listed repair actions (install, configure, set variable/secret, restart).
4. Re-run preflight and continue only when ready=true.
5. Include preflight output and repair evidence in task handover notes.
