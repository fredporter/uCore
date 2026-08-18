from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.core.settings import settings


def default_tasker_dir() -> Path:
    return Path(
        os.getenv(
            "UCORE_TASKER_DIR",
            str(settings.udos_root / "uCore/.tasker"),
        ),
    ).expanduser()


def scan_tasker_boards(tasker_dir: Path | None = None) -> dict[str, Any]:
    base = tasker_dir or default_tasker_dir()
    boards: list[dict[str, Any]] = []

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            files = sorted(board_dir.glob("*.md"))
            boards.append(
                {
                    "name": board_dir.name,
                    "path": str(board_dir),
                    "count": len(files),
                    "items": [f.name for f in files[:10]],
                },
            )

    return {
        "tasker_dir": str(base),
        "exists": base.exists(),
        "boards": boards,
        "count": len(boards),
        "total_items": sum(board["count"] for board in boards),
    }


def build_workflow_status(
    maintenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tasker = scan_tasker_boards()
    maintenance_jobs = []
    maintenance_state = "unknown"
    maintenance_tray: dict[str, Any] = {"status": "unknown"}
    if maintenance:
        maintenance_state = maintenance.get("status", "unknown")
        maintenance_tray = maintenance.get("tray") or maintenance_tray
        if maintenance_state == "ok":
            maintenance_jobs = maintenance.get("jobs", [])

    return {
        "engine": {
            "name": "uFlow Markdown Workflow Engine",
            "role": "Canonical user, developer, system, and autonomous workflow state",
            "storage": str(default_tasker_dir()),
            "access": "uCore API and vault-compatible Markdown",
            "isolation": "workflow type, workspace, mission, task, and step",
            "review_loop": "task evidence, artifact links, approval, and outcome",
            "automation": [
                "uFlow task transitions",
                "budget-gated execution",
                "reviewable developer changes",
            ],
        },
        "guardrails": [
            "uFlow is the sole durable task and workflow authority.",
            "Do not create repository-local or agent-owned task stores.",
            "Require explicit authorization for destructive or external actions.",
            "Record budget, evidence, artifacts, and outcome on durable tasks.",
        ],
        "task_markdown": tasker,
        "maintenance": {
            "status": maintenance_state,
            "jobs": maintenance_jobs,
            "tray": maintenance_tray,
            "endpoint": "/api/system/maintenance",
        },
        "next_actions": [
            "Expose uFlow board actions in the Workflow surface.",
            "Add sync controls for tasker_sync and vault_sync.",
            "Route agents through HiveMind and the budget manager.",
        ],
    }


# Compatibility exports: uFlow owns the durable task directory and board scan.
from uflow.task_store import (  # noqa: E402,F401
    default_tasker_dir as default_tasker_dir,
)
from uflow.task_store import (
    scan_tasker_boards as scan_tasker_boards,
)
