# uDos Documentation

Updated 2026-11-10. Owner: uCore documentation; workflow contracts belong to uFlow, language learning to uCode, media provisioning to Sonic Screwdriver. This index consolidates guidance without copying source corpora or creating another runtime store. Maintain it with product changes; remove superseded entries after their replacements are verified.

## Target role permission matrix

This is the agreed specification. The runtime still uses legacy WordPress-compatible roles and an Advanced display preference. These permissions require K09 backend enforcement and migration before they can be relied upon. Visibility is not authorization.

| Capability | Knight — regular user | Sorcerer — advanced user | Wizard — administrator |
| --- | --- | --- | --- |
| Missions, Binders, personal content, uCode, Sonic | Yes, owned/shared scopes | Yes, owned/shared scopes | Yes, administered scopes |
| Local Ollama | Yes | Yes | Yes |
| Direct external web/cloud access | No; request through an enrolled Drone | Yes, authorized providers | Yes, authorized providers |
| Cloud models, agents and APIs | No direct credentials or execution; scoped Drone service requests only | Yes, scoped and budgeted | Yes, including administration |
| Publish locally | Yes, owned materials | Yes | Yes |
| Publish to cloud | No; Drone cannot bypass this restriction | Yes, authorized destination | Yes, authorized destination |
| BitChat local messaging | Yes | Yes | Yes |
| Public uDos documentation and public Tombs | Read | Read | Read/curate |
| System administration, restricted system docs, open hood | No | No administrative grant | Full authorized access; software changes in external IDE |
| Read installed Global Knowledge | Yes | Yes | Yes |
| Curate canonical Global Knowledge/default datasets | Submit proposals only | Submit proposals only | Maintain/review canon and release editions |
| Grant/revoke human and device permissions | No | No | Yes |

“Full access” still respects host ownership, provider credentials and release verification. Installed canon remains immutable to ordinary runtime writes; Wizard updates use reviewed editions. Personal and Shared overlays remain separate. Sorcerer is canonical; historical Sorceror is a migration alias. WordPress administrator status must never automatically grant local Wizard authority.

## Resource and network profiles

These profiles describe resources or enrolled device/service principals, independently of the owner's human role.

| Profile | Contract |
| --- | --- |
| Tomb | Public resource: selected published collection, provenance, license, digest/version and offline reader. Public means explicitly released, not everything in a Vault. |
| Crypt | Encrypted Tomb: protected payload with established encryption, separate key access and recovery. Public metadata must not expose private titles, messages or keys. |
| Drone | Network access: enrolled gateway with narrow request scopes, isolated provider credentials, cost/time limits, audit history and revocation. It never inherits its owner's Wizard role. |
| Beacon | Opt-in presence/resource advertisement for a Tomb, Crypt or Drone. Announces supported capabilities and addresses; discovery alone establishes neither trust nor permission. |

Knight may use local BitChat/LAN messaging without being granted direct external web/cloud access. External requests cross a Drone boundary which checks the requesting identity, allowed operation and destination. Responses retain provenance. Offline failure stays explicit; there is no silent cloud fallback. A Drone's own network authority cannot elevate a Knight's publication or administration permissions.


Google Workspace offers a local Drone gateway for read-only Google Tasks previews. A Wizard signs in to a Google connection they own, selects a task list configured for all records, and grants one local profile access for a chosen duration. The recipient opens **Drone task access** in Google Workspace to preview the shared list. Previews are limited to 100 tasks and one request per minute per grant. A Wizard can revoke a grant, and disconnecting Google revokes the connection’s grants. The gateway checks expiry, account, scope and revocation before provider requests. Credentials stay in the server secret store.

Local Drone access relies on host-trusted profile switching. Remote Drone enrollment and live provider qualification remain open.

## BitChat and publishing flow

BitChat is a core messaging and networking surface. Current code supports LAN peer discovery/announcements and message WebSocket/polling flows. Beacon announcements are discovery, not proof of authenticated federation, BLE/LoRa delivery or encrypted messaging. Those transport/security guarantees need separate qualification.

