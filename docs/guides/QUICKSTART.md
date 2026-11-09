# First-time setup and quickstart

Use this guide with an already running uCore installation. Open [User Setup](http://127.0.0.1:5175/setup). You can revisit it from Settings → User Setup Story.

## Make the workspace yours

1. Enter your name and email for the local profile.
2. Confirm the suggested city/region and country from the offline timezone catalogue. GPS is not requested.
3. Confirm the device timezone and choose a date format. Your operating system remains responsible for time and timezone.
4. Choose appearance and text size.
5. Choose a starting workspace and, optionally, a calmer-day, focus or learning starter. Starters add four editable tasks; they do not schedule automations.
6. Choose an installed local Ollama model, or continue without AI. Configure connections later in Settings → Apps.
7. Review and finish. Continue saves story progress; Do this later lets you return without completing the profile.

Profiles and drafts are local. Selected connected data is exchanged only after you configure and run/enable its connection.

## Connect a small collection first

For Google, complete [OAuth app setup](GOOGLE_OAUTH_SETUP.md) first. Then use Settings → Apps:

1. Add Apple or Add Google account. New connections begin disabled, with Tasks selected and no lists chosen.
2. Choose the collection types you want **before** Google sign-in. Adding types later may require signing in again to grant their scopes.
3. For Google, select Choose Google account and finish sign-in in your system browser. Return to uCore. For Apple, Choose lists and folders may request macOS access to the selected apps.
4. Choose lists and folders. Select one small test list/group and Pull into local collection. Use a named list/group as the main sync boundary; individual-record selection can narrow it further.
5. Save the connection. Run Sync now, then inspect its health and imported records.
6. Verify titles, completion state, dates and source links. Review possible duplicates and conflicting edits before combining them.
7. For a round-trip check, switch only that collection to Push and pull, save, edit one disposable test record locally, sync and verify it in the original app. Change it there and verify the next pull. Repeat sync once to check that no duplicate appears.
8. Once satisfied, enable Sync automatically and save. Broaden the selected lists deliberately.

Do not test with an important contact, calendar event or note. Keep the initial test collection disposable and easily identifiable. Choosing both Apple and Google does not automatically copy every record between accounts: records retain source links, and new cross-account sharing requires an explicit destination.

## Find your work

| Surface | Purpose |
| --- | --- |
| Workflow | Daily overview and next actions |
| Tasks | Local and imported tasks/reminders, organized into lists/groups |
| Snackbar → Contacts | Combined contacts with linked sources and duplicate review |
| Snackbar → Notes | Combined notes; open local Markdown in Editor |
| Snackbar → Feeds | Monitored sources, directions and activity; promote actionable items to tasks |
| Binder → Research | Gather findings and connect them to work |
| Workflow → Queue | Workflow runs and research jobs; broader app/sync aggregation is planned |
| Binder / Editor | Organize content and work on the selected task or document |
| Knowledge / uCode | Read local knowledge and follow the user guide |

Mail and calendar items remain records/feed activity unless explicitly promoted or covered by an opted-in automation. Colour flags are shared local metadata and can trigger the optional create-task rule. Stars and VIP remain distinct; Apple Contacts VIP filtering uses a group you explicitly choose.

## Apple permissions

Apple connection discovery uses the native apps on macOS. Grant only the app access you intend to use. If discovery fails, check macOS System Settings → Privacy & Security and the relevant Automation/app permissions for the process hosting uCore. The displayed process name can depend on how uCore was launched. Return to Connections and retry discovery after changing permissions; do not grant unrelated access.

Apple is a local adapter, not an OAuth login. iCloud account synchronization is managed by macOS and its apps. uCore does not sign into iCloud separately.

## Pause, disconnect and review

Disable Sync automatically to stop scheduled polling. Disconnect also removes that connection’s local account token; local records remain. Revoke access in your Google account separately if you want to remove the grant at Google. Review conflicts through Keep local, Use incoming or Combine values. Duplicate suggestions require explicit review; a matching title does not prove identity.

Current limits: provider deletions do not propagate; Google notes are uCore Markdown files in Drive rather than consumer Keep; rich Apple Notes/attachments are protected from plaintext replacement; Gmail supports import and read/star/flag changes, not sending. Background polling is bounded but does not yet use incremental cursors for every provider. See [implementation status](../plans/CONNECTIONS_AND_USER_SETUP_2026-11-09.md).

## Location and local seed data

The location step suggests a city and country once from the device's IANA timezone. It uses the host's offline `zone.tab` and `iso3166.tab` catalogue, with searchable country/city suggestions. These are timezone representative places, not a complete street-address directory. Saved answers, including intentionally cleared fields, are never replaced when resuming or when the device timezone changes.

uDOS represents location on grids. Choosing a listed place links its public seed point to a cell in an installed GridCore map using uCode's shared mapping functions. This is a place-seed reference, not measured GPS, a precise address, or a change to the device timezone. The profile stores the map ID/cell and selected place timezone; it does not store the representative latitude/longitude as a measured user location. Places outside installed map coverage are identified rather than assigned a fabricated cell.

The step also confirms that the Global Knowledge Library, canonical GridCore protocols, shared mapping implementation, map seeds and place catalogue are available. Expand Local seed data for details or Recheck after installing missing baseline material. Missing required data blocks this step; Do this later remains available. Checks are read-only and do not let a user setup form alter canonical knowledge or standards.
