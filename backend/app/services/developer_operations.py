"""Governed ACP operations for the Developer Workbench.

This module is the product boundary around the optional NanoCoder engine.  It
keeps session state in uCore, requires approval for write-capable actions, and
normalizes vendor ACP events before they reach the UI.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.services.dev_layer import DevMode, get_dev_layer
from app.services.nanocoder_acp import AcpError, NanocoderAcpClient

ACTION_CATALOG: tuple[dict[str, Any], ...] = (
    {"id": "explain-selection", "label": "Explain selection", "icon": "lightbulb", "write": False},
    {"id": "diagnose-failure", "label": "Diagnose failure", "icon": "troubleshoot", "write": False},
    {"id": "propose-tests", "label": "Propose tests", "icon": "science", "write": False},
    {"id": "plan-refactor", "label": "Plan refactor", "icon": "account_tree", "write": False},
    {
        "id": "review-working-tree",
        "label": "Review working tree",
        "icon": "difference",
        "write": False,
    },
    {
        "id": "implement-reviewed-task",
        "label": "Implement reviewed task",
        "icon": "build",
        "write": True,
    },
)
_ACTIONS = {item["id"]: item for item in ACTION_CATALOG}


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class DeveloperOperation:
    id: str
    action: str
    repository: str
    prompt: str
    context: dict[str, Any]
    write_capable: bool
    status: str
    created_at: int = field(default_factory=_now_ms)
    updated_at: int = field(default_factory=_now_ms)
    session_id: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    task: asyncio.Task[None] | None = field(default=None, repr=False)
    client: NanocoderAcpClient | None = field(default=None, repr=False)

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "label": _ACTIONS[self.action]["label"],
            "repository": self.repository,
            "prompt": self.prompt,
            "context": self.context,
            "writeCapable": self.write_capable,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "sessionId": self.session_id,
            "events": self.events[-200:],
            "result": self.result,
            "error": self.error,
        }


class DeveloperOperationManager:
    """Own and supervise repository-scoped Developer ACP operations."""

    def __init__(self) -> None:
        self.operations: dict[str, DeveloperOperation] = {}

    def capabilities(self) -> dict[str, Any]:
        command = self._command()
        return {
            "engine": "nanocoder-acp",
            "available": command is not None,
            "devMode": get_dev_layer().mode.value,
            "approvalPolicy": "explicit-write",
            "actions": list(ACTION_CATALOG),
        }

    def create(
        self, *, action: str, repository: str, prompt: str, context: dict[str, Any]
    ) -> DeveloperOperation:
        spec = _ACTIONS.get(action)
        if spec is None:
            raise ValueError("Unsupported Developer action")
        if get_dev_layer().mode is not DevMode.ON:
            raise PermissionError("Developer ACP operations require Dev Mode on")
        clean_prompt = prompt.strip()
        if not clean_prompt or len(clean_prompt) > 16_000:
            raise ValueError("prompt must contain between 1 and 16000 characters")
        operation = DeveloperOperation(
            id=uuid.uuid4().hex,
            action=action,
            repository=repository,
            prompt=clean_prompt,
            context=self._bounded_context(context),
            write_capable=bool(spec["write"]),
            status="awaiting_approval" if spec["write"] else "queued",
        )
        operation.events.append(
            {"type": "lifecycle", "status": operation.status, "at": operation.created_at}
        )
        self.operations[operation.id] = operation
        if not operation.write_capable:
            operation.task = asyncio.create_task(self._run(operation, mode="plan"))
        return operation

    def approve(self, operation_id: str) -> DeveloperOperation:
        operation = self.get(operation_id)
        if operation.status != "awaiting_approval":
            raise ValueError("Operation is not awaiting approval")
        operation.status = "queued"
        operation.updated_at = _now_ms()
        operation.events.append(
            {"type": "approval", "decision": "approved", "at": operation.updated_at}
        )
        operation.task = asyncio.create_task(self._run(operation, mode="normal"))
        return operation

    def deny(self, operation_id: str) -> DeveloperOperation:
        operation = self.get(operation_id)
        if operation.status != "awaiting_approval":
            raise ValueError("Operation is not awaiting approval")
        operation.status = "denied"
        operation.updated_at = _now_ms()
        operation.events.append(
            {"type": "approval", "decision": "denied", "at": operation.updated_at}
        )
        return operation

    async def cancel(self, operation_id: str) -> DeveloperOperation:
        operation = self.get(operation_id)
        if operation.status in {"completed", "failed", "cancelled", "denied"}:
            return operation
        if operation.client is not None and operation.session_id:
            await operation.client.cancel(operation.session_id)
        if operation.task is not None:
            operation.task.cancel()
        operation.status = "cancelled"
        operation.updated_at = _now_ms()
        operation.events.append(
            {"type": "lifecycle", "status": "cancelled", "at": operation.updated_at}
        )
        return operation

    def get(self, operation_id: str) -> DeveloperOperation:
        try:
            return self.operations[operation_id]
        except KeyError as exc:
            raise KeyError("Developer operation not found") from exc

    def list(self, repository: str = "") -> list[dict[str, Any]]:
        values = self.operations.values()
        if repository:
            values = (item for item in values if item.repository == repository)
        return [
            item.public() for item in sorted(values, key=lambda item: item.created_at, reverse=True)
        ][:50]

    async def _run(self, operation: DeveloperOperation, *, mode: str) -> None:
        operation.status = "running"
        operation.updated_at = _now_ms()
        operation.events.append(
            {"type": "lifecycle", "status": "running", "at": operation.updated_at}
        )
        try:
            command = self._command()
            if command is None:
                raise AcpError("NanoCoder is not installed; run scripts/install_nanocoder.sh")
            repository = (settings.udos_root / operation.repository).resolve(strict=True)

            async def on_event(message: dict[str, Any]) -> None:
                operation.events.append(self._normalize_event(message))
                operation.updated_at = _now_ms()

            client = NanocoderAcpClient(
                command,
                repository=repository,
                repositories_root=settings.udos_root,
                udos_home=settings.udos_home,
                dev_mode=True,
                event_handler=on_event,
            )
            operation.client = client
            client.configure_local_provider(
                name="ollama",
                model=settings.ollama_default_model,
                base_url=f"{settings.ollama_base_url.rstrip('/')}/v1",
            )
            async with client:
                await client.initialize()
                operation.session_id = await client.new_session(mode=mode)
                operation.result = await client.prompt(
                    operation.session_id, self._build_prompt(operation)
                )
            operation.status = "completed"
        except asyncio.CancelledError:
            operation.status = "cancelled"
        except Exception as exc:
            operation.status = "failed"
            operation.error = str(exc)[:2_000]
        finally:
            operation.client = None
            operation.updated_at = _now_ms()
            operation.events.append(
                {"type": "lifecycle", "status": operation.status, "at": operation.updated_at}
            )

    @staticmethod
    def _bounded_context(context: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(context, dict):
            raise ValueError("context must be an object")
        allowed: dict[str, Any] = {}
        for key in ("file", "selection", "diagnostics", "taskReference"):
            value = context.get(key)
            if isinstance(value, str) and value:
                allowed[key] = value[: 20_000 if key == "selection" else 2_000]
        return allowed

    @staticmethod
    def _build_prompt(operation: DeveloperOperation) -> str:
        lines = [
            f"Developer action: {_ACTIONS[operation.action]['label']}",
            f"Repository: {operation.repository}",
            "Stay within this repository. Treat changes as proposals until uCore review.",
        ]
        for key, value in operation.context.items():
            lines.append(f"{key}: {value}")
        lines.append(f"Request: {operation.prompt}")
        return "\n".join(lines)

    @staticmethod
    def _normalize_event(message: dict[str, Any]) -> dict[str, Any]:
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        update = params.get("update") if isinstance(params.get("update"), dict) else {}
        return {
            "type": "acp",
            "method": str(message.get("method", "event"))[:120],
            "update": update,
            "at": _now_ms(),
        }

    @staticmethod
    def _command() -> list[str] | None:
        explicit = os.environ.get("UCORE_NANOCODER_BIN", "").strip()
        candidates = [Path(explicit)] if explicit else []
        candidates.append(
            settings.udos_home
            / "tools"
            / "nanocoder"
            / "1.30.0"
            / "node_modules"
            / ".bin"
            / "nanocoder"
        )
        located = shutil.which("nanocoder")
        if located:
            candidates.append(Path(located))
        for candidate in candidates:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return [str(candidate), "--acp"]
        return None


_manager: DeveloperOperationManager | None = None


def get_developer_operation_manager() -> DeveloperOperationManager:
    global _manager
    if _manager is None:
        _manager = DeveloperOperationManager()
    return _manager
