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
