# Universal live feeds, lists, spells and hexes

Delivery plan, 19 November 2026. The first release follows one live RSS
subscription from capture to a local task, with a readable history and a BBC
BASIC command surface. It extends the existing
[universal intake plan](UNIVERSAL_KNOWLEDGE_INTAKE_AND_FEEDS.md) and
[OK Assistant plan](OK_ASSISTANCE_AND_LOCAL_RUNS.md).

## Roles and execution

| Term | Runtime contract |
| --- | --- |
| Spell | A named, typed operation invoked on demand by a person or BASIC program. Local spells include listing available feeds and drafting a summary. Online spells require a provider capability. |
| Hex | An autonomous spell run from Crypt or Drone under an explicit uFlow schedule or event trigger. The grant binds a recipe revision, trigger, owner, inputs, operations, destinations and a run budget. |
| Sorcerer or Wizard | May invoke authorised online spells directly using their own connection. May enrol a Crypt or Drone where their existing permissions permit. Wizard administers grants and canonical releases. |
| Knight or another authorised profile | Can run local spells and opt into delegated spells or hexes within a Crypt or Drone grant. The gateway keeps provider credentials and verifies each call. |
| Crypt | An encrypted capsule. An enrolled container can load approved recipes and process selected local data. Online operations from Crypt route through Drone. |
| Drone | An enrolled, containerised gateway that can execute scoped online spells and hexes. The existing local Google Tasks preview provides the first grant contract to extend. |
| Tomb | A read-only edition that can plug into Crypt or Drone as a verified input. Mount the selected edition read-only by revision and digest. A subscribed hex may read its data using an independently approved recipe. |

Keep the stored role ID aligned with the existing Sorcerer role. Human roles,
device identities and the authority to run a specific hex are separate.
Bind identity on the server and recheck scope, expiry and revocation just
before each external action. A schedule or event uses the enrolled principal
even if another profile is active on the desktop. A human's online role and
the model's ability to suggest an action grant no additional authority to a hex.

## One local pipeline

1. **Capture.** Register a source under a profile and a connection or grant.
   Start with RSS fixtures and a live public RSS source, then add Atom, JSON
   Feed and selected Google Tasks lists. Reuse the Apple and Google connection
   adapters. uFlow owns polling, backoff, cancellation and source checkpoints.
   A source reports its last successful refresh, next attempt and stale state.
2. **Normalise.** Reuse the Feed Store for activity and the existing knowledge
   intake path for selected material. Carry source, subscription, item ID,
   revision digest, observed time, original time, visibility and origin
   reference. Keep task-list provider IDs with their connection and remote
   list ID. Update revisions on upstream edits. A feed's rolling window leaves
   older items intact. A task provider's deletion requires explicit deletion
   evidence or a completed authoritative reconciliation.
3. **Process.** Run deterministic parsing and feed rules first. Persist an
   item before advancing its checkpoint and deduplicate retries by source
   identity and revision. Route matching items to a review queue. Optional
   Ollama summaries cite intake IDs and remain inspectable drafts. Queue
   downstream work durably so a restart can resume after ingest.
4. **Promote.** Use the existing feed-to-task bridge and uFlow task store to
   create a Markdown-backed task from a reviewed proposal. Record the
   relation to the original feed revision. Make promotion retry-safe even
   when two runs race. A changed feed item updates evidence and preserves
   user-edited task fields. Commit the local task before any separately
   authorised provider write.
5. **Project.** Use the existing Feeds and workflow surfaces to show incoming
   items, source freshness, proposals and uFlow tasks. Expose provider lists
   as read-only snapshots in the first release. Explicitly importing a remote
   task creates or updates a linked local record. Task write-back is a later
   opt-in with field ownership, provider revisions, a durable outbox and
   visible conflict handling.

A universal list is a common view over tasks, an inbox or a provider snapshot.
Each row retains its record type, owner, stable identity and provenance.
Feed read state, task completion state and provider sync state are independent.
Use a cursor and a bounded export for views consumed from BASIC or offline.

## Open-box execution

Use a Markdown recipe with validated frontmatter, a human-readable prompt and
a declared output schema. The recipe identifies the approved local model,
input selectors, named operations and trigger. uFlow stores the approved
revision and validates the submission against its registered spell catalogue.
Record the recipe revision, input IDs and digests, model identifier,
structured result, policy decisions and action receipts. Show the resolved
prompt and output to the owner within the same data permissions. Apply the
existing redaction and retention policies to run records.

