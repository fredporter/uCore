# uKnowledge Offline Library Architecture

## Product intent

uKnowledge is the offline knowledge layer of uDos. It should remain useful when
internet services, cloud accounts, and remote models are unavailable. Its public
library aims for broad general-reference coverage comparable to a compact offline
encyclopaedia, while going further in practical, local, and actionable knowledge.

The installed Global Knowledge vault is `~/Public/global-knowledge`. It is read-only
in normal user mode. uKnowledge owns the contracts that validate, package, index,
search, update, and serve signed editions. uCore hosts the Vue experience; it does
not own the corpus or knowledge engine.

## Boundaries

| Owner | Responsibility |
| --- | --- |
| Global Knowledge vault | Read-only installed editions for normal users; canonical corpus writes and releases are restricted to the Dev/maintainer workflow. |
| uKnowledge | Corpus schema, validation, provenance, offline indexes, packages/deltas, search/retrieval, citations, integrity, and knowledge APIs. |
| uCore | Browse/search/read UI, download/update controls, storage reporting, and links into Learning and Workflow. |
| BrowserUI | User research workbench: capture, snapshot, cite, extract, compare, enhance, and save into a user-owned knowledge vault; optionally create a Global Knowledge submission. |
| Learning Pathway | Sequenced lessons, exercises, assessment, and progress built from cited knowledge items. |
| uCode | The small supported coding/runtime language and user-facing computing concepts documented in the knowledge bank. |
| SonicScrewdriver | Device identity, specifications, firmware/reflash knowledge, compatibility, transformation recipes, and device-derived portals. |
| User/add-on vaults | Personal notes and specialist packs. They may be indexed alongside the public library but are not part of its distributable edition. |

General computing coverage should teach the concepts required to understand and use
uDos and uCode. It should not attempt to mirror documentation for every programming
language, operating system, or machine. Device-specific technical depth belongs in
SonicScrewdriver's device library and may be linked by stable identifiers.

## Access and contribution boundary

- Normal user mode may browse, search, cite, link, and learn from an installed Global
  Knowledge edition. It cannot modify that edition.
- BrowserUI writes research into the user's own vault, or another explicitly selected
  writable add-on/shared vault. It never writes directly into Global Knowledge.
- A user can create a portable contribution package containing proposed Markdown,
  sources, provenance, licence assertions, diffs, and optional supporting media.
- Submission does not grant publication. It enters a review queue analogous to a wiki
  contribution or pull request.
- Only Dev Mode maintainers may accept submissions into the canonical candidate
  corpus, edit release material, sign an edition, or publish update packages.
- Installed editions are replaced or updated atomically from validated packages;
  local annotations and user extensions remain in user-owned vaults.

This is a capability rule, not merely a hidden button. uKnowledge's write APIs must
reject canonical-corpus mutation without an authorized Dev/maintainer context.

This boundary reconciles existing specifications rather than introducing a new
model: `VAULT_BINDER_WORKFLOW_INTEGRATION.md` already classifies Public vaults as
read-only, `VAULT_PLATES_AND_DESTROY_SPEC.md` defines Global Knowledge as a read-only
seed plate, and the corpus's `survival/INDEX.md` directs contributions through a
separate knowledge-bank system.

## Maintainer corpus lanes

Every item must be in exactly one lane:

1. **Release** — verified metadata, defensible redistribution licence, reviewed
   safety/accuracy, and included in a signed edition.
2. **Candidate** — useful material being normalized, sourced, reviewed, or rewritten.
3. **Reference quarantine** — private research that cannot be redistributed or whose
   provenance is uncertain. It is never included in packages or public indexes.
4. **Compost** — duplicates, superseded conversions, corrupt imports, and rejected
   material retained only while provenance or recovery work remains useful.

The current `contributor/` tree contains numerous apparent book conversions. Until
each item has a provenance and licence record, it must be treated as reference
quarantine rather than distributable content.

## Required item metadata

Each release candidate needs a stable identifier and machine-readable metadata:

- title, summary, topics, audience, reading level, language, and region;
- author/publisher, source URL or source record, acquisition date, and content hash;
- licence identifier, redistribution status, attribution, and modification policy;
- created, reviewed, and freshness dates plus reviewer identity/method;
- safety class, evidence/citation list, geographic limits, and explicit uncertainty;
- relationships to prerequisites, related items, lessons, uCode concepts, and Sonic
  device identifiers.

High-stakes medical, food safety, electrical, structural, weapons, and emergency
content requires stronger review policy and conspicuous limitations. Generated or
converted prose is not considered verified merely because it is well structured.

## Offline edition contract

A distributable edition is immutable and content-addressed. It contains:

