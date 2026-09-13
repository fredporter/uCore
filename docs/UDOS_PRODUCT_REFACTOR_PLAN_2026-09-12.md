# uDos product refactor plan

Date: 12 September 2026  
Status: agreed product direction; implementation plan awaiting Gemini's mandatory pre-start assessment  
Implementation environment: Gemini / Google Antigravity  
Companion: [Gemini handover](HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md)

## 1. Purpose and authority

uDos helps people turn local information into useful documents, interactive resources and publishable knowledge. Obsidian is the default editor. Antigravity is the external development environment. uCore is a user application/service host, not an IDE or general development environment.

September 12 clarification: this is a productisation and completion refactor of two years of accumulated work, not another rebuild. Preserve valuable features and the emerging UI look, layouts and interactions. Separate ownership, dependencies and release paths so practical standalone products can serve real projects outside the uDos ecosystem, while remaining compatible components when combined. The user's explicit retirements (internal IDE/Dev Mode and AppFlowy dependency) do not authorize general feature reduction.

This document records the user's decisions from the September 12 planning conversation. Creating this plan authorizes documentation only. No runtime refactor, installation, deletion, migration, commit, external message or publication is performed by this planning task. Gemini must assess the plan and current workspace before implementation, as specified in the companion handover.

The user-approved direction supersedes conflicting product priorities in the September 9 internal-development handover, Dev Chat/Internal IDE readiness plans and earlier Dev Mode roadmaps. Preserve their useful implementation evidence, security controls and historical records. They must not be used to resume internal IDE expansion. Earlier Sonic/HomeNest/Home Assistant handovers remain useful except where this plan explicitly refines shared boundaries.

Repository instructions, code and tests still require inspection. Record conflicts rather than silently rewriting instructions. Do not mistake this plan for evidence that a proposed capability exists. New command names, package names, schemas and destinations require verification before adoption.

## 2. Non-negotiable product principles

1. Every document has a durable Markdown representation. Originals and structured assets retain appropriate formats.
2. Local files and accepted local editions are authoritative working records. Remote copies reconcile explicitly.
3. Core reading, editing, search, task access, installed BASIC programs and local export work without cloud accounts or inference.
4. AI is optional assistance. Use deterministic tools first, retrieval next, and the least costly adequate model where inference helps.
5. Cloud connectivity and cloud inference are separate, explicitly scoped permissions. No automatic cloud fallback.
6. Products install and release independently through declared, versioned dependencies.
7. Ordinary users make things with uDos. Extending uDos belongs to external developer documentation and tools.
8. Feeds describe interoperable information; MCP exposes bounded capabilities. Neither is a mandatory transport for every internal function.
9. One owner per durable task, document, capability, credential and publication record. Views do not create competing stores.
10. Preserve evidence and accepted work. Enhancements never silently replace originals or erase requirements.
11. Zen means few meaningful choices, progressive disclosure and predictable results, not hiding failures.
12. Open files remain usable outside uDos and Obsidian. Product-specific views have readable fallbacks.
13. Preserve working product features and visual identity by default. Reassign or extract capabilities before considering removal; every retirement needs an explicit user decision or an evidence-backed disposition.
14. Release from individual repositories. `/Users/fredbook/Code` is the workspace home and temporary assessment scope, not a permanent monolithic build, runtime or development target.

Offline-first includes prepared installers, dependencies, model weights, fonts, documentation and recovery material. Devices still need power; qualify resource use and provide non-AI/static/printable outputs for constrained situations. A preserved local record is not automatically factually correct: dates, provenance, uncertainty and correction history remain essential.

## 3. Product and ownership map

| Lane | Target responsibility | Boundary and release rule |
| --- | --- | --- |
| uCore / UI Hub | Calm user shell, notebook projects, review/publish views, installed-product entry points | No internal IDE, Dev Mode, arbitrary repo browsing or maintenance dashboards |
| uKnowledge | Filesystem vault reading, indexing, search, provenance, library editions and contribution validation | Usable as a library/package without uCore, AppFlowy or AI |
| uFlow | Durable document projects, tasks, scheduled runs, checkpoints, execution evidence and recovery | Obsidian/Hub are clients; no duplicate task authority |
| uCode / GridCore | BASIC/runtime commands, grid rendering, retro software/capsule contracts | Independent packages; no dependency on host implementation |
| Sonic-Screwdriver | Hardware knowledge, diagnostics, qualified provisioning and offline device/toolkit use | Installs versioned dependencies; never owns a second interpreter or general host |
| Snackbar | Independent platform launcher, capture actions and small local action execution | Works alone with Obsidian; discovers products and hides absent launch entries |
| SnackMachine | Optional action/package catalogue and distribution support | Reassess package-manager duplication; no compulsory store UI |
| Publishing | Vault review, compilation, editions and publication adapters | Offline/static baseline, GitHub option, separate commercial hosting |
| Classic Modern Mint | Cinnamon and Xfce installation/configuration profiles | Qualified upstream base; reversible overlay, no new desktop environment |
| Portal / Beacon | Local content hubs, access-controlled portals and network integration | Separate product lane; align names/ownership with existing Sonic Beacon work before creating a repo |
| udos-google | Optional Google research/model/import/export/mirror adapters | Never canonical content or identity; distinguish local ledger from real remote actions |
| External development | Antigravity suite, maintenance CLI/MCP, SDK/capsule guides, experiments | No runtime dependency or user Dev switch |
| HomeNest | Standalone Steam/media living-room product | Preserve existing revival handover; optional uDos integration |
| udos-home-assistant | Adapter to the existing upstream Home Assistant/Matter products | Optional HomeNest TV/controller surface; upstream HA owns automations and device state |
| Groovebox | Standalone music production suite | Practical music workflow, independent release and interchange; no core release dependency |
| uVector | Standalone image generation and uDos image standardisation tool | Unified technical drawings, diagrams and scientific-style illustrations for published vaults; own release |
| uCode2 | Advanced spatial/runtime capabilities | Assess actual consumers and preserve useful features; later release scope must be explicit |
| Other extensions | Identity, budget, agents, Dreamscape and remaining domain functions | Classify actual code as shared capability, optional product, scaffold or retirement candidate |

