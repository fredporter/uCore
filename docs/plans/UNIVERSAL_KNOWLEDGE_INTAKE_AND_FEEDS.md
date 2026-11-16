# Universal knowledge intake, Markdown and feeds

Proposed delivery plan, 14 November 2026. The navigation and seed evidence
pilots supply the first reviewed fixtures.

One intake contract connects selected files, BrowserUI captures, feed
subscriptions and curated seed data to portable Markdown and JSON. The
same reviewed material can appear in a Binder, the offline library, or
an edition feed, with provenance and visibility carried through each step.

## Intake and collation

| Input | Adapter and first output |
| --- | --- |
| Local Markdown, text, HTML or JSON | Extend the existing Markdown import pipeline. Preserve structured seed JSON alongside a Markdown explanation when both are useful. |
| BrowserUI clip or queued URL | Reuse the existing capture path. Record the requested and final URL, capture time and extraction method. Treat generated summaries as separate drafts linked to the capture. |
| RSS 2.0, Atom or JSON Feed 1.1 | Parse each entry into the same intake record. Carry forward publisher ID, original dates, links, categories, attachments and authors when supplied. Fetch linked pages or enclosures as separate, explicit jobs. |
| Existing internal activity feed | Let the user select an event to promote to intake. Keep the private Activity Pod and its workflow semantics. |

Each adapter returns a source record, a content payload and conversion
diagnostics. Record source identity, capture time, media type, payload
digest, attribution and known reuse terms. Save selected originals in the
destination's visible intake archive when retention is requested. Keep
review state and capture history in the intake index. Collation groups
related sources into a Binder or candidate by reference and retains the
evidence for disputed claims. A new capture can share bytes with another
source while retaining its own provenance.

Use a profile and subscription scope for publisher IDs. Use an exact
content hash for byte duplicates and a normalized hash for equivalent
formatted drafts. Treat URLs, feed IDs and content hashes as different
signals. When a publisher edits an item, keep its identity and record a
new revision. Treat missing entries in a refreshed feed as a normal
window change. Poll through the existing workflow authority with
conditional HTTP requests, backoff and bounded fetches. Validate redirect
destinations, disable external XML entities and cap response size and
entry counts.

## Universal Markdown formatter and metadata

Extend the existing converter with a shared parse, normalize and validate
contract. Use the installed Prose standard for presentation. Provide
preview and check modes for imports, editors and maintainer batches, with
an explicit apply step for rewriting existing files. Make a second pass
over formatted output byte stable. Preserve code fences, diagrams, tables,
wiki links, relative links, block content and unrecognised frontmatter.
For ambiguous or malformed input, keep the captured source and show a
diagnostic. Qualify HTML conversion against fixtures for links, tables,
emphasis and code.

| Field | Proposed rule |
| --- | --- |
| `uid`, `title`, `type` | Preserve an existing UID across rename, edit and overlay. Mint once for new material. Map legacy type aliases through DocLang. |
| `schema_version`, `revision` | Version the metadata contract independently of the document. Each accepted content or metadata change creates one document revision under the same UID. Record the parent in revision history. |
| `created`, `updated` | Preserve known dates. Keep original publication date and capture time in provenance. Formatting a document alone preserves its authored dates and revision. |
| `tags`, `aliases` | Preserve author labels and keep stable category identifiers in a taxonomy seed. Normalize aliases at lookup. Offer model tags as suggestions with explicit acceptance. |
| `status`, `visibility` | Capture starts in the selected writable workspace. Track review state separately from publication eligibility and resolve visibility from workspace grants and output policy. |
| `sources`, `license` | Carry source references and the reviewable reuse basis. Include locators for factual claims and field-level provenance for selected seed data. |

Use DocLang's existing field aliases and extension handling. Keep
frontmatter readable and include an offline-friendly Sources section
when readers need citations. Store byte hashes and intake bookkeeping in
the manifest or index to avoid a digest covering its own field. Keep
edition version, item revision and upstream version independent. Seed
updates retain consumer keys unless an explicit migration has fixtures
for both versions.

## Storage, ownership and feed production

- **uCore** hosts BrowserUI, import preview, the Binder and reader surfaces.
  **uFlow** owns jobs, scheduling, retries and cancellation. Reuse the
  existing research and activity stores for their respective jobs.
- **uKnowledge** owns the portable item contract, metadata validation,
  overlay precedence and edition manifests. Its intake index under
  `UDOS_HOME` records source identities, revision digests and review
  transitions. Start by checking whether the existing workspace index
  can own these relations. Document migrations and retention before
  adding tables. Rebuild search from portable files and their manifests.
- **Vault and Shared** hold writable content. **Public Global Knowledge**
  is installed Layer 0. Overlay lookups keep Vault → Shared → canon
  precedence. Public edition exports use the selected reviewed revision
  manifest. Their output eligibility is determined independently of the
  reader's overlay lookup.
- **uCore-Publish** produces feed files from a selected edition,
  collection or release manifest. Define one logical feed projection with
  stable item IDs, canonical links, title, permitted body or excerpt,
  publication and update dates, categories and permitted enclosures.
  Export RSS 2.0, Atom and JSON Feed 1.1 with format-specific field
  mapping. Produce local preview artifacts first. Generate the feed and
  edition link manifest from the same revision so their URLs and dates
  agree. Add opt-in transport after preview and destination qualification.

## Delivery order and acceptance checks

