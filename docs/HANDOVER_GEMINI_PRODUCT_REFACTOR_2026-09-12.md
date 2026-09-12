# Gemini / Antigravity handover: uDos product refactor

Date: 12 September 2026  
Status: planning handover; pre-start assessment required before implementation  
Workspace: `/Users/fredbook/Code`  
Primary plan: [uDos product refactor plan](UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md)

## Start here

You are receiving a planning brief, not a completed refactor. The user has chosen Gemini/Antigravity for the actual implementation. First assess this plan, reread the current Code folder, and recommend improvements, refinements, missing product lanes and a safe execution sequence. Do not start runtime changes while doing this assessment. If a subsequent user instruction already authorizes implementation after assessment, follow that scope; otherwise present the assessment and await implementation authorization.

The user does not need to re-decide the agreed principles. Resolve ordinary technical refinements through evidence; call out changes to product scope explicitly. Do not use this handover to justify an unlimited cross-repository rewrite.

Latest clarification: preserve valuable features and the emerging UI look/behavior. This is productisation of existing near-release work, not another rebuild. Most extensions may be standalone products with practical uses outside uDos. Perform the broad inventory once, then work and release from individual repository directories. Do not make the whole ecosystem a prerequisite for releasing one product.

## Mandatory opening sequence

1. Read `/Users/fredbook/Code/AGENTS.md` and applicable repository/nested instructions.
2. Read the complete primary plan, especially Sections 2–4, 15–17 and 19.
3. Re-inventory all of `/Users/fredbook/Code`, including hidden state/dependency directories, active products, Vendor and ARCHIVED. Inspect actual code/manifests/tests, not just descriptions.
4. Capture each affected repository's branch, revision, remotes and dirty/untracked state. Preserve all existing work. Never assume this directory matches GitHub or a historical handover.
5. Read the recent Sonic/HomeNest/HA handovers and relevant older uCore/editor/publishing contracts. Reconcile conflicts with the new product direction.
6. Trace actual dependencies, persistence, routing, capability checks, lifecycle, credentials and external effects.
7. Recheck upstream tools, installation links, compatibility and licences using official sources. Distinguish availability from qualified integration.
8. Produce and present the pre-start assessment described below before runtime implementation.

## Required first response / assessment

Deliver an evidence-based assessment containing:

- Current repo/lane inventory, revisions and uncommitted work requiring preservation.
- Implemented versus scaffolded, mocked, untested, historical and absent capabilities.
- Existing code that can be reused, and hidden coupling that changes the migration sequence.
- Feature/surface preservation map: retained, moved to a named product, optional integration or explicitly authorised retirement; baseline existing UI rather than redesigning it.
- Explicitly missed or underdeveloped lanes: HomeNest, HA/Matter, Groovebox, uVector, uCode2, identity, budget, agents, Dreamscape, docs/branding, Portal/Beacon and hosting.
- Improvements/refinements to this plan, each with evidence, benefit, cost and scope impact.
- Conflicts with existing instructions/roadmaps and a proposed supersession/migration list.
- Ownership map for documents, tasks, automation, installation, identity, publishing and network access.
- Data/privacy/licensing/hardware blockers and how to progress without inventing support or credentials.
- Smallest useful release milestone, ordered phases and concrete acceptance checks.
- A recommendation: proceed as written, proceed with listed refinements, or revise identified portions first.
- A readiness-based repository release order, including products able to ship before the notebook track. Each repository must have its own practical user outcome, commands, dependencies and release gates.

Do not simply paraphrase the plan. Challenge assumptions where the current code or upstream capabilities justify it. Do not reintroduce a general internal IDE or alternative default editor under the label of refinement.

## Decisions to preserve