Product separation does not automatically require new repositories, daemons or identity systems. Define install/release/dependency boundaries first. Generic runtime extraction is justified only by a concrete independent consumer.

### Product preservation and independent entry points

Every product needs a concrete job for a user who does not know uDos: make music (Groovebox), create coherent technical illustrations (uVector), use a TV for games/media and optional home controls (HomeNest), revive hardware (Sonic), collect desktop activity (Snackbar), or publish a researched library. An extension is an integration/packaging relationship, not a limit on the product's ambition or independence.

Preserve the current UI language and useful surfaces. Capture a baseline of existing routes, screenshots, interactions and supported workflows before changing boundaries. Extract/reuse components and preserve behavior; do not replace the UI with a new design because the ownership table changed. Explicitly remove/repurpose only the agreed developer surfaces and their responsibilities. Shared USX/prose tokens and GridCore contracts unify products without requiring one giant application.

For every existing feature, record one disposition: keep in owner; move to named owner with equivalent user behavior; expose through optional integration; externally document/maintain; or retire with stated authority. No feature may silently disappear between repositories. Source duplication alone is not evidence a feature is unused.

## 4. Mandatory pre-start assessment

Before implementation Gemini must independently reassess this plan and reread the actual contents of `/Users/fredbook/Code`. Previous conversation findings are leads, not a current inventory.

### Required inspection

- Read workspace and applicable nested instructions; inspect Git status, branches, remotes and uncommitted changes in every affected repository.
- Inventory all top-level folders, including hidden runtime/dependency folders, active products, extensions, Vendor and ARCHIVED. Classify them without exposing secrets or private document content.
- Read current manifests, entry points, routes, dependency declarations, service startup, storage configuration, installer/release scripts and relevant tests. Do not rely on README claims.
- Trace cross-repository imports and file paths, AppFlowy dependencies, Dev Mode checks, developer tools, provider policies, Git mutations, editor persistence, packaging and publication flows.
- Compare the current user journeys with this plan. Identify reusable controls before removing their presentation.
- Inventory every meaningful feature and UI surface, including unfinished but valuable work. Record preservation/movement and concrete standalone use cases; do not equate simplification with removing product capability.
- Inspect existing Sonic/HomeNest/HA handovers and WordPress publishing work; reconcile ownership and parallel work.
- Assess missed lanes including Groovebox, uVector, uCode2, identity, budget, agents, Dreamscape, HA, HomeNest, branding/docs repositories and legacy publishing/infrastructure.
- Check current upstream versions, installation links, compatibility, licences and support status through primary sources. Never use the age of a source clone as proof of suitability.
- Identify required hardware, credentials, test fixtures and release channels without inventing their availability.

### Required assessment deliverable

Produce a dated assessment with: repository/commit/dirty-state inventory; implemented/stubbed/untested/retired capability matrix; dependency/ownership map; instruction and plan conflicts; missed lanes; recommended refinements; migration/data-loss risks; support/licensing findings; smallest useful release slice; and an amended execution sequence.

Every proposed change to this plan must say what evidence motivates it, what benefit it provides, what scope it adds/removes, and whether it changes an agreed user decision. Preserve the user's chosen Obsidian/external-development/offline-first direction unless an explicit reconsideration is requested.

The assessment must recommend an independent release order based on actual readiness. The notebook demonstration is a core-track milestone, not a gate that prevents Groovebox, uVector, HomeNest or any other qualified product releasing first.

Present the assessment and recommendations before runtime work. If implementation has not separately been authorized, stop after assessment. Do not repeatedly ask the user to reapprove settled decisions. An improvement proposal is not permission to broaden implementation.

## 5. Remove internal development; create an external bridge

### Remove from the product

- Dev Mode toggle, User/Developer chat scope, internal IDE and arbitrary-repository installation/testing journeys.
- Repo browser, code editor, stage/commit/PR controls and developer operations panels in general user surfaces.
- Developer-only services, routes, listeners, scheduled workers and dependencies once their consumers are removed or migrated.
- General service/agent/model/log/MCP maintenance panels from uCore user navigation.

Removing a toggle must not remove authorization checks. Replace mode-dependent privileges with explicit capability, root, network, provider and budget policies. Disabling a UI alone is not decommissioning a backend endpoint. Test direct calls to retired endpoints.

### Preserve and reassign

