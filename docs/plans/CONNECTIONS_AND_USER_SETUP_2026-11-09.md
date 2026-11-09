# Connections and User Setup implementation

uCore hosts profile-owned connections and the canonical local collection. uFlow remains the task-file authority. Workflow now brings together Tasks, Contacts, Notes, Feeds, Research, Binder and Editor. `/docs?tab=wiki` redirects to the existing documentation reader.

## First run

`/setup` refines the historical P100 User Setup reference (profile, preferences, workspace) using the existing StoryWizard and persisted identity-story contract. The archived onboarding document was developer installation guidance, not a complete end-user form.

Seven steps cover name, optional broad location, device timezone and date format, appearance/text size, starting workspace, optional accounts and review. Drafts resume per profile. Profile name/variables commit on Finish. Appearance stays in the existing Settings store. Home opens setup until completed or deferred; deep links remain usable. Settings includes User Setup Story to revisit it. No GPS request, clock daemon or OS timezone change is introduced.

## Provider setup

Google uses authorization code with PKCE, one-use state and loopback callback. Configure a desktop OAuth app through the existing server secret store using GOOGLE_OAUTH_CLIENT_ID/GOOGLE_OAUTH_CLIENT_SECRET (GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET aliases supported). Refresh tokens are encrypted and unique per connection; legacy global refresh tokens are not reused across users. Google app verification and enabled APIs remain deployment prerequisites. The user chooses their account in Google's sign-in and collections/lists/groups in uCore.

Apple uses native local permissions, not OAuth. Discovery and imports occur only through explicit setup/sync actions. Connections begin disabled. Existing scheduler polls enabled connections with bounds, backoff, profile isolation and actual health reporting; no additional service is installed.

Lists/groups are the primary selection boundary. Individual selection, stars, explicit Apple VIP groups and unified colour flags can further filter. Flags can opt into creating one linked task per source record. Google colour flags map to chosen custom Gmail labels; native Apple Mail supports one flag colour. Gmail imports metadata/body and flag/read updates, not message sending. Google notes are app-owned Markdown Drive files, not consumer Keep. Apple rich Notes/attachments are guarded against destructive plaintext replacement. Provider deletions are not propagated.

## Reconciliation

Stable replicas link provider IDs to local record IDs. Three-way field reconciliation preserves local-only fields and retains competing changes for explicit resolution. Duplicate candidates are suggestions, never automatic destructive merges; merge keeps alternative values and redirects replicas. Uncertain outbound creates are journalled and require linking/review before retry where provider idempotence is unavailable. Remote versions/ETags protect writes. Notes appear as editable Vault files; imported reminders/tasks appear in the uFlow task list. Mail/calendar are collection records projected into profile feeds; they become tasks through explicit promotion or opted-in flag rules.

## Ownership and removal

Connection database: settings.data_dir/connections.sqlite3. Identity stories: settings.udos_home/identity, profile-separated filenames. Editable notes: settings.vault_root/Connections/<profile hash>. Tasks: existing uFlow task root. Feed events: existing profile feed storage. Credentials: existing encrypted server SecretStore. Disable stops polling; Disconnect also removes the connection token while retaining local records. Removing these owners' data is an explicit user operation, not an automatic disconnect side effect.

## Validation and limits

Focused backend suite: 51 passed; existing identity-story contract: 7 passed. Frontend collection/workflow/documentation suite: 26 passed, plus setup draft-resume test. Production build/type-check and action inventory checked. Browser verified setup first step, Settings alignment, documentation alias and Workflow collection routes. No real account authorization, native permissions, remote writes or personal-profile completion were performed. Live Apple/Google end-to-end verification remains pending user account/list choices and OAuth app credentials. Bounded polling currently scans selected data; provider incremental cursor optimization remains future work.

Normal git-backed path-policy checking is blocked by the host Xcode licence state. The provided stdin policy scan passed for the complete path-owning sources. No commit was made.


## Advanced credential form and quickstart follow-up

Configuration now includes a dedicated Google OAuth form using a presence-only authenticated endpoint, encrypted writes, client-ID validation and accidental app-replacement protection. It never returns stored credential values. Blank secret preserves an existing secret; account tokens remain separate. Added first-time [quickstart](../guides/QUICKSTART.md) and [Google credential setup](../guides/GOOGLE_OAUTH_SETUP.md), verified against official Google documentation.

Live follow-up found AES-GCM unavailable in the currently shared Python environment. Added cryptography to backend package dependencies. The guided OAuth form blocks saving rather than accepting plaintext credentials. Existing nested venv symlinks resolve to Code/.venv, contrary to workspace ownership policy; repairing that environment and installing declared dependencies remains required before live sign-in. No shared environment was modified and no credentials were entered.


## Environment repair and release verification

The environment blocker is resolved: backend/.venv is now a real product-owned Python 3.12 environment with AES-GCM and platform-gated minimal Cocoa bindings. backend/uv.lock is committed. Setup uses an explicit uv target and bypasses stale interpreter metadata during rebuilds; runtime guards reject shared/system environments. Secret writes are atomic and fail closed, with verified encrypted migration of legacy plaintext. The backend LaunchAgent uses canonical paths and user-site isolation. Full Xcode and its specific support data were removed at the user's request; standalone Command Line Tools remain.

The old shared environment, empty pnpm store, outdated workspace configuration and recovery build directories were retired into Code/ARCHIVED/cleanup-2026-11-09 with a manifest. Active product repositories, Vendor, UDOS_HOME and user documents remain in place. An obsolete uServer scheduled launcher was disabled and archived.

The offline banner now distinguishes internet connectivity from local backend reachability. Local backend recovery triggers queued save retries even without a browser online event. Full backend suite: 710 passed; full frontend suite including connectivity checks: 129 passed. Production build/type-check, action inventory, whitespace and home-path policy checks passed. The local backend reports encrypted_storage=true. Live Google account authorization and Apple source permissions are still intentionally pending the user's setup choices.
