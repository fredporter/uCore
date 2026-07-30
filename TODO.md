# Dev Flow Implementation — Complete

- [x] tasker_ingest.py — MCP bridge: Cline task_progress → .tasker/spool/private wisdom
- [x] dev_layer.py — Dev Mode toggle service (on/off/minimal)
- [x] docs_roundup.py — End-of-round docs automation skill
- [x] /api/dev-layer/state routes wired in routes.py
- [x] SPRINT_PLAN.md success criteria unchecked → all checked
- [x] Fix USX frontend path (frontend/ → frontend-vue/)
- [x] USX hardcode-fix.css — var() overrides for usx-standard.css
- [x] USX surface-fix.css — var() overrides for all surfaces
- [x] devMode.ts store — 3-state backend API integration
- [x] Git commit all changes
- [x] Feed System: Pod schema, MCP server, API routes, FeedConsumer, frontend store
- [x] Docs round: FEED_SYSTEM_SPEC.md, archive SPRINT_PLAN, local fieldnotes, bump v4.0.1
- [x] Update .clinerules with Docs Round Completion rule and In-House Skills Library
- [x] Mark sprint complete in .tasker.dev-flow.yaml
- [x] Final push all round artifacts

## Repo Architecture Handoff

- [x] Create a Cline-ready handoff for the repo split and plugin boundary plan
- [x] Add plugin/extension surface scaffolding in uCore
- [x] Create or scaffold uFlow and uKnowledge repos
- [x] Create an initial udos- plugin repo pattern
- [x] Update README and architecture docs to reflect the new repo model

## Repo Split Phase 2 (Hard Cut)

- [x] Remove workflow adapter fallback and require uFlow ownership
- [x] Remove knowledge adapter fallback and require uKnowledge ownership
- [x] Extract and delete in-core workflow modules after parity checks
- [x] Extract and delete in-core knowledge modules after parity checks
- [ ] Keep SonicScrewdriver explicitly out of scope for this phase

### Wave 2 Knowledge Migration Progress

- [x] Migrate `/api/knowledge/search` to external uKnowledge implementation
- [x] Migrate `/api/knowledge/workspaces` to external uKnowledge implementation
- [x] Migrate `/api/knowledge/documents` to external uKnowledge implementation
- [x] Remove in-core search handler ownership
- [ ] Migrate next knowledge endpoint wave (document-content)

## Next Phase — uCode Boundary Hard Cut

- [x] Remove any remaining uCore ownership language for GridCore, GridSmith, teletext, terminal widgets, and runtime primitives
- [x] Audit overlapping implementation details and move them into uCode where they belong
- [ ] Keep uCore limited to shell, adapter, and orchestration surfaces
- [ ] Update repo descriptions and docs so uCode is clearly the runtime foundation repo
- [x] Verify and remove remaining in-core overlap modules after parity checks: `backend/app/api/workflows.py`
- [x] Verify and remove remaining in-core overlap modules after parity checks: `backend/app/api/knowledge.py`
- [ ] Cut runtime implementation overlap: externalize `backend/app/ucode/ceefax.py` behind runtime package/adapter
- [x] Cut runtime implementation overlap: externalize `backend/app/ucode/bbcsdl.py` bridge path to env-config (`UCORE_BBCSDL_BRIDGE_PATH`)
- [ ] Keep host-side terminal runtime adapter thin in `backend/app/api/terminal_runtime.py` (no runtime primitive ownership)
- [x] Route Ceefax/BBCSDL runtime registration through dedicated adapter (`backend/app/extensions/adapters/ucode_runtime_adapter.py`)

## Cline Run Order

- [x] Run uCode boundary hard cut first
- [ ] Then run the workflow deletion wave with parity checks
- [ ] Then run the knowledge document-content wave
- [ ] Capture proof bundles and push each wave separately

## uDev Dogfooding Wave

- [ ] Run extraction waves through uDev autonomous flow (low-cost model route first)
- [ ] Capture per-wave evidence (diff summary, tests, route checks)
- [ ] Record orchestration failures and tuning notes in handover docs
- [ ] Compare autonomous throughput vs manual throughput at end of phase

## Reliability and Consolidation

- [x] Fix Cline CLI execution blocker (code-signing + command syntax)
- [x] Establish low-cost local Cline run path (ollama provider override)
- [x] Remove duplicate variable route registration path
- [x] Add duplicate-route audit script and run it to zero duplicates
- [ ] Enforce stop-the-line gate on every wave completion

## Documentation and Planning Governance

- [x] Align extension registry spec with hard-cut semantics
- [x] Add docs non-regression validator (`scripts/validate_docs_nonregression.py`)
- [x] Wire docs non-regression check into CI
- [x] Add Ollama documentation audit workflow and script
