# uCore

uCore is the sovereign, local-first host application and desktop companion for the uDos ecosystem.
It provides a calm Vue 3 UI shell, governed backend APIs, native Obsidian vault indexing, task and workflow orchestration, and clean edition publishing.

**September 2026 Refactor:** In-browser IDE/Dev Mode has been decommissioned. External software development is conducted in Google Antigravity (AGY) and Codex. uCore is focused purely on user productivity, notebook binders, daily automations, and domain application hosting.

## Architecture & Ownership

| Component / Subsystem | Location in uCore | Responsibilities |
| --- | --- | --- |
| **uCore Shell & Host** | `frontend-vue` | Calm USX UI shell, Mission Control, Snackbar assistant, and document edition review |
| **uFlow Engine** | `backend/app/flow/` | Built-in durable missions, tasks, daily routines, autonomy, and execution evidence |
| **uKnowledge Library** | `backend/app/knowledge/` | Built-in filesystem-first vault discovery, indexing, search, and Obsidian baseline (`~/Vault`, `~/Shared`, `~/Public`) |
| **Sovereign Identity** | `backend/app/identity/` | Local profiles, keys, and headless WordPress RBAC mapping (`wordpress_mapper.py`) |
| **Network & Privacy** | `uCore-Network` | Spec: Offline local portals, BitChat LAN P2P chat, and home privacy stack |
| **Google & DreamBeans** | `uCore-Google` | Google Workspace bridge + DreamBeans autonomous morning briefing integration |

Independent domain products (`SonicScrewdriver`, `Groovebox`, `uVector`, `HomeNest`) follow an uncoupled, independent release path.

## Workspace & Storage Boundary (AGENTS.md)

- **Repository Source:** `~/Code/<repo>`
- **Mutable Ecosystem State:** `UDOS_HOME` (default `~/Code/.udos`)
- **User Documents:** `~/Vault` (User), `~/Shared` (Shared), and `~/Public` (Public)
- **External Engineering:** Antigravity IDE, `agy` CLI, and standard MCP servers (`mcp-server-git`, `mcp-filesystem`).
- **Policy Enforcement:** Run `python3 scripts/check_home_path_policy.py` before committing.

## Development & Running

Required baseline: macOS, Python 3.12, Node.js 22+, and pnpm 9+.

```bash
git clone https://github.com/uDosGo/uCore.git
cd uCore
./scripts/setup.sh

# backend: http://localhost:8484
pnpm dev:backend

# frontend: http://localhost:5175
pnpm dev
```

## Verification

```bash
pnpm build
pnpm test
pnpm lint
python3 scripts/check_home_path_policy.py
```

## Documentation

- [Product Refactor Plan](docs/UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md)
- [Product Refactor Handover](docs/HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md)
- [uCore-Network Architecture Spec](docs/UCORE_NETWORK_SPEC_2026.md)
- [Component Architecture Guide](docs/COMPONENT_ARCHITECTURE_GUIDE.md)
- [Surface Ownership](docs/SURFACE_OWNERSHIP.md)

## License

Apache 2.0 — see [LICENSE](LICENSE).
