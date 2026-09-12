"""Identity Subsystem — Sovereign local identity, profile management, and WordPress RBAC mapping."""

from __future__ import annotations

from aiohttp import web

from .routes import register_routes
from .story_store import IdentityStoryStore
from .wordpress_mapper import map_from_wordpress, map_to_wordpress


def setup(app: web.Application) -> None:
    """Run extension lifecycle setup."""
    pass


__all__ = [
    "IdentityStoryStore",
    "map_from_wordpress",
    "map_to_wordpress",
    "register_routes",
    "setup",
]
