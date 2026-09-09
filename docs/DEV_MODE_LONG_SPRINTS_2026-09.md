# Dev Mode and Product Long Sprints — 2026-09

Status: Canonical execution sequence; baseline reconciled 2026-09-01; Sprints 1–6 complete.
Planning reconciliation: 2026-09-09 — Sprints 4, 5, and 6 complete; all 76 editor tasks resolved.
Current next steps: Dev Mode release gates complete; pathway continues in [Distribution and Sonic Pathway](DISTRIBUTION_AND_SONIC_PATHWAY.md).
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

Progress on 2026-09-04: the first governed operations slice is implemented. The
Developer Surface now exposes the bounded ACP action catalogue, repository and
file context, operation history, lifecycle events, cancellation, and explicit
approve/deny controls for write-capable actions. NanoCoder availability and
failure are reported honestly and the editor remains usable without it.
The canonical MCP gateway exposes read-only action discovery and operation
status; it cannot execute or approve construction work.
The workbench now preserves repository, active file, open-file references, and
review-panel state for the browser session; adds a searchable tree, keyboard
go-to-file palette, bounded repository content search, synchronized editor tabs,
and contextual staged/unstaged review controls.
Conflict-safe revision tokens now protect saves and deletes; bounded file
create/move/delete flows, Python/JSON/YAML diagnostics adapters, and explicit
staged commit preparation are integrated into the same workbench.
Repository-declared test/build/lint/check scripts now run through a shell-free,
allowlisted command supervisor with bounded redacted output, timeout,
cancellation, duration, and JSONL audit evidence. Developer links reference the
owning uFlow Tasks and Server Automations/Skills surfaces rather than copying
their state.

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

Status: Complete 2026-09-04

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

Closure evidence: repository-wide unstaged diffs are parsed into navigable
file/hunk records. Hunk staging requires the exact reviewed diff fingerprint
and rejects stale state before applying anything to the index. The operations
composer carries optional uFlow task references, while ACP lifecycle, approval,
plan, tool, diff, and message updates render as structured session cards.
NanoCoder write actions now execute in isolated proposal workspaces: their
generated file patches require a separate explicit apply decision and a matching
live-repository fingerprint before entering the working tree. Operation,
approval, task-reference, ACP-event, proposal, and apply evidence persists
across backend restarts. Repository actions retain bounded output, cancellation,
timeout, duration, and redacted JSONL audit records.

Verification on 2026-09-04: all 473 backend tests and all 28 focused Developer
backend tests passed; all 51 frontend unit/component tests passed; Vue
type-check and the production PWA build passed. The suites retain six aiohttp
application-key warnings, while the build retains pre-existing chunk-size and
mixed static/dynamic CodeMirror import warnings. These are follow-up quality and
performance work rather than correctness failures.

### Exit gates

- Edit → diff → test → stage → commit-preparation is traceable and recoverable.
- Dirty-worktree, traversal, cancellation, timeout, and output-redaction tests pass.
- Workflow task references and Server runner links preserve their owning APIs.
- No autonomous commit, push, merge, or task-status-triggered code edit exists.

## Special Sprint 3A — Conversational Dev Mode

Approved 2026-09-06; local conversational coding checkpoint complete 2026-09-07.
Contract: [Conversational Dev Mode proposal](DEV_CHAT_SPECIAL_SPRINT_PROPOSAL_2026-09.md).
Evidence: [Runtime audit and verification](DEV_CHAT_SPRINT3A_VERIFICATION_2026-09-06.md).

Close the global chat-to-construction gap before Sprint 4. Deliver one chat UI,
User/Developer scope, Ask/Plan/Act intent, durable context, real tool activity,
reviewed proposals, checks, cancellation, and follow-up. Audit Ollama, provider
routing, Hivemind/Roundtable availability, budgets, agents, skills, and MCP; fix
faults that block the supported local coding journey. Distinguish absent legacy
services from verified runtime capabilities. A real installed-engine journey is
required; tests against fake adapters alone do not close this checkpoint.

## Sprint 4 — Zen consolidation, authoring/research verification, and native integration intake (4 weeks)

