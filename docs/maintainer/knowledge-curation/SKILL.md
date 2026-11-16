---
name: knowledge-curation
description: Research and standardise uDOS Global Knowledge Markdown and offline seed data as reviewable maintainer proposals. Use for selective canon reconciliation and evidence audits.
---

# Global Knowledge curation

Work from the Global Knowledge source checkout and read its edition plan.
Treat installed Layer 0 as a comparison input. Use Shared and Vault only
when explicitly in scope; they may contain private material. Do not pass
private data to a frontier provider. Keep this workflow in external
developer tooling; BrowserUI research jobs produce user Binder material.

1. Pick a bounded batch with named paths, a question per topic or field,
   and a source and time budget. Record the starting Git revision or file
   hashes. For a first pass, use one topic, up to five files and up to
   three primary sources. Stop when evidence is missing or conflicting
   and report the gap rather than widening the batch automatically.
2. Find primary sources for the proposed claims. Record URL, exact section
   or table, access date, what it supports and the reuse basis. A model can
   suggest sources or flag inconsistencies. If available, use a qualified
   local Ollama model for a second pass over the selected material. Check
   the source yourself; agreement between models is not evidence.
3. Preserve existing article UIDs, relative links and dataset keys unless
   proposing a migration with consumer tests. Follow installed
   `standards/PROSE-STANDARDS.md`: one article title, clear headings,
   relative links for offline material and citations for external sources.
   For seed data, record units, exactness or uncertainty and the definition
   or epoch when it affects the value. Separate sourced data from derived
   values; keep calculations in the consuming product.
4. Keep proposed edits in the source checkout. Record the expected article
   title or reviewed JSON paths in the evidence manifest; a whole-file hash
   detects drift and does not certify the other claims in that file.
   Use the read-only audit below before handing off. It checks hashes,
   titles or values, and required citation fields. It does not establish
   factual accuracy or reuse rights. Include the diff,
   evidence, rights status, unresolved claims and any reader/seed
   compatibility impact. No automatic promotion, install or publication.

Use manifest `version: 1` with a `files` array. Each entry gives the
library-relative `path`, its `sha256` and a `checks` array. Each check
contains `equals` and `source` (`url`, `locator`, `accessed` and
`reuse_basis`). For JSON, add `keys`: a sequence of object keys or
zero-based array indices. For Markdown, `equals` is the expected title.
Add `uid` to the file entry for an existing plain frontmatter UID and
`links` for the expected inline relative `.md` paths without fragments.
The audit checks only those declared links; review other links and
reader behaviour separately.

From the uCore checkout:

```sh
python3 scripts/audit_knowledge_evidence.py \
  --root /path/to/library \
  --manifest /path/to/evidence.json
```

See `research/length-conversions.md` in the Global Knowledge checkout
for a manifest and an example handoff. This repo-owned skill is read by
external maintainers on demand. The audit uses Python's standard library,
writes only to stdout and has no model spend or persistent state. Retire
both through source control when a replacement audit owns the workflow.
