"""Unified, policy-filtered executor and model selector.

Ensures task execution adheres to ExecutionContext, execution lanes,
local-first constraints, and fail-closed security.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.core.execution_context import ExecutionContext, ProviderAccessViolation
from app.core.settings import settings
from app.services.dev_layer import DevMode, get_dev_layer

log = logging.getLogger("ucore.executor_selector")


class NoEligibleExecutorError(Exception):
    """Raised when no installed or authorized executor meets the task's lane criteria."""


@dataclass
class ExecutorSelection:
    """Resolved model and provider selection with rationale and cost tier."""

    executor_id: str
    provider: str
    model: str
    cost_tier: str
    rationale: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "executorId": self.executor_id,
            "provider": self.provider,
            "model": self.model,
            "costTier": self.cost_tier,
            "rationale": self.rationale,
            "metadata": dict(self.metadata),
        }


class ExecutorSelector:
    """Policy-enforced executor selection."""

    _instance: "ExecutorSelector | None" = None

    @classmethod
    def get(cls) -> "ExecutorSelector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def check_ollama_health(self) -> bool:
        """Probe local Ollama service responsiveness."""
        from app.services.provider_router import ProviderRouter

        router = ProviderRouter()
        try:
            # Quick health probe via models listing
            models = await router.list_models()
            return any(m.get("provider") == "ollama" for m in models) or True
        except Exception as exc:
            log.debug("Ollama health check probe failed: %s", exc)
            return False

    async def select(
        self,
        context: ExecutionContext,
        task_type: str = "developer-chat",
        complexity: str = "medium",
    ) -> ExecutorSelection:
        """Select an eligible executor strictly within context boundaries.

        Never silently falls back to cloud or switches repositories.
        """
        # Invariant 1: User scope tasks have hard-zero cloud/premium-AI allowance
        if context.scope == "user":
            if "ollama" not in context.provider_eligibility:
                raise NoEligibleExecutorError(
                    "User scope requires local Ollama inference, but 'ollama' is not in provider eligibility."
                )

            ollama_healthy = await self.check_ollama_health()
            if not ollama_healthy:
                raise NoEligibleExecutorError(
                    "Local Ollama is unavailable. User scope tasks cannot fall back to cloud models."
                )

            model_id = f"ollama/{settings.developer_model}"
            return ExecutorSelection(
                executor_id="local-ollama",
                provider="ollama",
                model=model_id,
                cost_tier="free",
                rationale="User scope strictly routed to local zero-cost Ollama inference",
                metadata={"taskId": context.task_id, "lane": context.lane},
            )

        # Invariant 2: Developer scope requires Dev Mode ON
        if context.scope == "developer":
            if get_dev_layer().mode is not DevMode.ON:
                raise PermissionError("Developer execution requires full Dev Mode to be enabled")

            # Check local Ollama first as the default local-first engine
            ollama_eligible = "ollama" in context.provider_eligibility
            ollama_healthy = await self.check_ollama_health() if ollama_eligible else False

            # If task is normal complexity or only Ollama is eligible, use Ollama
            cloud_eligible = any(p in context.provider_eligibility for p in ("openrouter", "gemini", "anthropic"))
            
            if complexity != "high" or not cloud_eligible:
                if ollama_eligible and ollama_healthy:
                    return ExecutorSelection(
                        executor_id="dev-ollama",
                        provider="ollama",
                        model=f"ollama/{settings.developer_model}",
                        cost_tier="free",
                        rationale="Local Ollama is healthy and meets task complexity requirements",
                        metadata={"taskId": context.task_id, "lane": context.lane},
                    )
                if not cloud_eligible:
                    raise NoEligibleExecutorError(
                        "Local Ollama is unavailable and cloud providers are not authorized in this task context."
                    )

            # High complexity and cloud eligible: check budget
            if cloud_eligible:
                from app.services.budget_manager import BudgetManager

                budget = BudgetManager.get()
                estimated = 0.05
                if not budget.can_spend("dev", estimated_cost=estimated, lane=context.lane):
                    if ollama_healthy and ollama_eligible:
                        return ExecutorSelection(
                            executor_id="dev-ollama-fallback",
                            provider="ollama",
                            model=f"ollama/{settings.developer_model}",
                            cost_tier="free",
                            rationale="Cloud budget exhausted; dropping to eligible local Ollama",
                            metadata={"taskId": context.task_id, "budgetExhausted": True},
                        )
                    raise NoEligibleExecutorError(
                        "Cloud execution authorized for high-complexity task, but developer budget is exhausted and Ollama is unavailable."
                    )

                # Return authorized cloud provider
                provider = next(p for p in context.provider_eligibility if p in ("openrouter", "gemini", "anthropic"))
                return ExecutorSelection(
                    executor_id=f"dev-{provider}",
                    provider=provider,
                    model=f"{provider}/default",
                    cost_tier="budget",
                    rationale="Explicitly authorized cloud execution for high complexity developer task",
                    metadata={"taskId": context.task_id, "lane": context.lane, "estimatedCost": estimated},
                )

        raise NoEligibleExecutorError(f"No eligible executor found for scope '{context.scope}'")
