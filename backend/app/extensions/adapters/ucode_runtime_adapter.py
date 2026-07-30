"""uCode runtime route adapter.

This adapter keeps uCore's host routing thin by delegating runtime-owned
Ceefax/BBCSDL route registration to an external runtime package when
available. A compatibility fallback to legacy in-repo modules remains
available while the external runtime package is being finalized.
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("ucore.adapters.ucode_runtime")

DEFAULT_CEEFAX_REGISTRAR = "ucode_runtime.ceefax.register_ceefax_routes"
DEFAULT_BBCSDL_REGISTRAR = "ucode_runtime.bbcsdl.register_bbcsdl_routes"


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _ensure_ucode_path() -> None:
    """Add local uCode repo path for import in split-repo dev mode."""
    hint = os.environ.get("UCORE_UCODE_PATH", str(Path.home() / "Code" / "uCode"))
    path = Path(hint)
    if path.exists():
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _resolve_callable(dotted_path: str) -> Callable[..., Any] | None:
    """Import a callable from `module.symbol`, with local uCode path hinting."""
    try:
        module_path, symbol_name = dotted_path.rsplit(".", 1)
    except ValueError:
        log.warning("Invalid registrar path: %s", dotted_path)
        return None

    try:
        module = importlib.import_module(module_path)
        return getattr(module, symbol_name)
    except Exception:
        _ensure_ucode_path()
        try:
            module = importlib.import_module(module_path)
            return getattr(module, symbol_name)
        except Exception as exc:
            log.debug("Unable to import registrar %s: %s", dotted_path, exc)
            return None


def _ensure_ceefax_store(app: Any, store_key: Any) -> Any:
    if store_key in app:
        return app[store_key]

    from app.ucode.ceefax import CeefaxStore

    app[store_key] = CeefaxStore()
    return app[store_key]


def _register_legacy_runtime_routes(app: Any, store_key: Any) -> None:
    """Compatibility mode while external runtime package is still being cut over."""
    from app.ucode.bbcsdl import register_bbcsdl_routes
    from app.ucode.ceefax import register_ceefax_routes

    store = _ensure_ceefax_store(app, store_key)
    register_ceefax_routes(app, store)
    register_bbcsdl_routes(app, store)
    log.warning("uCode runtime routes registered via legacy in-repo provider")


def register_routes(app: Any, ceefax_store_key: Any) -> None:
    """Register Ceefax/BBCSDL routes via external runtime registrars when available."""
    require_external = _is_truthy(os.environ.get("UCORE_UCODE_RUNTIME_REQUIRE_EXTERNAL", "0"))

    ceefax_registrar = os.environ.get("UCORE_CEEFAX_ROUTE_REGISTRAR", DEFAULT_CEEFAX_REGISTRAR)
    bbcsdl_registrar = os.environ.get("UCORE_BBCSDL_ROUTE_REGISTRAR", DEFAULT_BBCSDL_REGISTRAR)

    ceefax_register = _resolve_callable(ceefax_registrar)
    bbcsdl_register = _resolve_callable(bbcsdl_registrar)

    if ceefax_register and bbcsdl_register:
        store = _ensure_ceefax_store(app, ceefax_store_key)
        ceefax_register(app, store)
        bbcsdl_register(app, store)
        log.info("uCode runtime routes registered (provider=external-runtime)")
        return

    if require_external:
        raise RuntimeError(
            "External uCode runtime registrars are required but unavailable. "
            "Set UCORE_UCODE_PATH and provide route registrars for Ceefax/BBCSDL.",
        )

    _register_legacy_runtime_routes(app, ceefax_store_key)
