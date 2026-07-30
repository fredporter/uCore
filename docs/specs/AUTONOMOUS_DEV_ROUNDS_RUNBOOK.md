# Autonomous Dev Rounds Runbook

Status: Active
Scope: uCore host shell + extension/plugin ecosystem

## 1. Objective

Provide a repeatable autonomous development round process that preserves core stability, prevents regressions, and produces verifiable evidence for every wave.

## 2. Hard Rules

1. Core first: no plugin wave starts if host shell gates are red.
2. Contract before implementation: capability preflight and route contracts come first.
3. One plugin focus per wave branch.
4. No fallback-to-core ownership paths for externalized capabilities.
5. Stop-the-line bundle is required before wave completion.

## 3. Round Lifecycle

## R0 - Preflight Baseline

Run:

1. `python3 scripts/audit_duplicate_routes.py`
2. `python3 scripts/validate_extension_manifests.py`
3. `python3 scripts/validate_split_repo_packaging.py`
4. `python3 scripts/smoke_split_repo_imports.py`
5. `python3 scripts/validate_docs_nonregression.py`
6. `python3 scripts/validate_legacy_settings_cleanup.py`

Expected:

1. All checks pass.
2. No duplicate routes.
3. No forbidden legacy settings/modules.

## R1 - Scope Lock

1. Select one wave target only.
2. Define acceptance checks before code edits.
3. Record planned commands and expected outputs.

## R2 - Execute

1. Implement minimal vertical slice.
2. Keep boundaries strict (host shell vs plugin ownership).
3. Avoid speculative UI wiring to unfinished APIs.

## R3 - Verify

1. Compile/lint/test relevant repos.
2. Validate route behavior and capability preflight.
3. Verify no governance regressions.

## R4 - Evidence and Close

Publish:

1. Changed files summary.
2. Commands executed.
3. Runtime route/status proof.
4. Test/build proof.
5. Repairs performed and residual risks.

## 4. Logging and Repair Model

## Required per-round logs

1. `commands.log` (or documented command list)
2. `checks.log` (validation output summary)
3. `repairs.log` (issues found -> fix -> verification)
4. `delta.md` (what changed and why)

## Repair sequence

1. Detect failure.
2. Triage root cause.
3. Apply smallest safe fix.
4. Re-run failed gate.
5. Document proof.

## 5. Stable Core Checklist

Before promoting a wave:

1. Host routes stable.
2. Extension registry stable.
3. Capability preflight accurate.
4. Developer Surface build/dev stable.
5. Governance scripts passing.

## 6. Anti-Regression Gates

Required CI gates:

1. planning governance
2. docs non-regression
3. extension manifest validation
4. split-repo smoke/packaging checks
5. duplicate-route audit
6. legacy settings/module cleanup check

## 7. Wave Exit Template

Use this structure in handovers:

1. Wave name
2. Goal
3. Commands run
4. Runtime proof
5. Test proof
6. Evidence proof
7. Repair notes
8. Next wave entry criteria
