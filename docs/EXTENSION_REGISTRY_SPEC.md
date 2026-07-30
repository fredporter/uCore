# Extension Registry Specification

## Overview

uCore's extension system allows capabilities to be discovered,
loaded, and registered at runtime. This enables a clean repo split where
workflow, knowledge, and domain plugins live in separate repositories
while uCore remains the host platform core.

## Design Principles

1. **Lightweight** — no plugin framework dependency. A dataclass manifest
   and a dict-backed registry.
2. **Fail-fast for required capabilities** — missing required extension
   prerequisites block execution and trigger repair guidance.
3. **Discoverable** — extensions declare themselves via a
   `ucore-extension.json` file placed in well-known locations.
4. **Required means required** — required extensions fail fast when missing.

## Extension Manifest

Each extension ships a `ucore-extension.json` at its repo root:

```json
{
  "id": "uflow",
  "name": "uFlow Workflow Engine",
  "kind": "workflow",
  "version": "0.1.0",
  "description": "Workflow definitions, runs, logs, task orchestration",
  "optional": false,
  "api_prefix": "/api/workflows",
  "entrypoint": "uflow.setup",
  "route_registrar": "uflow.routes.register_routes",
  "dependencies": ["ucore-core"]
}
```

### Fields

| Field             | Required | Description                                                          |
| ----------------- | -------- | -------------------------------------------------------------------- |
| `id`              | yes      | Unique extension id (e.g. `uflow`, `udos-home`)                      |
| `name`            | yes      | Human-readable name                                                  |
| `kind`            | yes      | One of: `core`, `workflow`, `knowledge`, `plugin`, `surface`, `tool` |
| `version`         | no       | Semver (default `0.1.0`)                                             |
| `description`     | no       | Short description                                                    |
| `optional`        | no       | If `false`, startup/route wiring must fail fast when missing         |
| `api_prefix`      | no       | URL prefix for routes (`/api/workflows`, etc.)                       |
| `entrypoint`      | no       | Dotted path to `setup(app)` callable                                 |
| `route_registrar` | no       | Dotted path to `register_routes(app)` callable                       |
| `dependencies`    | no       | List of extension IDs this one requires                              |

### Extension Kinds

| Kind        | Purpose                                  |
| ----------- | ---------------------------------------- |
| `core`      | uCore built-in — never externalised      |
| `workflow`  | Workflow engine, task orchestration      |
| `knowledge` | Knowledge bridge, search, indexing       |
| `plugin`    | Optional udos-\* domain capability       |
| `surface`   | UI surface served by uCore               |
| `tool`      | Dev tool integration (docker, git, etc.) |

## Discovery

The registry scans these locations (in order):

1. `backend/app/extensions/manifests/` — manifests bundled with uCore
2. `~/.ucore/extensions/` — user-installed extension manifests
3. Any extra paths passed to `registry.discover(paths=[...])`

Built-in core extensions (`ucore-core`, `ucore-skills`, `ucore-surfaces`,
`ucore-secrets`, `ucore-tools`) are registered programmatically at
registry init and do not require manifest files.

## Loading Sequence

At startup, uCore calls:

1. `registry.discover()` — scan for external manifests
2. `registry.load_all(app)` — import and call `setup(app)` on each extension
3. `registry.register_routes(app)` — wire in route registrars

Extensions without an `entrypoint` are treated as "route-only".
Route registration still must pass required-extension rules.

## Capability Preflight Gate

Before executing capability actions, clients should call:

- `GET /api/extensions/status`
- `GET /api/capabilities/{capability}/preflight`

If preflight reports `ready=false` (or HTTP 412), execution must be blocked
and repair steps shown to the user. Resume only after repair and a passing
preflight rerun.

## Compatibility Adapters

For extensions extracted to dedicated repos (uFlow, uKnowledge),
uCore provides **adapters** in `app.extensions.adapters/`:

```
workflow_adapter.py:
  import uflow.routes.register_routes
  if import fails and extension is required -> raise RuntimeError

knowledge_adapter.py:
  import uknowledge.routes.register_routes
  if import fails and extension is required -> raise RuntimeError

ucode_runtime_adapter.py:
  import runtime-owned Ceefax/BBCSDL registrars when available
  if required by env and missing -> raise RuntimeError
  otherwise -> explicit compatibility fallback to legacy in-repo provider
```

Adapters may exist during extraction phases, but must not hide missing
required prerequisites for active capability paths.

## Wave 2 Status (Current)

- Workflow route registration: externalized to uFlow (hard-cut).
- Knowledge route registration: externalized to uKnowledge (hard-cut).
- In-core workflow and knowledge API modules were removed from uCore after
  parity checks.
- Active knowledge endpoints are served by external uKnowledge route
  registration (including `search`, `workspaces`, and `documents` routes).
- uCode runtime bridge registration in `app.api.routes` now goes through
  `app.extensions.adapters.ucode_runtime_adapter.register_routes(...)`.
- BBCSDL bridge path uses `UCORE_BBCSDL_BRIDGE_PATH` configuration instead of
  a single hardcoded location.

## Route Registration

The adapter pattern externalizes workflow and knowledge route registration.
uCore still wires host-shell routes directly in `app.api.routes`, and then
delegates extension-owned routes through the registry:

```python
# In routes.py:
register_host_shell_routes(app)
from app.extensions.registry import registry
registry.register_routes(app)
```

This calls each extension's `route_registrar` for extension-owned paths
(`/api/workflows/*`, `/api/knowledge/*`) so client contracts stay stable while
host-shell routes remain in uCore.

## Creating a udos- Plugin

1. Copy the `HomeNest/modules/home-ops/udos-home` module
2. Update `ucore-extension.json` with your plugin id/name
3. Create a Python package that exports `register_routes(app)`
4. Install alongside uCore — automatically discovered

## Status Endpoint

```bash
curl http://localhost:8484/api/extensions/status
```

Returns:

```json
{
  "total": 7,
  "loaded": 7,
  "failed": 0,
  "errors": {},
  "extensions": [
    {"id": "ucore-core", "name": "uCore Runtime Shell", "kind": "core", ...},
    {"id": "uflow", "name": "uFlow Workflow Engine", "kind": "workflow", ...},
    ...
  ]
}
```

## Migration Path

1. **Phase 1 (done):** Plugin contract + adapters in uCore
2. **Phase 2 (done):** Scaffold uFlow, uKnowledge, and HomeNest udos-home module manifests
3. **Phase 3 (active):** Workflow extraction/deletion waves with parity checks
4. **Phase 4 (active):** Knowledge extraction/deletion waves with parity checks
5. **Phase 5:** Update CI/CD, publish packages, update docs
6. **Phase 6 (done):** Capability preflight gates enforced across S-pages

Execution should prefer explicit repair flows over silent fallback for
required capability paths.
