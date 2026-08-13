"""Model pricing — static per-1000-token costs and cost-tier helpers.

Pure, stateless helpers used by the Hivemind cost endpoints to estimate
costs and categorise models into free/cheap/premium tiers. Budget
enforcement and spend tracking live in ``budget_manager``.
"""
from __future__ import annotations

# Known per-1000-token costs (USD per 1K tokens).
# Sources: OpenRouter pricing pages.
MODEL_COST_PER_1K = {
    # OpenRouter models
    "glm-5.1": {"input": 0.0015, "output": 0.0030},       # architecture
    "claude-opus-4.7": {"input": 0.0150, "output": 0.0750}, # reviewer
    "deepseek-v4-flash": {"input": 0.0005, "output": 0.0015}, # debugger
    "qwen3.6-27b": {"input": 0.0010, "output": 0.0020},     # docgen
    # Ollama (free/local)
    "qwen2.5-coder:3b": {"input": 0.0, "output": 0.0},
    "llama3": {"input": 0.0, "output": 0.0},
    "codellama": {"input": 0.0, "output": 0.0},
    "mistral": {"input": 0.0, "output": 0.0},
    # OpenAI fallback
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "gpt-4o": {"input": 0.0025, "output": 0.0100},
    # Generic catch-all (conservative estimate)
    "__default__": {"input": 0.002, "output": 0.008},
}


def _rates(model: str) -> dict[str, float]:
    return MODEL_COST_PER_1K.get(model, MODEL_COST_PER_1K["__default__"])


def estimate_cost(
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> float:
    """Estimate cost for a model given token counts."""
    rates = _rates(model)
    input_cost = (prompt_tokens / 1000) * rates["input"]
    output_cost = (completion_tokens / 1000) * rates["output"]
    return input_cost + output_cost


def cheapest_model(models: list[str]) -> str | None:
    """Return the model with the lowest output cost, or None if empty."""
    if not models:
        return None
    return min(models, key=lambda m: _rates(m)["output"])


def cost_tiers(models: list[str]) -> dict[str, list[str]]:
    """Categorise models into free/cheap/premium tiers."""
    tiers: dict[str, list[str]] = {"free": [], "cheap": [], "premium": []}
    for model in models:
        output_cost = _rates(model)["output"]
        if output_cost == 0.0:
            tiers["free"].append(model)
        elif output_cost <= 0.002:
            tiers["cheap"].append(model)
        else:
            tiers["premium"].append(model)
    return tiers


def summarize_tiers() -> dict[str, list[str]]:
    """Return all known models grouped into free/cheap/premium tiers."""
    tiers: dict[str, list[str]] = {"free": [], "cheap": [], "premium": []}
    for model, rates in MODEL_COST_PER_1K.items():
        if model.startswith("_"):
            continue
        output_cost = rates["output"]
        if output_cost == 0.0:
            tiers["free"].append(model)
        elif output_cost <= 0.002:
            tiers["cheap"].append(model)
        else:
            tiers["premium"].append(model)
    return tiers
