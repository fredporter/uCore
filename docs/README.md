# uCore Documentation

**Active docs live here.** Historical and superseded docs are in [`docs/archive/`](archive/).

Target product authority: [September 12 refactor plan](UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md). Existing [Zen contract](ZEN_ECOSYSTEM_CONTRACT.md) is retained with a supersession scope notice.

## Active Runbooks

| Doc                                                                                      | Purpose                           |
| ---------------------------------------------------------------------------------------- | --------------------------------- |
| [MCP_SETUP.md](MCP_SETUP.md)                                                             | Build and configure `udos-mcp`    |
| [USER_SETUP_VAULT_MCP_WORKSPACES.md](USER_SETUP_VAULT_MCP_WORKSPACES.md)                 | Vault and workspace setup         |

## Active System Specs

| Doc                                                                    | Purpose                          |
| ---------------------------------------------------------------------- | -------------------------------- |
| [SNACKS_SYSTEM_SPEC.md](SNACKS_SYSTEM_SPEC.md)                         | Snackbar / system snacks catalog |
| [SPOOL_SPEC.md](SPOOL_SPEC.md)                                         | Spool logging and activity feed  |
| [MCP_VAULT_ALIGNMENT_ASSESSMENT.md](MCP_VAULT_ALIGNMENT_ASSESSMENT.md) | MCP/vault alignment              |
| [CLIPBOARD_POPOVER_SURFACE.md](CLIPBOARD_POPOVER_SURFACE.md)           | Clipboard popover surface        |
| [ADDENDUM_MAC_CLIPBOARD_BUFFER.md](ADDENDUM_MAC_CLIPBOARD_BUFFER.md)   | macOS clipboard buffer           |

## Grid / uCode Architecture

| Doc                                                              | Purpose                                        |
| ---------------------------------------------------------------- | ---------------------------------------------- |
| [UCORE_UCODE_ROLE_BOUNDARY.md](UCORE_UCODE_ROLE_BOUNDARY.md)     | uCore (host) vs uCode (runtime) ownership split |
| [GRIDUI_RENDERING_CONTRACT_v3.md](GRIDUI_RENDERING_CONTRACT_v3.md) | Pixel-exact rendering contract + 5 surface tabs |
| [GRID_ALGEBRA_COLUMN_SPECS.md](GRID_ALGEBRA_COLUMN_SPECS.md)     | Responsive grid column algebra                 |
| [specs/GRIDCORE_VARIABLEIZATION_SPEC.md](specs/GRIDCORE_VARIABLEIZATION_SPEC.md) | `--gridcore-*` variable contract |

## Current Frontend / UI Specs

| Doc                                                                      | Purpose                       |
| ------------------------------------------------------------------------ | ----------------------------- |
| [BANGLE_EDITOR_USER_GUIDE.md](BANGLE_EDITOR_USER_GUIDE.md)               | Bangle markdown authoring user guide |
| [COMPONENT_ARCHITECTURE_GUIDE.md](COMPONENT_ARCHITECTURE_GUIDE.md)       | Frontend/backend architecture and USX design system |
| [USX_LAYOUT_SYSTEM_SPEC.md](USX_LAYOUT_SYSTEM_SPEC.md)                   | USX layout system             |
| [FONT_SIZING_STANDARDS.md](FONT_SIZING_STANDARDS.md)                     | Font sizing standards         |
| [FILEPICKER_SIDEBAR_SPEC.md](FILEPICKER_SIDEBAR_SPEC.md)                 | Filepicker sidebar            |
| [FILEPICKER_INTEGRATION_STATUS.md](FILEPICKER_INTEGRATION_STATUS.md)     | Filepicker integration status |
| [SURFACE_OWNERSHIP.md](SURFACE_OWNERSHIP.md)                             | Canonical route and tab ownership |
| [UDOS_HOME_MIGRATION.md](UDOS_HOME_MIGRATION.md)                         | Runtime/vault boundary and safe migration |
| [ECOSYSTEM_STORAGE_ARCHITECTURE.md](ECOSYSTEM_STORAGE_ARCHITECTURE.md)   | Canonical storage, credentials and drift controls |
| [WORKSTATION_MIGRATION_2026-08-18.md](WORKSTATION_MIGRATION_2026-08-18.md) | Migration record, verification and rollback boundary |

## Product refactor and Gemini handover

Start with the [Gemini handover — 12 September 2026](HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md) and [complete product refactor plan](UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md).

This is separation and completion of existing products, not another rebuild. Preserve useful features and the emerging UI. After a fresh Code-folder assessment, develop and release from individual repositories. Groovebox is a music production suite; uVector generates/standardises coherent illustrations; HomeNest can optionally expose existing Home Assistant controls.

Internal IDE/Dev Mode plans are superseded. Their preserved evidence is indexed in the [development archive](archive/superseded-development-2026-09-12/README.md). Existing architecture/runbook documents describe the current implementation unless reconciled with the new plan; they do not authorize resuming the old development program.

Retained integration references: [DocLang export](DOCLANG_BRIDGE_EXPORT_SPEC.md) and [terminal/teletext work tag](TERMINAL_TELETEXT_GRID_WORK_TAG.md).

## Task ownership

- `uFlow` — canonical workflow and task owner (`$UDOS_HOME/flow/tasks`)

## Archive

See [`docs/archive/`](archive/) for completed milestones, deprecated runbooks, and historical handovers.

## Local-first execution planning

The [product refactor plan](UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md) owns the future local-first, bounded-execution and publishing direction. Earlier execution proposals are preserved in the [development archive](archive/superseded-development-2026-09-12/README.md) for reusable safeguards and evidence, not as active Dev Mode policy.
