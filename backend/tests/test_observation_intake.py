"""Gate B step 1: fixture-driven observation intake and change detection."""
from __future__ import annotations

import json

import pytest

from app.services.observation_intake import (
    ObservationError,
    ObservationStore,
    parse_observation,
)


def _observation(**overrides):
    payload = {
        "observation_id": "obs-1",
        "source_id": "feed.example",
        "subject_id": "notice",
        "observed_at": "2026-11-26T10:00:00+00:00",
        "values": {"status": "open", "count": 2},
        "source_url": "https://feed.example/notice",
    }
    payload.update(overrides)
    return parse_observation(payload)


def _store(tmp_path) -> ObservationStore:
    return ObservationStore(tmp_path / "observations.db")


def test_first_observation_establishes_a_baseline(tmp_path):
    result = _store(tmp_path).ingest(_observation())

    assert result == {"accepted": True, "outcome": "baseline"}


def test_equivalent_observation_is_suppressed(tmp_path):
    store = _store(tmp_path)
    store.ingest(_observation())
    result = store.ingest(
        _observation(observation_id="obs-2", observed_at="2026-11-26T11:00:00+00:00")
    )

    assert result == {"accepted": True, "outcome": "suppressed"}
    assert store.pending_transitions() == []


def test_one_field_change_becomes_one_pending_transition(tmp_path):
    store = _store(tmp_path)
    store.ingest(_observation())
    result = store.ingest(
        _observation(
            observation_id="obs-2",
            observed_at="2026-11-26T11:00:00+00:00",
            values={"status": "closed", "count": 2},
        )
    )

    assert result["outcome"] == "transition"
    assert result["changed"] == {"status": "closed"}
    assert result["removed"] == []
    pending = store.pending_transitions()
    assert [row["transition_id"] for row in pending] == [result["transition_id"]]


def test_removed_field_is_reported(tmp_path):
    store = _store(tmp_path)
    store.ingest(_observation())
    result = store.ingest(
        _observation(
            observation_id="obs-2",
            observed_at="2026-11-26T11:00:00+00:00",
            values={"status": "open"},
        )
    )

    assert result["removed"] == ["count"]
    assert result["changed"] == {}


def test_duplicate_observation_is_not_reprocessed(tmp_path):
    store = _store(tmp_path)
    store.ingest(_observation())
    store.ingest(_observation())

    assert store.pending_transitions() == []


def test_older_observation_is_quarantined_as_stale(tmp_path):
    store = _store(tmp_path)
    store.ingest(_observation())
    result = store.ingest(
        _observation(
            observation_id="obs-0",
            observed_at="2026-11-26T09:00:00+00:00",
            values={"status": "closed"},
        )
    )

    assert result == {"accepted": False, "outcome": "stale"}
    assert store.pending_transitions() == []


def test_reordered_retry_keeps_one_transition(tmp_path):
    store = _store(tmp_path)
    store.ingest(_observation())
    first = store.ingest(
        _observation(
            observation_id="obs-2",
            observed_at="2026-11-26T11:00:00+00:00",
            values={"status": "closed", "count": 2},
        )
    )
    replay = store.ingest(
        _observation(
            observation_id="obs-3",
            observed_at="2026-11-26T11:00:00+00:00",
            values={"status": "closed", "count": 2},
        )
    )

    # The second observation is stale relative to the stored baseline.
    assert replay["outcome"] == "stale"
    assert len(store.pending_transitions()) == 1
    assert store.pending_transitions()[0]["transition_id"] == first["transition_id"]


