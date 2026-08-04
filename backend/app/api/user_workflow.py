"""User Workflow API — markdown-first status and optional AppFlowy health."""
from __future__ import annotations

import json
import logging
import sqlite3
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aiohttp import web
import yaml

from app.api.vault_api import VAULT_LAYERS
from app.core.settings import settings
from app.knowledge.appflowy import list_workspaces
from app.knowledge.local_first import discover_databases
from app.services.markdown_import_pipeline import convert_content_to_markdown
from app.services.tasker_bridge import (
    normalize_priority,
    normalize_status,
    normalize_tags,
    render_task_markdown,
    slugify,
)
from app.services.workflow_status import default_tasker_dir, scan_tasker_boards

log = logging.getLogger("ucore.api.user_workflow")

DEFAULT_USER_BINDER = "Sandbox"


def _discover_appflowy_databases_safe() -> tuple[dict[str, str], list[str]]:
    try:
        return discover_databases(), []
    except Exception as exc:
        log.warning("AppFlowy database discovery failed: %s", exc)
        return {}, [f"database_discovery_failed: {exc}"]


def _vault_status() -> dict[str, Any]:
    layers: list[dict[str, Any]] = []
    missing: list[str] = []

    for layer in VAULT_LAYERS:
        path = Path(layer["path"]).expanduser()
        exists = path.exists() and path.is_dir()
        if not exists:
            missing.append(layer["id"])
        layers.append(
            {
                "id": layer["id"],
                "label": layer["label"],
                "path": str(path),
                "exists": exists,
            },
        )

    return {
        "ready": len(missing) == 0,
        "missing_layers": missing,
        "layers": layers,
    }


def _appflowy_status() -> dict[str, Any]:
    databases, errors = _discover_appflowy_databases_safe()
    workspaces: list[dict[str, Any]] = []

    try:
        workspaces = list_workspaces()
    except Exception as exc:
        log.warning("AppFlowy workspace list failed: %s", exc)
        errors.append(f"workspace_list_failed: {exc}")

    available = bool(databases) and not errors
    status = "ok" if available else "degraded"

    return {
        "status": status,
        "mode": "optional-mirror",
        "enabled_by_default": True,
        "available": available,
        "database_count": len(databases),
        "workspace_count": len(workspaces),
        "databases": sorted(databases.keys()),
        "errors": errors,
    }


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _safe_relative_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if resolved_root != candidate and resolved_root not in candidate.parents:
        raise ValueError("Path escapes vault root")
    return candidate


def _vault_layer_by_id(layer_id: str) -> dict[str, Any] | None:
    for layer in VAULT_LAYERS:
        if layer.get("id") == layer_id:
            return layer
    return None


def _safe_binder_name(raw: str) -> str:
    binder = (raw or "").strip() or DEFAULT_USER_BINDER
    if any(part in binder for part in ("..", "/", "\\")):
        raise ValueError("Invalid binder name")
    return binder


def _build_import_filename(title: str, filename: str) -> str:
    if filename:
        candidate = filename.strip()
        if any(part in candidate for part in ("..", "/", "\\")):
            raise ValueError("Invalid filename")
        if not candidate.lower().endswith(".md"):
            candidate += ".md"
        return candidate

    base = slugify(title.strip() or "imported-document")
    return f"{base}-{_utc_stamp().lower()}.md"


def _render_import_document(frontmatter: dict[str, Any], markdown: str) -> str:
    front = yaml.safe_dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=False,
    ).strip()
    body = markdown.strip()
    if not body:
        body = "Imported document has no body."
    return f"---\n{front}\n---\n\n{body}\n"


def _archive_base_dir() -> Path:
    return settings.logs_dir / "user-workflow-archives"


def _copy_tasker_snapshot(tasker_dir: Path, out_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": str(tasker_dir),
        "exists": tasker_dir.exists(),
        "copied_files": 0,
    }
    if not tasker_dir.exists():
        return result

    snapshot_dir = out_dir / "tasker"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for file in tasker_dir.rglob("*"):
        if not file.is_file():
            continue
        rel = file.relative_to(tasker_dir)
        dest = snapshot_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(file.read_bytes())
        copied += 1

    result["copied_files"] = copied
    result["snapshot"] = str(snapshot_dir)
    return result


