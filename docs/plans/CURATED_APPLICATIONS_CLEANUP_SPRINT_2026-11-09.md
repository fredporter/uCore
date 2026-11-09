# uDOS user-workspace cleanup and curated applications sprint

Updated: 2026-11-10 · Australia/Perth
Status: Slice 1 in progress; not release-certified
Scope: uCore host and bundled uFlow authority, uCode language/runtime, existing product/package owners

## Purpose

People choose curated applications, connect local content, preview results, and run or schedule useful work without writing code. Optional uCode learning/composition supports internal user operations. Local and explicitly connected AI help creative output, personal knowledge and projects. General software development, application packaging and canon curation happen externally in maintainer IDEs.

This is the single current backlog for the conversation. It supersedes conflicting internal IDE/Dev Mode priorities while preserving useful code, data and historical evidence. It is not a claim that the proposed application platform, autonomous knowledge workflow or all sync adapters already work.

## Latest decisions — execution authority

The following refinements supersede conflicting wording later in this document and earlier plans:

1. **Binders only.** One Binder holds tasks, documents, sources, research and outputs. “Lists” and task boards are compatibility/storage details, not another user-facing container. External provider list/group names remain source metadata and sync boundaries.
2. **One Workflow dashboard.** Binder content and Research belong in the dashboard under the selected Binder context. Main tabs are Workflow, Tasks, Queue and Editor. Connected collections belong in Snackbar; Sidebar selects a Binder.
3. **One sidebar browser.** Switch between Vault and Binders. Knowledge uses that shared sidebar, not another file picker inside the reader. Contents/headings remain optional reading aids, not a second filesystem tree.
4. **Shared functionality first.** Similar functions across surfaces must consume the same resource contract and shared component, rather than copy controllers, state, APIs, pollers or CSS.
5. **uCode is the user's optional programming language.** The Terminal starts its actual BBC BASIC language authority, not zsh. Vault/workflow commands must be registered capabilities with real validation; do not invent command vocabulary or implement another interpreter.
6. **Non-development assistance.** Ollama/OpenRouter support personal knowledge, creativity, learning and projects. A uCode authoring skill is grounded in the installed language/reference and capability manifest. General software development stays external.
7. **Discover capabilities, don't embed model shopping lists.** Installed model inventory is live. Reviewed app/skill/model pack manifests supply requirements, licences, sizes and compatibility. Do not hard-code developer recommendations in Python or UI.
8. **Roundtable is bounded work, not an autonomous developer team.** Research, Create and Review reuse adequate installed models, normally sequentially. Repeated agreement is not verification. Web retrieval is explicit; accepted personal/shared layers preserve canonical Global Knowledge.
9. **Curated applications require no code from users.** Install reviewed code packages through a real managed runtime. Simulated installs/running states cannot count as success.
10. **Fresh start is authorised and performed reversibly.** Existing task folders, workflow definitions/runs and research queue history were archived on 2026-11-09. Do not re-seed technical examples or restore old user content automatically.

The scope now exceeds a credible single ten-day sprint. Keep one ordered programme backlog with three gated delivery slices. The first sprint is foundation/cleanup, the second delivers one curated application, and the third qualifies interest-driven knowledge/sync automation. Each slice must be useful and truthful independently; dates remain planning targets until its first-day capacity review.

## Current-state assessment

