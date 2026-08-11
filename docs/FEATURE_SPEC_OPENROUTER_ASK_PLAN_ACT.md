# Feature Spec — OpenRouter/Free Ask → Plan → Act Pipeline

**Status:** Complete (Wave 1-3), Partial (Wave 4-5)
**Date:** 2026-08-11
**Scope:** Ask/Plan/Act modes in uCore Chat with OpenRouter free tier

---

## Overview

Added three new interaction modes to uCore Chat (Ask/Plan/Act) alongside the existing Chat and Workflow modes. The new modes leverage OpenRouter's free-tier models for research and planning, with a path to local vault operations in Act mode.

### Mode Summary

| Mode | Icon | Model | Execution | Context |
|------|------|-------|-----------|---------|
| **Chat** | chat | Ollama (local, free) | Tool-calling loop | Quick Q&A, vault-aware |
| **Plan** | psychology | OpenRouter free tier | Direct response, no tools | Vault + Repo + Skill context |
| **Act** | play_arrow | Ollama / OpenRouter | Tool-calling + confirm gate | Vault writes, web scrape |
| **Workflow** | account_tree | Ollama | Tool-calling | Task-focused |

---

## Architecture

```
Frontend (AssistUISurface.vue)
  └─ 4-mode toggle → useChatStore.sendMessage(mode)
       └─ POST /api/chat  { message, mode, model, history }
            ├─ plan → direct response with plan_steps[] and budget info
            ├─ act  → tool-calling loop with safety tools
            ├─ chat/workflow → tool-calling loop with full tools
            └─ budget check via BudgetManager
       └─ GET /api/chat/modes
            └─ Available modes + budget status
```

### Key Files

| File | Purpose |
|------|---------|
| `backend/app/api/chat.py` | Mode routing, system prompts, plan parsing, modes endpoint |
| `backend/app/services/provider_router.py` | Free-tier model registration, cost-annotated model list |
| `backend/app/services/chat_context.py` | Vault + Repo + Skill context gathering |
| `backend/app/api/routes.py` | Route registration for `/api/chat/modes` |
| `frontend-vue/src/stores/chat.ts` | Mode state, plan steps, budget status types |
| `frontend-vue/src/surfaces/assistui/AssistUISurface.vue` | 4-mode toggle, plan cards, budget badge |

---

## System Prompts

### `_UCORE_ASK_PLAN_SYSTEM` (Plan mode)
- Role: Research and planning assistant
- Knowledge sources: Vaults (~/Vault/, ~/Shared/, ~/Public/), Repos (~/Code/uCore/, ~/Code/uCode/), Skills
- Output format: Structured plans with ````plan` code blocks
- Rules: NEVER execute, always cite sources

### `_UCORE_ACT_SYSTEM` (Act mode)
- Role: Action-oriented assistant
- Capabilities: Research, scrape, summarize, save to vault
- Safety: Only write in ~/Vault/, confirm before actions

---

## Budget Integration

- **Plan mode**: Checks daily budget at ultra-cheap tier ($0.001/task). Falls back to Ollama (free) on exhaustion.
- **Act mode**: Checks session budget ($0.01/task). Blocks if exhausted.
- **Budget status**: Exposed via `GET /api/chat/modes` and tracked in `BudgetManager`.

---

## Plan Step Parsing

The `_parse_plan_steps()` function extracts structured steps from LLM responses:
- Searches for ````plan` code blocks
- Falls back to markdown checklists (`- [ ]` items)
- Extracts tool hints in `(tool: tool_name)` format
- Returns `PlanStep[]` with `{ description, tool, done }`

---

## Context Enrichment

`gather_chat_context(query, mode)` enriches system prompts with:
- **Vault documents**: Scans ~/Vault/, ~/Shared/, ~/Public/ for matching .md files
- **Repo snippets**: Uses `git grep` across ~/Code/uCore/ and ~/Code/uCode/
- **Skill catalog**: Lists available skills from `backend/app/skills/builtin/`
- Capped at 4000 characters to avoid token overflow

---

## Frontend Components

### Mode Toggle
4-way toggle rendering all `ASSISTUI_MODES` entries (Chat, Plan, Act, Workflow).

### Plan Card
Renders `planSteps[]` as an interactive checklist with:
- Step description
- Tool badge (if a tool is referenced)
- Done/undone state

### Act Confirmation Gate
Before executing Act mode tools, shows a confirmation dialog requiring user approval.

### Mode Badge
Colored indicator in the status bar showing the current mode (Research/Action).

### Model Picker
Shows free-tier models with cost badges (free/ultra-cheap/budget/mid-range/premium).

---

## Remaining Work (Wave 4-5)

- [ ] Wire `editor_api.py` scrape endpoint as a chat tool
- [ ] Wire save-to-vault as a chat tool with vault layer boundaries
- [ ] Full test suite for new functionality
- [ ] End-to-end smoke test (Plan → Approve → Act → Vault result)
- [ ] Update devlog, fieldnotes, wisdom