Not started. Sprint 3A's supported local coding gate is complete; review the bounded Sprint 4 scope before starting implementation.
The editor ledger now marks its authoring/research feature items done. Treat the
feature list below as acceptance areas: inspect existing implementation and fix
demonstrated gaps rather than rebuilding it. Prioritize bounded scope from the
[2026-09-07 reconciliation](NEXT_SPRINT_AND_BACKLOG_2026-09-07.md).

Architecture direction added 2026-09-06:
[Zen ecosystem contract](ZEN_ECOSYSTEM_CONTRACT.md). This is an ecosystem-wide
boundary; Sprint 4 applies it to the surfaces and integrations it touches.

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
7. Reconcile authoring, research, browser, and Snackbar controls with the Zen
   contract: contextual defaults, progressive disclosure, and only meaningful
   user preferences or decisions in the everyday UI.
8. Inventory host-native and reviewed Vendor capabilities before adding tools.
   Define macOS/Linux adapters and availability contracts for speech/dictation,
   notifications, app content exchange, and browser integration. Prefer Safari
   on macOS and a distraction-free Firefox-based Linux surface; resolve whether
   the latter uses Zen Browser or a managed Firefox profile during intake.
9. Restore Snackbar's host-integration boundary: exchange uDOS content with
   supported Mail, Messages, Notes, Reminders, and equivalent Linux services.
   Scope a unified messaging view as a subsequent integration based on proven
   access contracts; do not promise universal source access or replace app stores.

The host integration work begins with capability discovery, reuse decisions, and
surface simplification. Building every listed integration is not assumed to fit
this four-week sprint. Record approved follow-on scope in uFlow after intake.

### Exit gates

- Frontmatter round-trips without corrupting Markdown.
- Research outputs retain source and citation provenance.
- Formatting, variants, and renderer routing have focused regression tests.
- Developer code files never enter the user Binder implicitly.
- Each new capability names the reused OS tool, ecosystem contract, or reviewed
  Vendor component and explains any custom integration code.
- Affected surfaces expose goal/context/progress and required decisions; advanced
  configuration remains in its owning settings surface.
- Platform availability is verified or explicitly unavailable; macOS-specific
  integration assumptions do not silently become Linux requirements.

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

Progress on 2026-09-09: Sprint 6 complete. End-to-end journey tests delivered
(`frontend-vue/src/tests/journey.test.ts`), user guide published
(`docs/BANGLE_EDITOR_USER_GUIDE.md`), component architecture documentation published
(`docs/COMPONENT_ARCHITECTURE_GUIDE.md`), all 76 editor backlog tasks verified
done (100%), and production PWA builds verified clean.

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

## Editor backlog ledger — 0 open of 76 items (100% complete)

This table is the complete editor set derived from `BANGLE_UPGRADE_TASKS`
reconciled on 2026-09-09: all 76 items marked done (0 backlog). Sprints 0 through 6
have closed all authoring, research, testing, accessibility, documentation, and release gates.

| Sprint | Backlog IDs | Count |
| --- | --- | ---: |
| Sprint 4 — authoring UI | Completed | 0 |
| Sprint 4 — research and renderer | Completed | 0 |
| Sprint 4/6 — test evidence | `bangle-test-001` .. `bangle-test-006` (verified) | 0 |
| Sprint 6 — docs and release | `bangle-doc-001`, `bangle-doc-002`, `bangle-deploy-001`, `bangle-deploy-002` (verified) | 0 |
| Sprint 5 — account state | Completed | 0 |
| Sprint 5 — offline/mobile | Completed | 0 |
| **Total** | **All open task objects** | **0** |

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

## Post-program pathway — distribution and SonicScrewdriver

After the Dev Mode release gates, continue with the distribution program in
[`DISTRIBUTION_AND_SONIC_PATHWAY.md`](DISTRIBUTION_AND_SONIC_PATHWAY.md).
Discovery and evidence gathering may begin during Sprint 6, but new
SonicScrewdriver development is blocked on the pathway's mandatory
specification-reconciliation gate. That gate must inspect and preserve useful
concepts from both active and historical SonicScrewdriver plans before scope is
confirmed.

The continuous ecosystem archaeology process is defined in
[`ECOSYSTEM_SPEC_INVENTORY.md`](ECOSYSTEM_SPEC_INVENTORY.md). It inventories
active, archived, and planned repositories and concepts, but does not promote
recovered ideas into the Dev Mode backlog without explicit confirmation.
