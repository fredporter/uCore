# Agent Execution Architecture

**Status:** Canonical direction

**Updated:** 2026-08-18

## Product principle

Users choose an intention, not an agent, provider, or model. uDOS converts that
intention into a governed task envelope and selects the least expensive capable
execution path. Provider selection remains observable in diagnostics and
advanced settings, but is not normal user interaction.

## Authorities

| Component | Authority |
| --- | --- |
| uFlow | Durable missions, tasks, workflow state, approval state and resumability |
| HiveMind | Decomposition, capability routing, retries, escalation and evidence collection |
| Roundtable | Optional multi-model deliberation and review strategy |
| Provider router | Capability-to-provider/model resolution and health-aware fallback |
| Budget service | Per-task, daily and monthly admission control and cost ledger |
| uCode BASIC | User coding and structured document computation |
| Codex | External ecosystem and add-on development environment |
| GitHub/Copilot | Source collaboration, Actions, issues, pull requests and optional review |

HiveMind is not a model and Roundtable is not a general executor. Neither owns
tasks. They operate on uFlow task envelopes and return structured evidence.

## Task envelope

Every model or agent request must carry:

- intention and success criteria;
- lane: user, workflow, developer or system;
- referenced vault, repository and file context rather than unrestricted roots;
- privacy classification and cloud permission;
- required capabilities;
- allowed tools and write targets;
- risk class and approval requirements;
- maximum cost, attempts and wall-clock time;
- provenance identifiers for prompts, models, tools and outputs.

## Routing ladder

1. Deterministic implementation: parsing, indexing, validation, transforms,
   policy, budgets and workflow state.
2. Ollama: private/local drafting, classification, summaries, Markdown and BASIC
   assistance.
3. OpenRouter free or low-cost models: larger or specialist user work and
   optional diverse review.
4. OpenAI API efficient tier: reliable escalation where free/local quality is
   insufficient.
5. Roundtable: ambiguity, disagreement, high-value review or failed single-agent
   attempts only.
6. Frontier API model or external Codex: difficult, high-value developer work.

Failure moves upward only when the next tier is permitted by privacy and budget
policy. Budget exhaustion moves downward or pauses; it never silently selects a
more expensive provider.

## Surface contract

- Intelligence owns user-visible planning, agent history, provider diagnostics
  and budget decisions.
- Workflow owns uFlow missions, tasks, approvals and resumability.
- Snackbar owns process health, logs, provider availability and runtime alerts.
- Developer remains Code / Repository / Editor. It supplies repository, file,
  selection and diff context to actions such as Plan, Review and Implement; it
  does not regain dedicated agent, model or Kanban tabs.

## Developer executors

Codex is the primary environment for real ecosystem development. GitHub/Copilot
may add repository-native issue, pull-request, Actions and review assistance.

Cline is retained as an optional contained planner. It is disabled by default,
cannot use yolo/auto-approval, cannot be launched directly by Dev Mode and may
operate only in an active Git repository under `UDOS_ROOT`. Act mode requires a
future harness with an isolated worktree, file/path allow-list, budget gate,
command policy, diff review, tests, rollback and explicit merge/push approval.

Cline Kanban is not installed. Durable task presentation belongs to uFlow and
uCore; duplicating it would reintroduce task and status drift.

## Non-negotiable controls

- Model calls pass through the provider router and budget service.
- Mutating execution requires authorization at the core registry, not only UI.
- Vault content cannot reach cloud providers unless its privacy policy permits.
- No executor receives unrestricted credential or home-directory access.
- No agent may merge, push, publish, delete or spend above its envelope without
  the required approval.
- Every result records provider/model, cost, attempts, evidence and mutations.
