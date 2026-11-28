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


async def handle_dispatch(request: web.Request) -> web.Response:
    """POST /api/host/observations/dispatch — admit pending transitions."""
    from app.flow.workflow_api import get_workflow_manager
    from app.services.execution_authority import active_identity
    from app.services.transition_bindings import BindingError, load_bindings
    from app.services.transition_dispatch import dispatch_transitions

    identity = active_identity()
    if not identity.get("authenticated", True):
        return web.json_response(
            {"error": "Authenticate a local profile to dispatch transitions"}, status=403
        )

    try:
        bindings = load_bindings()
    except BindingError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    results = await dispatch_transitions(
        ObservationStore(), get_workflow_manager(), bindings
    )
    return web.json_response({"count": len(results), "results": results})


async def handle_schedule_tick(request: web.Request) -> web.Response:
    """POST /api/host/schedules/tick — plan reviewed schedules and admit due work."""
    from app.services.execution_authority import active_identity
    from app.services.maintenance_scheduler import admit_timed_occurrences

    identity = active_identity()
    if not identity.get("authenticated", True):
        return web.json_response(
            {"error": "Authenticate a local profile to tick schedules"}, status=403
        )

    results = await admit_timed_occurrences()
    return web.json_response({"count": len(results), "results": results})


async def handle_schedules(request: web.Request) -> web.Response:
    """GET /api/host/schedules — reviewed schedules and their recent occurrences.

    Read-only: no admission, no authority. Run ids link an occurrence to the run
    the Gate A contract created, so scheduled work is visible without opening
    the database.
    """
    from app.services.execution_authority import active_identity
    from app.services.timing import TimingStore, load_schedules

    identity = active_identity()
    if not identity.get("authenticated", True):
        return web.json_response(
            {"error": "Authenticate a local profile to read schedules"}, status=403
        )

    try:
        limit = int(request.query.get("limit", "10"))
    except ValueError:
        return web.json_response({"error": "limit must be an integer"}, status=400)

    store = TimingStore()
    planned = {item.schedule_id: item for item in load_schedules()}
    rows = {row["schedule_id"]: row for row in store.list_schedules()}

    schedules: list[dict] = []
    for schedule_id, config in planned.items():
        row = rows.get(schedule_id, {})
        schedules.append(
            {
                "schedule_id": schedule_id,
                "workflow_id": config.workflow_id,
                "kind": config.kind,
                "revision": config.revision,
                "timezone": config.timezone,
                "local_time": config.local_time,
                "enabled": config.enabled,
                "planned": bool(row),
                "occurrences": store.list_occurrences(schedule_id, limit=limit),
            }
        )
    schedules.sort(key=lambda item: item["schedule_id"])
    return web.json_response({"schedules": schedules, "count": len(schedules)})


def register_observation_routes(app: web.Application) -> None:
    app.router.add_post("/api/host/observations", handle_observation)
    app.router.add_post("/api/host/observations/dispatch", handle_dispatch)
    app.router.add_post("/api/host/schedules/tick", handle_schedule_tick)
    app.router.add_get("/api/host/schedules", handle_schedules)
