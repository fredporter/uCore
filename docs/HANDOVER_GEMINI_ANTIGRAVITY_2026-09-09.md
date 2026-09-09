# Handover to Gemini Agent / Antigravity — 2026-09-09

## Start here

Continue in `/Users/fredbook/Code/uCore`. This is a handover of planning and a
working local Dev Mode checkpoint, not a claim that Sprint 4 is implemented.
The user explicitly selected Gemini and Antigravity as the receiving environment.
The parent workspace contract's reference to Codex does not override that request;
retain its architecture and storage boundaries. Do not create another IDE/agent
configuration tree or a separate internal runtime.

Read `/Users/fredbook/Code/AGENTS.md`, then these documents in order:

1. [Internal readiness audit](INTERNAL_DEV_READINESS_AUDIT_2026-09-09.md): concrete source findings and the next acceptance gate.
2. [Local-first lanes](LOCAL_FIRST_EXECUTION_LANES_BRIEF_2026-09-08.md): user-directed model, network and execution boundaries.
3. [Execution contract](ECOSYSTEM_EXECUTION_CONTRACT_2026-09-08.md): proposed enforcement, USX recipes, Actions and publishing.
4. [Sprint 4 and backlog](NEXT_SPRINT_AND_BACKLOG_2026-09-07.md): scope and deferred work.
5. [Sprint 3A verification](DEV_CHAT_SPRINT3A_VERIFICATION_2026-09-06.md): what actually worked and its supported limits.
6. [Zen ecosystem contract](ZEN_ECOSYSTEM_CONTRACT.md) and [surface ownership](SURFACE_OWNERSHIP.md).

## Repository checkpoint

