# Plugin Release Checklist

This checklist is required for release cutovers involving extension manifests
and capability preflight parity.

## Scope

Applies to plugin and split-repo releases for:

1. `uflow`
2. `uknowledge`
3. `ucode-runtime`
4. `udos-*` plugins discovered via manifest paths

## Pre-Release Gates

1. Manifest contract validation
   - Run: `python3 scripts/validate_extension_manifests.py`
   - All manifests pass strict field/type/dependency checks.

2. Split-repo packaging validation
   - Run: `python3 scripts/validate_split_repo_packaging.py`
   - `uflow`, `uknowledge`, and `ucode-runtime` have publishable Python metadata/layout.

3. Split-repo import and route smoke
   - Run: `python3 scripts/smoke_split_repo_imports.py`
   - External imports pass and required extension routes register.

4. Capability requirements non-regression
   - Run: `python3 scripts/validate_capability_requirements.py`
   - Capability map remains complete and valid.

## Capability Preflight Parity

For each capability affected by plugin/repo changes:

1. Verify extension readiness:
   - `GET /api/extensions/status`
2. Verify capability readiness snapshot:
   - `GET /api/capabilities/readiness`
3. Verify targeted capability preflight:
   - `GET /api/capabilities/{capability}/preflight`

Required result:

1. No missing required extensions for active capability paths.
2. `repair_required` is `false` for validated capabilities.
3. Any `412` response blocks release until fixed and re-validated.

## Plugin Manifest Checklist

For each plugin manifest (`ucore-extension.json`):

1. `id`, `name`, `kind` present and valid.
2. `route_registrar` dotted path resolves in runtime environment.
3. `dependencies` reference known extension IDs only.
4. `api_prefix` matches owned route namespace.
5. `optional` flag matches intended blast radius.

## Release Evidence Bundle

Each release must include:

1. Changed files list.
2. Commands executed and outputs for all gate checks.
3. Route proof summary for extension-owned endpoints.
4. Capability preflight parity summary (`/status`, `/readiness`, `/preflight`).

If any gate fails: stop-the-line, repair, rerun, and only then proceed.
