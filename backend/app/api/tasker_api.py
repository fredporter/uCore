"""Tasker API — expose .tasker markdown boards as structured data.

Provides:
- GET /api/developer/tasker/boards — list all boards with task counts
- GET /api/developer/tasker/board/{board_name} — list all tasks in a board
- GET /api/developer/tasker/tasks — all tasks across boards (for Kanban)
- GET /api/developer/tasker/summary — aggregate stats by status
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aiohttp import web

from app.services.tasker_bridge import (
    normalize_priority,
    normalize_status,
    normalize_tags,
    render_task_markdown,
    slugify,
)
from app.services.workflow_status import default_tasker_dir, scan_tasker_boards

log = logging.getLogger("ucore.api.tasker")

USER_EXCLUDED_BOARDS = {
    "active",
    "archive",
    "backlog",
    "dev",
    "developer",
    "engineering",
    "feature",
    "repo",
    "review",
    "sprints",
}

USER_SOURCE_HINTS = (
    "seed-user-workflow",
    "user",
    "vault",
)


def _is_user_workflow_task(task: dict[str, Any]) -> bool:
    """Keep user-workflow tasks and hide obvious dev planning lanes."""
    board = str(task.get("board") or "").strip().lower()
    source = str(task.get("source") or "").strip().lower()
    tags = [str(t).strip().lower() for t in task.get("tags") or []]

    has_user_metadata = bool(
        str(task.get("mission") or "").strip()
        or str(task.get("binder") or "").strip()
        or str(task.get("task") or "").strip(),
    )
    source_signals_user = any(hint in source for hint in USER_SOURCE_HINTS)
    tag_signals_user = any(tag in {"user", "personal", "seed"} for tag in tags)

    if has_user_metadata or source_signals_user or tag_signals_user:
        return True

    if board in USER_EXCLUDED_BOARDS:
        return False

    return True


def _parse_markdown_task(path: Path) -> dict[str, Any]:
    """Parse a single .tasker markdown file into a structured dict.

    Supports both Obsidian-style YAML frontmatter (Properties) and the legacy
    `- key: value` metadata lines, so tasker notes work in Obsidian and in uCore.
    Frontmatter takes precedence over legacy metadata lines.
    """
    content = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body_content = _parse_frontmatter(content)
    lines = body_content.splitlines()

    task: dict[str, Any] = {
        "id": path.stem,
        "title": "",
        "description": "",
        "status": "todo",
        "priority": "medium",
        "board": path.parent.name,
        "source": "manual",
        "source_id": "",
        "tags": [],
        "file": str(path),
        "body": "",
    }

    in_summary = False
    summary_parts: list[str] = []
    body_parts: list[str] = []

    def _set_meta(key: str, value: str) -> None:
        cleaned = value.strip()
        if not cleaned:
            return

        canonical = _META_ALIASES.get(key, key)

        if canonical == "status":
            task["status"] = normalize_status(cleaned)
        elif canonical == "priority":
            task["priority"] = normalize_priority(cleaned)
        elif canonical == "tags":
            task["tags"] = normalize_tags(cleaned)
        elif canonical in {"mission", "task", "binder"}:
            task[canonical] = cleaned
        else:
            task[canonical] = cleaned

    # ── Legacy `- key: value` metadata lines + body ──────────────
    for line in lines:
        if line.startswith("# ") and not task["title"]:
            task["title"] = line[2:].strip()
        elif line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            _set_meta(key.strip().lower(), value)
            if key.strip().lower() == "source":
                src = value.strip()
                if src and src not in task["tags"]:
                    task["tags"].append(src)
        elif line == "## Summary":
            in_summary = True
        elif in_summary and line.startswith("- "):
            summary_parts.append(line[2:].strip())
        elif in_summary and line.startswith("## "):
            in_summary = False
        elif (
            not line.startswith("#")
            and not line.startswith("-")
            and line.strip()
        ):
            body_parts.append(line.strip())

    # ── Obsidian frontmatter (Properties) — takes precedence ─────
    for key, value in frontmatter.items():
        canonical = _META_ALIASES.get(str(key).strip().lower(), str(key).strip().lower())
        if canonical == "tags":
            task["tags"] = normalize_tags(value)
        elif canonical == "status":
            task["status"] = normalize_status(str(value))
        elif canonical == "priority":
            task["priority"] = normalize_priority(str(value))
        elif canonical in {"mission", "task", "binder", "board"}:
            task[canonical] = str(value).strip()
        elif value is not None:
            task[canonical] = value

    task["description"] = (
        "\n".join(summary_parts)
        if summary_parts
        else "\n".join(body_parts)
    )
    task["body"] = "\n".join(body_parts) if body_parts else task["description"]

    # Derive status from filename prefix (fallback only)
    name_lower = path.stem.lower()
    if not task["status"] or task["status"] == "unknown":
        if name_lower.startswith("done-"):
            task["status"] = "completed"
        elif name_lower.startswith("in-progress-"):
            task["status"] = "in-progress"
        elif name_lower.startswith("todo-"):
            task["status"] = "todo"
        elif name_lower.startswith("wip-"):
            task["status"] = "in-progress"
        elif name_lower.startswith("blocked-"):
            task["status"] = "blocked"

    task["status"] = normalize_status(str(task.get("status") or "todo"))
    task["priority"] = normalize_priority(
        str(task.get("priority") or "medium"),
    )
    task["tags"] = normalize_tags(task.get("tags") or [])

    return task


_META_ALIASES: dict[str, str] = {
    "state": "status",
    "task_status": "status",
    "prio": "priority",
    "urgency": "priority",
    "project": "mission",
    "objective": "mission",
    "work_item": "task",
    "todo": "task",
    "notebook": "binder",
    "collection": "binder",
    "label": "tags",
    "labels": "tags",
    "tag": "tags",
}


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse an Obsidian-style YAML frontmatter block.

    Returns (meta_dict, remaining_content). If the file has no leading `---`
    block, returns ({}, original_content).
    """
    if not content.startswith("---"):
        return {}, content
    lines = content.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, content
    fm_block = "\n".join(lines[1:end])
    rest = "\n".join(lines[end + 1:])
    try:
        import yaml
        data = yaml.safe_load(fm_block) or {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    return data, rest


async def handle_list_boards(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/boards — list all tasker boards."""
    tasker = scan_tasker_boards()
    return web.json_response(tasker)


async def handle_list_board_tasks(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/board/{board_name}.

    List all tasks in a single board.
    """
    board_name = request.match_info.get("board_name", "")
    if not board_name:
        return web.json_response({"error": "board_name required"}, status=400)

    base = default_tasker_dir()
    board_path = base / board_name
    if not board_path.exists() or not board_path.is_dir():
        return web.json_response(
            {"error": f"Board '{board_name}' not found"},
            status=404,
        )

    tasks: list[dict[str, Any]] = []
    for md_file in sorted(board_path.glob("*.md")):
        tasks.append(_parse_markdown_task(md_file))

    return web.json_response({
        "board": board_name,
        "path": str(board_path),
        "count": len(tasks),
        "tasks": tasks,
    })


async def handle_all_tasks(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/tasks.

    Return all tasks across all boards for kanban views.
    """
    base = default_tasker_dir()
    tasks: list[dict[str, Any]] = []

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            for md_file in sorted(board_dir.glob("*.md")):
                if md_file.name == "README.md":
                    continue
                tasks.append(_parse_markdown_task(md_file))

    return web.json_response({
        "tasker_dir": str(base),
        "count": len(tasks),
        "tasks": tasks,
    })


async def handle_workflow_tasks(request: web.Request) -> web.Response:
    """GET /api/workflow/tasks.

    Return tasks filtered by board/tag for the workflow surface.

        Query params:
      - board: filter by board name (substring match)
      - tag: filter by tag (exact match)
      - scope: user|all (default: user)
    """
    base = default_tasker_dir()
    board_filter = request.query.get("board", "").lower()
    tag_filter = request.query.get("tag", "").lower()
    scope = request.query.get("scope", "user").strip().lower() or "user"
    tasks: list[dict[str, Any]] = []

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            if board_filter and board_filter not in board_dir.name.lower():
                continue
            for md_file in sorted(board_dir.glob("*.md")):
                if md_file.name == "README.md":
                    continue
                task = _parse_markdown_task(md_file)
                tags = [t.lower() for t in task.get("tags", [])]
                if tag_filter and tag_filter not in tags:
                    continue
                if scope == "user" and not _is_user_workflow_task(task):
                    continue
                tasks.append(task)

    return web.json_response({
        "tasker_dir": str(base),
        "count": len(tasks),
        "scope": scope,
        "board_filter": board_filter or None,
        "tag_filter": tag_filter or None,
        "tasks": tasks,
    })


async def handle_tasker_summary(request: web.Request) -> web.Response:
    """GET /api/developer/tasker/summary — aggregate stats by status."""
    base = default_tasker_dir()
    status_counts: dict[str, int] = {}
    board_counts: dict[str, int] = {}
    total = 0

    if base.exists():
        for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            count = 0
            for md_file in board_dir.glob("*.md"):
                if md_file.name == "README.md":
                    continue
                task = _parse_markdown_task(md_file)
                status = task.get("status", "todo") or "todo"
                status_counts[status] = status_counts.get(status, 0) + 1
                total += 1
                count += 1
            if count > 0:
                board_counts[board_dir.name] = count

    return web.json_response({
        "tasker_dir": str(base),
        "total": total,
        "by_status": status_counts,
        "by_board": board_counts,
        "status_keys": sorted(status_counts.keys()),
        "board_keys": sorted(board_counts.keys()),
    })


def _find_task_file(base: Path, task_id: str) -> Path | None:
    for board_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        candidate = board_dir / f"{task_id}.md"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _build_task_filename(
    status: str,
    title: str,
    source_id: str,
    task_id: str,
) -> str:
    safe_source = slugify(source_id or task_id)
    return f"{normalize_status(status)}-{slugify(title)}-{safe_source}.md"


def _task_metadata_from_record(task: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "priority": task.get("priority") or "medium",
        "mission": task.get("mission") or "",
        "task": task.get("task") or "",
        "binder": task.get("binder") or "",
        "tags": task.get("tags") or [],
    }
    return metadata


def _update_task_file(
    *,
    base: Path,
    task_id: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    source_path = _find_task_file(base, task_id)
    if not source_path:
        raise FileNotFoundError(task_id)

    current = _parse_markdown_task(source_path)

    new_status = normalize_status(
        str(patch.get("status") or current.get("status") or "todo"),
    )
    new_priority = normalize_priority(
        str(patch.get("priority") or current.get("priority") or "medium"),
    )
    new_board = str(
        patch.get("board") or current.get("board") or source_path.parent.name,
    ).strip() or source_path.parent.name
    new_title = (
        str(patch.get("title") or current.get("title") or "Untitled").strip()
        or "Untitled"
    )
    new_tags = normalize_tags(
        patch.get("tags") if "tags" in patch else current.get("tags") or [],
    )
    new_body = str(
        patch.get("body")
        or current.get("body")
        or current.get("description")
        or "",
    ).strip()
    source = str(current.get("source") or "manual")
    source_id = str(current.get("source_id") or task_id)

    metadata = _task_metadata_from_record(current)
    metadata["priority"] = new_priority
    metadata["tags"] = new_tags

    target_dir = base / new_board
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = _build_task_filename(new_status, new_title, source_id, task_id)
    target_path = target_dir / filename

    content = render_task_markdown(
        title=new_title,
        source=source,
        source_id=source_id,
        status=new_status,
        body=new_body,
        metadata=metadata,
    )
    target_path.write_text(content, encoding="utf-8")

    if source_path.resolve() != target_path.resolve() and source_path.exists():
        source_path.unlink(missing_ok=True)

    updated = _parse_markdown_task(target_path)
    return {
        "updated": updated,
        "path": str(target_path),
        "source_path": str(source_path),
    }


async def handle_update_task(request: web.Request) -> web.Response:
    """PATCH /api/developer/tasker/tasks/{task_id}.

    Update Tasker-backed markdown task state for kanban/list transitions.
    """
    task_id = request.match_info.get("task_id", "").strip()
    if not task_id:
        return web.json_response({"error": "task_id required"}, status=400)

    try:
        patch = await request.json() if request.body_exists else {}
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)

    if not isinstance(patch, dict):
        return web.json_response(
            {"error": "Invalid patch payload"},
            status=400,
        )

    base = default_tasker_dir()
    if not base.exists():
        return web.json_response(
            {"error": "Tasker directory not found"},
            status=404,
        )

    try:
        result = _update_task_file(base=base, task_id=task_id, patch=patch)
    except FileNotFoundError:
        return web.json_response(
            {"error": f"Task '{task_id}' not found"},
            status=404,
        )
    except Exception as exc:
        log.exception("Task update failed")
        return web.json_response(
            {"error": f"task_update_failed: {exc}"},
            status=500,
        )

    return web.json_response({
        "status": "ok",
        "task_id": task_id,
        **result,
    })


def register_tasker_routes(app: web.Application) -> None:
    """Register tasker API routes under /api/developer/tasker/."""
    app.router.add_get("/api/developer/tasker/boards", handle_list_boards)
    app.router.add_get(
        "/api/developer/tasker/board/{board_name}",
        handle_list_board_tasks,
    )
    app.router.add_get("/api/developer/tasker/tasks", handle_all_tasks)
    app.router.add_patch(
        "/api/developer/tasker/tasks/{task_id}",
        handle_update_task,
    )
    app.router.add_get("/api/developer/tasker/summary", handle_tasker_summary)
    app.router.add_patch("/api/workflow/tasks/{task_id}", handle_update_task)
