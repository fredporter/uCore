# Reliability Single-Path Policy

## Why

uCore has accumulated multiple overlapping paths for similar capabilities.
This policy enforces one primary implementation path per capability and
requires proof before a wave is marked complete.

## Rules

1. One capability, one owner path.
2. Any duplicate path must be either removed or explicitly marked temporary.
3. Scaffolds are never counted as complete without runtime proof.
4. Route/feature overlap must be audited each wave.
5. Missing required config must fail fast and trigger repair instructions (no silent hardcoded defaults).
6. Agent claims are not proof; repository artifacts and runtime checks are proof.

## Required Wave Evidence

For each wave, attach:

- changed files list
- compile/test outputs
- route checks for touched capability
- duplicate-route audit output
- preflight/readiness output for touched capabilities

## Duplicate Route Audit

Run:

```bash
cd /Users/fredbook/Code/uCore
python3 scripts/audit_duplicate_routes.py
```

Interpretation:

- exit 0: no duplicates detected
- exit 1: one or more duplicates found, requires triage

## Capability Preflight Gate (S-Page Integration)

Use these APIs before attempting capability actions:

- GET /api/extensions/status
- GET /api/capabilities/{capability}/preflight

Behavior:

- 200 ready=true: execute capability
- 412 ready=false: block action and present repair steps

S-page UX should never "keep calm and carry on" on missing prerequisites.
It must block, show repair actions, and require re-check before resume.

Frontend contract:

- Render repair payloads via a reusable repair panel component.
- Show capability-level blockers and per-step actions.
- Provide an explicit "Re-check" action that re-runs preflight.

## Model Role Split (Speed Without Drift)

1. Planner: breaks wave into atomic tasks and acceptance checks.
2. Executor: performs scoped edits only.
3. Verifier: runs compile/test/route/readiness and blocks merge on failure.

You can swap model providers for each role, but the gate sequence cannot be
skipped.

Recommended practical split:

- local Ollama models: draft/refactor/scaffold bursts
- Copilot in VS Code: integration fixes, verification, final wave closeout
- Cline: bounded branch-local execution only, never source-of-truth

## Documentation Non-Regression Gate

Governance docs must stay aligned with hard-cut and preflight policy.

Required checks in CI:

- extension spec must reflect required uFlow/uKnowledge ownership
- no fallback-to-core guidance in active split docs
- preflight block semantics (`ready=false` / `412`) must be documented

## Config Source-of-Truth

For Cline invocation and model/provider settings:

1. uCore user variables store (`~/.ucore/data/variables.json`)
2. uCore settings/env (`UCORE_CLINE_*`, `UCORE_OLLAMA_*`)
3. Secret store for key-based providers only

No hardcoded provider/model values in execution code.

## Fail-Fast Config Policy

For execution skills (for example Cline invocation):

- Required runtime values (provider/model and required API keys) must be validated.
- If missing, return repair-required response with concrete steps.
- Do not auto-substitute hidden defaults for missing required values.
