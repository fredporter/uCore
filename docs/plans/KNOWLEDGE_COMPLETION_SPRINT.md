# Global Knowledge and User Vault completion sprint

Status: notebook round closed on 16 November 2026. Release qualification remains open. Scope and acceptance follow the
[universal intake and feeds plan](UNIVERSAL_KNOWLEDGE_INTAKE_AND_FEEDS.md#completion-gate).
The sprint targets a qualifying Core edition and User Vault seed, followed
by a production release decision based on the resulting evidence.

The starting point is a two-article Markdown package with three feed
formats, a four-value seed evidence audit, a common Binder intake
format and fixture tests for feed replay and publisher edits. The next
build must bring the reviewed content, data, seed layout and reader
together from clean inputs.

| Order | Owner | Work | Exit evidence |
| --- | --- | --- | --- |
| K1 | Global Knowledge maintainer | Define the Core scope and reconcile the historical inventory. Select its topic entry points, reviewed articles, standards and seed datasets. Record what belongs in the edition and the disposition of the remaining material. | Every selected item has a stable ID or dataset key, source, reuse basis, review status and digest. Every historical inventory entry has a disposition. Links in the edition resolve. |
| K2 | uCore-Publish and uKnowledge | Extend the package manifest to include reviewed standards and JSON datasets. Keep the edition, catalog and three feeds tied to the same revision set. | Two builds from the same inputs have matching manifests and file digests. Changed bytes and unapproved inputs are rejected or excluded as appropriate. Seed data passes exact-value and consumer checks. |
| K3 | uCore and uFlow | Render the User Vault seed with the existing seeding path. Reconcile the starter Binder with the runtime Binder layout and provide a migration preview for existing vaults. | Seed an empty disposable vault twice. The starter Binder opens through Workflow. User edits survive the second run. The preview reports retained paths, proposed moves and collisions, including case-sensitive and case-insensitive fixtures. |
| K4 | uCore and uKnowledge | Qualify the universal formatter and shared review flow with a local file, a capture and a saved feed entry. Agree the frontmatter schema and initial taxonomy for the edition and starter vault. | Formatting twice produces identical bytes. UIDs, authored fields, tags and links survive. Retry and revision checks pass. Vault and Shared overlays resolve in order and their content stays outside the public export. |
| K5 | uCore and uCore-Publish | Install the package into a disposable Public root and exercise the seeded User Vault through uCore. Qualify staging delivery and recovery using the reviewed release candidate. | Browser walkthrough covers article navigation, seed browsing, Binder intake, overlay precedence and offline reading. All three feeds re-import. The release record includes source revisions, package digest, staging results and a tested recovery procedure. |

K1 supplies the manifest inputs for K2. K3 and K4 can start with
disposable fixtures while K1 is in review. K5 starts when K2–K4 pass.
Use the existing uFlow and uKnowledge contracts for runtime work. Keep
scratch installs disposable and use the existing product environments.

Start K1 with the checked-in navigation drafts and seed evidence.
The four verified conversion fields qualify as evidence for those fields.
Select a bounded seed dataset or verify the remaining fields before
including the full installed data file. Start K3 by comparing the seed
plate's starter Binder paths with the Binder engine's directory and ID
rules.

Close the completion gate when the organised Global Knowledge package
and User Vault seed both pass K1–K5, with evidence attached to the
release record. Track live scheduled feed retrieval separately unless
the release enables subscriptions. Record any excluded topics and
deferred features in the edition scope.

## Execution checkpoint

K1 and K3 are in progress. The [Core scope](../../../global-knowledge/research/core-scope.md)
selects the two navigation drafts and a standalone JSON dataset with
the four verified length factors. Remaining recovered paths are held
for selective review.

Workflow seed now uses the existing Binder engine for Sandbox and
reports recognised legacy starter files as retained, conflicting or
candidates for a move. A move candidate leaves the destination available.
The focused seed test covers first run, repeat run and legacy conflict
in a disposable vault. Full plate rendering, a complete existing-vault
migration preview and cross-platform qualification remain open.


K2 now packages approved JSON datasets from the optional `datasets`
manifest list. Each dataset uses `path`, `sha256`, `visibility` and
`review_status`. The compiler validates the JSON and pins its original
bytes. RSS, Atom and JSON Feed contain the article entries.

Two fixture builds produced identical files. A disposable Core package
built from the real navigation and length-conversion evidence was read
through uCore's documentation content loader. All three feeds parsed
back with two articles, and Workflow created Sandbox and reseeded it
without writing duplicate starter files. Approval flags and URLs were
fixture values. Standards selection, browser dataset discovery, full
vault migration and staging release remain open.

### SilverBullet notebook pilot

Use SilverBullet to author and browse Markdown notes for a disposable Sandbox
Binder. The Binder holds the notebook and related documents. Its Mission holds
the objective, tasks and run history in uFlow. Feeds remains the intake view, and
the Workflow Queue remains the place to follow execution.

Start with a disposable SilverBullet space containing an index and one Binder
working note. Keep the existing Binder brief, draft and workflow metadata under
uCore and uFlow ownership. Bring the edited note back through the existing Binder
Markdown intake. Record how frontmatter, links and tags survive the round trip
and confirm the note opens from the Binder in uCore. Use ordinary Markdown
links in the pilot so the note is readable in both editors. SilverBullet
queries can be tried as a local view of the notes.

Before adopting a shared writable space in the User Vault seed, test concurrent
edits, rename and delete behavior, and profile isolation. Limit the space to
user-owned notebook content. Keep canonical Global Knowledge and Public
publishing under their existing owners. Jupyter remains available for
computational work, and NotebookLM remains an optional export destination.

See the [SilverBullet space model](https://docs.silverbullet.md/Space) and
[filesystem API](https://docs.silverbullet.md/HTTP%20API).

The disposable intake fixture passed with a simulated Markdown edit. The
Binder listed the imported note, and intake preserved its UID, title, tags,
body and external link. Repeating the import returned the existing document.
Importing changed content under the same filename returned a conflict and
preserved the original. The next check is to use the SilverBullet editor
for the same workflow, then verify an intentional update of the imported
note and navigation between two linked notebook pages.

### SilverBullet integration sprint

| Order | Owner | Work | Exit evidence |
| --- | --- | --- | --- |
| 1 | uCore | Open the disposable notebook in SilverBullet Desktop on macOS. Follow the links from the index to the working note and evidence page, edit the working note, then restart the editor. | Both page links resolve and the edit survives restart on disk. |
| 2 | uCore | Import both pages into Sandbox through Binder Markdown intake and open them in the Binder. | Titles, UIDs, tags and note links survive. A repeat import leaves the stored files intact. |
| 3 | uCore | Add an explicit revision action using the saved document digest. Keep the import conflict behavior for ordinary uploads. | An intentional update keeps the UID. A stale update preserves the newer revision. Rename and delete behavior is documented and exercised. |
| 4 | uCore and uFlow | Run a Sandbox Mission from feed intake through Tasks and Queue. Record the result in the notebook using a safe sample action. | The task retains the feed source, Mission and Binder. Queue shows the execution outcome. The notebook links to the result. |
| 5 | uCore | Check access between two disposable profiles and rerun User Vault seed qualification with the chosen notebook layout. | A second seed pass preserves user edits, notes stay within their owning profile, and the existing-vault migration preview accounts for collisions. |

Sprint completion requires the live walkthrough and the revision and isolation
checks. The disposable Desktop space belongs to the pilot operator and can be
removed after capturing the results. Its cost is the local app and a few
Markdown files. Desktop uses a local folder, so the walkthrough requires no
new running service. See [SilverBullet Desktop setup](https://docs.silverbullet.md/Install/Desktop).

The import API now accepts `expected_sha256` for a named Markdown note in an
existing user Binder. Use the digest returned by the previous import. The API
returns the new digest on success and a conflict if the file has changed or
the submitted note changes its UID. The fixture covers both conflicts and a
successful update with intact tags and a relative link. Import requests are
serialized in one uCore process. Direct filesystem edits and the live
SilverBullet walkthrough still require qualification.

The disposable Mission fixture now exercises the feed promotion handler and
imports two linked notebook pages. The saved task keeps its feed source,
Mission and Binder. The initial promotion and its retry return the same
task ID. A second profile cannot promote to that Mission. Both notebook
pages appear in the Binder with their UIDs, tags and relative links intact.
The fixture runs the registered Vault Discovery Skill in dry-run mode
against the disposable User Vault. The Queue API returns the persisted
completed run, and the Binder evidence note records the task and run IDs.
The Queue browser view and the SilverBullet editor walkthrough remain
pending. The shell could not resolve GitHub to fetch a SilverBullet binary.

The User Vault reseed fixture now verifies that a notebook page remains
listed in Sandbox and retains its exact bytes. The profile review found
that Binder reads and writes use the host User Vault root across app
profiles. Mission scoping therefore does not establish notebook isolation.
The notebook isolation checkpoint remains open.

### Notebook pilot closeout sprint

The disposable fixture already verifies feed promotion, a real Vault Discovery
dry run, Queue API persistence, Markdown revision conflicts, and byte-for-byte
notebook preservation on reseed. Use that fixture as the baseline for the
remaining checks.

| Order | Owner | Work | Pass criteria |
| --- | --- | --- | --- |
| 1 | uCore | Run the two-page notebook in SilverBullet on a disposable local space. SilverBullet availability is the current dependency. | Follow both page links, edit and restart the editor, import both pages, then apply an intentional revision. UIDs, tags, and relative links survive. |
| 2 | uCore and uFlow | Verify the Mission from Feeds through Tasks and Queue in the browser. This can run alongside step 1. | The promoted task opens from Feeds, retains its Mission and Binder, and the completed sample run appears in Queue. The evidence note identifies the same task and run. |
| 3 | uCore | Resolve the shared host vault boundary before enabling profile-private notebooks. Exercise both profiles through Binder and vault document routes, including direct links and writes. | The owning profile can read and revise its notebook. A second profile cannot list, read, or edit it. Existing host vault documents remain accessible through their intended routes. |
| 4 | uCore | Verify notebook file lifecycle and repeat seeding against the chosen layout. | A stale revision preserves newer content. Rename and delete behavior is verified, including what happens to links. Reseeding preserves edits and the migration preview reports collisions. |

Close this round when the four checks have recorded results with the test or
walkthrough steps and any remaining defects. Keep the notebook pilot open
while a required check is blocked. Record the closeout here before qualifying
the User Vault seed for release.

Closeout sprint started on 15 November 2026. The live Workflow Queue displayed
an existing completed run. The disposable feed, Mission, notebook and task
sync suites passed 36 tests. The browser check confirms Queue rendering.
The full browser walkthrough still needs one disposable task and run
followed through Feeds, Tasks, Queue and the Binder evidence note.

The disposable lifecycle check now covers two linked notes through Binder
rename, Trash and restore. Renaming the Binder title preserves its path.
Trashing the Binder moves both pages together. Restoring it to its original
location restores both pages and their relative links byte for byte.
The editor file handlers were also exercised on an individual page. Rename
preserved the page bytes at the new path. Delete removed the page from the
Binder listing. The surviving page retained its original link, which no
longer resolves after the target page is renamed or deleted. SilverBullet's
own link handling still needs the live walkthrough.


The Sandbox seed now detects filename collisions that differ only in case.
The disposable migration fixture verifies that the preview marks the
collision and that reseeding preserves both the existing note and its legacy
counterpart. This check covers recognized Sandbox starter files. A full
migration inventory and a run on a case-sensitive volume remain pending.
The focused notebook, workspace and feed suites passed 46 tests.

The migration preview now inventories custom files and nested notes as well
as starter documents. It reports matching copies, move candidates, and path
or content conflicts. Legacy Binder metadata and symbolic links are flagged
for manual review. The fixture verifies original and destination bytes remain
intact and that linked directories outside the vault are excluded. A review
of the live migration inventory remains pending.

The live Sandbox inventory contains four move candidates and one legacy
Binder descriptor for manual review. The current Sandbox destination has
an evidence directory and lacks Binder metadata. Review that directory
before creating the missing runtime Binder and applying the proposed moves.

The Filepicker now groups Global Knowledge by indexed topics and shows
related files from the indexed vaults. Authored topics take precedence over
legacy categories and folder fallbacks. References can match a document UID
or an unambiguous title. The Editor shows topic and tag pills, provenance,
and review needs. Storytelling terminology changes the displayed difficulty
label and value. The source UID stays stable and the index associates it
with known origin fields and revisions. Missing provenance requires evidence
before it can be recorded.

OK Assistant now selects a local model by purpose unless the user overrides
the selection. Snackbar includes batch pull and update actions for explicit
tagged model references. A mocked local service exercised the update batch.
The live public index rebuilt 745 entries. Browser verification opened a
Communication document through the topic group and displayed its metadata
and related documents.

Rehearsed Sandbox migration with temporary copies of both live directories.
Initializing the runtime Binder and copying the four candidate files preserved
the existing evidence byte for byte. Three Markdown files appeared in the
Binder documents directory, and a second preview reported all four copies
as retained. The live migration has not been applied.

Resumed on 15 November 2026. Restored the live Sandbox Binder with its
runtime metadata and four legacy files. The follow-up preview reports all
four copies as retained and flags the legacy descriptor for manual review.
Existing Binder evidence matched byte for byte.

The browser regression now covers promoting a Feed item from Lists, opening
its task in Editor with the Mission and Binder intact, and finding that task
and a completed sample run in Queue. Promotion refreshes the task list before
offering the Editor link. The Chromium run used disposable API fixtures; the
backend intake suite separately verified persisted run and Binder evidence.
The full walkthrough against the live vault remains open.

The live Feeds-to-Binder walkthrough passed on 16 November 2026. Chromium
used the running uCore UI and backend without API fixtures. A synthetic
feed item promoted to task `feed-294` under the checkpoint Mission and
Sandbox Binder. Editor displayed the source text with that context intact.
Vault Discovery completed as a dry run (`run-c9a704d496`); Queue displayed
the Mission task and completed run, and the runs API confirmed persistence.
Opening `sprint-evidence-4b4cb322.md` from Sandbox in Editor showed both IDs.
The checkpoint records were retained for inspection. SilverBullet and
profile-private notebook checks remain open.

On 16 November 2026, the SilverBullet 2.12.1 browser editor pilot passed
using the official macOS server binary on loopback and a temporary space.
Chromium followed the index and both notebook links. An edit reached disk
and reopened after restarting the server in a fresh browser context. uCore
imported both synthetic pages into Sandbox, retained the digest on repeat
import, accepted the intentional revision, and rejected the stale digest
with HTTP 409. Both notes opened from Binder Documents. The saved Markdown
retained UIDs, tags and reciprocal relative links; Editor rendered both
relative link targets and the revised text. The evidence files are
`sb-35822f9d-working.md` and `sb-35822f9d-evidence.md`.

The temporary SilverBullet process was stopped. This verifies the editor
and Markdown handoff on the Server edition. The Desktop-specific launch
and restart check, in-app link navigation after import, and cross-profile
isolation remain open.

The live Sandbox notebook link check passed in uCore. Relative links to
sibling Markdown files now open inside Workflow Editor and retain the
Binder context. Chromium followed the working note's link to the evidence
page and used Enter to return to the working note in the same tab. The
revised text was still present. The check read the existing pilot files
without changing them. Desktop qualification and profile-private notebook
isolation remain open.

The profile isolation check failed in a disposable User Vault. With the
active identity set to the owner and then to a second authenticated profile,
both identities received HTTP 200 from Binder list, Binder detail, the
editor workspace tree, and a direct read of the notebook's Markdown path.
The second profile also saved through the versioned editor endpoint and
changed the file on disk. This exercised the actual route handlers with
injected identities and a temporary vault.

Treat Sandbox notebooks as host vault documents. To qualify a profile-private
notebook, define its owning profile in storage and enforce it across Binder
operations and direct vault access, including browse, search, open, save,
move and delete. Retest with both identities and a regular host vault
document before enabling the private layout.

The Binder Documents panel now states that its host vault files are
accessible from any local uCore profile. The identity check used temporary
identity and session files and exercised the profile switch handler. A
second profile switched to the owner by supplying only the owner profile ID.
A private notebook requires independently authenticated identities and
request-bound authorization before Binder and vault ownership checks can
provide isolation.


## Round closeout, 16 November 2026

Notebook pages are ordinary Markdown documents in the User Vault Binder.
Users manage them in Workflow with their active uDOS profile. Missions and
feeds keep their existing profile scope. Local profiles using the same host
vault can see its notebook files. Separate notebook storage and account
isolation are outside this round.

The notebook backlog is complete for this scope. The two-page SilverBullet
Server walkthrough verified editing and restart persistence. uCore verified
linked navigation, revision conflicts, Binder Trash and restore, reseeding,
and the live Feed → Mission → Queue → Binder evidence flow. SilverBullet
Desktop is an optional client and its native walkthrough is deferred.

The K1–K5 production release gate remains open. The Global Knowledge source records the candidate and the recovered
material held for review. Wizard approval and standards selection remain
open. The fixture edition evidence
covers repeatable builds and feed round trips. The approved package still
needs the staging install, browser acceptance and recovery record required
by K5.
