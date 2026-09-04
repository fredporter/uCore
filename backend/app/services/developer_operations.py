"""Governed ACP operations for the Developer Workbench.

This module is the product boundary around the optional NanoCoder engine.  It
keeps session state in uCore, requires approval for write-capable actions, and
normalizes vendor ACP events before they reach the UI.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
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
    proposal: dict[str, Any] | None = None
    repository_fingerprint: str = ""
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
            "proposal": self.proposal,
        }


def _git(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def _repository_fingerprint(repo: Path) -> str:
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    diff = _git(repo, "diff", "--binary", "HEAD")
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    digest = hashlib.sha256(f"{status.stdout}\0{diff.stdout}".encode())
    for relative in filter(None, untracked.stdout.split("\0")):
        candidate = repo / relative
        digest.update(relative.encode())
        if candidate.is_file():
            digest.update(candidate.read_bytes())
    return digest.hexdigest()


def _copy_working_tree(source: Path, destination: Path) -> None:
    ignored = {".git", "node_modules", ".venv", "dist", "build", "__pycache__"}
    for child in destination.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in source.iterdir():
        if child.name in ignored:
            continue
        target = destination / child.name
        if child.is_dir() and not child.is_symlink():
            shutil.copytree(child, target, ignore=shutil.ignore_patterns(*ignored))
        elif child.is_file():
            shutil.copy2(child, target)


def _proposal_files(diff_text: str) -> list[dict[str, Any]]:
    lines = diff_text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith("diff --git ")]
    files: list[dict[str, Any]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        section = "\n".join(lines[start:end]) + "\n"
        path = ""
        for line in lines[start:end]:
            if line.startswith("+++ b/"):
                path = line[6:]
                break
            if line.startswith("--- a/"):
                path = line[6:]
        if path:
            files.append(
                {
                    "path": path,
                    "patch": section,
                    "fingerprint": hashlib.sha256(section.encode()).hexdigest(),
                    "applied": False,
                }
            )
    return files


def _prepare_proposal_workspace(repository: Path) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory(prefix="ucore-acp-proposal-")
    workspace = Path(temporary.name) / repository.name
    clone = subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(repository), str(workspace)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if clone.returncode != 0:
        temporary.cleanup()
        raise RuntimeError(f"Could not create proposal workspace: {clone.stderr.strip()}")
    _copy_working_tree(repository, workspace)
    _git(workspace, "add", "-A")
    baseline = subprocess.run(
        [
            "git",
            "-C",
            str(workspace),
            "-c",
            "user.name=uCore",
            "-c",
            "user.email=proposal@localhost",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "uCore proposal baseline",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if baseline.returncode != 0:
        temporary.cleanup()
        raise RuntimeError(f"Could not seal proposal baseline: {baseline.stderr.strip()}")
    return temporary, workspace


class DeveloperOperationManager:
    """Own and supervise repository-scoped Developer ACP operations."""

    def __init__(self, state_path: Path | None = None) -> None:
        self.operations: dict[str, DeveloperOperation] = {}
        self.state_path = state_path or settings.data_dir / "developer-operations.json"
        self.audit_path = self.state_path.with_suffix(".jsonl")
        self._load()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            records = json.loads(self.state_path.read_text(encoding="utf-8"))
            for record in records[-50:]:
                status = record.get("status", "failed")
                if status in {"queued", "running"}:
                    status = "interrupted"
                operation = DeveloperOperation(
                    id=record["id"],
                    action=record["action"],
                    repository=record["repository"],
                    prompt=record["prompt"],
                    context=record.get("context", {}),
                    write_capable=bool(record.get("writeCapable")),
                    status=status,
                    created_at=int(record.get("createdAt", _now_ms())),
                    updated_at=int(record.get("updatedAt", _now_ms())),
                    session_id=record.get("sessionId"),
                    events=record.get("events", []),
                    result=record.get("result"),
                    error=record.get("error"),
                    proposal=record.get("proposal"),
                    repository_fingerprint=record.get("repositoryFingerprint", ""),
                )
                self.operations[operation.id] = operation
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            self.operations = {}

    def _persist(self, operation: DeveloperOperation, event: str) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        records = [
            item.public() | {"repositoryFingerprint": item.repository_fingerprint}
            for item in self.operations.values()
        ]
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(records[-50:], indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)
        audit_record = {
            "at": _now_ms(),
            "event": event,
            "operationId": operation.id,
            "repository": operation.repository,
            "action": operation.action,
            "status": operation.status,
            "taskReference": operation.context.get("taskReference", ""),
            "proposalFingerprint": (operation.proposal or {}).get("fingerprint", ""),
        }
        with self.audit_path.open("a", encoding="utf-8") as audit:
            audit.write(json.dumps(audit_record, separators=(",", ":")) + "\n")

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
        operation.repository_fingerprint = _repository_fingerprint(
            (settings.udos_root / repository).resolve(strict=True)
        )
        self._persist(operation, "created")
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
        self._persist(operation, "approved")
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
        self._persist(operation, "denied")
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
        self._persist(operation, "cancelled")
        return operation

    def apply_proposal(self, operation_id: str, path: str, fingerprint: str) -> DeveloperOperation:
        operation = self.get(operation_id)
        proposal = operation.proposal or {}
        files = proposal.get("files") if isinstance(proposal.get("files"), list) else []
        item = next((entry for entry in files if entry.get("path") == path), None)
        if item is None or item.get("fingerprint") != fingerprint:
            raise ValueError("Proposal file or fingerprint is invalid")
        if item.get("applied"):
            raise ValueError("Proposal file was already applied")
        repository = (settings.udos_root / operation.repository).resolve(strict=True)
        candidate = (repository / path).resolve()
        if repository not in candidate.parents or candidate == repository:
            raise ValueError("Proposal path escapes repository root")
        if _repository_fingerprint(repository) != operation.repository_fingerprint:
            raise RuntimeError("Repository changed since this proposal was created; review again")
        result = _git(
            repository,
            "apply",
            "--whitespace=nowarn",
            "-",
            input_text=item["patch"],
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Proposal could not be applied")
        item["applied"] = True
        operation.repository_fingerprint = _repository_fingerprint(repository)
        operation.updated_at = _now_ms()
        operation.events.append(
            {"type": "proposal", "status": "applied", "path": path, "at": operation.updated_at}
        )
        self._persist(operation, "proposal_applied")
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
        temporary: tempfile.TemporaryDirectory[str] | None = None
        try:
            command = self._command()
            if command is None:
                raise AcpError("NanoCoder is not installed; run scripts/install_nanocoder.sh")
            repository = (settings.udos_root / operation.repository).resolve(strict=True)
            temporary, proposal_workspace = _prepare_proposal_workspace(repository)

            async def on_event(message: dict[str, Any]) -> None:
                operation.events.append(self._normalize_event(message))
                operation.updated_at = _now_ms()
                self._persist(operation, "acp_event")

            client = NanocoderAcpClient(
                command,
                repository=proposal_workspace,
                repositories_root=proposal_workspace.parent,
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
            proposal_diff = _git(proposal_workspace, "diff", "--binary", "HEAD").stdout
            proposal_files = _proposal_files(proposal_diff)
            operation.proposal = (
                {
                    "fingerprint": hashlib.sha256(proposal_diff.encode()).hexdigest(),
                    "files": proposal_files,
                }
                if proposal_files
                else None
            )
            operation.status = "completed"
        except asyncio.CancelledError:
            operation.status = "cancelled"
        except Exception as exc:
            operation.status = "failed"
            operation.error = str(exc)[:2_000]
        finally:
            if temporary is not None:
                temporary.cleanup()
            operation.client = None
            operation.updated_at = _now_ms()
            operation.events.append(
                {"type": "lifecycle", "status": operation.status, "at": operation.updated_at}
            )
            self._persist(operation, operation.status)

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
