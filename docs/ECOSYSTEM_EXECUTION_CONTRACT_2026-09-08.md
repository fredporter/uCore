# Ecosystem execution contract: Skills, harness and release gates

Date: 2026-09-08
Status: Proposed enforcement design for review; no runtime changes in this update
Parent: [Local-first execution lanes](LOCAL_FIRST_EXECUTION_LANES_BRIEF_2026-09-08.md)
Scope: USX surfaces, publishing, Actions, Skills, Snacks, uCode and agent execution

## Core rule

Models may interpret intent and propose changes. Versioned code determines what
can execute and what qualifies as complete. A Skill document is guidance, not a
security boundary. A Python Skill is executable code, not automatically a safe or
repeatable operation. Both require validation and constrained execution.

Routine USX work must select approved layouts, components and token values rather
than author arbitrary CSS or invent interactions. Publishing must deliver a verified
artifact, not improvise a deployment. Routine Actions must invoke tested operations,
not generate shell commands. These rules apply to Ollama as well as frontier models.

## What recent agent work teaches us

1. **Skills package reusable knowledge and code.** Agent Skills use instructions,
   resources and executable helpers with progressive loading. That improves reuse
   and context efficiency; it does not make the instructions mandatory or certify
   the bundled code. uDOS should reuse the packaging concept while retaining its
   Python capability registry as the execution authority.
   [Anthropic Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).