- Stale-revision checks, cancellation, scoped execution, audit receipts, safe apply, budget limits and rollback.
- Health/diagnostic data through CLI and bounded MCP for external maintainers.
- Diff/review primitives for user document changes and publishing, restricted to selected vault/publication roots.
- User-visible failure messages and permission/account connection controls needed to complete work; no diagnostic dashboard is needed to explain a failed export.

### Developer documentation in UI Hub

Add a documentation-only advanced section with official install links and explanations for Antigravity desktop, IDE, CLI and SDK. The SDK is optional and advanced. Link to current official commands; only document locally verified uDos commands as working commands.

Document external repo checkout/install/test workflows; how to use uCode/GridCore packages; how to create and validate a capsule; accepted permissions and assets; deterministic build/export; how to install a release into a test profile; and how to remove/recover it. External tools own development sessions. uCore does not run an embedded Antigravity service.

Use the existing bounded MCP gateway where appropriate. Initial bridge: version/capabilities, diagnostics, logs with redaction, contracts and installed artifacts. Mutations require explicit scoped CLI/capability contracts. Avoid generic shell/file-system tools exposed through the user host. Maintenance must remain useful when UI Hub cannot start.

## 6. User experience and Obsidian baseline

### Target journey

Open a vault/activity inbox; create or select a binder; gather sources; define an outcome; complete tasks or run bounded assistance; review document changes; publish an edition. Learn BASIC and add an interactive capsule when desired. Installed product cards open independent products.

Use a small user vocabulary: Vault, Inbox, Notebook/Binder, Tasks, Create, Review, Publish. Resolve Notebook versus Binder consistently during assessment: proposed meaning is Notebook as the interface and Binder as the portable project. Keep CLI/package taxonomy out of the normal flow.

### Supported editor choice

Obsidian is the single recommended default. Remove AppFlowy as a product/runtime prerequisite, installer action, API assumption and onboarding choice after safe export/migration.

| Component | Baseline |
| --- | --- |
| Obsidian | Official installation; ordinary Markdown vaults |
| Core features | Search, Properties, Templates, Daily Notes, Bases and file navigation |
| Tasks plugin | Consolidated task views; plain task checkboxes remain readable without it |
| uDos configuration | Pinned minimal templates, prose/mono stylesheet, Inbox, binder views and help |
| Copilot plugin | Optional local chat via Ollama; explicitly configured local embeddings if used |
| Other plugins | No default requirement until a concrete need and offline/permission review justify it |

Install community plugins through Obsidian's supported flow, linked to their official project documentation. Record exact qualified versions, permissions and settings. Do not indiscriminately enable plugins from imported vault configuration. Link users to Obsidian installers; assess redistribution terms before bundling proprietary binaries. Obsidian is replaceable at the file boundary, not an open-source component to fork.

The configuration works without paid Sync or Publish. Select and qualify one transport per vault/platform profile; do not run competing sync systems over the same folder. Define offline edits, conflicts, deletions and recovery before claiming Apple-device sync. Cloud sync is optional; LAN/offline bundle transfer remains available.

### AppFlowy migration

Inventory actual AppFlowy stores and consumers, back up, export into staging, compare counts/content/attachments/links/tasks, report losses and unsupported database semantics, then obtain migration acceptance under the implementation scope. Cut over readers and installers only after verification. Preserve recoverable originals. Remove dependencies after a rollback window; never delete user data merely because an integration is retired.

### Task authority

Human task content lives in portable Markdown. uFlow owns scheduling, dependencies, execution state and receipts, referring to stable task IDs. Obsidian edits those records through a documented convention; indexes/views are rebuildable. Define reconciliation with the existing uFlow storage before moving files. Imported Apple reminders carry external IDs and initially have one-way capture semantics. Do not create competing hidden task databases.

## 7. Vault, import and edition contract

### Logical storage (proposed, map to current paths first)

| Area | Contents | Visibility/publication |
| --- | --- | --- |
| Originals | Byte-preserved source files and attachments | Regular filesystem; outside editor content root when possible; never directly published |
| Working vault | Converted Markdown, user edits, tasks and curated assets | Obsidian and uDos-readable; private by default |
| Binder records | Brief, requirements, sources, plan, decisions and review references | Inspectable project evidence; excluded from public output unless selected |
| Runtime state | Caches, indexes, jobs, connector cursors and receipts | UDOS_HOME under existing storage contract; not content authority |
| Edition staging | Explicitly selected, validated compiled output | Clean build directory; target-specific access policy |
| Library packages | Versioned content/manifests and permitted assets | Offline install/share; contribution changes reviewed |

Preserve `~/Vault`, `~/Shared`, `~/Public` and the current UDOS_HOME contract unless a separately reviewed migration is necessary. Never create new home-root state directories. Do not move credentials from OS/application-owned stores. Do not store originals or secrets in a publication repo or its Git history.

Open box / look under the hood: do not use `.local` or dot/hidden folders to conceal user-accessible data. Filesystem structures under `~/Code`, `~/Vault`, `~/Shared`, and `~/Public` remain completely transparent and inspectable in standard file managers and shell sessions. The uCore file browser excludes internal runtime files, lockfiles, and raw intake archives (`Originals/`) at the UI presentation layer, leaving them unhidden on disk. Maintain space transparency to educate users on disk consumption and avoid bloat; keep shared caches (e.g. `Code/Vendor/01-RAW`, Sonic Depot) explicitly visible; and enforce product-specific, gitignored Python virtual environments (`<repo>/.venv/`) rather than a fragile monolithic `.venv`.

