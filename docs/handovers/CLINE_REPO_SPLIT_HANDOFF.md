# Cline Handoff — Repo Split and Plugin Boundaries

## Goal

Advance the repo architecture cleanup in a staged but aggressive way:

- keep uCore as the host/platform core
- create dedicated repos for workflow and knowledge concerns
- use the udos- prefix for plugin-style repos
- leave SonicScrewdriver unchanged for now
- add a plugin and extension surface inside uCore
- prioritize structural progress over backward compatibility

## Target repo model

- uCore: host shell, plugin contract, extension registry, default core capabilities
- uFlow: workflow engine and workflow-specific surfaces
- uKnowledge: knowledge integration and knowledge-specific services
- uCode: grid/runtime foundation, GridCore, GridSmith, teletext, terminal widgets, and embeddable runtime artifacts
- udos-\*: plugin-style repos for optional capabilities such as home, budget, identity, media, automation, and similar domain features

## Immediate work items

1. Audit the current backend modules and classify them as:
   - core host
   - workflow
   - knowledge
   - plugin candidate

2. Introduce a lightweight plugin/extension contract in uCore so optional capabilities can be discovered and loaded.

3. Create or scaffold the repo boundaries for:
   - uFlow
   - uKnowledge
   - at least one starter udos- plugin repo

4. Move workflow-related logic out of uCore first and remove in-core workflow endpoint implementation.

5. Move knowledge-related logic out of uCore second and remove in-core knowledge endpoint implementation.

6. Update the READMEs and architecture docs so the public repo story is consistent.

7. Keep uCode as the implementation home for GridCore, GridSmith, teletext, and embedded runtime primitives; uCore should consume those capabilities, not own them.

## Guardrails

- Do not touch SonicScrewdriver during this phase.
- Do not move the core runtime shell into a plugin repo.
- Prefer direct extraction over long-lived compatibility shims.
- Keep uCore bootable and testable while the split is in progress.

## Suggested first implementation order

1. plugin manifest + registry surface
2. workflow hard cut to uFlow (no fallback path)
3. knowledge hard cut to uKnowledge (no fallback path)
4. README and architecture docs
5. optional starter udos- plugin repo

## Phase 2 — Hard Cut Execution

1. Remove adapter fallbacks once uFlow and uKnowledge are importable in the environment.
2. Delete extracted workflow/knowledge modules from uCore after endpoint parity validation.
3. Keep endpoint URLs stable where practical, but allow breaking internal imports and module locations.
4. Push small, reversible commits by wave: registry, workflow cut, knowledge cut, docs.

## Phase 3 — uCode Boundary Hard Cut

1. Remove any remaining uCore host-shell language for GridCore, GridSmith, teletext, terminal widgets, and runtime primitives.
2. Migrate any overlapping implementation details out of uCore and into uCode boundaries where they belong.
3. Keep uCore focused on shell, adapter, and orchestration surfaces only.
4. Update repo descriptions and docs so uCode is clearly the runtime foundation repo and uCore is clearly the host shell.

## Cline Execution Brief

Run the next round in this order and do not widen scope unless a check fails:

1. uCode boundary hard cut
   - audit uCore for any remaining host-shell language, imports, or runtime primitives that belong in uCode
   - remove or rewrite those references so uCore is shell-only
   - update the uCode repo metadata and docs if anything still implies host-runtime control

2. Workflow deletion wave
   - remove in-core workflow implementation after parity validation with uFlow
   - keep only the adapter/route bridge in uCore

3. Knowledge document-content wave
   - migrate the next knowledge endpoint wave into uKnowledge
   - delete the matching in-core implementation after route parity

4. Evidence bundle
   - capture changed files, commands run, route checks, and any failures/fixes
   - commit and push each wave separately

Stop-the-line rules for Cline:

- do not mark a wave complete without runtime proof, command proof, test proof, and evidence proof
- if a command example in docs is stale, rewrite it before continuing
- if a boundary is unclear, stop and document the ambiguity instead of broadening scope

## Evidence Bundle — 2026-07-31 (uCode Boundary + Route Parity)

