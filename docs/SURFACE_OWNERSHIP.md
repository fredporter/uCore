# uCore Surface Ownership

**Status:** Canonical  
**Updated:** 2026-08-18

This is the current UI Hub surface contract. Current routes and components take
precedence over historical feature plans. Superseded plans remain evidence, but
must not be used to recreate retired tabs.

## Canonical surfaces

| Surface | Route | Owns |
| --- | --- | --- |
| Dashboard | `/` | Navigation and ecosystem overview |
| Developer | `/developer` | Repositories, file preview, editing, diff and Git actions |
| Intelligence | `/intelligence` | Chat, planning, models, agents, budget decisions and history |
| Snackbar | `/snackbar` | Service health, feeds, skills, snacks, extensions, logs and MCP |
| System | `/system` | System pages, variables, secrets, global and user settings |
| Workflow | `/workflow` | User missions, tasks, automation, document editing and publishing |
| uCode | `/ucode` | Terminal, teletext, pixel, grid, layer and glyph runtime tools |
| Documentation | `/documentation` | Documentation and published knowledge |

## Developer boundary

Developer is deliberately a small repository tool with three tabs: Code,
Repository and Editor. It does not own models, agents, budgets, services, feeds,
skills, extensions, logs, MCP, missions or user tasks.

The historical `udev` identifier may remain temporarily in saved extension
state and compatibility APIs. It refers to the built-in Developer surface; it
does not identify a separately installable repository or server.

## Workflow boundary

uFlow is the canonical workflow and task engine. uCore owns the Vue Workflow
surface and delegates persistence and execution through the uFlow extension
contract. uCore Tasker files are migration/development adapters, not a second
user workflow engine.

## Compatibility routes

- `/assistui/*` redirects to `/intelligence`.
- `/server/*` redirects to `/snackbar/*`.
- `/teletext/*` and `/terminal/*` redirect to their uCode tabs.
- `/snackmachine?tab=mcp` redirects to `/snackbar?tab=mcp`.

New code and documentation must use canonical routes.

## Duplicate presentation

Some operational data can be summarized on more than one surface, but it has
one owner:

- Intelligence owns agent use, model selection and budget decisions.
- Snackbar may show agent process health and budget alerts.
- `udos-budget` owns budget policy and persistence once its extension contract
  replaces the current in-core implementation.
