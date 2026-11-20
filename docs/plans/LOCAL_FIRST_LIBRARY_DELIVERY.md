# uDOS local-first library and spatial delivery plan

19 November 2026 · Proposed implementation and agent handoff

This plan ties together [knowledge intake](UNIVERSAL_KNOWLEDGE_INTAKE_AND_FEEDS.md), [live feeds, lists, spells and hexes](UNIVERSAL_LIVE_FEEDS_LISTS_AND_HEXES.md), [OK Assistant](OK_ASSISTANCE_AND_LOCAL_RUNS.md), [workspace governance](WORKSPACES_AND_VAULT_GOVERNANCE_2026-11-10.md) and [edition publishing](EDITION_PUBLISHING_SPRINT_2026-11-11.md).

## First vertical slice

Load a saved RSS item about a fictional place. Find it by topic in the existing library, follow its provenance and attach it to a waypoint. Simulate tapping the place's NFC marker and open the authorised local resource. From the item, review a proposal and promote it through uFlow to one task. Collect selected material in a Binder, compile an offline Tomb and open its links without uCore or internet access. Preview the same edition's online destinations and verify that a mock release returns a receipt. Repeat the tap and feed ingest after restart to verify that retries create one logical task and one accepted receipt per operation ID.

## Vocabulary and ownership

| Concept | Meaning in this plan |
| --- | --- |
| Library | uCore's organised view of documents, feed items, tasks, lists, recipes, spatial records and editions. Owning stores retain the originals. |
| Spool activity | Searchable operational history. Reuse the Spool reader/writer for concise event references and outcomes. uFlow retains authoritative run state. |
| SPOOL archive | Existing recovery artifact from backup/archive lifecycle. Index permitted metadata and a recovery reference. Recovery uses the existing explicit UNFURL workflow. |
| Nug / Nugget | A deliberately preserved or salvaged artifact in uCore's Nugget lifecycle. Index a typed metadata reference, version and provenance. Distinguish these from Feed runtime bundles and executable uCode Nuggets through their existing types and owners. Opening a library result displays metadata. Redeployment or execution goes through its owning workflow. |
| Waypoint | Proposed durable place record with a stable ID and optional canonical geographic or GridCore position. Multiple resources can link to one waypoint. |
| Marker | Proposed presentation or lookup record pointing to a waypoint. Map pins, QR references and simulated NFC tags can refer to the same waypoint. |
| Beacon | Existing opt-in advertised presence or resource descriptor for a Tomb, Crypt or Drone. An advertisement can reference a waypoint or approved edition. Access requires an independent policy check. |
| Binder / Tomb / Crypt / Drone | Binder curates source materials. Tomb distributes a read-only edition. Crypt holds an encrypted capsule. Drone brokers approved online capability. |
| Spell / Hex | A Spell invokes a registered operation. A Hex runs an approved recipe revision under a uFlow schedule or event grant. A simulated tap can open a preview or lodge a proposal. Any later tap-triggered Hex requires its own explicit grant. |

## Index and links

Extend `backend/app/services/library_index.py` and its existing reader. Keep its Markdown/SQLite search and add bounded projections from the owning Feed, uFlow, Nugget, spatial and edition stores. Put stable typed ID, owner/scope, revision, title, tags, source reference and optional waypoint in the common metadata. Browse by collection, topic, type and place. Search within the caller's scope before ranking, counting, suggesting or resolving. Test rename, move, delete, overlay collisions and rebuild from source. Build public or portable link manifests from the selected edition.

| Link | Resolution |
| --- | --- |
| Local resource | Typed ID through the existing service and configured uCore base path. Pin a revision for evidence. |
| Upstream source | Preserve its URL as provenance and show last-known freshness offline. Open it on explicit user action. |
| Portable edition | Resolve relative links in a versioned manifest. Include selected assets and mark external references. |
| Public edition | Resolve approved URLs from the uCore-Publish manifest. Use `udo.guide` for the edition and `udo.place` for its spatial mirror. Review target and visibility before release. |
| Publishing tool | Use the existing Binder compiler and uCore-Publish adapters. Offer local Markdown/Quartz/Jekyll exports and a reviewed WordPress draft after the adapter and role checks are qualified. Track destination, edition revision and delivery status. |

Keep canon and datasets read-only in `~/Public/global-knowledge`. Shared and Vault add scoped annotations and defaults. Resolve eligible overlays Vault → Shared → canon while preserving canonical units, geometry and codec rules. Keep source files visible in their owning locations and mutable index state under the owning settings-resolved UDOS_HOME. Rebuild the index without copying source corpora. Keep AppShell navigation and USX controls consistent with the workspace contract.

