# Vault, Binder, Workflow, and AssistUI Integration

**Status:** Active Guide
**Scope:** User workflow — how vaults, binders, missions, tasks, and chat connect
**Audience:** uCore users building projects

## Overview

uCore has three vault types, three workflow primitives (binders, missions, tasks), and two AssistUI tabs (Chat, Workflow). This guide explains how they all connect — and how to build a project from scratch.

```
                    ┌──────────────────────────────────────────┐
                    │            AssistUI (/assistui)           │
                    ├────────────────┬─────────────────────────┤
                    │   Chat Tab     │    Workflow Tab         │
                    │  (AI assistant)│  (tasks, missions,      │
                    │  knows vault   │   board status)         │
                    │  structure)    │                          │
                    └───────┬────────┴──────────┬──────────────┘
                            │                   │
              ┌─────────────┴──┐    ┌───────────┴───────────────┐
              │ /api/chat      │    │ /api/workflow/tasks        │
              │ (with system   │    │ /api/user/workflow/status  │
              │  prompt about  │    │ /api/knowledge/...         │
              │  vault APIs)   │    │ /api/knowledge/adapter/    │
              └───────────────┬┘    └───────────┬───────────────┘
                              │                 │
              ┌───────────────┴─────────────────┴───────────────┐
              │                 Vault Types                      │
              ├─────────────┬───────────────┬───────────────────┤
              │ User        │ Shared        │ Public            │
              │ ~/Vault/    │ ~/Shared/     │ ~/Public/         │
              │ (personal)  │ (team)        │ (reference)       │
              └──────┬──────┴──────┬────────┴──────┬────────────┘
                     │             │               │
          ┌──────────┴──┐  ┌───────┴────────┐  ┌───┴────────────┐
          │ Binders     │  │ Shared        │  │ Templates      │
          │ Missions    │  │ Workspaces    │  │ Examples       │
          │ Tasks       │  │               │  │ Global Docs    │
          │ Daily       │  │               │  │                │
          │ Journals    │  │               │  │                │
          └─────────────┘  └───────────────┘  └────────────────┘
```

**Note:** `~/Code/` is **not** a vault. It is part of the Developer Lane (see section 9).

## 1. Vault Types (Topology)

Defined in `backend/app/api/vault_api.py` and seeded via `plates/vault/*.yaml`:

| Type | Path | Purpose | Permissions |
|------|------|---------|-------------|
| **User** | `~/Vault/` | Personal workspace — **the single source of truth**. All your binders, documents, notes, missions, tasks, daily, journals. | Read/Write |
| **Shared** | `~/Shared/[vault-name]/` | Collaborative vaults for team projects. Each shared vault is a separate directory. | Read/Write (permission check) |
| **Public** | `~/Public/[vault-name]/` | Published, system-provided, or community-contributed vaults. Includes `global-knowledge/`, `doc-sites/`, `learning/`, templates. | Read-only |

### User Vault Directory Structure

Seeded by `plates/vault/user_vault_seed.yaml`:

```
~/Vault/
├── @inbox/              Quick capture (pending/processed/failed)
├── @groovebox/          Creative workspace (music, production)
├── knowledge/           Personal knowledge base
│   ├── concepts/
│   ├── insights/
│   └── research/
├── binders/             Project collections
│   ├── active/          Current projects
│   ├── completed/       Finished projects
│   ├── on-hold/         Paused projects
│   └── templates/       Binder templates
├── missions/            Mission tracking
│   ├── active/
│   ├── completed/
│   └── templates/
├── tasks/               Individual task files
├── daily/               Daily notes
├── journals/            Journal entries
├── people/              Contact directory
├── agents/              AI agent definitions
├── attachments/         File attachments
├── scripts/             Automation scripts (.ucode)
├── security/            Security policies
├── templates/           Personal templates
└── dev/                 Development scratch space
```

## 2. Binders — Project Containers

### What is a Binder?

A **binder** is a project container inside a vault. It groups:
- Documents (Markdown, YAML)
- Tasks (linked from `.tasker/`)
- References
- Publishable work

### Creating a Binder

Each binder has a `_binder.yaml` descriptor:

```yaml
# ~/Vault/binders/active/MyProject/_binder.yaml
id: my-project
name: My Project
status: active
description: A new project to build something useful.
```

**Binder statuses:** `active`, `completed`, `on-hold`

**Default binder:** `Sandbox` — always available at `~/Vault/binders/active/Sandbox/`