| Area | Working / changed | Remaining gate |
| --- | --- | --- |
| Workflow | Real task persistence and contextual editing; reversible fresh-start archive; dashboard composition | Complete Binder identity/profile/source migration and context-scoped research |
| Reader/sidebar | One sidebar tree, wider reader, central reading font, top toolbar, optional metadata/TOC and toolbar actions | Shared behaviour/regression checks across reader, Editor and uCode guide; keyboard/fullscreen/narrow tests |
| uCode | Native language route; live BASIC calculation succeeds; language reference owned by uCode | Registered vault/workflow command bridge, validator and authoring acceptance suite; do not fabricate unsupported commands |
| Ollama | Live installed inventory; explicit tagged model download/progress; bounded local selected-text roundtable preview | Durable download jobs, reviewed packs/hardware qualification, dependency-aware cleanup, research/skills integration |
| Skills | Governed builtin registry and confirmation contracts exist | Curated non-dev skill inventory, version/enable/disable/dependency management; no arbitrary AI-installed code |
| Application platform | Existing package/catalogue and container records; fake package install/update success removed | Actual verified artifact installation and real isolated executor |
| Sync | Source-scoped engine and Snackbar facade; Mac/direct Google adapters; browser file exchange | Live account round-trip qualification, full facade consolidation and Linux handoff/live-adapter work |
| Development retirement | Gallery/runtime navigation removed; Settings agent table and assistant developer-store dependency removed | Audit remaining APIs/configs/external consumers before retiring repo mutation/ACP/agent execution |
| Global Knowledge | Preserved source/install split and availability checks | Remote corpus reconciliation, licensed edition manifests and atomic installer; immutable canon plus personal/shared overlays |
| Publishing/repos | Protected uCore release flow exists; old superseded sources archived previously | Audit all active repo divergence and package contracts; qualify publishing/export adapters individually |

## Surface ownership

- **Home:** resume work and launch installed useful applications; no duplicate sync/infrastructure dashboard.
- **Workflow:** dashboard with Binder documents/sources/research, Tasks, Queue and contextual Editor. Binders contain tasks and content; groups/sections are inside a Binder.
- **Sidebar:** Vault or Binders; sole workspace/library file browser. Preserve current location and provide full-width aligned rows.
- **Knowledge:** read the installed reference bank and Shared/Personal overlays through the common reader. Canon editing belongs to maintainers externally.
- **uCode / creative tools:** optional BASIC learning, internal operations and GridCore output; uCode2/vector/spatial features retain their existing product owners.
- **Snackbar:** curated apps/snacks, routines, imported Tasks/Contacts/Notes/Feeds, assistant and reconciliation. Imported Tasks are a source view of the same logical work, not another task authority.
- **Settings → Apps:** selected native/cloud app connections, scopes and app recommendations. Keep connection setup out of the first-run story.
- **Settings:** Name, assigned Role, appearance, reading preferences, assistant preferences and explicit Advanced connection/cost controls.
- **Server:** Python/backend, Node/Vue host, Docker/runtime lifecycle, Git/GitHub installation/publication support, Ollama service lifecycle, core Vault/Obsidian health, bounded logs/recovery. No internal IDE.

## Shared resources and consolidation contracts

A second view does not justify a second owner or data store. Extract/refine the existing owner before adding another abstraction. Resource contracts must work for UI clients, Snackbar routines and uCode alike.

| Resource | Single authority / reusable contract | Consolidation acceptance |
| --- | --- | --- |
| Binders and task membership | Existing uFlow Binder/task authority behind uCore | One stable Binder identity; old board/list paths are aliases; task IDs and imported replica links survive moves; one creation form |
| Files, selection and navigation | Shared workspace/file browser and document selection contract | Sidebar owns browsing; readers/editors use the same selected document/version; roots and permissions are consistent; no duplicate tree fetch/poller |
| Document rendering | Shared Markdown/frontmatter/TOC/citation renderer | Box metadata, optional metadata/contents toggles, bullet-free indented TOC, safe links and matching reader typography across Knowledge, Binder and Editor |
| Reader preferences | Profile settings store and preferences API | Reading font is in Settings; no per-surface Serif/Sans state; toolbar at panel top; one inner gutter, no stacked padding/borders |
| Assistant/model access | One local Ollama adapter plus explicit provider gateway | Live inventory, capability-aware selection, bounded requests and one cost/privacy policy; no duplicate per-surface model list or implicit cloud fallback |
| Skills and applications | Governed existing capability/catalogue registry with versioned pack manifests | Skills expose typed inputs, scopes, limits and evidence; apps expose purpose/results. Prompts alone cannot install tools, mutate the canon or gain host permissions |
| Jobs and results | Existing worker stores, uFlow run linkage and one Queue read model | One job identity/status vocabulary; shared retry/cancel/progress component; no new parallel scheduler for each surface |
| Sync | Snackbar facade over the source-scoped connection engine | Manual, scheduled, feed and uCode calls use the same reconciliation path, lock, profile scope and last-success record |
| Install/update/remove | One reviewed catalogue and Server execution adapter | Actual artifact verification, progress, rollback and data-preserving removal; model/content/skill artifacts remain distinct types with declared owners |
| Identity and setup | Existing profile/identity and settings contracts | Name once; Role separately assigned; setup resumes without resetting saved answers; account config is in Apps, not a second setup subsystem |
| Design/navigation | Canonical USX/Prose/GridCore tokens and shared controls | Compact one-row toolbars; common selectors/buttons/icons/focus states; no independent font/palette/layout systems in gallery derivatives |

