# uCore

uCore is the local-first host application for the uDOS development ecosystem.
It provides the Vue shell, governed backend APIs, extension discovery, runtime
health, and the Developer surface used to work with repositories under
`~/Code`.

**Pre-release:** the architecture is being dogfooded directly from `main`; it is
not yet a public release or a compatibility target.

## Canonical ownership

| Repository | Owns |
| --- | --- |
| `uCore` | Host shell, Developer UI, governed capabilities, settings and extension loading |
| `uFlow` | Durable missions, tasks, workflows, approvals and execution evidence |
| `uKnowledge` | Vault discovery, search, indexing and knowledge APIs |
| `uCode` | GridCore, rendering packages, terminal/runtime and code primitives |

Domain projects and `udos-*` extensions remain independently owned. They may
integrate through the extension contract; their domain logic does not move into
uCore.

## Development

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

Enable Dev Mode from the uCore interface, then open
`http://localhost:5175/developer`. The Developer surface is deliberately small:

- **Code** — repository and file browsing;
- **Repository** — working-tree review, stage/unstage and commit;
- **Editor** — guarded file editing with diff review.

It also shows the current branch, open pull request and recent GitHub Actions
runs through the authenticated `gh` CLI. Remote mutations follow the explicit
branch → checks → pull request → merge sequence.

## Verification

```bash
pnpm build
pnpm test
pnpm lint
pnpm mcp:build
pnpm mcp:test
```

The official MCP implementation is `backend/app/mcp/udos_mcp`. It is a
self-hosted stdio gateway with six bounded read-only tools. It is not a second
orchestration, task, provider, or knowledge system.

## Architecture rules

- `~/Code` is the Developer lane; `~/Vault`, `~/Shared`, and `~/Public` are
  content lanes.
- GitHub is the remote source of truth. uFlow owns durable task and evidence
  state.
- Provider and budget decisions pass through one governed routing path.
- Capabilities are registered explicitly and fail closed; loose runtime scripts,
  fake users, compatibility shims and duplicated MCP facades are unsupported.
- `Vendor/` is local development research only. Useful components are forked
  into an active repository before becoming product dependencies.
- Required extensions fail clearly when unavailable; there are no hidden
  fallback implementations.

## Current documentation

- [Developer surface](docs/DEVELOPER_SURFACE.md)
- [Developer GitHub contract](docs/DEVELOPER_GITHUB_CONTRACT.md)
- [Extension registry](docs/EXTENSION_REGISTRY_SPEC.md)
- [MCP setup](docs/MCP_SETUP.md)
- [MCP architecture audit](docs/MCP_ARCHITECTURE_AUDIT_2026-08-19.md)
- [Surface ownership](docs/SURFACE_OWNERSHIP.md)
- [Repository ownership boundaries](docs/UCORE_UCODE_ROLE_BOUNDARY.md)

Historical plans and superseded experiments live under `docs/archive/`,
`docs/archived/`, and `docs/legacy/`; they are not implementation contracts.

## License

Apache 2.0 — see [LICENSE](LICENSE).
