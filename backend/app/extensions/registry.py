"""Extension Registry — discover, load, and query extensions.

The registry is the central bookkeeper. It holds manifests for every
known extension (whether loaded from disk or declared inline by uCore
for its own built-in capabilities).

At startup uCore calls:
  1. registry.discover()   — scan known locations for manifest files
  2. registry.load_all()   — import and call setup() on each extension
  3. registry.register_routes(app) — wire in route registrars

Adapters (stubs that delegate to real implementations) use the registry
to decide whether to call the external package or return stub responses.
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from .manifest import ExtensionKind, ExtensionManifest

log = logging.getLogger("ucore.extensions.registry")

# ── Discovery paths ──────────────────────────────────────────────────

MANIFEST_FILE_NAME = "ucore-extension.json"
"""Each extension repo/package places this file at its root."""

DISCOVERY_PATHS: list[Path] = [
    Path(__file__).parent.parent / "extensions" / "manifests",
    Path.home() / ".ucore" / "extensions",
]
"""Default search locations for extension manifests."""

# Known external package paths for split-repo dev mode
_EXTERNAL_REPO_PATHS: dict[str, str] = {
    "uflow": "UCORE_UFLOW_PATH",
    "uknowledge": "UCORE_UKNOWLEDGE_PATH",
}


def _env_discovery_paths() -> list[Path]:
    """Read additional manifest discovery roots from environment.

    `UCORE_EXTENSION_MANIFEST_PATHS` accepts colon-separated paths.
    """
    raw = os.environ.get("UCORE_EXTENSION_MANIFEST_PATHS", "").strip()
    if not raw:
        return []

    paths: list[Path] = []
    for part in raw.split(":"):
        value = part.strip()
        if value:
            paths.append(Path(value).expanduser())
    return paths


def _add_external_path(ext_id: str) -> None:
    """Add a known external package repo to sys.path for import.

    Uses env var if set, otherwise defaults to ~/Code/{ext_id}.
    Only adds the path if it exists on disk.
    """
    default = str(Path.home() / "Code" / ext_id.title() if ext_id == "uflow" else Path.home() / "Code" / ext_id)
    # Normalise: uflow -> ~/Code/uFlow, uknowledge -> ~/Code/uKnowledge
    repo_name_map = {"uflow": "uFlow", "uknowledge": "uKnowledge"}
    repo_dir = repo_name_map.get(ext_id, ext_id)
    default = str(Path.home() / "Code" / repo_dir)

    env_key = _EXTERNAL_REPO_PATHS.get(ext_id, "")
    hint = os.environ.get(env_key, default) if env_key else default
    path = Path(hint).expanduser()
    if path.exists():
        sys.path.insert(0, str(path))
        log.debug("External path added for %s: %s", ext_id, path)


class ExtensionRegistry:
    """Central registry for all known extensions."""

    def __init__(self) -> None:
        self._manifests: dict[str, ExtensionManifest] = {}
        self._loaded: dict[str, bool] = {}
        self._errors: dict[str, str] = {}
        self._register_builtins()

    # ── Built-in core extensions ────────────────────────────────────

    def _register_builtins(self) -> None:
        """Declare uCore's own capabilities as extensions.

        These are never externalised — they represent the core runtime
        shell that the handoff guardrails say must stay in uCore.
        """
        builtins: list[dict[str, Any]] = [
            {
                "id": "ucore-core",
                "name": "uCore Runtime Shell",
                "kind": ExtensionKind.CORE,
                "description": "Host daemon, skills engine, secret store, MCP bridge, shell surfaces, and extension registry",
                "optional": False,
                "api_prefix": "/api",
            },
            {
                "id": "ucore-skills",
                "name": "Skills Engine",
                "kind": ExtensionKind.CORE,
                "description": "Skill discovery, execution, and built-in skills",
                "optional": False,
                "api_prefix": "/api/skills",
            },
            {
                "id": "ucore-surfaces",
                "name": "Surface Server",
                "kind": ExtensionKind.SURFACE,
                "description": "Dashboard and host-shell UI surfaces; uCode runtime content is bridged, not owned",
                "optional": False,
            },
            {
                "id": "ucore-secrets",
                "name": "Secret Store",
                "kind": ExtensionKind.CORE,
                "description": "AES-256-GCM encrypted secret store",
                "optional": False,
                "api_prefix": "/api/secrets",
            },
            {
                "id": "ucore-tools",
                "name": "Dev Tools",
                "kind": ExtensionKind.TOOL,
                "description": "Docker, Git, GitHub CLI, Ollama, Node, Python, VS Code tool integrations",
                "optional": True,
                "api_prefix": "/api/tools",
            },
            # Workflow — declared here, routes owned by uFlow
            {
                "id": "uflow",
                "name": "Workflow Engine",
                "kind": ExtensionKind.WORKFLOW,
                "description": "Workflow definitions, runs, logs, task orchestration",
                "optional": False,
                "api_prefix": "/api/workflows",
                "entrypoint": "uflow.setup",
                "route_registrar": "uflow.routes.register_routes",
            },
            # Knowledge — declared here, routes owned by uKnowledge
            {
                "id": "uknowledge",
                "name": "Knowledge Bridge",
                "kind": ExtensionKind.KNOWLEDGE,
                "description": "Vault search, semantic search, knowledge layer, vault indexing",
                "optional": False,
                "api_prefix": "/api/knowledge",
                "entrypoint": "uknowledge.setup",
                "route_registrar": "uknowledge.routes.register_routes",
            },
        ]
        for raw in builtins:
            manifest = ExtensionManifest.from_dict(raw)
            self._manifests[manifest.id] = manifest
            log.debug("Registered built-in extension: %s", manifest.id)

    # ── Discovery ───────────────────────────────────────────────────

    def discover(self, extra_paths: list[Path] | None = None) -> int:
        """Scan discovery paths for external extension manifests.

        Returns the number of newly discovered extensions.
        """
        paths = list(DISCOVERY_PATHS)
        paths.extend(_env_discovery_paths())
        if extra_paths:
            paths.extend(extra_paths)

        discovered = 0
        for base in paths:
            if not base.exists():
                continue
            for manifest_file in base.rglob(MANIFEST_FILE_NAME):
                try:
                    raw = json.loads(manifest_file.read_text())
                    manifest = ExtensionManifest.from_dict(raw)
                    if manifest.id not in self._manifests:
                        self._manifests[manifest.id] = manifest
                        discovered += 1
                        log.info(
                            "Discovered extension: %s (%s)",
                            manifest.id, manifest_file,
                        )
                except Exception as exc:
                    log.warning(
                        "Failed to load manifest %s: %s",
                        manifest_file, exc,
                    )
        return discovered

    # ── Registration API ────────────────────────────────────────────

    def register(self, manifest: ExtensionManifest) -> None:
        """Programmatically register an extension manifest."""
        self._manifests[manifest.id] = manifest
        log.info("Registered extension: %s", manifest.id)

    def unregister(self, extension_id: str) -> bool:
        """Remove an extension from the registry."""
        if extension_id in self._manifests:
            del self._manifests[extension_id]
            self._loaded.pop(extension_id, None)
            self._errors.pop(extension_id, None)
            return True
        return False

    # ── Loading ─────────────────────────────────────────────────────

    def load_all(self, app: Any | None = None) -> dict[str, bool]:
        """Load all registered extensions.

        For each extension with an entrypoint, imports the module
        and calls `setup(app)`. Stub-only extensions are marked loaded.

        Returns a dict of {extension_id: success}.
        """
        results: dict[str, bool] = {}
        for ext_id, manifest in self._manifests.items():
            if ext_id in self._loaded:
                results[ext_id] = self._loaded[ext_id]
                continue

            if manifest.entrypoint is None:
                # No entrypoint means stub-only or route-only extension
                self._loaded[ext_id] = True
                results[ext_id] = True
                continue

            try:
                mod_path, func_name = manifest.entrypoint.rsplit(".", 1)
                mod = importlib.import_module(mod_path)
                setup_fn = getattr(mod, func_name)
                if app is not None:
                    setup_fn(app)
                else:
                    setup_fn()
                self._loaded[ext_id] = True
                results[ext_id] = True
                log.info("Loaded extension: %s", ext_id)
            except Exception as exc:
                self._loaded[ext_id] = False
                self._errors[ext_id] = str(exc)
                results[ext_id] = False
                if not manifest.optional:
                    log.error(
                        "Required extension %s failed to load: %s",
                        ext_id, exc,
                    )
                else:
                    log.warning(
                        "Optional extension %s failed to load: %s",
                        ext_id, exc,
                    )
        return results

    def register_routes(self, app: Any) -> None:
        """Call route_registrar for every extension that has one.

        On ImportError for external packages (uflow, uknowledge), adds the
        local repo path to sys.path and retries before failing.
        """
        for ext_id, manifest in self._manifests.items():
            if manifest.route_registrar is None:
                continue
            try:
                mod_path, func_name = manifest.route_registrar.rsplit(".", 1)
                mod = importlib.import_module(mod_path)
                register_fn = getattr(mod, func_name)
                register_fn(app)
                self._loaded[ext_id] = True
                self._errors.pop(ext_id, None)
                log.debug(
                    "Routes registered for extension: %s", ext_id,
                )
            except ImportError:
                # Path-discovery fallback for external split-repo packages
                _add_external_path(ext_id)
                try:
                    mod_path, func_name = manifest.route_registrar.rsplit(".", 1)
                    mod = importlib.import_module(mod_path)
                    register_fn = getattr(mod, func_name)
                    register_fn(app)
                    self._loaded[ext_id] = True
                    self._errors.pop(ext_id, None)
                    log.info(
                        "Routes registered for extension %s (path-discovered)",
                        ext_id,
                    )
                except ImportError:
                    self._loaded[ext_id] = False
                    self._errors[ext_id] = "Route registrar import failed"
                    if manifest.optional:
                        log.debug(
                            "Extension %s route registrar not available "
                            "(optional, skipping): %s",
                            ext_id, manifest.route_registrar,
                        )
                    else:
                        log.exception(
                            "Required extension %s route registrar failed",
                            ext_id,
                        )
                        raise
            except Exception:
                self._loaded[ext_id] = False
                self._errors[ext_id] = "Route registration failed"
                log.exception(
                    "Failed to register routes for extension: %s",
                    ext_id,
                )
                if not manifest.optional:
                    raise

    # ── Queries ─────────────────────────────────────────────────────

    def get(self, extension_id: str) -> ExtensionManifest | None:
        """Get a manifest by id."""
        return self._manifests.get(extension_id)

    def list_all(self) -> list[ExtensionManifest]:
        """Return all registered manifests."""
        return list(self._manifests.values())

    def list_by_kind(self, kind: ExtensionKind) -> list[ExtensionManifest]:
        """Return manifests filtered by kind."""
        return [m for m in self._manifests.values() if m.kind == kind]

    def is_loaded(self, extension_id: str) -> bool:
        """Check if an extension has been successfully loaded."""
        return self._loaded.get(extension_id, False)

    def status(self) -> dict[str, Any]:
        """Return a health summary of the extension registry."""
        manifests = self.list_all()
        loaded_count = sum(1 for m in manifests if self._loaded.get(m.id, False))
        return {
            "total": len(manifests),
            "loaded": loaded_count,
            "failed": len(self._errors),
            "errors": dict(self._errors),
            "extensions": [
                {
                    "id": m.id,
                    "name": m.name,
                    "kind": m.kind.value,
                    "version": m.version,
                    "loaded": self._loaded.get(m.id, False),
                    "optional": m.optional,
                    "error": self._errors.get(m.id),
                }
                for m in manifests
            ],
        }


# ── Singleton ───────────────────────────────────────────────────────

registry = ExtensionRegistry()
