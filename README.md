# uCore — Unified Development OS

[![Python](https://img.shields.io/badge/Python-3.12-blue)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-green)]()
[![Tests](https://img.shields.io/badge/Tests-301%20passing-brightgreen)]()

uCore is a **local-first, AI-powered development daemon** that unifies syntax, automation, and runtime management.

**Port:** 8484 | **Stack:** Python 3.12 + aiohttp + SQLite + Vue 3 + TypeScript

## Quick Start

### First Time on macOS (Fresh System)

```bash
curl -fsSL https://raw.githubusercontent.com/uDosGo/uCore/main/scripts/bootstrap.sh | bash
```

This installs Homebrew, Python 3.12, Node.js 22, pnpm, clones uCore, and starts everything.

The installer also validates and syncs locked vendor modules for a consistent
uDos experience (SnackMachine core, udos-agents, udos-budget, udos-identity).

### Already Have Prerequisites

```bash
git clone https://github.com/uDosGo/uCore.git
cd uCore
./scripts/setup.sh
```

### Vendor Module Lock (Deterministic)

```bash
# Refresh lock metadata from vendor/sources.yaml and validate
./scripts/vendor_sync.sh --refresh-lock --check

# Install locked Python vendor modules
source .venv/bin/activate
./scripts/vendor_sync.sh --install-python --check
```

### Verify

```bash
curl http://localhost:8484/api/health
# Look for 🍿 in the macOS menu bar
# Frontend: http://localhost:5175
```

### Uninstall

```bash
./scripts/install.sh --uninstall
```

## Architecture

uCore is the **host platform core**. Optional capabilities — workflow,
knowledge, and domain plugins — live in dedicated repos and plug in via
a lightweight extension contract.

```
VS Code (Cline) → MCP Bridge → uCore (port 8484)
  │
  ├── Core shell (uCore host-only)
  │   ├── Skills (15 built-in) — backup, sync, route, ask vault
  │   ├── Secrets — AES-256-GCM encrypted store
  │   ├── Chat — AI providers via OpenRouter/Ollama/Gemini
  │   ├── Surfaces (10) — Dashboard, Assistant, Server, Developer,
  │   │                    System, Workflow, SnackMachine, BrowserUI,
  │   │                    Documentation, uCode
  │   ├── Plates — Vault plates, surface templates (Cookiecutter)
  │   ├── Hivemind — MCP orchestration, template verification, audit
  │   ├── TOON Context Optimization — Token-optimized context encoding
  │   └── Flow-LLM Router — Cost-optimized routing with analytics
  │
  ├── Extension Registry (plugin contract)
  │   ├── Discovery — scans for ucore-extension.json manifests
  │   ├── Loading — imports and calls setup(app) on each extension
  │   └── Routing — delegates /api/* prefixes to extensions
  │
  ├── Adaptable (moving to dedicated repos)
  │   ├── uFlow — workflow engine, runs, logs, task orchestration
  │   └── uKnowledge — AppFlowy SQLite + vector DB bridge
  │
  └── Plugins (udos-* prefix)
      └── HomeNest/modules/home-ops/udos-home — starter domain plugin module

→ Roundtable MCP → parallel Claude/Gemini/OpenRouter execution
```

## Repositories

| Repo           | Kind          | Purpose                                    | Location            |
| -------------- | ------------- | ------------------------------------------ | ------------------- |
| **uCore**      | host/core     | Platform daemon + extension registry       | `~/Code/uCore`      |
| **uFlow**      | workflow      | Workflow engine, runs, logs, tasks         | `~/Code/uFlow`      |
| **uKnowledge** | knowledge     | AppFlowy bridge, semantic search, indexing | `~/Code/uKnowledge` |
| **uCode**      | runtime       | Base runtime and core grid/code foundation | `~/Code/uCode`      |
| **uCode2**     | runtime       | Advanced runtime layer (later extension)   | `~/Code/uCode2`     |
| **HomeNest**   | plugin (udos) | Home automation + app-layer runtime        | `~/Code/HomeNest`   |
| **uDocs**      | docs          | Canonical documentation                    | GitHub              |

## Editor Strategy

- Dedicated AppFlowy customization inside uCore is deprecated.
- Vault content should remain portable and work in standard editors such as
  AppFlowy and Obsidian without uCore-specific lock-in.
- Primary editing focus is moving to the Bangle.io fork for first-class
  in-product document workflows.
- Task flows should link to markdown specs/docs when deeper implementation
  details are required.

> During the repo split, uCore keeps **routing adapters**
> (`app.extensions.adapters/`) as import bridges only.
> Missing required external repos must fail fast.

## Surfaces (10)

| Surface       | Route                | Description                                                           |
| ------------- | -------------------- | --------------------------------------------------------------------- |
| Dashboard     | `/`                  | Main landing, Dev Mode filtering                                      |
| Assistant     | `/assistui`          | AI chat & agent-assisted workflows                                    |
| Server        | `/server`            | Server management                                                     |
| Developer     | `/developer`         | Developer tools                                                       |
| System        | `/system`            | System settings                                                       |
| Workflow      | `/workflow`          | Workflow builder                                                      |
| SnackMachine  | `/server?tab=snacks` | Core snack workspace (packaged snacks via SnackMachine extension)     |
| BrowserUI     | `/browserui`         | Browser automation                                                    |
| Documentation | `/documentation`     | Docs viewer                                                           |
| uCode         | `/ucode`             | uCode runtime bridge: GridCore, GridSmith, teletext, terminal widgets |

## Documentation

Canonical docs live in **[uDocs](https://github.com/uDosGo/uDocs)**:

| Section                                                                                   | Description                            |
| ----------------------------------------------------------------------------------------- | -------------------------------------- |
| [Architecture](https://github.com/uDosGo/uDocs/blob/main/architecture/overview.md)        | System topology, data flow, security   |
| [API Reference](https://github.com/uDosGo/uDocs/blob/main/api/rest-api.md)                | All endpoints with examples            |
| [Runbooks](https://github.com/uDosGo/uDocs/blob/main/runbooks/development.md)             | Setup, deploy, backup, troubleshooting |
| [Surfaces](https://github.com/uDosGo/uDocs/tree/main/surfaces)                            | All 12 surfaces                        |
| [Cline Guide](https://github.com/uDosGo/uDocs/blob/main/guides/cline-roundtable-setup.md) | Cline + Roundtable orchestration       |

Local docs in `docs/` cover vault plates, USX layout, and system specs.

## Key Endpoints

```bash
curl http://localhost:8484/api/health          # Health check
curl http://localhost:8484/api/skills          # 15 skills
curl http://localhost:8484/api/tools           # 7 tools
curl http://localhost:8484/api/models          # 4 providers
curl http://localhost:8484/api/secrets         # Encrypted store
curl http://localhost:8484/api/mcp/tools       # MCP tools
curl http://localhost:8484/api/knowledge/workspaces  # Vault workspace bridge
```

## Status

- **301 backend tests** — all passing
- **0 TypeScript errors** — clean build
- **15 built-in skills** — auto-discovered
- **4 AI providers** — Ollama, OpenRouter, Claude, Gemini
- **12 surfaces** — Vue 3 + USX layout system
- **Plates system** — Vault plates, surface templates, destroy patterns

## License

Apache 2.0 — see LICENSE.
