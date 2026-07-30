# Phase 10 - Ecosystem Hardening and Autonomous Rounds

- status: active
- owner: developer-lane
- started: 2026-07-31
- governance: stop-the-line required per wave

## Goal

Ship a stable core host shell with clean extension/plugin boundaries, zero legacy fallback drift, and repeatable autonomous dev rounds with verifiable evidence.

## Gate 0 - Stability Baseline

- [ ] Confirm uCore boot + `/api/health` + `/api/mcp/diagnostics`
- [ ] Confirm `python3 scripts/audit_duplicate_routes.py` returns zero duplicates
- [ ] Confirm `python3 scripts/validate_extension_manifests.py` passes
- [ ] Confirm `python3 scripts/validate_legacy_settings_cleanup.py` passes
- [ ] Confirm Developer Surface build + dev startup on fixed `5176`

## Gate 1 - Governance and Cleanup

- [ ] Remove obsolete compatibility notes that imply in-core fallback ownership
- [ ] Remove dead/legacy settings references from active docs and scripts
- [ ] Validate no forbidden legacy modules reappear in uCore host tree
- [ ] Record cleanup evidence bundle in `docs/handovers/CLINE_REPO_SPLIT_HANDOFF.md`

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
