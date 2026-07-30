# Phase 10 - Ecosystem Hardening and Autonomous Rounds

- status: active
- owner: developer-lane
- started: 2026-07-31
- governance: stop-the-line required per wave

## Goal

Ship a stable core host shell with clean extension/plugin boundaries, zero legacy fallback drift, and repeatable autonomous dev rounds with verifiable evidence.

## Gate 0 - Stability Baseline

- [x] Confirm uCore boot + `/api/health` + `/api/mcp/diagnostics`
- [x] Confirm `python3 scripts/audit_duplicate_routes.py` returns zero duplicates
- [x] Confirm `python3 scripts/validate_extension_manifests.py` passes
- [x] Confirm `python3 scripts/validate_legacy_settings_cleanup.py` passes
- [x] Confirm Developer Surface build + dev startup on fixed `5176`

## Gate 1 - Governance and Cleanup

- [ ] Remove obsolete compatibility notes that imply in-core fallback ownership
- [ ] Remove dead/legacy settings references from active docs and scripts
- [ ] Validate no forbidden legacy modules reappear in uCore host tree
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

- [ ] Finalize capability map: `identity_gateway`, `wordpress_gateway`
- [ ] Expand `udos-identity` API contracts for story progression + variables
- [ ] Add privacy/share rules with expiry checks
- [ ] Add WordPress mapping adapters for user meta/taxonomy
- [ ] Add route parity + preflight validation for all new identity routes

## Wave G - Google Plugin Foundation

- [ ] Create `udos-google` repository skeleton and manifest
- [ ] Implement OAuth contract and token ownership model
- [ ] Implement Gemini chat + gems thin slice
- [ ] Implement Vault docs <-> Drive thin sync slice
- [ ] Add `google_ai_bridge` capability preflight and health gates

## Wave H - Dreamscape Foundation

- [ ] Create `udos-dreamscape` repository skeleton and manifest
- [ ] Implement interest intake -> mission/task scaffolding routes
- [ ] Implement daily briefing baseline output flow
- [ ] Define Chronos integration contracts without core fallback logic
- [ ] Add `dreamscape_orchestration` capability preflight and readiness checks

## Wave I - Developer Surface and MCP Bridge Integration

- [ ] Add readiness cards for WordPress, Google, Dreamscape capabilities
- [ ] Hide/disable controls until capability preflight is ready
- [ ] Add bridge tool coverage in `uDev/mcp-bridge` for new plugin APIs
- [ ] Validate deterministic startup and no stale API client imports

## Autonomous Dev Rounds

- [ ] Adopt runbook: `docs/specs/AUTONOMOUS_DEV_ROUNDS_RUNBOOK.md`
- [ ] Execute low-cost route first (ollama-first)
- [ ] Execute broad-strokes pass with diagnostics + hivemind health checks
- [ ] Capture cost/perf metrics and compare with manual throughput
- [ ] Publish per-round artifacts and repairs log

## Evidence Gate (Mandatory Each Wave)

- [ ] Runtime proof
- [ ] Command proof
- [ ] Test proof
- [ ] Evidence proof
