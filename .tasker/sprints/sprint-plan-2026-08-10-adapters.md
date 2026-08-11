# Sprint B — Move Adapters to uFlow and uKnowledge

**Status:** Active
**Started:** 2026-08-10
**Scope:** Move workflow_adapter and knowledge_adapter out of uCore into their target repos

---

## Current State

### workflow_adapter.py (uCore, 40 lines)
- Tries `from uflow.routes import register_routes`
- On ImportError, adds `~/Code/uFlow` to sys.path and retries
- uFlow already has: `uflow/__init__.py`, `uflow/routes.py`, `uflow/workflow_api.py`

### knowledge_adapter.py (uCore, 42 lines)
- Tries `from uknowledge.routes import register_routes`
- On ImportError, adds `~/Code/uKnowledge` to sys.path and retries
- uKnowledge already has: `uknowledge/__init__.py`, `uknowledge/routes.py`

### uCore Registry (builtins)
- Both uflow and uknowledge declared with `route_registrar` pointing at the adapters
- Adapters are thin wrappers — no fallback logic, no core behavior
- The path-discovery logic is the only reason they exist in uCore

---

## Tasks

### Wave 1: Package the Adapters

- [ ] **B1.1** Move `workflow_adapter.py` path-discovery into `uflow/__init__.py`
  - Add `setup(app)` that handles sys.path modification and import
  - Keep the two-try pattern (direct import → add path → retry)
- [ ] **B1.2** Move `knowledge_adapter.py` path-discovery into `uknowledge/__init__.py`
  - Same pattern: direct import → add path → retry
- [ ] **B1.3** Update uFlow `ucore-extension.json` to use `uflow.setup` as entrypoint
- [ ] **B1.4** Update uKnowledge `ucore-extension.json` to use `uknowledge.setup`

### Wave 2: Wire Directly from uCore Registry

- [ ] **B2.1** Replace `app.extensions.adapters.workflow_adapter.register_routes` with direct import in registry
  - Registry calls `uflow.routes.register_routes(app)` directly
  - Registry handles the path-discovery (keep the env var pattern)
- [ ] **B2.2** Replace `app.extensions.adapters.knowledge_adapter.register_routes` with direct import
- [ ] **B2.3** Remove `workflow_adapter.py` from uCore
- [ ] **B2.4** Remove `knowledge_adapter.py` from uCore
- [ ] **B2.5** Remove `__init__.py` references to adapters

### Wave 3: Verify

- [ ] **B3.1** Run `python3 scripts/validate_extension_manifests.py`
- [ ] **B3.2** Run `python3 scripts/smoke_split_repo_imports.py`
- [ ] **B3.3** Run `python3 scripts/check_knowledge_route_contract.py`
- [ ] **B3.4** Verify backend starts with uFlow and uKnowledge routes registered
- [ ] **B3.5** Verify workflow and knowledge endpoints respond correctly

### Exit Criteria
1. workflow_adapter.py deleted from uCore
2. knowledge_adapter.py deleted from uCore
3. uFlow package handles its own path discovery and route registration
4. uKnowledge package handles its own path discovery and route registration
5. All extension manifest checks pass
6. Backend boots with external route registration working