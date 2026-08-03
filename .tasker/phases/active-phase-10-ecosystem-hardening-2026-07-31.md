# Phase 10 - Ecosystem Hardening and Autonomous Rounds

- status: active
- owner: developer-lane
- started: 2026-07-31
- governance: stop-the-line required per wave

## Goal

Ship a stable core host shell with clean extension/plugin boundaries, zero legacy fallback drift, and repeatable autonomous dev rounds with verifiable evidence.

## Restructure Checkpoint (2026-08-03)

- [x] Confirm core split repos exist: `uCore`, `uDev`, `uFlow`, `uKnowledge`, `uCode`
- [x] Confirm plugin repos exist with scaffold baseline: `udos-budget`, `udos-identity`, `udos-google`, `udos-dreamscape`, `udos-publishing`
- [x] Add missing `udos-publishing` plugin manifest (`ucore-extension.json`) to complete baseline plugin shape

## Gate 0 - Stability Baseline

- [x] Confirm uCore boot + `/api/health` + `/api/mcp/diagnostics`
- [x] Confirm `python3 scripts/audit_duplicate_routes.py` returns zero duplicates
- [x] Confirm `python3 scripts/validate_extension_manifests.py` passes
- [x] Confirm `python3 scripts/validate_legacy_settings_cleanup.py` passes
- [x] Confirm Developer Surface build + dev startup on fixed `5176`

## Gate 1 - Governance and Cleanup

- [x] Remove obsolete compatibility notes that imply in-core fallback ownership
- [x] Remove dead/legacy settings references from active docs and scripts
- [x] Validate no forbidden legacy modules reappear in uCore host tree
- [x] Record cleanup evidence bundle in `docs/handovers/CLINE_REPO_SPLIT_HANDOFF.md`

## Gate 1B - Surface Ownership Cleanup

- [x] Remove detached legacy `snackmachine` standalone surface (merged into Server/Workflow/System redirects)
- [x] Remove detached legacy standalone `teletext` and `terminal` surfaces (canonical home is uCode tabs)
- [x] Re-scan `/api/surfaces/discover` and verify no detached surfaces remain
- [x] Publish surface placement policy in docs (host UI vs plugin backend ownership)

## Wave E2 - Documentation Publishing Recovery

- [x] Restore documentation backend API contract used by Documentation surface (`/api/docs`, `/api/docs/sites`, `/api/docs/global-knowledge`, `/api/docs/export`, `/api/docs/serve/{site}`)
- [x] Validate doc-site discovery from `~/Public/doc-sites` and global knowledge from `~/Public/global-knowledge`
- [x] Define publishing ownership split: uCore UI shell vs plugin/provider logic
- [x] Add route parity and runtime probes for documentation publishing endpoints

## Wave F - Identity, Story Forms, Publishing

- [x] Finalize capability map: `identity_gateway`, `wordpress_gateway`
- [x] Expand `udos-identity` API contracts for story progression + variables
- [x] Add privacy/share rules with expiry checks
- [x] Add WordPress mapping adapters for user meta/taxonomy
- [x] Add route parity + preflight validation for all new identity routes

## Wave F2 - Publishing and Place Cloud Mirror

- [x] Confirm `udos-publishing` as the owning repo for cloud mirror publishing
- [x] Define `udo.guide` and `udo.place` contracts for guide/place mirror behavior (scaffold baseline)
- [x] Add frontmatter, tagging, location, beacon, and portal mapping checks (scaffold baseline)
- [x] Add verification and shareable publishing reference gates (scaffold baseline)
- [x] Add route parity + preflight validation for publishing/place routes (scaffold baseline)

Wave F2 implementation note:

- [ ] Complete production-depth publishing integrations and route behavior hardening in the next execution plan.

## Wave G - Google Plugin Foundation

- [x] Create `udos-google` repository skeleton and manifest
- [x] Implement OAuth contract and token ownership model
- [x] Implement Gemini chat + gems thin slice
- [x] Implement Vault docs <-> Drive thin sync slice
- [x] Add `google_ai_bridge` capability preflight and health gates

## Wave H - Dreamscape Foundation

- [x] Create `udos-dreamscape` repository skeleton and manifest
- [x] Implement interest intake -> mission/task scaffolding routes
- [x] Implement daily briefing baseline output flow
- [x] Define Chronos integration contracts without core fallback logic
- [x] Add `dreamscape_orchestration` capability preflight and readiness checks

## Wave I - Developer Surface and MCP Bridge Integration

- [x] Add readiness cards for WordPress, Google, Dreamscape capabilities
- [x] Hide/disable controls until capability preflight is ready
- [x] Add bridge tool coverage in `uDev/mcp-bridge` for new plugin APIs
- [x] Validate deterministic startup and no stale API client imports

## Wave J - Final Dev-Round and Closure

- [x] Execute the final autonomous dev-round after Waves G, H, and I are complete
- [x] Collect the stop-the-line evidence bundle across all completed waves
- [x] Publish the final repairs log, release notes, and rollback notes
- [x] Commit and push remaining planning/documentation updates before closing the phase

## Autonomous Dev Rounds

- [x] Adopt runbook: `docs/specs/AUTONOMOUS_DEV_ROUNDS_RUNBOOK.md`
- [x] Execute low-cost route first (ollama-first)
- [x] Execute broad-strokes pass with diagnostics + hivemind health checks
- [x] Capture cost/perf metrics and compare with manual throughput
- [x] Publish per-round artifacts and repairs log
- [x] Run the final dev-round closure pass for completed waves before phase handoff

## Evidence Gate (Mandatory Each Wave)

- [x] Runtime proof
- [x] Command proof
- [x] Test proof
- [x] Evidence proof
