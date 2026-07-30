"""Cline Invoke Skill — invoke Cline CLI from uCore skills.

Invokes Cline CLI (VS Code extension's CLI) from within uCore's skill
ecosystem, allowing Dev Mode to use Cline as an agentic executor for
complex multi-step tasks.

Modes:
    - yolo: autonomous execution with auto-approval on
    - interactive: auto-approval off

Integrates with: Cline CLI, OpenRouter API, gh CLI.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path

from app.core.settings import settings
from app.skills.base import BaseSkill, SkillMeta, SkillParam

log = logging.getLogger("ucore.skills.cline_invoke")


def _find_cline_binary() -> str | None:
    """Locate the Cline CLI binary."""
    candidates = [
        "cline",
        str(Path.home() / ".local" / "bin" / "cline"),
        str(Path.home() / ".npm-global" / "bin" / "cline"),
        "/usr/local/bin/cline",
    ]
    for c in candidates:
        if Path(c).exists() or _which(c):
            return c
    return None


def _which(cmd: str) -> bool:
    """Check if a command is in PATH."""
    try:
        result = subprocess.run(
            ["which", cmd],
            capture_output=True, text=True, timeout=2, check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def _load_user_vars() -> dict:
    """Load uCore user/dev variables from the internal variable store."""
    path = settings.data_dir / "variables.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _resolve_cline_runtime_config(kwargs: dict, mode: str) -> dict[str, str]:
    """Resolve provider/model/thinking/approval from internal config first.

    Fail-fast policy:
    - provider/model must be explicitly configured in kwargs, variables store,
      or UCORE_CLINE_* env vars.
    - do not silently hardcode provider/model defaults.
    """
    user_vars = _load_user_vars()

    provider = (
        str(kwargs.get("provider", "")).strip()
        or str(user_vars.get("cline_provider", "")).strip()
        or os.environ.get("UCORE_CLINE_PROVIDER", "").strip()
    )

    model = (
        str(kwargs.get("model", "")).strip()
        or str(user_vars.get("cline_model", "")).strip()
        or os.environ.get("UCORE_CLINE_MODEL", "").strip()
    )

    thinking = (
        str(kwargs.get("thinking", "")).strip()
        or str(user_vars.get("cline_thinking", "")).strip()
        or os.environ.get("UCORE_CLINE_THINKING", "").strip()
        or "low"
    )

    auto_approve = str(
        kwargs.get(
            "auto_approve",
            user_vars.get(
                "cline_auto_approve",
                "true" if mode == "yolo" else "false",
            ),
        ),
    ).strip().lower()
    if auto_approve not in {"true", "false"}:
        auto_approve = "true" if mode == "yolo" else "false"

    return {
        "provider": provider,
        "model": model,
        "thinking": thinking,
        "auto_approve": auto_approve,
    }


def _build_repair_instructions(missing: list[str]) -> list[str]:
    """Return actionable repair steps for missing runtime config."""
    steps = [
        "Set values via internal API: PUT /api/variables/user",
        "Example payload: {\"cline_provider\": \"ollama\", \"cline_model\": \"qwen2.5-coder:3b\", \"cline_thinking\": \"low\"}",
        "Or set env vars: UCORE_CLINE_PROVIDER and UCORE_CLINE_MODEL",
    ]
    if "api_key" in missing:
        steps.append(
            "For key-based providers, set API key in Secret Store (/api/secrets) or env (e.g. OPENROUTER_API_KEY)",
        )
    return steps


class ClineInvokeSkill(BaseSkill):
    """Invoke Cline CLI for autonomous task execution."""

    meta = SkillMeta(
        id="cline-invoke",
        name="Cline Invoke",
                description=(
                    "Invoke Cline CLI from uCore skills using positional"
                    " prompt mode. Supports yolo (auto-approve true) and"
                    " interactive (auto-approve false)."
                ),
        category="developer",
        timeout=300,
        params=[
            SkillParam(
                name="task",
                type="string",
                required=True,
                description="Task description for Cline to execute",
            ),
            SkillParam(
                name="mode",
                type="string",
                required=False,
                default="interactive",
                description="Execution mode: 'yolo' or 'interactive'",
            ),
            SkillParam(
                name="cwd",
                type="string",
                required=False,
                default="",
                description="Working directory (default: uCore root)",
            ),
            SkillParam(
                name="timeout",
                type="integer",
                required=False,
                default=120,
                description="Max execution time in seconds",
            ),
            SkillParam(
                name="context",
                type="string",
                required=False,
                default="",
                description="Additional context for Cline",
            ),
            SkillParam(
                name="provider",
                type="string",
                required=False,
                default="",
                description="Override provider (else uCore variables/settings)",
            ),
            SkillParam(
                name="model",
                type="string",
                required=False,
                default="",
                description="Override model id (else uCore variables/settings)",
            ),
            SkillParam(
                name="thinking",
                type="string",
                required=False,
                default="",
                description="Thinking level override: none|low|medium|high|xhigh",
            ),
            SkillParam(
                name="auto_approve",
                type="string",
                required=False,
                default="",
                description="Override auto-approve: true|false",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        task = kwargs.get("task", "").strip()
        mode = kwargs.get("mode", "interactive").lower()
        cwd = kwargs.get("cwd", str(Path.cwd()))
        timeout = int(kwargs.get("timeout", 120))
        context = kwargs.get("context", "")

        if not task:
            return {"success": False, "error": "task is required"}

        if mode not in ("yolo", "interactive"):
            mode = "interactive"

        # Locate Cline CLI
        cline_bin = _find_cline_binary()
        if not cline_bin:
            return {
                "success": False,
                "error": "Cline CLI not found in PATH",
                "fallback": (
                    "Install Cline CLI: npm install -g @cline/cli"
                    " or use roundtable-dispatch instead"
                ),
            }

        runtime_cfg = _resolve_cline_runtime_config(kwargs, mode)

        missing_cfg: list[str] = []
        if not runtime_cfg["provider"]:
            missing_cfg.append("provider")
        if not runtime_cfg["model"]:
            missing_cfg.append("model")
        if missing_cfg:
            return {
                "success": False,
                "error": (
                    "Cline runtime config missing required values: "
                    f"{', '.join(missing_cfg)}"
                ),
                "repair_required": True,
                "missing": missing_cfg,
                "repair_steps": _build_repair_instructions(missing_cfg),
            }

        # Resolve API key: DEEPSEEK_API_KEY first, then SecretStore, then
        # OPENROUTER_API_KEY, then env file fallback
        api_key: str = ""
        # Priority 1: DEEPSEEK_API_KEY from environment
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        # Priority 2: DEEPSEEK_API_KEY from SecretStore
        if not api_key:
            try:
                from app.secret.store import get_store
                store = get_store()
                dsk_val = store.get("DEEPSEEK_API_KEY")
                if dsk_val:
                    api_key = dsk_val
            except Exception:
                pass
        # Priority 3: OPENROUTER_API_KEY from environment (fallback)
        if not api_key:
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
        # Priority 4: DEEPSEEK_API_KEY or OPENROUTER_API_KEY from env file

        if not api_key:
            try:
                config_path = (
                    Path.home() / ".config" / "hivemind" / ".env"
                )
                if config_path.exists():
                    content = config_path.read_text()
                    for line in content.splitlines():
                        if line.startswith("DEEPSEEK_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"')
                            if api_key:
                                break
                        if line.startswith("OPENROUTER_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"')
                            if api_key:
                                break
            except Exception:
                pass

        # Build command against current Cline CLI interface.
        prompt = task
        if context:
            prompt = f"{task}\n\nContext:\n{context}"

        cmd = [
            cline_bin,
            "--json",
            "--cwd", cwd,
            "-P", runtime_cfg["provider"],
            "-m", runtime_cfg["model"],
            "--thinking", runtime_cfg["thinking"],
            "-t", str(timeout),
            "--auto-approve", runtime_cfg["auto_approve"],
        ]

        # API key is only required for key-based providers.
        needs_key_provider = runtime_cfg["provider"].lower() in {
            "openrouter", "openai", "anthropic", "gemini", "groq", "deepseek", "mistral",
        }
        if needs_key_provider and not api_key:
            missing_cfg = ["api_key"]
            return {
                "success": False,
                "error": (
                    f"Provider '{runtime_cfg['provider']}' requires an API key, but none was found"
                ),
                "repair_required": True,
                "missing": missing_cfg,
                "repair_steps": _build_repair_instructions(missing_cfg),
                "provider": runtime_cfg["provider"],
                "model": runtime_cfg["model"],
            }
        if needs_key_provider and api_key:
            cmd.extend(["-k", api_key])

        cmd.append(prompt)

        # Execute
        try:
            result = await self._run_cline(cmd, cwd, timeout)
            if result.get("needs_auth"):
                return {
                    "success": False,
                    "action": "cline-invoke",
                    "mode": mode,
                    "binary": cline_bin,
                    "error": "Cline requires authentication before headless task execution",
                    "fallback": "Run: cline auth, then retry cline-invoke",
                    "output": result.get("output", ""),
                    "exit_code": result.get("exit_code", -1),
                    "duration_ms": result.get("duration_ms", 0),
                }

            return {
                "success": result.get("success", False),
                "action": "cline-invoke",
                "mode": mode,
                "binary": cline_bin,
                "output": result.get("output", ""),
                "provider": runtime_cfg["provider"],
                "model": runtime_cfg["model"],
                "exit_code": result.get("exit_code", -1),
                "duration_ms": result.get("duration_ms", 0),
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Cline task timed out after {timeout}s",
                "mode": mode,
                "binary": cline_bin,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "mode": mode,
                "binary": cline_bin,
            }

    async def _run_cline(
        self, cmd: list[str], cwd: str, timeout: int,
    ) -> dict:
        """Execute Cline CLI and capture output."""
        import time
        t0 = time.perf_counter()

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        duration = round((time.perf_counter() - t0) * 1000, 1)
        output = (
            stdout.decode("utf-8", errors="replace")
            if stdout else ""
        )
        if stderr:
            err_text = stderr.decode("utf-8", errors="replace")
            if err_text.strip():
                output += f"\n[stderr]\n{err_text}"

        needs_auth = "requires re-authentication" in output.lower()

        # Cline --json may emit one JSON object per line.
        parsed_obj = None
        for line in output.splitlines():
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(obj, dict):
                parsed_obj = obj

        if isinstance(parsed_obj, dict):
            msg = parsed_obj.get("message") or parsed_obj.get("response") or output
            if str(parsed_obj.get("type", "")).lower() == "error" and "requires re-authentication" in str(msg).lower():
                needs_auth = True
            return {
                "success": process.returncode == 0 and not needs_auth,
                "output": msg,
                "exit_code": process.returncode,
                "duration_ms": duration,
                "needs_auth": needs_auth,
            }

        return {
            "success": process.returncode == 0 and not needs_auth,
            "output": output[:5000],
            "exit_code": process.returncode,
            "duration_ms": duration,
            "needs_auth": needs_auth,
        }
