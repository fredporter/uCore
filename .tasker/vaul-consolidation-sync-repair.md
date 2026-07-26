# Vault Consolidation & Sync Repair - Sprint Plan

**Date:** 2026-07-26
**Status:** Complete
**Branch:** vault-consolidation-sync-repair

## Objectives

### O1: Consolidate Vault Content — ✅ Complete
- No stale vault content found at `~/.ucore/vaults/` (doesn't exist)
- `~/Vault/`, `~/Shared/`, `~/Public/` already have content and correct structure
- No stale config paths in `~/.ucore/config/`, `backend/config/`, or `frontend-vue/src/`
- **Result:** Nothing to migrate. Architecture already correct.

### O2: Update Documentation — ✅ Complete
Files updated:
- `docs/VAULT_BINDER_WORKFLOW_INTEGRATION.md` — Converted from 5-layer to 3-type vault system (User/Shared/Public). Added Section 9: "Lane Separation — Boundary Rules" with agent boundary rules, mental model diagram. Removed Code layer (now part of Developer Lane). Corrected diagram and all path references.
- `docs/DEVELOPER_SURFACE.md` — Added "Lane Separation — Read This First" section at top with boundary table, agent rules, vault architecture reference. Added "Vault vs Code — The Boundary" section at bottom.
- `docs/FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md` — Added "Lane Separation — Boundary Rules" section with User/Developer Lane breakdown, boundary rules, lane diagram. Corrected vault path reference from `~/Public/global-knowledge/, ~/Code/` to `~/Public/ (reference)`.

### O3: Diagnose AppFlowy Sync — ✅ Complete
Issues found and fixed:
- `backend/app/af_manager/config.py` — Fallback config had stale paths: `~/Vault/Public` and `~/Vault/Shared` instead of `~/Public/` and `~/Shared/`. Fixed to canonical 3-layer vault architecture.
- `config/vault-sync.example.yaml` — Updated from 5-layer topology comment and removed stale `code-docs` container. Merged global + public containers into single Public vault entry.
- Sync tested with dry-run: **566 files detected**, engine working correctly.
- AppFlowy data directory exists and is populated (local workspace `604455883014934528`, cloud workspace `604455307002777600`).
- Note: `config/vault-sync.yaml` doesn't exist yet (only the `.example.yaml` template). Sync will work when user copies the example and customizes.

### O4: Audit Vault Filepicker Sidebar — ✅ Complete
Files updated:
- `frontend-vue/src/skills/molecules/WorkspaceFilter.vue` — Fixed filter to show all 3 vault types (was hard-coded to only `user`). Added `shared` and `public` to static fallback list. Updated topology filter from `layer.id === 'user'` to `['user', 'shared', 'public'].includes(layer.id)`.
- `backend/app/api/vault_api.py` — Rewrote topology from 5-layer (User/Shared/Global/Public/Code) to 3-layer (User Vault, Shared Vaults, Public Vaults). Added `PUBLIC_SUB_LAYERS` for granular public vault access. Added `permissions` field. Removed Code layer (now Developer Lane).

## Summary of Changes

| File | Change |
|------|--------|
| `docs/VAULT_BINDER_WORKFLOW_INTEGRATION.md` | Major rewrite: 3 vault types, lane separation section, corrected diagram |
| `docs/DEVELOPER_SURFACE.md` | Added lane separation warning at top, boundary section at bottom |
| `docs/FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md` | Added boundary rules section, corrected vault path |
| `backend/app/api/vault_api.py` | 3-layer topology, removed Code, merged Global+Public, added sub-layers |
| `backend/app/af_manager/config.py` | Fixed stale fallback paths to canonical 3-layer architecture |
| `config/vault-sync.example.yaml` | Updated topology comment, merged containers, removed Code |
| `frontend-vue/src/skills/molecules/WorkspaceFilter.vue` | Show all 3 vault types in dropdown |
| `.tasker/vaul-consolidation-sync-repair.md` | This sprint plan (new) |

## Verification
- All documentation: 3 vault types (User, Shared, Public), Code excluded from vaults
- Lane separation rules: documented in all 3 core docs with agent boundary rules
- Backend topology: returns 3 layers with `permissions` field
- Sync engine: dry-run passes with 566 files detected
- Sidebar filter: now shows User, Shared, and Public vaults