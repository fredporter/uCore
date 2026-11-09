# UI simplification and reliable background execution

Status: implementation delivered 2026-11-09; see UI_SIMPLIFICATION_IMPLEMENTATION.md for changes, evidence and verification limits. Initial source audit completed 2026-11-08.
Scope: uCore routes, 50 surface Vue components, their shared controls/stores, API handlers, and background execution dependencies. This is not a certification that every button has been exercised. No destructive, publishing, messaging, or approval action was executed for this audit.

## Outcome

A calm interface that names the user's work directly. Every available action produces a durable result or a clear error. Background work continues without an open browser, recovers from ordinary interruption, and respects existing permissions and budgets.

uCore owns UI, hosting and service lifecycle; uFlow owns workflow/task authority. Reuse existing services, queues, health contracts and USX standards. Do not introduce a separate runtime, agent tree, clock service or scheduler platform.

## 1. Establish the complete action inventory (P0)

Enumerate every registered route and tab from frontend-vue/src/router/index.ts, including conditional panels and shared dialogs. Use Vue template parsing to inventory native buttons, UButton, links, form submissions, keyboard actions, emitted events and dynamic menus. Missing inline click handlers alone are not evidence of a broken control: resolve forms, router links and parent event bindings.

Maintain a review matrix: route/tab, control label, visibility prerequisite, handler, store/API call, registered backend route, required capability, durable effect, busy/error feedback, permission boundary, verification result. Mark each verified, broken, intentionally unavailable, or untested. Hidden and unavailable features must explain their actual prerequisite; no apparently working placeholder buttons.

Prioritize Save, task changes, Re-check, sync, queue/run/retry/cancel, approvals and publishing. Verify read-only and reversible actions live; verify consequential actions with mocked transports or isolated test data. Never use production reset/archive/publish/send actions merely to test wiring.

Acceptance: every reachable action has a matrix entry; no unresolved broken enabled actions. Success is checked against the persisted result after reload, not a toast or HTTP 200 alone.

## 2. Repair behavior before polishing labels (P0)

Initial source findings:

- WorkflowSurface.vue onEditorSave persists shared workspace files, but its alternate branch only calls updateEditorContent and logs "Editor saved". The store changes client state. Trace all entry points and wire task/file persistence or explicitly mark an unsaved draft; show success only after durable write.
- The recent workflow repair exposed an overly broad Git prerequisite. Keep read access and unrelated operations independent of optional tools; retest recovery after service restart and stale client state.
- SnackbarSnacksPanel.vue accepts requires_confirmation in runExe but does not use it in that function. Verify backend enforcement and the rendered control path before enabling execution; retain necessary approval gates.
- Audit sample-data fallbacks in the workflow store. Service failure must not display believable sample tasks as live user records. Use an honest cached/offline state or an empty state.

Acceptance: save survives reload; repeated clicks do not duplicate effects; failure never produces a success message; missing optional capabilities do not block unrelated work; server-side authorization remains authoritative.

## 3. Simplify copy across every surface (P1)

Principles: omit repeated philosophy; use familiar nouns and short verb-led actions; state the outcome once. Put architecture, storage paths and implementation details in Help or expandable diagnostics when they are useful. Keep information that affects an actual choice: destination, sharing, cost, permissions, destructive effects and offline availability.

| Current wording | Proposed wording |
| --- | --- |
| Sovereign Ecosystem Sync | Sync |
| Apple Ecosystem (PIM) | Calendar, reminders and contacts (match actual sources) |
| Sovereign Vault Storage | Files |
| Create Sovereign Task | Create task |
| Autonomous Actions Pending Human Approval | Needs approval |
| Autonomous Gate | Remove redundant badge, or use Needs approval where needed |
| Sovereign Identity & Profiles | Profiles |
| Sovereign Budget & Resource Policy | Resource limits |
| Generate Sovereign Dispatch Token | Create invitation (verify actual result) |
| Active Sovereign Dispatches for this Binder | Invitations |
| Accepted Editions & Sovereign Publication Receipts | Publications |
| Return to Sovereign Home | Home |
| Welcome to the Sovereign Local Wikipedia | Knowledge |

Audit visible text, tooltips, placeholders, notifications, empty/loading/error states and accessibility labels. Cover Dashboard, Workflow/Tasks/Binder/Editor, Research, Knowledge/Docs, Services/Snacks/Budget/Agents, Profiles/Settings, BitChat, Dispatch, Google, Dreamscape, uCode and other registered surfaces. Also inspect global toolbar and shared molecules.

