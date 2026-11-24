<!-- path-policy: allow-literals -->
# Ecosystem Storage Architecture

**Status:** Canonical
**Updated:** 2026-11-17

## Ownership boundary

| Location | Owner | Lifecycle |
| --- | --- | --- |
| `~/Code/<repo>` | Git repositories | Clone, develop, archive independently |
| `~/Code/.udos` | uDOS runtime | Detachable and destructible as one unit |
| `~/Code/Depot` | SonicScrewdriver | Retained delivery artifacts only; hash-verified, self-cleaning, receipt per removal |
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

## Depot boundary

`~/Code/Depot` is the retention boundary for delivery artifacts. It is visible
on purpose, and it is owned by SonicScrewdriver, not by uDOS runtime state.

- Retained: pinned installers, capsule payloads, and pinned dependency bundles
  that a consumer installs from offline. Each file is registered in
  `depot_manifest.json` with its SHA-256 and byte size.
- Not retained: model weights and OCI layers (their owning stores under
  `UDOS_HOME/runtimes`), user documents (`~/Vault`, `~/Shared`, `~/Public`), or
  upstream clones. Provenance lives in the distribution catalogue, not in a
  clone tree.
- Curation: `sonic depot register|verify|gc --depot ~/Code/Depot`. Serving
  requires an explicit artifact root, binds loopback by default, and answers
  only for files registered in the manifest; unregistered files, directories
  and paths outside the root are not reachable.
- Removal is never silent. Every retention or removal action writes a JSON
  receipt under `Depot/receipts/`, and retention may never drop the only
  verified copy of an artifact a consumer still pins.
- The distributable base catalogue is Layer 0 data in
  `~/Public/global-knowledge/datasets/distribution_catalogue.json`, authored in
  the `global-knowledge` repository. The local instance (retention state,
  verification results, receipts) stays in the Depot and is never committed.

## Private document layout

Active Binders are top-level folders identified by their Binder records.
`Sandbox/` holds drafts and captures without a Binder. `Memory/` groups
durable documents and exported artifacts by purpose. Host activity, dispatch
feeds, intake originals, knowledge overlays, and publishing exports use
their Memory collection paths. Move files with their owning service so
future writes use the same location. Dispatch records and contribution bundles
use `Memory/Activity/Transport/`. Retired Binder folders use
`Memory/Archive/Archived Binders/`. Task and Mission state remains in the
workflow runtime under `UDOS_HOME`.

See the [User Vault layout](plans/USER_VAULT_LAYOUT.md) for the collection map
and migration record.

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
