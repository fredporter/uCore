# Apple intake, Tasks and automation gap review

Read-only review on 9 November 2026. No Apple source import, permission grant, outbound sync, email mutation, or personal-data export was performed.

## Finding

The product has adapters and manual endpoints, but not a single continuous, observable Apple-to-workflow pipeline. A supported adapter is currently presented too much like a connected source.

## Evidence

- `/api/feed/runtime` reports six Apple adapters available, four enabled example rules, and `auto_execute: false`. Availability checks macOS plus osascript, not successful authorization or import. There is no per-source last-success/count/error in this response.
- Feed runtime imports the scheduler getter from `snackmachine.scheduler`. uCore startup creates and registers `app.services.maintenance_scheduler.MaintenanceScheduler`. These modules have independent singleton registries. The Feed stopped indication does not describe the active scheduler reliably.
- `/api/system/maintenance` reports the existing overnight jobs. There is no Apple intake job. Stored results for backup, vault_sync, tasker_sync, docs_mirror_sync, brain_sync and clipboard_maintenance are unsuccessful, with no last_success; spool_prune succeeded. Their underlying failure causes need a separate execution/log audit.
- `AppleFeedSync.sync` runs only through explicit source sync or Snackbar activity sync routes. Snackbar activity sync defaults to Calendar and Mail. Its response always sets outer `ok: true` even when individual sources fail.
- Tasks' Sync Reminders button calls a separate `TaskActionBridge` inbound/outbound pair. Inbound defaults to inbox and reads incomplete reminders; outbound defaults to binder uDos. It is not the same operation as Feed source sync and does not follow the selected Tasks list/binder automatically.
- `AppleFeedSync` writes Feed activity, emits consumer/spool records, and projects daily activity Markdown. `FeedConsumer._maybe_trigger_tasks` only logs keyword matches; it does not create tasks. Rule proposals are another explicit layer; enabled rules do not imply automatic execution.
- Contacts adapter reads names, IDs and notes only, skipping contacts without notes. It is not a contacts directory import or address/email/telephone resolver.
- Mail adapter reads unread inbox messages only; this is not mailbox-wide synchronization. Messages exposes chat metadata rather than message bodies. Reminders Feed intake reads incomplete reminders and is distinct from completion reconciliation.
- AutomationPanel displays definitions, stored schedule labels and recent runs. The inspected maintenance scheduler does not dispatch these workflow definitions based on those labels.

## Recommended integration

Use existing owners: uCore owns native source connections and service UI; uFlow owns tasks and workflow execution; Snackbar supplies executable adapters; the existing scheduler owns polling. Do not introduce another daemon or state root.

1. Consolidate scheduler status and source health. Persist enabled scope, authorization state, last attempt/success, imported/updated/unchanged counts and actionable error per source under the existing settings-resolved runtime state. Distinguish supported, permission-needed, connected, stale and failed.
2. Add a user-controlled Apple Connections setup in Settings. Choose apps, Reminders lists, Mail scope and contact fields. A first connection can request macOS permission; background execution should only use previously enabled connections.
3. Register bounded source intake jobs with the existing scheduler: timeouts, per-source locks, incremental cursors, deduplication, retry/backoff, and no blocking native calls on the web event loop.
4. Route all source events through one normalized Feed contract with stable source IDs and provenance. Reconcile reminder edits/completion rather than just importing incomplete items. Reuse this path for the Tasks sync action.
5. Apply explicit user rules to propose or create tasks. Mail/contact/calendar activity should not automatically become tasks without a rule. Show the originating item and execution result in task detail; keep contact information as context.
6. Connect workflow definitions to registered executable IDs and real scheduling. Display last run/next run/errors in the Workflow overview; keep script/engine administration in Advanced. Report partial failures honestly in every sync response.

## First implementation slice

Correct the scheduler getter and status semantics; expose connection health and scope; make one enabled Reminders list reconcile reliably through the shared intake contract; verify repeat-run idempotence, completion propagation and denied-permission handling using mocked adapters and a disposable local list before enabling recurring intake. Follow with Mail and Contacts once their user-selected scopes and retention behavior are defined.
