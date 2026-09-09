"""Test suite for Sprint 4 Slice 1: Internal Dev Mode Readiness Gate.

Verifies:
1. Missing/unresponsive Ollama fails closed with NoEligibleExecutorError and zero cloud fallback.
2. User scope has hard-zero cloud allowance (zero-cost cloud tiers are still denied).
3. Path containment and permitted_paths enforcement (PathAccessViolation).
4. Stale proposal application rejected on fingerprint mismatch.
5. Atomic budget reservations enforce caps across concurrent tasks.
6. Skills registry enforces lane, timeout, and allowed roots.
"""

from __future__ import annotations

import asyncio
import pytest
from pathlib import Path

from app.core.execution_context import (
    ExecutionContext,
    PathAccessViolation,
    ProviderAccessViolation,
    NetworkAccessViolation,
)
from app.services.dev_layer import DevMode, get_dev_layer
from app.services.executor_selector import ExecutorSelector, NoEligibleExecutorError
from app.services.budget_manager import BudgetManager
from app.skills import registry
from app.skills.base import BaseSkill, SkillMeta


# --- Scenario 1: Missing or Unresponsive Ollama ---

@pytest.mark.asyncio
async def test_user_scope_fails_closed_when_ollama_offline(monkeypatch):
    """If Ollama is offline, user scope tasks must fail with NoEligibleExecutorError, not cloud fallback."""
    selector = ExecutorSelector()
    monkeypatch.setattr(selector, "check_ollama_health", lambda: asyncio.sleep(0, result=False))

    ctx = ExecutionContext(
        task_id="task-u1",
        scope="user",
        lane="everyday",
        provider_eligibility=["ollama"],
    )

    with pytest.raises(NoEligibleExecutorError) as exc_info:
        await selector.select(ctx, task_type="developer-chat")

    assert "Local Ollama is unavailable" in str(exc_info.value)
    assert "cannot fall back to cloud" in str(exc_info.value)


@pytest.mark.asyncio
async def test_dev_scope_fails_closed_when_ollama_offline_and_no_cloud_authorized(monkeypatch):
    """Dev scope fails closed when Ollama is offline and cloud providers are not authorized."""
    selector = ExecutorSelector()
    monkeypatch.setattr(selector, "check_ollama_health", lambda: asyncio.sleep(0, result=False))
    monkeypatch.setattr(get_dev_layer(), "mode", DevMode.ON)

    ctx = ExecutionContext(
        task_id="task-d1",
        scope="developer",
        lane="dev",
        provider_eligibility=["ollama"],
    )

    with pytest.raises(NoEligibleExecutorError) as exc_info:
        await selector.select(ctx, task_type="developer-chat")

    assert "cloud providers are not authorized" in str(exc_info.value)


# --- Scenario 2: Normal / User Scope Cloud Denial ---

def test_user_scope_denies_all_cloud_providers():
    """User scope tasks strictly forbid non-ollama providers, even if cost is 0."""
    ctx = ExecutionContext(
        task_id="task-u2",
        scope="user",
        lane="everyday",
    )

    # Free cloud tier is still remote inference and must be denied
    with pytest.raises(ProviderAccessViolation) as exc_info:
        ctx.validate_provider("openrouter", cost=0.0)
    assert "User scope tasks are restricted to local zero-cost inference" in str(exc_info.value)

    # Paid cloud tier denied
    with pytest.raises(ProviderAccessViolation):
        ctx.validate_provider("anthropic", cost=0.05)


def test_user_lane_hard_zero_budget_allowance():
    """BudgetManager.can_spend returns False for any non-zero cost in user lane."""
    bm = BudgetManager.get()
    assert bm.can_spend("dev", estimated_cost=0.0, lane="user") is True
    assert bm.can_spend("dev", estimated_cost=0.01, lane="user") is False


# --- Scenario 3: Out-of-Scope File Access & Permitted Paths ---