External feed text and Tomb files are data passed into the prompt. Run Ollama
through the existing loopback service with no tool execution. Validate its
structured output and allow it to propose actions using known item IDs.
uFlow handles accepted actions. A hex may automatically persist a summary
or proposal under its grant. Publishing, sending messages and changing
external task lists require separate authority and are outside the pilot.

### Proposed BBC BASIC interface

```basic
10 REM uDOS host commands for BBC BASIC
20 OSCLI "FEED LIST"
30 OSCLI "FEED SHOW entry-42"
40 OSCLI "SPELL RUN triage entry-42"
50 OSCLI "TASK LIST inbox"
60 OSCLI "HEX STATUS daily-inbox"
```

Qualify these proposed commands against the embedded runtime's OSCLI support.
If it lacks a host hook, expose the same grammar through the existing uCode
Local input route first. The uDOS host dispatcher accepts registered verbs
and validated IDs, derives the profile from the session, and calls the
same uCore/uFlow services as the UI. Return a display result and stable run
or item ID. Keep the shell and provider credentials outside that interface.
The Markdown recipe may display these commands as examples. Only a user
invocation or enrolled uFlow trigger starts a run.

## Delivery and proof

| Slice | Implement in | Evidence required |
| --- | --- | --- |
| 1. Local feed to list | uCore Feed Store/API, Feed Rules and uFlow task bridge | Import a saved RSS fixture, handle an edited revision and a replay, promote to one visible Markdown task, then reopen both source and task offline. Two profiles cannot read each other's records. |
| 2. Open-box spelling | uCore OK Assistant, uFlow catalogue and uCode terminal adapter | A local Markdown recipe produces a source-linked proposal via UI and terminal. A feed entry containing apparent instructions cannot execute a command. Invalid verbs, profile IDs and model output return explicit errors. |
| 3. Live direct and delegated | uCore connections, existing Drone grants and uFlow polling | Sorcerer uses a real opted-in RSS connection. Knight receives the same feed through a scoped Drone. Expired grants, redirected destinations outside scope and exceeded budgets fail cleanly. Qualify Google Tasks against a real authorised account separately. |
| 4. Autonomous and portable | uFlow durable runs, Sonic capsule lifecycle and existing Crypt/Drone profiles | A scheduled Crypt hex reads a mounted Tomb and optionally refreshes via Drone. Restart after fetch before task promotion and demonstrate one logical result. Disable the hex, revoke the grant, unmount the Tomb, and verify each effect independently. |

## Universal seed variables and spatial data

Load this read-only baseline before qualifying live providers. The pilot seed
manifest references installed canonical files by relative path, version and
digest. A run receipt records those references and the resolved settings.
The values below illustrate the existing canon and should be read from it at
runtime. Wizard-approved releases update the baseline. Shared and Vault can
supply namespaced defaults or annotations without shadowing canonical
geometry, units or conversion rules. Resolve editable defaults in Vault →
Shared → baseline order. Read the current time and zone from the host.

| Variable set | Source and examples | Use |
| --- | --- | --- |
| GridCore geometry and mapping | `standards/GRIDCORE-STANDARDS.json`. A dot is 4×4 px, square cells are 8×8 px, tall cells are 12×20 px and the shared pitch is 24×40 px. Use its mapping hierarchy, layer definitions and character catalogue. | Convert cell positions to dots or pixels consistently. Record the register and frame with each placement. |
| Spatial coordinates and operations | Existing GridCore coordinate codec and `SpatialAlgebra`. UCode address, zoom level, layer, eight directions, geographic conversion, distance in metres and bounding box. | Normalise input coordinates with the existing codec. Keep grid, render and geographic frames explicit. |
| World and units | `datasets/world_parameters.json`. Earth and planetary reference metrics. | Include source field and unit for numerical results. Qualify spatial calculations against the runtime's actual constants before claiming parity with canon. |
| Pilot data and defaults | uCore fixtures. Two fictional mapped feed items, one unmapped item, two lists, one Tomb manifest and one Markdown recipe. | Exercise the same inputs offline across UI, BASIC and container runs. Keep polling budgets and display preferences separate from reference values. |

Use a typed spatial record. A geographic point carries latitude and
longitude in degrees and its reference system. A GridCore position carries
its validated UCode address and mapping revision. A render position carries
column, row, register and origin. Retain the source geometry and provenance
when deriving a placement. For example, a synthetic render point at column
3, row 5 on a zero-based square grid lies 24 px right and 40 px down from
the origin. Verify the matching tall-grid placement at column 2, row 2.

