# UI simplification and background reliability — implementation

Implemented 2026-11-09 in uCore. Companion plan: UI_SIMPLIFICATION_AND_AUTONOMY.md.

## Delivered

- Simplified visible headings, buttons, placeholders, notices and accessibility labels across Dashboard, Workflow, Tasks, Binder, Research, Knowledge, Documentation, Settings, Dispatch, BitChat, Snackbar and recipe views. Repeated sovereignty/ecosystem claims are removed from ordinary flows. Runtime details are collapsed; architecture documentation and stable identifiers remain intact.
- Dashboard descriptions name user activities. Unsupported guarantees such as zero latency and set-and-forget were removed from the inspected surfaces.
- Added a reproducible Vue-template action inventory covering all frontend source components, including shared controls, recipes and layouts. `npm run audit:actions` in frontend-vue inventories 810 controls/event bindings, checks simple handler references against Vue compiler bindings, and exits unsuccessfully on unbound controls or unresolved handlers. Current result: zero unbound enabled actions and zero unresolved simple handler references.
- Fixed two inert controls: routine details and recipe card navigation. Unconfigured recipe actions are disabled and labelled Preview only. Removed fictional routine starters from the live automation panel.
- Task editor Save now PATCHes task content, reports transport errors, blocks duplicate submissions and reports success after persistence. Blank bodies can be saved. The backend resolves metadata task IDs as well as filenames after status/title changes; it rejects ambiguous IDs and invalid destinations. Task writes use replacement rather than truncating the live file.
- New virtual drafts use a Save As form and the existing bounded workspace API. Existing file saves retain conflict handling and distinguish queued offline writes from completed saves.
- Empty task responses and offline workspace fallbacks no longer generate sample tasks/files. Genuine cached workspace content is identified as offline.
- Binder compilation validates create/intake/assembly results and does not announce successful compilation after a failed assembly.
- Executable UI actions respect confirmation metadata, prevent duplicate submissions and display unsuccessful API results as errors. The API forwards explicit confirmation to the existing skill authorization contract and returns useful failure HTTP statuses. Required parameter validation errors are shown rather than discarded.
- Research Open note opens the existing output rather than enqueueing duplicate work. Request Research honors its binder input. Progress refreshes with one non-overlapping loop and stops on unmount. Cancel and Retry are wired through registered API routes. Missing local-model summaries are disclosed as source-only output.
- Removed Research All: it merely overwrote a search field repeatedly. Per-topic Search now actually starts the search. Knowledge gaps are restricted to configured binder folders rather than flagging every folder, including runtime folders, as deficient knowledge.

## Background lifecycle

The existing uCore service owns one research worker through its startup/cleanup lifecycle. It resumes queued/interrupted jobs without an open browser. SQLite receives additive attempts/retry_at columns; existing jobs and output files remain intact.

Limits: one research execution lane shared by manual and background processing; 100 active queued jobs; three automatic attempts for transient source/network failures; 30/60-second exponential delays plus jitter; 15-second source fetch, 120-second local-model and 180-second overall execution timeouts. Permission errors and permanent source failures are not blindly retried. Manual Retry reuses job identity and explicitly resets its attempt budget.

Research claims use a conditional SQLite update. Results use job-specific filenames, preserve existing notes on recovery and avoid duplicate citations. Filesystem output runs outside the event loop. Cancel interrupts scraping/inference while keeping the worker alive; cancellation is unavailable once saving has begun.

Maintenance has a shared execution lock, per-job timeout, persistent attempt counts, atomic state replacement, last-success reporting and failure isolation. Only explicitly retry-safe jobs receive automatic retries. Docs mirroring is marked retry-safe. Approval-required operations report needs_approval instead of receiving automatic authorization. Existing historical failures remain historical; they are not silently replayed.

Docs mirroring and vault indexing use shared in-flight thread tasks so filesystem scans do not block the event loop or start duplicate scans when a caller times out.

Health polling cannot overlap, pauses network requests for hidden/offline tabs, backs off on errors and removes listeners/timers on stop. Research progress uses 5 seconds while jobs are active and 30 seconds while idle; UI polling does not execute jobs.

Ownership and rollback: no new service, container or agent tree. Research state remains in settings-resolved UDOS_HOME/indices/research_queue.db; maintenance uses its existing state path; user outputs remain in Vault. Remove the research cleanup context to disable the worker; retain the SQLite file and user documents. Additive columns can remain during source rollback. Shared in-flight tasks end with their owning process. No canonical global-knowledge content was changed.

## Evidence

- Backend regression selection: 42 passed, including task save/clear/reload, research restart recovery without a client, serialization, bounded retry, cancellation, replay-safe file/citation output, non-blocking single-flight scans, gap filtering, maintenance failure/timeout isolation, approval boundaries and existing workflow/tasker contracts.
- Frontend regression selection: 7 passed, including editor Save success/failure, empty task responses, task PATCH behavior and non-overlapping/hidden-tab health polling.
- Frontend production build and type check passed. Build reports large editor/diagram chunks; this change does not attempt a bundling redesign.
- Ruff passes for the new/modified background and executable modules and tests.
- Action inventory: 810 entries; no missing action bindings or unresolved simple handlers. The TSV explicitly labels static-only outcomes as unexercised; binding existence is not a claim of successful external effects.
- Live verification: backend restarted; workflow.run ready; research worker running with concurrency 1 and queue limit 100; maintenance status responds. Dashboard, Workflow, Automation and Research views inspected. Navigation, Source inspection, scheduled-status disclosure and concise headings verified in the live browser.
- Default Git-based home-path checker is blocked by the host's unaccepted Xcode licence. The checker's supported --diff-stdin mode passes when conservatively supplied all lines of the touched path-owning modules. No commit was attempted.

## Verification limits

External publishing, messaging, credential-dependent integrations, destructive controls and approval-required maintenance were not executed against user data for QA. Their controls remain subject to their existing authorization/capability checks. The inventory is not a certification that every external integration is configured or that every possible conditional UI state was exercised.

No before/after CPU/RAM load baseline was available. Resource guarantees here are enforced concurrency/queue/time limits and tested event-loop responsiveness, not an unmeasured performance claim. Restart recovery is tested with isolated persisted state; existing user jobs were not fabricated or rerun merely to test it.