### Intake pipeline

Receive → preserve/checksum original → extract → normalise → review → compile → publish.

Each intake records stable document ID, source URI/path reference, acquisition date, available author/publication date, source hash, converter/version/configuration, output hash, attachment relationships, extraction losses, privacy and redistribution status. Missing metadata is unknown, not invented.

Reuse Pandoc for supported structured document conversion, Docling for qualified extraction/OCR, Quartz for static Markdown sites and Kiwix through an adapter for selected ZIM collections. Download/pin required models and assets for offline operation. Support a small tested format matrix first: Markdown/text, HTML, DOCX and text PDF; add scanned PDF/OCR after quality gates. Spreadsheet extraction preserves originals and reports formula/layout loss. CSV is data, not a full spreadsheet replacement.

Updated source documents produce new candidate revisions. Use source identity and checksums to avoid duplicate intake. Preserve user edits and surface merge conflicts; do not regenerate the whole document over accepted work. Invalid/encrypted/unsupported inputs remain retained with an explicit result.

### Rendering and publishing format

Choose a documented Markdown subset and metadata schema. Keep standard links, headings, tables and task fallbacks readable. uDos styling is a renderer/template contract rather than destructive rewriting of source evidence. GridCore embeds are explicit extensions with static descriptions, user-initiated execution and qualified exported runtime assets.

Originals are not publishable directly. Approved derived illustrations and attachments enter a separate publishable asset list. The compiler starts empty and copies only approved inputs/dependencies, stripping private metadata and checking links. Exclusion by dot-folder convention is insufficient. Validate archive paths/symlinks, resource sizes and embedded active content on import.

### Community libraries

Create versioned editions with manifest, content hashes, schema version, provenance, licences, reader requirements and optional validated signatures. A signature proves publisher/integrity, not truth. Installed public editions are normally read-only; users annotate in their own vaults. Contributions are reviewable patches/packages against an edition. Preserve corrections, conflicting claims and stale-source warnings. Indexes and embeddings can be rebuilt from preserved documents.

## 8. Notebook production and anti-drift model

### Obsidian plus focused UI Hub surface

Obsidian owns everyday authoring. UI Hub's Notebook assembles and reviews durable document projects. Reuse existing Bangle editor/diff/research components after qualification; do not resume building a general-purpose editor platform. Both interfaces operate on the same files with revision-aware writes.

Views: Brief; Sources; Plan/Tasks; Draft; Review & Publish. Chat is a convenient input to this process, not the authoritative project record. A minimal later Obsidian integration may open the corresponding Hub review/project; do not require a custom plugin for the initial proof.

### Durable binder records

- Brief: outcome, audience, document type, non-goals, required sections, budget/deadline and completion criteria.
- Requirements: stable IDs and accepted wording; mapping to sections/checks.
- Sources: original/extracted references, dates, hashes, citations and trust/rights metadata.
- Plan: bounded tasks, dependencies, source selection, executor eligibility and output paths.
- Decisions: accepted decisions, rejected/superseded proposals and reasons.
- Draft: stable section IDs, accepted text and proposed revisions.
- Evidence: source/output/task linkage and review receipts.
- Editions: immutable approved snapshots and publication receipts.

Use readable Markdown and small open manifests as appropriate. Long-form inputs remain available; summaries point back to them. Do not cram all machine state into prose or turn every relationship into a custom file format.

uVector outputs are optional cited/labelled assets of a binder. Keep the distinction between extracted source graphics, generated illustration and verified data plots; a uniform style must not convert imagined details into evidence.

### Execution state machine

Draft brief → planned → authorised run → running → ready for review → accepted edition → published when authorised.

Blocked, cancelled and failed are explicit outcomes. Publication is distinct from acceptance. Implement checkpoints, bounded retries, idempotent side effects and restart reconciliation. Local scheduling is owned by uFlow and must work without an Antigravity session. The machine must be awake/powered or a separately configured local host must own the run; do not promise execution on a sleeping device.

An autonomous document run reads the approved brief, completes selected tasks, saves sources and outputs, assembles the draft, checks requirement coverage and stops ready for review. External research runs only where the plan allows connectivity. Publishing, sending or submitting requires target-specific authorization; a drafting instruction does not confer it. Standing authorization can be bounded and reused without repetitive approval prompts.

### Enforced guardrails

| Rule | Required behavior/evidence |
| --- | --- |
| Brief preservation | Original accepted brief survives summarisation and revisions |
| Scope control | New ideas enter backlog; scope changes recorded explicitly |
| Coverage | Each requirement links to output or a visible unresolved issue |
| Provenance | Material claims link to sources; inference/uncertainty labelled |
| Revision safety | Expected-hash/revision checks; concurrent edits reconcile, never overwrite blindly |
| Accepted text protection | Targeted changes; no blanket rewrite to fix a paragraph |
| Cost/resource control | Task/provider/network/time/token/resource ceilings and cancellation |
| Stop condition | Repeated no-progress/contradiction/budget exhaustion yields review or blocker |
| Truthful completion | Missing evidence remains missing; mock/local ledger is never a remote success |
| Tool authority | Imported documents cannot grant permissions or instruct trusted execution |
| Auditability | Show sources, diffs, outputs and decisions; do not promise private chain-of-thought |
| Privacy | Source classification carries into prompts, output staging and publication |