The first spatial commands are proposed as `SEED SHOW gridcore`,
`MAP NEIGHBOUR <address> <direction>` and
`MAP DISTANCE <address> <address>`. Bind them to the same dispatcher as
feed and task commands. Qualify valid addressing, invalid coordinates,
east/west and north/south boundary crossing, and metre output using shared
fixtures. Verify antimeridian behaviour before offering geographic bounds
search. The current pathfinding and region clustering methods are stubs,
so defer those commands.

## Index and URL paths

Use one stable reference per resource, represented as resource type plus
opaque ID. Adapt existing IDs through the owning store. Where IDs are only
unique within a profile, source or list, include that scope in the indexed
identity and resolve the public-facing opaque key server-side. Preserve
DocLang UIDs and scope overlays to their owning workspace. Keep title,
slug, spatial address, upstream URL and file path as searchable attributes.
Moving a file, retitling an item or updating its map position preserves its ID.

These are proposed uCore view paths under the existing application shell.
Resolve them through the existing Feed, uFlow and library services.

| Resource | View path |
| --- | --- |
| Subscription | `/feeds/{feed-id}` |
| Feed item | `/feeds/{feed-id}/items/{item-id}` |
| Task list, including provider snapshot | `/lists/{list-id}` |
| Task | `/tasks/{task-id}` |
| Spell and hex | `/spells/{spell-id}`, `/hexes/{hex-id}` |
| Run receipt | `/runs/{run-id}` |
| Seed set and revision | `/seeds/{set-id}`, `/seeds/{set-id}/revisions/{revision}` |
| Mapped resources | `/map?address={encoded-ucode-address}` |
| Tomb edition | `/tombs/{tomb-id}/revisions/{revision}` |

Add a resource index as a rebuildable projection, using the existing library
index for Markdown and querying the owning stores for feed, task and run
records. Start with typed ID, owner/scope, revision, title, tags, source
reference, optional spatial key and update time. Support bounded cursor
pagination and enforce visibility before matching, counting or resolving
links. Updates and deletions must reach the projection through the owning
store. Rebuild from those stores and the selected seed manifests after
interruption. Use explicit revision links for evidence and the plain resource
link for the current authorised view.

Keep provider URLs as provenance and use the edition manifest for public
uCore-Publish links. Local resource paths use the configured app base,
including on subpath installs. A Tomb manifest carries the resource IDs and
relative edition links, so the offline reader can resolve bundled records
without a running uCore server. BASIC returns typed IDs and local view paths
from the same resolver. Reuse existing API routes behind these views. Scope
checks happen on every lookup, including link and map results.

## Pilot runbook

### Live provider runs

| Run | Setup and execution | Pass evidence |
| --- | --- | --- |
| Public RSS, direct | Enrol one user-approved public HTTPS feed for a Sorcerer. Run a manual refresh, repeat it, then run via the scheduled path. Save ETag and Last-Modified when supplied and use conditional refresh. Set a 15-minute pilot interval, 15-second request deadline and 2 MiB response limit. | First refresh records provenance. Retry or unchanged response creates no duplicates. A changed fixture item creates a revision. An outage marks the source stale and leaves its last good items readable. |
| Public RSS, delegated | Enrol a Knight grant for the same subscription and call the named refresh operation through Drone. Use a separately scoped inbox for the Knight. Retry after revocation. | Drone returns a bounded result with grant and source provenance. Revocation records a denial before any new provider request. |
| Google Tasks, read-only pilot | Use a Wizard-owned test connection and one disposable list. Begin with the existing read-only Drone preview. Add, edit and complete a test task in Google, then refresh manually and check the local snapshot. Qualify pagination and interrupted reconciliation with fixtures before enabling scheduled reads. | Stable remote IDs map correctly, completion is reflected, and an interrupted refresh preserves the previous snapshot. Expired or disconnected grants fail. No pilot operation writes to Google. |

The current Google Tasks connection requests the broader Tasks scope. Treat
that as a qualification gap. Add a read-only enrolment path and require fresh
read-only consent for this pilot. Keep existing integrations on their current
configuration. Use one in-flight refresh per subscription, bounded retries
with provider backoff, and persist a checkpoint only after durable ingest.
Check redirects against the enrolled destination policy and block local/private
network targets for public RSS. Use saved fixtures for error cases, including
oversized, malformed and interrupted responses. Capture a run ID, source ID,
status, counts and next retry time in the receipt.