Before any extraction, list existing callers and ownership. Keep stable public contracts or add a tested compatibility alias, migrate callers, then retire the duplicate. Do not centralise unrelated product algorithms merely because their screens look alike.

## Reviewed application / offline pack contract

One catalogue contract handles distinct artifact types: application, model, skill and knowledge edition. It declares identity/version, owner/upstream/provenance, licence, verified digest/signature, OS/CPU/runtime, exact installed/download size when known, dependencies, typed inputs/outputs, filesystem/network/credential permissions, CPU/memory/time/output limits, retry/cancel behaviour, migrations, rollback and data-preserving removal. Do not create a second store, scheduler or package manager per artifact type.

Server owns actual installation and isolated execution; Snackbar owns user invocation/scheduling; uFlow owns task/run linkage. Models remain Ollama-owned rather than copied per skill/app. Scratch state uses settings-resolved UDOS_HOME; accepted documents remain in approved Vault/Shared destinations. No new hidden HOME state or shared monolithic Python environment. Existing app-owned credential/model locations are not silently moved.

A database row labelled running is not execution. The executor must prove real process/container start, bounded logs, resource/network/mount enforcement, true exit/results, cancellation and cleanup. No privileged container, blanket HOME/repository mount, in-container Docker socket or arbitrary host-shell fallback. Built-in readers and uCode do not require Docker simply to open the workspace.

## Roundtable and knowledge rules

Research → Create → Review is one bounded user job, normally reusing one adequate local model sequentially. It is not a general developer-agent team. Model/role agreement is not factual verification. Runtime capability and language references ground uCode drafts; scripts are validated and explicitly authorised before execution. Retrieved pages and notes never grant tool/install authority.

Interests and projects select sources, Binder, cadence and budgets. Existing research tools collect evidence/citations; accepted results enrich Personal or Shared overlays. Preserve originals, source identity, dates, licences, uncertainty and deduplication history. Canonical Global Knowledge is immutable through user flows; proposed canon improvements become reviewable Wizard submissions. Cloud/OpenRouter use is explicit, scoped and budgeted, with no silent fallback. Offline/deterministic workflows remain useful without AI.

## Consolidated execution sequence

### Slice 1 — clean user workspace and truthful foundations

Proposed ten-working-day target. Start with a green baseline and end with an offline, usable workspace. This is the sprint to commence/continue now.