- uCore/uDos is no longer a development environment. Remove Dev Mode, included IDE/dev tools and arbitrary-repository user journeys.
- Maintenance is external CLI/MCP and Antigravity-readable documentation, not uCore maintenance panels. Preserve necessary user error/connection/permission controls.
- The Git-like review flow is repurposed for vault/document/library/site publishing, with strict content-root boundaries.
- UI Hub contains advanced developer documentation and Antigravity product/install links. BASIC/uDos scripting remains a beginner user capability.
- Obsidian is the default editor. Tasks is the baseline task plugin; Copilot/Ollama is optional quick chat. Remove AppFlowy only after verified export/cutover and rollback preparation.
- UI Hub Notebook uses existing qualified editor/diff components for brief/sources/plan/draft/review. Durable execution has one owner, uFlow. No duplicate full editor or agent scheduler.
- Every document has durable Markdown; originals are preserved outside ordinary editor/publication content. Publish only validated derived editions and selected assets.
- Snackbar is standalone, hides absent products and supports bounded Apple activity capture into portable records. No universal Messages/notification capture promise.
- uCode/GridCore, Sonic, HomeNest, HA and Groovebox release independently. Dependencies install as versioned artifacts, including offline bundles, rather than sibling source checkouts.
- Groovebox is a standalone music production suite, not a widget. Preserve its existing feature scope and choose a qualified practical music workflow for release.
- uVector is a standalone image generation/standardisation product: unified technical drawings, diagrams and scientific-style illustrations for compact published libraries and external documents. Preserve generation/conversion/style work; do not classify the whole product as deferred spatial research.
- Home Assistant is an existing upstream product. The optional HomeNest smart-TV/controller integration should let users control selected home entities/scenes through the adapter; HA owns device/automation state and HomeNest owns TV presentation. Neither requires the other or uCore to remain independently useful.
- Classic Modern has Cinnamon and Xfce profiles on qualified upstream Mint releases.
- Portal/Beacon is a separate lane. Router security and application content access remain distinct. MeshCore is later research, not a release dependency or global-web promise.
- Google services are optional around local authority. A cloud research notebook is not the canonical binder format.
- Offline/static publication is baseline; GitHub Pages is the public static option; commercial WordPress hosting is independently qualified.
- Vendor is dispositioned into adopted dependencies, reference archives and removable unused clones; future experiments stay in external development.
- Preserve current useful UI surfaces/design and reassign features before removal. Only the explicitly agreed internal developer/AppFlowy retirements are settled removals; other features need an explicit disposition.
- Enforce brief preservation, coverage, provenance, bounded iterations, revision safety, truthful completion and separate publication authority. Exclude philosophical AI material.

## Prior handovers and source entry points

Read these as evidence, subject to current inspection and the supersession rule:

- [September 9 Gemini handover](HANDOVER_GEMINI_ANTIGRAVITY_2026-09-09.md): internal-IDE expansion priorities are superseded. Preserve useful controls/test evidence, not its next-sprint direction.
- [Superseded development archive](archive/superseded-development-2026-09-12/README.md): archive inventory, replacement links and preservation policy. Original entry points carry redirects so old links cannot silently resume obsolete work.
- [Sonic/HomeNest/HA session index](REVIVAL-SESSION-HANDOVER-2026-09.md): preserve independent revival work and reconcile shared ownership.
- [Sonic handover](../../SonicScrewdriver/docs/GEMINI-HANDOVER.md)
- [HomeNest handover](../../HomeNest/docs/GEMINI-HANDOVER.md)
- [Home Assistant handover](../../udos-home-assistant/docs/GEMINI-HANDOVER.md)
- [Sonic reuse assessment](../../SonicScrewdriver/docs/REUSE-AND-UPSTREAM-2026-09.md)
- [uCore current README](../README.md), [surface ownership](SURFACE_OWNERSHIP.md), [Developer surface](DEVELOPER_SURFACE.md)
- [Bangle guide](BANGLE_EDITOR_USER_GUIDE.md): verify every retained capability against implementation.
- [uKnowledge reader](../../uKnowledge/uknowledge/library.py), [routes](../../uKnowledge/uknowledge/routes.py)
- [uFlow routes](../../uFlow/uflow/routes.py): inspect host imports and task authority.
- [uCode README](../../uCode/README.md), package manifests and runtime/capsule tests.
- [SnackMachine README](../../SnackMachine/README.md), uCore menu/snackbar services and lifecycle contracts.
- [udos-vaults README](../../udos-vaults/README.md), AppFlowy installers/plugins and actual data consumers.
- [Google service](../../udos-google/udos_google/src/service.py), [publishing extension](../../udos-publishing/README.md)
- [Archived WordPress workspace](../../ARCHIVED/wpmudev-agent/README.md): archived source is not a release-certified local portal.
- [Vendor policy](../../Vendor/README.md), [manifest](../../Vendor/VENDOR_MANIFEST.yaml), audit indexes and consumer paths.

