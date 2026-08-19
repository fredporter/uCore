# User Setup Guide: Vault Integration, MCP, and Workspace Switching

This guide provides steps for setting up and integrating Vault, MCP, and
workspace switching with uCore.

## Prerequisites

*   **uCore Installation**: Ensure uCore is installed and running. Refer to the main README for installation instructions.
*   **Vault directories**: uCore reads `~/Vault` (master user vault), `~/Shared` (shared vaults), and `~/Public` (public vaults). Create them if missing.
*   **MCP Server**: Ensure MCP servers (e.g., Firewatch) are installed and configured if needed. Refer to MCP documentation for setup.
*   **Zen Browser**: Recommended UI shell for development and automation.
*   **Playwright**: Automation driver for Zen Browser and other headless tasks.

## 1. Vault Integration

### 1.1. Vault Layout

uCore manages three vault layers:

| Layer   | Path       | Purpose                       |
|---------|------------|-------------------------------|
| user    | `~/Vault`  | Master personal vault (one)   |
| shared  | `~/Shared` | Shared team vaults            |
| public  | `~/Public` | Public/published vaults       |

### 1.2. Running Vault Sync

You can trigger a manual index rebuild with:

```bash
cline --yolo "Run Vault sync"
```

This runs the `vault_sync` skill, which scans the three vault layers into
the FTS5 index at `~/.ucore/indices/library.db`. Scheduled syncs run daily.

## 2. MCP Integration

### 2.1. Canonical Gateway

uCore provides one local stdio gateway, `udos-mcp`. Build and test it using
[`MCP_SETUP.md`](MCP_SETUP.md). The MCP host launches the gateway; it is not an
always-running uCore HTTP service.

External MCP servers are configured directly in the client that owns them. They
are not proxied, registered, or supervised by uCore.

### 2.2. Using MCP Tools

MCP tools are accessed through an MCP client using the stdio command documented
in `MCP_SETUP.md`.

There is no `/api/mcp/*` compatibility facade.

## 3. Workspace Switching

Additional workspaces (any folder under `~/Shared` or `~/Public`) can be
registered through the vault API so they appear alongside the three built-in
layers in the sidebar and knowledge tools.

1.  **List workspaces**: `GET /api/knowledge/workspaces`
2.  **Register a workspace**: `POST /api/vault/workspaces` with `{name, path}`
3.  **Rebuild the index**: run the `vault_sync` skill after registering.

## 4. Integrating with Automation Tools

Use the existing skills (`vault_sync`, `tasker_sync`, `brain_sync`) directly
instead of third-party sync tools. Workflow automation uses the canonical
uFlow and uKnowledge APIs.

## 5. Scheduling Automation

Schedule the `vault_sync` skill with the maintenance scheduler (built-in) or a
system scheduler:

*   **macOS/Linux**: Use `cron` jobs or the built-in maintenance scheduler.
*   **Windows**: Use Task Scheduler.

Example `cron` entry to run a daily index rebuild at 4:00 AM:

```cron
0 4 * * * /Users/you/Code/uCore/.venv/bin/python -m app.skills.builtin.vault_sync >> /var/log/ucore_vault_sync.log 2>&1
```

## 6. Zen Browser and Playwright for Development

Zen Browser, recommended as the UI shell, works seamlessly with Playwright for automation.

### 6.1. Zen Browser Setup

1.  **Install Zen Browser**:
    *   macOS: `brew install zen-browser`
    *   Linux: Download from zen-browser.com
2.  **Install Playwright Browsers**:
    ```bash
    npx playwright install firefox
    # or for Python:
    # playwright install firefox
    ```

### 6.2. Playwright Automation

Playwright can be used to control Zen Browser for various development tasks:

*   **Navigation and Interaction**: Automate browser actions like visiting pages, clicking elements, and filling forms.
*   **Console Log Capture**: Capture logs for debugging.
*   **Data Extraction**: Extract text content, HTML, or perform evaluations.

Refer to `docs/ZEN_PLAYWRIGHT_AUTOMATION_TOOLCHAIN.md` for detailed examples and advanced usage.

---

**Last Updated**: 2026-06-22T21:45:00+08:00
**Session**: Phase 9B Developer wiring and endpoint verification
**Status**: Ready for user setup documentation completion.