| Ticket | Priority | Work and dependency | Evidence required |
| --- | --- | --- | --- |
| F01 / C01 | P0 | Freeze inventory of working tree, active repositories, runtime state and prior plans; record archive/restore checkpoint | No uncommitted work or user records lost; source versus runtime clearly separated |
| F02 / C02 | P0 | Binder-only model and shared sidebar; migrate list/board UI/callers into existing Binder authority; dashboard composes Binder content and research | Create Binder → add task/document → navigate/edit → reload; task IDs/versions/source links unchanged; no duplicate picker or Binder tab |
| F03 / C12 | P0 | Shared-resource consolidation pass using table above; consolidate document rendering/navigation, controls and status/polling first | One owner per resource; tests cover at least two surfaces consuming each changed contract; old implementations removed only after caller migration |
| F04 / C03 | P0 | Retire internal repo/IDE chat and development-agent defaults after call-site audit | Ordinary assistant never initialises repo agents/commands; historical conversations/source evidence retained; no new IDE configuration |
| F05 / C11 | P0 | uCode Terminal and language contract: native language entry, installed reference, testable bridge inventory and scoped command validation | Immediate calculation, numbered program + RUN/LIST, reconnect/missing runtime, and honest unsupported-operation messages; no shell fallback |
| F06 / C02 | P0 | Apply useful recipe layouts to their owning working features; remove gallery route/top-level entry; qualify remaining previews | Task layout → Tasks, authoring/citations → Editor/Binder, prose → reader, story → Setup, terminal/teletext → uCode, status → Server; no sample records injected |
| F07 / C08 | P1 | Reader/settings/setup polish and beginner starters; remove engineering wording and repeated explanations | Shared reading-font preference; metadata and contents toggles; compact top toolbar; keyboard/fullscreen/narrow view; setup no account wall |
| F08 / C10 | P0 | Qualification and checkpoint release | Full isolated tests/build/path/action/credential checks; live empty Workflow and actual Terminal proof; docs match shipped scope; protected PR and reviewed merge |

**Slice 1 demonstration:** start from the archived empty state, create one Binder through the normal form, add a meaningful personal task and Markdown note, navigate via the single sidebar, read/edit with consistent controls, and run a small uCode program. Use isolated disposable fixtures for destructive/round-trip tests; do not repopulate the user's empty workspace as QA.

### Slice 2 — curated applications, offline installation and local assistance

Starts after Slice 1 contracts stabilise. C04–C06 are the critical path; retain the original reading-pack demonstration as its release gate.

- **A01 / C04:** One reviewed app catalogue/manifest and real installer. Detect existing host tools before offering installation; no duplicate Ollama service/app or Python environment. Verify release source, signature/digest, licences, OS/CPU and disk requirements. Distinguish missing runtime, downloading, verifying, ready, failed and updating. Existing installer simulations must fail closed.
- **A02 / C05:** Real isolated app executor and lifecycle; explicit input/output mounts, network, credentials, CPU/memory/time/output limits, cancellation, logs and recovery. Server owns it; Snackbar and uCode are clients. Core reading/uCode do not require Docker.
- **A03 / C06:** Package the reviewed offline reading-pack application from existing working code. Preview, execute, inspect actual output, link result to Binder, repeat safely and uninstall without deleting user output.
- **A04 / C08:** Ollama management: dynamic inventory/capabilities, reviewed offline packs, actual download progress, durable resumable jobs, memory-aware selection, usage/storage visibility and explicit dependency-aware cleanup. Do not delete coding models merely because their names mention code; some may suit uCode. Record evaluations before retiring unused ones.
- **A05 / C08:** Roundtable as one bounded job: Research → Create → Review, with a uCode authoring capability for relevant requests. Prefer one adequate model reused sequentially. Cite source documents, record uncertainty, limit passes/tokens/time, support stop/recovery, return a reviewable draft and never interpret retrieved content as execution permission.
- **A06 / C04:** Skills library through the existing registry, not a new agent/plugin tree. Versioned reviewed manifests, typed arguments, source/capability provenance, enable/disable for optional skills, app dependencies and clear uninstall effects. AI-produced uCode is a draft until validated and authorised; Python/shell code is packaged externally.
- **A07 / C07:** Unified Queue adapter for workflow, research, app, model-download and sync jobs; source IDs preserved. Only retry-safe work retries automatically; mutating steps retain approval/idempotency boundaries.

