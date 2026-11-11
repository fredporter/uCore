# Consolidation sprint — 2026-11-10

Status: ready; first correctness fix complete locally. Owner: external Wizard/maintainer.
Authority: existing curated-applications backlog and bundled uFlow; this is a delivery plan, not a second task engine.

## Outcome and boundaries

Complete the repository, extension and documentation consolidation identified in REPOSITORY_ASSESSMENT_2026-11-10.md. Preserve source history and user material. Keep existing product owners; introduce no repository, service, environment or runtime state. This Markdown plan shares uCore's source lifecycle and negligible storage budget; remove/archive it through normal Git history after closeout. Live account migrations and broader application-platform implementation remain governed by the parent backlog.

## Ordered work

| ID | Owner | Deliverable | Completion evidence |
| --- | --- | --- | --- |
| C01 | uCore-Publish | Remove fabricated cloud success and readiness | Configured/unconfigured regression tests pass; no invented remote receipt. Implemented, awaiting publication. |
| C02 | global-knowledge maintainer | Recheck divergent commits and untracked assets; preserve and reconcile on a reviewed branch | Recorded SHAs, untracked inventory/checksums and recovery reference; reviewed content decisions; no blind reset/pull or installed canon writes. |
| C03 | uCore maintainer | Publish current planning and Mission-led branch | Tests/checks recorded, remote branch matches local SHA; review/merge qualification distinct from push. |
| C04 | uCore plus extension owners | One extension disposition register using existing registry contracts | Google, Publish, Vector, SnackMachine and uCode2 each have owner, capabilities, dependencies, qualification, lifecycle, budget and removal procedure; overlaps resolved without duplicate engines. |
| C05 | uCore | Correct documentation-mirror sources for bundled uFlow/knowledge | Fresh-install source discovery and missing optional repositories tested; reading/refresh preserved, no repository write-back. |
| C06 | Product documentation owners | Consolidate task-focused user guidance under uDos Documentation | Source/destination/provenance inventory; canonical guides and redirects; broken-link check; uCode curriculum and restricted maintainer reference retain their owners. |
| C07 | Product owners | Correct stale descriptions and unsupported capability claims | Sonic hardware-revival description, HomeNest scope and family/extension links audited; claims match qualified behavior. |
| C08 | uCore maintainer | Closeout and handoff | Changed-product checks pass, path policy passes for path changes, remote SHAs recorded, remaining parent-backlog work explicitly linked. |

C02 precedes corpus cleanup. C04 precedes archival decisions. C05 and C07 can proceed independently after source inspection. No repository/archive deletion is required by this sprint. Remote publication never implies release certification.

## Integration with existing programme

Workspace W01–W06 remain in WORKSPACES_AND_VAULT_GOVERNANCE_2026-11-10.md. Role/Drone enforcement and curation/edition delivery remain K09/K14/K10/K12/K03 in CURATED_APPLICATIONS_CLEANUP_SPRINT_2026-11-09.md. This sprint reconciles foundations and documentation rather than declaring those features complete.

## Validation record

Kickoff: uCore-Publish unittest suite: six passed; both repositories' whitespace checks passed. No live provider writes, vault moves or canon changes performed. Existing uCore feature commits retain their earlier validation records; this planning pass does not re-certify those features.

C02 started: fetched upstream; histories have no common ancestor. Both tips retained and four untracked files committed on a local recovery branch. See GLOBAL_KNOWLEDGE_RECONCILIATION_2026-11-10.md. Selective corpus comparison and provenance review remain open; no installed canon changes.

C02 comparison checkpoint: 518 local-only paths, upstream VERSION only, differing README; full object inventory and content holds recorded in GLOBAL_KNOWLEDGE_RECONCILIATION_2026-11-10.md. Tomb semantics and unsupported runtime claims require revision before selective delivery.

C02 selective delivery proposal prepared on global-knowledge branch `plan/selective-canon-reconciliation`, based on upstream. Includes edition plan plus revised README, layering, host reference and container contracts; historical corpus/assets remain on the recovery branch. Removed stale Tomb meaning, fixed model recommendations, fabricated implementation guarantees and unmeasured capacity promises. Relative Markdown links, whitespace and uCore home-path policy pass. No installed baseline changes or release certification; content/edition approval and publication remain open.

