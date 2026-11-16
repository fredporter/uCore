# Edition publishing sprint — 2026-11-11

Status: started. uCore owns preview and authorization, bundled uFlow owns queued publishing work, and uCore-Publish owns edition compilation and transport. The WordPress extension serves reviewed editions. This plan follows the existing source documentation lifecycle and introduces no runtime state.

The [starter collection](https://udo.guide/editions/starter-collection/1/) and its [mirror](https://udo.place/editions/starter-collection/1/) are live. Five editions and their index returned HTTP 200 on both hosts. The CDN grid image matched the source hash. This gives the sprint a working publication target and a small set of links to check.

| Work | Owner | Completion evidence |
| --- | --- | --- |
| Inventory Vault links | uCore | Read-only totals for resolved, missing and ambiguous links, anchors and embeds. Preserve source paths and collect only aggregate evidence in this plan. |
| Build an edition link manifest | uCore-Publish | Resolve against the selected edition and authorized assets. Preserve labels and headings for included targets. Report missing, ambiguous and restricted targets in preview. Avoid publishing private paths or labels. |
| Publish one reviewed Binder through the normal flow | uCore and uFlow | Knight exports locally. Sorcerer sends an approved edition to an approved origin. Wizard manages the origins. The receipt records the stable edition ID, revision and confirmed destination. |
| Verify guide, mirror and graphics | uCore-Publish | Both edition URLs serve the same revision. The mirror declares the guide canonical. Relative links work on both hosts and offline. Verify withdrawal and cache behavior with a disposable edition. |
| Add the approved spatial view | uCore-Publish and GridCore | Stable GridCore references link to mirrored editions. Publish approved location fields and units only. |
| Keep forms and fallback task work tracked | WordPress integration owner | WordPress owns extended form submissions and new fallback tasks when neither Apple nor Google Tasks is available. Confirm the task API origin and HubSpot mapping before wiring delivery. |

Initial read-only Vault scan found 24 Markdown files, 123 other visible files and two wiki links with no candidate in Vault. This is a Vault-only sample. Shared and installed Global Knowledge, Markdown links, heading validity, and public visibility still need to be checked. No source content or paths were copied into this report.

The cross-layer check found no matching Markdown target for either Vault wiki link in Vault, Shared or installed Global Knowledge. This is a path and filename check. The edition preview now distinguishes included, outside-edition, missing and ambiguous targets, and supplies URLs only for manifest entries. Heading text and embed intent are retained for review.

The preview and review cycle is wired and qualified: `preview_edition_links` and the `preview: true` option on `/api/binder/{binder_id}/publish` inspect edition markdown wiki links against extracted section headings, returning link target statuses (`outside_edition`, `heading_found`, `ambiguous_heading`, `missing_heading`) without generating publishing receipts. The `NotebookBinderPanel` consumes this preview via a dedicated `Review links` action with accessible status labels and error handling. Tested across backend unit tests and frontend vitest suites.

Link sanitization and in-edition anchor rewriting are delivered and qualified: `binder_engine.py` converts verified in-edition references to valid HTML anchor links (`[label](#anchor)`) using standard-library `docs_publish.markdown_to_html` fallback when the external `markdown` package is absent, ensuring internal markers are stripped and outside-edition references render as safe text without broken targets. In parallel, `uCore-Publish` compiler performs manifest-driven link rewriting via `rewrite_wiki_links`. Full qualification passed with 770 backend tests, 15 publishing tests, 164 Vitest unit tests, clean production build, and home-path policy compliance.
