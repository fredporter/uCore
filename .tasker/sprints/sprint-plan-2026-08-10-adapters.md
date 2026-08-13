# Sprint B — Move Adapters to uFlow and uKnowledge

**Status:** Complete
**Started:** 2026-08-10
**Completed:** 2026-08-13
**Scope:** Move workflow_adapter and knowledge_adapter out of uCore into their target repos

---

## Outcome

uCore no longer contains thin `workflow_adapter.py` / `knowledge_adapter.py`
wrappers. The extension registry wires `uflow` and `uknowledge` directly:

- `route_registrar: uflow.routes.register_routes` (entrypoint `uflow.setup`)
- `route_registrar: uknowledge.routes.register_routes` (entrypoint `uknowledge.setup`)

Each external package owns its own path discovery (`setup(app)` in its
`__init__.py` adds the local repo to `sys.path` when running split-repo).

## Completed

- [x] `workflow_adapter.py` removed from uCore
- [x] `knowledge_adapter.py` removed from uCore
- [x] `app/extensions/adapters/__init__.py` updated — only runtime adapters remain
- [x] Registry declares `uflow`/`uknowledge` with direct import paths
- [x] uFlow `__init__.py` provides `setup(app)` + path discovery
- [x] uKnowledge `__init__.py` provides `setup(app)` + path discovery
- [x] uFlow + uKnowledge `ucore-extension.json` point at `uflow.setup` / `uknowledge.setup`
- [x] Fixed `scripts/check_knowledge_route_contract.py` to add the uKnowledge repo path in split-repo dev mode

## Verification (all pass)

- [x] `python3 scripts/validate_extension_manifests.py`
- [x] `python3 scripts/smoke_split_repo_imports.py` — route_count=272, identity_pairs=11
- [x] `python3 scripts/check_knowledge_route_contract.py` — 20/20 routes
- [x] Backend boots with external routes registered (knowledge + workflow respond 200)

## Notes

- `/api/knowledge/status` is a stub in uKnowledge (returns 501 "Not implemented
  in uKnowledge yet") — expected, route registration itself is proven working.