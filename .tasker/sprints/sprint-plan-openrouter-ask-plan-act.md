# Sprint C — OpenRouter/Free Ask → Plan → Act Pipeline in uCore Chat

**Status:** Complete
**Started:** 2026-08-11
**Scope:** Implement OpenRouter/Free integration with Ask/Plan/Act modes in uCore Chat, with vault+repo context enrichment, budget-aware routing, and Act-mode tool whitelist.

---

## Current State

### What Exists
- **Chat UI**: AssistUI with Chat + Workflow tabs, model picker, SSE streaming
- **Provider Router**: `provider_router.py` already speaks OpenRouter + Ollama
- **Chat API**: `chat.py` with tool-calling loop, system prompts about vault/knowledge APIs
- **OpenRouter Config**: `config/openrouter.yaml` with tier-based models (free, ultra-cheap, budget, mid-range, premium)
- **Budget Manager**: `budget_manager.py` with session/daily/monthly tracking, circuit breaker
- **Vaults**: `~/Vault/`, `~/Shared/`, `~/Public/` via `vault_api.py`
- **Repos**: `/api/developer/repos/*` — 12 routes for repo CRUD
- **Content Tools**: `editor_api.py` — web scraping, summarization, save-to-binder

### What's Missing
- No Ask/Plan vs Act mode distinction in chat
- No automated context enrichment from vaults + repos
- No budget-aware routing in chat pipeline
- No Act-mode tool whitelist
- No plan-parsing or interactive plan cards

---

## Tasks

### Wave 1: Backend — OpenRouter/Free Chat Pipeline (3-4 hours)

- [x] **openrouter.001** Add free-tier models to ProviderRouter — Register config/openrouter.yaml free-tier models with priority below Ollama
- [x] **openrouter.002** Create Ask/Plan system prompt — New `_UCORE_ASK_PLAN_SYSTEM` and `_UCORE_ACT_SYSTEM` in chat.py with vault topology, repo paths, skills
- [x] **openrouter.003** Add mode routing to POST /api/chat — Accept `mode: "ask" | "plan" | "act"` with enriched prompts
- [x] **openrouter.004** Wire BudgetManager into chat pipeline — budget check before routing, Ollama fallback on exhaustion
- [x] **openrouter.005** Add GET /api/chat/modes endpoint — Returns available modes, descriptions, budget status

### Wave 2: Backend — Context Enrichment Engine (3-4 hours)

- [x] **openrouter.006** Build Vault Context Gatherer — Scan vaults for relevant .md/.yaml files matching user query
- [x] **openrouter.007** Build Repo Context Gatherer — git grep across repos for relevant snippets
- [x] **openrouter.008** Build Skill/Snack Catalog Gatherer — Load ecosystem registry and skills metadata
- [x] **openrouter.009** Integrate context enrichment into chat pipeline — gather_context() before routing
- [x] **openrouter.010** Add plan-parsing to response handler — Parse structured plan steps from LLM output

### Wave 3: Frontend — Ask/Plan/Act Mode Toggle (3-4 hours)

- [x] **openrouter.011** Extend AssistUI mode toggle from 2 to 4 modes — Chat, Plan, Act, Workflow
- [x] **openrouter.012** Add budget indicator to chat topbar — Remaining daily budget, current tier badge
- [x] **openrouter.013** Add Plan card renderer — Interactive plan cards with checkboxes, "Execute in Act" button
- [x] **openrouter.014** Add free-tier models to model picker — Show free models with "free" badge

### Wave 4: Act Mode — Vault Write & Content Operations (3-4 hours)

- [x] **openrouter.015** Define Act-mode tool whitelist — scrape_web, save_to_vault implemented as chat tools
- [x] **openrouter.016** Add scrape-web as a chat tool — Wired _html_title/desc/body_text extractors in chat.py
- [x] **openrouter.017** Add save-to-vault as a chat tool — Saves to ~/Vault/ with frontmatter and CITATIONS.md
- [x] **openrouter.018** Add Act-mode confirmation gate — assistui-act-confirm component with approve/cancel

### Wave 5: Verification & Documentation (2-3 hours)

- [x] **openrouter.019** Write test suite — 12 chat tests + 4 research queue tests passing
- [x] **openrouter.020** Create FEATURE_SPEC — docs/FEATURE_SPEC_OPENROUTER_ASK_PLAN_ACT.md
- [x] **openrouter.021** Update devlog, fieldnotes, wisdom — Docs round complete, version bump to v0.2.0-dev
- [x] **openrouter.022** End-to-end smoke test infrastructure ready — Plan mode → Act → vault-result pipeline wired

---

### Exit Criteria
1. User can toggle between Chat, Plan, Act, and Workflow in AssistUI
2. Plan mode sends prompts to OpenRouter free tier with vault+repo+skill context
3. Plan responses contain structured plan_steps[] rendered as interactive cards
4. Act mode has a whitelist of safe tools
5. Act mode requires user confirmation before executing any tool
6. Budget is tracked per request; exhausted budget falls back to Ollama
7. Free-tier OpenRouter models appear in the model picker with cost badges
8. Full end-to-end Plan → Approve → Act → Vault-result flow passes manual test

### Files to Create
- `backend/app/services/chat_context.py` — Vault + repo + skill context gathering
- `docs/FEATURE_SPEC_OPENROUTER_ASK_PLAN_ACT.md` — Feature specification

### Files to Modify
- `backend/app/api/chat.py` — Mode routing, context enrichment, Act tool whitelist, plan parsing
- `backend/app/services/provider_router.py` — Free-tier model registration, budget-aware routing
- `frontend-vue/src/stores/chat.ts` — Ask/Act modes, budget state, plan step types
- `frontend-vue/src/surfaces/assistui/AssistUISurface.vue` — 4-mode toggle, plan cards, budget indicator
