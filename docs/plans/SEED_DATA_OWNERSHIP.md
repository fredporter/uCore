# Global Knowledge editions and seed ownership

## Developer source and installed edition

The data-only developer checkout is `~/Code/global-knowledge`, retaining the existing Git history and configured `https://github.com/fredporter/global-knowledge.git` origin. The installed content stays at `settings.public_vault_root/global-knowledge` (normally `~/Public/global-knowledge`). It is a read-only baseline through uCore's user flows, not a repository that a typical user edits or updates with Git. Shared and Vault overlays retain their existing precedence and isolation.

Migration preserved all 518 tracked/untracked content files by checksum and retained the three pre-existing uncommitted assets in the developer checkout. The original installed `.git` metadata was archived under `Code/ARCHIVED/cleanup-2026-11-09/installed-knowledge-git`; installed readable content was not modified. Generated `_site` material remains in the installed directory and is not silently treated as developer source. No knowledge repository changes have been published by this migration. The accessible fredporter remote currently contains only README/version files on main; the preserved installed-baseline history is not that remote corpus. Reconcile through a reviewed import/release pathway; never force-push away either history.

The repository is the offline knowledge bank: survival/reference content, Markdown, city guides, topic data, licences/provenance and seed manifests. Both the modern knowledge reader and teletext reader consume editions of the same content. This is an offline encyclopedia edition, not a second reader runtime or service.

## Code and data boundary

Calculation code, mapping algorithms and minimum runtime constants remain with their existing product owners. GridCore code stays in uCode; uCore hosts setup, installation/readiness and reader services. Canonical standards remain installed in Public/global-knowledge and must not drift between products. A maintainer-controlled seed release can carry the source standards and larger reference datasets without moving application algorithms into the content repository.

Current setup checks read installed knowledge/standards, map data from the owning uCode seed tree, and host public-domain IANA timezone/place tables. No duplicate baseline is embedded in uCore. Map data should migrate into edition packs through a manifest-backed release process; the current change does not pretend this future migration has happened.

## Edition model

Use one content corpus plus pack manifests, rather than separate copied repositories for each edition:

- **Core:** minimum setup/catalogue/protocol data and a compact starter reference.
- **Essential:** curated survival, everyday practical knowledge and selected illustrations.
- **Reference:** broader encyclopedia topics and richer assets.
- **Complete:** all distributable packs appropriate to the device's capacity.
- **Interest packs:** independently selected topics such as physical computing, hardware revival, gardening or astronomy.

These are proposed edition names, not invented released versions or size promises. Each release must calculate actual download/installed bytes and declare pack IDs, dependencies, checksums, provenance, content licences, reader compatibility and schema versions. Shared files are installed once even when multiple packs need them. Do not publish third-party corpus content without its redistribution rights being reviewed.

Installation must stage and validate an edition before switching the installed baseline, retain a recoverable prior edition, and leave personal overlays untouched. Setup can show actual installed edition/pack status and capacity once this manifest-backed installer exists. The user may choose an edition or accept an update; curation/publication remain maintainer actions. Installed editions work offline.

Current checks confirm availability and structure, not a release checksum that does not yet exist. Setup therefore reports Ready/Needs attention rather than fabricating an edition identity.
