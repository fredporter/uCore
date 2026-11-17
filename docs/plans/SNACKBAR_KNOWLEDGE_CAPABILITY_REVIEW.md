# Snackbar capability review for the knowledge sprint

This review traces the current source from visible controls through API
handlers and services. It includes focused test evidence. Live provider
sync, Ollama generation and production operations require live qualification.

| Surface | Current capability | Role in the knowledge sprint |
| --- | --- | --- |
| Dashboard | Shows scoped app connection status and runs manual sync through the existing connection engine. Links to Apps and Workflow. | Useful for collecting material from configured accounts. Its scheduling copy overstates the controls available here. It also repeats the Manage apps link. |
| Feeds | Reuses the Workflow activity feed. Lists activity and configured connections, supports source sync and rules, and promotes an activity into a Markdown Tasker task. The current promotion UI uses Sandbox. | An inbox for source leads and follow-up tasks. Binder evidence requires a separate intake action. Saved RSS, Atom and JSON Feed imports use Workflow's import endpoint and require the uCore-Publish codec. Public edition feeds use the publisher. |
| Snacks and Available skills | Lists system Snacks and backend skills from the executable registry. Runs actions and displays their returned results. Skills can expose source for inspection. | Supports maintenance and lookup. The generic Run control sends an empty payload, so it cannot select a research batch, evidence manifest or edition root. |
| Routines | Displays the pending Snack event queue with a manual refresh. Its embedded heading is Feeds. | Currently an event monitor. The separate maintenance scheduler already defines Vault Sync, docs mirror sync and other recurring jobs. This tab provides no schedule controls or combined run history. |
| Assistant | Discovers installed local Ollama models and passes explicitly supplied material through roles using one model. Offers a Markdown download and an explicit model pull. | Useful for drafting and a second pass on curated material. Source retrieval, citation verification, reuse review, and evidence validation remain separate steps. |
| Logs and Server | A direct Snackbar logs route and separate Server views expose operational logs and service health. | Useful for diagnosing service failures. An edition verification receipt belongs with the Workflow run and package manifest. |

## Capability and authority

The [active Snackbar surface](../../frontend-vue/src/surfaces/snackbar/SnackbarSurface.vue)
mounts five visible tabs. Legacy panels in the directory are insufficient
evidence of a visible capability. The [activity feed](../../frontend-vue/src/surfaces/workflow/panels/FeedsPanel.vue)
and [Routines view](../../frontend-vue/src/surfaces/snackbar/panels/SnackbarFeedsPanel.vue)
read different stores. Workflow Queue remains the user-facing place to
follow research jobs and workflow runs.

Existing knowledge skills cover Vault discovery and lookup, library index
refresh, and docs mirror sync. The external
[knowledge curation skill](../maintainer/knowledge-curation/SKILL.md)
and evidence audit live in the maintainer workflow. The registered skill
catalogue and unified executable list do not expose that workflow or
the publisher's edition compiler. Keep Wizard approval and edition
building in the maintainer path.

The executable endpoint checks confirmation when declared and the skill
runner validates parameters and enforces a timeout. The confirmation
header records a caller assertion. The registry's developer-lane check
depends on execution context, which this endpoint does not derive from
the caller. The runner reads catalogue roots but the generic path check
only rejects traversal strings. Treat catalogue roots as metadata here.
Any knowledge operation exposed through this surface needs its own
server-side scope checks and an authenticated Workflow dispatch. See
[executable endpoint](../../backend/app/api/executables_api.py) and
[skill registry](../../backend/app/skills/registry.py).

## Fit with the completion gate

- **Core scope and edition packaging, K1–K2.** The maintainer skill and
  publisher own review, digest checks and artifact creation. Snackbar
  can surface a read-only receipt if an existing Workflow run provides it.
- **User Vault seed and shared intake, K3–K4.** Workflow owns the
  Sandbox seed, file import and Binder review. Feeds can supply a lead.
  A source-to-Binder handoff is the missing connection. Preserve provider
  identity and citation and qualify replay through the existing intake
  contract before exposing it as a runtime action.
