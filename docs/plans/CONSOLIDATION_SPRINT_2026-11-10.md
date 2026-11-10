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
