# Ecosystem Extended Dev Flow (2026-07-31)

Status: Active planning baseline
Owner: uCore host shell + companion plugin/extension repos
Purpose: keep core infrastructure simple and robust while enabling focused plugin waves.

## 1. Current Ecosystem State

### 1.1 Repo topology (validated)

1. Host shell and extension registry are in `uCore`.
2. Developer lane UI/runtime tooling are in `uDev` (`developer-surface`, `mcp-bridge`).
3. Runtime foundations are in `uCode` (GridCore/uCode profile model).
4. External plugin repos exist and register via manifest discovery:
   - `udos-budget`
   - `udos-identity`
5. Workflow/knowledge/runtime boundaries are already hard-cut to external providers (`uFlow`, `uKnowledge`, `ucode_runtime`).

### 1.2 Stability snapshot

1. `uCore` main is clean except active planning edits.
2. `uDev/developer-surface` was failing build due stale imports and tab/store drift; fixed in this round.
3. Developer Surface now builds and serves on `http://127.0.0.1:5176` with strict port binding.
4. `udos-identity` is currently minimal (profile/session routes only), ready for expansion waves.

### 1.3 Source-of-truth constraints

1. Keep uCore as host shell + registry + preflight gates only.
2. Keep feature ownership in extension/plugin repos.
3. No new in-core fallback route ownership for plugin capabilities.
4. Stop-the-line proof bundle remains mandatory each wave.

## 2. What Is Needed (Delta)

### 2.1 Core (uCore) needs

1. Capability contracts for:
   - Headless WordPress user gateway readiness.
   - Google service readiness (OAuth, API scopes, sync health).
   - Dreamscape briefing/chronos orchestration readiness.
2. Preflight/readiness checks expanded for new capabilities.
3. Registry docs and migration matrix updated for new plugin repos.

### 2.2 Existing repos needing updates

1. `uDev/developer-surface`
   - Keep build green and dev startup deterministic.
   - Add panels/widgets only for capabilities that pass preflight.
2. `uDev/mcp-bridge`
   - Add bridge tools for new plugin APIs after routes are stable.
3. `udos-identity`
   - Expand from stubs to full story/profile/privacy/auth gateway logic.
4. `uCode`
   - Continue mapping-system phases (GridCore-first, future 3D/uCode2-profile compatibility).
5. `uFlow` and `uKnowledge`
   - Only if workflow/knowledge orchestration endpoints need bridge updates for Dreamscape.

### 2.3 New repos to create

1. `udos-google`
   - Canonical name for the Google AI/Workspace plugin (brief alias: GooglePlugin).
   - Owns Gemini/Gems/Agent Studio and Workspace sync APIs.
2. `udos-dreamscape`
   - Owns personalized journey, proactive briefing, and Chronos-driven orchestration.
3. `udos-publishing` (optional split)
   - If publishing/review scope becomes large enough, keep it independent from `udos-identity`.

Repo-creation rule:

1. Start with minimal manifest + route registrar + health endpoint + tests.
2. Add capability only after preflight contract exists in uCore.

## 3. Target Ownership Model

### 3.0 Surface Placement Policy

1. Keep end-user shell UI surfaces primarily in `uCore`.
2. Keep Developer Lane UI in `uDev`.
3. Keep feature/business logic ownership in plugins/extensions (`udos-*`, `uFlow`, `uKnowledge`, `uCode`).
4. Keep legacy route redirects in uCore where useful, but avoid duplicate standalone surfaces when a canonical host surface already exists.

Current decisions:

1. `snackmachine` standalone surface removed; capabilities route to Server/Workflow/System/Developer.
2. Standalone `teletext` and `terminal` surfaces removed; canonical UX is inside `uCode` tabs.
3. `workflow` surface UI stays in `uCore`, while workflow execution/route ownership remains in `uFlow`.
4. `documentation` surface UI stays in `uCore`; publishing/backing providers can move to plugin ownership.

### 3.1 Keep core simple

uCore owns:

1. Host-shell APIs and orchestration.
2. Extension registry and manifest validation.
3. Capability readiness/preflight policy.
4. Developer control/status/reporting surfaces.

uCore does not own:

1. Google API business logic.
2. WordPress identity/content business logic.
3. Dreamscape mission/briefing intelligence logic.
4. Runtime mapping implementation details.

### 3.2 Plugin ownership map

1. `udos-identity`
   - Story forms, profile variables, vault privacy model, publish-review metadata.
2. `udos-google`
   - OAuth + Workspace sync + Gemini/Gems + Agent Studio + Nano Banana services.
3. `udos-dreamscape`
   - Interest parsing, mission generation, proactive briefing, Chronos schedule hooks.
4. `udos-publishing` (optional)
   - Draft/review/publish flow and external target registry.

## 4. Extended Dev Flow (Anti-Mess)

## Gate 0 - Core Stability First