At handover preparation, branch `main` is at
`d30337c42c08c1c65001464c83fc514ecce465af`,
“Complete Sprint 3A and simplify UIHub navigation (#15)”.
PR: https://github.com/fredporter/uCore/pull/15

The working tree contains intentional, UNCOMMITTED planning changes:

- Modified: `docs/NEXT_SPRINT_AND_BACKLOG_2026-09-07.md`, `docs/README.md`, `docs/ZEN_ECOSYSTEM_CONTRACT.md`.
- New: `docs/LOCAL_FIRST_EXECUTION_LANES_BRIEF_2026-09-08.md`, `docs/ECOSYSTEM_EXECUTION_CONTRACT_2026-09-08.md`, `docs/INTERNAL_DEV_READINESS_AUDIT_2026-09-09.md`, and this handover.

These changes are not included in a fresh remote clone. Use this working directory
or transfer all listed files. Inspect status/diff before any branch operation;
preserve this work. No new commit, push, force push or deployment was performed
for the handover. Remote state was not freshly queried during preparation.

## User intent: keep these decisions intact

uDOS is a Zen, local-first overlay on macOS (current main machine), with Linux
support relevant to architecture but not the immediate implementation target.
Reuse OS tools and vetted open-source/Vendor capabilities before writing new ones.
uCore hosts UI/services; uFlow owns tasks/workflows; uCode owns its runtime.
Mutable state belongs under UDOS_HOME, not new home-root directories. Do not
resurrect uDev or make a second task store.

Keep one shared chat, User/Developer scope and Ask/Plan/Act. Automatically choose
eligible executors behind the scenes; avoid additional chats, agents or selectors.
Expose compact task scope, review and exceptional decisions rather than internal
orchestration details.

- Normal work, Markdown management, BASIC/uCode and capsule packaging, routine
  USX styling and routine Git actions: deterministic Skills/Snacks first; eligible
  local Ollama when inference helps. No premium/cloud inference.
- Frontier inference: explicitly scoped Dev Mode development/experimentation.
  The global Dev toggle alone is not permission to spend or broaden a task.
- BrowserUI/research may access the web. The current brief interprets this as web
  access with local synthesis, not paid inference outside Dev Mode.
- Snacks may connect to named services such as iCloud/Drive. Service connectivity
  and model-provider eligibility are separate permissions.
- Skills are instructions plus reusable execution resources, not a security gate.
  Runtime policy, typed contracts and independent checks enforce the rules.
- USX must use approved components/tokens/layout recipes and behavior/visual
  checks. Do not introduce Gemini-generated styling variations as routine output.
- Publishing uses reviewed artifacts and explicit/standing target authorization;
  retries must reconcile external effects. Preserve useful authorization controls.

## Completed: do not rebuild

Sprint 3A delivered a durable, repository-scoped local Developer Chat with
Ask/Plan read tools, isolated construction proposals, review/Apply, stale-source
checks, cancellation and a real repository test follow-up. The supported recorded
configuration is NanoCoder 1.30.0 ACP with the Vendor permission patch, Ollama and
`qwen2.5-coder:7b-instruct-q4_K_M`. Other models and paid execution were not certified.

Recent UI corrections were included in the merged checkpoint: identity under
Settings, card-only specialist surfaces, truthful extension routes, docked Dev HUD
with edge tab, theme/icon repairs, simplified Dreamscape controls, linear Workflow
and Tasks lists, always-visible Binder/settings and collapsible recent history.
Verify regressions rather than redesigning these surfaces.

The existing editor ledger records 76 items: 66 done and 10 backlog. These are
recorded statuses, not blanket release certification. Consult the backlog document.

## Immediate priority: internal development readiness

The user wants to trust the internal IDE before expanding specific repositories
and extensions. The audit found a working supervised local loop, but disconnected
routing and incomplete shared enforcement:

- `backend/app/services/developer_chat.py` explicitly uses the configured Ollama
  model; `developer_operations.py` uses the same configured construction model.
- `agent_specialization.py` routes elsewhere by task/complexity with fallback.
  This is not yet integrated, policy-filtered selection for the verified IDE path.
- `backend/app/skills/registry.py` checks authorization, but does not centrally
  enforce catalogue lane/root/lifecycle fields or timeout.
- `frontend-vue/src/stores/devMode.ts` can show cached/optimistic mode without
  confirmed server acceptance. Backend mode checks still exist.
- `developer_commands.py` bounds named scripts and duration; cwd and an allowed
  script name do not confine arbitrary script effects.
- `budget_manager.py` checks and records spend separately. Lane eligibility,
  atomic paid reservations and local resource limits need a coherent gate.

First inspect the current source and entry points; reuse the existing code.
Prepare a bounded implementation plan for one complete readiness slice:

1. Server-owned task context: repository/revision, allowed effects/files, non-goals,
   executor/provider eligibility, network scope, budget/resource limits and checks.
2. Enforce context at each selected execution path, not just chat entry.
3. Select only eligible, tested executors; fail clearly if none qualify. Never
   silently switch repository, broaden writes or upgrade to cloud.
4. Prove one internal IDE journey with real diffs/checks and negative cases:
   missing Ollama, denied cloud, out-of-scope writes/network, stale Apply,
   cancellation, restart and conflicting concurrent work.
5. Expand from one supervised repository to one extension only after evidence.

Sprint 4 remains planned. This handover does not itself authorize an unlimited
implementation sweep. Present the concrete first slice for scope review before
starting runtime changes; do not ask the user to re-decide the lane principles.
Keep implementation tasks in uFlow. Defer breadth to fit the existing timebox.

## Verification and remaining uncertainty

For this documentation work, these checks passed:

```sh
python3 scripts/validate_docs_nonregression.py
bash scripts/validate_planning_governance.sh
git diff --check
```

No new runtime tests, deployment or live IDE trial were performed for this handover.
For implementation, follow `.github/workflows/ci.yml`, the repository lockfiles
and installed tooling. Run relevant backend/frontend tests and required governance
checks. Run `python3 scripts/check_home_path_policy.py` for path changes. Frontend
requires Node >=22 and has workspace dependencies; do not replace its package setup.

Use the Sprint 3A verification document for previous live evidence. The last
observed development UI was localhost:5175; do not assume it or the backend is
currently running or serving the latest code. Recheck installed versions and
service health before claiming readiness.

Authentication across all API paths, per-user ownership, downstream provider use,
all extensions and Linux remain uncertified by this source audit. Reconcile Budget
ownership, Hivemind/Roundtable lifecycle, native adapters and canonical USX docs
before expanding those areas. Do not confuse a specification or registered adapter
with a functioning end-to-end capability.

## Suggested opening prompt

> Continue the uDOS handover in `/Users/fredbook/Code/uCore`. Read
> `docs/HANDOVER_GEMINI_ANTIGRAVITY_2026-09-09.md` and its ordered references.
> Preserve the uncommitted planning work. Verify the source findings and propose
> the smallest complete Sprint 4 internal-Dev-readiness slice for review before
> runtime implementation. Keep the established local-first lanes, Zen UI and
> existing runtime ownership. Focus on enforced task scope and eligible automatic
> selection, not new features or additional agent selectors. Distinguish working
> controls, proposals and acceptance evidence throughout.
