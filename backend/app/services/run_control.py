"""Cooperative cancellation for workflow runs.

uCore serves the API and the scheduler from one process, so an in-memory flag is
exact. If uCore ever runs multiple workers, this must move into the run store.
"""
from __future__ import annotations

import threading

_lock = threading.Lock()
_cancelled: set[str] = set()


def request_cancel(run_id: str) -> None:
    with _lock:
        _cancelled.add(run_id)


def is_cancelled(run_id: str) -> bool:
    with _lock:
        return run_id in _cancelled


def clear(run_id: str) -> None:
    with _lock:
        _cancelled.discard(run_id)