def _copy_workflow_db(out_dir: Path) -> dict[str, Any]:
    db_path = settings.data_dir / "workflows.db"
    result: dict[str, Any] = {
        "source": str(db_path),
        "exists": db_path.exists(),
        "copied": False,
    }
    if not db_path.exists():
        return result

    dest = out_dir / "workflows.db"
    dest.write_bytes(db_path.read_bytes())
    result["copied"] = True
    result["snapshot"] = str(dest)
    return result


def _archive_data_dir_tar(out_dir: Path) -> dict[str, Any]:
    source = settings.data_dir.expanduser()
    tar_path = out_dir / "ucore-data.tar.gz"
    result: dict[str, Any] = {
        "source": str(source),
        "exists": source.exists(),
        "archive": str(tar_path),
        "created": False,
    }
    if not source.exists():
        return result

    with tarfile.open(tar_path, mode="w:gz") as tar:
        tar.add(source, arcname="ucore-data")

    result["created"] = True
    return result


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        (
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name = ? LIMIT 1"
        ),
        (table,),
    ).fetchone()
    return bool(row)


def _export_appflowy_sidecar_tables(out_dir: Path) -> dict[str, Any]:
    exports: list[dict[str, Any]] = []
    dbs, errors = _discover_appflowy_databases_safe()
    sidecar_dir = out_dir / "appflowy-sidecar"
    sidecar_dir.mkdir(parents=True, exist_ok=True)

    for key, db_path in dbs.items():
        db_result: dict[str, Any] = {
            "database": key,
            "path": db_path,
            "exported": [],
            "errors": [],
        }
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            for table in ("ucore_vault_index", "ucore_vault_index_fts"):
                if not _table_exists(conn, table):
                    continue
                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
                out_file = sidecar_dir / f"{key}-{table}.jsonl"
                with out_file.open("w", encoding="utf-8") as f:
                    for row in rows:
                        line = json.dumps(
                            dict(row),
                            ensure_ascii=True,
                        )
                        f.write(line + "\n")
                db_result["exported"].append(
                    {
                        "table": table,
                        "rows": len(rows),
                        "file": str(out_file),
                    },
                )
            conn.close()
        except Exception as exc:
            db_result["errors"].append(str(exc))

        exports.append(db_result)

    return {
        "count": len(exports),
        "exports": exports,
        "errors": errors,
    }


def _create_archive_snapshot(reason: str = "manual") -> dict[str, Any]:
    stamp = _utc_stamp()
    base = _archive_base_dir()
    archive_dir = base / stamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    tasker_dir = default_tasker_dir()
    tasker_snapshot = _copy_tasker_snapshot(tasker_dir, archive_dir)
    workflows_snapshot = _copy_workflow_db(archive_dir)
    data_snapshot = _archive_data_dir_tar(archive_dir)
    appflowy_sidecar = _export_appflowy_sidecar_tables(archive_dir)

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "reason": reason,
        "archive_dir": str(archive_dir),
        "tasker": tasker_snapshot,
        "workflows_db": workflows_snapshot,
        "data_dir_tar": data_snapshot,
        "appflowy_sidecar": appflowy_sidecar,
    }
    manifest_path = archive_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    manifest["manifest"] = str(manifest_path)
    return manifest


def _clear_tasker_files(tasker_dir: Path) -> dict[str, Any]:
    removed = 0
    if not tasker_dir.exists():
        return {
            "tasker_dir": str(tasker_dir),
            "exists": False,
            "removed_files": 0,
        }

    for md in tasker_dir.rglob("*.md"):
        if md.name.lower() == "readme.md":
            continue
        md.unlink(missing_ok=True)
        removed += 1

    return {
        "tasker_dir": str(tasker_dir),
        "exists": True,
        "removed_files": removed,
    }


def _clear_workflow_db() -> dict[str, Any]:
    db_path = settings.data_dir / "workflows.db"
    existed = db_path.exists()
    if existed:
        db_path.unlink(missing_ok=True)
    return {
        "path": str(db_path),
        "existed": existed,
        "removed": existed,
    }


def _clear_appflowy_sidecar_tables() -> dict[str, Any]:
    dbs, errors = _discover_appflowy_databases_safe()
    cleared: list[dict[str, Any]] = []

    for key, db_path in dbs.items():
        result: dict[str, Any] = {
            "database": key,
            "path": db_path,
            "dropped": [],
            "errors": [],
        }
        try:
            conn = sqlite3.connect(db_path)
            for table in ("ucore_vault_index_fts", "ucore_vault_index"):
                conn.execute(f'DROP TABLE IF EXISTS "{table}"')
                result["dropped"].append(table)
            conn.commit()
            conn.close()
        except Exception as exc:
            result["errors"].append(str(exc))
        cleared.append(result)

    return {
        "count": len(cleared),
        "results": cleared,
        "errors": errors,
    }


