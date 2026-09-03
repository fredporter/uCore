# Dev Mode and Product Long Sprints — 2026-09

Status: Canonical execution sequence; baseline reconciled 2026-09-01
Owner: uCore
Related owners: uFlow task authority, uCode runtime authority, uKnowledge research authority

## Outcome

Deliver a dependable Developer Workbench, complete the editor and research
backlog, connect user-owned services, and close the release gates without
creating duplicate task, automation, model, or runtime authorities.

This plan uses one two-week reconciliation sprint followed by six four-week
construction sprints. Each sprint must end in a shippable checkpoint; unfinished
work returns to the backlog rather than silently rolling into the next sprint.

## Product boundaries

- Server owns models, agents, budgets, services, automations, skills, extensions,
  and logs.
- Workflow owns missions, tasks, binders, and references to Server automations.
- Developer owns repository discovery, file editing, Git review, and approved
  construction actions.
- The global chat widget is the only chat UI.
- uFlow remains the task and workflow source of truth.
- Nanocoder is the governed Dev Mode construction engine. uCore owns its process,
  repository scope, permissions, budgets, audit, and lifecycle through ACP.
- The code editor remains a presentation/editing engine, not a task store,
  provider router, terminal authority, or replacement repository API.

## Sprint 0 — Reconcile and freeze the baseline (2 weeks)

### Scope

1. Review and split the current large working-tree change set into coherent,
   testable checkpoints.
2. Reconcile `frontend-vue/src/tasks/bangle-upgrade.tasks.ts` against completed
   editor, surface, research, chat, and workspace work.
3. Update surface ownership documentation for the Server, Workflow, System,
   Developer, and global chat consolidation.
4. Capture browser journeys for Dashboard, Workflow, Developer, Server, System,
   and the chat widget.
5. Establish focused frontend and backend test commands for every later sprint.

### Exit gates

- Reviewed change groups with no accidental mixing of unrelated user changes.
- Task counts are generated from real task objects rather than text matching.
- Type-check, production build, focused backend tests, and canonical browser
  journeys pass.
- The active delivery branch has an explicit merge disposition.

## Sprint 1 — Nanocoder intake and ACP engine boundary (4 weeks)

Progress on 2026-09-01: immutable npm intake, dependency audit, isolated config,
loopback provider policy, fake ACP contract suite, and real initialize handshake
are complete. The handshake exposed an upstream repository-local task-store
write; the pinned installer patch and `NANOCODER_TASKS_DIR` supervisor policy
now redirect it to `UDOS_HOME`, with a clean repeated smoke test. Activation
remains gated on Server runtime policy/audit and the Developer operations UI.

### Scope

1. Complete immutable intake for `Nano-Collective/nanocoder`: pin release,
   package/artifact integrity, MIT licence, supported Node/macOS versions, and
   deterministic install/removal under `UDOS_HOME`.
2. Implement a uCore-owned ACP client and supervised process adapter for
   `nanocoder --acp` using JSON-RPC over stdin/stdout.
3. Map ACP initialization, sessions, streaming content, tool calls, diffs,
   permission requests, modes, models, plan updates, cancellation, and errors
   into bounded internal types.
4. Force Nanocoder configuration and logs into uCore-owned `UDOS_HOME` paths;
   never rely on implicit home-directory configuration discovery.
5. Resolve provider, model, agent, and budget policy from Server authority before
   creating a Nanocoder session.
6. Build a fake ACP server and contract suite before invoking the real binary.

### Exit gates

- Immutable provenance, licence, integrity, installation, and removal evidence.
- Fake and real ACP initialize/session/stream/cancel tests pass.
- Nanocoder cannot select an unapproved repository, provider, model, or secret.
- Dev Mode off prevents process launch; process failure leaves the editor usable.

## Sprint 2 — Developer Workbench foundation (4 weeks)

### Scope

1. Replace the current three-step Code/Repository/Editor journey with a coherent
   workbench layout: repository switcher, searchable tree, editor tabs, status
   bar, and contextual review panel.
