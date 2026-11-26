# Train 0 — Consolidation and release baseline: evidence

- Status: complete — squash-merged to `main` as `e1811ed` (PR #58), tagged `v4.1.0`; the scoped-retention patch follows as `v4.1.1`
- Branch: `consolidation/train0-2026-11-26`
- Base: local `main` `0dbf34e`
- Merges: `eb8443e` (origin/main) → `7ddf7b1` (variables) → `5e9ebd0` (depot integration) → `b154f21` (into `main`)
- Captured: 2026-11-26
- Governance: measurements taken on the committed tree, not on a dirty worktree

## Why this train existed

Five sprint branches were unmerged, `origin/main` and local `main` were separate
lineages, the runtime reported `4.0.5` while packaging declared `4.0.3`, and no
scheduled maintenance job had ever succeeded. No product release could be traced
to one reproducible uCore tree.

## Branch disposition

| Branch | Scope | Disposition |
| --- | --- | --- |
| `sprint/variables-and-recipe-surfaces` | 11 commits, 94 files | Merged (`7ddf7b1`) |
| `sprint/content-contract` | 2 commits | Contained in the variables branch (same commits) |
| `sprint/depot-integration` | 7 commits, 4 files | Merged (`5e9ebd0`); superset of the three depot branches |
| `sprint/depot-release-gate` | 1 commit | Already delivered upstream as PR #57 (`a2ee815`); tree identical |
| `sprint/visible-delivery-depot` | 1 commit | Contained in `sprint/depot-integration` |
| `sprint/nanocoder-cache-install` | 4 commits | Contained in `sprint/depot-integration` |
| `sprint/ucode-plus-integration` | 0 ahead | Already an ancestor of `main` |

`origin/main` shares base `31c5909` with local `main`, so merging it was clean and
makes the remote tip an ancestor of the consolidation branch. It added the four
PR #57 files (NanoCoder install contract, storage architecture row, installer,
dependency lock).

## Conflicts and resolution

Five files conflicted because local `main` carried the pre-rewrite duplicate of
the variables/recipe work (`ba88a14`, `2496c33`) while the sprint branch carried
the reviewed rewrite:

`backend/app/api/variables_api.py`, `backend/tests/test_variables_api.py`,
`frontend-vue/src/main.ts`,
`frontend-vue/src/recipes/components/AuthoringRecipeView.vue`,
`frontend-vue/src/surfaces/recipes/RecipeGallerySurface.vue`.

Each was resolved to the sprint side. The full suites below confirm no reviewed
behaviour was lost; the display-profile import that only the sprint added to
`main.ts` is present.

## Verification gates

| Gate | Command | Result |
| --- | --- | --- |
| Backend suite | `./.venv/bin/python -m pytest backend/tests -q` | **860 passed**, 8 warnings |
| Frontend suite | `npx vitest run` | **185 passed**, 53 files |
| Frontend build | `npm run build` | exit 0 |
| Action audit | `npm run audit:actions` | **1006 controls, 0 missing, 0 unresolved** |
| Content contract | `python3 scripts/check_content_contract.py` | 0 errors, 17 known warnings |
| Path policy | `python3 scripts/check_home_path_policy.py` | OK |
| Browser flows | `npx playwright test e2e/sprint-verification.spec.ts` | **11 passed** |

The browser suite covers the authoring-recipe mode controls, focus ring, 390 px
reflow, settings-form labelling, recipe-gallery preview controls and theme
switch, workflow lanes and keyboard reachability, and the ten-foot root scale at
1280/1920/2560/3840 widths.

## Version: one declaration

The runtime version came from a literal in `Settings` (`4.0.5`) while packaging
declared `4.0.3`. `backend/app/core/settings.py` now resolves one value:
`backend/pyproject.toml` when present (source checkout, so a stale editable
install cannot win), otherwise the installed distribution metadata (wheel).

| Proof | Result |
| --- | --- |
| Declared version | `backend/pyproject.toml` → `4.1.0`; `backend/uv.lock` record updated |
| Resolver in checkout | `settings.version == "4.1.0"` |
| Wheel | `ucore-4.1.0-py3-none-any.whl`, `app/core/vars.def` present (2,894 bytes) |
| Wheel metadata | `Version: 4.1.0` |
| Installed outside checkout | `/tmp/wheelenv410` reports `4.1.0` from site-packages |

