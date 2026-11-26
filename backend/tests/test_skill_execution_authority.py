"""Authority checks at the skill execution entry points (Gate A step 2)."""
from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest
from aiohttp.test_utils import make_mocked_request

from app.api import skills as skills_api
from app.services import identity
from app.skills import registry


class _LaneSkill:
    def __init__(self, lane: str, category: str = "general", confirm: bool = False) -> None:
        self.meta = SimpleNamespace(
            id="demo",
            requires_confirmation=confirm,
            category=category,
            timeout=5,
        )
        self._catalogue_entry = {"lane": lane, "allowed_roots": []}

    def validate(self, **_kwargs) -> list[str]:
        return []

    async def run(self, **_kwargs) -> dict:
        return {"success": True}


def _request(body: dict | None = None):
    payload = io.BytesIO(json.dumps(body or {}).encode("utf-8"))
    return make_mocked_request("POST", "/api/skills/demo/run", payload=payload)


def _identity(role: str, authenticated: bool = True) -> dict:
    return {
        "authenticated": authenticated,
        "active_profile_id": role or "default",
        "active_profile": {"id": role, "role": role},
    }


def _patch_skill(monkeypatch, skill: _LaneSkill) -> None:
    monkeypatch.setattr(skills_api, "get_skill", lambda _skill_id: skill)
    monkeypatch.setattr(registry, "get_skill", lambda _skill_id: skill)


@pytest.mark.asyncio
async def test_developer_lane_skill_denied_for_user_scope(monkeypatch):
    """A guest profile cannot reach a developer-lane skill through the API."""
    _patch_skill(monkeypatch, _LaneSkill("developer"))
    monkeypatch.setattr(identity, "get_full_identity", lambda: _identity("guest"))

    response = await skills_api.handle_run_skill(_request())

    payload = json.loads(response.text)
    assert payload["success"] is False
    assert "developer lane" in payload["error"]


@pytest.mark.asyncio
async def test_guest_cannot_authorise_mutating_skill(monkeypatch):
    """Confirmation is not authority: a guest profile may not mutate."""
    _patch_skill(monkeypatch, _LaneSkill("everyday", category="mutating", confirm=True))
    monkeypatch.setattr(identity, "get_full_identity", lambda: _identity("guest"))

    response = await skills_api._run_skill_by_id("demo", _request(), {"confirm": True})

    assert response.status == 403
    assert "Guest profiles" in json.loads(response.text)["error"]


@pytest.mark.asyncio
async def test_developer_runs_mutating_skill_with_server_context(monkeypatch):
    """An authorised profile runs with developer scope derived by the server."""
    _patch_skill(monkeypatch, _LaneSkill("everyday", category="mutating", confirm=True))
    monkeypatch.setattr(identity, "get_full_identity", lambda: _identity("developer"))

    seen = {}

    async def fake_run(skill_id, **kwargs):
        seen["skill_id"] = skill_id
        seen["context"] = kwargs.get("context")
        seen["authorized"] = kwargs.get("execution_authorized")
        return {"success": True}

    monkeypatch.setattr(skills_api, "run_skill_by_id", fake_run)

    response = await skills_api._run_skill_by_id("demo", _request(), {"confirm": True})

    assert response.status == 200
    assert seen["skill_id"] == "demo"
    assert seen["context"].scope == "developer"
    assert seen["context"].metadata == {
        "profile": "developer",
        "role": "developer",
        "surface": "skill-run",
    }
    assert seen["authorized"] is True


@pytest.mark.asyncio
async def test_unauthenticated_caller_is_rejected(monkeypatch):
    _patch_skill(monkeypatch, _LaneSkill("everyday"))
    monkeypatch.setattr(
        identity,
        "get_full_identity",
        lambda: _identity("guest", authenticated=False),
    )

    response = await skills_api.handle_run_skill(_request())

    assert response.status == 403
    assert "Authenticate" in json.loads(response.text)["error"]


def test_caller_supplied_server_fields_are_rejected(monkeypatch):
    """A body cannot set execution_authorized or context directly."""
    assert registry.SERVER_RUN_FIELDS == {"execution_authorized", "context"}
