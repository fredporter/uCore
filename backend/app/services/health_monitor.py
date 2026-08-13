"""Health Monitor & Self-Healing System

Monitors backend health, logs issues, and attempts auto-recovery.
- Real-time health checks (component readiness)
- Automatic restart detection and recovery
- Log aggregation and analysis
- Console output capturing
- Self-healing skills (retry, reset, recover)

Usage:
    from app.services.health_monitor import HealthMonitor
    monitor = HealthMonitor()
    await monitor.start()
"""

import asyncio
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("health_monitor")

# ─── Data Models ──────────────────────────────────────────────────


@dataclass
class HealthEvent:
    """Single health check event"""
    timestamp: str
    component: str  # "backend", "frontend", "ollama", "database", etc.
    status: str  # "ok", "degraded", "error", "recovering"
    message: str
    severity: str  # "info", "warning", "error", "critical"
    recovery_action: Optional[str] = None
    result: Optional[str] = None


@dataclass
class ComponentHealth:
    """Component health status"""
    name: str
    status: str  # "ok", "degraded", "error"
    last_check: str
    last_error: Optional[str] = None
    check_count: int = 0
    error_count: int = 0
    recovery_attempts: int = 0


# ─── Health Monitor ───────────────────────────────────────────────


class HealthMonitor:
    """Monitor and heal backend services"""

    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.events: List[HealthEvent] = []
        self.max_events = 500  # Keep last 500 events
        self.log_dir = Path("~/.ucore/logs").expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        self.check_interval = 5.0  # seconds

    async def start(self):
        """Start the health monitor as a background task."""
        log.info("Health monitor starting...")
        self.running = True
        self._task = asyncio.create_task(self._run_checks())
        log.info("Health monitor background task created")

    async def stop(self):
        """Stop the health monitor."""
        log.info("Health monitor stopping...")
        self.running = False
        if hasattr(self, '_task') and self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            log.info("Health monitor stopped")

    async def _run_checks(self):
        """Run health checks in loop"""
        while self.running:
            try:
                await self._check_all_components()
            except Exception as e:
                log.error(f"Error in health check loop: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_all_components(self):
        """Check all backend components"""
        checks = [
            ("backend", self._check_backend),
            ("database", self._check_database),
            ("imports", self._check_imports),
            ("popcorn", self._check_popcorn),
        ]

        for name, check_fn in checks:
            try:
                # Run blocking checks in thread pool to avoid blocking event loop
                status, message = await asyncio.to_thread(check_fn)
                await self._record_check(name, status, message)
            except Exception as e:
                await self._record_check(name, "error", str(e))

    def _check_backend(self) -> tuple[str, str]:
        """Check if backend is responsive (runs in thread pool)."""
        try:
            from app.core.settings import settings
            port = settings.port
            import urllib.request
            response = urllib.request.urlopen(
                f"http://localhost:{port}/api/health", timeout=2
            )
            if response.status == 200:
                return "ok", f"Backend responding normally on port {port}"
            else:
                return "degraded", f"Backend returned status {response.status}"
        except urllib.error.URLError as e:
            return "error", f"Backend not responding: {e}"
        except Exception as e:
            return "error", f"Backend check failed: {e}"

    def _check_database(self) -> tuple[str, str]:
        """Check database connectivity (runs in thread pool)."""
        try:
            indices_dir = Path("~/.ucore/indices").expanduser()
            db_files = (
                list(indices_dir.glob("*.db")) if indices_dir.exists() else []
            )
            if not db_files:
                return "error", "No database files in ~/.ucore/indices"

            if os.access(db_files[0], os.R_OK):
                return "ok", f"Database accessible ({len(db_files)} db file(s))"
            else:
                return "error", "Database not readable"
        except Exception as e:
            return "error", f"Database check failed: {e}"

    def _check_imports(self) -> tuple[str, str]:
        """Check critical imports (runs in thread pool)."""
        imports = [
            ("aiohttp", "aiohttp"),
            ("PyObjC", "objc"),
            ("PyYAML", "yaml"),
        ]

        failed = []
        for name, module in imports:
            try:
                __import__(module)
            except ImportError:
                failed.append(name)

        if failed:
            return "error", f"Missing imports: {', '.join(failed)}"
        else:
            return "ok", "All critical imports available"

    def _check_popcorn(self) -> tuple[str, str]:
        """Check Popcorn status (runs in thread pool, macOS only)."""
        import platform
        if platform.system() != "Darwin":
            return "ok", "Popcorn not applicable (not macOS)"

        try:
            from app.services.popcorn_manager import get_popcorn_status
            status = get_popcorn_status()

            menu = status.get("menu", {})
            if menu.get("installed"):
                if menu.get("running"):
                    return "ok", "Popcorn (menu) running"
                else:
                    return "degraded", "Popcorn installed but menu not running"
            else:
                return "degraded", "Popcorn not installed"
        except Exception as e:
            return "error", f"Popcorn check failed: {e}"

    async def _record_check(self, component: str, status: str, message: str):
        """Record a health check result"""
        # Initialize component if needed
        if component not in self.components:
            self.components[component] = ComponentHealth(
                name=component,
                status="unknown",
                last_check=datetime.now(timezone.utc).isoformat(),
            )

        comp = self.components[component]
        comp.status = status
        comp.last_check = datetime.now(timezone.utc).isoformat()
        comp.check_count += 1

        # Determine severity
        severity = {
            "ok": "info",
            "degraded": "warning",
            "error": "error",
        }.get(status, "info")

        # Try recovery on error
        recovery_action = None
        recovery_result = None
        if status == "error":
            comp.error_count += 1
            comp.last_error = message
            recovery_action, recovery_result = await self._attempt_recovery(component)

        # Record event
        event = HealthEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            component=component,
            status=status,
            message=message,
            severity=severity,
            recovery_action=recovery_action,
            result=recovery_result,
        )

        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        # Log it
        if severity == "error":
            log.error(f"{component}: {message}")
        elif severity == "warning":
            log.warning(f"{component}: {message}")
        else:
            log.debug(f"{component}: {message}")

    async def _attempt_recovery(self, component: str) -> tuple[Optional[str], Optional[str]]:
        """Attempt to recover a failed component"""
        recovery_skills = {
            "backend": self._recover_backend,
            "database": self._recover_database,
            "imports": None,  # Can't recover import issues
            "popcorn": self._recover_popcorn,
        }

        recover_fn = recovery_skills.get(component)
        if recover_fn is None:
            return None, None

        try:
            comp = self.components[component]
            comp.recovery_attempts += 1

            result = await recover_fn()
            return f"recover_{component}", result
        except Exception as e:
            log.error(f"Recovery failed for {component}: {e}")
            return f"recover_{component}_failed", str(e)

    async def _recover_backend(self) -> str:
        """Attempt to recover backend via control recover endpoint."""
        log.info("Attempting backend recovery via /api/control/recover...")
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://127.0.0.1:8484/api/control/recover",
                method="POST",
                data=b'{"lane":"ecosystem"}',
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status < 400:
                    return "backend_recovery_triggered_via_control"
                return f"backend_recovery_failed_status_{resp.status}"
        except urllib.error.URLError:
            # Backend is completely down — try restart via launchd
            log.info("Backend unreachable; attempting launchd kickstart...")
            import subprocess
            try:
                subprocess.run(
                    ["launchctl", "kickstart", "gui/$(id -u)/com.udos.ucore-server"],
                    capture_output=True, timeout=5,
                )
                return "backend_launchd_kickstart_attempted"
            except Exception as e:
                return f"backend_launchd_kickstart_failed: {e}"
        except Exception as e:
            return f"backend_recovery_error: {e}"

    async def _recover_database(self) -> str:
        """Attempt to recover database connectivity."""
        log.info("Attempting database recovery...")
        try:
            db_path = Path("~/.ucore/ucore.db").expanduser()
            if not db_path.exists():
                # Try to recreate from migration
                try:
                    from app.core.database import migrate_db
                    result = migrate_db()
                    return f"database_recreated_v{result.get('version', '?')}"
                except Exception as e:
                    return f"database_recreate_failed: {e}"
            # Check and repair file permissions
            if not os.access(db_path, os.R_OK | os.W_OK):
                try:
                    os.chmod(db_path, 0o644)
                    return "database_permissions_fixed"
                except Exception as e:
                    return f"database_permission_fix_failed: {e}"
            return "database_accessible_no_action_needed"
        except Exception as e:
            return f"database_recovery_error: {e}"

    async def _recover_popcorn(self) -> str:
        """Attempt to recover Popcorn via perform_action restart-menu."""
        log.info("Attempting Popcorn recovery...")
        try:
            from app.services.popcorn_manager import perform_action
            result = perform_action("restart-menu")
            if result.get("success"):
                return "popcorn_restarted_via_menu"
            return f"popcorn_restart_returned: {result.get('message', 'unknown')}"
        except Exception as e:
            return f"popcorn_recovery_error: {e}"

    def get_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                name: asdict(comp) for name, comp in self.components.items()
            },
            "events_count": len(self.events),
            "last_events": [asdict(e) for e in self.events[-10:]],  # Last 10
        }

    def get_logs(self, lines: int = 100) -> List[str]:
        """Get recent log lines"""
        try:
            log_file = self.log_dir / "ucore-monitor.log"
            if log_file.exists():
                with open(log_file) as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:]
            return []
        except Exception as e:
            log.error(f"Failed to read logs: {e}")
            return []

    def get_console_output(self) -> Dict[str, Any]:
        """Get captured console output"""
        return {
            "stdout_log": str(self.log_dir / "ucore-stdout.log"),
            "stderr_log": str(self.log_dir / "ucore-stderr.log"),
        }


# ─── Global Instance ──────────────────────────────────────────────

_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get or create global health monitor"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


def set_health_monitor(monitor: Optional[HealthMonitor]) -> None:
    """Set global health monitor"""
    global _health_monitor
    _health_monitor = monitor
