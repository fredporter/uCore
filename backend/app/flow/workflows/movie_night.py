"""Cross-product durable workflow: Movie Night.

Coordinates HomeNest media playback and Home Assistant lighting scenes.
Enforces explicit partial-failure resilience: HomeNest playback must never
be broken or cancelled if Home Assistant is offline, unavailable, or errors.
Enforces idempotency: scenes are never activated twice on retry.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MovieNightRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_item_id: str = Field(min_length=1)
    target_client: str = "living-room-tv"
    scene_id: str = "scene.movie_night"
    idempotency_key: str | None = None


class MovieNightResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    status: Literal["success", "partial_failure", "failed"]
    media_dispatched: bool
    media_status: str | None = None
    media_error: str | None = None
    scene_activated: bool
    scene_error: str | None = None
    executed_steps: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=_utc_now_iso)


# In-memory deduplication set for idempotency
_EXECUTED_SCENES: set[str] = set()


async def execute_movie_night(
    request: MovieNightRequest,
    homenest_client: Any = None,
    ha_client: Any = None,
    executed_scenes_store: set[str] | None = None,
) -> MovieNightResult:
    """Execute the durable Movie Night workflow with partial-failure isolation."""
    workflow_id = str(uuid.uuid4())[:8]
    steps: list[str] = []
    scenes_store = executed_scenes_store if executed_scenes_store is not None else _EXECUTED_SCENES

    # Step 1: Dispatch media playback via HomeNest
    steps.append("dispatch_homenest_playback")
    media_dispatched = False
    media_status = None
    media_error = None

    try:
        if homenest_client is not None:
            # Can be PlaybackService or an HTTP client
            if hasattr(homenest_client, "handoff"):
                res = homenest_client.handoff(
                    item_id=request.media_item_id,
                    target_client=request.target_client,
                )
            elif hasattr(homenest_client, "post"):
                res = await homenest_client.post(
                    "/api/playback/handoff",
                    json={"item_id": request.media_item_id, "target_client": request.target_client},
                )
            else:
                res = {"success": True, "status": "queued"}

            if isinstance(res, dict) and res.get("success"):
                media_dispatched = True
                media_status = res.get("status", "queued")
                steps.append("homenest_playback_accepted")
            else:
                err_msg = res.get("error", "Unknown HomeNest error") if isinstance(res, dict) else str(res)
                media_error = f"HomeNest rejected handoff: {err_msg}"
        else:
            # Fallback/simulation
            media_dispatched = True
            media_status = "queued"
            steps.append("homenest_playback_simulated")
    except Exception as exc:
        media_error = f"HomeNest playback exception: {str(exc)}"

    if not media_dispatched:
        # Failure to dispatch media terminates the workflow
        steps.append("workflow_failed_at_media")
        return MovieNightResult(
            workflow_id=workflow_id,
            status="failed",
            media_dispatched=False,
            media_error=media_error,
            scene_activated=False,
            executed_steps=steps,
        )

    # Step 2: Call Home Assistant Scene with idempotency and partial-failure protection
    steps.append("trigger_ha_scene")
    scene_activated = False
    scene_error = None

    idempotency_id = f"{request.idempotency_key}:{request.scene_id}" if request.idempotency_key else None

    if idempotency_id and idempotency_id in scenes_store:
        steps.append("ha_scene_skipped_idempotent")
        scene_activated = True
    else:
        try:
            if ha_client is not None:
                # Can be HomeAssistantClient
                if hasattr(ha_client, "call_service"):
                    try:
                        from udos_home_assistant.models import ServiceCall as HAServiceCall
                        scall = HAServiceCall(
                            domain="scene",
                            service="turn_on",
                            target_entity_id=request.scene_id,
                        )
                    except ImportError:
                        class LocalServiceCall(BaseModel):
                            domain: str = "scene"
                            service: str = "turn_on"
                            target_entity_id: str | None = request.scene_id
                            service_data: dict[str, Any] = Field(default_factory=dict)
                        scall = LocalServiceCall()

                    res = await ha_client.call_service(scall)
                    if getattr(res, "status", "") == "confirmed":
                        scene_activated = True
                        steps.append("ha_scene_confirmed")
                        if idempotency_id:
                            scenes_store.add(idempotency_id)
                    else:
                        scene_error = f"HA service call returned {getattr(res, 'status', 'error')}: {getattr(res, 'error', '')}"
                else:
                    scene_activated = True
                    steps.append("ha_scene_mock_confirmed")
                    if idempotency_id:
                        scenes_store.add(idempotency_id)
            else:
                scene_activated = True
                steps.append("ha_scene_simulated")
                if idempotency_id:
                    scenes_store.add(idempotency_id)
        except Exception as exc:
            scene_error = f"HA connection exception: {str(exc)}"

    # Determine overall status: if media played but scene failed, it's a PARTIAL FAILURE, not total failure
    if not scene_activated:
        steps.append("ha_scene_failed_playback_uninterrupted")
        overall_status = "partial_failure"
    else:
        overall_status = "success"

    return MovieNightResult(
        workflow_id=workflow_id,
        status=overall_status,
        media_dispatched=True,
        media_status=media_status,
        scene_activated=scene_activated,
        scene_error=scene_error,
        executed_steps=steps,
    )
