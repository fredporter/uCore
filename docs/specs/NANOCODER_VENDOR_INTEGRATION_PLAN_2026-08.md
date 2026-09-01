# Nanocoder Vendor Integration Plan

**Status:** Phase 0 active; canonical upstream and licence verified, immutable artifact intake pending
**Owner:** uCore Dev Mode and vendor intake
**Related owners:** uFlow task authority, uCode runtime authority

## Decision

Nanocoder will be integrated as the governed construction engine behind uCore
Dev Mode operations. The primary interactive boundary is a uCore-owned Agent
Client Protocol (ACP) client supervising `nanocoder --acp`; bounded
non-interactive JSON runs are secondary. Nanocoder is not a uFlow task store,
provider authority, Server skills registry, or autonomous replacement for the
Developer Surface.

The canonical upstream is `https://github.com/Nano-Collective/nanocoder` and the
project publishes `@nanocollective/nanocoder`. The upstream repository identifies
an MIT licence and publishes versioned releases. Intake pins `v1.30.0`, which
requires Node 22 or newer, with npm integrity
`sha512-QCZt7fo2fvazmo/nC2wjU/lfBCRdUfMdmX3rQ8saXPT4Lu/9S0vczcsdOfr3npT6AIcXW9w5Zx517KrE9KnYSg==`
and independently computed tarball SHA-256
`ba9323207bd2d2b4d5ac9d7c77f08f7c2405415d73e8fe0b8929e7366df6dccc`.
Dependency audit and supported-host execution remain required before activation.

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
- The Developer Surface remains the repository browser/editor and hosts a
  contextual Dev Mode operations panel for the selected repository. It renders
  ACP session output, plans, tool calls, diffs, permission requests, and stop
  controls; it does not add a second global chat interface.
- Do not create vendor, configuration, compatibility, or runtime state directly
  under the home directory. Mutable tool state belongs under `UDOS_HOME`.

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
   format, and actual ACP/MCP behaviour from upstream documentation.
2. Record the immutable source commit or release version, artifact URL, SHA-256,
   license, capability inventory, operator, date, and disposition in the uCore
   vendor source/lock workflow.
3. Review the binary in a disposable environment. Verify `--version`, offline
   start behaviour, filesystem/network defaults, telemetry statement, and
   configuration discovery paths.

**Exit:** upstream identity and a reproducible pinned artifact are verified;
`vendor_sync.sh --check` remains green. Otherwise close the intake as rejected.

### Phase 1 - Installation, preflight, and ACP supervision

1. Add a uCore-owned optional tool capability only after Phase 0 approval.
2. Resolve the binary solely from its pinned `$UDOS_HOME/tools/nanocoder/...`
   installation path; never search arbitrary `PATH` entries or user home paths.
3. Preflight reports installed version, artifact hash match, supported platform,
   Dev Mode state, selected repository allowlist, and unavailable reason without
   executing Nanocoder.
4. A supervised ACP process accepts an approved repository ID and resolves its
   working directory under `~/Code`; it rejects traversal, external paths,
   unbounded environment forwarding, and secret injection.
5. Set `NANOCODER_CONFIG_DIR` and logging paths to uCore-owned locations beneath
   `UDOS_HOME`, preventing fallback to implicit platform/home configuration.
6. Implement initialize, session, prompt, permission, plan, diff, cancellation,
   shutdown, timeout, and crash handling against a fake ACP server first.

**Exit:** absent, invalid, and hash-mismatched artifacts fail safely; a healthy
artifact is discoverable but cannot perform writes without the next phase.

### Phase 2 - Governed ACP execution and uFlow handoff

1. Start with plan/read-only sessions. The ACP adapter captures non-secret
   session events, duration, artifact version, repository ID, policy decision,
   and task reference.
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

### Phase 3 - Developer Surface operations and deeper development

1. Add a contextual Dev Mode operations panel to the Developer Surface with
   capability preflight, ACP transcript, plan, tool/diff cards, explicit
   approve/deny, cancellation, execution status, and audit link.
2. Add bounded internal-development actions for explaining selected code,
   diagnosing failures, proposing tests, planning refactors, implementing an
   approved task, and reviewing the working tree.
3. If upstream supports MCP, configure it as a third-party client directly from
   Nanocoder under operator control. Do not add routes, a daemon, a bridge, or
   `udos-mcp` tools for generic Nanocoder execution.
4. A future uCore-managed extension is a separate proposal. It must use
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
| ACP | fake-server initialize, stream, plan, permission, diff, cancel, timeout, crash, and shutdown tests |
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
| Unscoped Developer chat overlay | Rejected. Developer uses a repository-scoped ACP operations panel; global chat remains the bottom widget. |

## Initial implementation backlog

1. Pin and verify the immutable npm/release artifact for the canonical upstream.
2. Extend the vendor source/lock schema only if it needs an npm CLI artifact type;
   do not add an unpinned source record.
3. Design the optional capability preflight and invocation request schema.
4. Implement the ACP client against a fake server, followed by plan-only real-binary tests.
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
- Verified: canonical upstream, package identity, versioned releases, ACP support,
  and MIT licence.
- [x] Immutable npm artifact, integrity, SHA-256, Node requirement, licence, and
      approved optional lock entry recorded without installing it.
- [x] Fake ACP server and supervised process adapter cover initialize, session,
      stream, default-deny permission, cancel, containment, invalid output, and
      shutdown behavior.
- [x] Registry audit of the pinned graph reports 0 known vulnerabilities across
      361 resolved production/optional dependencies on 2026-09-01.
- [x] Real `v1.30.0` ACP initialize succeeds with a generated loopback-only
      Ollama policy; the no-policy smoke test fails closed without discovering
      home-directory configuration.
- [x] Real-binary testing discovered an upstream `.nanocoder/tasks.json` write.
      The deterministic installer now applies one version-pinned patch adding
      `NANOCODER_TASKS_DIR`; the supervisor routes it beneath `UDOS_HOME`, and a
      repeated initialize handshake leaves the repository clean.
- Pending before activation: live Server model/budget resolution, runtime audit,
  session persistence, permission UI, and uFlow handoff.

The schemas live in `backend/app/services/vendor_tool_contracts.py`; the inert
transport lives in `backend/app/services/nanocoder_acp.py`. Neither is imported
by runtime routes. No capability, binary discovery, installation, execution,
UI, MCP, or scheduler behavior has been activated.

## Dev Mode foundation completed

The Developer Surface now fetches the repository-authoritative Git baseline for
the selected file rather than comparing an editable buffer only with its browser
load snapshot. The merge panel identifies clean, modified, and new-file state;
its edits participate in the shared dirty/save lifecycle. This is the required
review boundary before any later confirmed code-construction action.

Evidence: uCore frontend type-check passes; Playwright passes 15 tests including
the sidebar-to-editor authoritative-diff workflow; focused Developer backend
tests pass 6 tests; `scripts/check_home_path_policy.py` passes.

Nanocoder remains at Phase 0 intake. No artifact, configuration, process adapter,
UI action, MCP route, or task automation has been installed yet; the remaining
gate is immutable artifact and dependency verification rather than upstream
identity.
