# uDev Binder Compiler Integration Checklist (uCore Alignment)

Status: Draft for Wave 1 execution
Date: 2026-08-03
Scope: uDev + uCore parallel alignment

## Goal

Ensure uDev can compile deterministic Binder context and consume uCore contracts without duplicating ownership.

## Contract Baseline

1. uCore owns runtime APIs, capability readiness, and extension registry.
2. uDev owns Binder authoring/visibility and context compiler UX.
3. Every AI action in uDev must carry inspectable compiled context.

## Required uCore Endpoints (must remain stable)

- GET /api/capabilities/readiness
- GET /api/capabilities/{capability}/preflight
- GET /api/control/status
- GET /api/system/workflow
- Chat endpoints used by uDev:
  - POST /api/chat/stream
  - POST /api/chat

## Binder Compiler Input Contract (uDev -> uCore coordination)

Required binder inputs:

- binder/current.md
- binder/architecture.md
- binder/roadmap.md
- binder/decisions.md
- repository branch/head metadata
- selected lane and active rules
- active issue/task reference (if available)

Compiler output:

- binder/context.json validated by binder/context.schema.json
- stable fingerprint hash for identical input sets

## Integration Tasks

## A. Capability and Policy Integration

- [ ] Confirm control panel capabilities remain aligned with capability_requirements.json keys.
- [ ] Ensure readiness/preflight failures always return actionable repair payloads.
- [ ] Verify HTTP 412 semantics are preserved and surfaced to uDev.

## B. Context Attachment Path

- [ ] Define server-accepted envelope fields for context payload attachment to chat actions.
- [ ] Validate no hidden server-side prompt state overrides Binder intent.
- [ ] Add explicit logging marker when Binder context is attached successfully.

## C. Determinism and Auditability

- [ ] Add validation check that context schema version is supported.
- [ ] Ensure deterministic normalization rules are documented and testable.
- [ ] Add evidence output in logs/telemetry for context fingerprint per request.

## D. Reliability Gates

- [ ] CI: validate capability requirements parity (already present).
- [ ] CI: validate docs/runtime parity for capability counts and key contracts.
- [ ] Add lightweight contract probe script for Binder-context chat envelope acceptance.

## E. Dogfood Runbook (Daily)

- [ ] Start in uDev binder/current.md.
- [ ] Regenerate/verify binder/context.json.
- [ ] Run one AI task with context attachment.
- [ ] Verify preflight/readiness before capability actions.
- [ ] Record decisions and blockers in Binder markdown.

## Exit Criteria (Wave 1)

1. uDev control routes never target invalid tabs.
2. uDev sends validated binder/context.json with default AI actions.
3. uCore returns deterministic preflight/readiness responses for all Wave 1 capabilities.
4. One full MVP loop completes daily without manual context reconstruction.
