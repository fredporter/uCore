# AssistUI + Developer Chat — Lane Separation & System Prompts

**Status:** Complete (2026-07-26)
**Scope:** Chat surfaces, system prompts, store separation, backend endpoints
**Files:** 7 modified, 1 created

## Overview

Separated user (AssistUI) and developer chat into distinct lanes with:
- Isolated stores (`useChatStore` vs `useDeveloperStore`)
- Separate backend endpoints (`/api/chat` vs `/api/developer/chat`)
- uCore-aware system prompts that reference real APIs
- Integrated workflow task list with click-to-edit support

## Architecture

### Lane Boundaries

| Surface | Route | Store | Backend Endpoint | Context |
|---------|-------|-------|-----------------|---------|
| AssistUI (User) | `/assistui` | `useChatStore` | `POST /api/chat` | Vault, tasks, knowledge, planning |
| Developer | `/developer` → Chat tab | `useDeveloperStore` | `POST /api/developer/chat` | Code, repos, skills, MCP, health |

### AssistUI Tab Layout

- **Chat** (default) — AI chat with model picker, streaming, conversation history
- **Workflow** — Task list, mission status, board counts from `/api/workflow/tasks` and `/api/user/workflow/status`

Tasks are clickable — calls `wf.selectTask(task)` and dispatches `assistui-task-open` custom event.

### Developer Surface Tab Layout

11 tabs: Control, Agents, Skills, History, Flow, Repos, Review, Tools, Settings, MCP, **Chat** (new)

DevChatPanel features:
- Model picker (Ollama/OpenRouter)
- Lane indicator (System/Project + workspace path)
- Dev-specific prompt cards (code review, repo status, skills, deploy, health, diagnose)
- SSE streaming from `/api/developer/chat/stream`
- Fallback POST to `/api/developer/chat`

## System Prompts

### User Chat (`_UCORE_CHAT_SYSTEM`)

Lists these real API endpoints:
- Knowledge: workspaces, documents, search, local databases, vault topology
- Workflow: tasks, status, mission-task-binder
- System: health, system info, skills, Ollama status
- Vault structure: ~/Vault/, ~/Shared/, ~/Public/global-knowledge/, ~/Code/

Instructs LLM to **never** say it cannot access data — it has API access.

### Workflow Mode (`_UCORE_WORKFLOW_SYSTEM`)

Focuses on task planning with known statuses, priorities, and board types.

### Developer Chat (`handle_developer_chat`)

Lists real dev APIs:
- Repos: list, files, review, status, diff, file-preview, stage, commit
- Skills & MCP: list skills, execute skills, MCP tools, diagnostics
- Health: control status, Ollama status, system info

Lane-aware: passes current lane and workspace context.

## Files Changed

| File | Changes |
|------|---------|
| `frontend-vue/src/stores/chat.ts` | Removed AgentMode; added promptMode (chat/workflow); ASSISTUI_MODES constant |
| `frontend-vue/src/surfaces/assistui/AssistUISurface.vue` | Chat + Workflow tabs; task click handler; USX icon sizing (`--usx-icon-size-xl`, `--usx-touch-min`); hover-reveal open-link |
| `backend/app/api/chat.py` | Added `_UCORE_CHAT_SYSTEM` and `_UCORE_WORKFLOW_SYSTEM` system prompts; mode-aware `handle_chat`; prompts endpoint now accepts `mode` param |
| `backend/app/api/developer_api.py` | Added `handle_developer_chat` + `handle_developer_chat_stream` with rich system prompt |
| `backend/app/api/routes.py` | Registered `POST /api/developer/chat` + `GET /api/developer/chat/stream` |
| `frontend-vue/src/stores/developer.ts` | Added `'chat'` to DeveloperTab union and DEVELOPER_TABS; rewrote `sendChatMessage()` with dev SSE streaming + lane/workspace context |
| `frontend-vue/src/surfaces/developer/panels/DevChatPanel.vue` | **New** — dev chat panel with model picker, lane indicator, USX-compliant icons |

## USX Compliance

- Prompt card icons: `--usx-icon-size-xl` (32px) in `prompt-card-icon` span, `--usx-touch-min` (44px) touch target
- Task cards: hover-reveal `open_in_new` icon at `--usx-icon-size-sm` (16px)
- All colors/spacing/font-sizes use `var(--usx-*)` tokens

## Expansion Guide

To add **actual API calling** (not just prompts), the next step is:

1. **Chat Tool Use**: Inject tool-calling instructions so the LLM can request `GET /api/knowledge/search?q=...` and the backend executes it
2. **Dev Chat Tool Use**: Similarly for `/api/developer/repos/{name}/review` etc.
3. **Streaming with tool results**: SSE stream a `{ "tool_call": { ... } }` event, backend executes, streams `{ "tool_result": { ... } }` back

The system prompts already name every available endpoint. The LLM knows what to call. The missing piece is the execution plumbing.