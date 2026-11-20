"""spool_writer — Write structured log entries to uCore spool.

Provides a simple interface for skills and snacks to write to the spool
for audit trails and activity tracking.

Spec: docs/SPOOL_SPEC.md
"""
from __future__ import annotations

from datetime import UTC, datetime

from app.core.settings import settings

LOG_DIR = settings.logs_dir


def write_spool(
    level: str = "INFO",
    module: str = "unknown",
    message: str = "",
    tags: list[str] | None = None,
) -> None:
    """Write a structured log entry to the spool.

    Args:
        level: Log level (INFO, WARNING, ERROR, DEBUG, CRITICAL)
        module: Module name for categorization
        message: Log message content
        tags: Optional list of tags for filtering
    """
    log_dir = LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
    tag_str = " ".join(f"[{t}]" for t in (tags or []))
    log_line = f"{timestamp} [{level}] {module}: {message} {tag_str}\n"

    for filename in dict.fromkeys(("spool.log", f"{module}.log")):
        with (log_dir / filename).open("a", encoding="utf-8") as log_file:
            log_file.write(log_line)


def write_spool_batch(
    entries: list[dict[str, str]],
) -> int:
    """Write multiple log entries at once.

    Args:
        entries: List of {level, module, message, tags} dicts

    Returns:
        Number of entries written
    """
    log_dir = LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")
    lines = []

    for entry in entries:
        level = entry.get("level", "INFO")
        module = entry.get("module", "unknown")
        message = entry.get("message", "")
        tags = entry.get("tags", [])
        tag_str = " ".join(f"[{t}]" for t in tags)
        lines.append(f"{timestamp} [{level}] {module}: {message} {tag_str}\n")

    if lines:
        with (log_dir / "spool.log").open("a", encoding="utf-8") as log_file:
            log_file.writelines(lines)

    return len(lines)
