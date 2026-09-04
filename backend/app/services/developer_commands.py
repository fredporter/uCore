"""Bounded repository-defined commands for the Developer Workbench."""

from __future__ import annotations

import asyncio
import json
import os
import re
import signal
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.settings import settings
from app.services.dev_layer import DevMode, get_dev_layer

MAX_OUTPUT = 100_000
MAX_HISTORY = 100
ALLOWED_SCRIPT_NAMES = {"test", "build", "lint", "type-check", "check"}
_SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|token|secret|password)(\s*[:=]\s*)([^\s,;]+)"
)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _redact(value: str) -> str:
    return _SECRET_PATTERN.sub(r"\1\2[REDACTED]", value)


@dataclass
class CommandRun:
    id: str
    repository: str
    action: str
    command: tuple[str, ...]
    status: str = "queued"
    created_at: int = field(default_factory=_now_ms)
    started_at: int | None = None
    finished_at: int | None = None
    output: str = ""
    exit_code: int | None = None
    error: str | None = None
    process: asyncio.subprocess.Process | None = field(default=None, repr=False)
    task: asyncio.Task[None] | None = field(default=None, repr=False)

    def public(self) -> dict[str, Any]:
        duration = None
        if self.started_at:
            duration = ((self.finished_at or _now_ms()) - self.started_at) / 1000
        return {
            "id": self.id,
            "repository": self.repository,
            "action": self.action,
            "command": list(self.command),
            "status": self.status,
            "createdAt": self.created_at,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "durationSeconds": round(duration, 3) if duration is not None else None,
            "output": self.output,
            "truncated": len(self.output) >= MAX_OUTPUT,
            "exitCode": self.exit_code,
            "error": self.error,
        }


class DeveloperCommandManager:
    def __init__(self) -> None:
        self.runs: dict[str, CommandRun] = {}

    def discover(self, repository: str, repo_path: Path) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        package_file = repo_path / "package.json"
        if package_file.is_file():
            try:
                scripts = json.loads(package_file.read_text(encoding="utf-8")).get("scripts", {})
            except (json.JSONDecodeError, OSError):
                scripts = {}
            runner = "pnpm" if (repo_path / "pnpm-lock.yaml").exists() else "npm"
            for name in sorted(ALLOWED_SCRIPT_NAMES & set(scripts)):
                command = [runner, "run", name] if runner == "pnpm" else [runner, "run", name]
                actions.append(
                    {"id": name, "label": name.replace("-", " ").title(), "command": command}
                )
        return actions

    def start(
        self, repository: str, repo_path: Path, action: str, timeout: int = 300
    ) -> CommandRun:
        if get_dev_layer().mode is not DevMode.ON:
            raise PermissionError("Developer commands require Dev Mode on")
        actions = {item["id"]: item for item in self.discover(repository, repo_path)}
        if action not in actions:
            raise ValueError("Action is not defined and allowed by this repository")
        if timeout < 1 or timeout > 900:
            raise ValueError("timeout must be between 1 and 900 seconds")
        run = CommandRun(
            id=uuid.uuid4().hex,
            repository=repository,
            action=action,
            command=tuple(actions[action]["command"]),
        )
        self.runs[run.id] = run
        run.task = asyncio.create_task(self._execute(run, repo_path, timeout))
        return run

    async def cancel(self, run_id: str) -> CommandRun:
        run = self.get(run_id)
        if run.status not in {"queued", "running"}:
            return run
        if run.process and run.process.returncode is None:
            with __import__("contextlib").suppress(ProcessLookupError):
                os.killpg(run.process.pid, signal.SIGTERM)
        if run.task:
            run.task.cancel()
            with __import__("contextlib").suppress(asyncio.CancelledError):
                await run.task
        else:
            run.status = "cancelled"
            run.finished_at = _now_ms()
            self._audit(run)
        return run

    def get(self, run_id: str) -> CommandRun:
        if run_id not in self.runs:
            raise KeyError("Developer command run not found")
        return self.runs[run_id]

    def list(self, repository: str = "") -> list[dict[str, Any]]:
        values = self.runs.values()
        if repository:
            values = (run for run in values if run.repository == repository)
        return [
            run.public() for run in sorted(values, key=lambda run: run.created_at, reverse=True)
        ][:MAX_HISTORY]

    async def _execute(self, run: CommandRun, repo_path: Path, timeout: int) -> None:
        run.status = "running"
        run.started_at = _now_ms()
        env = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "LANG", "LC_ALL", "TERM", "TMPDIR", "CI"}
        }
        env["CI"] = "1"
        try:
            run.process = await asyncio.create_subprocess_exec(
                *run.command,
                cwd=repo_path,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
            )
            stdout, _ = await asyncio.wait_for(run.process.communicate(), timeout=timeout)
            run.exit_code = run.process.returncode
            run.output = _redact(stdout.decode(errors="replace"))[:MAX_OUTPUT]
            run.status = "passed" if run.exit_code == 0 else "failed"
        except TimeoutError:
            if run.process and run.process.returncode is None:
                os.killpg(run.process.pid, signal.SIGKILL)
            run.status = "timed_out"
            run.error = f"Action exceeded {timeout} seconds"
        except asyncio.CancelledError:
            run.status = "cancelled"
        except Exception as exc:
            run.status = "failed"
            run.error = _redact(str(exc))[:1_000]
        finally:
            run.finished_at = _now_ms()
            run.process = None
            self._audit(run)

    @staticmethod
    def _audit(run: CommandRun) -> None:
        path = settings.logs_dir / "developer-actions.jsonl"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            record = run.public()
            record.pop("output", None)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        except OSError:
            pass


_manager: DeveloperCommandManager | None = None


def get_developer_command_manager() -> DeveloperCommandManager:
    global _manager
    if _manager is None:
        _manager = DeveloperCommandManager()
    return _manager
