# Extension Registry Specification

## Overview

uCore's extension system allows capabilities to be discovered,
loaded, and registered at runtime. This enables a clean repo split where
workflow, knowledge, and domain plugins live in separate repositories
while uCore remains the host platform core.

## Terminology (Extension vs Plugin)

In this architecture, **extension** is the top-level runtime contract and
**plugin** is one extension kind.

1. **Extension**
   - Any component discoverable/loadable by uCore via `ucore-extension.json`
     and the extension registry.
   - Can be required (`optional=false`) or optional (`optional=true`).
   - Can represent engine-like services (`workflow`, `knowledge`) or
     domain features (`plugin`).
2. **Plugin**
   - A subtype of extension (`kind: plugin`).
   - Intended for optional domain capabilities, typically in dedicated
     `udos-*` repositories.
   - Usually capability-gated through preflight and readiness checks.

Practical classification used now:

1. `uflow` and `uknowledge` are **required extensions** (not plugins).
2. `udos-*` repos are **plugin extensions**.
3. Surface projects such as Groovebox, HomeNest, and SonicScrewdriver can be
   treated as independent project surfaces that may consume uCore, but are not
   automatically extension manifests unless explicitly onboarded.

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

### Contract Validation Rules

The manifest contract is strict and validated in code/CI:

1. Allowed fields are locked to: `id`, `name`, `kind`, `version`,
   `description`, `entrypoint`, `dependencies`, `optional`, `api_prefix`,
   `route_registrar`.
2. Required fields: `id`, `name`, `kind`.
3. `kind` must be one of: `core`, `workflow`, `knowledge`, `plugin`,
   `surface`, `tool`.
4. `entrypoint` and `route_registrar` must be dotted paths.
5. `dependencies` must be a list of non-empty extension IDs, may not contain
   self, and may not contain unknown IDs.
6. Dependency cycles are invalid and fail validation.

CI enforcement command:

```bash
python3 scripts/validate_extension_manifests.py
```

### Extension Kinds

| Kind        | Purpose                                  |
| ----------- | ---------------------------------------- |
| `core`      | uCore built-in — never externalised      |
| `workflow`  | Workflow engine, task orchestration      |
| `knowledge` | Knowledge bridge, search, indexing       |
| `plugin`    | Optional udos-\* domain capability       |
| `surface`   | UI surface served by uCore               |
| `tool`      | Dev tool integration (docker, git, etc.) |

### Distinction Matrix

| Scope Type                  | Typical Kind                               | Runtime Coupling to uCore                      | Naming Pattern   | Examples                                                             |
| --------------------------- | ------------------------------------------ | ---------------------------------------------- | ---------------- | -------------------------------------------------------------------- |
| Core companion extension    | `workflow`, `knowledge`, `tool`, `surface` | often required for active routes               | no strict prefix | `uflow`, `uknowledge`                                                |
| Domain plugin extension     | `plugin`                                   | usually optional and preflight-gated           | `udos-*`         | `udos-identity`, `udos-google`, `udos-dreamscape`, `udos-publishing` |
| Independent project/surface | n/a unless onboarded                       | may consume uCore but can evolve independently | project-specific | Groovebox, HomeNest, SonicScrewdriver                                |

## Discovery

The registry scans these locations (in order):

1. `backend/app/extensions/manifests/` — manifests bundled with uCore
2. `~/.ucore/extensions/` — user-installed extension manifests
3. Any extra paths passed to `registry.discover(paths=[...])`
4. Any paths listed in `UCORE_EXTENSION_MANIFEST_PATHS` (colon-separated)

Built-in core extensions (`ucore-core`, `ucore-skills`, `ucore-surfaces`,
`ucore-secrets`, `ucore-tools`) are registered programmatically at
registry init and do not require manifest files.

