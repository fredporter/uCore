# Documentation mirror inventory

Public uDOS Docs snapshot: `203b65349258704953c4bc7aaf5365e2c7a1dee4`. The full Git checkout was copied into the workspace archive and verified against the source.

| Location | Markdown | Exact matches in repository sources | Non-identical |
| --- | ---: | ---: | ---: |
| Published docs | 185 | 125 | 60 |
| Public local runtime | 21 | 0 | 21 |
| Installed Global Knowledge | 496 | 492 | 4 |
| Shared seed | 1 | 0 | 1 |

Counts compare exact bytes across uCore, uCode, uCodePlus and Global Knowledge. A non-match can be an older revision, a reformatted copy, or distinct content. The installed Global Knowledge collection is a live reader source. Shared contains user resources and fixtures.

## Published Markdown dispositions

All 60 non-identical pages in the comparison queue are mapped below. The archived
checkout keeps all original revisions, companion HTML, assets, and Git history.
Counts above are from the initial inventory.

| Published page | Destination | Disposition |
| --- | --- | --- |
| `README.md` | uCore/docs/DOCUMENTATION_OWNERSHIP.md | Replaced site index with ownership guide |
| `learning/README.md` | uCode/docs/README.md; uCode/docs/tutorials/ | Both linked lessons match the repo byte for byte |
| `uCode/AI_INTEGRATION.md` | uCore/docs/FEATURE_SPEC_OPENROUTER_ASK_PLAN_ACT.md | Old provider setup and Hivemind architecture retained in snapshot |
| `uCode/DEV_PLAN.md` | uCode/docs/archive/DEV_PLAN.md | Historical planning revision |
| `uCode/GRIDUI_RENDERING_CONTRACT.md` | uCode/docs/GRIDUI_RENDERING_CONTRACT.md | Use repository revision; retain published revision in snapshot |
| `uCode/HANDOVER_CLINE_EXTENDED_WORK_2026-07-08.md` | Archived snapshot | Dated Cline backlog |
| `uCode/INTEGRATION.md` | uCode/docs/INTEGRATION.md | Current integration contract replaces old Hivemind and network examples |
| `uCode/README.md` | uCode/docs/README.md | Use repository revision; retain published revision in snapshot |
| `uCode/UCODE_REPO_BOUNDARY.md` | uCode/docs/UCODE_REPO_BOUNDARY.md | Use repository revision; retain published revision in snapshot |
| `uCode/UCODE_RUNTIME_SPEC.md` | uCode/docs/UCODE_RUNTIME_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCode/basic/CLI_README.md` | uCode/docs/basic/CLI_README.md | Use repository revision; retain published revision in snapshot |
| `uCode/basic/QUICK_START.md` | uCode/docs/basic/QUICK_START.md | Use repository revision; retain published revision in snapshot |
| `uCode/basic/README.md` | uCode/docs/basic/README.md | Use repository revision; retain published revision in snapshot |
| `uCode/learning-pathway/05-skills-framework.md` | uCode/docs/learning-pathway/05-skills-framework.md | Use repository revision; retain published revision in snapshot |
| `uCode/learning-pathway/README.md` | uCode/docs/learning-pathway/README.md; SonicScrewdriver/docs/manual/ | Current learning index and separate hardware manual replace the old course index |
| `uCode/learning-pathway/course-hooks-and-onboarding.md` | uCode/docs/learning-pathway/course-hooks-and-onboarding.md | Use repository revision; retain published revision in snapshot |
| `uCode/spatial/GRID_ALGEBRA_ARCHITECTURE.md` | uCode/docs/spatial/GRID_ALGEBRA_ARCHITECTURE.md | Use repository revision; retain published revision in snapshot |
| `uCode/specs/SKILLS_FRAMEWORK.md` | uCode/docs/specs/SKILLS_FRAMEWORK.md | Use repository revision; retain published revision in snapshot |
| `uCode/specs/UCODE_ADAPTATION_STRATEGY.md` | uCode/docs/specs/UCODE_ADAPTATION_STRATEGY.md | Use repository revision; retain published revision in snapshot |
| `uCode/specs/UCODE_USER_MANUAL_DEV_AGENT_PROMPT.md` | uCode/docs/specs/UCODE_USER_MANUAL_DEV_AGENT_PROMPT.md | Use repository revision; retain published revision in snapshot |
| `uCode/specs/UDOS_MAPPING_SPEC.md` | uCode/docs/specs/UDOS_MAPPING_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCode/tutorials/AGENT_GUIDE.md` | uCode/docs/tutorials/AGENT_GUIDE.md | Use repository revision; retain published revision in snapshot |
| `uCode/tutorials/lesson_04.md` | uCode/docs/tutorials/lesson_04.md | Use repository revision; retain published revision in snapshot |
| `uCore/CLINE_GITHUB_WORKFLOWS.md` | Archived snapshot | Retired Cline procedures |
| `uCore/CONSOLIDATION_PLAN.md` | uCore/docs/CONSOLIDATION_PLAN.md | Use repository revision; retain published revision in snapshot |
| `uCore/DEVELOPER_SURFACE.md` | uCore/docs/DEVELOPER_SURFACE.md | Use repository revision; retain published revision in snapshot |
| `uCore/DEVMODE_CODE_ANALYSIS_SKILLS.md` | Archived snapshot | Retired DevMode tool design |
| `uCore/DOCLANG_BRIDGE_EXPORT_SPEC.md` | uCore/docs/DOCLANG_BRIDGE_EXPORT_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCore/EXTENSION_REGISTRY_SPEC.md` | uCore/docs/EXTENSION_REGISTRY_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCore/EXTERNAL_DEVELOPMENT.md` | uCore/docs/DOCUMENTATION_OWNERSHIP.md | Absorbed repository ownership and verified pointers |
| `uCore/FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md` | uCore/docs/archive/superseded-development-2026-09-12/FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md | Historical UI design |
| `uCore/FEATURE_SPEC_CONTROL_PANEL_AND_AGENTIC_EXECUTION.md` | Archived snapshot | Historical Control Panel architecture |
| `uCore/FEATURE_SPEC_OPENROUTER_ASK_PLAN_ACT.md` | uCore/docs/FEATURE_SPEC_OPENROUTER_ASK_PLAN_ACT.md | Use repository revision; retain published revision in snapshot |
| `uCore/FEED_SYSTEM_SPEC.md` | uCore/docs/FEED_SYSTEM_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCore/GRIDUI_RENDERING_CONTRACT.md` | uCore/docs/GRIDUI_RENDERING_CONTRACT.md | Use repository revision; retain published revision in snapshot |
| `uCore/GRIDUI_RENDERING_CONTRACT_v3.md` | uCore/docs/GRIDUI_RENDERING_CONTRACT_v3.md | Use repository revision; retain published revision in snapshot |
| `uCore/MCP_SETUP.md` | uCore/docs/MCP_SETUP.md | Use repository revision; retain published revision in snapshot |
| `uCore/MENUBAR_UNIFICATION_PLAN.md` | uCore/docs/archive/MENUBAR_UNIFICATION_PLAN.md | Historical plan |
| `uCore/PLATES_SYSTEM_SPEC.md` | uCore/docs/archive/PLATES_SYSTEM_SPEC.md; uCore/docs/VAULT_PLATES_AND_DESTROY_SPEC.md | Historical revision and current Vault plate boundary |
| `uCore/README.md` | uCore/docs/README.md | Use repository revision; retain published revision in snapshot |
| `uCore/RELIABILITY_SINGLE_PATH_POLICY.md` | uCore/docs/RELIABILITY_SINGLE_PATH_POLICY.md | Use repository revision; retain published revision in snapshot |
| `uCore/SETTINGS_ARCHITECTURE_2026.md` | uCore/docs/SETTINGS_ARCHITECTURE_2026.md | Use repository revision; retain published revision in snapshot |
| `uCore/SNACKS_SKILLS_STATUS_AUDIT.md` | uCore/docs/archive/SKILLS_AUDIT_2026-08-18.md | Dated inventory retained in snapshot |
| `uCore/SNACKS_SYSTEM_SPEC.md` | uCore/docs/SNACKS_SYSTEM_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCore/SPOOL_SPEC.md` | uCore/docs/SPOOL_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCore/USER_SETUP_VAULT_MCP_WORKSPACES.md` | uCore/docs/USER_SETUP_VAULT_MCP_WORKSPACES.md | Use repository revision; retain published revision in snapshot |
| `uCore/USX_SURFACE_BASELINE_SPEC.md` | uCore/docs/USX_SURFACE_BASELINE_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCore/mcp-diagnostics.md` | uCore/docs/MCP_SETUP.md | Prototype route retained in snapshot |
| `uCore/mcp-policy.md` | uCore/docs/mcp-policy.md | Use repository revision; retain published revision in snapshot |
| `uCore/specs/ECOSYSTEM_EXTENDED_DEV_FLOW_2026-07-31.md` | uCore/docs/archive/ECOSYSTEM_EXTENDED_DEV_FLOW_2026-07-31.md | Historical execution lanes |
| `uCore/specs/GRIDCORE_VARIABLEIZATION_SPEC.md` | uCore/docs/specs/GRIDCORE_VARIABLEIZATION_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uCore/specs/KNOWLEDGE_LAYERING_AND_CONTRIBUTION_SPEC.md` | global-knowledge/KNOWLEDGE_LAYERING_AND_CONTRIBUTION_SPEC.md | Canon owns overlay and contribution rules |
| `uCore/specs/UDEV_BINDER_COMPILER_INTEGRATION_CHECKLIST_2026-08.md` | uCore/docs/VAULT_BINDER_WORKFLOW_INTEGRATION.md | Historic uDev checklist retained in snapshot |
| `uCore/specs/WISDOM_SYSTEM.md` | uCore/docs/specs/WISDOM_SYSTEM.md | Use repository revision; retain published revision in snapshot |
| `uCore/tech/devices/README.md` | global-knowledge/tech/devices/README.md | Use repository revision; retain published revision in snapshot |
| `uCore/tech/devices/meshcore.md` | global-knowledge/tech/devices/meshcore.md | Use repository revision; retain published revision in snapshot |
| `uCore/templates/fieldnotes.md` | uCore/docs/templates/fieldnotes.md | Use repository revision; retain published revision in snapshot |
| `uCore/templates/wisdom.md` | uCore/docs/templates/wisdom.md | Use repository revision; retain published revision in snapshot |
| `uVector/INTEGRATION_SPEC.md` | uCodePlus/docs/INTEGRATION_SPEC.md | Use repository revision; retain published revision in snapshot |
| `uVector/NANO_BANANA_UVECTOR_SUMMARY.md` | uCodePlus/docs/NANO_BANANA_UVECTOR_SUMMARY.md | Use repository revision; retain published revision in snapshot |

## Retirement status

- Wiki articles and course content read repository sources. Generated editions are served from the configured Public root under `doc-sites/`.
- Public Global Knowledge remains an installed reader source. The three installed-only standards were copied to the Global Knowledge repo. The revised bank README and unrelated runtime and Shared seed material remain separate.
- Verify fresh remote refs and GitHub Pages settings before archiving the remote. The cached remote tip matches the verified local snapshot.

## Remote verification

- Repository URL: https://github.com/fredporter/udos-docs
- Latest commit SHA (main): 203b65349258704953c4bc7aaf5365e2c7a1dee4
- GitHub Pages: not enabled (no Pages configuration found)

**Cleanup action**: The old checkout `~/Public/udos-docs` remains on disk but this session has read‑only access to `~/Public`. Please delete it locally (e.g., `rm -rf ~/Public/udos-docs`) before archiving.
