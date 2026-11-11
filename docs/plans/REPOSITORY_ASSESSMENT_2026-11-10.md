# Local and remote repository assessment — 2026-11-10

Read-only assessment of top-level Code repositories, GitHub account fredporter, current ownership contract, selected README files and integration source. No repository was moved, deleted, fetched, reset, published or remotely archived. Recommendations below are architectural judgments, not release certification. Tests were not run for this inventory.

## Synchronization and preservation

Live GitHub default-branch SHAs were compared with local main for 13 repositories. Twelve match: uCore, uCode, SonicScrewdriver, uCore-Google, uCore-Publish, SnackMachine, uCode2, uVector, HomeNest, Groovebox, wpmudev-agent and fredporter. Matching source commits do not prove all local branches, tags, assets or releases are backed up.

uCore main matches remote 513a1c6; its current local plan/curation-roles-distribution branch contains three additional commits: c191175, c48a34e, bcef217. Those implement the sprint extension, Mission-led workflow and documentation/matrix. This assessment is additional local documentation. Review/publish this branch before treating the sprint additions as remotely available.

Global Knowledge is the exception: local main 5e6abf3 differs from remote main c69c46c. The cached origin/main matches that live SHA; comparison reports seven local-only and two remote-only commits. Four untracked paths also need preservation: EDITION_PLAN.md, elements/bob-zen_envelope-teletext_ceefax.gif, standards/COMMUNICATIONS-LOOP-SPEC.md, standards/GRIDCORE-LATTICE-SPEC.md. Historical local commits include legacy home-layout changes. Reconcile selected content/history on a reviewed branch; do not blindly pull, reset or publish the entire local tree. This is maintainer source, distinct from the installed Public/global-knowledge baseline.

## Repository disposition

| Repository | Assessment | Needed next |
| --- | --- | --- |
| uCore | Essential host and bundled workflow/knowledge/identity authority | Finish sprint qualification; publish local sprint branch through review; implement target roles separately from display preferences. |
| uCode | Essential language/runtime and learning owner | Keep independent; retain tested native BASIC integration and explicit host/runtime boundary. |
| SonicScrewdriver | Essential hardware revival/provisioning product | Retain; qualify safe USB/media operations before advertising them. Current README explicitly says no disk-writing capability. Correct GitHub description, which still calls it an API gateway/security layer. |
| global-knowledge | Essential canon/standards/dataset source; immediate reconciliation priority | Preserve divergent history and untracked material; inventory/deduplicate; build reviewed editions and separate standards from ordinary user documentation. |
| uVector | Useful optional engine with actual uCore integration references | Retain; qualify packaging, Rust/Python bridge and GridCore conversions; no need to absorb it into uCore. |
| uCore-Google | Useful optional cloud integration, not core identity/workflow owner | Retain and audit each operation; align with Sorcerer/Wizard and Knight-through-Drone rules, provider consent and truthful remote status. README scope is not proof of production behavior. |
| uCore-Publish | Useful compiler/export owner plus unfinished cloud adapter | Retain; qualify clean-edition/privacy pipeline and replace fabricated cloud success before enabling remote publication. |
| SnackMachine | Optional packaging/catalog extension; legacy snack vocabulary overlaps new governed skill/recipe work | Decide package contract and responsibility against uCore registry, installer and uFlow. Consolidate overlapping catalogs/contracts before considering archival. Do not recreate a task engine or generic shell. |
| uCode2 | Optional spatial/voxel experiment, not a second everyday OS/runtime | Keep as experimental extension pending demonstrated use; reconcile old uCode1/2 family terminology. Existing launcher/extension references mean it is not safe to remove by name alone. |
| HomeNest | Independent deferred product, not legacy merely because idle | Keep outside core sprint. Current focus is Linux gaming/media; older home-automation remote description is stale. |
| Groovebox | Independent optional music product | Keep outside core sprint; audit stale family links and version claims before reuse/distribution. |
| wpmudev-agent | Separate WordPress/travel development workspace | Keep isolated from uDos runtime and credentials; no justification to absorb it into uCore. |
| fredporter | GitHub profile repository | Unrelated infrastructure; leave separate. |
| bangle-io | Remote-only fork in this inventory | Treat as third-party/reference, not a new core service. Establish dependency/license/update purpose before cloning or adopting. |

## Already legacy, not missing services

GitHub marks these six repositories archived: udos-vaults, udos-identity, udos-budget, uKnowledge, uFlow, udos-agents. Local dated archived counterparts exist under ARCHIVED. Their former independent runtime boundaries are retired; useful concepts and source may remain in bundled uCore contracts. In particular, uFlow remains the workflow authority as bundled code, not a missing standalone deployment.

ARCHIVED also contains historical DevStudio, uDev, uServer, uConnect, uCode1/2/3/4, uDocs and recovery snapshots. Preserve as provenance/recovery inputs until useful material is reconciled. ARCHIVED presence alone does not prove remote backup or make an entire tree safe to delete. This pass did not recursively audit every archived or vendor Git repository.

Vendor is a visible upstream/reference cache, not an application repository. Code/.udos is mutable ecosystem state, not source or an archive candidate. Vault/Shared/Public documents likewise require their own content audit. Avoid classifying runtime data, personal content and repository source together.

## Concrete legacy and correctness issues

- uCore-Publish/udos_publishing/src/cloud_adapter.py: publish_post_remote returns success true, mode live and remote_id 1001 when configured, without performing an outbound request. Replace with explicit unavailable status or a tested provider implementation; configuration cannot establish successful delivery.
- uCore/backend/app/services/docs_mirror.py still lists sibling uFlow and uKnowledge repositories. Reconcile document sources with their bundled ownership so archived repos are not required by new installs.
- uCore snackbar extension/launcher metadata still references uCode2 and uCore-Publish; assess actual exposure and ownership before removal. Menu text still describes SnackMachine through old vocabulary.
- Human role implementation remains WordPress-compatible. Wizard/Sorcerer/Knight, Drone mediation and cloud publication restrictions are target contracts, not guaranteed runtime enforcement.
- Multiple READMEs retain old family names, retired repository links or stronger capability claims than source supports. Consolidate user instructions under uDos Documentation; retain language curriculum in uCode and restricted architecture/maintenance reference under Wizard authority.

## Recommended sequence

1. Preserve and reconcile Global Knowledge history/untracked content before broad corpus cleanup.
2. Review/publish the existing uCore sprint branch and record remote parity.
3. Correct cloud adapter false-success behavior and stale product/ownership descriptions.
4. Establish one extension disposition register for Google, Publish, Vector, SnackMachine and uCode2: owner, capability contract, dependencies, qualification, install/remove lifecycle and budget impact. Reuse existing registry; no new service tree.
5. Consolidate task-focused documentation using UDOS_DOCUMENTATION.md; record authority/provenance and redirect superseded pages.
6. Implement server-enforced roles, scoped Drone access, Beacon discovery and qualified publishing adapters. Keep optional products independent.
7. Consider additional remote archival only after dependency searches, history/assets preservation and tested replacements. No new repository is presently necessary for roles, Beacons, Drone or BitChat; start with existing uCore contracts and Sonic provisioning.

Sources: live authenticated GitHub repository metadata/default-branch API; local git status/log/remotes; repository READMEs; uCore integration references; uCore-Publish cloud adapter. Scope is fredporter's 20 returned repositories, not an organization-wide search or exhaustive dependency/security audit.