def test_delivery_is_recorded_once(tmp_path):
    store = _store(tmp_path)
    store.ingest(_observation())
    transition = store.ingest(
        _observation(
            observation_id="obs-2",
            observed_at="2026-11-26T11:00:00+00:00",
            values={"status": "closed", "count": 2},
        )
    )

    store.mark_delivered(transition["transition_id"], "run-1")

    assert store.pending_transitions() == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"values": {}},
        {"observed_at": "2026-11-26T10:00:00"},
        {"observed_at": "not-a-date"},
        {"values": {"bad field": "x"}},
        {"values": {"status": "x" * 2001}},
        {"schema_version": 2},
        {"observation_id": "../escape"},
        {"source_url": "file:///etc/passwd"},
    ],
)
def test_malformed_observations_are_rejected(overrides):
    with pytest.raises(ObservationError):
        _observation(**overrides)


@pytest.mark.asyncio
async def test_endpoint_admits_data_and_reports_the_outcome(tmp_path, monkeypatch):
    from unittest.mock import AsyncMock

    from aiohttp.test_utils import make_mocked_request

    from app.api import observation_api
    from app.core.settings import settings
    from app.services import identity, observation_intake

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(observation_intake.settings, "data_dir", tmp_path)
    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: {
            "authenticated": True,
            "active_profile_id": "alice",
            "active_profile": {"id": "alice", "role": "developer"},
        },
    )
    request = make_mocked_request("POST", "/api/host/observations")
    request.json = AsyncMock(
        return_value={
            "observation_id": "obs-endpoint-1",
            "source_id": "feed.endpoint",
            "subject_id": "endpoint-subject",
            "observed_at": "2026-11-26T10:00:00Z",
            "values": {"status": "open"},
        }
    )

    response = await observation_api.handle_observation(request)

    assert (tmp_path / "observations.db").is_file()
    assert response.status == 200
    assert json.loads(response.text)["outcome"] == "baseline"


@pytest.mark.asyncio
async def test_endpoint_rejects_malformed_and_anonymous(tmp_path, monkeypatch):
    from unittest.mock import AsyncMock

    from aiohttp.test_utils import make_mocked_request

    from app.api import observation_api
    from app.core.settings import settings
    from app.services import identity, observation_intake

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(observation_intake.settings, "data_dir", tmp_path)
    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: {
            "authenticated": True,
            "active_profile_id": "alice",
            "active_profile": {"id": "alice", "role": "developer"},
        },
    )
    bad = make_mocked_request("POST", "/api/host/observations")
    bad.json = AsyncMock(return_value={"values": {}})

    malformed = await observation_api.handle_observation(bad)

    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: {"authenticated": False, "active_profile_id": ""},
    )
    anonymous = await observation_api.handle_observation(bad)

    assert malformed.status == 400
    assert anonymous.status == 403


def test_prune_removes_settled_records_and_keeps_pending(tmp_path):
    from datetime import UTC, datetime

    store = ObservationStore(tmp_path / "observations.db")
    baseline = {
        "source_id": "feed.p",
        "subject_id": "notice",
        "values": {"status": "open"},
    }
    store.ingest(
        parse_observation(
            {**baseline, "observation_id": "p-1", "observed_at": "2026-11-26T10:00:00Z"}
        )
    )
    delivered = store.ingest(
        parse_observation(
            {
                **baseline,
                "observation_id": "p-2",
                "observed_at": "2026-11-26T11:00:00Z",
                "values": {"status": "closed"},
            }
        )
    )
    receipt, _ = store.record_receipt(
        transition_id=delivered["transition_id"],
        binding_id="b-1",
        workflow_id="wf-1",
        status="admitting",
    )
    store.complete_receipt(receipt["receipt_id"], "run-1")
    store.mark_delivered(delivered["transition_id"], "run-1")
    pending = store.ingest(
        parse_observation(
            {
                **baseline,
                "observation_id": "p-3",
                "observed_at": "2026-11-26T12:00:00Z",
            }
        )
    )

    removed = store.prune(days=30, now=datetime(2027, 1, 31, tzinfo=UTC))

    assert removed >= 2
    assert store.get_receipt(delivered["transition_id"]) is None
    assert [row["transition_id"] for row in store.pending_transitions()] == [
        pending["transition_id"]
    ]

