"""Tests for uFlow cross-product Movie Night workflow."""
import pytest

from app.flow.workflows.movie_night import (
    MovieNightRequest,
    MovieNightResult,
    execute_movie_night,
)


class MockHomeNestService:
    def __init__(self, succeed: bool = True):
        self.succeed = succeed

    def handoff(self, item_id: str, target_client: str):
        if self.succeed:
            return {"success": True, "status": "queued", "item_id": item_id}
        return {"success": False, "error": "Item not found in catalog"}


class MockHAClient:
    def __init__(self, succeed: bool = True):
        self.succeed = succeed
        self.calls: list[str] = []

    async def call_service(self, service_call):
        self.calls.append(f"{service_call.domain}.{service_call.service}")
        if self.succeed:
            class MockConfirmed:
                status = "confirmed"
                error = None
            return MockConfirmed()
        class MockRejected:
            status = "failed"
            error = "HA host unreachable"
        return MockRejected()


@pytest.mark.asyncio
async def test_movie_night_full_success():
    hn = MockHomeNestService(succeed=True)
    ha = MockHAClient(succeed=True)
    store = set()

    req = MovieNightRequest(
        media_item_id="film-interstellar-4k",
        target_client="living-room-tv",
        scene_id="scene.cinema_dim",
        idempotency_key="key-001",
    )

    result = await execute_movie_night(req, homenest_client=hn, ha_client=ha, executed_scenes_store=store)
    assert result.status == "success"
    assert result.media_dispatched is True
    assert result.media_status == "queued"
    assert result.scene_activated is True
    assert result.scene_error is None
    assert len(ha.calls) == 1
    assert "ha_scene_confirmed" in result.executed_steps


@pytest.mark.asyncio
async def test_movie_night_partial_failure_ha_offline():
    # Crucial acceptance criteria: Home Assistant failure must NOT break media playback!
    hn = MockHomeNestService(succeed=True)
    ha = MockHAClient(succeed=False)
    store = set()

    req = MovieNightRequest(
        media_item_id="film-dune-part-2",
        target_client="living-room-tv",
        scene_id="scene.cinema_dim",
        idempotency_key="key-002",
    )

    result = await execute_movie_night(req, homenest_client=hn, ha_client=ha, executed_scenes_store=store)
    assert result.status == "partial_failure"
    # Media dispatched despite HA failure
    assert result.media_dispatched is True
    assert result.scene_activated is False
    assert "HA host unreachable" in result.scene_error
    assert "ha_scene_failed_playback_uninterrupted" in result.executed_steps


@pytest.mark.asyncio
async def test_movie_night_failure_at_media():
    hn = MockHomeNestService(succeed=False)
    ha = MockHAClient(succeed=True)
    store = set()

    req = MovieNightRequest(
        media_item_id="nonexistent-id",
        target_client="living-room-tv",
    )

    result = await execute_movie_night(req, homenest_client=hn, ha_client=ha, executed_scenes_store=store)
    assert result.status == "failed"
    assert result.media_dispatched is False
    assert result.scene_activated is False
    assert len(ha.calls) == 0


@pytest.mark.asyncio
async def test_movie_night_idempotency_skip():
    hn = MockHomeNestService(succeed=True)
    ha = MockHAClient(succeed=True)
    store = set()

    req = MovieNightRequest(
        media_item_id="film-blade-runner",
        target_client="living-room-tv",
        scene_id="scene.cinema_dim",
        idempotency_key="unique-booking-123",
    )

    # First run
    res1 = await execute_movie_night(req, homenest_client=hn, ha_client=ha, executed_scenes_store=store)
    assert res1.status == "success"
    assert len(ha.calls) == 1

    # Retry with same idempotency key
    res2 = await execute_movie_night(req, homenest_client=hn, ha_client=ha, executed_scenes_store=store)
    assert res2.status == "success"
    # Scene was not called twice!
    assert len(ha.calls) == 1
    assert "ha_scene_skipped_idempotent" in res2.executed_steps
