"""uCode runtime route adapter.

This adapter keeps uCore's host routing thin by delegating runtime-owned
Ceefax/BBCSDL route registration to an external runtime package.
Missing runtime providers are treated as hard failures.
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
DEFAULT_TERMINAL_WS_HANDLER = "ucode_runtime.terminal_runtime.handle_terminal_runtime_ws"
DEFAULT_SESSION_WS_HANDLER = "ucode_runtime.session_runtime.handle_ucode_session_ws"
DEFAULT_LIBRARY_REGISTRAR = "ucode_runtime.software_library.register_software_library_routes"
DEFAULT_INFO_REGISTRAR = "ucode_runtime.runtime_info.register_runtime_info_routes"
DEFAULT_CEEFAX_STORE_FACTORY = "ucode_runtime.ceefax.CeefaxStore"

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

    # uCode owns its runtime. In split-repo development the active uCode
    # checkout must win over any older package already present in the host
    # environment, otherwise Terminal can silently bind to stale behaviour.
    _ensure_ucode_path()
    try:
        module = importlib.import_module(module_path)
        return getattr(module, symbol_name)
    except Exception:
        try:
            module = importlib.import_module(module_path)
            return getattr(module, symbol_name)
        except Exception as exc:
            log.debug("Unable to import registrar %s: %s", dotted_path, exc)
            return None


def _ensure_ceefax_store(app: Any, store_key: Any, factory_path: str) -> Any:
    if store_key in app:
        return app[store_key]

    store_factory = _resolve_callable(factory_path)
    if store_factory is None:
        raise RuntimeError(
            f"Unable to resolve Ceefax store factory: {factory_path}",
        )

    app[store_key] = store_factory()
    return app[store_key]


def register_routes(app: Any, ceefax_store_key: Any) -> None:
    """Register Ceefax/BBCSDL routes via external runtime registrars."""
    ceefax_registrar = os.environ.get("UCORE_CEEFAX_ROUTE_REGISTRAR", DEFAULT_CEEFAX_REGISTRAR)
    bbcsdl_registrar = os.environ.get("UCORE_BBCSDL_ROUTE_REGISTRAR", DEFAULT_BBCSDL_REGISTRAR)
    ceefax_store_factory = os.environ.get(
        "UCORE_CEEFAX_STORE_FACTORY",
        DEFAULT_CEEFAX_STORE_FACTORY,
    )

    ceefax_register = _resolve_callable(ceefax_registrar)
    bbcsdl_register = _resolve_callable(bbcsdl_registrar)

    if ceefax_register and bbcsdl_register:
        store = _ensure_ceefax_store(app, ceefax_store_key, ceefax_store_factory)
        ceefax_register(app, store)
        bbcsdl_register(app, store)
        log.info("uCode runtime routes registered (provider=external-runtime)")
        return

    raise RuntimeError(
        "External uCode runtime registrars are required but unavailable. "
        "Set UCORE_UCODE_PATH and provide route registrars for Ceefax/BBCSDL.",
    )


def register_terminal_runtime_routes(app: Any) -> None:
    """Register terminal runtime route via external runtime handler."""
    terminal_handler_path = os.environ.get(
        "UCORE_TERMINAL_RUNTIME_WS_HANDLER",
        DEFAULT_TERMINAL_WS_HANDLER,
    )
    terminal_handler = _resolve_callable(terminal_handler_path)

    if terminal_handler is not None:
        app.router.add_get("/api/terminal/runtime/ws", terminal_handler)
        log.info("Terminal runtime route registered (provider=external-runtime)")
        return

    raise RuntimeError(
        "External terminal runtime handler is required but unavailable. "
        "Set UCORE_UCODE_PATH and provide UCORE_TERMINAL_RUNTIME_WS_HANDLER.",
    )


def register_session_runtime_routes(app: Any) -> None:
    """Register the versioned uCode session route via the external runtime."""
    handler_path = os.environ.get(
        "UCORE_UCODE_SESSION_WS_HANDLER",
        DEFAULT_SESSION_WS_HANDLER,
    )
    handler = _resolve_callable(handler_path)
    if handler is None:
        raise RuntimeError(
            "External uCode session handler is unavailable. Set UCORE_UCODE_PATH "
            "or UCORE_UCODE_SESSION_WS_HANDLER."
        )
    app.router.add_get("/api/ucode/runtime/ws", handler)
    log.info("uCode session route registered (protocol=ucode-session/1)")


def register_software_library_routes(app: Any) -> None:
    """Register the uCode-owned curated Software Library API."""
    registrar_path = os.environ.get(
        "UCORE_UCODE_LIBRARY_REGISTRAR",
        DEFAULT_LIBRARY_REGISTRAR,
    )
    registrar = _resolve_callable(registrar_path)
    if registrar is None:
        raise RuntimeError(
            "External uCode Software Library registrar is unavailable. "
            "Set UCORE_UCODE_PATH or UCORE_UCODE_LIBRARY_REGISTRAR."
        )
    registrar(app)
    log.info("uCode Software Library routes registered")


def register_runtime_info_routes(app: Any) -> None:
    """Register the uCode-owned runtime capability manifest."""
    registrar_path = os.environ.get(
        "UCORE_UCODE_INFO_REGISTRAR",
        DEFAULT_INFO_REGISTRAR,
    )
    registrar = _resolve_callable(registrar_path)
    if registrar is None:
        raise RuntimeError(
            "External uCode runtime-info registrar is unavailable. "
            "Set UCORE_UCODE_PATH or UCORE_UCODE_INFO_REGISTRAR."
        )
    registrar(app)
    log.info("uCode runtime capability route registered")