### Slice 3 — interests, knowledge layers and connected life

- **K01 / C13:** User interests/projects become explicit local profile/Binder preferences, with opt-in sources, cadence, relevance, time/storage/network budgets and “pause all”. Start with a single personal interest digest, not unbounded background crawling.
- **K02 / C13:** Research intake reuses existing fetch/citation/worker contracts. Deduplicate by source identity/content, preserve original evidence and licences, reconcile updates and separate summaries from verified facts. Saved accepted results enrich Personal or Shared overlays; baseline canon stays immutable in user flows.
- **K03 / C13:** Wizard review/submission and Global Knowledge editions. Reconcile preserved developer corpus with the minimal remote through reviewed history/import work; build manifests/checksums/licences and Core/Essential/interest editions; stage/verify/switch/rollback installs atomically. Modern and teletext readers use the same edition and mapping standards.
- **K04 / C09:** Snackbar local app sync proof for selected Mac app lists/groups, then Linux standards-based handoff and later a qualified live adapter. Keep iCloud/Google authentication and normal cloud sync with the chosen stable apps. Direct cloud APIs remain explicit Advanced options.
- **K05 / C09:** Contact/task/note reconciliation, stable IDs, duplicate suggestions, explicit merges and conflict review; flags drive opted-in routines while source groups/lists define sync scope. VIP/stars remain identifiable source semantics. Provider deletions and unsupported fields must not be silently inferred.
- **K06 / C09:** Bookmarks/favourites/reading-list HTML exchange is the current working boundary. Continuous browser integration is a separately qualified adapter; no direct mutation of live browser databases as a shortcut.
- **K07 / C14:** Remote/local repository and publishing alignment. Compare active checkouts/branches/remotes, retain unrelated projects, archive proven remnants with recovery manifests, finish protected app releases and knowledge publication independently. SnackMachine is optional catalogue tooling, not another Server; Google/Publish scaffolds do not claim deployment until tested.
- **K08 / C10:** Consolidated first-run, installer, offline-model, app/skill, sync and recovery quickstarts. Document what is manual, installed, supported, proposed or unavailable. Keep external maintainer guides separate from beginner learning.

## Recipe disposition

The gallery is no longer an ordinary runtime destination. Existing recipe source/tests remain implementation references for external development until useful behaviour is absorbed and verified.

| Gallery item | Working owner | Qualification work |
| --- | --- | --- |
| Task list | Workflow Tasks | Real task status/group/Binder operations, not local sample checkboxes |
| Authoring workbench | Contextual Editor + Binder sources | Existing editor save/citation/version contracts; no separate unsaved document state |
| Prose document | Shared Knowledge/Editor renderer | Same properties, TOC and font settings |
| Card matrix | Home / installed apps | Real installed app metadata and actions; no placeholder launch success |
| Settings form | Settings | Existing persisted profile preferences |
| Story form | Setup and guided app configuration | Existing StoryWizard, validation and resume state |
| System page | Server | Actual health, truthful runtime/install status |
| Alerts | Shared overlays / Queue | Real status/events and consistent action controls |
| Terminal / teletext | uCode | Actual runtime/reader, not static canvas screen text |

## Complete conversation backlog coverage