| Slice | Working result | Acceptance evidence |
| --- | --- | --- |
| 1. Shared intake | A BrowserUI clip and a local Markdown file enter one Binder through the same format. | Retry produces one item per source. Equivalent content is detected. Provenance and an existing UID survive import. |
| 2. Formatter and taxonomy | Preview and validate Markdown, frontmatter, tags and seed descriptions using the existing pilots. | Reformatting is byte stable. Legacy metadata survives. Exact seed values and known links pass the evidence audit. |
| 3. Subscription ingestion | Import a saved feed fixture for each wire format, then qualify one opt-in subscription. | Replay adds no duplicates. An edited entry becomes a revision. Invalid input, redirects and fetch limits are exercised. |
| 4. Production and round trip | Generate local RSS, Atom and JSON Feed files from one reviewed public fixture. | Re-import projections and verify stable IDs, dates, links and categories where each format supports them. Fixtures with private drafts and overlays verify publication isolation. |
| 5. Edition and research workflow | Use the maintainer skill to collate a bounded batch into an edition candidate and produce its feed. | Evidence and rights review, reader navigation against the package, deterministic rebuild and registry/retention checks. |

Use the existing [Markdown import pipeline](../../backend/app/services/markdown_import_pipeline.py),
[DocLang frontmatter mappings](../DOCLANG_BRIDGE_EXPORT_SPEC.md#front-matter-normalization),
[Activity Feed specification](../FEED_SYSTEM_SPEC.md), and
[offline library architecture](../UKNOWLEDGE_OFFLINE_LIBRARY_ARCHITECTURE.md).

Wire-format references
[RSS 2.0](https://www.rssboard.org/rss-specification) ·
[Atom RFC 4287](https://www.rfc-editor.org/rfc/rfc4287) ·
[JSON Feed 1.1](https://www.jsonfeed.org/version/1.1/)

## Completion gate

The [completion sprint](KNOWLEDGE_COMPLETION_SPRINT.md) tracks delivery and exit evidence.

Completion means a fully organised **Global Knowledge library and User
Vault seed structure**, verified by rendering both into disposable
workspaces and opening the result through uCore.

- Global Knowledge has clear topic navigation, a reviewed set of Markdown
  articles and structured datasets for the declared edition, stable item
  identities, traceable sources and a reproducible edition manifest.
  The reconciliation inventory records the destination or review status
  of historical material. Every included file passes its evidence checks.
- A newly seeded User Vault guides the user from intake and originals
  through Binder review to personal knowledge and overlays. Its paths
  match the actual import and reader entry points. Reapplying the seed
  preserves user documents. Existing vaults have a previewable migration
  that identifies moves, conflicts and retained content.
- A local file, web capture and feed entry reach the same review flow.
  Replay and revision tests pass. One reviewed collection produces the
  three feed formats and passes the publication isolation checks above.

Gate status is open. Workflow file imports and queued web captures share
a Markdown provenance renderer and resolve the same documents directory
for an existing Binder. Identical local retries at the same destination
return the existing item. Seed plates describe the existing intake and
reference directories. Feed round trips and packaged edition verification
remain open.

### Feed fixture checkpoint

uCore-Publish now parses and renders local UTF-8 RSS 2.0, Atom and
JSON Feed 1.1 payloads through a shared feed record. A reviewed fixture
round-trips identity, links, UTC dates, categories and HTML excerpts
through all three formats. The parser bounds the input size and item
count, and rejects XML DTDs and entity declarations. RSS descriptions
are treated as HTML on import, with plain text escaped on export.

The next integration is to send the parsed records through Binder
intake and build the export projection from an eligible edition
manifest. Subscription scheduling, revision persistence, attachments,
author mapping and publication isolation still need qualification.

### Saved feed intake

With uCore-Publish installed in uCore's environment, the existing
`POST /api/user/workflow/import-markdown` endpoint accepts
`source_format: feed`, `feed_source`, an existing user `binder`, and
the saved UTF-8 feed as `content`. The source is a stable feed label or
URL supplied by the caller. This endpoint reads the supplied content.

Each entry becomes Markdown with the shared intake frontmatter.
Repeating the same source and entry revision returns the existing
document. An edited entry retains its UID and creates a new revision
file. A batch error reports the completed items so the caller can
retry safely. Import into Shared and Public is rejected. The optional
codec returns a capability error when unavailable.

A disposable Binder integration test covers first import, retry,
publisher edits, provenance and destination restrictions. Scheduled
retrieval and export from a reviewed edition manifest remain open.

### Reviewed edition feed preview

The publisher accepts a version 1 public projection manifest and an
explicit edition root. Feed membership requires both public visibility
and approved review state. The preview checks each included Markdown
file against its pinned SHA-256. The feed uses the manifest's reviewed
excerpt, public URL, UID, dates and tags.

From the uCore-Publish checkout:

```sh
python3 -m udos_publishing.src.edition_feed \
  --manifest /path/to/reviewed-feed-manifest.json \
  --edition-root /path/to/edition --format atom
```

The same command accepts `rss` and `json`. It writes the local preview
to standard output. Tests cover all three feed formats, draft and
private records, an unlisted file, an external overlay, changed
article bytes and a symlink outside the edition. The manifest is
maintainer supplied. Connecting it to the edition compiler and
qualifying transport and the packaged library remain open.

### Offline package checkpoint

The publisher's `edition_feed` command accepts `--package /path/to/new-directory`
in place of `--format`. The compiler reads each approved article once,
checks its pinned digest and copies those bytes into the package. It
writes a public edition manifest and three feed files from the same
approved records. The destination must be new.

A disposable package of the two navigation drafts passed feed
re-import and uCore documentation tree and content handler checks.
Approval flags and publication URLs were fixture values. This package
compiler currently includes reviewed Markdown articles. Seed datasets,
a rendered User Vault seed, browser verification and production
transport remain part of the completion gate.