2. **Measure the result separately from generating it.** Anthropic's March 24,
   2026 harness report describes explicit criteria, browser-based evaluation and
   separating generation from evaluation. It also reports evaluator weaknesses,
   cost and growing complexity. Its creative frontend experiment rewards
   originality; USX should instead grade conformity to approved design contracts.
   This is a design inference for uDOS, not evidence that the reported harness
   guarantees correctness or that we need more agents.
   [Harness design report](https://www.anthropic.com/engineering/harness-design-long-running-apps).
3. **Constrain model output, then validate its meaning.** Ollama supports JSON
   schema structured output. Use it for a typed action proposal or a layout recipe
   selection. Valid JSON does not prove that a path, publication destination or
   layout is appropriate. Low temperature is a tuning choice, not a reproducibility
   guarantee.
   [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).
4. **Separate infrastructure from model reasoning.** A session log, execution loop
   and sandbox have different responsibilities. Reuse this separation in existing
   uCore/uFlow infrastructure; do not import a cloud platform or agent fleet merely
   to reproduce it.
   [Managed-agent architecture](https://www.anthropic.com/engineering/managed-agents).

## Minimum enforcement stack

| Layer | Responsibility | What it cannot substitute for |
| --- | --- | --- |
| Skill guide | Explain intent, examples and when to use an existing capability | Authorization or enforcement |
| Typed contract | Validate inputs, allowed recipe IDs, versions, targets and expected effects | Semantic tests and permissions |
| Policy gate | Authorize lane, provider, data, network, writes and spending | A frontend switch or model's assurance |
| Executor/harness | Run a pinned Skill/Action through allowed tools, bounded time and durable state | Unrestricted generated scripts |
| Independent checks | Verify artifacts, UI behavior, changes and external results | The generator claiming success |
| Release record | Bind approved version, tests, permissions and provenance for reuse | Automatically trusting newly downloaded code |

The harness is the existing execution machinery around the model, not another user
surface. Extend uCore's dispatch/registry and uFlow's workflow state. Use OS process,
filesystem and network boundaries where a trusted runtime alone cannot contain code.
Do not assume JSON/MCP itself constrains a tool: it is a transport/interface contract.

## USX as a constrained composition system

Use the existing `packages/usx-tokens`, shared Vue components and frontend tooling.
Reconcile their ownership before publishing a versioned recipe catalogue. The
`frontend-vue/src/skills` component directory is a UI hierarchy, distinct from the
backend's executable Python Skills and agent-facing Skill guides.

An approved surface recipe specifies:

- Shell and navigation placement; permitted sections, ordering and nesting.
- Layout semantics and breakpoints, including single-column lists at every width.
- Shared components and supported slots, variants and approved icon names/sizes.
- Theme-token references, spacing, text hierarchy and touch/focus behavior.
- Loading, empty, offline, error, overflow and disabled states.
- Data bindings, route identity and capability requirements; no dead launchers.
- A contract version and fixtures against which the surface is checked.

A routine request becomes data such as `recipe=task-list`, `version=1`,
`columns=1`, `history=collapsible`, `settings=expanded`, plus typed content bindings.
These names are illustrative, not implemented APIs. A fixed renderer or reviewed
transform applies that data. No arbitrary CSS, HTML, event handlers or shell
fragments may be smuggled into recipe arguments. Sanitize content separately.

Source-based surfaces can adopt this incrementally: shared components plus
schema-validated recipe configuration and narrowly bounded AST transforms are
sufficient. A new universal UI language/compiler is not required. New bespoke
components, layout primitives or tokens are Developer work, not normal recipe use.

Convert the recent UI notes into explicit acceptance fixtures:

| Requirement | Enforced evidence |
| --- | --- |
| Workflow and Tasks remain linear | DOM layout checks at narrow and wide viewports |
| Theme follows the application | Known-token validation plus light/dark contrast and visual checks |
| Icons remain legible | Approved icon catalogue, bounding-box and glyph-render checks |
| HUD docks and collapses to an edge tab | Region geometry, focus behavior and no chat overlap |
| One destination per launcher | Canonical route/capability checks; no generic fallback masquerading as a surface |
| Binder/settings always visible, history collapsible | Semantic element and interaction checks |
| Flat navigation and bounded panel nesting | Component/AST constraints, not a universal ban on legitimate containment |

Static checks reject undefined USX variables, prohibited hardcoded shell colours,
unsupported components and local overrides of protected layout rules. Intentional
image/canvas/GridCore palettes are explicitly scoped exceptions; do not replace
runtime artwork with shell theme tokens. Visual baselines run in a pinned browser,
font set and viewport with known dynamic regions masked. Include behavioral and
accessibility checks: screenshot similarity alone can approve a broken interface.

The editing agent cannot bless its own new baseline or weaken the rule to pass.
Contract/baseline changes require a separate reviewed Developer change. Existing
violations receive a recorded migration baseline with no-new-violations checks,
then are repaired in bounded slices; do not claim the whole repository conforms.

## Publishing as artifact promotion

Publishing approved user content stays a normal local operation with a named Snack
for transport. It is not frontier development and needs no paid model. Changing a
publisher, build pipeline or rendering engine is Developer work.

Use a fixed workflow:

`validate inputs → build in staging → check output → preview → authorize exact artifact → deliver → verify destination → record receipt`

Bind publication to source revision, recipe/toolchain versions, artifact digest,
target/account and requested visibility. Authorization may come from a standing,
bounded user workflow; do not add a confirmation prompt to every routine run.
A changed artifact or destination invalidates the earlier publication decision.
Never regenerate content between preview and delivery.

Use reproducible build settings where feasible (fixed dependency versions, stable
ordering/timestamps). Keep a content manifest even when a renderer cannot guarantee
byte-identical output. Deliver an immutable build; verify remote version/digest or
use the service's strongest available acknowledgement. A successful HTTP status
alone is not proof the requested content is live at the intended destination.

Record idempotency keys and durable receipts. On an ambiguous timeout, reconcile
remote state before retrying. Use atomic promotion and rollback where the service
supports them; otherwise document compensating actions and irreversible effects.
Do not promise universal exactly-once delivery or recovery across external services.

## Actions and permission propagation

An Action ID resolves to a registered, versioned executor with input/output schemas,
preconditions and expected effects. Normal use has no generic shell, arbitrary
Python evaluator, unrestricted HTTP client or unrestricted source-write capability.
Basic content/program generation can remain generative; execution and packaging
still pass the fixed validators and declared filesystem/network boundaries.

The server creates execution context from authenticated user/task policy. A model
cannot provide `execution_authorized=true`, rename itself Developer, inject a
provider alias or grant a child task broader rights. Each effect boundary checks
the same context, including direct APIs, MCP, scheduled work and subprocess adapters.
Scope credentials and network destinations to the Action, not the model process.
Persist policy version, task scope, limits and checkpoints across cancellation,
restart and retries; revalidate eligibility before resuming effects.

Keep spending eligibility separate from available money. A normal task never gains
premium inference because budget remains. A browser research task can retrieve web
sources without obtaining cloud-model rights. A connected Snack cannot tunnel model
calls through a storage/service exemption. Inspect actual inference destination,
including cloud-backed Ollama aliases and remote embedding/reranking tools.

## Developer experimentation and promotion

Dev Mode permits bounded experimentation and authorized frontier-model spending in
an isolated working copy. It does not suspend path, data, budget or release rules.
Routine USX conformance and standard publishing remain local/deterministic even in
Dev Mode; frontier models may help design a new recipe or extension as an explicit
experiment, not restyle normal surfaces freely.

Promotion path:

`experimental capability → reviewed implementation → fixtures and negative tests → versioned catalogue admission → normal-use executor`

Pin admitted dependencies and provenance through the existing Vendor process.
Normal agents cannot install/update their own Skills, modify policy, replace checks
or promote generated code. A model-assisted quality opinion may inform a review,
but cannot override a failed deterministic gate. No extra evaluator agent is needed
where ordinary checks answer the question.

## Ownership and integration

- uCore owns host dispatch, provider/budget enforcement and integration adapters.
- uFlow owns workflow definitions, action state and durable execution coordination.
- uCode owns BASIC semantics, runtime validation and capsule rules.
- Existing USX package owners govern tokens, components and recipe releases.
- Existing documentation authority (including uDocs) owns mirrored specifications;
  this uCore proposal must be reconciled upstream before cross-repository adoption.

Publish one versioned contract package from existing authorities, consumed by each
entry point and CI. Avoid copies of policy prose drifting across repositories.
Schema compatibility and fail-closed handling of unknown permissions/versions are
part of the contract. Inventory direct provider SDK calls and subprocess/network
escape paths; a shared router is insufficient if an extension can bypass it.

Current gap: `SkillMeta` mainly describes parameters/timeouts/confirmation, while
`run_skill_by_id` checks confirmation/category and required parameters. Catalogue
ownership, lanes and roots are present, but this path alone does not demonstrate
full type, filesystem, network or provider enforcement. The old USX layout link in
`docs/README.md` also points to an absent file. Reconcile the canonical source rather
than adding another competing style specification. These are audit findings, not
claims that all other paths have been reviewed.

## Sprint 4 acceptance and rollout

First agree on the contracts and representative fixtures; then implement one
vertical slice through policy, executor and verification before broad migration.
Prioritize USX task-list/layout conformance, one publish recipe, and one reusable
Markdown or capsule Action. Retain existing CI and runtime authorities.

Measure contract conformance, layout regressions, action postcondition failures,
duplicate external effects, unauthorized dispatches and premium calls in normal
use. Pin and evaluate each local model update against the same fixtures. Test with
Ollama stopped, malformed/hostile output, expired authorization, changed files,
failed checks, retries after ambiguous responses and direct bypass attempts.

Release gates require zero prohibited premium dispatches and zero contract
violations in the selected test suite; neither is a claim of universal safety.
Document capability coverage and measured limits. No new runtime or settings are
introduced by this planning update, and no approval controls are loosened.