Prefer deterministic lint/coverage/schema checks where possible. A second model saying "looks good" is not sufficient verification. Final review tests factual support, requirement coverage, contradiction handling, formatting and provenance separately. Philosophical claims about AI consciousness or collective identity are excluded from this brief.

### Bulk document generation

Use versioned templates for proposals, applications, case studies and blueprints. Each job has isolated binder/context, selected shared sources and its own completion checks. Prevent cross-client/private-context leakage. Generate a sample and validate the template before bulk runs. Track partial success per document; rerun failed tasks without duplicating completed publications.

## 9. Review and publishing product

Repurpose the former Developer flow into Draft → Changes → Review → Edition → Publish. Retain diff/rollback/stale-source controls, remove arbitrary repo access. Source-code developer history is not user publication history. Git may power local history internally; signing in to GitHub is never required to edit or review locally.

| Target | Contract |
| --- | --- |
| Offline bundle/local static site | Complete permitted assets, local links and search; no CDN dependency |
| Local Portal | Same edition, with server-side access controls for restricted material |
| GitHub Pages | Public static document library; verified target and deployment receipt |
| Commercial hosting | Separate WordPress-backed product for managed publication/accounts/access |

GitHub Pages cannot host a PHP/WordPress runtime. Account/plan restrictions and service usage limits must be verified at delivery. Private source repositories do not imply private Pages sites. Do not promise revocation of already downloaded public content.

WordPress is a commercial service foundation, not a proprietary relicensing of upstream code. Review distribution/licensing of derived components, premium plugins and hosted/offline rights. Qualify the archived local WordPress workspace before adoption; avoid importing its entire cloud stack as a local prerequisite. Static publishing remains valid without WordPress.

Define compile/preview/publish/verify/rollback receipts with edition hash, target, external identifier and actual result. Idempotency and reconciliation precede retry after network interruption. First prove a local edition, then one GitHub target, then commercial service readiness independently. No invented domains, credentials or deployment claims.

## 10. Snackbar and Apple activity

Snackbar is separately installable. Installed products register explicit launch/capability entries; absent products remain hidden. Standalone users can open Obsidian/activity inbox and configure supported captures. No uCore daemon requirement for a basic launcher.

Use one action language: ID/version, inputs, required platform/tools, allowed effects/paths/network, schedule eligibility, timeout, retry/idempotency policy, outputs and removal procedure. Small local capture actions run under the minimal Snackbar executor. Durable multi-step projects delegate to uFlow when installed. Share contracts rather than creating another agent scheduler. Assess existing SnackMachine/lifecycle ownership before extraction.

### Capture scope

| Source | Initial direction | Limit |
| --- | --- | --- |
| Calendar/Reminders | EventKit permissioned one-way capture | Completion write-back is a later explicit capability |
| Mail | Qualified selected-account/folder adapter | Bound volume, attachments and privacy; capture is not sending |
| Notes | Supported export/Shortcut workflow | Qualify incremental IDs/updates; do not promise universal API |
| Messages | Research separately | No blanket access or private database scraping baseline |
| Notifications | Cooperating source integrations | No universal system notification harvesting promise |

Create stable event records and a generated Markdown activity view. Export machine-readable JSON Feed/JSONL and suitable calendar data where useful. Store external IDs, timestamps/time zones, source links, update/deletion state and privacy. Test duplicate capture, offline resumption, permission revocation and deletion handling. Separate annotations from generated fields so refresh cannot erase user notes.

Distinguish capture from transport: Snackbar reads data locally available to its authorised adapters; it does not replace Apple's cross-device synchronization. A chosen optional vault-sync transport distributes resulting files. Public sharing is never the default for private activity.

## 11. uCode, Sonic and Mint delivery

User coding is a beginner environment for BASIC, explicit uDos commands and small scripts/capsules. Define resource/time/filesystem/network permissions and static fallbacks. Imported capsules never autorun. Qualify retro title/runtime/content licences separately; availability of source does not confer redistribution rights.

Runtime dependencies install as verified versioned artifacts, not live sibling checkouts. Reuse compatible installed packages, resolve version conflicts explicitly, support offline bundles, verify integrity and record shared dependencies. Uninstall preserves packages still needed by another product and never removes user documents.

Sonic retains diagnostics, hardware-model records, qualified provisioning, device libraries and boot/toolkit roles. It consumes uCode/uKnowledge only as required. Keep read-only inspection, disk writes and firmware flashing separate gates. Exact device/firmware support, recovery and physical tests are required before advertising a write operation.

Classic Modern has two profiles: Cinnamon/full and Xfce/light. Pin the latest qualified Mint release and maintain one common profile specification with limited desktop differences. Test reversible install/uninstall, live USB versus installed OS, offline setup, sleep/wake, network, display/input/audio and recovery. Track PC x86-64, older Intel Mac and ARM support separately. No universal "old hardware" claim or Windows/macOS binary compatibility promise.

## 12. Portal, access and future networking

Treat Portal/Beacon as one reconciled product lane before choosing names/repositories. Separate local content hosting from network-equipment management and from public cloud publishing. HomeNest and Home Assistant remain independent consumers/integrations.

