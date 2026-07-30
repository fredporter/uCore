"""Knowledge adapter — hard-cut delegation to uKnowledge.

Wave B removes uCore fallback behavior for knowledge routes.
uCore now requires uKnowledge ownership for knowledge endpoint registration.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("ucore.adapters.knowledge")


def _ensure_uknowledge_path() -> None:
    """Add local uKnowledge repo path for import when running in split-repo dev mode."""
    hint = os.environ.get(
        "UCORE_UKNOWLEDGE_PATH",
        str(Path.home() / "Code" / "uKnowledge"),
    )
    path = Path(hint)
    if path.exists():
        sys.path.insert(0, str(path))

def register_routes(app):
    """Register knowledge routes via the external uKnowledge package only."""
    try:
        from uknowledge.routes import register_routes as register_uknowledge_routes
    except ImportError as exc:
        _ensure_uknowledge_path()
        try:
            from uknowledge.routes import register_routes as register_uknowledge_routes
        except ImportError as exc2:
            raise RuntimeError(
                "uKnowledge is required for knowledge routes in Wave B hard-cut mode. "
                "Install uKnowledge and expose uknowledge.routes.register_routes(app).",
            ) from exc2

    register_uknowledge_routes(app)
    log.info("Knowledge routes registered (provider=uknowledge-external)")