"""User Workflow API — markdown-first status for the filesystem vaults."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import tarfile
from tempfile import NamedTemporaryFile
from threading import Lock
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from aiohttp import web

from app.api.vault_api import VAULT_LAYERS
from app.core.settings import settings
from app.flow import binder_engine
from app.services.doclang_bridge import extract_frontmatter
from app.services.markdown_import_pipeline import (
    convert_content_to_markdown,
    render_intake_markdown,
)
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
_markdown_import_lock = Lock()


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


def _build_import_filename(title: str, filename: str, digest: str) -> str:
    if filename:
        candidate = filename.strip()
        if any(part in candidate for part in ("..", "/", "\\")):
            raise ValueError("Invalid filename")
        if not candidate.lower().endswith(".md"):
            candidate += ".md"
        return candidate

    base = slugify(title.strip() or "imported-document")
    return f"{base}-{digest[:16]}.md"


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


def _create_archive_snapshot(reason: str = "manual") -> dict[str, Any]:
    stamp = _utc_stamp()
    base = _archive_base_dir()
    archive_dir = base / stamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    tasker_dir = default_tasker_dir()
    tasker_snapshot = _copy_tasker_snapshot(tasker_dir, archive_dir)
    workflows_snapshot = _copy_workflow_db(archive_dir)
    data_snapshot = _archive_data_dir_tar(archive_dir)

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "reason": reason,
        "archive_dir": str(archive_dir),
        "tasker": tasker_snapshot,
        "workflows_db": workflows_snapshot,
        "data_dir_tar": data_snapshot,
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


def _preview_legacy_sandbox(
    vault: Path, legacy_root: Path, binder_dir: Path, seed_paths: set[Path],
) -> list[dict[str, str]]:
    """Inventory legacy content without following links or changing either copy."""
    managed = {
        "binder.json", "_binder.yaml", "brief.md", "requirements.json", "sources.json",
        "plan.json", "draft.md", "evidence.json", "decisions.json", "editions", "evidence",
    }
    canonical = {
        tuple(part.casefold() for part in path.relative_to(binder_dir).parts): path
        for path in seed_paths
    }
    rows: list[dict[str, str]] = []

    def report(source: Path, target: Path, status: str) -> None:
        rows.append({"source": str(source), "target": str(target), "status": status})

    def destination_status(source: Path, target: Path) -> str:
        if binder_dir.is_symlink():
            return "conflict"
        if not binder_dir.exists():
            return "move_candidate"
        if not binder_dir.is_dir():
            return "conflict"
        current = binder_dir
        parts = target.relative_to(binder_dir).parts
        for index, part in enumerate(parts):
            matches = [entry for entry in current.iterdir() if entry.name.casefold() == part.casefold()]
            if not matches:
                return "move_candidate"
            if len(matches) != 1 or matches[0].name != part or matches[0].is_symlink():
                return "conflict"
            current = matches[0]
            if index < len(parts) - 1 and not current.is_dir():
                return "conflict"
        if current.is_file() and source.stat().st_size == current.stat().st_size:
            with source.open("rb") as original, current.open("rb") as existing:
                while True:
                    chunk = original.read(64 * 1024)
                    if chunk != existing.read(64 * 1024):
                        break
                    if not chunk:
                        return "retained"
        return "conflict"

    def walk(folder: Path, inherited_collision: bool = False) -> None:
        groups: dict[str, list[Path]] = {}
        for entry in sorted(folder.iterdir()):
            groups.setdefault(entry.name.casefold(), []).append(entry)
        for group in groups.values():
            collision = inherited_collision or len(group) > 1
            for entry in group:
                relative = entry.relative_to(legacy_root)
                key = tuple(part.casefold() for part in relative.parts)
                target = canonical.get(key, binder_dir / relative)
                if entry.is_symlink() or key[0] in managed:
                    report(entry, target, "manual_review")
                elif entry.is_dir():
                    walk(entry, collision)
                elif not entry.is_file():
                    report(entry, target, "manual_review")
                else:
                    report(entry, target, "conflict" if collision else destination_status(entry, target))

    current = vault
    for part in legacy_root.relative_to(vault).parts:
        current /= part
        if current.is_symlink():
            report(current, binder_dir, "manual_review")
            return rows
        if not current.is_dir():
            return rows
    walk(legacy_root)
    # Keep starter documents first for callers reviewing an existing seed.
    return sorted(rows, key=lambda row: (Path(row["target"]) not in seed_paths, row["source"]))


def _seed_user_vault_docs() -> dict[str, Any]:
    user_vault = settings.vault_root.resolve()
    legacy_root = user_vault / "binders" / "active" / DEFAULT_USER_BINDER
    if binder_engine.VAULT_ROOT.resolve() != user_vault:
        raise ValueError("Starter Binder belongs to a different vault")
    binder_root = binder_engine.BINDERS_ROOT.resolve()
    if not binder_root.is_relative_to(user_vault) or binder_root == user_vault:
        raise ValueError("Starter Binder directory escapes the vault")
    if (binder_root / DEFAULT_USER_BINDER).is_symlink():
        raise ValueError("Starter Binder directory is a symbolic link")
    try:
        docs_dir = binder_engine.get_binder_documents_dir(DEFAULT_USER_BINDER)
    except FileNotFoundError:
        binder_engine.create_binder(
            DEFAULT_USER_BINDER, "Sandbox", "Review starter documents and practise Binder intake.",
        )
        docs_dir = binder_engine.get_binder_documents_dir(DEFAULT_USER_BINDER)
    binder_dir = docs_dir.parent
    docs_dir.mkdir(parents=True, exist_ok=True)

    seed_files = {
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

    legacy_review = _preview_legacy_sandbox(user_vault, legacy_root, binder_dir, set(seed_files))
    reviewed = [tuple(part.casefold() for part in Path(row["target"]).relative_to(binder_dir).parts)
                for row in legacy_review]
    created: list[str] = []
    existing: list[str] = []
    for path, content in seed_files.items():
        key = tuple(part.casefold() for part in path.relative_to(binder_dir).parts)
        covered = any(key[:len(other)] == other or other[:len(key)] == key for other in reviewed)
        targets = [
            entry for entry in path.parent.iterdir()
            if entry.name.casefold() == path.name.casefold()
        ]
        if targets:
            existing.extend(str(entry) for entry in targets)
            if not covered:
                legacy_review.extend(
                    {"source": str(entry), "target": str(path), "status": "conflict"}
                    for entry in targets
                    if entry.name != path.name or entry.is_symlink() or not entry.is_file()
                )
        if targets or covered:
            continue
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(content)
        except FileExistsError:
            existing.append(str(path))
        else:
            created.append(str(path))

    return {
        "vault_path": str(user_vault),
        "binder": DEFAULT_USER_BINDER,
        "created_count": len(created),
        "created": created,
        "existing": existing,
        "legacy_review": legacy_review,
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

    seeded_tasks = _seed_user_tasks(tasker_dir)
    seeded_vault_docs = _seed_user_vault_docs()
    seeded_workflows = _seed_workflows()

    return {
        "archive": archive,
        "cleared": {
            "tasker": cleared_tasker,
            "workflows_db": cleared_workflows,
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

    next_actions: list[str] = []
    if not vault["ready"]:
        next_actions.append(
            "Create missing vault directories and run initial "
            "Vault sync dry-run.",
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

    Canonical import lane: any supported source format -> markdown ->
    vault/binder.
    """
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON payload"},
            status=400,
        )

    if not isinstance(body, dict):
        return web.json_response({"error": "Expected an import object"}, status=400)
    if body.get("source_format") == "feed":
        return await asyncio.to_thread(_import_feed, body)
    return _import_markdown(body)


