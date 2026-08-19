# Skills Audit — 2026-08-18

**Status:** Active remediation

**Observed registry:** 53 executable Skills, including one user example

**Dedicated Skill test files before remediation:** 8

**2026-08-19 base-standard hard cut:** Runtime user-skill discovery and arbitrary
filesystem executable fallback are removed. Internal uDos capabilities load only
from the governed builtin registry. Codex Skills are external development
instructions, not executable uDos capabilities. This is a pre-release reset;
there is no compatibility shim for loose `.py` files, legacy skill directories,
or caller-selected scripts and environment variables.

## Findings

The current term “Skill” covers unrelated concepts:

- backend executable capabilities;
- destructive recovery/admin operations;
- orchestration and provider adapters;
- workflow and legacy Tasker adapters;
- a frontend Vue component library at `frontend-vue/src/skills`;
- menu Snacks and uCode Snack runtimes.

The backend registry dynamically imports every Python file and previously
enforced confirmation only in the HTTP API. Internal scheduler and executable
registry calls could bypass it. Core authorization is now enforced in
`run_skill_by_id` with regression tests.

Provider and executor selection is duplicated across `route_task`, Dev Mode,
HiveMind, Roundtable and Cline. Cline integration also contained obsolete CLI
flags, direct key discovery and auto-approval behavior; it is now contained and
disabled by default.

## Disposition

### Keep and harden

- Vault/user capability: `ask_vault`, `attach_context`, `vault_discovery`,
  `vault_sync`.
- Safe maintenance: `backup`, `clipboard_maintenance`, `docs_mirror_sync`,
  `git_maintenance`, `lint_fix`.
- Workflow controls: `workflow_audit`, `workflow_guard`, `workflow_pause`.
- Context/provenance: `episodic_log` after privacy and retention review.

Each retained capability needs an owner, risk class, input/output schema,
allowed roots, deterministic dry run where relevant and dedicated tests.

### Repair behind canonical contracts

- `route_task`: become intention/capability classification only; remove direct
  provider names from user inputs and duplicated execution logic.
- `hivemind-consensus`: become HiveMind orchestration client with budget,
  privacy, attempts and evidence fields.
- `roundtable-dispatch`: become a selective deliberation strategy invoked by
  HiveMind, not a default provider.
- `cline-invoke`: retain disabled, plan-only adapter until worktree harness.
- `gh-workflow-bridge`: narrow to GitHub issues, Actions, PR/review and Codex
  handoff with explicit external-write approval.
- `brain_sync`: separate deterministic indexing from model synthesis.
- `skill-audit` and `ecosystem-audit`: replace source-text heuristics with
  manifest/schema validation and executable tests.

### Merge or split

- Merge `enhancement-planner`, `modularisation-planner`, `duplicate-detector`,
  `dead-code-archiver` and `hardcoded-path-detector` behind one code-analysis
  capability with separate read-only checks and reviewed mutations.
- Split the nearly 2,000-line `skill_nuggets_and_spool.py` into an archive
  service, recovery service and small capability adapters.
- Consolidate `diagnose_system`, `recover_port_conflict`, `cleanup_resources`,
  `restart_backend` and MCP self-heal behind one governed recovery service.
- Move `tasker_sync` and `devlog_mcp` behind the uFlow compatibility adapter;
  they must not maintain a second task engine.
- Rename the frontend Vue `skills` directory to a UI component/system term so
  it cannot be mistaken for executable agent capabilities.

### Remove from general Skill execution

- `reset_database`, `spool_destroy` and `dev-destroy-rebuild`: privileged
  recovery workflows, never ordinary agent-selected Skills.
- `autostart`: lifecycle/service management, owned by Snackbar/System.
- `surface-registry` and `usx-standard`: build/registry tooling rather than
  user-selectable agent Skills.
- `hello-world`: example fixture only; do not dynamically load in production.
- Cline Kanban and all Cline/VS Code surface assumptions.

## Remediation order

1. Core authorization and Cline containment — completed.
2. Add lifecycle, risk, owner, lane, capabilities and allowed-root metadata to
   the Skill contract.
3. Default-deny unclassified and example Skills in production discovery.
4. Separate privileged recovery operations from general execution.
5. Implement the intention task envelope and one provider/budget route.
6. Rewire HiveMind, Roundtable, GitHub and Cline as bounded adapters.
7. Split/merge the oversized and duplicated capabilities.
8. Add catalogue validation, dedicated tests and CI coverage for every enabled
   capability.
