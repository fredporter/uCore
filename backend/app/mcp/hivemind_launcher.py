"""Shared Hivemind launcher — single source of truth for starting Hivemind.

Used by both ``__main__.py`` (startup) and ``control_service.py`` (recovery).
"""
from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from app.core.logging import log


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _health_is_ready(host: str, port: int) -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(
            f"http://{host}:{port}/health",
            timeout=1.0,
        ) as response:
            return response.status == 200
    except Exception:
        return False


def start_hivemind() -> None:
    """Launch Hivemind MCP server as a background child process.

    Hivemind hosts the governed agent and consensus service. Provider and
    budget selection remain behind the canonical Flow Router rather than
    separate executable Skill wrappers.

    If Hivemind is already running and healthy, attaches silently.
    If the port is occupied but unhealthy, skips auto-start.
    Spawned as a child process with atexit cleanup.
    """
    backend_root = Path(__file__).resolve().parents[2]
    agents_config = backend_root / "config" / "agents.yaml"
    llm_config = backend_root / "config" / "llm_router.yaml"
    host = os.environ.get("UCORE_HIVEMIND_HOST", "127.0.0.1")
    port = int(os.environ.get("UCORE_HIVEMIND_PORT", "8490"))

    if _port_in_use(host, port):
        if _health_is_ready(host, port):
            log.info(
                "Hivemind already running on %s:%d; attaching",
                host,
                port,
            )
            return
        log.warning(
            "Hivemind port %s:%d is occupied but unhealthy; "
            "skipping auto-start",
            host,
            port,
        )
        return

    try:
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "app.mcp.hivemind_server",
                "--host", host,
                "--port", str(port),
                "--agents-config", str(agents_config),
                "--llm-config", str(llm_config),
            ],
            cwd=str(backend_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Verify child process actually booted and reached health endpoint.
        for _ in range(30):
            if proc.poll() is not None:
                log.warning(
                    "Hivemind exited during startup (code %s); "
                    "skills depending on it will be unavailable",
                    proc.returncode,
                )
                return
            if _health_is_ready(host, port):
                atexit.register(proc.terminate)
                log.info(
                    "Hivemind auto-started (PID %d) on %s:%d",
                    proc.pid,
                    host,
                    port,
                )
                return
            time.sleep(0.1)

        atexit.register(proc.terminate)
        log.warning(
            "Hivemind process launched (PID %d) "
            "but health did not report ready yet",
            proc.pid,
        )
    except Exception as exc:
        log.error("Failed to start Hivemind: %s", exc)