2. Preserve selected repository, file, open tabs, and panel layout per session.
3. Add file create, rename, move, and delete flows through bounded developer APIs
   with confirmation where destructive.
4. Add command palette, go-to-file, in-file search, and repository search.
5. Add diagnostics and language-service surfaces only through explicit adapters;
   unsupported languages remain honest rather than simulated.
6. Add a Dev Mode operations panel driven by ACP: session transcript, plan,
   tool/diff cards, approve/deny controls, stop, and audit link. It is contextual
   to the selected repository and editor, not a second global chat UI.
7. Make desktop, narrow-window, and keyboard-only layouts first-class.

### Exit gates

- A repository can be opened, searched, edited, saved, and restored in one
  continuous browser journey.
- Dirty-state and external-change conflicts cannot silently discard content.
- The workbench has no duplicate chat, model, agent, automation, or task UI.
- Accessibility smoke checks cover tree, tabs, palette, editor, and review panel.
- Nanocoder suggestions and diffs remain proposals until uCore approves and
  applies them through repository APIs.

## Sprint 3 — Git review and governed construction (4 weeks)

### Scope

1. Consolidate authoritative diff, staged/unstaged state, review, and commit
   preparation into the Developer review panel.
2. Add per-file and repository-wide diff navigation, hunk staging where the API
   can support it safely, and explicit conflict presentation.
3. Surface test/build commands as repository-defined actions with bounded output,
   cancellation, duration, and audit records.
4. Link Developer work to uFlow task references without copying task state into
   uCore.
5. Route reusable execution through the Server Automations/Skills runner.
6. Retain explicit user review before any write-capable vendor-tool invocation.
7. Add deep internal-development actions: explain selection, diagnose failure,
   propose tests, plan refactor, implement reviewed task, and review working tree.
   Each action sends bounded editor/repository context through the ACP session.

### Exit gates

- Edit → diff → test → stage → commit-preparation is traceable and recoverable.
- Dirty-worktree, traversal, cancellation, timeout, and output-redaction tests pass.
- Workflow task references and Server runner links preserve their owning APIs.
- No autonomous commit, push, merge, or task-status-triggered code edit exists.

## Sprint 4 — Authoring and research completion (4 weeks)

### Scope

1. Finish the frontmatter editor and enhanced formatting toolbar.
2. Complete formatting commands, responsive toolbar behavior, and keyboard
   shortcuts.
3. Add toolbar research capture, Combine Research, variants, and citations using
   uKnowledge persistence and provenance contracts.
4. Finish StoriesOverlay renderer integration.
5. Align the Workflow editor and Developer editor through shared primitives only;
   keep prose workflow and repository-code behavior distinct.
6. Complete unit and component coverage for editor utilities and interactions.

### Exit gates

- Frontmatter round-trips without corrupting Markdown.
- Research outputs retain source and citation provenance.
- Formatting, variants, and renderer routing have focused regression tests.
- Developer code files never enter the user Binder implicitly.

## Sprint 5 — Identity, settings, chat history, and offline shell (4 weeks)

### Scope

1. Integrate user identity and clear unauthenticated states.
2. Replace cross-surface preference `localStorage` ownership with the settings API,
   including migration and offline fallback.
3. Add per-user chat-history persistence to the global widget, including clear
   history and retention behavior.
4. Add the service worker, app-shell caching, offline indicator, and bounded sync
   queue.
5. Add mobile gestures, editor-toolbar collapse, and an install prompt.

### Exit gates

- Identity, preferences, and chat records cannot leak between users.
- Offline changes expose queued/conflicted state and never claim a false save.
- One chat widget remains the only chat entry point on desktop and mobile.
- PWA cache invalidation and upgrade behavior are tested.

## Sprint 6 — Hardening, documentation, and release (4 weeks)

### Scope