Keep stable API IDs, filenames and internal capability identifiers unchanged. Retain product names where they aid navigation. Avoid unconditional claims such as zero latency, zero cloud spend or set-and-forget unless enforced and observable. Summarize configured policy as state, for example Cloud spending off.

Use canonical USX tokens, UIcon and button styles; remove duplicate navigation within AppShell. Add a lightweight copy review for new visible terminology, rather than banning useful technical words in diagnostics.

Acceptance: one useful heading and at most one necessary introductory sentence per panel; no repeated sovereign/ecosystem/runtime doctrine in ordinary task flows; remaining exceptions reviewed in context.

## 4. Make background work recoverable and bounded (P0/P1)

Confirmed inspection targets:

- research_api.py creates a task per enqueue and tracks it in a process-local set. research_queue.py persists jobs but the inspected path has no worker concurrency limit, startup resumption or lease-based recovery. Inspect router-level model limits before setting the final aggregate limit.
- Research writes synchronous SQLite and file operations inside async methods. Same-title output names can collide and citation updates use read/modify/write. Recovery must avoid duplicate output and preserve existing documents.
- MaintenanceScheduler.run_due awaits jobs serially without a scheduler-level timeout. A returned failure is recorded as today's last run; an exception aborts the remaining cycle. There is no explicit per-job bounded retry policy in this scheduler.
- snackbarOps health polling uses setInterval with async requests. Verify in-flight protection, hidden-tab behavior and shared ownership; guard against overlap rather than assuming interval timing bounds request duration.

Implementation:

1. Map the existing SnackMachine and maintenance ownership/lifecycle before changes. Consolidate duplicate scheduling paths behind existing contracts; keep uFlow authoritative for task state.
2. Adopt an explicit lifecycle through existing job records: queued, running, waiting for retry, completed, failed, cancelled, needs approval. Store attempts, last error, timestamps and next retry where needed.
3. Atomically claim jobs; reclaim interrupted work after restart with bounded attempts. Use idempotency keys and transactional or atomic writes for externally visible effects.
4. Start with one local inference job and a small configurable I/O limit; tune against measured CPU, RAM and latency. Bound queue depth and per-step/overall timeouts. Avoid blocking the host event loop with database/file work.
5. Retry transient failures with backoff and jitter, at most three automatic attempts initially. Do not retry permission, credential, invalid input, or non-idempotent side-effect failures blindly. Isolate one maintenance job's failure so later jobs still run; distinguish last attempt from last success.
6. Register startup/shutdown cleanup, drain or persist active work, close database/network resources and expose worker health. Continue processing with all browser tabs closed.
7. Prefer existing event streams for progress; otherwise use one non-overlapping poller per data source, back off when idle/offline and refresh on focus. UI polling must not drive execution.
8. Surface a compact activity indicator and actionable exceptions. Show progress, last success, next retry and cancellation in details; notify only on completion when useful or when intervention is required.

Ownership/storage: extend existing uCore-owned services and uFlow records. Mutable state stays in settings-resolved UDOS_HOME; user output stays in Vault/Shared as appropriate; base canon remains protected. No new service/container/cache is proposed. Any schema additions require migration, bounded retention, cleanup and rollback documented before implementation. Budget defaults remain local and honor configured cloud allowances. Use host time; no independent timezone daemon.

Self-healing means detecting stale state, retrying safe failures and resuming durable jobs. It does not mean silently accepting licences, inventing credentials, granting permissions, changing budgets or replaying external side effects.

## 5. Verification and release (P1)

- Add focused regressions for durable Save, stale repair recovery, duplicate clicks, server errors and permission-required actions.
- Exercise scheduler failures, hung jobs, restart mid-job, retry exhaustion, duplicate claims and cancellation using a controlled clock and isolated state.
- Test background completion with the UI closed; restart the backend mid-job and verify a single durable result.
- Record idle request rate, peak concurrency, queue wait time, memory/CPU, event-loop responsiveness and recovery time before/after. No overlapping health polls; no unbounded worker growth. Set performance thresholds from the baseline before rollout.
- Review every routed surface visually at desktop and narrow widths. Check accessible names and concise status feedback.
- Run targeted backend/frontend tests, frontend type check and required checks. Run scripts/check_home_path_policy.py before committing path-related changes.
- Restart the owned service using its existing lifecycle, confirm live readiness and complete representative actions after deployment. Record any remaining unverified controls explicitly.

Delivery order: action inventory and critical repairs; background lifecycle fixes; surface-by-surface copy cleanup; complete action matrix and live verification. Each implementation batch should include its evidence and remaining limitations.
