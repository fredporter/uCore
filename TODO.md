# uCore Dev Status Ledger

Status: Active
Last updated: 2026-08-13

## Purpose

This file is a high-level status ledger only.

Active planning tasks, checklists, and sprint execution must live under `.tasker/` per governance policy:

- `.tasker/phases/`
- `.tasker/backlog/`
- `.tasker/UNIFIED_DEV_TASK_WORKFLOW.md` (archived index)

## Completed Foundations (Summary)

1. Repo split hard-cut completed for workflow and knowledge route ownership.
2. uCode runtime bridge ownership externalized behind strict adapters.
3. Extension registry contract locked and validated in CI.
4. External plugin discovery path operational (including `udos-budget` and `udos-identity`).
5. Split-repo packaging and import smoke validations are wired and passing.

## Active Program (Canonical Source)

Current active execution program:

1. `.tasker/phases/active-phase-11-docs-mirror-publishing-2026-08-13.md`

This phase controls:

1. uDos component docs mirroring (Dev Lane — in-repo `docs/` as source of truth),
2. user published-vault separation (User Lane — never merged with component docs),
3. two-way sync in Dev Mode,
4. docs-site build and publish to `docs.udo.guide`.

## Completed Phase

- Phase 10 — Ecosystem Hardening and Autonomous Rounds (all gates checked).

## Documentation Alignment

Primary planning specs for this phase:

1. `.tasker/phases/active-phase-11-docs-mirror-publishing-2026-08-13.md`
2. `docs/DEVELOPER_SURFACE.md` (lane separation rules)

## Governance

Every wave must pass stop-the-line evidence gates before completion:

1. runtime proof,
2. command proof,
3. test proof,
4. evidence proof.