At route assembly time, uCore runs discovery before extension route
registration, so newly added external manifests are picked up without
adding in-core route ownership.

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
  import runtime-owned Ceefax/BBCSDL registrars from external runtime package
  if missing -> raise RuntimeError
  terminal runtime WS route can also be delegated via
  UCORE_TERMINAL_RUNTIME_WS_HANDLER
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
- Runtime adapter behavior is strict external by default; missing external
  runtime providers are hard failures.
- Legacy in-core runtime modules were removed from uCore:
  `backend/app/ucode/ceefax.py`, `backend/app/ucode/bbcsdl.py`, and
  `backend/app/api/terminal_runtime.py`.

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
3. **Phase 3 (done):** Workflow extraction/deletion waves with parity checks
4. **Phase 4 (done):** Knowledge extraction/deletion waves with parity checks
5. **Phase 5 (active):** CI/CD alignment, package publication, and split-repo install smoke tests
6. **Phase 6 (done):** Capability preflight gates enforced across S-pages
7. **Phase 7 (planned):** External plugin matrix execution (`udos-*` repo migration waves)
8. **Phase 8 (planned):** Dead settings and compatibility-note cleanup across docs/scripts
9. **Phase 9 (planned):** Release cutover with stop-the-line evidence bundle per wave

## External Plugin Migration Matrix (Phase 7)

This matrix defines the first `udos-*` migration targets beyond `udos-home`.
Each row must complete route ownership transfer, capability preflight parity,
and wave evidence bundles before marking done.

| Plugin ID         | Owner Repo            | Route Prefix        | Capability Scope                | Dependencies                         | Acceptance Gates                 |
| ----------------- | --------------------- | ------------------- | ------------------------------- | ------------------------------------ | -------------------------------- |
| `udos-home`       | HomeNest module       | `/api/home/*`       | Home operations + shell tasks   | `ucore-core`, `ucore-secrets`        | preflight + route parity + docs  |
| `udos-budget`     | new `udos-budget`     | `/api/budget/*`     | Budget tracking + policy gates  | `ucore-core`, `ucore-secrets`        | preflight + route parity + tests |
| `udos-identity`   | new `udos-identity`   | `/api/identity/*`   | Identity profile + auth helpers | `ucore-core`, `ucore-secrets`        | preflight + route parity + tests |
| `udos-media`      | new `udos-media`      | `/api/media/*`      | Media ingest + transform hooks  | `ucore-core`, `ucore-tools`          | preflight + route parity + tests |
| `udos-automation` | new `udos-automation` | `/api/automation/*` | Automation orchestration        | `ucore-core`, `uflow`, `ucore-tools` | preflight + route parity + tests |

Wave execution guidance:

1. Migrate one plugin per wave branch to keep rollback clean.
2. Add/update `ucore-extension.json` in plugin repo before enabling routes in uCore.
3. Keep endpoint contracts stable; only module ownership changes.
4. Require `scripts/validate_extension_manifests.py` pass before merge.

Execution should prefer explicit repair flows over fallback behavior for
required capability paths.

## uVector Position (Current)

`uVector` is currently best treated as an **extension-class engine candidate**
aligned with future uCode rendering profiles, not as a `udos-*` domain
plugin.

Evidence from `uVector` repository:

1. `Cargo.toml` and crate metadata position it as `uvcore`, a universal
   vector conversion engine.
2. `src/lib.rs` explicitly describes SVG-to-multiple-target conversion,
   including grid/cell and ASCII/teletext outputs.
3. `docs/NANO_BANANA_UVECTOR_SUMMARY.md` describes likely integration with
   Gemini/Nano-Banana style image generation workflows.

Current recommended interpretation:

1. uVector aligns with future uCode and grid-runtime rendering
   concerns.
2. uVector may also be consumed by Google/Nano-Banana image-generation flows
   as a conversion/post-processing engine.
3. uVector is a strong fit for vector/font asset conversion into bitmap/grid
   uCode-compatible formats.
4. Do not force immediate migration; document as extension-class and onboard
   via manifest when integration wave starts.