1. Complete end-to-end tests for the primary product journeys.
2. Run mobile, responsive, dark/light theme, keyboard, and accessibility audits.
3. Profile startup, editor load, large repositories, large files, and long chat
   sessions; fix measured bottlenecks.
4. Write component documentation, the editor user guide, operator runbooks, and
   vendor lifecycle/removal documentation.
5. Reconcile active specs, archive superseded plans, and update canonical README
   pointers.
6. Execute protected-branch CI and clean-checkout smoke tests.

### Exit gates

- Runtime, command, test, and evidence proof is recorded for every major lane.
- No critical accessibility or data-loss defect remains open.
- Nanocoder removal leaves the Developer editor and repository workflow usable
  without repository-data migration.
- Release notes identify deferred work and externally blocked dependencies.

## Nanocoder integration posture

Nanocoder is the construction engine behind Dev Mode operations, not a new
surface and not the editor widget itself. ACP is the primary interactive
transport because it preserves streaming, tool cards, diffs, approvals, plan
updates, model selection, and cancellation. Non-interactive `--json run` is
reserved for bounded smoke tests and explicitly approved Server automations.

Nanocoder's internal task list, skills, provider configuration, and MCP support
must not become competing uCore authorities:

- ACP plan updates may be displayed within a session, while durable tasks remain
  uFlow references.
- Nanocoder provider/model requests are constrained by Server policy and budget.
- uCore Server skills remain canonical; any Nanocoder skill bundle is an adapter
  generated from an approved Server skill contract or an explicitly isolated
  vendor capability.
- External MCP servers remain direct third-party connections unless a separate
  reviewed uCore integration owns the lifecycle.

## Backlog mapping

| Existing backlog lane | Owning sprint |
| --- | --- |
| Frontmatter editor and formatting toolbar | Sprint 4 |
| Research combine, variants, citations, scrape entry | Sprint 4 |
| Unit, component, E2E, accessibility, docs, performance | Sprints 0, 4, and 6 |
| Identity, settings, chat persistence | Sprint 5 |
| PWA and mobile enhancements | Sprint 5 |
| Nanocoder ACP and Developer Surface revamp | Sprints 1–3 |

## Canonical 28-item backlog ledger

This table is the complete open set derived from
`BANGLE_UPGRADE_TASKS`. Partial working-tree improvements do not close an item
until its checklist and focused tests provide evidence.

| Sprint | Backlog IDs | Count |
| --- | --- | ---: |
| Sprint 4 — authoring UI | `bangle-p3-001`, `bangle-p3-002`, `bangle-p3-003`, `bangle-p3-004`, `bangle-p3-005` | 5 |
| Sprint 4 — research and renderer | `bangle-p5-003`, `bangle-p6-003`, `bangle-p6-005`, `bangle-p6-006`, `markdown-p9-004` | 5 |
| Sprint 4/6 — test evidence | `bangle-test-001`, `bangle-test-002`, `bangle-test-003`, `bangle-test-004`, `bangle-test-005`, `bangle-test-006` | 6 |
| Sprint 6 — docs and release | `bangle-doc-001`, `bangle-doc-002`, `bangle-deploy-001`, `bangle-deploy-002` | 4 |
| Sprint 5 — account state | — | 0 |
| Sprint 5 — offline/mobile | — | 0 |
| **Total** | **All open task objects** | **20** |

The current working tree contains partial formatting, research capture, chat,
responsive, and surface-consolidation work. Those changes remain checkpoint
evidence only: no backlog status is advanced merely because related code exists.

## Sprint operating rules

1. Every sprint starts from an evidence-backed baseline and names the exact
   repositories in scope.
2. No sprint expands ownership boundaries as an implementation convenience.
3. New vendor code requires immutable provenance, license review, adapter
   isolation, a fallback, and deterministic removal.
4. Browser acceptance tests use visible labels and supported interactions, not
   implementation selectors where an accessible role exists.
5. A sprint closes only after runtime proof, command proof, test proof, evidence
   proof, and a clean diff review.
