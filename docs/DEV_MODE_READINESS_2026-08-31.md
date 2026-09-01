# Dev Mode Readiness — 2026-08-31

Status: Active readiness plan
Owner: uCore Developer and Workflow surfaces

## Objective

Complete or explicitly scaffold every prerequisite for the next confirmed Dev
Mode construction plan without restoring retired autonomous runtimes, task
stores, MCP meshes, or unverified vendor tools.

## Completed readiness work

- [x] Developer editor uses the repository-authoritative Git baseline.
- [x] Modified, clean, and new-file states share the editor dirty/save lifecycle.
- [x] uCode runtime routes register as required host routes with adapter tests.
- [x] Workflow workspace supports bounded CRUD, search, drag/move, mobile access,
      offline reads, queued saves, and optimistic conflict detection.
- [x] BrowserUI research capture persists content before opening Workflow editor.
- [x] Overlay infrastructure and Markdown format routing are mounted and active.
- [x] Feed signals can be reviewed, rule-previewed, and explicitly promoted to tasks.
- [x] Optional vendor artifact, preflight, and dry-run request contracts are
      scaffolded as inert validation models with no runtime registration.
- [x] Bangle/Dev task ledger reconciled against tracked implementation evidence.
- [x] Companion uCode GridCore/runtime prework validated, committed, and pinned
      immutably for clean-checkout CI.

## Branch disposition

| Branch | Disposition | Evidence / next action |
| --- | --- | --- |
| `codex/advance-runtime-feed-workflows` | Active delivery branch | Four earlier checkpoints plus current readiness work; merge through protected checks. |
| uCode `codex/complete-gridcore-runtime-prework` | Companion delivery branch | Validated GridCore, Teletext, BBCSDL, session-runtime, and software-library prework at `c7dbc44`; merge through the uCode PR before returning the uCore CI pin to `main`. |
| `recovery/2026-08-18-teletext-import` | Superseded, retain until active branch merges | Current Teletext catalogue, golden pages, and 16-test browser suite replace the incomplete two-file recovery commit. |
| `work/2026-08-18-stabilise` | Historical stabilization branch | Its architecture/removal work was subsequently merged or superseded by protected PRs; do not merge wholesale. |
| `codex/mcp-vendor-architecture-audit` | Superseded by current accepted audit | Current `MCP_ARCHITECTURE_AUDIT_2026-08-19.md` contains the accepted and implementation-updated form. |
| merged `codex/*` architecture/removal branches | Closed | `git cherry` reports patch-equivalent commits already in `origin/main`. Remote deletion is deferred until the active delivery PR merges. |

## Verification-gated vendor prework

Nanocoder has passed Phase 0 intake. Its canonical Nano Collective upstream,
MIT licence, pinned npm package, integrity, dependency audit, and ACP editor
protocol are verified. The repository contains inert validation contracts and a
route-independent supervised ACP transport. These contracts reject arbitrary
paths, environment injection, write mode, unbounded prompts, unbounded timeouts,
non-loopback initial providers, and launch while Dev Mode is off.

The following work remains gated and must not be simulated:

- Record and verify the immutable npm/release artifact, integrity, version,
  platform support, and dependency audit.
- Review the pinned artifact in a disposable environment.
- Decision gate: accept or reject; only acceptance may activate capability requirements.
- Planned after acceptance: implement a fake ACP server, supervised ACP process
  adapter, and audit tests.
- Planned after adapter evidence: implement the uFlow task-reference/audit handoff
  and Developer Surface Dev Mode operations panel.

No source entry, lock entry, binary path, capability requirement, route, UI
action, MCP tool, or scheduler registration exists before that decision.

## Remaining product backlog

The long-form execution sequence is
`docs/DEV_MODE_LONG_SPRINTS_2026-09.md`. It makes Nanocoder ACP the governed
construction engine for the Developer Workbench while retaining uCore policy,
repository, audit, and lifecycle control.

The reconciled frontend task ledger is
`frontend-vue/src/tasks/bangle-upgrade.tasks.ts`: 76 actual task objects, with
48 done and 28 backlog. `BANGLE_TASK_SUMMARY` derives these counts from the
objects so comments and type declarations cannot inflate the total.
The next product lanes are:

1. Frontmatter editor and enhanced Bangle formatting toolbar.
2. Research synthesis: combine, citation, variants, and toolbar scrape entry.
3. Tests, accessibility, docs, performance, and final editor smoke gates.
4. Identity, settings, and chat persistence using their owning APIs.
5. PWA/mobile enhancements beyond the completed workspace drawer.

## Stop-the-line gate

Every construction checkpoint requires runtime proof, command proof, test
proof, evidence proof, a clean diff check, and protected-branch CI. A vendor
provenance failure or capability preflight `412` blocks execution rather than
triggering repair or fallback execution.
