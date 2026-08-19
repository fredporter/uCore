"""Autonomy Engine — scheduled background tasks for uCore ecosystem.

Runs every 24 hours (or on demand) to:
- Execute ecosystem-audit
- Check health thresholds
- Log results to ``$UDOS_HOME/logs``
- Alert if health drops below 95%

Usage as cron job:
  */30 * * * * cd ~/Code/uCore && backend/.venv/bin/python -m health.autonomy_engine

Usage as one-shot:
  python -m health.autonomy_engine --once
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.settings import settings

LOG_DIR = settings.logs_dir
LOG_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG = LOG_DIR / "autonomy.log"
STATE_FILE = LOG_DIR / "autonomy_state.json"
HEALTH_THRESHOLD = 95.0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [autonomy] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(AUDIT_LOG),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("autonomy")


def _call_api(
    path: str, method: str = "GET", body: dict | None = None, timeout: int = 120
) -> dict | None:
    """Call the uCore backend API."""
    import urllib.request

    url = f"http://127.0.0.1:8484{path}"
    try:
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"} if data else {},
            method=method,
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning(f"API call failed: {path} — {e}")
        return None


def run_ecosystem_audit() -> dict[str, Any]:
    """Run the ecosystem-audit skill and return parsed results."""
    log.info("Starting ecosystem audit...")
    start = time.time()

    result = _call_api(
        "/api/skills/ecosystem-audit/run",
        method="POST",
        body={"action": "assess"},
        timeout=120,
    )

    elapsed = time.time() - start

    if result is None:
        return {
            "success": False,
            "error": "API call failed",
            "duration_seconds": round(elapsed, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    health = result.get("health", {})
    return {
        "success": result.get("success", False),
        "health_pct": health.get("health_pct", 0),
        "working": health.get("working", 0),
        "untested": health.get("untested", 0),
        "broken": health.get("broken", 0),
        "orphaned": health.get("orphaned", 0),
        "total_items": health.get("total_items", 0),
        "duration_seconds": round(elapsed, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def check_ollama() -> dict[str, Any]:
    """Check Ollama status."""
    result = _call_api("/api/ollama/status", timeout=10)
    if result is None:
        return {"online": False, "error": "unreachable"}
    return {
        "online": result.get("online", False),
        "model_count": result.get("model_count", 0),
    }


def save_state(state: dict[str, Any]) -> None:
    """Persist autonomy state for frontend consumption."""
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    except Exception as e:
        log.warning(f"Failed to save state: {e}")


def load_state() -> dict[str, Any]:
    """Load last known autonomy state."""
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception:
        pass
    return {}


def run_full_check() -> dict[str, Any]:
    """Run all health checks and return combined state."""
    log.info("=== Autonomy Engine: Full Health Check ===")

    audit = run_ecosystem_audit()
    ollama = check_ollama()

    health_pct = audit.get("health_pct", 0)

    if audit.get("success"):
        if health_pct >= HEALTH_THRESHOLD:
            log.info(f"Health OK: {health_pct}% (threshold: {HEALTH_THRESHOLD}%)")
        else:
            log.warning(
                f"Health BELOW threshold: {health_pct}% < {HEALTH_THRESHOLD}% "
                f"({audit.get('broken', 0)} broken, {audit.get('untested', 0)} untested)"
            )
    else:
        log.error(f"Audit failed: {audit.get('error', 'unknown')}")

    if not ollama.get("online"):
        log.warning("Ollama is offline")

    state = {
        "last_audit": audit,
        "ollama": ollama,
        "health_pct": health_pct,
        "healthy": health_pct >= HEALTH_THRESHOLD,
        "threshold": HEALTH_THRESHOLD,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    save_state(state)
    log.info(
        f"State saved. Health: {health_pct}% | Ollama: {'online' if ollama.get('online') else 'offline'}"
    )
    return state


def main() -> None:
    """Entry point — run full check and exit."""
    state = run_full_check()
    if not state.get("healthy"):
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="uCore Autonomy Engine")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument(
        "--interval", type=int, default=86400, help="Seconds between checks (default: 24h)"
    )
    args = parser.parse_args()

    if args.once:
        state = run_full_check()
        print(json.dumps(state, indent=2, default=str))
    else:
        log.info(f"Starting autonomy loop (interval: {args.interval}s)")
        while True:
            try:
                run_full_check()
            except Exception as e:
                log.error(f"Check failed: {e}")
            time.sleep(args.interval)
