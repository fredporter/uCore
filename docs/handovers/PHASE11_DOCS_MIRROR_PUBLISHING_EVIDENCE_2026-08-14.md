# Phase 11 — Docs Mirroring & Publishing: Evidence Bundle

- Phase: 11 — Docs Mirroring & Publishing (Lane-Separated)
- Status: Complete
- Owner: developer-lane
- Closed: 2026-08-14
- Governance: stop-the-line evidence gates per wave

## Goal

One readable Documentation surface that mirrors uDos component docs (Dev Lane),
keeps user published vaults separate (User Lane), supports two-way sync in Dev
Mode, and publishes a static docs site from the mirror.

## Wave Completion

| Wave | Scope | Status |
|------|-------|--------|
| 1 | docs_mirror sync engine (pull only) | ✅ |
| 2 | provenance + two-way sync (Dev Mode gate) | ✅ |
| 3 | surface lane separation + Dev Mode editing | ✅ |
| 4 | docs-site publish pipeline | ✅ |
| 5 | verification & evidence | ✅ |

## Runtime Proof

```
POST /api/docs/mirror/sync        -> {status: completed, total_files: 168}
GET  /api/docs/mirror/status      -> {status: ok, total_files: 168, sources: 5}
POST /api/docs/mirror/push        -> 403 (Dev Mode off — User lane cannot mutate)
POST /api/docs/publish            -> {status: ok, rendered_pages: 168}
GET  /api/docs/publish/status     -> {status: ok, total_files: 168}
```

- Mirror: `~/.ucore/docs-mirror/` (168 files; uCode 96, uCore 70, uVector 2;
  uFlow + uKnowledge missing because those repos do not exist under ~/Code).
- Published site: `~/Public/doc-sites/udos-docs/` (index.html, per-repo and
  per-doc pages, sitemap.html, USX-styled assets/style.css, publish.json).

## Test Proof

- Backend: `python -m pytest -q` → **490 passed** (6 warnings).
- Docs route contract: `scripts/check_documentation_route_contract.py` → **17/17**.
- Docs publish unit tests: `tests/test_docs_publish.py` → 4 passed.
- docs_mirror tests: covered by the mirror push gate (403) + sync round-trip.

## Command Proof

- Duplicate-route audit: `scripts/audit_duplicate_routes.py` →
  **194 unique routes, 0 duplicates**.
- Frontend type-check: `pnpm -C frontend-vue run type-check` → clean.
- Frontend production build: `pnpm -C frontend-vue run build` → **built in 5.47s**.

## Lane Separation Verification

- `docs_mirror._ensure_allowed` rejects `~/Vault`, `~/Shared`, `~/Public` (tested
  via Wave 1 D1.4; FORBIDDEN_ROOTS guard).
- `push_to_repo(require_dev_mode=True)` returns 403 when Dev Mode is off
  (runtime proof above).
- Documentation surface serves component docs read-only in User lane; Dev Mode
  enables edit → `POST /api/docs/mirror/push` write-back (D3.3).

## Exit Criteria

1. ✅ Component docs mirror exists with provenance and periodic pull sync
   (04:10 daily maintenance job `docs_mirror_sync`).
2. ✅ Dev Mode can edit + write back to source repos; User lane cannot mutate.
3. ✅ Documentation surface separates Dev-lane component docs from User-lane
   vaults (Guide = component docs from mirror; Learning = user vaults).
4. ✅ docs-site builds from the mirror (`POST /api/docs/publish`).
5. ✅ All waves passed stop-the-line evidence gates.

## Deferred / Follow-up

- `docs.udo.guide` live deploy: `deploy_site()` now initializes the site git
  repo, commits, and pushes when a remote is configured
  (`UDOS_DOCS_DEPLOY_REMOTE` env var or `.deploy-remote` file). The site dir is
  a git repo with a committed snapshot — only the Pages remote needs to be set
  (owned by `~/Code/udos-publishing`).
- uFlow/uKnowledge repos missing under `~/Code` — mirror sync reports them as
  `missing`; they will be picked up automatically when the repos exist.
