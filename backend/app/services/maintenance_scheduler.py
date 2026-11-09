from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from app.core.logging import log
from app.core.settings import settings
from app.skills.registry import run_skill_by_id


@dataclass(frozen=True)
class MaintenanceJob:
    skill_id: str
    time_hhmm: str
    params: dict
    retry_safe: bool = False
    timeout_seconds: float = 300


DEFAULT_JOBS = (
    MaintenanceJob("backup", "03:00", {"type": "full"}),
    MaintenanceJob("vault_sync", "04:00", {"summary_only": True}),
    MaintenanceJob(
        "tasker_sync",
        "04:05",
        {
            "db": "database",
            "board": "inbox",
        },
    ),
    MaintenanceJob("docs_mirror_sync", "04:10", {}, retry_safe=True),
    MaintenanceJob(
        "brain_sync",
        "04:15",
        {
            "hours": 24,
            "limit": 20,
            "include_spool": True,
            "include_vault_activity": True,
        },
    ),
    MaintenanceJob(
        "clipboard_maintenance",
        "04:30",
        {"capture_current": True},
    ),
    MaintenanceJob(
        "spool_prune",
        "04:35",
        {"max_age_days": 14, "archive_completed_tasks": True},
    ),
)


_scheduler: MaintenanceScheduler | None = None


def get_maintenance_scheduler() -> MaintenanceScheduler | None:
    return _scheduler


def set_maintenance_scheduler(
    scheduler: MaintenanceScheduler | None,
) -> None:
    global _scheduler
    _scheduler = scheduler


class MaintenanceScheduler:
    def __init__(
        self,
        *,
        state_path: Path | None = None,
        jobs: tuple[MaintenanceJob, ...] = DEFAULT_JOBS,
        interval_seconds: int = 60,
    ) -> None:
        self.state_path = state_path or (settings.data_dir / "maintenance_state.json")
        self.jobs = jobs
        self.interval_seconds = max(15, int(interval_seconds))
        self._state = self._load_state()
        self._task: asyncio.Task | None = None
        self._run_lock = asyncio.Lock()

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {"last_run": {}, "last_result": {}, "started_at": None}
        try:
            import json

            with self.state_path.open("r", encoding="utf-8") as f:
                state = json.load(f)
                if not isinstance(state, dict):
                    raise ValueError("Invalid maintenance state")
                for key in ("last_run", "last_result", "last_success", "attempts"):
                    if not isinstance(state.get(key, {}), dict):
                        state[key] = {}
                return state
        except Exception:
            return {"last_run": {}, "last_result": {}, "started_at": None}

    def _save_state(self) -> None:
        import json

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_path)

    def status(self) -> dict:
        return {
            "status": "running" if self._task and not self._task.done() else "stopped",
            "jobs": [
                {
                    "skill_id": job.skill_id,
                    "time": job.time_hhmm,
                    "params": job.params,
                    "last_success": self._state.get("last_success", {}).get(job.skill_id),
                    "attempt": self._state.get("attempts", {}).get(job.skill_id, {}),
                    "last_run": self._state.get("last_run", {}).get(
                        job.skill_id,
                    ),
                    "last_result": self._state.get("last_result", {}).get(
                        job.skill_id,
                    ),
                }
                for job in self.jobs
            ],
            "started_at": self._state.get("started_at"),
            "interval_seconds": self.interval_seconds,
        }

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._state["started_at"] = datetime.now().isoformat()
        self._save_state()
        self._task = asyncio.create_task(self.run_forever())
        log.info("Maintenance scheduler started with %d jobs", len(self.jobs))

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        log.info("Maintenance scheduler stopped")

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_due()
                from app.services.connections.engine import sync_due_connections
                await sync_due_connections()
            except Exception as exc:
                log.warning("Maintenance scheduler cycle failed: %s", exc)
            await asyncio.sleep(self.interval_seconds)

    async def run_due(self, now: datetime | None = None) -> list[dict]:
        # Manual recovery and the timer share one execution lane.
        async with self._run_lock:
            return await self._run_due(now or datetime.now())

    async def _run_due(self, now: datetime) -> list[dict]:
        ran: list[dict] = []
        for job in self.jobs:
            if not self._is_due(job, now):
                continue
            attempt = self._state.setdefault("attempts", {}).get(job.skill_id, {})
            count = attempt.get("count", 0) if attempt.get("date") == now.date().isoformat() else 0
            # Persist the attempt before execution so restart cannot loop forever.
            self._state["attempts"][job.skill_id] = {
                "date": now.date().isoformat(),
                "count": count + 1,
                "next_retry": (now + timedelta(minutes=2**count)).isoformat(),
            }
            self._save_state()
            try:
                result = await asyncio.wait_for(
                    run_skill_by_id(job.skill_id, **job.params),
                    timeout=job.timeout_seconds,
                )
            except Exception as exc:
                result = {"success": False, "error": str(exc) or type(exc).__name__}
            success = bool(result.get("success"))
            needs_approval = bool(result.get("requires_confirmation"))
            retry = job.retry_safe and not success and not needs_approval and count + 1 < 3
            if success or not retry:
                self._state.setdefault("last_run", {})[job.skill_id] = now.date().isoformat()
            if success:
                self._state.setdefault("last_success", {})[job.skill_id] = now.isoformat()
            self._state.setdefault("last_result", {})[job.skill_id] = {
                "success": success,
                "timestamp": now.isoformat(),
                "state": "completed"
                if success
                else "needs_approval"
                if needs_approval
                else "retrying"
                if retry
                else "failed",
                "error": result.get("error"),
                "next_retry": self._state["attempts"][job.skill_id]["next_retry"]
                if retry
                else None,
            }
            self._save_state()
            ran.append({"skill_id": job.skill_id, "result": result})
            log.info("Maintenance job ran: %s success=%s", job.skill_id, success)
        return ran

    def _is_due(self, job: MaintenanceJob, now: datetime) -> bool:
        last_run = self._state.get("last_run", {}).get(job.skill_id)
        if last_run == now.date().isoformat():
            return False
        attempt = self._state.get("attempts", {}).get(job.skill_id, {})
        if attempt.get("date") == now.date().isoformat():
            if attempt.get("count", 0) >= 3:
                return False
            retry_at = attempt.get("next_retry")
            if retry_at and now < datetime.fromisoformat(retry_at):
                return False
        hour_str, minute_str = job.time_hhmm.split(":", 1)
        due_hour = int(hour_str)
        due_minute = int(minute_str)
        return (now.hour, now.minute) >= (due_hour, due_minute)
