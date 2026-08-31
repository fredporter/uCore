# Nanocoder Vendor Integration Plan

**Status:** Phase 0 blocked; inert contract prework complete
**Owner:** uCore Dev Mode and vendor intake
**Related owners:** uFlow task authority, uCode runtime authority

## Decision

Nanocoder may be evaluated as an optional, locally invoked developer tool. The
first integration mode is an unmanaged vendor CLI with a uCore-owned preflight
and governed invocation boundary. It is not an MCP service, uFlow task store,
provider router, or autonomous Developer Surface agent.

The proposed upstream URL must be verified before intake. The current
`https://github.com/nanocoder/nanocoder` lookup returns 404, so the claimed
release artifact, supported configuration format, MCP capability, and MIT
license are unverified. No binary download, vendor source entry, or runtime
registration may occur until the canonical upstream and a pinned release asset
are independently confirmed.

## Non-negotiable boundaries

- uCore owns Dev Mode, vendor intake, preflight, approved invocation, audit,
  and removal.
- uFlow owns missions, workflow definitions/runs, and task state at
  `$UDOS_HOME/flow/tasks`. Nanocoder receives a task reference through an owned
  uFlow API, never a `.tasker` path or a second task store.
- uCode owns GridCore and runtime contracts. Nanocoder must not run or modify
  them outside ordinary repository review controls.
- MCP remains an external adapter boundary. uCore does not proxy, supervise,
  or publish third-party Nanocoder MCP servers. A user-configured Nanocoder MCP
  client connects directly to compatible external servers.
- The Developer Surface remains a repository browser/editor. Do not add an
  autonomous chat or terminal overlay there. Any future guided invocation UI
  belongs behind an approved Intelligence or Workflow action contract.
- Do not create `~/Vendor`, `~/.config/nanocoder`, `~/.nanocoder`, `~/.ucore`,
  or `~/.udos` state. Mutable tool state belongs under `UDOS_HOME`.

## Storage and lifecycle

| Concern | Owner and location |
| --- | --- |
| Provenance record | `uCore/vendor/sources.yaml` and pinned `uCore/vendor/lock.yaml` after intake approval |
| Installed binary and non-secret config | `$UDOS_HOME/tools/nanocoder/<version>/<platform>/` |
| Invocation logs and audit metadata | uCore logging/spool under `$UDOS_HOME/logs/` |
| Credentials | Existing uCore secret-provider flow or the operator's native credential mechanism; never a plan-created config file |
| Task references and execution evidence | uFlow under `$UDOS_HOME/flow/tasks` and its owned workflow-run records |

Removal is deterministic: disable the optional capability, stop launching the
binary, remove the pinned artifact directory under `UDOS_HOME`, remove its
approved source/lock entry in a reviewed uCore change, and retain only the
non-secret audit disposition required by uCore retention policy.

## Phased implementation

### Phase 0 - Provenance and release verification

1. Confirm the canonical upstream repository, organization, license text,
   release signing/checksum process, supported host platforms, configuration
   format, and actual MCP behaviour from upstream documentation.
2. Record the immutable source commit or release version, artifact URL, SHA-256,
   license, capability inventory, operator, date, and disposition in the uCore
   vendor source/lock workflow.
3. Review the binary in a disposable environment. Verify `--version`, offline
   start behaviour, filesystem/network defaults, telemetry statement, and
   configuration discovery paths.

**Exit:** upstream identity and a reproducible pinned artifact are verified;
`vendor_sync.sh --check` remains green. Otherwise close the intake as rejected.

### Phase 1 - Optional CLI preflight

1. Add a uCore-owned optional tool capability only after Phase 0 approval.
2. Resolve the binary solely from its pinned `$UDOS_HOME/tools/nanocoder/...`
   installation path; never search arbitrary `PATH` entries or user home paths.
3. Preflight reports installed version, artifact hash match, supported platform,
   Dev Mode state, selected repository allowlist, and unavailable reason without
   executing Nanocoder.
4. A process wrapper accepts an approved repository ID and task/prompt payload;
   it resolves repository roots under `~/Code` and rejects traversal, external
   paths, unbounded environment forwarding, and secret injection.

**Exit:** absent, invalid, and hash-mismatched artifacts fail safely; a healthy
artifact is discoverable but cannot perform writes without the next phase.

### Phase 2 - Governed execution and uFlow handoff

1. Start read-only planning/dry-run operations only. The wrapper sends a bounded
   structured request and captures non-secret stdout/stderr, exit code, duration,
   artifact version, repository ID, and task reference.
2. Use uFlow task IDs through owned read APIs. No workflow may automatically
   invoke a write-capable tool because a task carries a tag or status.
3. Permit a write-capable invocation only after a separate user confirmation,
   repository allowlist check, clean/dirty-worktree policy decision, bounded
   timeout, uCore budget preflight, and resulting diff/commit review.
