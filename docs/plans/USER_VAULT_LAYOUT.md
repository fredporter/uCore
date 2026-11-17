# User Vault layout

17 November 2026. Seed layout and migration record.

## Root layout

| Entry | Purpose | Seed behavior |
| --- | --- | --- |
| `Memory/` | System-managed documents, captures, exports, and history | Create once as a collapsed section |
| `Sandbox/` | Permanent space for drafts, experiments, and unassigned work | Create once as an ordinary folder |
| `<Binder name>/` | User-created projects and their documents | Create at the Vault root when a user creates a Binder |

Root documents belong in a Binder, Sandbox, or a designated system folder.
Put starter orientation in Sandbox. Within Memory, use Intake, Activity,
Reference, Workflow, Personal, Files, and Exports for documents that need
a durable place outside a Binder. Keep capture accessible through the Inbox
action. Create Memory subfolders on first use.

A Binder is a root folder with a valid Binder record. A plain folder remains a
plain folder. Reserve the Sandbox name for the permanent folder. Use the
unassigned task view for work without a Binder. Draft imports without a Binder
may go into Sandbox without putting a Binder ID in their metadata. Show Sandbox
even when it is empty and keep it out of the Binder picker. Use existing uDOS
profile scoping for workflow records and the configured User Vault for files.

## Memory collections

| Collection | Contents |
| --- | --- |
| `Memory/Activity/` | Host activity journal in `Activity/`, dispatches and contribution bundles in `Transport/`, syndicated copies in `feeds/` |
| `Memory/Intake/` | Inbox captures and byte-preserved intake originals |
| `Memory/Reference/` | Personal knowledge overlays, research notes, and retained policy documents |
| `Memory/Workflow/` | Portable task and Mission documents, templates, scripts, recovery tombs, and historical Binders |
| `Memory/Personal/` | Daily notes, journals, people, and personal collections |
| `Memory/Files/` | Attachments and processed documents |
| `Memory/Exports/` | Jekyll and web exports, and DocLang exports |
| `Memory/Archive/` | Retired collections retained for reference |

Live task boards, Mission records, indexes, and service logs remain under
`UDOS_HOME`. The copies in Memory are user-visible documents and exports.
Raw Originals remain inspectable on disk and outside ordinary browsing.
The platform may also keep application-owned settings at the Vault root.

## Migration record

The workstation migration on 17 November 2026 moved the two active Binders
to the root and the two loose documents into Sandbox and Memory. The follow-up
moved the legacy collections under Memory, preserved the old Binder tree under
`Memory/Workflow/Legacy Binders/`, and moved the retired Sandbox Binder's
working documents to `Sandbox/Legacy Binder Docs/`. Fourteen tasks and one
Mission retain their existing IDs and now have no Binder assignment.

The follow-up archive groups the legacy Binder records, their working
documents, and the `m` and `my-binder` folders under
`Memory/Archive/Archived Binders/`. Transport records and contribution
bundles live under `Memory/Activity/Transport/`.

The migration verified destinations before moving files. Retain the move
ledger, prior task files, and Mission database snapshot under the runtime home
for rollback. Rebuild the local library index after any further manual moves.

## Read-only migration preview

From the uCore checkout, run:

```sh
PYTHONPATH=backend backend/.venv/bin/python scripts/preview_user_vault_migration.py
```

The report lists proposed moves, collisions, legacy entries for review,
loose documents, proposed Memory destinations, Sandbox assignments, and
candidate Markdown link locations. Memory candidates require owner review
to distinguish durable documents from generated service state.
It uses the configured Vault and workflow storage and does not apply moves.
Link candidates cover explicit legacy paths and Sandbox wiki links. External
bookmarks and unresolved relative links need a separate check.
