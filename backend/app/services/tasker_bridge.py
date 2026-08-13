from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

STATUS_ALIASES: dict[str, str] = {
    "todo": "todo",
    "to-do": "todo",
    "open": "todo",
    "pending": "todo",
    "in-progress": "in-progress",
    "inprogress": "in-progress",
    "wip": "in-progress",
    "review": "review",
    "blocked": "blocked",
    "done": "completed",
    "complete": "completed",
    "completed": "completed",
}

PRIORITY_ALIASES: dict[str, str] = {
    "high": "high",
    "h": "high",
    "urgent": "high",
    "medium": "medium",
    "med": "medium",
    "normal": "medium",
    "low": "low",
    "l": "low",
}


def normalize_status(value: str) -> str:
    key = str(value or "").strip().lower()
    if not key:
        return "todo"
    return STATUS_ALIASES.get(key, key)


def normalize_priority(value: str) -> str:
    raw = str(value or "").strip()
    key = raw.lower()
    if not key:
        return "medium"
    return PRIORITY_ALIASES.get(key, raw)


def normalize_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = [str(v).strip() for v in value if str(v).strip()]
    elif isinstance(value, str):
        raw = [part.strip() for part in value.split(",") if part.strip()]
    else:
        raw = []

    deduped: list[str] = []
    seen: set[str] = set()
    for item in raw:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(item)
    return deduped


def pick_alias(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        val = mapping.get(key)
        if val is None:
            continue
        text = str(val).strip()
        if text:
            return text
    return ""


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    cleaned = cleaned.strip("-")
    return cleaned or "task"


def render_task_markdown(
    *,
    title: str,
    source: str,
    source_id: str,
    status: str,
    body: str,
    metadata: dict[str, Any],
    created_at: str | None = None,
) -> str:
    """Render a task as Obsidian-compatible markdown.

    Format: YAML frontmatter (Properties) + `# Title` + `## Summary` body.
    Obsidian reads the frontmatter natively (properties panel) and scans the
    body for `- [ ]` task checkboxes, so tasker notes open/query in Obsidian.
    """
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    mission = pick_alias(metadata, "mission", "project", "objective")
    task_name = pick_alias(metadata, "task", "todo", "work_item")
    binder = pick_alias(metadata, "binder", "notebook", "collection")
    priority = normalize_priority(
        pick_alias(metadata, "priority", "prio", "urgency"),
    )
    tags = normalize_tags(
        metadata.get("tags") or metadata.get("labels") or metadata.get("tag"),
    )

    frontmatter: dict[str, Any] = {
        "id": metadata.get("id") or source_id or slugify(title),
        "board": metadata.get("board") or "",
        "status": normalize_status(status),
        "priority": priority,
        "source": source,
        "source_id": source_id,
        "created": created_at or metadata.get("created") or timestamp,
        "updated": timestamp,
    }
    if mission:
        frontmatter["mission"] = mission
    if task_name:
        frontmatter["task"] = task_name
    if binder:
        frontmatter["binder"] = binder
    if tags:
        frontmatter["tags"] = ", ".join(tags)
    if metadata.get("due"):
        frontmatter["due"] = metadata.get("due")

    extra_meta = {
        key: value
        for key, value in metadata.items()
        if key
        not in {
            "title",
            "name",
            "status",
            "source",
            "source_id",
            "synced_at",
            "priority",
            "mission",
            "task",
            "binder",
            "tags",
            "labels",
            "tag",
            "assignee",
            "due",
            "dueDate",
            "id",
            "uuid",
            "description",
            "notes",
            "board",
            "created",
            "created_at",
            "updated",
        }
    }
    if extra_meta:
        for key, value in extra_meta.items():
            if value not in (None, ""):
                frontmatter[key] = value

    # Drop empty optional fields for a clean properties panel
    frontmatter = {
        key: value for key, value in frontmatter.items() if value not in (None, "")
    }

    try:
        fm_text = yaml.safe_dump(
            frontmatter,
            sort_keys=False,
            allow_unicode=True,
        ).strip()
    except Exception:
        fm_text = "\n".join(
            f"{key}: {value}" for key, value in frontmatter.items()
        )

    lines = ["---", fm_text, "---", "", f"# {title}", ""]
    if body:
        lines.extend(["## Summary", body, ""])
    return "\n".join(lines)


def export_rows_to_tasker(
    rows: list[dict[str, Any]],
    *,
    tasker_dir: str,
    board: str = "inbox",
    title_field: str = "title",
    body_fields: list[str] | None = None,
    status_field: str = "status",
    id_field: str = "id",
    source: str = "appflowy",
    dry_run: bool = False,
) -> dict[str, Any]:
    body_fields = body_fields or ["description", "notes", "content"]
    out_dir = Path(tasker_dir).expanduser() / board
    exported: list[dict[str, Any]] = []

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    for index, row in enumerate(rows, start=1):
        title = str(
            row.get(title_field) or row.get("name") or f"Task {index}",
        ).strip()
        source_id = str(row.get(id_field) or row.get("uuid") or index)
        status = normalize_status(str(row.get(status_field) or "todo"))

        metadata = dict(row)
        metadata["priority"] = normalize_priority(
            pick_alias(row, "priority", "prio", "urgency"),
        )
        metadata["mission"] = pick_alias(
            row,
            "mission",
            "project",
            "objective",
        )
        metadata["task"] = pick_alias(row, "task", "todo", "work_item")
        metadata["binder"] = pick_alias(
            row,
            "binder",
            "notebook",
            "collection",
        )
        metadata["tags"] = normalize_tags(
            row.get("tags") or row.get("labels") or row.get("tag"),
        )

        body_parts: list[str] = []
        for field in body_fields:
            value = row.get(field)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                body_parts.append(f"{field}: {text}")
        body = "\n\n".join(body_parts)

        filename = f"{status}-{slugify(title)}-{slugify(source_id)}.md"
        path = out_dir / filename
        content = render_task_markdown(
            title=title,
            source=source,
            source_id=source_id,
            status=status,
            body=body,
            metadata=metadata,
        )
        if not dry_run:
            path.write_text(content, encoding="utf-8")
        exported.append(
            {
                "title": title,
                "status": status,
                "source_id": source_id,
                "file": str(path),
            },
        )

    return {
        "tasker_dir": str(Path(tasker_dir).expanduser()),
        "board": board,
        "count": len(exported),
        "exports": exported,
        "dry_run": dry_run,
    }