## NFC spatial awareness in code

Use deterministic fixture bytes and an in-process transport. The first contract handles a passive marker reference. An observed tap resolves a waypoint and its authorised library links. Store claimed position separately from host-observed position. Set the observation to unknown when the fixture supplies none. A known waypoint reports its registered location. Treat physical proximity as unverified for simulated inputs.

```text
MarkerEnvelope { version, marker_id }
TapObservation { event_id, marker_payload, observed_at, simulated_position? }
TapReceipt { event_id, outcome, waypoint_ref?, authorised_resource_refs? }
```

Decode a bounded, versioned payload. Resolve the marker locally, then check waypoint and resource visibility using the session identity. Give unreadable and unknown targets the same generic response to unauthorised callers. Store an idempotent receipt by profile and event ID. Recheck visibility before returning resources on replay. Expose one fixture path through the existing UI/API boundary. Reuse the existing coordinate codec and test coordinate frames and boundaries before adding nearby search.

For a separate code-only peer handshake fixture, exchange a fresh challenge and a response bound to the protocol version, peer identities, request scope, intended resource and expiry. Verify the response against a pre-enrolled test identity using an existing library, consume the nonce once and ask local policy whether the requested lookup is allowed. Test malformed input, stale and replayed responses, wrong audience and revoked identity. Receipts retain references and outcomes. Hardware drivers, radio ranging, background location, real peer enrolment and production transport belong to later work.

## Delivery order

| Gate | Deliverable and proof |
| --- | --- |
| 0. Agree contracts | Record existing entry points, ownership, typed references, visibility rules and a shared fictional fixture. Freeze the integration fields and mark proposed commands and routes. |
| 1. Offline foundations | Build index/reader projections and the tap simulator in parallel against the fixture. Bring feed intake and explicit task promotion through uFlow. Rebuild offline and test cross-profile isolation. |
| 2. Connect and export | Join tap lookup to the library. Add Binder → Tomb compilation and test relative links, visibility and asset resolution offline. Write task/release and accepted tap references to Spool. |
| 3. Extend online | Qualify one opted-in RSS source, then scoped Drone reads and Google Tasks read-only snapshots. Preview publication, qualify staging separately and record delivery receipts. Try command parity via existing uCode Local input, then bind BBC BASIC OSCLI after verifying its host callback. |
| 4. Enable bounded automation | Enrol a uFlow Hex against an approved Tomb revision and grant. Exercise expiry, revocation, restart and retry. Reuse existing Crypt/Drone lifecycle and optional local Ollama draft processing. Disable the grant and confirm cached records remain readable. |

Use macOS natively on Apple Silicon. The pilot reuses current stores and needs no new service. Keep the index bounded and rebuildable. Document retention and removal for new receipt data and route bindings. Run `python3 scripts/check_home_path_policy.py` in uCore before committing path changes.

## Running the work with agents

Run the coordinator first. Review the contract it produces, then start the implementation lanes in isolated worktrees from the same agreed baseline. Assign one owner per shared file. The current checkout has in-progress index, workflow, assistant and reader edits. Review those changes with the coordinator and provide them as an agreed baseline before overlapping work. A worktree from HEAD alone will omit them. Give every agent the plan path, baseline, owned files, agreed fixture and verification command. Have agents return a branch or patch with test results and integration questions. Let the coordinator merge in gate order and run the full offline scenario.

### Shared prompt prefix

> Read ~/Code/AGENTS.md and uCore/docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md, then inspect the assigned code and relevant linked plan. Work from the baseline and fixture I supply. Stay within your assigned files, reuse the owning stores and preserve existing working changes. Report blockers against the agreed contract before changing a shared interface. Return changed files, tests and results, unresolved issues and rollback notes. Use offline fixtures for acceptance. Leave live accounts and deployments for separately authorised qualification.

### Agent assignments