| Request | Owning tickets / disposition |
| --- | --- |
| Repair/self-heal, offline banner, Python/environment hardening | F01/F08; retain existing bounded recovery and owned environment; no repeat execution of unsafe historical actions |
| Calm terminology, aligned controls, typography, padding and one-row toolbars | F02/F03/F07 across touched surfaces; shared tokens rather than copied CSS |
| Task navigation, done/next, drag/drop/group/move/copy and Editor integration | F02; one Binder identity and durable task IDs, not separate lists |
| Merge Binder content/research into Workflow dashboard; Queue is cross-workspace | F02, A07; keep existing records/worker owners and contextual links |
| Duplicate docs file picker, frontmatter boxes/toggles, TOC, fullscreen and toolbar actions | F03/F07; sole sidebar and shared document renderer/preferences |
| Recipe layouts become working features | F06 disposition table; no generic showroom or sample production records |
| User Name/Role/email, host timezone/location/grid seed and first-run story | F07; save once/resume, host clock authority, explicit seed readiness, optional practical starters |
| Apple/Google contacts/tasks/notes/mail/calendar, flags/VIP/stars and source groups | K04/K05; explicit scopes, duplicates/conflicts and tested round trips; no blind cross-account copying |
| Bookmarks/favourites/reading lists | K06; current manual exchange stays accurately labelled |
| Recommended Mac/Linux apps, app installation/management and Snackbar central sync | A01/A02/A06, K04; app-managed cloud accounts, no duplicate iCloud service |
| Ollama cleanup, installation, offline libraries and skills library | A04/A06; dynamic inventory and reviewed manifests; no automatic model deletion/download |
| Non-dev roundtable, interests and projects, local knowledge enhancement | A05/K01/K02; reviewable outputs in overlays, bounded autonomous work |
| uCode commands and an assistant skilled in uCode | F05/A05; real language authority/capabilities, no zsh or guessed syntax |
| Server/Popcorn/SnackMachine ownership, Obsidian as core, external IDE development | F03/F04/A01/A02/K07; one owner per lifecycle and capability |
| Global Knowledge source repo, large editions, shared seeds/GridCore/teletext | K03; preserve Code source and Public installed baseline, reconcile remote corpus without force-push |
| Code-folder remnants, Xcode retirement, repository/branch merge and publishing | F01/F08/K07; prior cleanup retained; audit new diffs, protected release flow and recoverable archive |
| Clean current Workflow/Binder “lists” and start fresh | Completed reversible archive checkpoint below; no automatic technical reseeding |
| First-time credentials/setup/quickstart and honest capability documentation | F07/F08/K08; separate beginner use from external maintainer packaging |

## Release and rollback gates

Run isolated backend tests, frontend tests/type-check/production build, action binding inventory, whitespace/path policy and credential scan against the final tree. Do not treat static handler bindings as proof of native/cloud effects. Exercise fresh-profile setup, offline use, language runtime, restart recovery, concurrent document edits, missing optional runtime, cancellation and failed credentials. Qualify target Apple Silicon/macOS and supported Linux independently. Use disposable fixtures, not new technical tasks in the user's clean Workflow.

Restore prior app/host artifacts without overwriting new user work. Retain source identities and personal/shared outputs. Knowledge installation stages/verifies before switching and preserves the prior edition. Archive proven superseded sources with manifests; do not delete unrelated repos, accepted documents, credentials or historical evidence.

Source publication follows repository → branch → isolated checks → protected PR → required CI → reviewed merge → versioned artifact → clean install smoke test. Content edition publication is independent and licence/provenance-qualified. Current uCore and uCode edits must be checked/committed in their own repositories; no force-push of preserved knowledge history.

## Current checkpoint and limits

- Publishing/export ownership checkpoint (2026-11-10): runtime documentation build/deploy returns HTTP 410; the deployment helper cannot initialise/commit/push Git, and external static builds require an explicit destination. Jekyll preparation rejects execute_git before writing and defaults to User Vault; local preparation, source content and publication guidance remain. Removed unused deployment UI state and Git execution fields from the client. GET docs/export is discovery-only; POST restricts source/output to configured Vault/Shared roots and defaults to `Vault/Exports/doclang/vault-doclang.jsonl`, never Global Knowledge. This is a user-owned generated artifact, one output file per chosen path (replaced by subsequent exports), retained until the user removes it through normal files; no daemon or extra runtime cache. Export scans skip symlinks outside their source. Historical publishing receipts remain readable. Validation: 737 backend tests, 148 frontend tests, production build, final type-check, documentation route contract, action audit, path policy and whitespace passed. External deployment and static-builder packaging qualification remain maintainer work; Binder editions and personal export adapters retain their existing owners.

