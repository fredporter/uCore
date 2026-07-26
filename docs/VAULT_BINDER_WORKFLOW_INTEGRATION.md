# Vault, Binder, Workflow, and AssistUI Integration

**Status:** Active Guide
**Scope:** User workflow — how vaults, binders, missions, tasks, and chat connect
**Audience:** uCore users building projects

## Overview

uCore has five vault layers, three workflow primitives (binders, missions, tasks), and two AssistUI tabs (Chat, Workflow). This guide explains how they all connect — and how to build a project from scratch.

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
              │                 Vault Layers                     │
              ├─────────┬─────────┬──────────┬────────┬─────────┤
              │ User    │ Shared  │ Global   │ Public │ Code    │
              │ ~/Vault/│~/Shared/│~/.public/│~/.pub/ │~/Code/  │
              │         │         │g-know/   │d-sites/│         │
              └────┬────┴────┬────┴──────────┴────────┴────┬────┘
                   │         │                              │
          ┌────────┴──┐ ┌────┴──────────┐        ┌─────────┴──────┐
          │ Binders   │ │ Shared        │        │ Code repos     │
          │ Missions  │ │ Workspaces    │        │ (git managed)  │
          │ Tasks     │ │               │        │                │
          │ Daily     │ │               │        │                │
          │ Journals  │ │               │        │                │
          └───────────┘ └───────────────┘        └────────────────┘
```

## 1. Vault Layers (Topology)

Defined in `backend/app/api/vault_api.py` and seeded via `plates/vault/*.yaml`:

| Layer | Path | Purpose | Permissions |
|-------|------|---------|-------------|
| **User** | `~/Vault/` | Personal documents, notes, binders, missions, tasks, daily, journals | Read/Write |
| **Shared** | `~/Shared/` | Team workspaces (e.g., uConnect/) | Read/Write (permission check) |
| **Global** | `~/Public/global-knowledge/` | Curated reference material | Read-only |
| **Public** | `~/Public/doc-sites/` | Published documentation sites | Publish-only |
| **Code** | `~/Code/` | Development repositories (git-managed) | Read/Write (dev lane) |

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

A **binder** is a project container inside a vault layer. It groups:
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
- All vault layer paths (`~/Vault/`, `~/Shared/`, etc.)
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
| `/api/vault/topology` | GET | List all vault layers with existence status |
| `/api/knowledge/workspaces` | GET | List AppFlowy workspaces |
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
| Chat LLM cannot actually call APIs | System prompt lists them; tool-calling plumbing needed |
| Workflow tasks don't sync from `.tasker/` to vault | Tasks are hardcoded samples; `.tasker/` sync is next phase |
| Binder file creation from chat | Not implemented — LLM tells you what to do, can't do it yet |
| Mission progress auto-update | Not implemented |

## 9. See Also

- [VAULT_PLATES_AND_DESTROY_SPEC.md](VAULT_PLATES_AND_DESTROY_SPEC.md) — Vault plates and DESTROY/REBUILD
- [SPOOL_SPEC.md](SPOOL_SPEC.md) — Activity feed and spool logging
- [DEVELOPER_SURFACE.md](DEVELOPER_SURFACE.md) — Developer Surface documentation
- [SETTINGS_ARCHITECTURE_2026.md](SETTINGS_ARCHITECTURE_2026.md) — Settings system
- [FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md](FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md) — Latest chat work