### Commands executed

1. `rg -n "ceefax|bbcsdl|terminal_runtime|register_.*routes|uCode runtime bridge|host shell adapter" backend/app docs -S`
2. `rg -n "def register_.*routes|app\.router\.add_(get|post|put|delete|patch)\(" backend/app/ucode backend/app/api/terminal_runtime.py -S`
3. `for p in /health /api/ceefax/pages /api/ceefax/feed/latest /api/bbcsdl/teletext /api/terminal/runtime/ws /api/workflows /api/knowledge/workspaces /api/knowledge/search; do ...; done`
4. `for p in /api/health '/api/knowledge/search?q=test' /api/terminal/runtime/ws; do curl -i ...; done`

### Runtime route proof (localhost:8484)

| Route                       | Status | Note                                                 |
| --------------------------- | ------ | ---------------------------------------------------- |
| `/api/health`               | `200`  | canonical health route is `/api/health`              |
| `/api/ceefax/pages`         | `200`  | Ceefax bridge registered                             |
| `/api/ceefax/feed/latest`   | `200`  | Ceefax feed endpoint live                            |
| `/api/bbcsdl/teletext`      | `200`  | BBCSDL bridge endpoint live                          |
| `/api/terminal/runtime/ws`  | `400`  | expected over plain HTTP; requires WebSocket upgrade |
| `/api/workflows`            | `200`  | served via external uFlow route registrar            |
| `/api/knowledge/workspaces` | `200`  | served via external uKnowledge route registrar       |
| `/api/knowledge/search`     | `400`  | expected without `q`; with `?q=test` returns `200`   |

### Boundary findings

1. Workflow and knowledge in-core API modules were removed from uCore and route ownership is externalized through adapters + extension registry.
2. This snapshot preceded strict runtime extraction; see later evidence bundles for completed external runtime cut.

### Next wave cut targets

1. Move Ceefax/BBCSDL runtime implementation package out of uCore host tree or consume it as an external runtime package.
2. Replace hardcoded runtime bridge path with manifest/env-configured runtime contract.
3. Keep only route adapter/wiring logic in uCore for runtime-owned modules.

## Evidence Bundle — 2026-07-31 (Runtime Adapter Cut)

### Commands executed

1. `python3 -m compileall -q backend/app/api/routes.py backend/app/extensions/adapters/ucode_runtime_adapter.py backend/app/ucode/bbcsdl.py backend/app/extensions/adapters/__init__.py`
2. `rg -n "uCode runtime bridge|ucode_runtime_adapter|UCORE_BBCSDL_BRIDGE_PATH|UCORE_UCODE_RUNTIME_REQUIRE_EXTERNAL" backend/app -S`
3. `for p in /api/ceefax/pages /api/bbcsdl/teletext /api/workflows /api/knowledge/workspaces; do ...; done`

### Runtime route proof (localhost:8484)

| Route                       | Status | Note                                                         |
| --------------------------- | ------ | ------------------------------------------------------------ |
| `/api/ceefax/pages`         | `200`  | runtime bridge still functional after adapter routing change |
| `/api/bbcsdl/teletext`      | `200`  | BBCSDL bridge still functional after adapter routing change  |
| `/api/workflows`            | `200`  | external uFlow registration unaffected                       |
| `/api/knowledge/workspaces` | `200`  | external uKnowledge registration unaffected                  |

### Boundary findings delta

1. Ceefax/BBCSDL route registration moved out of direct `app.api.routes` imports and into a dedicated runtime adapter (`app.extensions.adapters.ucode_runtime_adapter`).
2. BBCSDL bridge path is now configuration-driven via `UCORE_BBCSDL_BRIDGE_PATH`.
3. Compatibility fallback for legacy in-repo Ceefax/BBCSDL remains explicit and can be disabled with `UCORE_UCODE_RUNTIME_REQUIRE_EXTERNAL=1` for strict external enforcement.

## Evidence Bundle — 2026-07-31 (Terminal Runtime Adapter Cut)

### Commands executed