- F04 documentation-mirror boundary: repository write-back is retired at both HTTP API (410) and compatibility service level, including the legacy bypass argument; no persisted Dev Mode value can re-enable it. Removed unused reader edit/save state, controls, handler and styles. Refresh/status/diff/reading remain; cache refresh rejects source/destination symlink escapes and index symlinks, while diff validates indexed paths before reading. Forbidden user roots come from owning settings. Source repositories and installed canon remain unchanged by these tests. Validation: 732 backend tests, 148 frontend tests, ten focused mirror checks, documentation route contract, type-check, action audit, path policy and whitespace passed. Publishing/deployment APIs are a separate pending ownership audit.

- F04 generic execution/Dev Layer retirement: `/api/exec` now returns HTTP 410 without reading payloads or starting subprocesses; removed its unused frontend client helper. No active frontend, MCP, script or audited sibling-product callers were found. Dev Layer state/HUD reads report off/retired without loading saved mode or collecting development data; enable/toggle return 410. Explicit mode=off preserves persistence and cancellation of leftover development work. Registered skills, executable IDs and task actions retain their existing governed routes. Validation: 728 backend tests, 148 frontend tests, type-check, path policy and whitespace checks passed. Historical Dev Layer service code and documentation-mirror write gating remain available for a separate external-maintainer/canon audit; no old persisted user configuration was automatically rewritten.

- F04 production endpoint retirement: audited runtime Vue callers, menu callbacks and the read-only `backend/app/mcp/udos_mcp` bridge, plus sibling uCode/SonicScrewdriver/HomeNest sources. Repository writes/stage/commit/moves, new command/ACP operations, decisions/apply, developer start/workspace and chat execution now bind to HTTP 410 (`internal_development_retired`). Fifteen mutation routes plus developer-chat streaming are retired. Repository inspection, historical conversations/operations/runs and stop/cancel remain accessible. Capability/status responses explicitly report retirement without probing Vite or starting a manager. Legacy implementation source remains for historical tests/recovery; Dev Layer toggles and further agent/exec surfaces remain a separate audit. Final full backend suite passed (729 tests); read-only MCP build/protocol suite passed (3 tests); path policy and whitespace checks passed.

- F04 assistant-default audit: ordinary chat uses the governed skills registry instead of nonexistent API discovery plus sample skills. Removed repository-research wording, invented workflow board names, fixed model recommendations and promised free planning from chat metadata. Unknown tools receive an unavailable response rather than an invitation to execute in Act. Sixteen deterministic chat API tests pass, including no execution of fabricated repository tools; model calls in endpoint tests use fixtures. Developer mutation/ACP endpoints and external consumers still require an independent audit before retirement.

- Commit qualification (2026-11-09, Australia/Perth): complete isolated uCore backend suite passed (723 tests); the subsequently added sync-refresh regression passed with its collection suite (16 tests). Frontend suite passed (148 tests); production build, action inventory, path policy, whitespace and staged credential-pattern scan passed. Fixture-only Chromium checks passed at 1280px and 390px: keyboard sidebar navigation, Binder task opening, one shared Editor sidebar, sidebar close and no page-level horizontal overflow. uCode suite passed (44 tests, one skipped). Tests used disposable runtime/vault roots or intercepted APIs and did not seed the clean user Workflow. Existing create/import/move/copy/save/reload tests cover persistence; real provider account round trips, historical migration, Linux qualification and protected release remain separate gates.

- Task/Binder context checkpoint (F02): Binder views and Editor sibling navigation span source boards; known legacy list links resolve to loaded Binder IDs. Binder move/copy/drop UI changes membership without renaming provider boards, and new Binder tasks use the existing inbox storage lane. Task updates retain original frontmatter/provenance and preserve Markdown bodies for membership/status-only edits; unlinking clears old notebook/collection aliases. Disposable regressions cover source IDs, collection mapping, provider metadata, creation date, links, Markdown formatting, reload and unlink. Validation: 29 backend tests and 148 frontend tests passed; path policy passed. No existing user records were migrated. Unknown legacy lists remain compatibility filters; account round trips and historical migration remain unqualified.