4. Provider and budget authority remains uCore. The wrapper must not embed model
   defaults, provider credentials, or fallback routing in Nanocoder config.

**Exit:** controlled dry-run evidence is linked to a uFlow task; rejected and
timed-out calls leave no untracked state outside `UDOS_HOME` or the selected
repository.

### Phase 3 - Optional user experience and MCP posture

1. Only after Phase 2, add an approved action to the owning Intelligence or
   Workflow surface with capability preflight, explicit confirmation, execution
   status, and audit link. Keep Developer Surface repository editing unchanged.
2. If upstream supports MCP, configure it as a third-party client directly from
   Nanocoder under operator control. Do not add routes, a daemon, a bridge, or
   `udos-mcp` tools for generic Nanocoder execution.
3. A future uCore-managed extension is a separate proposal. It must use
   `kind: "tool"`, `optional: true`, `$UDOS_HOME/extensions`, and a narrow
   owned lifecycle contract.

**Exit:** no UI claims autonomous execution until capability preflight,
confirmation, and audit acceptance tests pass.

## Test gates

| Gate | Required evidence |
| --- | --- |
| Vendor integrity | pinned URL/version/SHA-256/license record; artifact hash mismatch test; `bash scripts/vendor_sync.sh --check` |
| Storage policy | `python3 scripts/check_home_path_policy.py` |
| Optional capability | preflight tests for missing, wrong-platform, and valid artifacts |
| Invocation boundary | repository traversal, environment/secret exclusion, timeout, cancellation, and audit-redaction tests |
| uFlow handoff | task reference read and execution-evidence write through uFlow-owned contracts |
| UI | frontend type-check, focused unit tests, and confirmed-action browser test |
| MCP | no new uCore MCP route/tool; any upstream MCP use is tested outside uCore's service boundary |

## Explicitly rejected draft assumptions

| Draft assumption | Plan decision |
| --- | --- |
| `~/Vendor/nanocoder` binary | Rejected. Use a verified, pinned artifact under `$UDOS_HOME/tools/nanocoder`. |
| `~/.config/nanocoder` and `~/.nanocoder/skills` | Rejected. No new application state under `$HOME`; configuration and lifecycle remain uCore-owned. |
| `uDev` skills and `.tasker` automation | Rejected. uDev is compatibility data; uFlow owns tasks and workflows. |
| Automatic task-status-triggered autonomous edits | Rejected. Dry-run first; writes require explicit confirmation and review. |
| uCore/Roundtable/Hivemind MCP bridge mesh | Rejected. Third-party MCP servers connect directly to the external client. |
| Developer Surface overlay | Rejected. Developer remains a repository browser/editor; future actions belong to Intelligence or Workflow. |

## Initial implementation backlog

1. Verify upstream provenance and decide accept/reject.
2. Extend the vendor source/lock schema only if it needs a binary-artifact type;
   do not add an unpinned source record.
3. Design the optional capability preflight and invocation request schema.
4. Implement dry-run-only wrapper tests with a fake executable.
5. Add uFlow task-reference/audit integration without changing uFlow ownership.
6. Propose any UI or managed extension only after the preceding gates pass.

## Prework completed 2026-08-31

- [x] Developer authoritative-diff review boundary implemented and browser-tested.
- [x] Artifact provenance schema scaffolded with pinned HTTPS URL, SHA-256,
      version, platform, license, and bounded vendor identifier requirements.
- [x] Preflight request schema requires Dev Mode on and a repository identifier;
      it accepts no arbitrary filesystem path.
- [x] Invocation request schema is dry-run-only, bounded by prompt/timeout limits,
      and rejects undeclared environment or secret injection.
- [x] Contract tests prove invalid provenance, traversal-like repository IDs,
      write mode, and environment injection fail closed.
- [ ] Canonical upstream and pinned release provenance verified externally.
- [ ] Fake-executable wrapper, audit, and uFlow handoff implemented after acceptance.

The schemas live in `backend/app/services/vendor_tool_contracts.py` and are not
imported by runtime routes. No capability, binary discovery, installation,
execution, UI, MCP, or scheduler behavior has been activated.

## Dev Mode foundation completed

The Developer Surface now fetches the repository-authoritative Git baseline for
the selected file rather than comparing an editable buffer only with its browser
load snapshot. The merge panel identifies clean, modified, and new-file state;
its edits participate in the shared dirty/save lifecycle. This is the required
review boundary before any later confirmed code-construction action.

Evidence: uCore frontend type-check passes; Playwright passes 15 tests including
the sidebar-to-editor authoritative-diff workflow; focused Developer backend
tests pass 6 tests; `scripts/check_home_path_policy.py` passes.

Nanocoder itself remains at Phase 0. No vendor artifact, configuration, wrapper,
MCP route, UI action, or task automation has been installed because upstream
provenance has not been verified.
