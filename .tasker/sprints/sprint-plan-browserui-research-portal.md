# Sprint D — BrowserUI Research Portal Upgrade

**Status:** Complete
**Started:** 2026-08-11
**Scope:** Transform BrowserUI into an automated research web portal with binder integration, ChatUI assistant bridge, and prose-style preview/editing tabs.

---

## Current State

### BrowserUI (single file, 754 lines)
At `frontend-vue/src/surfaces/browserui/BrowserUISurface.vue`:
- Card stacks with hardcoded defaults (Research, Bookmarks, Learning)
- Search/filter, slide-in editor panel (Expand, Summarise, Research buttons)
- "Open in Markdown Editor" dispatches to workflow store
- Uses `webScraper.ts` → `/api/editor/scrape-web`

### Existing Backend
- `editor_api.py`: scrape, summarise, save-to-binder endpoints
- `chat.py`: `scrape_web` and `save_to_vault` chat tools (from Sprint C)
- `mission_task_binder_adapter.py`: Binder metadata adapter
- `chat_context.py`: Vault context gathering (from Sprint C)

### What's Missing
- No research queue API (async scrape→summarise→save pipeline)
- No quality scoring (auto-compute from token count + AI confidence)
- No binder metadata files (`binder.json`, `CITATIONS.md`)
- No ChatUI assistant bridge from BrowserUI
- Summarise/Enhance buttons are stubs (no backend AI call)
- No "Research" tab with request → queue → result flow
- Cards not sortable by score/category
- No prose preview vs raw edit distinction

---

## Architecture

```
BrowserUI Shell
├── ResearchDashboard.vue    Queue, status, progress, "Research Gaps"
├── CardStack.vue             Sortable cards, score badges, tag filters
├── PreviewTab.vue            Prose-style rendered markdown
├── EditTab.vue               Markdown editor with binder context
└── ApiBridge.ts              Unified API client

Backend (new)
├── research_api.py           POST /api/research/start, /status, /cancel
├── binder_api.py             GET/POST/PATCH /api/binder/*
├── research_queue.py         Async job: scrape→summarise→enhance→save
└── quality_scorer.py ext     Auto-score: tokens × confidence → 0-5
```

---

## Tasks

### Wave 1: Backend Research API (2 hours)

- [x] **browser.001** Create `research_api.py` — `POST /api/research/start`, `GET /api/research/status`, `POST /api/research/cancel`. Body: { url, binderId, tags, mode: "summarise"|"enhance"|"full" }.
- [x] **browser.002** Create `research_queue.py` — lightweight async job queue (SQLite-backed). Jobs: scrape → summarise (ChatUI) → enhance (optional) → save to binder. Track state/progress.
- [x] **browser.003** Create `binder_api.py` — `GET /api/binder/list` (all binders with metadata), `POST /api/binder/add`, `PATCH /api/binder/update`, `PATCH /api/binder/score`.
### Wave 2: Frontend Panel Decomposition (3 hours)

- [x] **browser.005** Split BrowserUI into shell + sub-panels. `BrowserUISurface.vue` becomes a tab router. Create `panels/` directory with `ResearchDashboard.vue`, `CardStack.vue`, `PreviewTab.vue`, `EditTab.vue`.
- [x] **browser.006** `CardStack.vue` — sortable by date/score/category. Drag-and-drop between stacks. Category tags as filter chips. Quality score badge (color-coded 0-5 green→yellow→red). "Research" quick-action per card.
- [x] **browser.007** `PreviewTab.vue` — prose-style rendered markdown. Frontmatter metadata table. Source citation block with favicon. Expand/collapse sections. "Send to ChatUI" button.
- [x] **browser.008** `EditTab.vue` — markdown editor. Binder context indicator. Auto-insert frontmatter. Save-to-binder with confirmation. Undo/redo via textarea history.
- [x] **browser.009** `ResearchDashboard.vue` — queue list with progress bars. Scraper logs panel. "Approve & Commit" per-topic. "Request Research" button pushes to ChatUI. "Research Gaps" section from vault analysis.

### Wave 3: ChatUI Assistant Bridge (2 hours)

- [x] **browser.010** `POST /api/research/summarise` — delegates to ChatUI Plan mode. Body: { text, model, budget }. Returns structured summary + citations + suggested tags.
- [x] **browser.011** "Send to ChatUI" button in PreviewTab → dispatch to `chatStore.sendMessage()` with research content pre-filled in Plan mode. Opens AssistUI surface or inline chat panel.
- [x] **browser.012** Batch research: multi-select cards → "Research All" → queue processes each → results grouped into single binder with cross-reference index.

### Wave 4: Binder File System (2 hours)

- [x] **browser.013** `binder.json` schema: `{ name, description, created, updated, score, tags, sources: [{url, title, date}] }`. Created per binder directory.
- [x] **browser.014** `CITATIONS.md` auto-generation: append source URL + access date + title on scrape complete. Format: `- [Title](URL) — accessed YYYY-MM-DD`
- [x] **browser.015** Save flow: research result → `~/Vault/<binder>/` or `global-knowledge/<binder>/`. Update `SUMMARY.md` with new entry.

### Wave 5: Polish & Verification (2 hours)

- [x] **browser.016** Vault knowledge gap detection: scan `SUMMARY.md` for broken/missing links → suggest topics in "Research Gaps" dashboard section.
- [x] **browser.017** Topic enhancement: existing binder doc → "Enhance" → ChatUI expands with deeper detail → diff preview → approve merge.
- [x] **browser.018** E2E smoke test: scrape URL → summarise via ChatUI → save to binder → view in PreviewTab → edit → approve → verify CITATIONS.md updated.

---

### Exit Criteria
1. BrowserUI has Dashboard, Preview, Edit tabs with card stack + queue view
2. Cards sortable by score/category/tags with quality score badge
3. Research queue API: scrape → ChatUI summarise → save to binder, end to end
4. "Send to ChatUI" pushes content to AssistUI Plan mode
5. Binder files created with binder.json + CITATIONS.md + SUMMARY.md updated
6. All new endpoints respond and tests pass

### Files to Create
- `backend/app/api/research_api.py` — async research endpoints
- `backend/app/services/research_queue.py` — SQLite-backed job queue
- `backend/app/api/binder_api.py` — binder CRUD endpoints
- `frontend-vue/src/surfaces/browserui/panels/ResearchDashboard.vue`
- `frontend-vue/src/surfaces/browserui/panels/CardStack.vue`
- `frontend-vue/src/surfaces/browserui/panels/PreviewTab.vue`
- `frontend-vue/src/surfaces/browserui/panels/EditTab.vue`
- `frontend-vue/src/surfaces/browserui/ApiBridge.ts` — unified API client

### Files to Modify
- `frontend-vue/src/surfaces/browserui/BrowserUISurface.vue` → shell with tab routing
- `backend/app/api/routes.py` → register research + binder routes
- `backend/app/services/quality_scorer.py` → add auto-score function

- [x] **browser.004** Extend `quality_scorer.py` — auto-score: token count × AI confidence → 0-5 scale with color code. Store in binder metadata.
