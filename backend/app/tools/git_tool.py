"""Tools: Git probe."""

from __future__ import annotations

import asyncio
import logging

from app.tools.base import BaseTool, ToolInfo

log = logging.getLogger(__name__)


class GitTool(BaseTool):
    """Probe for Git on PATH."""

    id = "git"
    name = "Git"
    description = "Version control"

    async def check(self) -> ToolInfo:
        """Return ToolInfo describing whether `git` is installed."""
        info = ToolInfo(id=self.id, name=self.name)
        try:
            proc = await asyncio.create_subprocess_exec(
                "git",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                info.installed = True
                info.version = out.decode().strip()
            else:
                info.error = err.decode(errors="replace").strip() or f"git --version failed (exit {proc.returncode})"
                if "license" in info.error.lower() and "xcode" in info.error.lower():
                    info.repair_action = "Review and accept the Xcode licence in Terminal with sudo xcodebuild -license, then re-check"
                else:
                    info.repair_action = "Resolve the Git probe error, then re-check"
        except (TimeoutError, FileNotFoundError, OSError) as exc:
            log.debug("Git check failed: %s", exc)
        return info