def _seed_user_tasks(tasker_dir: Path) -> dict[str, Any]:
    seed_rows = [
        {
            "board": "sandbox",
            "title": "Welcome to uCode",
            "status": "todo",
            "mission": "Getting Started",
            "task": "Welcome to uCode",
            "binder": DEFAULT_USER_BINDER,
            "priority": "high",
            "tags": ["seed", "user", "ucode"],
            "summary": "Open the Sandbox binder and review the starter docs.",
        },
        {
            "board": "sandbox",
            "title": "My First Binder",
            "status": "todo",
            "mission": "Getting Started",
            "task": "My First Binder",
            "binder": DEFAULT_USER_BINDER,
            "priority": "medium",
            "tags": ["seed", "binder"],
            "summary": "Add one note, one task, and one reference to Sandbox.",
        },
        {
            "board": "sandbox",
            "title": "Add a Sandbox note",
            "status": "review",
            "mission": "Getting Started",
            "task": "Add a Sandbox note",
            "binder": DEFAULT_USER_BINDER,
            "priority": "medium",
            "tags": ["seed", "notes"],
            "summary": "Create or edit a Markdown note from the filepicker.",
        },
        {
            "board": "sandbox",
            "title": "Publish Sandbox draft",
            "status": "completed",
            "mission": "Getting Started",
            "task": "Publish Sandbox draft",
            "binder": DEFAULT_USER_BINDER,
            "priority": "low",
            "tags": ["seed", "publish"],
            "summary": (
                "Use the Publish tab after the binder has useful content."
            ),
        },
    ]

    created: list[str] = []
    tasker_dir.mkdir(parents=True, exist_ok=True)

    for row in seed_rows:
        board_dir = tasker_dir / str(row["board"])
        board_dir.mkdir(parents=True, exist_ok=True)
        title = str(row["title"])
        status = normalize_status(str(row.get("status") or "todo"))
        source_id = f"seed-{slugify(title)}"
        file_path = board_dir / (
            f"{status}-{slugify(title)}-{slugify(source_id)}.md"
        )

        content = render_task_markdown(
            title=title,
            source="seed-user-workflow",
            source_id=source_id,
            status=status,
            body=str(row.get("summary") or ""),
            metadata={
                "mission": str(row.get("mission") or ""),
                "task": str(row.get("task") or title),
                "binder": str(row.get("binder") or ""),
                "priority": normalize_priority(
                    str(row.get("priority") or "medium"),
                ),
                "tags": normalize_tags(row.get("tags") or []),
            },
        )
        file_path.write_text(content, encoding="utf-8")
        created.append(str(file_path))

    return {
        "tasker_dir": str(tasker_dir),
        "created_count": len(created),
        "created": created,
    }


def _seed_user_vault_docs() -> dict[str, Any]:
    user_vault = Path.home() / "Vault"
    binder_dir = user_vault / "binders" / "active" / DEFAULT_USER_BINDER
    docs_dir = binder_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    seed_files = {
        binder_dir / "_binder.yaml": (
            "id: sandbox\n"
            "name: Sandbox\n"
            "status: active\n"
            "description: Default user binder for new files and starter "
            "docs.\n"
        ),
        binder_dir / "README.md": (
            "---\n"
            "title: Sandbox\n"
            "binder: Sandbox\n"
            "mission: Getting Started\n"
            "tags: [seed, sandbox, binder]\n"
            "---\n\n"
            "# Sandbox\n\n"
            "Sandbox is your default user binder. New user files connect here "
            "when no binder is specified.\n"
        ),
        docs_dir / "welcome-to-ucode.md": (
            "---\n"
            "title: Welcome to uCode\n"
            "binder: Sandbox\n"
            "mission: Getting Started\n"
            "tags: [seed, ucode, welcome]\n"
            "---\n\n"
            "# Welcome to uCode\n\n"
            "This starter document confirms your User Vault is connected to "
            "the Workflow editor through the Sandbox binder.\n\n"
            "Open this file from the sidebar to edit it in Workflow.\n"
        ),
        docs_dir / "my-first-binder.md": (
            "---\n"
            "title: My First Binder\n"
            "binder: Sandbox\n"
            "mission: Getting Started\n"
            "tags: [seed, binder]\n"
            "---\n\n"
            "# My First Binder\n\n"
            "A binder groups notes, tasks, references, and publishable work. "
            "Sandbox is always available as the default binder.\n"
        ),
    }

    created: list[str] = []
    existing: list[str] = []
    for path, content in seed_files.items():
        if path.exists():
            existing.append(str(path))
            continue
        path.write_text(content, encoding="utf-8")
        created.append(str(path))

    return {
        "vault_path": str(user_vault),
        "binder": DEFAULT_USER_BINDER,
        "created_count": len(created),
        "created": created,
        "existing": existing,
    }