1. Ensure `uCore` boot + diagnostics pass.
2. Ensure Developer Surface build/dev pass in `uDev`.
3. Freeze contract docs before coding new plugin features.

## Gate 1 - Contract Before Code

1. Write/lock API contracts and manifests.
2. Add preflight capability stubs in uCore.
3. Add route parity tests before feature implementation.

## Gate 2 - Vertical Slice by Plugin

1. Pick one plugin wave at a time.
2. Deliver end-to-end thin slice (routes, tests, UI hooks, docs).
3. Stop-the-line evidence bundle before next plugin.

## Gate 3 - Surface Integration Last

1. Expose only ready capabilities in Developer Surface.
2. Hide/disable controls when preflight is failing.
3. Avoid speculative UI wiring to unfinished APIs.

## 5. Sprint Plan

### Sprint 0 (Stabilize and Align, 3-4 days)

1. Lock this execution model and plugin matrix.
2. Keep Developer Surface green and deterministic.
3. Add preflight placeholders for WordPress/Google/Dreamscape.
4. Complete detached-surface cleanup and confirm `discover` parity (registered == filesystem).

Exit criteria:

1. Build/test/runtime green.
2. Contract docs approved.
3. No ambiguous ownership in docs.

### Sprint 1 (Identity + Story Contract, 1 week)

1. Expand `udos-identity` API contracts.
2. Implement story-form progression and variable persistence.
3. Implement privacy/share rule checks and tests.

Exit criteria:

1. Story/profile/privacy routes pass parity tests.
2. Preflight for identity capability returns accurate readiness.

### Sprint 2 (Headless WordPress Gateway, 1 week)

1. Add WordPress gateway connector routes in `udos-identity` (or `udos-publishing` if split).
2. Add OAuth handoff and token-safe server-side flow.
3. Add content directory + publish/review metadata endpoints.
4. Restore documentation publishing API endpoints consumed by uCore Documentation surface.

Exit criteria:

1. Gateway auth/content/permission preflight passes.
2. End-to-end story submission and content retrieval proof exists.

### Sprint 3 (Google Plugin Foundation, 1 week)

1. Create `udos-google` repo with manifest + health + basic Gemini chat tool.
2. Add Vault documents <-> Drive thin sync slice.
3. Add bridge endpoints for safe token management and scope checks.

Exit criteria:

1. `udos-google` loads via manifest discovery.
2. Basic sync + chat slice proven with tests.

### Sprint 4 (Dreamscape Foundation, 1 week)

1. Create `udos-dreamscape` repo and mission model endpoints.
2. Add 3-file method scaffolding and daily briefing generator baseline.
3. Integrate optional memory tool interface (non-blocking if unavailable).

Exit criteria:

1. Mission create/list and briefing generation routes working.
2. Daily briefing artifact proof in Vault-compatible path.

### Sprint 5 (Surface Integration and Hardening, 1 week)

1. Wire Developer Surface widgets for readiness + execution controls.
2. Add reliability/performance/security checks for all new flows.
3. Finalize docs, release checklist, and rollback notes.

Exit criteria:

1. Control panel reflects all new capabilities with accurate status.
2. Stop-the-line bundle complete for each plugin wave.

## 6. First-Cut Backlog by Repo

### uCore

1. Add capability keys:
   - `identity_gateway`
   - `wordpress_gateway`
   - `google_ai_bridge`
   - `dreamscape_orchestration`
2. Add preflight endpoints and failure-repair hints.
3. Update extension registry migration matrix docs.

### uDev/developer-surface

1. Keep `Control`, `Flow`, `Repos`, `MCP`, `Chat` stable first.
2. Add cards for WordPress/Google/Dreamscape preflight states.
3. Add action buttons only when routes are implemented.

### udos-identity

1. Add setup-story schema, step progression, and submissions.
2. Add privacy rules and share expiry validation.
3. Add WordPress user/meta/group mapping adapters.

### udos-google (new)

1. Manifest + route registrar + health.
2. Gemini chat + Gems minimal endpoints.
3. Drive mirror thin slice.

### udos-dreamscape (new)

1. Manifest + route registrar + health.
2. Interest intake + mission scaffolding.
3. Briefing generation baseline.

## 7. Risk Controls

1. Never merge plugin feature code without preflight contract.
2. Keep one plugin focus per wave branch.
3. Prefer additive routes first; defer destructive sync operations.
4. Maintain strict env-driven discovery (`UCORE_EXTENSION_MANIFEST_PATHS`).
5. Enforce route duplicate audit and manifest validation in CI.

## 8. Immediate Next Actions

1. Approve repo names and ownership split (`udos-google`, `udos-dreamscape`, optional `udos-publishing`).
2. Scaffold new repos with minimal manifests and health routes.
3. Start Sprint 1 in `udos-identity` while Sprint 0 contract work lands in `uCore` and `uDev`.
