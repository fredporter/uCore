> Archived 12 September 2026. Historical implementation evidence only; Dev Mode/internal IDE delivery direction is superseded. Start with the [current Gemini handover](../../HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md). Relative Markdown links below were rebased; prose and recorded claims are preserved, not recertified.

# Sprint 6 Release Notes — Dev Mode & Sovereign Workbench Program

**Release Date:** 2026-09-10  
**Program Status:** Completed (Sprints 0 through 6 closed)  
**Governance Authority:** uCore (Host & UI), uFlow (Tasks), uKnowledge (Research & Provenance), uCode (Runtime)  

---

## 1. Executive Summary

Sprint 6 marks the completion of the 2026-09 Dev Mode Long Sprint sequence. With the delivery of end-to-end product journey tests, published user guides, architectural component documentation, and full backlog reconciliation (76 of 76 tasks completed), all release gates for the Developer Workbench and Bangle Authoring environments are closed.

All code has been merged into `main` (PR #18), passing all CI checks, local verification suites, and storage boundary audits.

---

## 2. Exit Gate Compliance Record

The exit gates defined in [`docs/DEV_MODE_LONG_SPRINTS_2026-09.md`](../../DEV_MODE_LONG_SPRINTS_2026-09.md) have been satisfied:

### Gate 1: Major Lane Runtime, Command, and Test Proof
- **USX Design System & Recipe Hierarchy**: Delivered authentic USX patterns (`AuthoringRecipeView`, `RecipeGallerySurface`, cards, status tables, alert notifications). Separate showroom lanes for USX and GridCore.
- **Bangle Authoring & Research**: Frontmatter parsing and serialization roundtrips (`parseDocument`, `serializeDocument`), document variant generation, and academic citation formatting (APA, MLA, Chicago, Markdown, uKnowledge callouts) with URL provenance.
- **Sovereign Identity & Multi-Profile Boundary**: Multi-profile isolation (`default`, `developer`), `/api/identity/switch`, `/api/identity/logout`, and session token handling.
- **Settings Architecture**: Scoped user preferences synced via `/api/user/preferences` (with a 250ms debounce window), and system settings scoped per profile under `UDOS_HOME/system_settings.json`.
- **Per-Profile Chat Isolation**: Global AssistUI conversations partitioned by active profile key (`assistui-conversations-${profileId}`) and isolated backend chat history stores (`{user}_{profile}.json`).
- **GridCore Teletext & Monospace Engine**: Canvas-based character grid rendering with strict lane separation from standard USX surfaces.
- **Offline PWA Shell**: Pre-caching of 61 assets and Workbox service worker caching strategies for network-resilient local operation.

### Gate 2: Defect Status & Non-Regression
- **Accessibility**: Strict WCAG AA contrast ratios (>4.5:1), keyboard navigation shortcuts (`Cmd+S`, `Cmd+J`, `Ctrl+Opt+1..3`), modal focus traps, and Escape handling.
- **Data Integrity**: Zero data loss across profile switches; non-destructive YAML frontmatter serialization; conflict-safe atomic file saves.
- **Path Policy Compliance**: Verified clean via `python3 scripts/check_home_path_policy.py` with zero hard-coded home-root state paths.

### Gate 3: Vendor Isolation & Removal Posture
- **Governed Nanocoder Engine**: Nanocoder operates strictly as a construction engine behind the Agent Client Protocol (ACP). All operations require explicit user approval for destructive changes.
- **Independent Editor Operation**: Nanocoder removal leaves the Developer Surface editor, workspace tree, Git review panels, and repository file manipulation fully functional without requiring repository migration.
- **Zero Cloud Spend Invariant**: Execution relies strictly on local-first runtimes and local model providers (Ollama/Nanocoder).

### Gate 4: Explicitly Deferred Work & External Dependencies
- **Linux Platform Packaging**: Intake and native packaging for Linux (e.g. Zen Browser / Firefox profile integration, Wayland/X11 clipboard) remain deferred to a dedicated Linux intake milestone. macOS Safari and native PIM adapters are currently canonical.
- **Unified Messaging Inbox**: Advanced aggregation across Mail, Messages, and third-party chat platforms remains scoped as a post-release integration requiring formal privacy and sandbox reviews.
- **Distribution & SonicScrewdriver Pathway**: Post-program work proceeds according to [`docs/DISTRIBUTION_AND_SONIC_PATHWAY.md`](../../DISTRIBUTION_AND_SONIC_PATHWAY.md) following the mandatory specification reconciliation gate.

---

## 3. Verification & CI Evidence

| Gate / Test Suite | Scope | Target | Result |
| :--- | :--- | :--- | :--- |
| **Frontend Test Suite** | 23 test files | 85 unit and journey tests | **PASS** (100%) |
| **Backend Test Suite** | Identity, settings, chat history, DevChat | 20 pytest test cases | **PASS** (100%) |
| **TypeScript Typecheck** | `frontend-vue` | `vue-tsc --noEmit` | **PASS** (0 errors) |
| **Production PWA Build** | `frontend-vue` | `npm run build` | **PASS** (61 precached assets) |
| **Home Path Policy** | Root repository | `python3 scripts/check_home_path_policy.py` | **PASS** (OK) |
| **GitHub Actions CI** | PR #18 | Backend Tests, Frontend Build, Planning Governance | **PASS** (Clean) |

---

## 4. Documentation Index

- **User Guide**: [`docs/BANGLE_EDITOR_USER_GUIDE.md`](../../BANGLE_EDITOR_USER_GUIDE.md)
- **Architecture Guide**: [`docs/COMPONENT_ARCHITECTURE_GUIDE.md`](../../COMPONENT_ARCHITECTURE_GUIDE.md)
- **Dev Mode Sequence**: [`docs/DEV_MODE_LONG_SPRINTS_2026-09.md`](../../DEV_MODE_LONG_SPRINTS_2026-09.md)
- **Post-Program Pathway**: [`docs/DISTRIBUTION_AND_SONIC_PATHWAY.md`](../../DISTRIBUTION_AND_SONIC_PATHWAY.md)
- **Canonical Overview**: [`docs/README.md`](../../README.md)