| Agent | Copy-ready assignment |
| --- | --- |
| Coordinator | Inventory live entry points and in-progress changes. Propose the typed IDs, link resolver, visibility rules, tap fixture and a precise file ownership list. After review, integrate branches and run the first vertical slice end to end. |
| Library and UI | Extend the existing library index and reader to browse and resolve authorised typed records. Own the index and reader files. Exercise file moves, rebuild, profile isolation and configured base paths. Use fixture projections until the producers land. |
| Spatial and NFC | Implement waypoint and marker fixtures, typed coordinate resolution, simulated tap decoding and replay-safe receipts. Add the pure peer handshake fixture after tap lookup works. Own the spatial adapter and tests. Consume the agreed resolver interface. |
| Feed and uFlow | Follow one saved RSS revision through intake, reviewed proposal, task promotion and Spool evidence. Own the Feed/uFlow changes and the task projection adapter. Demonstrate restart and repeated promotion with a single task. |
| Publishing | Start in uCore-Publish. Reuse clean edition compiler and mirror contracts to export a fixture Binder as a Tomb and preview its destinations. Verify relative links, scope and mock delivery receipts. Coordinate any shared uCore route changes with the coordinator. |
| uCode and qualification | Verify Local input and BBC BASIC host callback support. Add the agreed command bindings after services stabilise. Exercise offline resolution, tap replay, cross-profile isolation and edition navigation end to end. Report any capability still using a fixture or awaiting staging. |

With two agents, run coordinator/library and spatial/workflow first, then take publishing and command qualification in sequence. With more capacity, run the four implementation lanes after Gate 0 and bring in uCode/qualification once the shared interfaces stabilise.

## Production readiness and release decision

The coordinator records the exact commits, fixture revision, test results, rollout owner and rollback rehearsal for each release candidate. The Wizard reviews the release decision and any canon or publishing-origin change. Ship the offline slice first. Qualify online adapters, BBC BASIC and timed execution as separate capabilities so their readiness can be verified independently.

| Release check | Required evidence | Owner |
| --- | --- | --- |
| Offline operation | Start with networking and Ollama disabled. Browse and rebuild the index, resolve a simulated tap, promote one task, restart and reopen the Tomb in an offline reader. | Qualification |
| Identity and privacy | Use two profiles to test search, counts, deep links, map results, tap replay and export. Inspect the compiled edition for private paths, excluded documents and unapproved links. | Library and Publishing |
| Existing installations | Open a copy of an existing workspace, rebuild its derived index, verify preserved document IDs and record any migration and reversion steps. Use disposable data for rollback rehearsal. | Library |
| Recovery and operating limits | Interrupt work between ingest and task promotion and between release submission and confirmation. Reconcile ambiguous remote outcomes before retry. Record index size and rebuild time, receipt retention and owner-selected limits on a representative workspace. | Feed and uFlow, Publishing |
| Staging and operations | Verify provider credentials and roles through existing integrations, approved destinations, visibility, denial after revocation, and links from the delivery receipt. Record staging and online capabilities qualified for this release. | Publishing, Coordinator |

Roll out first against a disposable workspace, then an approved pilot profile. Keep the previous release and the existing source stores available. If a gate fails, revert the affected release binding, pause its uFlow schedules and revoke its provider/device grant where applicable. Rebuild the derived index using the previous release. For a remote draft or release, inspect the provider receipt and apply the destination's existing withdrawal process with authorisation.

## Standalone handover prompts

Replace bracketed fields before sending each prompt. Supply the coordinator's contract and fixture to the implementation agents after Gate 0.

### Coordinator and release owner

> Read ~/Code/AGENTS.md and uCore/docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Inventory existing entry points and inspect the current dirty checkout. Produce a baseline manifest identifying the commits and approved working changes, a shared fictional RSS/place/Binder fixture, typed reference and policy contracts, and a file ownership list. Start from [baseline]. At handback collect branches and evidence, resolve shared-file changes, and run the offline acceptance scenario. Record per-capability readiness, outstanding decisions and the rollback rehearsal. Keep real-account staging pending explicit authorisation.

### Library and reader

> Read ~/Code/AGENTS.md and uCore/docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Use [baseline], [fixture revision] and [owned files]. Extend the current uCore index and reader with typed results, filters, scoped resolution and configured base paths. Use the agreed fixture projections and preserve existing IDs across moves and rebuilds. Verify deleted results, colliding scoped IDs and cross-profile search, counts and links. Return the branch, migration/rebuild procedure, commands and results.

### Spatial and NFC

> Read ~/Code/AGENTS.md and uCore/docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Use [baseline], [fixture revision] and [owned files]. Implement the in-process marker → waypoint → authorised resource flow using the agreed resolver and existing spatial codec. Add a passive tap fixture with replay-safe receipts and a separate pre-enrolled test-peer handshake. Verify malformed input, replay, expiry, wrong audience and revocation. Report exactly which observations the fixture supplies. Return the branch and test evidence. Keep the scope to software simulation.

### Feed, uFlow and Spool

