# Core Stabilization Merge Ledger — 2026-08-18

**Status:** Ready for review; merging requires explicit maintainer approval.

## Outcome

This wave establishes one ownership and storage path across the four core
repositories:

- uFlow owns durable missions, tasks, workflow definitions, runs and approvals.
- uKnowledge owns filesystem-first workspace registration, safe Markdown reads,
  offline search and the read-only Public-vault boundary.
- uCode owns the BASIC/GridCore runtime and uses the shared ecosystem environment
  and `$UDOS_HOME`; it owns no editor, provider, secret or task configuration.
- uCore hosts the user surfaces, delegates to those owners, and keeps Developer
  focused on repository/code work without restoring agent/model/Kanban tabs.

The canonical mutable runtime root is `$UDOS_HOME` (normally
`~/Code/.udos`). User documents remain in `~/Vault`; shared/add-on vaults in
`~/Shared`; public read-only editions in `~/Public`. The shared Python environment
is `~/Code/.venv`.

## Review branches and checkpoints

| Repository | Branch | Head checkpoint |
| --- | --- | --- |
| uFlow | `work/2026-08-18-stabilise` | `028df3d` — task substrate moved into uFlow |
| uKnowledge | `work/2026-08-18-stabilise` | `7e52162` — filesystem-first knowledge library |
| uCode | `work/2026-08-18-stabilise` | `65b1706` — shared state/runtime boundary |
| uCore | `work/2026-08-18-stabilise` | `2f3c5f4` — canonical runtime/tooling cleanup |

## Verification evidence

| Gate | Result |
| --- | --- |
| uCore backend | 498 passed; 6 existing aiohttp warnings |
| uCore Vue unit tests | 12 passed |
| uCore Vue production build | passed; existing chunk-size warnings only |
| uCore changed-file Ruff gate | passed |
| uCore home-path policy | 4 passed |
| uCore self-hosted MCP bridge | TypeScript build passed; diagnostics healthy |
| uFlow | 4 passed |
| uKnowledge | 10 passed, including Public read-only and traversal controls |
| uCode JavaScript/TypeScript | 188 tests passed across GridCore, viewport and GridSmith |
| uCode package build | all three workspaces built, including declarations |
| uCode BASIC runtime | 169 passed, 48 skipped, 2 warnings |

The skipped BASIC tests are marked optional/integration tests in the existing
suite; they are not newly skipped by this wave.

## Merge order

1. uFlow — establishes workflow/task ownership.
2. uKnowledge — establishes knowledge and vault contracts.
3. uCode — establishes runtime/state boundary and buildable UI dependencies.
4. uCore — consumes all three contracts and supplies the reconciled surfaces.

After each merge, rerun that repository's gate. After uCore merges, rerun the
complete table above from clean `main` checkouts before tagging or releasing.

## Review focus

- Confirm no duplicate task or knowledge store remains active in uCore/uCode.
- Confirm Public knowledge mutation is rejected by capability, not merely hidden
  in the UI.
- Confirm Workflow and BrowserUI show live owner-backed state.
- Confirm the Developer surface remains Repo / Code / Editor oriented.
- Confirm Snackbar/System/Intelligence contain operational concerns without new
  top-level navigation.
- Confirm no active install/runtime path recreates `~/.ucore`, `~/.udos`, <!-- path-policy: allow -->
  `.tasker`, `.vscode`, or `.clinerules`.
- Confirm generated files, credentials, vault contents and local runtime state are
  absent from every diff.

## Local-worktree note

`uCore/backend/tests/test_skill_registry_authorization.py` has a local import-order
change that predates/is unrelated to this wave. It was intentionally excluded from
all stabilization commits and must not be swept into a merge.

## Rollback

Each repository is independently reversible to `origin/main`. Do not partially
revert uCore's delegation commits while retaining the owner-repository changes;
either revert the consuming uCore wave first or roll back in reverse merge order.
Runtime/user vault data is not part of these Git changes.
