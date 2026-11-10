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