> Read ~/Code/AGENTS.md and uCore/docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Use [baseline], [fixture revision] and [owned files]. Route the saved RSS item through the existing Feed Store, reviewed proposal and uFlow task promotion. Preserve source revisions and write a linked Spool activity event. Prove replay, interrupted processing and profile checks. Return the branch, a run receipt and the commands used to reproduce one logical task.

### Publishing

> Read ~/Code/AGENTS.md and uCore/docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Use [baseline], [fixture revision] and [owned files]. Compile the fixture Binder through uCore-Publish into a versioned offline Tomb. Verify selected assets, portable links, revision references and exclusion of private material. Preview the guide/place destinations and use the mock adapter to test receipts and ambiguous delivery. Return the branch, sample edition and staging acceptance steps. Coordinate shared uCore route edits with the release owner.

### uCode and independent qualification

> Read ~/Code/AGENTS.md and uCore/docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Use [integrated commits], [fixture revision] and [owned files]. Verify the existing uCode Local input path and whether the embedded runtime supports OSCLI callbacks. Bind agreed commands to the shared dispatcher where supported. Run the offline production checks on a disposable workspace, capture reproducible commands and results, and report capability status and release blockers per gate.

## Antigravity and Codex handover

Use this repo and plan as the shared record. Read the workspace AGENTS.md, this
plan and the relevant source before proposing changes. Use Antigravity for an
assigned implementation or local browser check. Use Codex to reconcile the
patch, run checks and review the same running app when browser access is
available. Either tool can take either role when its local capabilities allow.

At pickup, record `git rev-parse --short HEAD` and `git status --short`.
Transfer pending changes as an agreed patch or topic branch. If both tools
work concurrently, assign disjoint files or use isolated worktrees from the
agreed baseline. Treat generated proposals as suggestions until their paths,
API contracts and changes have been verified in the checkout.

| Surface | Existing route | Contract to verify |
| --- | --- | --- |
| Local Wiki Reader | `/documentation` | Library search and `GET /api/library/stats`. Open a typed result in the reader. |
| Feeds | `/workflow?tab=feeds` | Import saved RSS with `review_only: true`, then promote explicitly and verify the task link and available `spool_receipt`. |
| Binder publishing | `/workflow?tab=binder` | Open an edition and inspect Export to Public and its receipt. Use a disposable Binder for an actual export. The fixed-fixture Tomb API is a separate Wizard pilot. |
| Simulated NFC | `/ucode-plus` | Expand Simulated NFC tap and use the Oakhaven fixture. The client sends an event ID and a versioned marker envelope. |

The product UI lives in `frontend-vue` and uses the existing AppShell,
UIcon and USX controls. Implement UI changes in the owning Vue surfaces.
Use the launch commands and ports in the repo README. If a tool cannot reach
the running browser, hand off the route, selected fixture and expected result
to the tool with access. Record browser observation separately from builds
and mocked tests.

### Copy-ready Antigravity prompt

> Work in ~/Code/uCore. Read ~/Code/AGENTS.md and the Antigravity and Codex
> handover in docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Record HEAD and dirty
> files first. Verify the four existing Vue screens in a local browser using
> disposable data for mutations. Report observed behaviour, exact failing
> steps and screenshots where available. For any assigned fix, preserve
> pending changes and return the branch or patch, touched files, verification
> commands and unresolved items. A model or tool error requires checking the
> actual diff before reporting an edit as complete.

### Copy-ready Codex pickup prompt

> Work in ~/Code/uCore. Read ~/Code/AGENTS.md and the Antigravity and Codex
> handover in docs/plans/LOCAL_FIRST_LIBRARY_DELIVERY.md. Compare the supplied
> branch or patch against current HEAD and working changes. Review the
> affected Vue and backend contracts, run the relevant tests, and repeat
> browser checks where available. Report what was observed, what was tested
> through mocks, and what remains unverified. Keep profile-scoped library
> access, private Tomb export and generic NFC resource links open until their
> respective acceptance checks pass.

### Browser pass status · 20 November 2026

Antigravity reported failed Feeds and Binder HEAD checks and announced a
Chromium run. Its handover supplied no completed browser observations.
Codex saw listeners on ports 5175 and 8484, but its GET requests to all four
routes and the library stats endpoint failed to connect on loopback. This
leaves the visual pass pending. The connection result alone gives no
evidence about Vue rendering.

Run the next pass from the desktop browser that can reach the local
frontend. Start with a normal navigation to /documentation and confirm
that the Vue shell and reader render. Then use the route table above.
Record one verdict per route, the visible error if any, and the path to
each screenshot. Keep screenshot files separate from the plan.