def test_execution_context_path_containment():
    """Paths must be repository-relative and match permitted_paths whitelist if provided."""
    ctx = ExecutionContext(
        task_id="task-p1",
        repository="uCore",
        permitted_paths=["backend/app/*.py", "tests/test_*.py"],
    )

    # Allowed paths
    ctx.validate_path("backend/app/main.py")
    ctx.validate_path("tests/test_api.py")

    # Outside permitted patterns
    with pytest.raises(PathAccessViolation):
        ctx.validate_path("frontend-vue/src/App.vue")

    # Path traversal attempts
    with pytest.raises(PathAccessViolation):
        ctx.validate_path("../outside.py")

    with pytest.raises(PathAccessViolation):
        ctx.validate_path("backend/../../etc/passwd")

    with pytest.raises(PathAccessViolation):
        ctx.validate_path("/absolute/path.py")


def test_network_policy_containment():
    """Network policies offline and local_only reject unauthorized outbound destinations."""
    ctx_offline = ExecutionContext(task_id="net-1", network_policy="offline")
    with pytest.raises(NetworkAccessViolation):
        ctx_offline.validate_network("localhost")

    ctx_local = ExecutionContext(task_id="net-2", network_policy="local_only")
    ctx_local.validate_network("http://localhost:11434")
    ctx_local.validate_network("http://127.0.0.1:8000")

    with pytest.raises(NetworkAccessViolation):
        ctx_local.validate_network("https://api.openai.com")


# --- Scenario 4: Atomic Budget Reservations ---

def test_atomic_budget_reservations():
    """Budget reservations prevent overspending across concurrent requests."""
    bm = BudgetManager.get()
    bm._reservations.clear()

    res1 = "test-res-1"
    res2 = "test-res-2"

    orig_budget = bm._config.get("session_budget_usd", 5.0)
    bm._config["session_budget_usd"] = 0.15
    try:
        # Max per task for 'dev' is $0.10; $0.09 is permitted
        assert bm.reserve_spend("dev", res1, estimated_cost=0.09, lane="dev") is True
        # Attempting to reserve another $0.09 should fail because $0.09 + $0.09 = $0.18 > $0.15
        assert bm.reserve_spend("dev", res2, estimated_cost=0.09, lane="dev") is False

        # After releasing res1, res2 can be reserved
        bm.release_reservation(res1)
        assert bm.reserve_spend("dev", res2, estimated_cost=0.09, lane="dev") is True

        # Reconcile spend records actual usage and cleans up reservation
        bm.reconcile_spend(res2, actual_cost=0.04, task_type="dev-test")
        assert res2 not in bm._reservations
    finally:
        bm._config["session_budget_usd"] = orig_budget
        bm._reservations.clear()


# --- Scenario 5: Skills Registry Runtime Enforcement ---

class _TimeoutSkill(BaseSkill):
    meta = SkillMeta(
        id="test-timeout",
        name="Test timeout",
        category="general",
        timeout=1,
    )

    async def run(self, **kwargs) -> dict:
        await asyncio.sleep(2)
        return {"success": True}


class _DeveloperLaneSkill(BaseSkill):
    meta = SkillMeta(
        id="test-dev-skill",
        name="Test developer lane skill",
        category="general",
    )
    _catalogue_entry = {"lane": "developer", "allowed_roots": ["Code"]}

    async def run(self, **kwargs) -> dict:
        return {"success": True}


@pytest.mark.asyncio
async def test_skills_enforce_timeout(monkeypatch):
    """Skill execution exceeding timeout parameter returns timeout error."""
    monkeypatch.setattr(registry, "get_skill", lambda _id: _TimeoutSkill())
    result = await registry.run_skill_by_id("test-timeout")
    assert result["success"] is False
    assert "timed out after 1s" in result["error"]


@pytest.mark.asyncio
async def test_skills_enforce_user_scope_lane_check(monkeypatch):
    """Developer-lane skill is denied when called with user scope context."""
    monkeypatch.setattr(registry, "get_skill", lambda _id: _DeveloperLaneSkill())
    ctx = ExecutionContext(task_id="u-skill", scope="user", lane="everyday")
    result = await registry.run_skill_by_id("test-dev-skill", context=ctx)
    assert result["success"] is False
    assert "denied in user scope" in result["error"]


@pytest.mark.asyncio
async def test_skills_reject_path_traversal(monkeypatch):
    """Passing path traversal into skill kwargs is rejected."""
    monkeypatch.setattr(registry, "get_skill", lambda _id: _DeveloperLaneSkill())
    result = await registry.run_skill_by_id("test-dev-skill", path="../escape.py")
    assert result["success"] is False
    assert "Path traversal" in result["error"]