OpenWrt is a candidate for qualified routers/APs; Sonic handles explicit provisioning recipes. Router/firewall layers own network isolation. Portal/WordPress/reverse proxy own application content access. Public, household/shared and restricted content require clear asset/API policy; a UI label is not enforcement. Management interfaces stay separate from guest access.

Qualify multiple Wi-Fi node configuration, device/service discovery, authenticated shares, IoT/console integration, local DNS/discovery and intentionally enabled egress. Discovery does not imply private data access or control. Maintain a detected/identified/readable/controllable matrix by device/protocol.

First release proof: one host, one qualified router/AP, offline content, two access roles, WAN disconnected, and demonstrable isolation. Multi-node coordination follows. Do not expand to a network-security suite as a dependency of Markdown publishing.

MeshCore is future research for constrained messages, alerts and compact content announcements. Its messaging-first LoRa design is not a bulk-vault or ordinary web transport. Community-wide/global access needs actual connected infrastructure, bandwidth, operating permissions and maintenance. No promise of a free global replacement internet. Keep this research outside current release criteria.

### HomeNest and existing Home Assistant integration

Home Assistant is an existing upstream product; do not recreate it or rename the adapter as a replacement home automation platform. The intended optional user entry point is HomeNest's smart-TV/controller experience on the Steam/media server. Users should be able to discover/connect their existing HA instance and use qualified scenes, lights or other selected controls from the living-room interface.

Keep upstream HA authoritative for entities, automations, integrations and device state; its service may run elsewhere on the LAN. The uDos adapter owns connection, authentication and capability mapping. HomeNest owns the TV/controller presentation and media experience. Reuse an upstream-supported UI/API or a thin qualified integration before building a new dashboard. Exact embed versus native controller view is a pre-start design assessment, not a settled implementation.

HomeNest remains useful without HA; HA remains useful without HomeNest/uCore. Initial proof: invoke an explicitly selected scene or light from the TV/controller surface, show real state/errors and survive HA disconnection. Cross-product sequences such as a movie-night scene may use uFlow when installed; simple HA controls must not acquire a mandatory workflow-host dependency.

### uVector: unified illustrations as an independent product

uVector is a first-class image generation and standardisation product, not merely a deferred spatial experiment. Its purpose is to turn varied source/reference material into consistent, compact graphics for topic libraries: technical drawings, diagrams and scientific-style illustrations with a coherent visual language. It complements the currently text-focused uDos Prose presentation and GridCore's distinct graphics/runtime language; it does not replace either.

Standalone use: select a style profile and inputs/brief, generate or transform an illustration, review it, and export portable assets for any documentation or publishing tool. uDos integration inserts approved assets into a binder/edition. Model providers, vector/raster converters and publication adapters are optional declared capabilities. Qualify offline transforms separately from generation that may require a local model or explicitly selected cloud service.

Inventory existing generation, SVG/vector/raster conversion, styling, prompts, providers and UI work before deciding what is missing. Preserve working functionality. Define versioned profiles for typography, stroke, palette, background, labels, dimensions and output size; reuse established design tokens where suitable. Preserve editable source, generation/transform recipe, input provenance, model/tool versions and review status. Prefer vector output for suitable line art, with compact raster fallbacks and meaningful alt text/captions.

Do not silently stylise away technical meaning: labels, scale, dimensions, topology and numerical data need review. Scientific plots should come from verified data and deterministic plotting when precision matters; generated scientific-style illustrations are labelled illustrations, not measurement evidence. Keep original source/reference images outside publication unless separately approved and licensed. A style-normalisation step does not remove rights obligations.

First independent release slice is chosen from what already works: one coherent style profile, a qualified generation/transform path, reviewable output and portable export. Test acceptance in a standalone document and a compiled vault. Do not defer the entire product because later advanced generation or spatial ideas remain unfinished.

### Groovebox: standalone music production suite

Preserve Groovebox's suite identity, existing music workflows and independently versioned interchange. Assess its actual instruments, sequencing, pattern/project storage, playback, export and optional Songscribe integration; do not reduce it to a uDos widget. Choose a release-ready workflow from existing implementation and qualify save/reopen/play/export and dependency failure. uDos integration is optional discovery/interchange, not required to make music.

## 13. Google and provider adapters

Use Antigravity for external development; Gemini Notebook/NotebookLM for optional source-based research; Docs/Sheets for optional collaboration/import/export; Drive for optional explicit remote copies; Gemma through Ollama as a candidate local model.

Binder files remain canonical. Google exports return as provenance-bearing sources or proposed revisions. Notebook export is not assumed to be bidirectional synchronization. Verify supported APIs rather than designing around browser-only features or undocumented consumer endpoints. The local binder journey must work when Google adapters are removed.

Correct misleading readiness/success in existing Google scaffolding. A local mirror ledger must say locally recorded/pending upload; remote success requires verified external evidence. Do not replace a failed remote action with a successful mock. Preserve source privacy during provider selection. Qualify model/output quality on real BASIC and document tasks; downloaded weights/licence/hardware support form part of offline readiness.

## 14. Vendor closure and external research boundary

Inventory every Vendor item and actual consumers. For each record upstream URL, revision, licence/notices, modifications, dependencies, owner and disposition:

- Adopt: pinned package/API preferred; fork only for a concrete maintained patch.
- Reference archive: preserve unique research/provenance outside the product runtime.
- Remove: unused reproducible clone after confirming no unique work or active dependencies.

No deletion based solely on folder labels, age or duplicate filenames. Save disposition evidence and recovery references. Product builds must pass with Vendor absent. Product dependencies must never resolve through an absolute Vendor path.

After closure, new experiments live in a separate external development workspace. Do not create its directory or a new agent configuration tree merely to satisfy a diagram; decide location/owner/lifecycle when needed. Adoption into a product requires a tested, versioned, licensed boundary. Keep Home Assistant/Matter, Songscribe, retro fonts and specialised runtime consumers in scope for the assessment rather than deleting apparently unrelated clones.

## 15. Phased execution and gates

The order below is dependency guidance, not authorization for a single unlimited sweep. Gemini refines it after assessment. Each phase ends with a bounded reviewable result and recorded evidence. Independent products need not wait for unrelated releases.

These are workstreams, not a requirement that all products progress in a single serial queue. After P0/P1 establish the minimum shared contracts, move day-to-day work into the selected owning repository. Release the nearest qualified product first. Shared contracts evolve compatibly through explicit version changes; unfinished ecosystem lanes do not block an unrelated product release.

| Phase | Work | Exit evidence |
| --- | --- | --- |
| P0 Assess | Complete Section 4; reconcile all prior handovers | Assessment, missed lanes, revised sequence and ownership accepted for implementation |
| P1 Contracts | Lock document/task/action/edition/dependency boundaries; map migrations | Small schemas/examples, root/privacy/authority rules, no competing stores |
| P2 External development | Remove Dev UX and services safely; CLI/MCP docs; retarget diff primitives | No toggle/internal IDE/arbitrary-repo user route; direct endpoint negatives; diagnostics usable externally |
| P3 Obsidian/vault | Minimal profile, AppFlowy export/cutover, filesystem reader, initial converters | Existing content preserved, portable tasks, offline read/search/edit, loss reports and rollback |
| P4 Notebook | Brief/sources/plan/draft/review; one durable uFlow run | One complete document project with traceability, conflict protection, restart and bounded completion |
| P5 Publishing | Clean compiler, local edition, library package, GitHub adapter | Originals/private files absent; local offline result; separately verified remote target |
| P6 Snackbar | Standalone launcher/action runner and bounded Apple capture | Works without uCore; supported captures idempotent; absent products hidden |
| P7 Runtime/device | Qualified uCode artifact/capsule; Sonic dependency install; Mint profiles | Standalone packages, offline dependency install, hardware-specific evidence |
| P8 Portal/commercial | Local Portal proof then commercial WordPress hosting | Access/isolation/restore tests; independent hosting operations and licence qualification |
| P9 Closure | Vendor dispositions, documentation supersession, independent release catalogue | Builds without Vendor/sibling source; owners, artifacts, support matrix and unmet gates recorded |

Parallel *product tracks* (not an instruction to spawn agents): Groovebox music suite, uVector illustration tool, HomeNest media/TV with optional HA controls, and other assessment-qualified products each get a repository-owned release slice and gates. UI/feature preservation applies to every track. Coordinate shared-contract changes, but do not make these tracks wait for P8 or the complete notebook roadmap.

Cross-cutting Vendor audit begins in P0; adopted dependencies can move earlier, final deletions wait for proof. HomeNest/HA/Groovebox retain their own release tracks. Portal, commercial hosting and mesh research do not block the first notebook release.

### First complete milestone

On one qualified machine: import a small mixed-document collection; preserve originals; create a brief with explicit requirements; organise a binder; produce a coherent proposal through a bounded local run; edit concurrently and reconcile; inspect evidence for a disputed paragraph; accept a revision; compile a consistent offline site; transfer the edition to a disconnected second environment and read it there. No AppFlowy, Dev Mode, Antigravity runtime, Google account or frontier model is required for the offline stages.

## 16. Verification and release discipline

Use real fixtures with known expected outcomes, not tests that simply repeat implementation claims. Distinguish unit tests, integration tests, live external verification, VM qualification and physical-device evidence.

- Cold start with WAN blocked, no model running, no cached login; core documents/tasks/search/export still work.
- Fresh install from prepared artifacts; dependencies/models/fonts available offline; graceful unavailable capability reporting.
- Markdown round-trip preserves content/metadata/links; conversion reports expected losses; originals retain exact hashes.
- Delete caches/indexes and rebuild without losing authoritative content or project evidence.
- Concurrent Obsidian/Hub/agent edits fail stale writes safely; interrupted runs recover without duplicate effects.
- Imported instructions/capsules cannot execute or expand filesystem/network/provider authority.
- Publication staging rejects originals, secrets, private metadata, unexpected symlinks and unapproved assets.
- Google/hosting disconnected or denied: no fabricated success; retries reconcile real effects.
- Task completion and deletion semantics tested across imported records and local edits.
- Snackbar independently starts/stops and revokes permissions cleanly; uCore absence is supported.
- Sonic package install resolves shared dependencies and uninstalls safely; physical writes remain qualified separately.
- Portal access controls protect content/assets/API and guest network boundaries with WAN absent.
- Linux profiles get actual hardware/VM results and explicit untested fields.
- Required repository checks run for affected files. Path changes include uCore's `scripts/check_home_path_policy.py` under the workspace contract.

