"""Gate B milestone 1 — admit matched transitions as Gate A runs.

Exactly-once properties come from two deterministic keys: the run ID derived
from binding + transition, and one unique receipt row per transition. A replay,
a concurrent dispatch or a restart all converge on the same run.
"""
from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from app.services.observation_intake import ObservationStore
from app.services.transition_bindings import Binding, match_binding

_lock = asyncio.Lock()


def run_id_for(binding_id: str, transition_id: str) -> str:
    return "run-" + hashlib.sha256(
        f"{binding_id}|{transition_id}".encode("utf-8")
    ).hexdigest()[:10]


async def dispatch_transitions(
    store: ObservationStore,
    manager,
    bindings: list[Binding],
    *,
    pipeline_version: str = "v1",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Admit pending transitions through reviewed bindings; never guess."""
    from app.flow.workflow_api import start_workflow_run

    results: list[dict[str, Any]] = []
    async with _lock:
        for transition in store.pending_transitions(limit):
            transition_id = transition["transition_id"]
            change = transition["change"]
            fields = set(change.get("changed", {})) | set(change.get("removed", []))
            binding, reason = match_binding(
                bindings,
                source_id=transition["source_id"],
                subject_id=transition["subject_id"],
                pipeline_version=pipeline_version,
                fields=fields,
            )

            if binding is None:
                store.mark_suppressed(transition_id, reason)
                store.record_receipt(
                    transition_id=transition_id,
                    binding_id="none",
                    workflow_id="",
                    status="suppressed",
                    reason=reason,
                )
                results.append(
                    {"transition_id": transition_id, "status": "suppressed", "reason": reason}
                )
                continue

            receipt, _created = store.record_receipt(
                transition_id=transition_id,
                binding_id=binding.binding_id,
                workflow_id=binding.workflow_id,
                status="admitting",
            )
            if receipt.get("run_id"):
                store.mark_delivered(transition_id, receipt["run_id"])
                results.append(
                    {
                        "transition_id": transition_id,
                        "status": "already-admitted",
                        "run_id": receipt["run_id"],
                    }
                )
                continue

            workflow = manager.get_workflow(binding.workflow_id, owner=binding.owner)
            if workflow is None:
                store.fail_receipt(receipt["receipt_id"], "workflow-not-found")
                results.append(
                    {
                        "transition_id": transition_id,
                        "status": "failed",
                        "reason": "workflow-not-found",
                    }
                )
                continue

            run_id = run_id_for(binding.binding_id, transition_id)
            try:
                await start_workflow_run(
                    manager,
                    workflow,
                    binding.workflow_id,
                    binding.owner,
                    run_id=run_id,
                )
            except Exception as exc:  # noqa: BLE001 - recorded on the receipt
                store.fail_receipt(receipt["receipt_id"], f"admission-error:{exc}")
                results.append(
                    {
                        "transition_id": transition_id,
                        "status": "failed",
                        "reason": str(exc),
                    }
                )
                continue

            store.complete_receipt(receipt["receipt_id"], run_id)
            store.mark_delivered(transition_id, run_id)
            results.append(
                {
                    "transition_id": transition_id,
                    "status": "admitted",
                    "binding_id": binding.binding_id,
                    "workflow_id": binding.workflow_id,
                    "run_id": run_id,
                }
            )
    return results
