# Internal Dev Mode readiness audit — 2026-09-09

Status: source audit and proposed Sprint 4 gate; no runtime changes or deployment certification.
Owner: uCore hosting and enforcement; uFlow remains the task authority.

## Assessment

Sprint 3A proved a local, supervised repository coding loop. It did not prove
an automatically selected agent can execute every ecosystem task within the new
local-first boundaries. Use that supported loop for bounded, reviewed changes;
do not yet treat internal Dev Mode as an autonomous ecosystem maintainer.

This audit reads the current uCore implementation. It is not an exhaustive audit
of every extension, API authentication path, installed runtime or downstream repo.
The [Sprint 3A evidence](DEV_CHAT_SPRINT3A_VERIFICATION_2026-09-06.md) records the
previous live checkpoint; no new live coding trial was performed for this audit.

## Working foundations and remaining gaps

| Area | Source evidence | Remaining enforcement work |
| --- | --- | --- |
| Repository scope | `backend/app/services/developer_chat.py` locks a conversation to its repository; `backend/app/api/developer_api.py` resolves contained paths. `developer_operations.py` constructs in isolation and checks source fingerprints before Apply. | Bind each task to revision, permitted files, non-goals and accepted effects. Repository containment alone cannot prevent unrelated changes inside that repository. |
| Automatic selection | Developer Chat calls `ollama/{settings.developer_model}`; construction also configures that model. `agent_specialization.py:get_best_agent_for_task` separately routes by task/complexity and falls back to dev or the first configured agent. | Connect the supported coding path to one policy-filtered selector. Filter eligibility before ranking; no fallback outside the task lane. Record why an executor/model was selected. Existing routing elsewhere is not proof of integrated IDE selection. |
| Mode truth | Backend `require_developer` checks full Dev Mode. `frontend-vue/src/stores/devMode.ts` restores cached mode when unavailable, and `setMode` changes local state without checking the response status. | Distinguish confirmed server mode from cached preference and disconnected state. Block dependent actions until confirmed. The UI discrepancy is not evidence that backend checks can be bypassed. |
| Skills | `backend/app/skills/registry.py` requires catalogue lane/root/lifecycle metadata; `run_skill_by_id` checks execution authorization and calls validation/run. | The central runner does not enforce those lane/root/lifecycle fields or its advertised timeout. Make metadata executable policy; validate input types and output contracts, reject inactive recipes and bound execution. Keep useful existing authorization. |
| Command execution | `developer_commands.py` allows named repository scripts, requires Dev Mode, limits duration, filters inherited environment and supports cancellation. | A script named test can still execute arbitrary repository code. A working directory is not filesystem or network confinement. Define trusted script provenance and enforce task-specific process/file/network limits using existing OS facilities where available. |
| Budget | `budget_manager.py` has separate can_spend and record_spend operations; zero estimate returns true. Local Developer Chat records zero-cost Ollama calls. | Enforce lane eligibility before cost checks; reserve paid funds atomically and reconcile actual spend. Zero estimate must not mean an unknown paid call is free. Add local time/concurrency limits separately. This does not establish that current local chat silently uses paid inference. |
| Native and downstream work | `system_snacks.py` has native integration adapters and a legacy reply spool default; `gridsmith_bridge.py` delegates to uCode. | Verify actual downstream execution, provider/network behavior, cancellation, state paths and version compatibility. Adapter availability is not end-to-end acceptance. |
| Consistent output | Existing UI fixes and tests provide useful examples. The September 8 execution contract proposes strict USX recipes and publishing gates. | Implement selected recipes and independent checks. The proposal itself does not enforce layout, immutable publishing artifacts or consistent Actions. |

## Other boundaries that must become explicit

- **Authority and lifecycle:** one owner for each capability, one active implementation,
  one canonical spec, supported versions and a removal path. Resolve Budget overlap
  and retain/replace/retire Hivemind and Roundtable intentionally. A catalogue entry
  marked review, split or merge must not silently imply approved execution.
- **Completion:** a task finishes on stated acceptance evidence, not a model's
  statement. Distinguish proposed, applied, checked, committed and published.
  Failed checks must remain visible; test or visual-baseline edits require review.
- **Recovery and concurrency:** define interruption/restart handling, locks for
  conflicting edits, stale results and safe retries. Do not replay external effects
  merely because a response was lost. Reconcile delivery before retrying.
- **Identity and data:** establish the supported single-user/local boundary now;
  certify ownership of conversations, approvals and credentials before shared or
  remote use. This audit does not determine endpoint authentication coverage.
- **Dependencies and promotion:** experimental Dev Mode changes remain isolated
  until reviewed, checked and promoted into a versioned Skill/Action/USX recipe.
  Approved upstream tools should be pinned and tested, not replaced by new wrappers
  without an identified need.
- **Transport versus permission:** HTTPS, JSON and MCP describe different layers;
  changing transport alone does not enforce a lane. Every entry point must enforce
  the same execution context, including direct API, nested agents and schedules.

## Minimum gate before relying on automatic internal development

Keep the current chat and Ask/Plan/Act controls. Add no agent selector or new chat.
Show a compact task scope and exceptional decisions; maintain detailed receipts
behind the existing review surface.

1. **Issue a server-owned execution context:** task ID, User/Developer scope,
   selected repo/revision, allowed effects/files, provider eligibility, network
   destinations, resource/spend limits and acceptance checks. Agents may propose
   a scope change but cannot grant it to themselves.
2. **Enforce it at execution:** wire the current chat, construction, commands,
   Skills, provider dispatch and selected integration paths through shared checks.
   Validate at each effect, not only when the turn begins. Default normal work to
   deterministic execution, then eligible local Ollama; frontier inference requires
   a specifically authorized Dev task. Research web access and connected Snacks
   do not authorize cloud inference.
3. **Select automatically within eligibility:** choose a tested capability/model
   using capability, local health and resource limits; record the decision. When
   no eligible executor exists, report the missing capability. Do not silently
   upgrade to cloud, switch repositories or broaden the task.
4. **Prove a bounded internal IDE journey:** one selected repo, read/plan, proposed
   diff, review/Apply, real checks and restart recovery. Exercise missing Ollama,
   denied cloud access, out-of-scope writes, stale diffs, failed checks, cancellation
   and concurrent conflicting work. Include script attempts outside granted roots
   and network destinations; do not count path validation alone as containment.
5. **Promote only the proven subset:** start with a supervised single-repo pilot,
   then one extension. Admit additional executors and routes only with their own
   evidence. Recheck the installed runtime rather than assuming merged code is live.

Sprint 4 should deliver this gate before expanding features. Within its existing
timebox, choose the smallest complete slice; defer breadth rather than labelling
an incompletely enforced ecosystem ready. uFlow should hold implementation tasks;
this document is an acceptance brief, not a parallel task database.

Related: [execution lanes](LOCAL_FIRST_EXECUTION_LANES_BRIEF_2026-09-08.md),
[execution contract](ECOSYSTEM_EXECUTION_CONTRACT_2026-09-08.md),
[next sprint and backlog](NEXT_SPRINT_AND_BACKLOG_2026-09-07.md).