Release artifacts need version, source revision, dependency manifest, licences, integrity checks, install/update/remove/rollback guidance, supported platforms, resource expectations and known limits. Signing/channel ownership is a pre-release decision, not a fake placeholder implementation. Routine development tests do not certify a production release. Preserve independently owned uncommitted work and never force-reset a checkout to simplify migration.

## 17. Known source evidence and uncertainty

Read-only inspection during planning found the following; Gemini must verify again:

- uKnowledge's `uknowledge/library.py` is filesystem-first with no uCore/AppFlowy/model dependency; its README is stale.
- uFlow's `uflow/routes.py` still imports `app.api.tasker_api`, demonstrating incomplete host independence.
- uCode/GridCore and renderer have package boundaries; manifest versions alone do not prove published releases.
- uCore has Bangle/editor/diff/research components worth qualifying before reuse.
- `udos-google/udos_google/src/service.py` has a `drive_sync` path reporting success for local ledger creation rather than upload.
- SnackMachine documentation places Snackbar/Popcorn in uCore; extraction is real work.
- `udos-vaults` documents AppFlowy scaffolding and a stale uDev path.
- Archived WordPress code contains useful publishing intent plus cloud-specific assumptions; portal shell/theme documentation is scaffold-level.
- HomeNest/HA/Sonic have recent, separate handovers and intentional uncommitted work. Their assessments and test counts are historical until rerun.
- Several extensions have placeholder documentation. Inspect implementation rather than inferring readiness or uselessness.

No full runtime suite, physical-device qualification or live Google/hosting integration was performed to prepare this plan.

## 18. Primary references and install entry points

Links reviewed during planning; Gemini must recheck versions, links and terms before installation/release.

- [Antigravity downloads: desktop, IDE, CLI and SDK](https://antigravity.google/download)
- [Antigravity product overview](https://antigravity.google/docs/home)
- [Antigravity MCP integration](https://antigravity.google/docs/mcp)
- [Obsidian download](https://obsidian.md/download)
- [Obsidian Bases](https://help.obsidian.md/bases)
- [Obsidian commercial-use announcement](https://obsidian.md/blog/free-for-work/)
- [Tasks plugin guide](https://publish.obsidian.md/tasks/Introduction)
- [Copilot local/offline guidance](https://docs.obsidiancopilot.com/troubleshooting-and-faq/)
- [Pandoc](https://pandoc.org/)
- [Docling](https://docling-project.github.io/docling/)
- [Quartz](https://quartz.jzhao.xyz/)
- [Kiwix](https://kiwix.org/en/)
- [Google notebook source support and limits](https://support.google.com/gemininotebook/answer/16215270?hl=en)
- [Google notebook export behavior](https://support.google.com/gemininotebook/answer/16262519?hl=en)
- [Google Docs Markdown import/export](https://support.google.com/docs/answer/12014036?hl=en)
- [Gemma with Ollama](https://ai.google.dev/gemma/docs/integrations/ollama)
- [Apple EventKit access](https://developer.apple.com/documentation/eventkit/accessing-the-event-store)
- [Apple User Notifications](https://developer.apple.com/Documentation/usernotifications/)
- [Linux Mint editions](https://linuxmint-installation-guide.readthedocs.io/en/latest/choose.html)
- [OpenWrt guest networking](https://openwrt.org/docs/guide-user/network/wifi/guestwifi/guest-wlan)
- [MeshCore FAQ](https://docs.meshcore.io/faq/)
- [GitHub Pages limits](https://docs.github.com/en/enterprise-cloud%40latest/pages/getting-started-with-github-pages/github-pages-limits)
- [WordPress licence](https://wordpress.org/about/license/)

## 19. Definition of refactor completion

The refactor is complete only when the selected release scope has: no internal developer runtime/journey; a qualified external maintenance bridge; Obsidian baseline with safe AppFlowy retirement; portable vault/import/edition contracts; one evidence-preserving notebook production journey; independent Snackbar and runtime boundaries; verified publication paths; dispositioned Vendor dependencies; consistent current documentation; and product-specific release evidence.

A phase or product can release independently while later lanes remain planned. Final reporting must list delivered products, actual artifacts/tests, deferred lanes, unresolved hardware/service gates and rollback material. Do not label the entire ecosystem complete because the first notebook demonstration passes.

### Repository-by-repository operating model

The broad Code-folder assessment is a bounded transition activity. Afterwards each product repository owns its own README/product promise, current handover, bounded backlog/release plan, dependency manifest/lockfiles, build/test/package commands, user examples, support matrix, changelog and install/update/remove instructions. Do not recreate a workspace-wide mega-backlog as the daily execution authority.

Develop and qualify from the product's repository directory. CI must be able to build/test/package from that repository plus declared versioned dependencies, without arbitrary sibling source imports, a global editable environment or Vendor. If an artifact depends on shared uDos packages, consume their release contracts; a standalone product may still have explicit dependencies.

For each release record: practical standalone user journey; retained/moved feature inventory; UI baseline/regressions; source revision and artifact; clean-install evidence; data compatibility/rollback; optional integration behavior; unresolved scope. Release one product, learn from it, then continue with the next. No wholesale rewrite or ninth rebuild is part of this plan.
