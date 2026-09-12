> Archived 12 September 2026. Historical implementation evidence only; Dev Mode/internal IDE delivery direction is superseded. Start with the [current Gemini handover](../../HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md). Relative Markdown links below were rebased; prose and recorded claims are preserved, not recertified.

# Local-first execution lanes — implementation brief

Date: 2026-09-08
Status: User-directed boundary; implementation proposal for review, not enforced yet
Owners: uCore policy/service host; uFlow workflow authority; uCode runtime and capsule authority

## Decision

Normal uDOS operation must work without paid AI or a cloud model account. Use tested
Skills and Snacks first; use locally hosted Ollama inference when interpretation,
drafting, classification or explanation adds value. Cloud models, including free
cloud tiers, are restricted to explicitly scoped Developer work. Enabling Dev Mode
makes cloud execution eligible; it does not turn every task into a cloud task.

A task's model permission, network permission and write permission are separate.
A zero-dollar cloud model is still remote inference. A Google Drive sync is service
access, not permission to send documents to Gemini. A local model can still propose
unsafe or incorrect actions; execution remains governed by validated code.

BrowserUI/research may fetch web sources outside Dev Mode and synthesize them with
Ollama. This brief interprets the research exception as web/service access, not an
exception to the premium-model rule. Paid search/data services are also denied in
normal use under the proposed strict premium-API boundary. If paid research outside
Dev Mode is intended, that requires an explicit amendment before implementation.

## Lanes behind one interface

These are execution policies, not new chats, agent selectors or permanent tabs.
Keep one global User/Developer chat and Ask / Plan / Act. Routine routing is automatic.

| Work | Default executor | Network boundary | Cloud/premium AI |
| --- | --- | --- | --- |
| Everyday User chat and tasks | Skill; Ollama for language work | Offline unless a named integration is needed | Denied |
| Markdown, metadata, Binder management and exports | Parsers/templates/formatters; Ollama drafts | Local files; explicit Snack sync only | Denied |
| uCode BASIC programs and capsule packaging | GridSmith with local Ollama, existing uCode validator/runtime/packager | Offline after approved dependencies are provisioned | Denied |
| USX application and consistency repairs | Tokens, components, lint rules and deterministic transforms; Ollama selects bounded changes | Local; approved Git transport separately | Denied for routine styling |
| Git maintenance and automation | Git/CLI, linters, tests, build scripts; optional Ollama summaries | Named GitHub repository through integration | Denied for routine operations |
| Connected Snacks | Supported OS/app/service adapter | Only its declared service and user-selected data | No model access inherited from service access |
| BrowserUI/research | Browser/fetch/parser/indexer; Ollama extraction and synthesis | Web access with provenance and bounded fetches | Denied outside Developer scope |
| Backend, extension and novel infrastructure development | Existing Developer workbench; local first | Scoped repository, package and research access | Eligible with Dev Mode, task authorization and budget |

USX source edits still require Developer write authority when they modify core
repositories. Their inference policy stays local-only. User theme preferences only
change approved settings. Similarly, writing a BASIC program in a user workspace is
normal use; changing the BASIC runtime/compiler or installing a new executable
extension is development. Complexity alone must not silently promote either task.

## Predictability contract

The [ecosystem execution contract](../../ECOSYSTEM_EXECUTION_CONTRACT_2026-09-08.md)
defines the required harness, USX recipe constraints, publishing promotion flow,
Action permissions and Developer-to-normal release gates. Skills alone are not
enforcement; routine models select approved operations rather than invent tooling.


Ollama translates a request into a typed, bounded action or proposes an artifact.
A versioned Skill validates it and executes approved operations. Snacks adapt those
operations to the host or a connected service. An Action is a named invocation of
that contract; a workflow composes Actions through uFlow. Do not introduce another
scheduler, agent framework, registry or task store for these lanes.

Prefer Python orchestration for Skills, but retain working JS/native parsers and
existing CLIs behind thin wrappers. Rewriting markdown-it, Git, a BASIC runtime or a
platform integration in Python would contradict the reuse contract.

For every retained capability, extend the existing catalogue with:

- Stable ID/version, authority, maintainer, lifecycle and removal/migration path.
- Input/output schemas, prerequisites, supported platforms and allowed roots.
- Required effect permissions: read, write, delete, send, sync, install or publish.
- Model policy (`none`, local inference, Developer cloud eligible), network policy
  (offline, named connector, research web, Developer dependencies), data scope.
