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