def _import_feed(body: dict[str, Any]) -> web.Response:
    """Import a saved feed into an existing private Binder."""
    try:
        from udos_publishing.src.feed_codec import parse_feed
    except ModuleNotFoundError as exc:
        if exc.name not in {"udos_publishing", "udos_publishing.src.feed_codec"}:
            raise
        return web.json_response({"error": "Feed import requires the uCore-Publish feed codec"}, status=503)

    binder = body.get("binder")
    source = body.get("feed_source")
    payload = body.get("content")
    if not all(isinstance(value, str) and value.strip() for value in (binder, source, payload)):
        return web.json_response({"error": "binder, feed_source and content are required"}, status=400)
    if body.get("vault_layer", "user") != "user" or body.get("relative_dir"):
        return web.json_response({"error": "Feed imports require an existing private Binder"}, status=400)
    try:
        feed = parse_feed(payload.encode("utf-8"))
    except (ValueError, SyntaxError) as exc:
        return web.json_response({"error": str(exc)}, status=400)

    results = []
    for item in feed.items:
        identity = hashlib.sha256(json.dumps([source, item.uid]).encode("utf-8")).hexdigest()
        snapshot = json.dumps({
            "title": item.title, "url": item.url, "text": item.text, "html": item.html,
            "published": item.published, "updated": item.updated, "tags": item.tags,
        }, sort_keys=True, ensure_ascii=False)
        revision = hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
        converted = convert_content_to_markdown(item.html, "html") if item.html else None
        markdown = item.text or (converted.markdown if converted else "") or item.title or item.uid
        response = _import_markdown({
            "binder": binder,
            "require_existing_binder": True,
            "filename": f"feed-{identity[:24]}-{revision[:24]}.md",
            "title": item.title or "Feed entry",
            "source_format": "markdown",
            "content": markdown,
        }, feed_entry=({
            "uid": f"feed:{identity}", "tags": list(item.tags),
            "feed_entry_id": item.uid, "feed_title": feed.title,
            "source_url": item.url, "published": item.published, "updated": item.updated,
            "source_revision": revision,
        }, source, snapshot))
        results.append({"entry_id": item.uid, "http_status": response.status, **json.loads(response.text)})
        if response.status >= 400:
            return web.json_response({"status": "partial" if len(results) > 1 else "error",
                                      "items": results}, status=response.status)
    return web.json_response({"status": "ok", "items": results})