- **Browser and release qualification, K5.** Use Workflow and the
  documentation reader to verify the same packaged edition and seeded
  vault. Snackbar can show connection or model readiness during that
  run. Production approval and rollback evidence belong to the release.

For the sprint, prioritise accurate Routines status and the Feeds handoff
over adding a second execution surface. For a first runtime knowledge
action, use a scoped preview such as validating a Binder intake batch.
Use the existing Workflow run and Queue for execution history. Keep the
external canon reviewer and publisher as the release entry points.

Verification covered 26 focused tests across executable confirmation,
local assistant, maintenance scheduling, feed rules, Markdown intake
and Snack orchestration. These establish the exercised contracts with
fixtures. Live provider, model and browser qualification remain open.

## Integration update

The shared Feeds panel now sends a stored activity to a selected User
Vault Binder. The endpoint resolves the active profile's activity and
uses the same Markdown import path as saved feeds. The document carries
the source, entry ID, URL, timestamp and revision digest. Repeated
captures of the same revision reuse the existing document. Capturing
an item leaves it available in Feeds for other actions.

The Routines tab now reads the maintenance scheduler and displays
its configured times, last outcomes and retry status. Workflow Queue
shows research jobs and workflow runs. Schedule changes remain owned by
the existing scheduler configuration.

## Base workflow readiness review

| Area | Available through existing owners | Gap before expanding |
| --- | --- | --- |
| Local Snacks | Markdown formatting and validation; Apple reminders, mail and contact badges, Notes and Calendar launchers; Apple Intelligence shortcuts | Apple commands require native permissions. The generic executable dispatcher now forwards text to the same handler as the dedicated Snack endpoint. Contact VIP badge heuristics are distinct from Workflow contact metadata. |
| External and cloud adapters | Apple and Google connections, local Ollama, feed intake, separate WordPress post transport | Keep provider operations behind Connections and publication behind Binder review, uFlow and uCore-Publish. Qualify disposable Google and Apple lists, Linux availability, and an approved disposable WordPress target. |
| Internal Skills | Vault lookup/indexing, backup, sync, clipboard maintenance, workflow guard/audit/pause and spool retention | Snackbar's merged registry presents all entries as enabled. Its generic endpoint supplies a confirmation assertion without passing caller scope to the skill runner. Catalogue roots are descriptive at this boundary. Review the exposed set and enforce caller scope and allowed roots before adding user actions or adapters. |
| Daily operations | Workflow Queue, maintenance scheduler and connection polling | Scheduled backup, Vault sync, Tasker sync, brain sync and clipboard maintenance all require execution authorization at the registry. Automatic jobs omit it and can show Needs approval. Decide and persist scoped opt-in for scheduled effects; exercise missed runs, retries and receipts under one scheduler. |
| Vault storage | Binder documents, intake and user planning files | Activity, dispatches and feeds still have Vault writers. Classify user-facing records versus machine state and migrate the latter through their owners to UDOS_HOME before removing the old folders. Review legacy Binder placement on case-insensitive and case-sensitive volumes. |

The two sprint slices start with source-list identity in synced account task
views and explicit DocLang canonical and spatial refs. Remaining work includes
editable task metadata, Contacts/Binder links, scoped wiki resolution, the
submission review state machine and deployed cloud resolution. Use the
existing owners for each step. The starter Vault plate is an inventory;
rendering it produces YAML, while Workflow seed creates the Sandbox files.

For the existing Vault, start with a read-only inventory and a migration
preview that records source and destination, owner, references and conflicts:

- Keep `@inbox/`, `daily/` and the current Binder documents in place. Use
  the existing Binder migration preview for the legacy hierarchy and detect
  case-only collisions before renaming anything.
- Move confirmed project files into their Binders or Documents after checking
  links and attachments. Review ambiguous folders such as research, web and
  creative projects with their owners before grouping their content.
- Treat Activity, dispatch and feed records as separately owned. For each,
  distinguish authored exports from queues, indexes and caches. Switch
  machine-state readers and writers together and verify a replay against a
  disposable Vault before moving the live data.
- Review the legacy hidden folders by owner. Keep editor-owned configuration
  with that editor, surface user files in visible folders, and retire legacy
  runtime paths only after verifying their replacements.
