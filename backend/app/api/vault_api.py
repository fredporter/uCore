"""Vault Topology API — exposes vault layer configuration to the frontend."""
from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web

log = logging.getLogger("ucore.vault_api")

# Canonical vault topology — 3 vault types only.
# ~/Code/ is NOT a vault layer — it is the Developer Lane codebase.
VAULT_LAYERS = [
    {
        "id": "user",
        "label": "User Vault",
        "icon": "mdi:account",
        "description": (
            "Personal workspace — binders, documents, notes, missions, tasks"
        ),
        "path": str(Path.home() / "Vault"),
        "permissions": "read_write",
    },
    {
        "id": "shared",
        "label": "Shared Vaults",
        "icon": "mdi:account-group",
        "description": "Collaborative vaults for team projects",
        "path": str(Path.home() / "Shared"),
        "permissions": "read_write",
    },
    {
        "id": "public",
        "label": "Public Vaults",
        "icon": "mdi:book-open-variant",
        "description": (
            "Published, system-provided, community-contributed vaults"
        ),
        "path": str(Path.home() / "Public"),
        "permissions": "read_only",
    },
]

# Public vault sub-paths (for granular access within ~/Public/)
PUBLIC_SUB_LAYERS = [
    {
        "id": "global-knowledge",
        "label": "Global Knowledge",
        "icon": "mdi:brain",
        "description": "Curated reference material",
        "path": str(
            Path.home() / "Public" / "global-knowledge"
        ),
    },
    {
        "id": "doc-sites",
        "label": "Documentation Sites",
        "icon": "mdi:web",
        "description": "Published documentation sites",
        "path": str(Path.home() / "Public" / "doc-sites"),
    },
    {
        "id": "learning",
        "label": "Learning",
        "icon": "mdi:school",
        "description": "Learning resources and tutorials",
        "path": str(Path.home() / "Public" / "learning"),
    },
]


async def handle_vault_topology(
    request: web.Request,
) -> web.Response:
    """GET /api/vault/topology — vault layer topology with existence status."""
    layers = []
    for layer in VAULT_LAYERS:
        p = Path(layer["path"])
        layers.append({
            **layer,
            "exists": p.exists(),
            "is_dir": p.is_dir() if p.exists() else False,
        })
    return web.json_response({"layers": layers})


async def handle_vault_layers(
    request: web.Request,
) -> web.Response:
    """GET /api/vault/layers — vault layer definitions (simpler form)."""
    return web.json_response({"layers": VAULT_LAYERS})


def register_vault_routes(app: web.Application) -> None:
    """Register vault topology routes."""
    app.router.add_get("/api/vault/topology", handle_vault_topology)
    app.router.add_get("/api/vault/layers", handle_vault_layers)
    log.debug("Vault topology routes registered")