- Bounded timeout, retries, concurrency, CPU/RAM/GPU use and output size.
- Preflight, preview/diff when relevant, revision/conflict checks, idempotency and
  recovery behavior; distinguish an undoable local write from an external send.
- Fixture tests, postconditions and a structured execution receipt with real
  outputs, changes, model/version where used, cost and errors. Redact credentials.

Pin tool, schema and template versions. Do not regenerate helper scripts on each
run. A new or changed Skill/Snack is code development: propose, review, test and
admit it before reuse. Ollama cannot approve its own generated executable code.

Structured model output helps enforce shape, not semantic correctness or identical
prose. Repeatability comes from deterministic executors, fixtures and invariants;
cache approved generated artifacts when exact replay is needed. See
[Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

## Enforcement and budgets

Enforce policy on the server at dispatch and again at side-effect/provider entry
points, including REST, MCP, scheduled jobs, CLI bridges, retries and nested agents.
Do not trust a chat message, tool argument or frontend mode switch as authorization.
Pass an authenticated task scope and immutable policy decision through delegation.
Child work can narrow permissions but cannot elevate them. Resolve the effective
execution destination: an Ollama-compatible endpoint or model name does not prove
inference is local. Approved local/LAN hosts must actually serve local models;
Ollama Cloud and cloud proxies remain cloud execution.

Evaluate lane and data permissions before checking money. User tasks have a hard
zero premium-API/model allowance; a large global budget or free-tier fallback must
not override it. Developer cloud work needs a named provider, bounded context,
per-task reservation/ceiling and shared daily/monthly caps. Reconcile estimated and
actual spend, retries, tool calls and concurrent jobs atomically. Unknown price or
missing enforcement means no automatic paid dispatch. Exhaustion stops or returns
to an allowed local executor; it never silently moves to another cloud provider.

Local execution still has a resource budget: queue work, bound context and retries,
cap parallel models, and respect foreground responsiveness. If Ollama is offline,
continue model-free actions and queue/fail language work clearly. Never substitute
cloud inference. Downloads, initial model provisioning and updates are separate
network actions, not proof that ordinary operation requires connectivity.

Switching Dev Mode off prevents new cloud dispatches; already-issued requests may
still complete and incur charges. Persist scope and spend across restart, and
revalidate queued/retried work before resuming. Regular User tasks stay local even
while Developer work is running in the same UI.

## Skills and Snacks to develop or reconcile first

| Capability family | Predictable core | Ollama role |
| --- | --- | --- |
| Markdown/Binder | Frontmatter schemas, links, headings, rename/move, deduplication, export, index | Drafting, tags, summaries and query interpretation |
| uCode/capsules | Versioned grammar/examples, parse/compile/run checks, manifests, dependency allowlist, packaging/checksums | Generate BASIC against the supported dialect and bounded repair feedback |
| USX | Canonical component recipes, token replacement, lint/format, accessibility and light/dark visual checks | Classify requested change and select approved recipe |
| Vault/search | Local file inventory, full-text index, incremental updates, provenance and backup | Local embeddings where supported, semantic retrieval, summaries |
| Tasks/calendar | uFlow state transitions, dates, recurrence, validation, exports | Extract task intent and suggest scheduling |
| Git/CI | Diff/status, lint, tests, build, docs links, version/package checks, release manifests | Optional changelog, issue triage and failure explanation |
| Host productivity | Clipboard, notifications, dictation/voice adapters, app launch, file conversion | Language interpretation where native deterministic tools are insufficient |
| Connected services | iCloud-backed folders, Drive, supported Mail/Notes/Reminders adapters, sync/conflict handling | Local processing of explicitly retrieved content |
| Research | Fetch/cache, source metadata, citation checks, extract/index, export | Local synthesis with cited evidence and uncertainty |
| Maintenance | Health probes, rotation, backups, verified restore, dependency inventory | Explain faults; no unrestricted self-repair or automatic cloud escalation |

All are candidates for zero cloud-model spend. Media/OCR/transcription can also
stay local when a suitable installed native or reviewed local tool exists; lack of
one is an availability gap, not an automatic paid fallback. High-fidelity remote
image generation (including Banana/Imagen), Gemini synthesis/sandbox execution,
cloud embeddings/reranking, Apple Intelligence Shortcuts with unknown processing
location and remote agent review must be classified explicitly. Surface names do
not grant exceptions. Keep only permitted local alternatives in normal use.

For capsules, distinguish reproducible package construction from generative source:
normalize timestamps and ordering for reproducible hashes; preserve the actual
BASIC dialect/runtime, manifest and dependency rules owned by uCode. Do not assert
that all BASIC programs are easy or correct because the language is small.

## GitHub Actions and connected services

Most CI should use no model at all. Existing GitHub-hosted lint/test/build jobs may
remain: cloud compute is not a premium AI call, although Actions minutes/storage
have a separate infrastructure cost. Use local Ollama only for optional language
steps. Git transport and publication still require their own authorization.

A hosted GitHub runner cannot reach the Mac's loopback Ollama service. Do not expose
that service publicly to solve this. A future isolated trusted runner or controlled
job-pull adapter can run local AI, but it must not execute untrusted PR code with
personal-machine credentials. Choose the integration only after runner isolation,
repository trust and operating costs are defined. GitHub explicitly cautions
against self-hosted runners for public repositories:
[GitHub secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).

Snacks are the supported bridge from local work to connected services, not a way
around egress or model policy. Declare direction, destination, authoritative source,
selected content, credential owner, consent, conflict handling and offline queue.
Prefer the OS's sync client and supported APIs over rebuilding sync engines. Cache
locally where appropriate and visibly distinguish cached, queued, synced and failed.
Service subscriptions, storage and infrastructure bills are separate from AI spend;
normal use must not silently buy capacity or invoke a metered premium API.

## Current evidence and gaps

This is a source inventory, not a full certification of the existing backend.

- `backend/app/skills/base.py`, `registry.py` and `catalogue.json` already provide
  Python Skills and catalogue ownership/lifecycle metadata. Extend them rather than
  creating a parallel catalogue; current metadata is not the complete contract above.
- `backend/app/menu/system_snacks.py` already wraps native apps, Shortcuts and a JS
  Markdown tool. Audit real behavior, consent, its Apple Intelligence path and the
  legacy spool default; migrate mutable state to UDOS_HOME through existing policy.
- `backend/app/services/gridsmith_bridge.py` delegates to uCode's GridSmith CLI.
  Trace its model selection and capsule validation inside uCode before certification.
- `backend/app/services/provider_router.py` registers Ollama, OpenRouter and a free
  cloud provider, and supports default-provider fallback. None may bypass task lanes.
- `backend/app/services/budget_manager.py` has existing spend accounting. Reconcile
  the previously recorded Budget plugin/shared-manager split before claiming a
  single gate covers every entry point.
- `.github/workflows/ci.yml` uses GitHub-hosted runners. Preserve deterministic CI;
  do not confuse this with a requirement for cloud agents.
- Hivemind, Roundtable, agent factories, recurring jobs, direct SDK calls, extensions
  and MCP tools need an egress inventory. All orchestration inherits the task's lane.

## Proposed Sprint 4 delivery sequence

1. Inventory every provider/network/side-effect path and classify existing Skills,
   Snacks and integrations. Reconcile ownership with uFlow/uCode/uDocs. Record
   retained, repair, replace or retire, with measured capability evidence.
2. Implement and test the server-side lane gate before adding more paid providers.
   Prove User scope cannot reach cloud through aliases, free tiers, tools, child
   agents, direct APIs, retries, background jobs or a global Dev Mode toggle.
3. Complete three reusable local slices: Markdown/Binder, BASIC-to-capsule, and USX
   consistency. Each must run through existing authorities and pass fixture-based
   checks; model-free substeps must work with Ollama stopped.
4. Prove one connected Snack (choose after native intake) and BrowserUI web capture
   with local synthesis, source provenance and zero paid-model calls.
5. Reconcile Developer cloud budget reservations, audit receipts and restart/cancel
   behavior; verify optional Git automation remains model-free/local by default.

Acceptance: disconnect WAN for core local journeys; inspect outbound calls with
WAN available; inject forbidden provider requests; exhaust budgets; repeat actions;
change file revisions; stop/restart services; test malformed model output and
untrusted retrieved content. Assert no unauthorized writes, duplicate sends or
cloud fallback. USX passes token/layout/theme/accessibility checks; capsules pass
uCode validation and reproducible packaging. Record macOS evidence and Linux gaps
separately. No new user-facing lane selector is required.

This brief prioritizes Sprint 4 scope review; it does not start implementation or
claim all five slices fit the timebox. Retain incomplete work in uFlow, not a new
list of executable task records here. No runtime, provider, permission or budget
configuration is changed by this document.
