# Workspace completion sprint — 2026-11-10

Status: started. Owner: uCore maintainer, with existing adapter/package owners.
Parent: CURATED_APPLICATIONS_CLEANUP_SPRINT_2026-11-09.md. Continues W01–W06 and the unfinished consolidation gates; it does not supersede them or create another task engine.

## Outcome

Deliver a coherent Vault, Google, Apple and Linux workspace experience with truthful capabilities, shared presentation and tested navigation. Finish Binder rename and responsive Workflow qualification. Existing UI changes are an initial implementation, not completed account isolation or provider qualification.

## Ordered delivery

| ID | Owner | Work | Exit evidence |
| --- | --- | --- | --- |
| N01 | uCore | Finish Vault remapping and legacy navigation | Vault selects the shared shell browser; old local/Snackbar links preserve collection/record context; route tests and narrow keyboard checks. No connection database relabelled as filesystem content. |
| N02 | uCore | Complete shared recipe-based Workflow presentation and Binder rename | Mission Control, Tasks, Queue and Editor reviewed at 390/548/1280px, light/dark, keyboard focus, empty/error/busy states; rename HTTP and UI persistence tests preserve IDs and materials. Current styling only covers Mission Control and basic input containment. |
| N03 | uCore/adapters | W01/W02 inventory and operation matrix | Provider/account/collection/native identity, supported operations and platform availability recorded from source. Read-only and unsupported states truthful; no automatic account selection. |
| N04 | uCore/adapters | Dedicated collection views and feed parity | Account-qualified browsing and selected imports use shared components; connection settings expandable; no cross-account data leakage. Old Google Studio route reconciled with Google Workspace; local combined records clearly distinct from native provider records. Linux unavailable until qualified. |
| N05 | uCore/uFlow | Governed sync and recovery qualification | Preview, explicit direction/selection, one Queue/scheduler, cancellation/retry/idempotency, disconnect without deletion; role/provider/OS grants enforced. Disposable fixtures first; live accounts unchanged without explicit scoped authorization. |
| N06 | Product owners | Close consolidation C04/C06/C07 | Extension register documents dependencies/lifecycle/budgets/removal; canonical user guides and redirects; stale product claims corrected with evidence. No archival merely from product names. |
| N07 | Maintainers | Source review/publication and closeout | Recheck worktrees; changed-product suites/build/action/path checks; review diffs and publish intended branches; record remote SHAs. Canon proposal reviewed separately, with recovery history preserved. |

## Dependencies and limits

N01/N02 first. N03 precedes N04 provider data operations. N05 depends on qualified role/Drone contracts from K09/K14; unsupported effects stay unavailable. N06 can proceed independently. Global Knowledge C02 selective proposal remains open; no installed canon update or wholesale recovered corpus publication belongs to this UI sprint.

Use existing repository source, settings, shell/sidebar, resource registry and bundled uFlow. No new service, environment, agent configuration, persistent cache or filesystem root. This plan has source-document lifecycle and negligible storage cost; archive through Git after closeout.

## Starting evidence

Vault URL/name and shared sidebar action implemented locally. Previous slice: 152 frontend tests passed with Node native webstorage disabled for jsdom; Binder engine/lifecycle checks passed; build/action audit passed before final feed-only presentation change; final feed type-check/focused tests passed. These are starting evidence, not completion of N01–N07. Browser view showed Apple workspace feed; full responsive/keyboard and cross-platform qualification remain open.

N01 routing checkpoint: direct Vault entry opens the existing shared browser; legacy workspace=local normalizes to vault while retaining collection and record query context. Provider entry does not open Vault. Three component navigation regressions and type-check pass. Narrow viewport/keyboard qualification and legacy Snackbar redirect integration remain open.

N01 redirect/keyboard checkpoint: three real memory-router tests verify legacy Snackbar Tasks/Contacts/Notes links land on Vault retaining account and record queries; all six focused Apps/redirect tests pass. Isolated live browser check at 390px: Enter activates Linux workspace, focus remains on the selected button, unavailable adapter message appears, and document has no horizontal overflow. Temporary viewport restored and check tab closed. No live account effects. Full 548/1280px and light/dark/Workflow qualification remains N02 work.

N02 Binder rename UI checkpoint: three component regressions verify trimmed title submission to the original stable Binder ID even if navigation changes, refresh after acknowledgement, failed-save edit retention without changing the original title, blank-name rejection and cancellation without writes. Added explicit blank-title submit guard. Focused tests, type-check and whitespace pass. Uses mocked responses only; no live Binder changes. Broader Workflow responsive/light-dark and live rename API reload qualification remain open.

N02 responsive checkpoint: isolated live empty-state checks found no document overflow for Mission Control at 390px dark and 1280px light, Queue at 390/548px and Editor at 548px. Tasks empty-state navigation observed; Queue keyboard activation works. Desktop light inspection revealed grid-distributed vertical gaps; dashboard now aligns content to the start. Original dark theme/viewport restored and temporary tab closed. This is sampled empty-state evidence, not the full populated/error-state matrix. No tasks, missions or Binders created.

N02 Mission Control state checkpoint: fixture tests now cover creation failure with objective retention and successful retry, selected-mission progress/next-task isolation, and failed completion without optimistic status changes. Four Mission Control tests and type-check pass; no production code change or live data mutation. These component checks do not replace populated/error-state browser layout qualification, which remains open.
