# Workspace capability audit — 2026-11-10

N03 source inventory. Owner: uCore connections subsystem; UI: Apps workspaces. This records implemented code, not live account/platform certification. No provider calls were made.

## Operation matrix

| Collection | Google direct-cloud source | Apple local-app source | Writable common fields |
| --- | --- | --- | --- |
| Tasks | Google Tasks | Reminders | title, body, completion status, due |
| Contacts | Google contacts adapter | Contacts groups | title, body, emails, phones; Google starred; Apple VIP group separately scoped |
| Notes | Drive text/Markdown adapter, not Keep | Notes folders | title, body; Google starred |
| Calendar | Calendar events | Calendar | title, body, start/end |
| Mail | Gmail messages | Mail inbox | Existing-message read/flag state only; Google starred. No send/copy/new message. |

Both adapters implement discovery, pull and restricted push paths. `representation` explicitly selects writable fields; this is not evidence of lossless native round trips. Recurrence, attachments, rich formatting and provider permission metadata require separate fixtures and qualification before promising preservation. No remote deletion capability is established by this audit. Browser bookmarks/reading lists use manual HTML exchange, separate from these native adapters.

Linux has no registered live provider: CollectionStore accepts only apple/google and SyncEngine registers those two. Apple availability requires Darwin and native app automation permission. Google availability metadata means the adapter exists, not that credentials, consent, role authorization or network access are ready. Linux may use qualified Google direct-cloud access; Evolution/Thunderbird native adapters remain unavailable.

## Identity and authority

`connections_api.profile` selects the authenticated active profile rather than a caller-supplied profile and restricts mutation origins to localhost. CollectionStore scopes connection lookup by profile. The engine maps native objects with a connection ID and kind-qualified remote ID, preserving per-connection replicas; display names alone are not identity. Shared combined records can have multiple replicas, so the combined collection must not be presented as a native account browser.

Current reviewed API gate authenticates the profile and checks mutation origin. It does not itself implement Wizard/Sorcerer/Knight or scoped Drone authorization. Trace all entry points, scheduler and OAuth callbacks before claiming role enforcement. Presentation preferences cannot authorize effects. Existing OS/provider consent remains necessary.

## Execution and lifecycle

SyncEngine uses a profile lock and bounded worker; cancellation waits for the worker because native calls cannot safely be killed. Failure/backoff and acknowledgement paths exist. These details do not establish safe retry after every partial remote mutation; qualify interrupted creates and conflict handling. Store permits pull/both directions, selected lists/records and explicit flag rules. Account mapping changes and cross-provider propagation require reviewed previews; avoid silently widening scope.

Reuse existing connection store, sync engine and uFlow execution contracts. No new store, daemon or scheduler is authorized by this inventory. Existing ownership must be traced for removal, credentials and retained replicas before claiming safe uninstall/disconnect.

## Next qualification

1. Add a server-derived per-operation capability contract rather than infer readiness from provider names.
2. Test two accounts with colliding native IDs, profile changes and replica provenance; do not silently choose an account for ambiguous links.
3. Audit role/Drone enforcement across manual sync, automatic sync, discovery, preview and OAuth.
4. Add field-loss fixtures and explicit unsupported-state UI before enabling native collection editing.
5. Qualify create/update acknowledgement, interrupted export, disconnect and recovery with disposable adapters before live account round trips.

Evidence: backend/app/api/connections_api.py; backend/app/services/connections/{store,engine,providers,apple,google_auth}.py. Existing tests: test_connection_providers.py, test_connection_collection.py, test_connections_api.py. This source plan has the existing sprint document lifecycle and no runtime storage impact.
