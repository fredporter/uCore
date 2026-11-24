# Workflow tasks and Markdown

This is a proposed interchange contract. It records current behavior and the
checks required before changing storage or enabling notebook-to-task sync.

## Ownership and presentation

| Surface or adapter | Current role | Adopt or verify |
| --- | --- | --- |
| User Workflow in uCore | Board, rows, task editor, Binder context and workflow status. The Vue store uses the user-scoped Workflow API. | Keep the same task IDs and filter scope across Board and Rows. Show the next incomplete step, blockers, and approval state on the card. Keep detail and run history reachable from the selected task. |
| Cline Kanban | Engineering board with a terminal and worktree per development card, dependency-driven runs, diff review, and Git delivery. The workspace launcher exports a board snapshot. | Borrow board density, contextual detail, and visible activity. Use Cline's own CLI for development-card writes. Personal task moves go through uFlow. |
| Tasker | Markdown file adapter and compatibility API. The renderer lives in uFlow. | Reuse the renderer and converge active readers and writers on one codec before adding import paths. |
| SilverBullet | Notebook editor and index for Markdown pages and inline task checkboxes. | Qualify the disposable Binder pilot first. A checkbox can be captured into Workflow by explicit promotion with provenance. |

Use **Board**, **Rows**, **Task**, **Binder**, **Settings Form**, and **System Page**
as the user-facing labels in USX examples. Use descriptive `--usx-*` properties
for presentation and short dollar-prefixed IDs for registered system variables.
Use human-readable labels for task and settings values. Show a registry ID
alongside the label when the recipe teaches the system contract. YAML field keys
remain descriptive and stable.

[Cline Kanban](https://github.com/cline/kanban) ·
[Engineering board launcher](../../../DEV_ENGINEERING.md#development-kanban) ·
[Surface ownership](../SURFACE_OWNERSHIP.md#workflow-boundary) ·
[SilverBullet task notation](https://docs.silverbullet.md/Task) ·
[Binder pilot](../plans/KNOWLEDGE_COMPLETION_SPRINT.md#silverbullet-notebook-pilot)

## Read and write contract

The Tasker writer currently emits YAML frontmatter with `id`, `status`,
`priority`, provenance, timestamps and optional context, followed by an H1
and a Markdown body. Preserve stable `id` across renames, moves, and updates.
Keep `source` and `source_id` as provenance. Use the current Workflow status
vocabulary and normalize older spellings at intake. Preserve frontmatter fields
the current editor does not interpret and keep Markdown body structure intact.

The active Board routes are currently registered in `app.api.tasker_api`.
The older singular `/api/workflows/task/{task_id}` detail reader currently looks
for legacy `- key: value` metadata and can fall back to `todo` and `medium` for
files written with YAML. A local renderer-to-reader probe returned the filename
as the ID, defaulted `blocked/high` to `todo/medium`, and dropped the sample tags
and summary. The legacy reader also treats colon-bearing bullet lines as metadata
and strips list structure from summaries. This is a separate read path from the
user Board. Before consolidating it, test the writer-reader round trip with a
stable ID, a distinct source ID, a non-default status and priority, a due date,
tags, and body content containing lists and colons. Keep legacy bullet metadata
readable for historical files, limited to its recognized metadata region.

The frontend inline Markdown helper emits a checkbox plus `#tag`, `@board`
and `p:priority`. Its parser collapses completion to done or open and cannot
recover a full Workflow status or stable task ID. SilverBullet accepts
Markdown checkboxes and has its own inline attributes and custom states. For
portable capture, use a plain checkbox and preserve its source note and a stable
capture reference when promoting it. Keep Workflow IDs, status, priority and
provenance in the promoted task record. Treat custom SilverBullet states and
attributes as source data until individual mappings are specified and tested.

[Tasker renderer](../../backend/app/flow/task_store.py) ·
[Legacy task detail codec](../../backend/app/flow/workflow_api.py) ·
[Frontend Markdown helper](../../frontend-vue/src/utils/taskMarkdown.ts) ·
[SilverBullet task management](https://docs.silverbullet.md/Guide/Task%20Management)

## Acceptance sequence

1. Exercise one uFlow task through Board, Rows, and its editor. Verify a move,
   a failed write, approval handling, and consistent status after reload.
2. Add round-trip fixtures for current YAML files and legacy Tasker files.
   Then consolidate the detail codec. Verify duplicate captures are idempotent
   and revision conflicts leave the newer content intact.
3. Open the disposable SilverBullet notebook in Desktop. Link two notes with
   relative Markdown links, capture an inline checkbox, and promote it once.
   Reopen the notebook and Binder to verify source references and profile scope.
4. Review Cline Kanban side by side with Workflow using equivalent sample cards.
   Record which card details and keyboard actions improve the existing board.
   Revisit code reuse only if a particular upstream component answers a
   demonstrated need.