### Binder Document Format

Documents inside a binder use YAML frontmatter:

```markdown
---
title: Project Plan
binder: My Project
mission: Build Phase 1
tags: [planning, phase-1]
---

# Project Plan

Steps to build the thing...
```

The `binder` field links the document to its binder. The `mission` field links to a mission.

## 3. Missions — Goal Tracking

Missions are higher-level goals that span multiple tasks and documents.

```yaml
# ~/Vault/missions/active/build-phase-1.yaml
id: build-phase-1
title: Build Phase 1
status: active
priority: high
description: Complete the first phase of the project build.
task_ids:
  - task.001
  - task.002
  - task.003
```

Missions appear in the AssistUI Workflow tab via `/api/knowledge/adapter/mission-task-binder`.

## 4. Tasks — Action Items

Tasks are managed in `.tasker/` Markdown files with YAML frontmatter:

```markdown
---
id: task.001
title: "Set up project structure"
status: in-progress
priority: high
board: planning
tags: [setup, project]
---

# Set up project structure

1. Create the binder directory
2. Add _binder.yaml
3. Create initial documents
4. Link to mission
```

**Task statuses:** `todo`, `in-progress`, `review`, `blocked`, `completed`
**Priorities:** `low`, `medium`, `high`
**Boards:** `planning`, `writing`, `admin`, `learning`, `personal`, `finance`, `general`

Tasks appear in AssistUI Workflow tab via `/api/workflow/tasks?scope=user`.

### Clicking a Task

In the Workflow tab, clicking a task:
1. Calls `wf.selectTask(task)` — opens editor with task content
2. Dispatches `assistui-task-open` custom event

## 5. AssistUI Integration

### Chat Tab

The chat tab connects to `/api/chat` with the `_UCORE_CHAT_SYSTEM` system prompt. The LLM knows:
- All vault paths (`~/Vault/`, `~/Shared/`, `~/Public/`)
- Knowledge APIs: `/api/knowledge/search`, `/api/knowledge/workspaces`, `/api/knowledge/documents`
- Workflow APIs: `/api/workflow/tasks`, `/api/user/workflow/status`
- System APIs: `/api/health`, `/api/skills`

**Speak naturally.** Ask: *"What's in my vault?"* → LLM suggests searching via `GET /api/knowledge/search?q=...`

### Workflow Tab

Shows:
- Task counts (total, in-progress, completed)
- Board breakdown from tasker
- Clickable task cards with status, priority, tags
- Mission list with task counts

Data sources:
- `/api/workflow/tasks?scope=user` — task list
- `/api/user/workflow/status` — board counts
- `/api/knowledge/adapter/mission-task-binder` — mission/task/binder projections

## 6. Building a Project — Step by Step

### Step 1: Create a Binder

```bash
mkdir -p ~/Vault/binders/active/my-project
```

Create `~/Vault/binders/active/my-project/_binder.yaml`:

```yaml
id: my-project
name: My Project
status: active
description: My first uCore project.
```

### Step 2: Create a Mission

Create `~/Vault/missions/active/my-first-mission.yaml`:

```yaml
id: my-first-mission
title: My First Mission
status: active
priority: medium
description: Learn how binders, missions, and tasks work together.
task_ids: [task.project.001, task.project.002]
```

### Step 3: Create Tasks

Create `.tasker/tasks/task.project.001.md`:

```markdown
---
id: task.project.001
title: "Write project README"
status: todo
priority: medium
board: writing
tags: [project, docs]
---

# Write project README

Create a README that explains what this project does.
```

Create `.tasker/tasks/task.project.002.md`:

```markdown
---
id: task.project.002
title: "Create first document"
status: todo
priority: medium
board: writing
tags: [project, docs]
---

# Create first document

Write the first document inside the binder.
```

### Step 4: Add a Document to the Binder

Create `~/Vault/binders/active/my-project/docs/project-plan.md`:

```markdown
---
title: Project Plan
binder: my-project
mission: my-first-mission
tags: [planning, project]
---

# Project Plan

## Goals
- Learn how uCore binders work
- Connect tasks to a mission
- Use the chat to explore my vault

## Next Steps
1. Mark task.project.001 as in-progress
2. Write the README
3. Review in AssistUI Workflow tab
```

### Step 5: Open AssistUI

Go to `http://localhost:5175/assistui`

