"""Report proposed User Vault moves and references without changing files."""

import json
import os
import re
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path
from urllib.parse import unquote

from app.api.tasker_api import _parse_markdown_task
from app.core.settings import settings
from app.flow.task_store import default_tasker_dir

DOCUMENT_EXTENSIONS = {".md", ".markdown", ".txt", ".pdf", ".docx", ".rtf", ".ipynb"}
LEGACY_LINK = re.compile(r"(?i)(?:^|[^\w-])binders/([^/\s)#]+)(?:/|\b)")
REVIEW_FOLDERS = {"active", "completed", "on-hold", "templates"}

MEMORY_COLLECTIONS = {
    "@inbox": "Intake", "originals": "Intake",
    "activity": "Activity", "feeds": "Activity", "dispatches": "Activity",
    "knowledge": "Reference", "research": "Reference",
    "missions": "Workflow", "tasks": "Workflow", "templates": "Workflow",
    "daily": "Personal", "journals": "Personal", "people": "Personal",
    "attachments": "Files", "documents": "Files",
    "exports": "Exports", "jekyll": "Exports", "web": "Exports",
}


def memory_destinations(vault: Path, root: list[Path]) -> list[dict]:
    rows = []
    for source in root:
        name = path_key(source.name)
        if source.name.startswith(".") or name in {"binders", "sandbox", "memory", "trash"}:
            continue
        if not source.is_dir() and not source.is_symlink():
            continue
        if not source.is_symlink() and (source / "binder.json").is_file():
            continue
        category = MEMORY_COLLECTIONS.get(name)
        row = {"source": str(source), "status": "manual_review"}
        rows.append(row)
        if not category or source.is_symlink() or not source.is_dir():
            continue
        target_name = "Transport" if name == "dispatches" else source.name
        target = vault / "Memory" / category / target_name
        row["target"] = str(target)
        current = vault
        for component in target.relative_to(vault).parts:
            matches = [p for p in current.iterdir() if path_key(p.name) == path_key(component)]
            if not matches:
                row["status"] = "owner_review"
                break
            if (len(matches) != 1 or matches[0].name != component
                    or matches[0].is_symlink() or not matches[0].is_dir() or current / component == target):
                row["status"] = "conflict"
                break
            current = matches[0]
    return rows


def path_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def files_under(root: Path):
    if root.is_symlink():
        return
    for folder, children, files in os.walk(root):
        children[:] = sorted(name for name in children if not name.startswith("."))
        for name in sorted(files):
            path = Path(folder, name)
            if not path.is_symlink() and path.is_file():
                yield path


def preview(vault: Path, tasks: Path, database: Path) -> dict:
    if not vault.is_dir():
        raise ValueError(f"Vault is unavailable: {vault}")
    root = sorted(vault.iterdir())
    rows = []
    legacy_roots = [path for path in root if path_key(path.name) == "binders"]
    for legacy in legacy_roots:
        if legacy.is_symlink() or not legacy.is_dir():
            rows.append({"source": str(legacy), "status": "manual_review"})
            continue
        for source in sorted(legacy.iterdir()):
            row = {"source": str(source), "status": "manual_review"}
            rows.append(row)
            metadata = source / "binder.json"
            if source.is_symlink() or not source.is_dir() or metadata.is_symlink() or not metadata.is_file():
                if source.name in REVIEW_FOLDERS and source.is_dir() and not source.is_symlink():
                    row["entries"] = sorted(child.name for child in source.iterdir())
                continue
            try:
                record = json.loads(metadata.read_text(encoding="utf-8"))
                binder_id = record.get("id") if isinstance(record, dict) else None
            except (ValueError, OSError):
                continue
            if not isinstance(binder_id, str) or not re.fullmatch(r"[\w-]+", binder_id) or binder_id != source.name:
                continue
            target = vault / binder_id
            row.update(id=binder_id, target=str(target))
            if path_key(binder_id) in {"memory", "trash"} or any(path_key(path.name) == path_key(binder_id) for path in root):
                row["status"] = "conflict"
            elif path_key(binder_id) == "sandbox":
                row["status"] = "sandbox_conversion_review"
            else:
                row["status"] = "move_candidate"

    destinations = {}
    for row in rows:
        if "target" in row:
            destinations.setdefault(path_key(row["target"]), []).append(row)
    for matches in destinations.values():
        if len(matches) > 1:
            for row in matches:
                row["status"] = "conflict"

    sandbox = vault / "Sandbox"
    sandbox_entries = [path for path in root if path_key(path.name) == "sandbox"]
    sandbox_available = not sandbox_entries or (
        len(sandbox_entries) == 1 and sandbox.is_dir() and not sandbox.is_symlink()
        and sandbox_entries[0].name == "Sandbox"
    )
    used_names = {path_key(path.name) for path in sandbox.iterdir()} if sandbox_available and sandbox.exists() else set()
    loose = []
    for path in root:
        if path.name.startswith(".") or path.suffix.casefold() not in DOCUMENT_EXTENSIONS or path.is_dir():
            continue
        key = path_key(path.name)
        status = "conflict" if key in used_names or not sandbox_available or path.is_symlink() else "move_candidate"
        used_names.add(key)
        loose.append({"source": str(path), "target": str(sandbox / path.name), "status": status})

    sandbox_tasks = [
        str(path) for path in files_under(tasks)
        if path.suffix.casefold() == ".md"
        and str(_parse_markdown_task(path).get("binder", "")).casefold() == "sandbox"
    ]
    missions = []
    if database.is_file():
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='missions'").fetchone():
                missions = [row[0] for row in conn.execute(
                    "SELECT id FROM missions WHERE lower(binder) = 'sandbox' ORDER BY id"
                )]
    links = []
    for path in files_under(vault):
        if path.suffix.casefold() not in {".md", ".markdown"}:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            decoded = unquote(line)
            if LEGACY_LINK.search(decoded) or re.search(r"\[\[Sandbox(?:[/|#\]])", decoded, re.I):
                links.append({"path": str(path.relative_to(vault)), "line": number})
    return {
        "vault": str(vault), "legacy_binders": rows, "loose_root_documents": loose,
        "memory_collections": memory_destinations(vault, root),
        "sandbox_tasks": sandbox_tasks, "sandbox_missions": missions, "legacy_link_candidates": links,
    }


if __name__ == "__main__":
    print(json.dumps(preview(settings.vault_root, default_tasker_dir(), settings.data_dir / "workflows.db"), indent=2))