### Container deployment

1. **Host baseline.** Keep uCore, uFlow and Ollama native on Apple Silicon.
   Use an existing supported container engine and start with one Crypt and one
   Drone on a single host. Build the pilot image for the host architecture.
   Qualify Linux deployment separately with the same operation contract.
2. **Crypt.** Run a non-root worker with no direct internet route and a
   narrowly scoped connection to the uFlow broker. Mount the verified Tomb
   read-only. Give the worker a bounded temporary workspace. Limit access to
   the selected capsule payload. Use the existing Sonic capsule tooling as
   the package and integrity starting point. Qualify the encrypted Crypt
   format and key recovery separately from the worker image.
3. **Drone.** Run a non-root gateway with provider-only egress and no public
   listener. Use authenticated broker calls with an enrolled device identity.
   Keep Google refresh credentials in the existing uCore secret store and
   define the broker handoff before enabling Google in the container pilot.
   First qualify public RSS, which requires no credential handoff.
4. **Operations.** Use read-only container roots, no host socket, scoped
   mounts and CPU/memory limits. Start with one job per worker. Pin the
   deployed image digest, expose health in uCore and retain run receipts in
   existing uFlow storage. A worker must recover a claimed run after restart
   without reapplying a completed promotion.
5. **Rollback.** Pause the hex in uFlow, revoke its device grant, stop the
   workers and unmount the Tomb. Verify cached feeds and Markdown tasks
   remain readable. Keep the prior image digest for redeployment and record
   any required state migration before swapping versions.

### BBC BASIC command binding

| Command | Handler result |
| --- | --- |
| `FEED LIST` | Bounded list of the active profile's subscriptions and freshness. |
| `FEED SHOW <item-id>` | Selected item, source and revision. |
| `TASK LIST <list-id>` | Bounded local task view or authorised provider snapshot. |
| `SPELL RUN <spell-id> <item-id>` | Same validated submission as the UI, returning a run ID for an approved spell. |
| `HEX STATUS <hex-id>` | Last run state, next scheduled time and receipt ID. |

Implement the parser once at the uCore/uFlow boundary. Use the existing
uCode Local input route to establish end-to-end parity with the UI. The
BBC BASIC guide documents OSCLI, but the embedded host callback still needs
qualification. If available, bind the commands there to the same dispatcher.
If unavailable, use Local input for the pilot and add a runtime host callback
before claiming BBC BASIC support. Pass the session's identity separately
from command text. Accept only the documented grammar and return defined
errors for invalid input, unavailable services and permission denials.

Run the same fixtures through the UI, Local input and BBC BASIC. Verify
stable IDs, equivalent authorisation, a bounded display result, and clear
errors for unknown verbs, foreign-profile IDs and attempts to pass shell
syntax. Keep hex scheduling in uFlow so exiting BASIC has no effect on a run.

### Release gates

1. Offline seed manifest, spatial fixtures and index/path round trip. Verify
   rename stability, profile isolation, index rebuild and offline Tomb links.
2. Local fixture intake, promotion and command parity.
3. Live direct RSS with a saved receipt from an opted-in source.
4. Containerised delegated RSS and verified read-only Tomb mount, including
   restart and revocation checks.
5. Live Google Tasks read-only enrolment and preview after consent and the
   credential handoff are qualified.
6. Scheduled Crypt hex with one complete run, one induced interruption and
   one disable-and-revoke drill.

## Ownership and lifecycle

Reuse the existing settings-resolved Activity, connection and uFlow stores
under UDOS_HOME. Keep Markdown tasks in the existing task directory and
user-authored recipe documents in the selected writable Vault or Shared
workspace. Leave the canonical Public baseline under Wizard release control.
uCore hosts surfaces and connections, uFlow owns schedules and execution,
uCode owns the command transport, and Sonic owns capsule packaging and
removal. Implement a single worker through uFlow once the existing run path
has durable profile ownership. Use the host clock and preserve source
timestamps and schedule time zones in records.

Start with one authorised source and one read-only Drone grant. Cap response
bytes, poll frequency, queue depth, run duration and model output. Use the
existing local model and runtime where available. Before deploying containers,
record the owner, runtime requirements and resource budget. Removing the
pilot means disabling schedules, revoking grants, disconnecting providers
and removing the enrolled containers through their owner. Keep user-authored
Markdown and exported run receipts available through the existing workspace.
