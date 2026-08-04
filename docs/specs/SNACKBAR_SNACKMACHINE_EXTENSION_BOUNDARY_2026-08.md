# Snackbar and SnackMachine Boundary (2026-08)

## Decision

- Snackbar and Popcorn menu stay in uCore core runtime.
- SnackMachine moves to a separate extension repository.
- Core must remain useful without SnackMachine installed.

## Why

- Popcorn is the entry point to UI Hub and core surfaces.
- Snackbar owns daemon lifecycle, health, diagnostics, and routing.
- Snack packaging and catalog workflows can evolve faster as an extension.

## Core Responsibilities (uCore)

- Backend daemon bootstrap and health endpoints.
- Popcorn menu lifecycle and launchd integration.
- Surface navigation and service controls (backend/frontend/menu).
- Base snack APIs that are safe without external extension.
- Stable extension contract endpoints and capability checks.

## SnackMachine Extension Responsibilities

- Packaged snack catalog and install/uninstall lifecycle.
- Snack publishing templates and external snack bundles.
- Optional advanced snack UI and distribution workflows.
- Any extension-specific transports or channels.

## Install and Runtime Flow

1. User installs uCore.
2. Popcorn auto-starts with uCore and opens UI Hub routes.
3. User can install SnackMachine extension for packaged snacks.
4. Core detects extension presence and enables extension actions.

## Popcorn Menu Spec (Core)

- Header: uCore and environment status.
- Open UI Hub.
- Open Snacks Workspace (core route).
- Open Clipboard surface.
- Backend status row.
- Frontend status row.
- Start at Login toggle.
- Restart Backend.
- Restart Frontend.
- Restart Menu.
- Quit.

## Current Working Route Targets

- Open UI Hub -> / (UI Hub root).
- Open Snacks Workspace -> /server?tab=snacks.
- Open Clipboard -> /s310.

## Extension Presence UX

- If SnackMachine extension is not installed:
  - Show "Install SnackMachine Extension" action.
  - Keep core snack queue/status visible.
- If installed:
  - Show "Open SnackMachine Extension" action.
  - Show packaged snack management actions.

## Candidate Extension Assessment

### Keep Core

- MCP bridge runtime and routing:
  - Core orchestration and policy should remain in uCore.
- Feed/Spool substrate:
  - Core message/log transport and persistence should remain in uCore.
- Ollama provider wiring:
  - Provider abstractions and health checks should remain in uCore.
- Hivemind and Roundtable orchestration:
  - Core agent workflow graph and failover should remain in uCore.

### Good Extension Candidates

- Provider packs:
  - Extra model-provider adapters beyond baseline core providers.
- Surface packs:
  - Optional UI modules that are not required for startup/health.
- Workflow packs:
  - Domain-specific automations and templates.
- Snack packs:
  - Curated external snack bundles for specific ecosystems.

## Boundary Rule

If removing a module breaks:

- backend startup,
- health checks,
- menu startup,
- or opening core UI surfaces,

then it is core, not an extension.

## Next Steps

1. Create snackmachine-extension repository with packaging metadata.
2. Define extension capability handshake endpoint.
3. Add extension install status tile in Server/System surface.
4. Add extension-aware menu items in Popcorn.
