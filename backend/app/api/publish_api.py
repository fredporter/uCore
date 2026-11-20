"""Publish API — Local First Library Delivery REST Endpoints.

Provides:
- POST /api/publish/binder — compiles fixture binder into offline Tomb bundle.
"""

from __future__ import annotations

import asyncio
import logging

from aiohttp import web

from app.api.connections_api import profile
from app.services import publish_service
from app.services.identity import get_full_identity

log = logging.getLogger("ucore.publish_api")


async def handle_publish_binder(request: web.Request) -> web.Response:
    """POST /api/publish/binder — compile binder from ~/Shared/fixtures/fixture.json to Tomb bundle."""
    identity = get_full_identity()
    profile(request, identity=identity)
    role = (identity.get("active_profile") or {}).get("role", "")
    if role not in {"wizard", "owner"}:
        return web.json_response({"error": "The shared publishing fixture requires a Wizard profile."}, status=403)

    try:
        result = await asyncio.to_thread(publish_service.compile_binder_to_tomb)
        return web.json_response(result)
    except FileNotFoundError as fnf:
        log.error("Fixture or file not found: %s", fnf)
        return web.json_response({"error": "Publishing fixture not found."}, status=404)
    except ValueError as ve:
        log.error("Validation error during binder publishing: %s", ve)
        return web.json_response({"error": "Publishing fixture is invalid."}, status=422)
    except Exception as e:
        log.exception("Unexpected error compiling binder to tomb: %s", e)
        return web.json_response({"error": "Could not compile the publishing fixture."}, status=500)


def register_publish_routes(app: web.Application) -> None:
    """Register publishing API routes."""
    app.router.add_post("/api/publish/binder", handle_publish_binder)
    log.debug("Publishing API routes registered")
