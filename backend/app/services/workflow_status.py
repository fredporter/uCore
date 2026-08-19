"""uCore presentation of status from the uFlow-owned task store."""

from __future__ import annotations

from typing import Any

from uflow.task_store import default_tasker_dir, scan_tasker_boards


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
            "Add sync controls for task and vault sync.",
            "Route models through HiveMind and the budget manager.",
        ],
    }


__all__ = ["build_workflow_status", "default_tasker_dir", "scan_tasker_boards"]
