"""Snackbar package — modular daemon for uCore.

Route handlers are split into modules under ``snackbar/modules/`` and loaded
dynamically by ``core/snackbar.py``.  Each module exposes a ``register(app)``
function that receives the aiohttp Application and registers its routes.

The canonical app factory lives in ``app.core.snackbar.create_app()``.
"""
from __future__ import annotations

from app.core.snackbar import create_app, main

__all__ = ["create_app", "main"]
