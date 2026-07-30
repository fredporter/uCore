# Capability Preflight Repair Gate Rollout

- status: in-progress
- source: ucore-dev
- source_id: capability-preflight-repair-gate-20260730
- synced_at: 2026-07-30T00:00:00Z

## Goal

Enforce strict preflight + repair gating for capability actions across S-pages.

## Tasks

- [x] Add backend extension status endpoint (`/api/extensions/status`)
- [x] Add backend capability preflight endpoint (`/api/capabilities/{capability}/preflight`)
- [x] Add capability requirements config map (`config/capability_requirements.json`)
- [x] Add frontend preflight API helper (`frontend-vue/src/api/preflight.ts`)
- [x] Wire preflight blocking in workflow store for workflow/knowledge capabilities
- [x] Add reusable repair panel component for S-pages
- [x] Wire repair panel into Workflow surface
- [x] Add startup readiness snapshot for top capabilities
- [x] Add CI gate to fail when capability requirements are missing

## Verification Evidence

- backend compile: `python3 -m compileall -q backend/app`
- frontend typecheck: `npx tsc --noEmit`
- route audit: `python3 scripts/audit_duplicate_routes.py`

## Notes

No silent fallback for required capability paths.
Missing prerequisites must trigger repair steps and explicit rerun of preflight.
