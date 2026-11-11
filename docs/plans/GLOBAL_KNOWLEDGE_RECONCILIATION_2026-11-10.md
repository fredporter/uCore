# Global Knowledge reconciliation checkpoint

Owner: external maintainer; C02 in the consolidation sprint.

Local main: `5e6abf3327b56f8902d25fcb0f2a263339d00bf8`

Fetched upstream: `c69c46c5491cddf186b8fe4519fdfe447bee4568`

Both tips retained as local `preserve/local-2026-11-10` and `preserve/upstream-2026-11-10` branches. Git reports no common ancestor: these are independently rooted histories, not an ordinary seven-versus-two branch divergence. Do not use a routine pull/merge or wholesale replacement.

## Untracked material

```json
[
  {
    "path": "EDITION_PLAN.md",
    "bytes": 1748,
    "sha256": "64356dabf379a626aa59dfd7f334323146f68b7c09b142c57de0d0075cae6833"
  },
  {
    "path": "elements/bob-zen_envelope-teletext_ceefax.gif",
    "bytes": 201,
    "sha256": "3568b0fc03f95c82e96ee531407415d85599699db9f9012a957b85c4938d1ae5"
  },
  {
    "path": "standards/COMMUNICATIONS-LOOP-SPEC.md",
    "bytes": 3440,
    "sha256": "af2613d2be27fe47ef3695126fa0fefb4e1eb7c71da1cf9458d881da6f5cc15a"
  },
  {
    "path": "standards/GRIDCORE-LATTICE-SPEC.md",
    "bytes": 3374,
    "sha256": "fb405c2e18c597e37465981ea9888c97e55eaaa106263048f48cb67cadd572da"
  }
]
```

Files are now committed on local `recovery/consolidation-2026-11-10`; their paths remain in place. This is a local Git recovery reference, not an independent off-device backup. Recovery branches retain existing objects without duplicating the corpus. Their lifecycle is maintainer review through reconciliation; remove only after verified replacement history and assets are retained. No installed Public baseline changes.

## Reconciliation procedure

1. Preserve untracked assets in a dedicated local recovery commit, after provenance/secret review; do not publish the entire historical corpus automatically.
2. Compare upstream path inventory against local standards/datasets and content; classify identical, local-only, upstream-only and differing files with hashes.
3. Start the delivery branch from upstream, selectively import reviewed canon/standards and edition planning; retain historical layout changes only as provenance.
4. Check distribution rights, links and edition metadata before publishing; no unverified release claims.
5. Record selected commits/files and recovery references; install canon only through a separately validated edition workflow.

## Corpus comparison and first content decisions

Full Git object inventory: `GLOBAL_KNOWLEDGE_COMPARISON_2026-11-10.json`. Compares the recovery commit against fetched upstream using blob object IDs plus mode/type. Counts: 518 local-only files, one upstream-only file (`VERSION`), one differing file (`README.md`), zero identical paths. Upstream is a placeholder repository, not a competing populated edition. Historical seven-versus-two counts must not imply shared ancestry.

- Retain upstream VERSION as provenance; its prerelease marker does not certify local corpus content.
- Replace the stale local README in the eventual delivery proposal: it claims topic trees are absent although they are present, and references obsolete archive paths.
- Retain EDITION_PLAN as the basis for manifest/rights review; do not publish all recovered corpus files by default.
- Hold CONTAINER-STANDARDS for revision: it describes Tomb as a sealed archive/tombstone, conflicting with the accepted public Tomb / encrypted Crypt contract, and specifies unqualified storage paths.
- Hold KNOWLEDGE_LAYERING_AND_CONTRIBUTION_SPEC for revision: layering agrees with the contract, but fixed model recommendations, DeveloperReviewPanel and automatic cloud distribution claims are stale or unqualified.
- Hold SOVEREIGN_HOST_REFERENCE for wording review: host clock authority is correct, but claims that all products inherit location services and that mapping is already fully offline require product evidence.
- Keep recovered topical material, contributor references and GIF assets in recovery pending distribution-rights/provenance checks. No corpus files approved for a release in this pass.

The JSON inventory belongs to uCore maintainer planning, contains only paths and Git object IDs, and follows the sprint document lifecycle. It introduces no runtime cache or service. C02 preservation/comparison is complete; selective content revision and delivery review remain open.
