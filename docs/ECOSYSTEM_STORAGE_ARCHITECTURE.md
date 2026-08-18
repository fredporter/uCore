<!-- path-policy: allow-literals -->
# Ecosystem Storage Architecture

**Status:** Canonical
**Updated:** 2026-08-18

## Ownership boundary

| Location | Owner | Lifecycle |
| --- | --- | --- |
| `~/Code/<repo>` | Git repositories | Clone, develop, archive independently |
| `~/Code/.udos` | uDOS runtime | Detachable and destructible as one unit |
| `~/Vault` | User | Primary private document vault |
| `~/Shared` | User/workspaces | Shared and add-on vaults |
| `~/Public` | User/publishing | Public and publishable documents |
| Standard credential paths | User and owning applications | Survive uDOS removal |

`UDOS_HOME` defaults to `~/Code/.udos`. It owns application configuration,
logs, indexes, caches, model data, container data, generated state, runtime
metadata, compatibility archives and shared toolchains.

Credentials and operating-system integration are deliberately excluded:
`~/.ssh`, `~/.gitconfig`, `~/.config/gh`, `~/.npmrc`, `~/.docker`, `~/.kube`,
`~/.codex`, macOS Keychain and application-owned `~/Library` data.

## Compatibility links

The current workstation temporarily retains zero-storage links at historical
paths while active code is migrated. They are compatibility interfaces, not
approved write targets. New code must resolve `UDOS_HOME` instead.

## Drift prevention

Three controls apply:

1. The workspace `AGENTS.md` gives every compatible coding agent the same
   storage, ownership and lifecycle contract.
2. `scripts/check_home_path_policy.py` rejects newly added hard-coded uDOS
   state paths in staged changes or supplied CI diffs.
3. CI applies the checker to additions in pull requests and pushes. Historical
   references are migration debt, not precedent for new work.

Literal legacy paths in migration documentation require the explicit
`path-policy: allow-literals` marker. Individual exceptional lines require a
`path-policy: allow` comment so exceptions remain searchable.

## Destruction contract

Destroying or snapping off uDOS may include `~/Code/.udos` and selected code
repositories only. It must never remove document vaults, credentials, Codex
configuration or general application data without a separately approved plan.