- a signed edition manifest with schema and minimum-runtime versions;
- normalized source documents and approved media;
- a compact lexical index that works without a model;
- optional local embeddings built from the exact release content;
- topic graph, redirects, aliases, citations, and learning relationships;
- per-file hashes, total size, locale/region coverage, and licence inventory;
- optional delta packages from prior editions and a complete rollback path.

Search must degrade gracefully: lexical search and browsing always work; semantic
search is an optional local enhancement. No core read/search action may require
AppFlowy, a cloud model, or an internet connection.

## BrowserUI acquisition pipeline

BrowserUI is not a general-purpose browser surface. It is the contextual research
workbench used by Intelligence and Workflow when online material should become
durable offline knowledge in a user-owned vault:

1. Capture the URL, retrieval time, publisher/author, licence signals, and a hash or
   permitted snapshot before transformation.
2. Extract useful text, tables, media references, and citations into portable
   Markdown plus structured source metadata.
3. Compare against the local corpus, identify duplicates/conflicts, and attach the
   result to an existing topic or create a candidate topic.
4. Use local Ollama models first for classification, cleanup, tags, summaries, and
   link suggestions. Use free/low-cost OpenRouter models only when policy and budget
   allow; reserve frontier review for genuinely difficult or high-risk material.
5. Keep source text, model-produced changes, and reviewer decisions distinguishable.
   A model may propose edits but may not invent provenance, erase uncertainty, or
   promote a candidate into a release edition.
6. Save the resulting inspectable Markdown into the selected user-owned knowledge
   vault. If the user chooses to contribute it, build a submission package and create
   a uFlow submission/review task without mutating the installed Global Knowledge.

In Dev Mode, an authorized maintainer can review a submission, request changes,
accept it into the canonical candidate lane, and later include it in a signed release.

Because Markdown is the durable substrate, low-cost agents can perform most routine
corpus development. Quality comes from schemas, citations, diffs, validators,
budgets, and review gates rather than requiring a frontier model for every document.

## Device portal contract

SonicScrewdriver owns a separate device corpus keyed by stable device identifiers.
uKnowledge may provide general principles and link to device records, but it must not
absorb volatile per-model specifications or firmware recipes.

A future device portal can accept a photo or observed attributes, produce candidate
identities with confidence and evidence, resolve a Sonic device record, and present:

- what the device is and what useful components/capabilities it contains;
- safe inspection, recovery, reuse, or reflashing options;
- compatible uDos runtime images and required tools;
- cited general knowledge and a guided Learning/Workflow path.

Recognition may be model-assisted, but identity must remain confirmable offline from
observable features and the local device library.

## Current-state findings (2026-08-18)

- `~/Public/global-knowledge` is approximately 409 MB with 1,157 files, including
  about 501 Markdown files. Its strongest coverage is practical survival knowledge.
- The vault is on `knowledge-maintenance-20260614-192525` with an untracked `doclang/`
  export. Generated personal-vault DocLang does not belong in a public edition.
- Root documentation contradicts the current tree: it describes a migrated subset
  and archived topic trees that are physically present.
- Index/version figures are stale and disagree with the filesystem.
- Provenance and redistribution metadata are insufficient for public packaging.
- uKnowledge currently delegates much of its implemented behavior back to
  `app.knowledge.appflowy` and returns `501` for most ownership routes. It is not yet
  an independent offline knowledge engine.
- uKnowledge still writes workspace registry state to legacy `~/.ucore`; mutable
  index/registry state must resolve through `UDOS_HOME` under `~/Code/.udos`.
- `~/Public/.local` contains runtime/config/tool state and violates the storage
  boundary. Public should contain public vault content, not application runtime.

## Stabilization sequence

1. Preserve the current corpus and create an auditable inventory without publishing.
2. Enforce read-only installed editions, writable user knowledge vaults, and an
   explicit contribution-package boundary.
3. Separate release, candidate, reference-quarantine, compost, and generated output.
4. Define schemas for items, sources, licences, editions, submissions, citations, and
   device links.
5. Remove AppFlowy and uCore-internal dependencies from the basic filesystem reader,
   indexer, and search API.
6. Move all mutable indexes, caches, registries, and jobs into `UDOS_HOME`; keep the
   public vault portable and human-readable.
7. Build a deterministic edition validator and a minimal lexical offline package.
8. Wire uCore Documentation to browse/search/read the package with clear offline,
   provenance, freshness, and safety states.
9. Replace BrowserUI sample stacks with the provenance-preserving user-vault and
   contribution pipeline.
10. Curate a balanced minimum edition: orientation, language, maths, science,
   geography, history/civics, health, practical life, nature, making/repair,
   emergency readiness, and uDos/uCode basics.
11. Connect reviewed items to the Learning Pathway.
12. After the core stabilizes, define stable cross-links to SonicScrewdriver's device
    library and build the first device-to-knowledge portal journey.