def _seed_workflows() -> dict[str, Any]:
    from app.services.workflow_manager import WorkflowManager

    manager = WorkflowManager()
    seeds = [
        {
            "id": "wf-daily-review-seed",
            "name": "Daily Review Pipeline",
            "description": "Daily markdown review and planning loop.",
            "schedule": "manual",
            "steps": [
                {
                    "type": "skill",
                    "skill_id": "vault_sync",
                    "params": {"dry_run": True, "summary_only": True},
                },
            ],
        },
        {
            "id": "wf-draft-publish-seed",
            "name": "Draft to Publish Checklist",
            "description": "Lightweight readiness workflow for publishing.",
            "schedule": "manual",
            "steps": [
                {
                    "type": "skill",
                    "skill_id": "route_task",
                    "params": {
                        "task": "Review draft and prepare publish checklist",
                    },
                },
            ],
        },
    ]

    created: list[dict[str, Any]] = []
    for seed in seeds:
        created.append(
            manager.create_workflow(
                workflow_id=seed["id"],
                name=seed["name"],
                description=seed["description"],
                schedule=seed["schedule"],
                steps=seed["steps"],
            ),
        )

    return {
        "created_count": len(created),
        "workflows": created,
    }


def _reset_and_seed_user_workflow(reason: str) -> dict[str, Any]:
    archive = _create_archive_snapshot(reason=reason)
    tasker_dir = default_tasker_dir()

    cleared_tasker = _clear_tasker_files(tasker_dir)
    cleared_workflows = _clear_workflow_db()
    cleared_sidecar = _clear_appflowy_sidecar_tables()

    seeded_tasks = _seed_user_tasks(tasker_dir)
    seeded_vault_docs = _seed_user_vault_docs()
    seeded_workflows = _seed_workflows()

    return {
        "archive": archive,
        "cleared": {
            "tasker": cleared_tasker,
            "workflows_db": cleared_workflows,
            "appflowy_sidecar": cleared_sidecar,
        },
        "seed": {
            "tasks": seeded_tasks,
            "vault_docs": seeded_vault_docs,
            "workflows": seeded_workflows,
        },
    }


async def handle_user_workflow_status(request: web.Request) -> web.Response:
    """GET /api/user/workflow/status — user-flow status and health checks."""
    tasker = scan_tasker_boards()
    tasker_payload = {
        "tasker_dir": tasker.get("tasker_dir"),
        "exists": bool(tasker.get("exists", False)),
        "boards": tasker.get("boards", []),
        "total_tasks": int(tasker.get("total_items", 0)),
    }

    vault = _vault_status()
    appflowy = _appflowy_status()

    next_actions: list[str] = []
    if not vault["ready"]:
        next_actions.append(
            "Create missing vault directories and run initial "
            "Vault sync dry-run.",
        )
    if not appflowy["available"]:
        next_actions.append(
            "Run AppFlowy diagnostics and continue in "
            "Markdown-first mode.",
        )
    if not next_actions:
        next_actions.append(
            "User workflow is healthy. Continue with missions, "
            "tasks, and publish stages.",
        )

    return web.json_response(
        {
            "status": "ok",
            "domain": "user-workflow",
            "source_of_truth": "markdown",
            "tasker": tasker_payload,
            "vault": vault,
            "appflowy": appflowy,
            "next_actions": next_actions,
        },
    )


async def handle_user_workflow_archive(request: web.Request) -> web.Response:
    """POST /api/user/workflow/archive — snapshot current user workflow."""
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    reason = str(body.get("reason") or "manual").strip() or "manual"
    archive = _create_archive_snapshot(reason=reason)
    return web.json_response(
        {
            "status": "ok",
            "operation": "archive",
            "archive": archive,
        },
    )