**Chat tab** — ask: *"Look in my vault and tell me about my binders"*
The LLM will suggest searching via `/api/knowledge/search?q=binder`

**Workflow tab** — see your tasks with status, priority, and board.
Click a task to open it in the editor.

## 7. API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/vault/topology` | GET | List all vault types with existence status |
| `/api/knowledge/workspaces` | GET | List vault layers and registered workspaces |
| `/api/knowledge/documents?workspace_id=...` | GET | List documents in a workspace |
| `/api/knowledge/search?q=...` | GET | Semantic search across vault documents |
| `/api/knowledge/local/databases` | GET | List local SQLite databases |
| `/api/knowledge/local/query` | POST | Execute SQL query on a local database |
| `/api/workflow/tasks?scope=user` | GET | List user tasks |
| `/api/user/workflow/status` | GET | Overall workflow status with board counts |
| `/api/knowledge/adapter/mission-task-binder` | GET | Mission/task/binder projection table |
| `/api/chat` | POST | Chat with uCore assistant (mode: chat/workflow) |
| `/api/chat/prompts?mode=...` | GET | Get prompt cards for Chat or Workflow tab |

## 8. Current Gaps (What's Not Yet Wired)

| Gap | Status |
|-----|--------|
| Chat tool-calling (Act mode) | ✅ Implemented — `scrape_web` + `save_to_vault` chat tools (see `FEATURE_SPEC_OPENROUTER_ASK_PLAN_ACT.md`) |
| Workflow tasks sync from `.tasker/` to vault | Partial — `tasker_sync` skill exports rows; full two-way sync pending |
| Binder file creation (`binder.json`, `CITATIONS.md`) | ✅ Implemented via BrowserUI research queue |
| Mission progress auto-update | Not implemented |

## 9. Lane Separation — Boundary Rules

uCore enforces a strict separation between user content and system code:

### User Lane (The Product)

- **Who:** End users, creators, builders
- **What:** Vaults, binders, documents, missions, tasks, uCode (BASIC) files
- **Where:** `~/Vault/`, `~/Shared/`, `~/Public/`
- **Risk:** Low — data/content only
- **Visibility:** Main UI, AssistUI, Workflow tabs
- **Rule:** User Lane agents never access `~/Code/uCore/` or any system codebase

### Developer Lane (The Tool)

- **Who:** System developers, contributors, maintainers
- **What:** uCore/uCode codebase, companion repos, internal tools, skills, agents
- **Where:** `~/Code/uCore/`, `~/Code/uCode/`, companion repos
- **Risk:** High — can break the system
- **Visibility:** Developer Surface, hidden by default
- **Rule:** Developer Lane agents never modify user vaults unless explicitly directed

### Boundary Rules

1. **User Lane agents** (AssistUI chat) work only on vault content, binders, docs, and uCode (BASIC) files. They never touch the system codebase.
2. **Developer Lane agents** (Hivemind, Roundtable, Cline) work only on the codebase. They never touch user vaults unless explicitly directed.
3. The Assistant should ask which lane the user intends before performing ambiguous actions.
4. The Developer Surface is hidden by default (can be enabled in Settings).
5. The default lane in AssistUI is **User**.
6. **Vaults are for user content** (`~/Vault/`, `~/Shared/`, `~/Public/`). They contain binders, documents, mission definitions, and uCode (BASIC) files.
7. **`~/Code/` is for developer work** — it is the codebase where system development happens, not a vault.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER LANE                                  │
│  AssistUI (Chat)  │  Workflow  │  Binders  │  Missions  │  Vaults │
│  Everyone starts here. This is where you build projects.           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Advanced users only)
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DEVELOPER LANE                               │
│  Developer Surface (Control │ Agents │ Skills │ Repos │ DevChat)  │
│  Only for modifying the system or building companion repos.        │
│  Most users never need this.                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 10. See Also

- [VAULT_PLATES_AND_DESTROY_SPEC.md](VAULT_PLATES_AND_DESTROY_SPEC.md) — Vault plates and DESTROY/REBUILD
- [SPOOL_SPEC.md](SPOOL_SPEC.md) — Activity feed and spool logging
- [DEVELOPER_SURFACE.md](DEVELOPER_SURFACE.md) — Developer Surface documentation
- [SETTINGS_ARCHITECTURE_2026.md](SETTINGS_ARCHITECTURE_2026.md) — Settings system
- [FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md](FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md) — Chat lane separation spec