def _import_markdown(
    body: dict[str, Any],
    *,
    feed_entry: tuple[dict[str, Any], str, str] | None = None,
) -> web.Response:
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
    expected_sha256 = body.get("expected_sha256")
    if expected_sha256 is not None:
        if (
            not isinstance(expected_sha256, str)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)
            or not body.get("require_existing_binder")
            or not filename
            or overwrite
            or feed_entry is not None
        ):
            return web.json_response(
                {"error": "A revision requires a filename, an existing Binder and a SHA-256 digest"},
                status=400,
            )
    metadata = (
        body.get("metadata")
        if isinstance(body.get("metadata"), dict)
        else {}
    )

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

        require_existing = bool(body.get("require_existing_binder", False))
        if require_existing and (vault_layer_id != "user" or relative_dir):
            raise ValueError("Existing Binder imports use its user-vault documents directory")
        if relative_dir:
            target_dir = _safe_relative_path(root, relative_dir)
        elif vault_layer_id == "user":
            try:
                target_dir = binder_engine.get_binder_documents_dir(binder)
                if not target_dir.is_relative_to(root.resolve()):
                    raise ValueError("Binder belongs to a different vault")
            except FileNotFoundError:
                if require_existing:
                    return web.json_response({"error": "Binder not found"}, status=404)
                target_dir = root / "binders" / "active" / binder / "docs"
        else:
            target_dir = root / "binders" / "active" / binder / "docs"

        target_dir.mkdir(parents=True, exist_ok=True)

        entry_fields, source, payload = feed_entry or ({}, filename or title, content)
        source_kind = "feed" if feed_entry else "local"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        output_name = _build_import_filename(title, filename, digest)
        output_path = (target_dir / output_name).resolve()
        target_dir_resolved = target_dir.resolve()
        if target_dir_resolved not in output_path.parents:
            raise ValueError("Output path escapes target directory")

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
            **entry_fields,
        }
        if metadata:
            frontmatter["metadata"] = metadata

        document = render_intake_markdown(
            converted.markdown,
            frontmatter,
            source=source,
            source_kind=source_kind,
            captured_at=frontmatter["imported_at"],
            payload=payload,
            preserve_frontmatter=feed_entry is None and converted.source_format == "markdown",
        )
        duplicate = False
        with _markdown_import_lock:
            if expected_sha256 is not None:
                try:
                    previous_bytes = output_path.read_bytes()
                except FileNotFoundError:
                    return web.json_response({"error": "Binder note not found"}, status=404)
                if hashlib.sha256(previous_bytes).hexdigest() != expected_sha256:
                    return web.json_response({"error": "Binder note changed since it was read"}, status=409)

                previous, _ = extract_frontmatter(previous_bytes.decode("utf-8"))
                revised, _ = extract_frontmatter(document)
                if previous.get("uid") and revised.get("uid") != previous["uid"]:
                    return web.json_response({"error": "A revision must retain the existing note UID"}, status=409)

            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=target_dir, delete=False) as stream:
                staged = Path(stream.name)
                try:
                    stream.write(document)
                    stream.close()
                    if overwrite or expected_sha256 is not None:
                        staged.replace(output_path)
                    else:
                        try:
                            output_path.hardlink_to(staged)
                        except FileExistsError:
                            existing = output_path.read_text(encoding="utf-8")
                            previous, _ = extract_frontmatter(existing)
                            provenance = previous.get("intake")
                            if not isinstance(provenance, dict) or (
                                provenance.get("source_kind"), provenance.get("source"),
                                provenance.get("payload_sha256"),
                            ) != (source_kind, source, digest):
                                return web.json_response(
                                    {"error": "Target file already exists", "path": str(output_path)},
                                    status=409,
                                )
                            document = existing
                            duplicate = True
                finally:
                    staged.unlink(missing_ok=True)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:
        log.exception("Markdown import failed")
        return web.json_response(
            {"error": f"import_failed: {exc}"},
            status=500,
        )

    return web.json_response(
        {
            "status": "ok",
            "operation": "import-markdown",
            "path": str(output_path),
            "workspace_path": "/" + output_path.relative_to(root.resolve()).as_posix(),
            "vault_layer": vault_layer_id,
            "binder": binder,
            "title": title,
            "import_plugin": converted.plugin_id,
            "detected_source_format": converted.source_format,
            "bytes_written": 0 if duplicate else len(document.encode("utf-8")),
            "duplicate": duplicate,
            "sha256": hashlib.sha256(document.encode("utf-8")).hexdigest(),
        },
    )