Drift guards: `test_version_matches_packaged_metadata` compares the runtime value
to `pyproject.toml`, and the two former hardcoded assertions now compare to the
resolved settings value, so the next bump cannot silently desynchronise them.

## Maintenance authorization

Scheduled runs called `run_skill_by_id` without `execution_authorized`, so every
job whose skill requires confirmation reported `needs_approval` and nothing ran —
including `backup`, whose `last_success` had never been set.

`MaintenanceJob` now carries an explicit `authorized` standing grant. All five
owner-data jobs hold one — `backup`, `vault_sync`, `tasker_sync`, `brain_sync`
and `clipboard_maintenance` — approved by the owner on 2026-11-26;
`docs_mirror_sync` and `spool_prune` never required one. `status()` exposes the
grant so the surface can show it, and a regression test pins the exact set so
widening it further remains a reviewed change.

## Backup proof

The skill also reported `success: true` when it produced nothing. It now reports
failure with a reason when no component is available.

| Step | Evidence |
| --- | --- |
| Disposable rehearsal | 4 components (database, wisdom, secrets, config); DB SHA-256 matches the live database; `pragma integrity_check` = `ok` |
| Restore rehearsal | Config archive (15 files) extracted; `engineering-commands.json` hash matches the original |
| Production run | `$UDOS_HOME/backups` — 4 components, database 90,112 B, wisdom 8,296 B, secrets 97 B, config 6,004 B |

Retention is now scoped. The pass previously deleted any file or directory in the
destination older than the window, which removed 43 expired items in the first
production run — including artefacts this skill did not create. It now removes
only its own artefacts (`ucore-backup-*.db`, `wisdom-*.md`, `secrets-*.enc`,
`secrets-*.key`, `config-*.tar.gz`) and never touches another owner's files or
directories. Covered by `test_retention_only_prunes_its_own_artifacts`; released
as 4.1.1.

## Dirty trees parked

| Repository | Commit | Content |
| --- | --- | --- |
| SnackMachine | `d480913` | Bounded, profile-scoped capture receipts (3 tests pass) |
| HomeNook | `22911ca` | Retired Vendor paths; repo-local health check (shell syntax checked) |
| uCoreMac | `95ca66b` | Route registrar + discovery/disablement documentation (compile and manifest checked) |
| Groovebox | `6690795` | `sessions/` ignored as local runtime output |

## Kanban board self-heal

The Engineering board was down, which blocked card updates. `scripts/kanban_supervisor.py`
starts the loopback board when it is absent, waits for readiness and refreshes the
`kanban.json` export. `--status` changes nothing; `--open` heals and then opens the
board. The binary lookup also covers nvm installs that launchd's PATH omits.

| Concern | Detail |
| --- | --- |
| Owner | uCore Engineering tooling |
| Lifecycle | One-shot `--ensure` from `ucmd` (`kanban-heal`) and the `com.udos.kanban-supervisor` launchd agent every 60 s |
| Writes | `$UDOS_HOME/logs/kanban-supervisor.log` and the generated export; board data stays in `~/.cline/kanban` |
| Removal | `launchctl bootout gui/$UID/com.udos.kanban-supervisor`, then delete the plist, the script and its catalogue entry |

Verified live: kill the listener → `--status` reports `running: false` → `--ensure`
exits 0 → `--status` reports `running: true`.

## Rollback

Tags taken before the merges: `backup/pre-consolidation-main-2026-11-26`,
`backup/pre-consolidation-variables-2026-11-26`,
`backup/pre-consolidation-origin-main-2026-11-26`.

## Residual and unverified

- The running uCore service still executes the pre-consolidation process; the
  scheduled grant and the version string take effect after an authorised restart.
- Remote CI has not been run for this tree; no push was performed.
- No hardware qualification is implied by these checks.
- Sprint checkouts (`uCore-depot-integration`, `uCore-depot-pr`,
  `uCore-storage-depot`, `uCore-nanocoder-install`, `uCore-openrouter`) remain on
  disk; their branches are consolidated and can be removed after review.

