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
                "delay_seconds": config.delay_seconds,
                "enabled": config.enabled,
                "planned": bool(row),
                "occurrences": store.list_occurrences(schedule_id, limit=limit),
            }
        )
    schedules.sort(key=lambda item: item["schedule_id"])
    return web.json_response({"schedules": schedules, "count": len(schedules)})


def _require_schedule_admin(request: web.Request):
    """Owner or wizard, an explicit confirm header, and the caller's own profile."""
    from app.api.connections_api import profile
    from app.services.identity import get_full_identity

    owner = profile(request)
    identity = get_full_identity()
    role = str((identity.get("active_profile") or {}).get("role", "")).casefold()
    if identity.get("active_profile_id") != owner or role not in {"owner", "wizard"}:
        return None, web.json_response(
            {"error": "Only a local administrator can change schedules"}, status=403
        )
    if request.headers.get("x-ucore-confirm") != "true":
        return None, web.json_response(
            {"error": "Confirm the schedule change first"}, status=409
        )
    return owner, None


def _schedule_from_body(body: dict, *, schedule_id: str, owner: str, revision: int):
    from app.services.timing import Schedule

    return Schedule(
        schedule_id=schedule_id,
        workflow_id=str(body.get("workflow_id", "")).strip(),
        owner=owner,
        kind=str(body.get("kind", "calendar")).strip() or "calendar",
        revision=revision,
        timezone=str(body.get("timezone", "UTC")).strip() or "UTC",
        local_time=str(body.get("local_time", "09:00")).strip() or "09:00",
        delay_seconds=int(body.get("delay_seconds", 0) or 0),
        enabled=bool(body.get("enabled", True)),
    )


async def handle_schedule_create(request: web.Request) -> web.Response:
    """POST /api/host/schedules — add one reviewed schedule."""
    from app.services.timing import (
        ScheduleError,
        load_schedules,
        schedule_to_payload,
        write_schedules,
    )

    owner, refusal = _require_schedule_admin(request)
    if refusal is not None:
        return refusal

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "Expected an object"}, status=400)

    schedule_id = str(body.get("schedule_id", "")).strip()
    if not schedule_id or len(schedule_id) > 64 or any(ch.isspace() for ch in schedule_id):
        return web.json_response(
            {"error": "schedule_id is required (max 64 characters, no spaces)"}, status=400
        )

    try:
        existing = load_schedules()
    except ScheduleError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    if any(item.schedule_id == schedule_id for item in existing):
        return web.json_response({"error": "schedule_id already exists"}, status=409)

    try:
        schedule = _schedule_from_body(body, schedule_id=schedule_id, owner=owner, revision=1)
    except ScheduleError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except (TypeError, ValueError) as exc:
        return web.json_response({"error": f"invalid field: {exc}"}, status=400)

    from app.flow.workflow_api import get_workflow_manager

    if get_workflow_manager().get_workflow(schedule.workflow_id, owner=owner) is None:
        return web.json_response(
            {"error": f"workflow not found: {schedule.workflow_id}"}, status=400
        )

    write_schedules([*existing, schedule])
    _plan_new_schedule(schedule)
    return web.json_response({"schedule": schedule_to_payload(schedule)}, status=201)


def _plan_new_schedule(schedule) -> None:
    """Plan the upcoming window so the operator sees occurrences immediately."""
    from app.services.timing import TimingStore, plan_calendar_window

    try:
        plan_calendar_window(TimingStore(), [schedule])
    except Exception:  # noqa: BLE001 - the schedule is saved; planning retries next cycle
        pass


async def handle_schedule_update(request: web.Request) -> web.Response:
    """PATCH /api/host/schedules/{schedule_id} — revise timing or enablement."""
    from app.services.timing import (
        ScheduleError,
        TimingStore,
        load_schedules,
        plan_calendar_window,
        schedule_to_payload,
        write_schedules,
    )

    owner, refusal = _require_schedule_admin(request)
    if refusal is not None:
        return refusal

    schedule_id = request.match_info["schedule_id"]
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "Expected an object"}, status=400)

    try:
        existing = load_schedules()
    except ScheduleError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    current = next((item for item in existing if item.schedule_id == schedule_id), None)
    if current is None:
        return web.json_response({"error": "schedule not found"}, status=404)

    merged = {**schedule_to_payload(current), **body}
    try:
        revised = _schedule_from_body(
            merged,
            schedule_id=schedule_id,
            owner=current.owner,
            revision=current.revision + 1,
        )
    except ScheduleError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except (TypeError, ValueError) as exc:
        return web.json_response({"error": f"invalid field: {exc}"}, status=400)

    if revised.workflow_id != current.workflow_id:
        from app.flow.workflow_api import get_workflow_manager

        if get_workflow_manager().get_workflow(revised.workflow_id, owner=current.owner) is None:
            return web.json_response(
                {"error": f"workflow not found: {revised.workflow_id}"}, status=400
            )

    write_schedules([revised if item.schedule_id == schedule_id else item for item in existing])
    plan_calendar_window(TimingStore(), [revised])
    return web.json_response({"schedule": schedule_to_payload(revised)})


async def handle_schedule_delete(request: web.Request) -> web.Response:
    """DELETE /api/host/schedules/{schedule_id} — stop scheduling one workflow.

    The reviewed config row is removed, the planned schedule row is forgotten and
    unfinished occurrences are skipped with a reason, so a delete cannot leave a
    run armed. Completed history stays for receipts.
    """
    from app.services.timing import ScheduleError, TimingStore, load_schedules, write_schedules

    owner, refusal = _require_schedule_admin(request)
    if refusal is not None:
        return refusal

    schedule_id = request.match_info["schedule_id"]
    try:
        existing = load_schedules()
    except ScheduleError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    remaining = [item for item in existing if item.schedule_id != schedule_id]
    if len(remaining) == len(existing):
        return web.json_response({"error": "schedule not found"}, status=404)

    write_schedules(remaining)
    skipped = TimingStore().remove_schedule(schedule_id)
    return web.json_response(
        {"deleted": schedule_id, "remaining": len(remaining), "skipped_occurrences": skipped}
    )


def register_observation_routes(app: web.Application) -> None:
    app.router.add_post("/api/host/observations", handle_observation)
    app.router.add_post("/api/host/observations/dispatch", handle_dispatch)
    app.router.add_post("/api/host/schedules/tick", handle_schedule_tick)
    app.router.add_get("/api/host/schedules", handle_schedules)
    app.router.add_post("/api/host/schedules", handle_schedule_create)
    app.router.add_patch("/api/host/schedules/{schedule_id}", handle_schedule_update)
    app.router.add_delete("/api/host/schedules/{schedule_id}", handle_schedule_delete)