1. `python3 -m compileall -q backend/app/api/routes.py backend/app/extensions/adapters/ucode_runtime_adapter.py backend/app/api/terminal_runtime.py`
2. `rg -n "UCORE_TERMINAL_RUNTIME_WS_HANDLER|register_terminal_runtime_routes|terminal runtime bridge" backend/app -S`
3. `for p in /api/ceefax/pages /api/bbcsdl/teletext /api/terminal/runtime/ws /api/workflows /api/knowledge/workspaces; do ...; done`

### Runtime route proof (localhost:8484)

| Route                       | Status | Note                                                               |
| --------------------------- | ------ | ------------------------------------------------------------------ |
| `/api/ceefax/pages`         | `200`  | unchanged after terminal registration refactor                     |
| `/api/bbcsdl/teletext`      | `200`  | unchanged after terminal registration refactor                     |
| `/api/terminal/runtime/ws`  | `400`  | expected for plain HTTP probe (route present; WS upgrade required) |
| `/api/workflows`            | `200`  | external uFlow registration unaffected                             |
| `/api/knowledge/workspaces` | `200`  | external uKnowledge registration unaffected                        |

### Boundary findings delta

1. `app.api.routes` no longer imports terminal runtime registration directly; it now delegates terminal route wiring through `app.extensions.adapters.ucode_runtime_adapter.register_terminal_runtime_routes`.
2. External terminal runtime handler delegation is supported via `UCORE_TERMINAL_RUNTIME_WS_HANDLER`.
3. Legacy in-repo terminal handler remains explicit fallback unless strict external mode is enforced.

## Evidence Bundle — 2026-07-31 (Phase Completion: Strict External Runtime)

### Commands executed

1. `python3 -m compileall -q ucode_runtime` (in uCode)
2. `UCORE_UCODE_RUNTIME_REQUIRE_EXTERNAL=1 UCORE_UCODE_PATH=/Users/fredbook/Code/uCode UCORE_UFLOW_PATH=/Users/fredbook/Code/uFlow UCORE_UKNOWLEDGE_PATH=/Users/fredbook/Code/uKnowledge python3 - <<'PY' ... register_routes(app) ...` (in uCore/backend)
3. `rg -n "app\.ucode\.(ceefax|bbcsdl)|api\.terminal_runtime|from \.terminal_runtime" backend -S`

### Strict route-registration proof

| Check | Result |
| --- | --- |
| Strict external mode enabled | `UCORE_UCODE_RUNTIME_REQUIRE_EXTERNAL=1` |
| Missing required routes | `[]` |
| Registered route count | `220` |
| Workflow route registration | external uFlow loaded |
| Knowledge route registration | external uKnowledge loaded |
| Runtime route registration | external uCode runtime loaded |

### Completion delta

1. External runtime package now exists in uCode as `ucode_runtime` with Ceefax, BBCSDL, and terminal runtime providers.
2. uCore runtime adapter now defaults to strict external mode and fails fast on missing runtime providers.
3. Legacy in-core runtime implementation files were removed from uCore host repo.

## uDev Dogfooding Wave

Use this extraction as an autonomous uDev IDE test:

1. Run wave plans via low-cost model routing first.
2. Require per-wave proof: changed files, test command output, and route checks.
3. Capture failures and fixes in handover notes so uDev orchestration can be tuned.
4. Compare autonomous throughput vs manual throughput at the end of the split.

## Stop-The-Line Gate (Required)

Before marking any wave complete, all checks below must pass:

1. Runtime proof:
   - service boots without manual patching
   - route registration succeeds for the target wave
2. Command proof:
   - every documented CLI command is executed once and output captured
   - remove or rewrite any stale command examples immediately
3. Test proof:
   - compile/lint/test commands for touched areas succeed
   - failures block wave completion
4. Evidence proof:
   - include changed files list, command outputs, and route checks in handover
   - no "planned/scaffolded" item can be marked complete without this evidence

If any gate fails: stop, fix the blocker, re-run proof, then continue.

## Notes for the agent

The important outcome is architectural clarity and actual separation, not feature expansion. Treat this as both a repo cleanup and a uDev autonomous execution benchmark.
