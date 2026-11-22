# Documentation ownership and publication

Edit product documentation in its owning repository. Publish reviewed snapshots through the edition pipeline.

| Material | Source |
| --- | --- |
| System setup, onboarding, workflow, Library and integration contracts | `uCore/docs/` |
| BASIC, GridCore, runtime contracts and hands-on learning | `uCode/docs/`, starting with `manual/README.md` and `learning-pathway/README.md` |
| Spatial and vector implementation | `uCodePlus/docs/` |
| Shared standards and reference knowledge | `global-knowledge`, with the installed Public copy serving readers |
| Edition compiler and publisher implementation | `uCorePub` |

The [docs mirror](handovers/PHASE11_DOCS_MIRROR_PUBLISHING_EVIDENCE_2026-08-14.md) copies selected source docs into `${UDOS_HOME}/docs-mirror/` for local reading and preview. The [edition publishing workflow](plans/EDITION_PUBLISHING_SPRINT_2026-11-11.md) selects and publishes reviewed content. Published output should carry its source path, revision and canonical destination. Apply editorial changes upstream and rebuild the edition. The Documentation reader uses the owning repositories directly. Put generated sites in the configured Public root under `doc-sites/`, where the static viewer discovers them.

## Legacy site review

An archived site manifest lists onboarding, a family learning path, wiki units, courses and reference pages. The local runtime mirror currently has uCore, uCode, uVector and Home Assistant entries. It does not establish the contents of the remote uDOS-docs repository.

When the remote checkout is available, inventory tracked pages, source metadata, generator inputs and assets at a recorded commit. For each page, compare its claims and examples with the owning source. Replace duplicates with links, port verified unique material to its owner, and retain historical drafts with their provenance. Review Pages workflows, custom domains and incoming links before freezing or archiving any publication. A generated site can remain a publication target if its content is rebuilt from the canonical sources.

## External development

Open the repository that owns the component, follow its workspace instructions,
and run its tests before integrating changes. uCore hosts the user-facing
surfaces and services, and uFlow owns tasks and workflows. uCode owns the base
runtime, while uCode+ owns spatial and vector development.

- [Storage and repository boundaries](ECOSYSTEM_STORAGE_ARCHITECTURE.md)
- [Workflow and Binder integration](VAULT_BINDER_WORKFLOW_INTEGRATION.md)
- [Extension registration](EXTENSION_REGISTRY_SPEC.md)
- [MCP setup](MCP_SETUP.md)

## Sprint 1A – Format Smith

- [Sprint 1A handover](handovers/ANTIGRAVITY_SPRINT_1A_FORMAT_SMITH.md) merged in [PR #49](https://github.com/fredporter/uCore/pull/49).
- [PR #48](https://github.com/fredporter/uCore/pull/48) merged the docs-mirror cleanup. The [Sprint 1A tag](https://github.com/fredporter/uCore/tree/sprint-1a-format-smith) records the original cleanup commit `c8e644b`.

## Sprint 1B – Format Smith

- [Sprint 1B handover](handovers/ANTIGRAVITY_SPRINT_1B_FORMAT_SMITH.md) and [PR #50](https://github.com/fredporter/uCore/pull/50) track the follow-up on `sprint/ok-assistant-format-smith-1b`.

## Sprint 1D – Format Smith

- [Sprint 1D handover](handovers/ANTIGRAVITY_SPRINT_1D_FORMAT_SMITH.md) merged in [PR #52](https://github.com/fredporter/uCore/pull/52).
