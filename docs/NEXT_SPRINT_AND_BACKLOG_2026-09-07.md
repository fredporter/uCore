# Next sprint and remaining backlog — 2026-09-07

Status: Sprint 3A local checkpoint complete; Sprint 4 planned, not started.
Owner: uCore planning; uFlow remains the execution task authority.
This is a dated reconciliation of the [long-sprint sequence](DEV_MODE_LONG_SPRINTS_2026-09.md),
not a second task store. No new implementation sprint is started by this document.

## What happens next

The next planned sprint is **Sprint 4 — Zen consolidation, authoring/research verification, and
native integration intake**. Keep its four-week timebox, with exact implementation
scope selected after reviewing the existing work. Do not rebuild capabilities
already marked done or add another chat, agent selector, or runtime.

## Sprint 3A: local coding checkpoint complete

The shared User/Developer chat, Ask/Plan/Act controls, durable conversation state,
review controls, and governed construction plumbing are implemented. The real
local flow generated a correct diff, applied it through the browser, and ran the
repository-defined test through a follow-up chat request with exit code 0.
Ask/Plan context, restored history, cancellation, cross-scope running status,
and narrow-width review/Apply were also exercised.

The key handoff correction carries an actually inspected file into construction.
Exact repository paths, bounded operation evidence, and one governed continuation
when an engine stops without edits prevent advisory prose being treated as work.
Failed attempts remain failed and do not modify the live repository.

Evidence and supported-runtime limits: [Sprint 3A verification](DEV_CHAT_SPRINT3A_VERIFICATION_2026-09-06.md).
This closes the local coding integration checkpoint. It does not certify all
models, paid execution, all ecosystem services, or a deployed installation.
Broader release and service reconciliation remain explicitly scheduled below.

## Existing editor backlog: 10 open items

Read from `frontend-vue/src/tasks/bangle-upgrade.tasks.ts` on 2026-09-07:
76 task objects, 66 marked done, 10 marked backlog. These are recorded statuses,
not a new claim that every completed feature passed release acceptance.

| ID | Remaining item | Planned checkpoint |
| --- | --- | --- |
| bangle-test-001 | Unit tests across utilities | Sprint 4 targeted gaps; Sprint 6 release audit |
| bangle-test-002 | Interactive component tests | Sprint 4 |
| bangle-test-003 | Complete workflow E2E tests | Sprint 4 primary journeys; Sprint 6 release suite |
| bangle-test-004 | Mobile/responsive verification | Sprint 4 affected surfaces; Sprint 6 full audit |
| bangle-test-005 | Dark-mode rendering | Sprint 4 affected surfaces; Sprint 6 full audit |
| bangle-test-006 | Keyboard accessibility | Sprint 4 affected surfaces; Sprint 6 full audit |
| bangle-doc-001 | Component documentation | Sprint 6 |
| bangle-doc-002 | Editor user guide | Sprint 6 |
| bangle-deploy-001 | Measured performance optimization | Sprint 6 |
| bangle-deploy-002 | Final integration and smoke tests | Sprint 6 |

No task statuses are changed by this planning update. Reconcile checklist-level
acceptance and uFlow references before closing any of these items.

## Sprint 4: proposed scope

1. **Verify existing authoring and research.** Audit frontmatter round-trips,
   formatting, keyboard commands, capture, Combine Research, variants, citations,
   renderer routing, and Notebook/Drive integration against their current code and
   evidence. Repair demonstrated gaps; do not treat old feature lists as new work.
2. **Simplify affected surfaces.** Apply the Zen contract across authoring,
   research, browser, and Snackbar: one clear work surface, contextual controls,
   useful defaults, and advanced preferences in their owning settings. Inventory
   other ecosystem surfaces and assign follow-up rather than redesigning all at once.
3. **Reconcile native integration already present.** Inspect the existing macOS
   PIM bridge and historical Snackbar specifications before proposing adapters.
   Map availability, consent, source ownership, push/pull behavior, and graceful
   unavailability for Notes, Reminders, notifications, voice/dictation, Mail,
   Messages, Safari, and iCloud-backed content. API presence alone is not validation.
4. **Select a bounded native vertical slice after intake.** Prefer completing an
   existing adapter and proving one useful content-exchange journey. A universal
   messaging aggregator and every native service are not automatic Sprint 4 scope.
5. **Reconcile backend authorities.** Resolve the Budget plugin/shared-manager
   split and define the paid-execution gate. Classify Hivemind/Roundtable as retained,
   replaced, or retired based on historical intent and actual need. Verify agent
   and skill execution only for capabilities selected for this sprint. Keep these
   choices behind the UI; do not introduce user-facing orchestration selectors.
6. **Close relevant quality gaps.** Use the six testing backlog items above to
   prove the affected product journeys, including accessibility and responsive
   behavior. Preserve source provenance and keep code out of the user Binder.

Each selected slice must name its existing OS/ecosystem/Vendor authority, the
minimal custom integration required, acceptance evidence, and lifecycle owner.
Only take work that fits the timebox; retain unselected work in uFlow.

## Later and explicitly deferred

- **Sprint 5:** reconcile identity, shared settings, per-user chat history,
  retention, offline shell/sync, and mobile behavior. The editor ledger marks its
  original account/offline items done; verify ecosystem-wide gaps before scheduling
  new implementation. Dev conversation storage is not per-user isolation proof.
- **Sprint 6:** complete release E2E, accessibility/theme/mobile audit, measured
  performance, documentation, clean-checkout installation and smoke tests.
- **Native messaging:** unified inbox and additional app adapters follow proven
  access contracts; no promise of universal Mail/Messages/iCloud access.
- **Linux:** preserve Safari-on-Mac / Firefox-based Zen Browser-on-Linux direction
  and historical specs. Linux implementation and validation remain deferred;
  resolve packaging and compatibility during a Linux-specific intake.
- **Distribution/SonicScrewdriver:** follow the existing post-program pathway and
  mandatory specification reconciliation before new construction.

## Decision boundary

Sprint 3A closes with the merged source checkpoint and recorded local-runtime
acceptance. Sprint 4 is ready for scope review and a clean start; its development
has not been started by this closure. The user authorized completing 3A, merging
all open branches into main, committing, and pushing. Native integration expansion,
paid service activation, and broader deployment are not implied by this checkpoint.
