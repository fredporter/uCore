# Workspace and vault organisation proposal — 2026-11-10

Status: accepted direction; implementation and adapter qualification pending, extending the curated-applications programme. No live vaults, accounts or collections were migrated. This proposal supersedes the earlier direction to make Snackbar the user-facing home of connected collections and sync management.

## Repository and surface organisation

Keep existing repository locations and independent product histories. uCore owns shell surfaces, identity, resource registry and bundled uFlow execution. uCode owns language learning/runtime. Sonic owns media/device provisioning. global-knowledge owns canonical content/standards source and editions. uCore-Google remains an optional Google adapter owner; uCore-Publish owns edition compilation/publication adapters; uVector remains an optional conversion engine. HomeNest and Groovebox remain independent products. Review SnackMachine packaging overlap and uCode2 scope before any archival.

No new Apple Workspace, Drone, Beacon, BitChat or vault-management repository is needed now. Start Apple surface/host adapters inside uCore's existing connection contracts. Extract a package only if independent distribution/maintenance makes the boundary worthwhile. Do not create another identity database, task engine, agent tree, sync scheduler or environment.

| Surface | User purpose | Authority |
| --- | --- | --- |
| Mission Control | What would you like to do today? Objectives, selected task links and Queue | uFlow owns local mission work; external objects stay provider-owned |
| Binders / Vault browser | Author, collect, research and organise materials | Existing file/resource contracts and shared reader/editor |
| Google Workspace | Account-scoped Google collections, native organisation and sync status | Google adapter; scoped provider grants |
| Apple Workspace | Account/device-scoped Apple collections, native organisation and sync status | Host/native app adapters; explicit app permissions |
| Snackbar | Find/run/schedule Snacks and inspect their outcomes | Existing governed skill/recipe contracts and uFlow Queue |
| uDos Documentation | Everyday guides and role-appropriate system reference | Product documentation; uCode learning remains adjacent |
| Knowledge | Read canonical references plus Shared/Personal overlays | Installed immutable baseline and governed overlays |

Adapt existing Google Studio to Google Workspace, preserving route aliases. Add Apple Workspace with the same shared collection components but provider-specific semantics. Remove Tasks/Contacts/Notes and provider collection dashboards from Snackbar only after destination routes work. Old collection deep links must route to a source/account chooser when their destination is ambiguous; never silently pick an account. Preserve sync service API compatibility during migration.

## Native workspace collections

Both workspaces should offer Overview, Tasks/Reminders, Contacts, Notes/Docs, Links, Calendar and Mail where a qualified adapter exists. Use each ecosystem's vocabulary: task lists versus reminder lists, document folders versus note folders, stars versus flags/favourites. Preserve ordering, parent/list identities, memberships, recurring rules, time zones, completion state, attachments, native URLs and provider fields. A shared renderer is not a lossy shared schema.

Every resource key includes provider, account, collection and native ID. Same-title documents, contacts and lists across accounts are distinct. Keep supported raw provider metadata alongside a minimal common envelope. A link/bookmark collection may be local-only, import-only or unavailable depending on its app adapter; show that state clearly. No promise that a single Google or Apple API covers all these apps. Start read-only; qualify read/create/update/delete independently per collection and platform.

Apple Workspace uses the host's existing account/app synchronisation. Do not add an independent iCloud sync daemon or read arbitrary app databases as a substitute for a supported adapter. Linux exposes only qualified transports/import/export, otherwise unavailable. Google Workspace includes personal versus organisational accounts without assuming identical permissions or administrator access.

Selecting an external task for a Mission creates a reference/link with provenance, not a duplicate authoritative task. Explicit 'create local task' is a separate conversion with its own ID. Completion propagation, if supported, must be configured and confirmed by remote acknowledgement; local success cannot imply remote success. Imported Docs/Notes can become Binder materials through an explicit snapshot/export operation retaining native URL, source ID, version and capture date.

## Keep the three document roots; tighten their meaning

| Root | Meaning | Guard against drift |
| --- | --- | --- |
| Vault | Personal authored content, private Binders and deliberate imports | One primary file for each authored object; explicit import/update policy |
| Shared | Explicitly shared/community collections with named owners and grants | No automatic cross-account copying or public escalation |
| Public | Selected publication editions and installed reference content | Distinguish user releases from immutable global-knowledge; no raw private intake |

Resolve all roots from existing settings. A root is a storage/access boundary, not proof that a folder has actually been shared or published. Preserve additional vaults only when registered with owner, scope, purpose and lifecycle. Do not create a second Google vault, Apple vault, task vault or working copy for each surface. Provider grouping is a view unless a user explicitly creates an import destination.

Cloud/native systems remain authoritative for their own objects. The vault is authoritative for local authored documents. Canon source is authoritative for released Global Knowledge; the installed baseline is read-only. A source can have a derived snapshot or publication edition, but the relationship and version must be explicit. Binders collect references and selected local materials without relocating every original.

## Drift controls

Extend existing profile/connection/resource metadata, not another registry database:

- Stable document IDs and provider-qualified resource keys; track moves/aliases, versions, source and content hashes. IDs survive path changes.
- One authoritative source per object/field group. Explicit link, import snapshot, export and sync modes; no implicit bidirectional mirroring.
- Register sync mappings with account, collection, direction, destination, exclusions and permission scope. Prevent loops with origin/version markers and idempotent jobs.
- Detect concurrent edits and stage a conflict for review. No blanket last-write-wins, cross-account merge, or deletion propagation. Use deletion markers, preview, retention and recovery.
- Keep provider fetch caches/indexes and run logs under existing settings-resolved runtime state with documented retention/size budgets. No sole copy of accepted user content there; disposable caches can be rebuilt. Disconnect revokes credentials, stops jobs and offers explicit cached-data cleanup; retained imports remain user documents.
- Use a governed inventory Snack to report unregistered roots, broken links, duplicate IDs, stale imports, schema mismatches, orphaned attachments, conflicting mappings and attempted canon writes. Reporting never silently rewrites a vault.
- Normalisation/cleanup is a separate previewed migration with original hashes, link redirects, collision handling, rollback and user-selected scope. Never deduplicate on title alone or automatically publish an intake folder.