async def handle_user_workflow_reset(request: web.Request) -> web.Response:
    """POST /api/user/workflow/reset — archive, clear state, and seed fresh."""
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    reason = str(body.get("reason") or "reset").strip() or "reset"
    result = _reset_and_seed_user_workflow(reason=reason)
    return web.json_response(
        {
            "status": "ok",
            "operation": "reset",
            **result,
        },
    )


async def handle_user_workflow_seed(request: web.Request) -> web.Response:
    """POST /api/user/workflow/seed.

    Seed user tasks/workflows without clearing existing data.
    """
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        body = {}

    reason = str(body.get("reason") or "seed-only").strip() or "seed-only"
    tasker_dir = default_tasker_dir()
    seeded_tasks = _seed_user_tasks(tasker_dir)
    seeded_vault_docs = _seed_user_vault_docs()
    seeded_workflows = _seed_workflows()

    return web.json_response(
        {
            "status": "ok",
            "operation": "seed",
            "reason": reason,
            "seed": {
                "tasks": seeded_tasks,
                "vault_docs": seeded_vault_docs,
                "workflows": seeded_workflows,
            },
        },
    )


async def handle_user_workflow_import_markdown(
    request: web.Request,
) -> web.Response:
    """POST /api/user/workflow/import-markdown.

    Canonical import lane: any supported source format -> markdown -> vault/binder.
    """
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON payload"},
            status=400,
        )

    content = str(body.get("content") or "")
    if not content.strip():
        return web.json_response(
            {"error": "content is required"},
            status=400,
        )

    source_format = str(body.get("source_format") or "auto")
    title = str(body.get("title") or "Imported Document").strip()
    filename = str(body.get("filename") or "").strip()
    binder_raw = str(body.get("binder") or DEFAULT_USER_BINDER)
    vault_layer_id = str(body.get("vault_layer") or "user").strip()
    relative_dir = str(body.get("relative_dir") or "").strip()
    overwrite = bool(body.get("overwrite", False))
    metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else {}

    layer = _vault_layer_by_id(vault_layer_id)
    if not layer:
        return web.json_response(
            {
                "error": f"Unknown vault_layer: {vault_layer_id}",
                "valid_layers": [entry.get("id") for entry in VAULT_LAYERS],
            },
            status=400,
        )

    if str(layer.get("permissions") or "").lower() == "read_only":
        return web.json_response(
            {
                "error": f"vault_layer '{vault_layer_id}' is read-only",
            },
            status=403,
        )

    try:
        binder = _safe_binder_name(binder_raw)
        root = Path(str(layer.get("path") or "")).expanduser()
        root.mkdir(parents=True, exist_ok=True)

        if relative_dir:
            target_dir = _safe_relative_path(root, relative_dir)
        else:
            target_dir = root / "binders" / "active" / binder / "docs"

        target_dir.mkdir(parents=True, exist_ok=True)

        output_name = _build_import_filename(title=title, filename=filename)
        output_path = (target_dir / output_name).resolve()
        target_dir_resolved = target_dir.resolve()
        if target_dir_resolved not in output_path.parents:
            raise ValueError("Output path escapes target directory")

        if output_path.exists() and not overwrite:
            return web.json_response(
                {
                    "error": "Target file already exists",
                    "path": str(output_path),
                },
                status=409,
            )

        converted = convert_content_to_markdown(
            content=content,
            source_format=source_format,
        )

        frontmatter: dict[str, Any] = {
            "title": title,
            "binder": binder,
            "vault_layer": vault_layer_id,
            "imported_at": datetime.now(UTC).isoformat(),
            "import_source_format": source_format,
            "detected_source_format": converted.source_format,
            "import_plugin": converted.plugin_id,
        }
        if metadata:
            frontmatter["metadata"] = metadata

        document = _render_import_document(frontmatter, converted.markdown)
        output_path.write_text(document, encoding="utf-8")
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:
        log.exception("Markdown import failed")
        return web.json_response({"error": f"import_failed: {exc}"}, status=500)

    return web.json_response(
        {
            "status": "ok",
            "operation": "import-markdown",
            "path": str(output_path),
            "vault_layer": vault_layer_id,
            "binder": binder,
            "title": title,
            "import_plugin": converted.plugin_id,
            "detected_source_format": converted.source_format,
            "bytes_written": len(document.encode("utf-8")),
        },
    )