Messages can be deliberately saved into a Binder or converted into a task. A peer message or Beacon never executes a skill, joins a Mission or publishes content automatically. Mission is the objective; Binder is the resulting collection. Preserve sender, source and review state when promoting a message into work.

Publishing follows: select owned Binder materials → compile a versioned artifact → preview provenance, licenses and privacy → explicitly release to a permitted destination → optionally advertise a Beacon. Knight can release locally and use Ollama. Sorcerer and Wizard can release to cloud through a qualified provider adapter. Canon submissions enter Wizard review separately from public publishing. Crypt encryption/key delivery is separate from publishing public discovery metadata.

Current local export/preparation is not cloud deployment: retired docs-publish and generic Git/shell execution endpoints stay retired. Role-aware cloud publishing requires a qualified adapter, account/destination preview, backend permission checks and an auditable result. No new capability is granted by this documentation tab.

## Consolidation register

Keep one user-facing uDos Documentation entry beside the uCode learning tab. Public usage guides belong here; restricted system operations remain Wizard-authorized. uCode retains language curriculum. The following bounded repository/archive scan identifies candidates, not permission to restore obsolete implementations.

| Source | Destination / treatment |
| --- | --- |
| uCore/docs/VAULT_BINDER_WORKFLOW_INTEGRATION.md | Missions and Binders guide; reconcile older project/folder terminology with objective → collection. |
| uCore/docs/UKNOWLEDGE_OFFLINE_LIBRARY_ARCHITECTURE.md; docs/plans/KNOWLEDGE_READER_ALIGNMENT_2026-11-09.md | Offline knowledge, Personal/Shared overlays and immutable canon; align with configured storage roots. |
| uCore/docs/UCORE_UCODE_ROLE_BOUNDARY.md | Wizard architecture reference; “role” here means product ownership, not human grants. Verify older runtime/dependency claims. |
| uCode/docs/learning-pathway/binders-and-publishing.md; specs/udo/udo-publish.md; specs/usxd/obf-publish.md | Compile/publish guide, local Beacon presentation and format references; reconcile historical family/repository names and role assumptions. |
| SonicScrewdriver/docs/REVIVAL-PLAN-2026-09.md | Hardware revival, standalone readers and capsule provisioning; current brief overrides older Tomb-as-public-or-encrypted wording. |
| ARCHIVED/DevStudio-2026-06-21/docs/specs/mission-control-proseui.md; docs/plans/mission-control-dev-plan.md | Recover Mission Control objectives, queue and Binder concepts; exclude old paths, coupling and obsolete execution. |
| ARCHIVED/DevStudio-2026-06-21/docs/specs/WEB3_CONVERGENCE_BRIEF.md | Historical BitChat/mesh/Sonic Beacon concepts; distinguish aspirational transports and crypto claims from tested features. |
| ARCHIVED/uConnect-2026-06-21/docs/GHOST_MODE.md; docs/course/lesson-1-markdown-grimoire.md | Review local-first messaging and starter Vault examples; discard fake identity and obsolete role grants. |
| ARCHIVED/DevStudio-2026-06-21/docs/NARRATOR.md | Terminology/glossary only; narrative substitution is not encryption. |
| ARCHIVED/DevStudio-2026-06-21/docs/specs/UDN-SONIC-V2-001.md; docs/UDN-ECOSYSTEM-001.md | Historical universal OS and ownership evidence; validate against native Apple Silicon/non-destructive USB doctrine. |
| uCore/backend/app/identity/wordpress_rbac.py; services/mesh_transport.py; api/bitchat_api.py; services/docs_publish.py | Implementation evidence for role migration, discovery, messaging and retired publishing. Source code is evidence, not a user tutorial. |

Consolidation order: inventory and mark authority/date → reconcile against this matrix → author task-focused guides → preserve provenance and redirect superseded pages → verify links, offline reading and capability enforcement. Do not bulk import archived docs into the canonical baseline. K09 covers roles/migration, K14 network/resource profiles, K15 BitChat, and F10 Mission attribution; these remain backlog work.