C05 complete locally: default documentation-mirror roots now reference uCore, uCode and uVector, removing retired sibling uFlow/uKnowledge assumptions. Bundled service documentation remains under uCore; optional missing roots remain tolerated. Existing extension discovery and read-only/writeback boundaries are preserved. Twelve mirror tests pass, including fresh-install/missing-optional coverage; home-path policy and whitespace checks pass. C04 remains open: SnackMachine README assigns packaging metadata/catalogs to the extension and queue/lifecycle to uCore; uCode2 describes spatial conversion. Runtime manifest/dependency and install/removal qualification are still required before a disposition decision.

## Extension disposition

These packages remain with their current owners. Installation, budgets and removal apply only where the named component is actually enabled. The existing extension registry remains the discovery contract.

| Package | Ownership and dependencies | Lifecycle and budget | Qualification |
| --- | --- | --- | --- |
| uCore-Google | Optional Google Studio bridge. Manifest depends on ucore-core and ucore-secrets. uCore owns Google Workspace connections and Drone grants. | Opt-in extension discovery and Google credentials. Review provider usage and local mirrors before enabling. Remove the extension from discovery and its owning environment after disabling consumers. Review credentials and mirrored content separately. | Qualify Studio operations independently from Workspace sync. |
| uCore-Publish | Optional edition/export package. The publishing manifest declares /api/publishing. | Build selected editions with explicit destinations. Budget output and temporary storage per edition. Remove package/discovery entry after migrating consumers. Keep exported editions according to owner retention. | Local publishing tests cover the adapter's unavailable state. WordPress transport remains open. |
| uVector | Optional Rust vector engine and Python binding. Manifest declares /api/vector. | Build/install only for consumers that need conversion. Account for toolchain, build artifacts and generated assets. Detach consumers before removing discovery and package artifacts. | Qualify packaging and conversion on supported targets. |
| SnackMachine | Optional package catalog and install metadata. uCore owns host execution and bundled uFlow owns scheduling. | Use the package's environment for catalog tooling. Budget installed artifacts per package. Remove via the owning package contract after reviewing dependencies, scheduled consumers and retained content. | Managed artifact installation and cleanup need end-to-end validation. |
| uCode2 | Experimental spatial converter and voxel export CLI. uCode owns BBC BASIC and GridCore. | Run on demand in its owning environment. Budget generated voxel assets per export. Remove optional integration and package after checking launcher/route consumers and preserving exports. | Keep experimental. Qualify extension lifecycle before wider distribution. |

C04 disposition and C06 task-oriented documentation are recorded here and in the uDos Documentation index. C07 source review confirms Sonic's current scope is diagnostics, explicit intake and offline lookup. HomeNest's first release is Linux Steam gaming and media. Historical product claims remain in their archive context.

## Closeout evidence

- C01 and C05 are delivered. C02's selective proposal is published on Global Knowledge branch `plan/selective-canon-reconciliation` at `1b19557`. The recovery branch and broader corpus remain local for provenance and distribution review.
- C04 and C06 have a disposition register and a canonical task guide. Package lifecycle qualification and archive-wide provenance review remain follow-up work.
- C07 GitHub descriptions for SonicScrewdriver and HomeNest now match their active product scope. The knowledge and publishing validation scripts use bundled uCore and the current uCore-Publish repository.
- Final local qualification passed with 770 backend tests against disposable roots, 164 frontend tests, production build, 917 action controls with zero unresolved handlers, six publishing tests, route contracts, extension manifests, packaging smoke, planning governance and home path policy. The build reports large chunks and a redundant dynamic import.
- Release follow-up covers the disposable live Google and Apple rounds, populated Workflow layout checks, authenticated local profile switching and remote Drone enrollment. Linux native adapters, WordPress transport and optional package lifecycle certification remain open. See [final qualification rounds](WORKSPACE_COMPLETION_SPRINT_2026-11-10.md#final-qualification-rounds).
