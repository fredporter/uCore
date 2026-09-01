"""Governed Agent Client Protocol transport for NanoCoder Dev Mode.

The transport is deliberately route-agnostic.  It owns process containment and
JSON-RPC framing; product policy must authorize a repository, model and budget
before constructing a client.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any


class AcpError(RuntimeError):
    """Base error raised by the governed ACP transport."""


class AcpProtocolError(AcpError):
    """Raised when the child emits invalid or unsuccessful JSON-RPC."""


PermissionHandler = Callable[[dict[str, Any]], Awaitable[str | None]]
EventHandler = Callable[[dict[str, Any]], Awaitable[None]]
_POLICY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


class NanocoderAcpClient:
    """Supervise one NanoCoder ACP process using newline-delimited JSON-RPC."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        repository: Path,
        repositories_root: Path,
        udos_home: Path,
        dev_mode: bool,
        request_timeout: float = 120.0,
        permission_handler: PermissionHandler | None = None,
        event_handler: EventHandler | None = None,
    ) -> None:
        if not command or any(not part for part in command):
            raise ValueError("command must contain explicit non-empty arguments")
        if not dev_mode:
            raise PermissionError("Dev Mode must be enabled before ACP launch")
        if request_timeout <= 0 or request_timeout > 300:
            raise ValueError("request_timeout must be between 0 and 300 seconds")

        root = repositories_root.resolve(strict=True)
        repo = repository.resolve(strict=True)
        try:
            repo.relative_to(root)
        except ValueError as exc:
            raise PermissionError("repository is outside the approved root") from exc

        self.command = tuple(command)
        self.repository = repo
        self.udos_home = udos_home.resolve()
        self.request_timeout = request_timeout
        self.permission_handler = permission_handler
        self.event_handler = event_handler
        self.events: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1_000)

        self._process: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._next_id = 1
        self._write_lock = asyncio.Lock()
        self._stderr: list[str] = []

    def configure_local_provider(self, *, name: str, model: str, base_url: str) -> None:
        """Write a secret-free, loopback-only provider policy before launch."""
        if self.running:
            raise AcpError("provider policy cannot change while ACP is running")
        if not _POLICY_ID.fullmatch(name) or not _POLICY_ID.fullmatch(model):
            raise ValueError("provider and model must be bounded identifiers")
        if not base_url.startswith(("http://127.0.0.1:", "http://localhost:")):
            raise PermissionError("initial ACP provider policy is loopback-only")
        config_home = self.udos_home / "vendor" / "nanocoder" / "config"
        config_home.mkdir(parents=True, exist_ok=True)
        config = {
            "nanocoder": {
                "providers": [
                    {
                        "name": name,
                        "baseUrl": base_url,
                        "apiKey": "local",
                        "models": [model],
                        "sdkProvider": "openai-compatible",
                    }
                ],
                "modeProviders": {"plan": {"provider": name, "model": model}},
                "defaultMode": "plan",
                "headless": {"maxTurns": 20},
                "mcpServers": [],
                "alwaysAllow": [],
            }
        }
        target = config_home / "agents.config.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(target)

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    @property
    def stderr_tail(self) -> tuple[str, ...]:
        return tuple(self._stderr[-50:])

    async def start(self) -> None:
        if self.running:
            return
        config_home = self.udos_home / "vendor" / "nanocoder" / "config"
        state_home = self.udos_home / "vendor" / "nanocoder" / "state"
        tasks_home = state_home / "tasks" / self.repository.name
        config_home.mkdir(parents=True, exist_ok=True)
        state_home.mkdir(parents=True, exist_ok=True)
        tasks_home.mkdir(parents=True, exist_ok=True)
        child_env = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "LANG", "LC_ALL", "TERM", "TMPDIR"}
        }
        child_env.update(
            {
                "HOME": str(state_home),
                "XDG_CONFIG_HOME": str(config_home),
                "XDG_STATE_HOME": str(state_home),
                "XDG_DATA_HOME": str(state_home),
                "NANOCODER_CONFIG_DIR": str(config_home),
                "NANOCODER_DATA_DIR": str(state_home),
                "NANOCODER_TASKS_DIR": str(tasks_home),
            }
        )
        self._process = await asyncio.create_subprocess_exec(
            *self.command,
            cwd=self.repository,
            env=child_env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader_task = asyncio.create_task(self._read_stdout())
        self._stderr_task = asyncio.create_task(self._read_stderr())

    async def initialize(self, protocol_version: int = 1) -> dict[str, Any]:
        result = await self.request(
            "initialize",
            {
                "protocolVersion": protocol_version,
                "clientInfo": {"name": "uCore", "version": "1"},
                "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False}},
            },
        )
        if not isinstance(result, dict):
            raise AcpProtocolError("initialize result must be an object")
        return result

    async def new_session(self, *, mode: str = "plan") -> str:
        if mode not in {"plan", "normal"}:
            raise PermissionError("only plan and reviewed normal modes are supported")
        result = await self.request(
            "session/new",
            {"cwd": str(self.repository), "mcpServers": [], "modeId": mode},
        )
        if not isinstance(result, dict) or not isinstance(result.get("sessionId"), str):
            raise AcpProtocolError("session/new did not return a sessionId")
        return result["sessionId"]

    async def prompt(self, session_id: str, text: str) -> dict[str, Any]:
        if not text or len(text) > 16_000:
            raise ValueError("prompt must contain between 1 and 16000 characters")
        result = await self.request(
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": text}]},
        )
        if not isinstance(result, dict):
            raise AcpProtocolError("session/prompt result must be an object")
        return result

    async def cancel(self, session_id: str) -> None:
        await self.notify("session/cancel", {"sessionId": session_id})

    async def request(self, method: str, params: dict[str, Any]) -> Any:
        await self.start()
        request_id = self._next_id
        self._next_id += 1
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        await self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        try:
            return await asyncio.wait_for(future, timeout=self.request_timeout)
        except TimeoutError as exc:
            self._pending.pop(request_id, None)
            raise AcpError(f"ACP request timed out: {method}") from exc

    async def notify(self, method: str, params: dict[str, Any]) -> None:
        await self.start()
        await self._send({"jsonrpc": "2.0", "method": method, "params": params})

    async def close(self) -> None:
        process = self._process
        if process is None:
            return
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
            except TimeoutError:
                process.kill()
                await process.wait()
        for task in (self._reader_task, self._stderr_task):
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._fail_pending(AcpError("ACP client closed"))
        self._process = None

    async def _send(self, payload: dict[str, Any]) -> None:
        process = self._process
        if process is None or process.stdin is None or process.returncode is not None:
            raise AcpError("ACP process is not running")
        encoded = json.dumps(payload, separators=(",", ":")).encode() + b"\n"
        async with self._write_lock:
            process.stdin.write(encoded)
            await process.stdin.drain()

    async def _read_stdout(self) -> None:
        assert self._process is not None and self._process.stdout is not None
        try:
            while line := await self._process.stdout.readline():
                try:
                    message = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise AcpProtocolError("ACP child emitted invalid JSON") from exc
                await self._handle_message(message)
            code = await self._process.wait()
            self._fail_pending(AcpError(f"ACP process exited with status {code}"))
        except Exception as exc:
            self._fail_pending(exc)

    async def _read_stderr(self) -> None:
        assert self._process is not None and self._process.stderr is not None
        while line := await self._process.stderr.readline():
            self._stderr.append(line.decode(errors="replace").rstrip()[:2_000])
            del self._stderr[:-50]

    async def _handle_message(self, message: Any) -> None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            raise AcpProtocolError("invalid JSON-RPC envelope")
        request_id = message.get("id")
        if request_id is not None and "method" not in message:
            future = self._pending.pop(request_id, None)
            if future is None:
                return
            if "error" in message:
                future.set_exception(AcpProtocolError(str(message["error"])))
            else:
                future.set_result(message.get("result"))
            return
        if "method" in message and request_id is not None:
            await self._handle_agent_request(message)
            return
        await self.events.put(message)
        if self.event_handler is not None:
            await self.event_handler(message)

    async def _handle_agent_request(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        if method == "session/request_permission":
            outcome = None
            if self.permission_handler is not None:
                outcome = await self.permission_handler(message.get("params") or {})
            result = {"outcome": {"outcome": "cancelled"}}
            if outcome:
                result = {"outcome": {"outcome": "selected", "optionId": outcome}}
            await self._send({"jsonrpc": "2.0", "id": message["id"], "result": result})
            return
        await self._send(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "error": {"code": -32601, "message": "client method not enabled"},
            }
        )

    def _fail_pending(self, error: BaseException) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_exception(error)
        self._pending.clear()

    async def __aenter__(self) -> NanocoderAcpClient:
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
