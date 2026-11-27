"""Observation intake endpoint for the Gate B fixture harness.

Accepts data only. It grants no authority and admits no workflow; a transition
must still pass review before it can trigger a run.
"""
from __future__ import annotations

from aiohttp import web

from app.services.observation_intake import (
    ObservationError,
    ObservationStore,
    parse_observation,
)


async def handle_observation(request: web.Request) -> web.Response:
    """POST /api/host/observations — admit one bounded observation."""
    from app.services.execution_authority import active_identity

    identity = active_identity()
    if not identity.get("authenticated", True):
        return web.json_response(
            {"error": "Authenticate a local profile to submit observations"}, status=403
        )

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "Expected an object"}, status=400)

    try:
        observation = parse_observation(body)
    except ObservationError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    result = ObservationStore().ingest(observation)
    return web.json_response(result)


def register_observation_routes(app: web.Application) -> None:
    app.router.add_post("/api/host/observations", handle_observation)
