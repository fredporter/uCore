"""Workflow adapter — hard-cut delegation to uFlow.

Wave A removes uCore fallback behavior for workflow routes.
uCore now requires external uFlow route registration for workflow endpoint registration.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("ucore.adapters.workflow")


def _ensure_uflow_path() -> None:
    """Add local uFlow repo path for import when running in split-repo dev mode."""
    hint = os.environ.get("UCORE_UFLOW_PATH", str(Path.home() / "Code" / "uFlow"))
    path = Path(hint)
    if path.exists():
        sys.path.insert(0, str(path))


def register_routes(app):
    """Register workflow routes via the external uFlow package only."""
    try:
        from uflow.routes import register_routes as register_uflow_routes
    except ImportError as exc:
        _ensure_uflow_path()
        try:
            from uflow.routes import register_routes as register_uflow_routes
        except ImportError as exc2:
            raise RuntimeError(
                "uFlow is required for workflow route registration in Wave A hard-cut mode. "
                "Install uFlow and expose uflow.routes.register_routes(app).",
            ) from exc2

    register_uflow_routes(app)
    log.info("Workflow routes registered (provider=uflow-external)")