- Binder document ownership checkpoint (F02/F03): imports for existing user Binders now resolve to the Binder engine’s visible `Vault/Binders/<id>/docs/` directory and appear in `GET /api/binder/<id>` as documents, separate from citation evidence. Binder documents share the Binder’s lifetime and user-storage budget; there is no copied cache or additional service, and archive/removal includes the directory. Explicit selected-Binder imports fail if the Binder no longer exists instead of creating a legacy orphan. Legacy unscoped imports remain compatible; existing files are not moved automatically. Opening saved documents uses the shared workspace reader and retains persisted content/version. Frontend suite: 43 files / 146 tests passed; type-check, path policy and action audit passed. Legacy list/board migration and historical document reconciliation remain open.

- Research context checkpoint (F02): Workflow passes the selected Binder identity into Research and replaces its view on Binder changes, keeping search/session state separate by Binder. Job loading uses the existing Binder filter; job creation and Markdown import retain that identity. Queue remains cross-workspace. Saving a note no longer invokes the legacy second-Binder creation API. Removed generated Python filler and unsupported verification claims from research synthesis. Frontend suite: 43 files / 144 tests passed; focused context/save checks, action audit, whitespace and home path policy passed. Global knowledge/bookmark search remains intentionally a source-discovery view; canonical Binder source attachment and legacy storage migration still require qualification.

- Resume checkpoint: F03 removes the Editor-owned workspace tree, viewport state and private sidebar toggle event. Editor and other ordinary surfaces now use AppShell’s existing FilepickerSidebar and shell visibility state. The empty Editor opens that same sidebar; it no longer preloads a second tree. Frontend regression suite: 41 files / 140 tests passed; home path policy and whitespace checks passed. Binder identity migration, context-scoped research and live narrow/keyboard qualification remain open.

- Fresh-start archive: `Code/ARCHIVED/workflow-fresh-start-2026-11-09-214022`; SHA-256 movement checks passed. 102 Markdown task files, prior workflow DB and research queue DB preserved. Active task/list/run API counts were all zero after restart. Vault documents and external records were not changed; all connections were already paused.
- Terminal route now launches the packaged official BASIC executable directly. Live WebSocket check: `PRINT 83+7` returned `90`, without zsh. uCode language reference comes from its owner. This does not certify unimplemented vault/workflow language extensions.
- Fixed developer-model recommendations are removed. Inventory is discovered locally; all eight existing models are preserved. No models were downloaded or deleted in this work.
- The local roundtable is a bounded selected-text preview with three sequential passes and no tools/filesystem writes. It is not yet durable autonomous research, a fact-verification engine or a finished managed skills platform.
- Actual model pull/progress plumbing exists for an explicitly chosen official tagged reference. Reviewed manifests, durable download recovery, hardware qualification and dependency-aware removal remain A04. Arbitrary tagged downloads are not described as reviewed uDOS application packs.
- Simulated package install/update success is removed; those operations report unavailable until the real artifact/executor path is configured. Container execution remains unqualified.
- Knowledge navigation is moved into the shared sidebar. The duplicate in-panel file tree/header is removed. Reading font is centralised in Settings; toolbar is at panel top, outer padding removed, TOC bullets removed, and properties/TOC are toolbar toggles. Layer/copy actions are in the toolbar action menu.
- Binder dashboard composition and naming cleanup are underway. Full Binder identity/legacy-board consolidation, context-scoped research and removal of all duplicated state are still F02/F03 gates; do not equate changed labels with finished data migration.
- Cleanup checkpoint is ready for local commits in uCore and uCode. Validation below qualifies the touched behaviour; no protected merge, target-platform release or live account certification is implied.
