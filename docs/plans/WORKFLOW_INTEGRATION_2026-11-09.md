# Workflow, Tasks, Binder and Editor integration

Implemented 2026-11-09. Documentation-library frontmatter pills and the full-screen reader are a separate follow-up.

## Surface roles

- Workflow is an overview: next actionable task, list progress, binder summaries, and collapsed maintenance/history. It no longer repeats the task list or file-import workflow.
- Tasks defaults to List, with list/binder scope, groups, Open/Done/All filters, completion controls and optional Kanban or communications triage. The duplicate global Flowlog display and separate inline editor were removed. Communications are loaded only when triage is requested.
- Binder is the project content/workspace: brief, sources, assembly plan, decisions, draft and publications, plus related tasks. The title is now Project workspace. Draft editing uses the shared Editor; assembly steps remain distinct from user task records.
- Editor opens the selected task, binder draft/brief or file with its current location. It provides related-task previous/next navigation, completion and Done & next. Publishing a binder draft returns to its publication workflow. Directly opening an empty Editor no longer creates a fictional welcome task/file.

Tasks and binders remain different entities, connected through binder membership. Lists are task boards; groups are metadata within those lists. They share selection and navigation rather than maintaining separate editors or divergent task copies.

## Navigation and persistence

A shared WorkflowNavigator is used in the file picker and Editor workspace. It shows lists, binders, the current location and related tasks; brief/draft links appear only for registered project content. Existing task binder associations without project content can still be used as task collections. Editor navigation retains the selected task across tabs and updates the URL with task/list/binder/document/file context for reload.

Unsaved task/document text is retained in the session when switching items. It is not an autosave or a promise of draft recovery after closing/reloading the browser. Binder drafts keep the original base hash when reopened with unsaved changes, preserving concurrent-edit detection. File versions advance after successful saves.

New tasks, moves, groups, binder assignments and copies persist through uFlow's canonical Markdown storage. Task IDs survive filename/list/status changes. Copies have independent IDs, begin as To Do, and do not copy action-execution approvals. Native drag-and-drop uses the same persisted operations; Option/Alt or Control copies instead of moving. Explicit move/copy/group controls provide a non-drag alternative.

Empty task lists persist as board directories with a visible list.json user-scope marker. New binder creation from the file picker now opens the same project-binder form used by Workflow; the previous action only created a folder and README.

## Reliability fixes found during verification

- Task selection no longer loses to a previously opened file or gets cleared during Tasks → Editor navigation.
- Removed competing route updates and prevented late hydration from overwriting user navigation.
- YAML timestamps in existing task frontmatter are converted to ISO text for API serialization. This fixed an observed HTTP 500 on the live task-list endpoint.
- CORS preflight now includes PATCH and the existing explicit-confirmation header, allowing browser saves to reach their handlers.
- Indexed absolute user-file paths are accepted only within the owning workspace boundary. The picker opens canonical workspace paths with conflict-check versions. Incomplete previews and non-user sources remain read-only.
- Task-refresh failures are visible rather than appearing as an empty successful list.
- Completed work is available through the scoped Done filter. Superseded/cancelled/archived tasks are excluded from Open and remain available in All.

## Ownership, lifecycle and removal

uCore owns the UI and API host; uFlow remains the task authority. No service, container, agent configuration or scheduler was added. Task/list state remains beneath the owning settings-resolved task root (normally UDOS_HOME/flow/tasks). Group and binder membership live in the task's YAML properties. A list marker is a small JSON file in its board directory; an empty list can be removed by removing its marker and empty directory after checking it contains no tasks. User documents remain in the existing workspace/Vault. UI drafts and navigation are in-memory and end with the browser session. No canonical global-knowledge data was modified.

Legacy ordinary folders are still files/folders, not silently converted into project binders. They remain accessible in Files. The live project-binder index was empty during verification, so binder document handoff was verified using isolated component/store tests rather than creating or rewriting user binders.

## Verification

- 37 backend tests passed across task organization, tasker autonomy/storage, background recovery and bounded workspace-file operations.
- 12 frontend tests passed across shared task context, drag move/copy transports, draft/hash retention, Editor Save/navigation, binder handoff/creation intent and repeated file-save version updates.
- Frontend type checking and production build passed. The build still reports large editor/diagram bundles.
- Static action inventory: 827 controls/event bindings, zero missing bindings and zero unresolved simple handler references.
- Live browser: real task loading, list view, task → Editor, keyboard next-task navigation, picker location/related work and Binder naming were checked. The native browser's active comment overlay intercepted some pointer clicks; keyboard activation verified those controls without changing the user's comment mode.
- Production task API returned 37 existing records after the timestamp fix. No real tasks were moved/copied/completed and no user binder was created merely for QA; mutation round-trips used isolated test directories.
- Ruff passed on changed backend modules/tests.
- The normal Git-based home-path policy check remains blocked by the unaccepted Xcode licence. The checker's supported --diff-stdin mode passed against all lines of the touched path-owning modules. No commit was attempted.