def _safe_jekyll_collection(raw: str) -> str:
    collection = (raw or "posts").strip().lower()
    if not collection:
        collection = "posts"
    if not re.fullmatch(r"[a-z0-9_-]+", collection):
        raise ValueError("Invalid collection")
    return collection


def _safe_slug(raw: str) -> str:
    slug = slugify((raw or "").strip())
    if not slug:
        raise ValueError("slug is required")
    return slug


def _jekyll_filename(collection: str, slug: str) -> str:
    if collection == "posts":
        return f"{datetime.now(UTC).strftime('%Y-%m-%d')}-{slug}.md"
    return f"{slug}.md"


def _jekyll_target_dir(root: Path, collection: str, relative_dir: str) -> Path:
    if relative_dir:
        return _safe_relative_path(root, relative_dir)
    if collection == "posts":
        return root / "jekyll" / "_posts"
    if collection == "pages":
        return root / "jekyll" / "pages"
    return root / "jekyll" / f"_{collection}"


async def handle_user_workflow_publish_jekyll(
    request: web.Request,
) -> web.Response:
    """POST /api/user/workflow/publish-jekyll.

    Save markdown as a Jekyll-ready document and return local/cloud
    publish guidance.
    """
    try:
        body = await request.json() if request.body_exists else {}
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)

    if not isinstance(body, dict):
        return web.json_response({"error": "Expected an object"}, status=400)
    if body.get("execute_git"):
        return web.json_response({"error": "runtime_deployment_retired", "owner": "external-development"}, status=410)

    content = str(body.get("content") or "")
    if not content.strip():
        return web.json_response({"error": "content is required"}, status=400)

    title = str(body.get("title") or "Untitled").strip() or "Untitled"
    slug_input = str(body.get("slug") or title)
    collection_raw = str(body.get("collection") or "posts")
    publish_mode = str(body.get("publish_mode") or "local").strip().lower()
    if publish_mode not in {"local", "cloud"}:
        return web.json_response(
            {"error": "publish_mode must be 'local' or 'cloud'"},
            status=400,
        )

    vault_layer_id = str(body.get("vault_layer") or "user").strip()
    relative_dir = str(body.get("relative_dir") or "").strip()
    binder_raw = str(body.get("binder") or DEFAULT_USER_BINDER)
    overwrite = bool(body.get("overwrite", False))

    tags_raw = body.get("tags")
    tags: list[str] = []
    if isinstance(tags_raw, str):
        tags = [part.strip() for part in tags_raw.split(",") if part.strip()]
    elif isinstance(tags_raw, list):
        tags = [str(part).strip() for part in tags_raw if str(part).strip()]

    target_repo = str(body.get("target_repo") or "").strip()
    target_branch = str(body.get("target_branch") or "main").strip() or "main"
    layout = str(body.get("layout") or "post").strip() or "post"

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
            {"error": f"vault_layer '{vault_layer_id}' is read-only"},
            status=403,
        )

    try:
        collection = _safe_jekyll_collection(collection_raw)
        slug = _safe_slug(slug_input)
        binder = _safe_binder_name(binder_raw)

        root = Path(str(layer.get("path") or "")).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        target_dir = _jekyll_target_dir(root, collection, relative_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = _jekyll_filename(collection, slug)
        output_path = (target_dir / filename).resolve()
        if target_dir.resolve() not in output_path.parents:
            raise ValueError("Output path escapes target directory")

        if output_path.exists() and not overwrite:
            return web.json_response(
                {
                    "error": "Target file already exists",
                    "path": str(output_path),
                },
                status=409,
            )

        frontmatter: dict[str, Any] = {
            "layout": layout,
            "title": title,
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S +0000"),
            "tags": tags,
            "binder": binder,
            "workflow": "publish",
            "publish_mode": publish_mode,
            "target_branch": target_branch,
        }
        if target_repo:
            frontmatter["target_repo"] = target_repo

        document = _render_import_document(frontmatter, content)
        output_path.write_text(document, encoding="utf-8")
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:
        log.exception("Jekyll publish preparation failed")
        return web.json_response(
            {"error": f"publish_jekyll_failed: {exc}"},
            status=500,
        )

    rel_output = str(output_path)
    local_commands = [
        "bundle install",
        "bundle exec jekyll serve --livereload --drafts",
    ]
    cloud_commands = [
        f"git add '{rel_output}'",
        f"git commit -m 'publish: {slug}'",
        f"git push origin {target_branch}",
    ]

    git_publish = None  # Local preparation never performs repository deployment.

    return web.json_response(
        {
            "status": "ok",
            "operation": "publish-jekyll",
            "path": rel_output,
            "vault_layer": vault_layer_id,
            "collection": collection,
            "slug": slug,
            "publish_mode": publish_mode,
            "frontmatter": frontmatter,
            "next_steps": {
                "local_preview": local_commands,
                "cloud_publish": cloud_commands,
            },
            "git_publish": git_publish,
        },
    )
