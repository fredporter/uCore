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

- uCore: host runtime, core shell, plugin contract, extension registry, default core capabilities
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

4. Move workflow-related logic out of uCore first and remove in-core ownership of workflow endpoints.

5. Move knowledge-related logic out of uCore second and remove in-core ownership of knowledge endpoints.

6. Update the READMEs and architecture docs so the public repo story is consistent.

7. Keep uCode as the owner of GridCore, GridSmith, teletext, and embedded runtime primitives; uCore should consume those capabilities, not own them.

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

1. Remove any remaining uCore ownership language for GridCore, GridSmith, teletext, terminal widgets, and runtime primitives.
2. Migrate any overlapping implementation details out of uCore and into uCode boundaries where they belong.
3. Keep uCore focused on shell, adapter, and orchestration surfaces only.
4. Update repo descriptions and docs so uCode is clearly the runtime foundation repo and uCore is clearly the host shell.

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
