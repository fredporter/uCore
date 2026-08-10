from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.services.provider_router import ProviderRouter

log = logging.getLogger("ucore.services.flow_router")


def default_flow_router_db_path() -> str:
    from app.core.settings import settings
    return str(settings.data_dir / "flow_router.db")


@dataclass
class FlowRoutingDecision:
    """Represents a routing decision with cost analytics."""
    task_id: str
    task_description: str
    complexity: str
    context_size: str
    risk_level: str
    selected_provider: str
    selected_model: str
    estimated_cost: float
    estimated_tokens: int
    estimated_latency_ms: float
    routing_reason: str
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_description": self.task_description[:100] + ("..." if len(self.task_description) > 100 else ""),
            "complexity": self.complexity,
            "context_size": self.context_size,
            "risk_level": self.risk_level,
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "estimated_cost": self.estimated_cost,
            "estimated_tokens": self.estimated_tokens,
            "estimated_latency_ms": self.estimated_latency_ms,
            "routing_reason": self.routing_reason,
            "timestamp": self.timestamp,
        }


class FlowLLMRouter:
    """Enhanced Flow-LLM Router with cost analytics and visualization.
    
    Provides smart, cost-optimized routing to the best model for the task
    with detailed analytics and visualization capabilities.
    """

    def __init__(self, provider_router: Optional[ProviderRouter] = None):
        self.provider_router = provider_router or ProviderRouter()
        self._routing_history: List[FlowRoutingDecision] = []
        self._analytics = {
            "total_requests": 0,
            "cost_savings": 0.0,
            "token_savings": 0,
            "latency_improvement": 0.0,
            "provider_distribution": {},
            "complexity_distribution": {},
        }

    def _estimate_cost(self, provider: str, model: str, complexity: str, context_size: str) -> Tuple[float, int]:
        """Estimate cost and tokens for a provider/model combination."""
        # Cost estimates based on provider and model
        cost_table = {
            "ollama": {
                "qwen2.5-coder:3b": (0.0, 1000),
                "qwen2.5-coder:7b": (0.0, 2000),
                "llama3.2:3b": (0.0, 1500),
                "codellama:7b-code": (0.0, 2500),
            },
            "openrouter": {
                "deepseek/deepseek-chat": (0.01, 3000),
                "openai/o3-mini": (0.005, 2000),
                "anthropic/claude-sonnet-4-20250514": (0.05, 5000),
                "google/gemini-2.5-flash-001": (0.003, 4000),
                "anthropic/claude-opus": (0.15, 8000),
            },
        }

        # Base cost and tokens
        base_cost, base_tokens = cost_table.get(provider, {}).get(model, (0.01, 2000))

        # Adjust based on complexity
        if complexity == "simple":
            multiplier = 0.5
        elif complexity == "medium":
            multiplier = 1.0
        else:  # complex
            multiplier = 2.0

        # Adjust based on context size
        if context_size == "large":
            multiplier *= 1.5
        elif context_size == "medium":
            multiplier *= 1.2

        return round(base_cost * multiplier, 4), int(base_tokens * multiplier)

    def _get_routing_reason(self, complexity: str, context_size: str, risk_level: str, provider: str, model: str) -> str:
        """Generate a human-readable routing reason."""
        reasons = []

        if complexity == "simple":
            reasons.append("Simple task")
        elif complexity == "medium":
            reasons.append("Medium complexity task")
        else:
            reasons.append("Complex reasoning task")

        if context_size == "large":
            reasons.append("Large context requirement")
        elif context_size == "medium":
            reasons.append("Medium context requirement")

        if risk_level == "high":
            reasons.append("High security risk")
        elif risk_level == "medium":
            reasons.append("Medium security risk")

        if provider == "ollama":
            reasons.append("Local model for privacy")
        elif provider == "openrouter":
            reasons.append("Cloud model for best performance")

        return ", ".join(reasons)

    def _estimate_complexity(self, task: str) -> str:
        """Auto-detect complexity from task description."""
        task_lower = task.lower()

        complex_signals = [
            "security", "vulnerability", "exploit", "race condition",
            "deadlock", "concurrency", "encryption", "cryptography",
            "refactor", "architecture", "design pattern", "distributed",
            "performance optimization", "memory leak", "thread safety",
            "authentication", "authorization", "zero-day",
            "complicated", "intricate", "nuanced", "subtle bug",
        ]
        medium_signals = [
            "implement", "feature", "endpoint", "api", "route",
            "component", "module", "integration", "database",
            "migration", "schema", "query", "test", "coverage",
            "debug", "fix bug", "error handling", "validation",
        ]

        for signal in complex_signals:
            if signal in task_lower:
                return "complex"
        for signal in medium_signals:
            if signal in task_lower:
                return "medium"

        if len(task) > 200:
            return "medium"

        return "simple"

    def _estimate_risk(self, task: str, complexity: str) -> str:
        """Estimate risk level from task description."""
        task_lower = task.lower()

        high_risk_signals = [
            "security", "vulnerability", "exploit", "private key",
            "password", "token", "credential", "hack", "breach",
            "delete", "drop database", "truncate", "production",
            "critical infrastructure", "zero-day", "malware",
        ]
        for signal in high_risk_signals:
            if signal in task_lower:
                return "high"

        if complexity == "complex":
            return "medium"

        return "low"

    def _estimate_context_size(self, task: str) -> str:
        """Estimate required context size from task."""
        if len(task) > 10000:
            return "large"
        if len(task) > 2000:
            return "medium"
        return "small"

    def _build_routing(
        self,
        complexity: str,
        context_size: str,
        risk_level: str,
        budget_remaining: float = 100.0,
    ) -> dict:
        """Build routing decision considering cost, context, risk, budget."""
        cost_table = {
            "simple": {
                "provider": "ollama",
                "model": "qwen2.5-coder:3b",
                "cost": "$0 (local)",
                "reason": "Simple task — use local free model",
                "tokens_per_second": "~40",
            },
            "medium": {
                "provider": "openrouter",
                "model": "deepseek/deepseek-chat",
                "cost": "~$0.01/task (low)",
                "reason": "Medium task — cost-effective cloud model",
                "tokens_per_second": "~60",
            },
            "complex": {
                "provider": "openrouter",
                "model": "anthropic/claude-opus",
                "cost": "~$0.15/task (high)",
                "reason": "Complex task — best reasoning available",
                "tokens_per_second": "~30",
            },
        }

        routing = cost_table.get(complexity, cost_table["simple"])

        if context_size == "large":
            routing = {
                "provider": "openrouter",
                "model": "google/gemini-2.5-flash-001",
                "cost": "~$0.005/100K tokens (cheap for large context)",
                "reason": "Large context — use Gemini for 1M token window",
                "tokens_per_second": "~50",
            }

        if risk_level == "high":
            routing = {
                "provider": "ollama",
                "model": "qwen2.5-coder:7b",
                "cost": "$0 (local, no data leakage)",
                "reason": "High-risk task — keep local to prevent exposure",
                "tokens_per_second": "~20",
            }

        if budget_remaining < 1.0:
            routing = {
                "provider": "ollama",
                "model": "qwen2.5-coder:3b",
                "cost": "$0 (local, budget constrained)",
                "reason": "Budget exhausted — fall back to local model",
                "tokens_per_second": "~40",
            }

        return routing

    async def route_task(
        self,
        task_description: str,
        complexity: str = "auto",
        context_size: str = "small",
        risk_level: str = "low",
        task_id: Optional[str] = None,
        budget_remaining: float = 100.0,
        max_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Route a task to the optimal provider/model with cost analytics."""
        start_time = time.time()

        if complexity == "auto":
            complexity = self._estimate_complexity(task_description)

        if risk_level == "auto":
            risk_level = self._estimate_risk(task_description, complexity)

        if context_size == "auto":
            context_size = self._estimate_context_size(task_description)

        # Get provider configuration
        self.provider_router.get_provider()

        # Build routing decision
        routing = self._build_routing(
            complexity,
            context_size,
            risk_level,
            budget_remaining=budget_remaining,
        )

        # Estimate cost and tokens
        estimated_cost, estimated_tokens = self._estimate_cost(
            routing.get("provider", "ollama"),
            routing.get("model", "qwen2.5-coder:3b"),
            complexity,
            context_size,
        )

        # Calculate latency estimate
        estimated_latency_ms = 100.0
        if routing.get("provider") == "ollama":
            estimated_latency_ms = 50.0
        elif routing.get("provider") == "openrouter":
            estimated_latency_ms = 200.0

        # Create routing decision
        decision = FlowRoutingDecision(
            task_id=task_id or f"task_{int(time.time())}",
            task_description=task_description,
            complexity=complexity,
            context_size=context_size,
            risk_level=risk_level,
            selected_provider=routing.get("provider", "ollama"),
            selected_model=routing.get("model", "qwen2.5-coder:3b"),
            estimated_cost=estimated_cost,
            estimated_tokens=estimated_tokens,
            estimated_latency_ms=estimated_latency_ms,
            routing_reason=self._get_routing_reason(
                complexity, context_size, risk_level,
                routing.get("provider", "ollama"),
                routing.get("model", "qwen2.5-coder:3b"),
            ),
            timestamp=time.time(),
        )

        # Store in history
        self._routing_history.append(decision)

        # Update analytics
        self._update_analytics(decision)

        # Return routing decision
        result = {
            "success": True,
            "task_id": decision.task_id,
            "task_description": decision.task_description,
            "analysis": {
                "complexity": decision.complexity,
                "context_size": decision.context_size,
                "risk_level": decision.risk_level,
            },
            "routing": {
                "provider": decision.selected_provider,
                "model": decision.selected_model,
                "estimated_cost": decision.estimated_cost,
                "estimated_tokens": decision.estimated_tokens,
                "estimated_latency_ms": decision.estimated_latency_ms,
                "reason": decision.routing_reason,
            },
            "analytics": {
                "total_requests": self._analytics["total_requests"],
                "cost_savings": self._analytics["cost_savings"],
                "token_savings": self._analytics["token_savings"],
                "latency_improvement": self._analytics["latency_improvement"],
                "provider_distribution": self._analytics["provider_distribution"],
                "complexity_distribution": self._analytics["complexity_distribution"],
            },
        }

        return result

    def _update_analytics(self, decision: FlowRoutingDecision) -> None:
        """Update analytics based on routing decision."""
        self._analytics["total_requests"] += 1

        # Update provider distribution
        provider = decision.selected_provider
        self._analytics["provider_distribution"][provider] = \
            self._analytics["provider_distribution"].get(provider, 0) + 1

        # Update complexity distribution
        complexity = decision.complexity
        self._analytics["complexity_distribution"][complexity] = \
            self._analytics["complexity_distribution"].get(complexity, 0) + 1

        # Calculate cost savings (compared to using most expensive option)
        # For simplicity, assume baseline is Claude Opus
        baseline_cost = 0.15
        savings = max(0, baseline_cost - decision.estimated_cost)
        self._analytics["cost_savings"] += savings

        # Token savings (compared to baseline)
        baseline_tokens = 8000
        token_savings = max(0, baseline_tokens - decision.estimated_tokens)
        self._analytics["token_savings"] += token_savings

        # Latency improvement (compared to baseline)
        baseline_latency = 200.0
        latency_improvement = max(0, baseline_latency - decision.estimated_latency_ms)
        self._analytics["latency_improvement"] += latency_improvement

    def get_routing_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent routing decisions."""
        return [
            decision.to_dict()
            for decision in self._routing_history[-limit:]
        ]

    def get_analytics(self) -> Dict[str, Any]:
        """Get current analytics."""
        return {
            "total_requests": self._analytics["total_requests"],
            "cost_savings": round(self._analytics["cost_savings"], 4),
            "token_savings": self._analytics["token_savings"],
            "latency_improvement": round(self._analytics["latency_improvement"], 2),
            "provider_distribution": self._analytics["provider_distribution"],
            "complexity_distribution": self._analytics["complexity_distribution"],
            "average_cost_per_request": round(
                self._analytics["cost_savings"] / self._analytics["total_requests"]
                if self._analytics["total_requests"] > 0 else 0, 4
            ),
            "average_latency_ms": round(
                self._analytics["latency_improvement"] / self._analytics["total_requests"]
                if self._analytics["total_requests"] > 0 else 0, 2
            ),
        }

    def clear_history(self) -> None:
        """Clear routing history."""
        self._routing_history.clear()

    def reset_analytics(self) -> None:
        """Reset analytics."""
        self._analytics = {
            "total_requests": 0,
            "cost_savings": 0.0,
            "token_savings": 0,
            "latency_improvement": 0.0,
            "provider_distribution": {},
            "complexity_distribution": {},
        }

    async def execute_task(
        self,
        task_description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a task through the routed provider."""
        routing_result = await self.route_task(task_description, **kwargs)

        if not routing_result.get("success"):
            return routing_result

        try:
            # Use the provider router to execute
            response = await self.provider_router.chat(
                messages=[{"role": "user", "content": task_description}],
                provider=routing_result["routing"]["provider"],
                model=routing_result["routing"]["model"],
                timeout=30,
            )

            # Add execution result to the response
            routing_result["execution"] = {
                "success": True,
                "response": response,
                "execution_time_ms": round((time.time() - time.time()) * 1000, 2),
            }

            return routing_result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