## Snacks, roles and sync

Workspace Sync/Refresh actions invoke scoped Snacks through the existing connection engine/uFlow Queue. Snackbar exposes those same Snacks for schedules, retries and logs, without owning another collection browser. Provider surfaces show last successful contact, pending local work, conflicts, stale/offline data and unsupported operations. No duplicate poller or scheduler per surface.

Knight can inspect local/native content permitted by the host and use Ollama. uDos-originated external requests require an enrolled Drone; local host app data already synchronised by macOS is not a new direct-cloud grant. Remote writes through uDos must still respect the Knight role, including no cloud publication. Sorcerer can authorise direct web/cloud providers and scoped agents/APIs; Wizard administers grants, diagnostics and canon maintenance. Merely opening a Workspace or toggling Advanced grants nothing. Provider authorisation and native OS permissions remain necessary for all roles.

Google and Apple both remain visible as ordinary workspace entry points; each operation communicates connected/read-only/offline/Drone-required/unsupported states. Secrets stay in the owning credential facilities. Shared caches must never leak one profile/account's data to another.

## Ordered delivery gates

| Ticket | Work | Exit evidence |
| --- | --- | --- |
| W01 | Read-only vault/account/collection and mapping inventory | Report owners, authority, duplicates, drift and unsupported adapters; no user-data writes |
| W02 | Provider-qualified resource contract and operation capability matrix | Account isolation, native metadata round-trip, collision/conflict fixtures; no fabricated sync success |
| W03 | Google and Apple dedicated read-only surfaces | Shared UI; native collection grouping; offline/platform states; migrated deep links; Snackbar collection tabs removed after parity |
| W04 | Sync Snacks and permission enforcement | One existing execution/sync path, cancellation/retry/idempotency; direct/Drone role checks; no hidden fallback |
| W05 | Mission/Binder linking and selected imports | References preserve native identity; import provenance; no duplicate task authority or automatic completion writes |
| W06 | Selected vault normalisation and publication workflow | Dry-run and rollback; preserve IDs/links/originals; public selection separate from cloud publication and canon review |

W01 and W02 are foundation work. W03 starts in the curated-application slice; W04 depends on K09/Drone qualification for network effects; W05 shares F10 Mission attribution; W06 uses K10/K12 curation and K03 edition contracts. Existing live round-trip/platform qualification remains open. First migrate one disposable provider collection into a read-only workspace, then one explicit import into a test Binder before touching live vault structure.

## Accepted interaction model: universal compatibility layer

Users may connect Google, Apple, or both to their personal uDos workspace/vault. Their personal workspace is the sovereign local environment, not a third cloud account. Native provider collections remain separately browsable; selected items or whole lists/collections can participate in explicit sync mappings. A whole-account scope is optional and must enumerate included collection types; it is never the default.

Provide one shared **Sync with my vault** flow from either Workspace:

1. **Choose what:** selected items, a list/folder/collection, or explicitly selected supported account collections. Show the account and selection count. New items enter sync automatically only when the user chose a continuing collection scope.
2. **Choose where:** suggest an existing personal workspace/Binder destination; permit an authorised alternative. Linking to an existing local collection avoids parallel copies. Shared/Public requires a separate deliberate sharing/publication choice, not a default sync target.
3. **Choose how:** **Bring into my vault**, **Send from my vault**, or **Keep both updated**. Offer only directions qualified for the selected collection. Explain whether this is a one-time copy or continuing sync; unsupported formats can use an explicitly labelled snapshot/export.
4. **Review and connect:** show creates/updates, destination, schedule, permissions and any unsupported fields. Never silently enable deletes, merge contacts or grant cloud publication. The first operation must have a reviewable preview.

After setup, a compact **Connected collections** list shows source/account, destination, direction, last successful sync, pending changes and conflicts. Primary controls are **Sync now**, **Change selection**, **Pause** and **Disconnect**. Scheduling uses the same Snack under the existing scheduler. Technical identifiers and logs belong in expandable details, not the primary setup flow.

Two-way sync is an explicit supported option, not the default meaning of connecting an account. If several accounts connect to the same local collection, require an explicit mapping and conflict policy. Never automatically fan an Apple item into Google or vice versa. An intentional cross-provider bridge uses the selected local collection and qualified directional mappings, with duplicate/loop prevention and a clear preview of which accounts receive changes. Public publishing remains a separate role-gated action; ordinary private cloud collection sync must not be conflated with publishing.

Use shared common fields for interoperability while preserving provider-specific fields and relationships. Show **Needs review** for unrepresentable changes; do not silently discard recurrence, formatting, attachments, list membership or permissions. Resolve conflicts with **Keep mine**, **Keep provider version**, or supported reviewed merge, retaining recovery history. Default remote deletions to review; Disconnect stops future exchange without deleting originals or retained vault content. Changing a mapping must preview its effect on already-connected items.

The user sees a universal compatibility layer with consistent controls and truthful limits, rather than adapter internals. Provider-native identity, authoritative-source mappings, Drone/role checks, OS consent and offline state stay behind that simple flow. First acceptance demonstration: connect a test Google list and a test Apple list independently to selected personal destinations; verify selection changes, one supported two-way round trip, offline recovery, no cross-account leakage, and safe disconnect. Unsupported directions remain visibly unavailable.