These are starting points, not an exhaustive inventory. Inspect files added since preparation and locate moved references rather than assuming absence.

## Working-tree warning

At preparation, uCore already contained unrelated changes in:

- `frontend-vue/src/router/index.ts`
- `frontend-vue/src/stores/extensions.ts`
- `frontend-vue/src/surfaces/dashboard/DashboardSurface.vue`
- untracked `docs/REVIVAL-SESSION-HANDOVER-2026-09.md`
- untracked `frontend-vue/src/surfaces/homeassistant/`
- untracked `frontend-vue/src/surfaces/homenest/`

This is a time-bound observation, not a complete inventory of other repositories. The two new plan/handover documents are also local planning artifacts until deliberately committed/transferred. No commit, push, deployment, installation or message to Gemini was performed during preparation. Preserve current work and reconcile with the active author before overlapping edits.

## Execution discipline after authorization

Use the primary plan's phase gates. Refine the order with actual dependency evidence. Keep changes reviewable and reversible; do not mechanically split repositories or copy daemons to achieve a diagram. Update current contracts and add clear supersession notices as part of the authorised implementation, while retaining historical evidence.

Record concrete command/API/schema names only after checking existing implementations. No stub success, guessed remote IDs, invented tests, silent migrations, automatic source deletion or universal hardware claims. Verify meaningful positive and negative journeys. Use existing CI and required path-policy checks for affected changes.

Preserve local/source/credential storage boundaries. Metadata and hashes are generally sufficient for inventory; do not dump secrets or private vault contents into the handover. Plans and run records should link to authoritative files rather than duplicate divergent backlogs. A phase can finish while another product remains explicitly deferred.

The core notebook track's first complete outcome is the primary plan's offline document-production journey: sources + accepted brief → traceable coherent draft → reviewed edition → local published library readable on a disconnected second environment. Core stages must not require AppFlowy, Dev Mode, an active Antigravity session, a Google login or frontier inference. This does not block earlier independent releases of Groovebox, uVector, HomeNest or another qualified product. After the pre-start assessment, conduct ordinary implementation in the owning repository and release products one by one.

## Suggested opening prompt for Gemini

> Read `/Users/fredbook/Code/uCore/docs/HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md` and the complete linked product refactor plan. Start with assessment only. Reread the current contents of `/Users/fredbook/Code`, applicable instructions, manifests, code, tests and existing handovers; preserve all uncommitted work. Identify improvements, refinements, hidden dependencies and any missed product lanes. Present an evidence-based assessment and recommended phased execution sequence before runtime changes. The September 9 internal-IDE expansion direction is superseded: Antigravity owns external development; Obsidian is the default editor; uDos focuses on offline-first documents, BASIC/capsules, review and publishing. Do not implement, install, delete, migrate or publish during this assessment.

> Preserve existing features and UI identity: this is separation and completion, not another rebuild. Treat Groovebox as a music production suite, uVector as a first-class image generation/standardisation tool, and HomeNest as an optional TV/controller entry point into existing Home Assistant. Propose a readiness-based release order, then shift execution to each product's repository. Do not require all of uDos to be complete before releasing practical standalone products.
