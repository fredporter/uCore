"""Server-owned ExecutionContext for uDOS and uCore.

Provides immutable task scope, permitted paths, non-goals, provider eligibility,
network policy, and budget constraints across execution boundaries.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any


class ExecutionContextError(Exception):
    """Base exception for execution context violations."""


class PathAccessViolation(ExecutionContextError):
    """Raised when an operation attempts to access paths outside permitted boundaries."""


class ProviderAccessViolation(ExecutionContextError):
    """Raised when an executor or model attempts to use an ineligible provider."""


class NetworkAccessViolation(ExecutionContextError):
    """Raised when an operation violates the task's network policy."""


VALID_SCOPES = {"user", "developer"}
VALID_LANES = {
    "everyday",
    "authoring",
    "ucode",
    "usx",
    "git",
    "snacks",
    "research",
    "dev",
    "knowledge",
    "maintenance",
    "workflow",
}
VALID_NETWORK_POLICIES = {
    "offline",
    "local_only",
    "named_connector",
    "research_web",
    "dev_scoped",
}


@dataclass
class ExecutionContext:
    """Server-owned execution context binding a task to its authorized boundaries."""

    task_id: str
    scope: str = "developer"
    lane: str = "dev"
    repository: str = ""
    revision: str = ""
    permitted_paths: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)
    provider_eligibility: list[str] = field(default_factory=lambda: ["ollama"])
    network_policy: str = "local_only"
    budget_reservation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"Invalid scope '{self.scope}', must be one of {VALID_SCOPES}")
        if self.lane not in VALID_LANES:
            raise ValueError(f"Invalid lane '{self.lane}', must be one of {VALID_LANES}")
        if self.network_policy not in VALID_NETWORK_POLICIES:
            raise ValueError(
                f"Invalid network_policy '{self.network_policy}', must be one of {VALID_NETWORK_POLICIES}"
            )
        # Enforce local-first lane invariant: User scope has hard-zero cloud/premium-AI allowance
        if self.scope == "user":
            self.provider_eligibility = [p for p in self.provider_eligibility if p == "ollama"]
            if not self.provider_eligibility:
                self.provider_eligibility = ["ollama"]

    def validate_path(self, relative_path: str) -> None:
        """Validate that a repository-relative path does not escape root and matches permitted_paths."""
        if not relative_path or not isinstance(relative_path, str):
            raise PathAccessViolation("Path must be a non-empty string")

        clean = relative_path.replace("\\", "/").strip()
        if clean.startswith("/"):
            raise PathAccessViolation(f"Path '{relative_path}' must be repository-relative, not absolute")

        parts = PurePosixPath(clean).parts
        if ".." in parts:
            raise PathAccessViolation(f"Path traversal detected in '{relative_path}'")

        if self.permitted_paths:
            matched = any(
                fnmatch.fnmatch(clean, pattern) or clean == pattern
                for pattern in self.permitted_paths
            )
            if not matched:
                raise PathAccessViolation(
                    f"Path '{relative_path}' is not within permitted paths: {self.permitted_paths}"
                )

    def validate_provider(self, provider: str, cost: float = 0.0) -> None:
        """Enforce provider eligibility and local-first cost bounds."""
        if self.scope == "user":
            if provider != "ollama" or cost > 0.0:
                raise ProviderAccessViolation(
                    f"User scope tasks are restricted to local zero-cost inference; "
                    f"provider '{provider}' with cost {cost} is denied"
                )
        if provider not in self.provider_eligibility:
            raise ProviderAccessViolation(
                f"Provider '{provider}' is not eligible under this execution context. "
                f"Allowed providers: {self.provider_eligibility}"
            )

    def validate_network(self, destination: str) -> None:
        """Enforce task-level network boundaries."""
        if self.network_policy == "offline":
            raise NetworkAccessViolation(
                f"Task network policy is 'offline'; outbound access to '{destination}' is denied"
            )

        if self.network_policy == "local_only":
            dest_lower = destination.lower()
            allowed_local = ("localhost", "127.0.0.1", "::1", "0.0.0.0")
            if not any(local in dest_lower for local in allowed_local):
                raise NetworkAccessViolation(
                    f"Task network policy is 'local_only'; outbound access to '{destination}' is denied"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "taskId": self.task_id,
            "scope": self.scope,
            "lane": self.lane,
            "repository": self.repository,
            "revision": self.revision,
            "permittedPaths": list(self.permitted_paths),
            "nonGoals": list(self.non_goals),
            "providerEligibility": list(self.provider_eligibility),
            "networkPolicy": self.network_policy,
            "budgetReservationId": self.budget_reservation_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionContext:
        return cls(
            task_id=data.get("taskId") or data.get("task_id", ""),
            scope=data.get("scope", "developer"),
            lane=data.get("lane", "dev"),
            repository=data.get("repository", ""),
            revision=data.get("revision", ""),
            permitted_paths=list(data.get("permittedPaths") or data.get("permitted_paths") or []),
            non_goals=list(data.get("nonGoals") or data.get("non_goals") or []),
            provider_eligibility=list(
                data.get("providerEligibility") or data.get("provider_eligibility") or ["ollama"]
            ),
            network_policy=data.get("networkPolicy") or data.get("network_policy", "local_only"),
            budget_reservation_id=data.get("budgetReservationId") or data.get("budget_reservation_id"),
            metadata=dict(data.get("metadata", {})),
        )
