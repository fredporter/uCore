"""Developer API — local repo discovery and workspace file listing."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

from aiohttp import web

from app.core.settings import settings
from app.services.developer_operations import get_developer_operation_manager
from app.utils.config_loader import load_developer_repo_policy

# ─── File discovery constants (stable, not policy-driven) ────────

ALLOWED_EXTENSIONS = {
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".csv",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".css",
    ".sh",
    ".toml",
}
IGNORED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}
MAX_PREVIEW_BYTES = 200_000
MAX_SEARCH_RESULTS = 100


class FileConflictError(RuntimeError):
    """Raised when a file changed after the editor loaded it."""


# ─── Policy loader (lazy, cached once loaded) ────────────────────

_policy_cache: dict[str, Any] = {}


def _policy() -> dict[str, Any]:
    """Return the repo classification policy, loading from config once."""
    if not _policy_cache:
        loaded = load_developer_repo_policy()
        _policy_cache.update(loaded)
    return _policy_cache


def _vault_non_code_roots() -> tuple[Path, ...]:
    """Build absolute Paths for vault/doc root directories from policy."""
    home = Path.home()
    policy = _policy()
    roots = policy.get("vault_non_code_roots", [])
    paths: list[Path] = []
    for raw in roots:
        expanded = Path(raw).expanduser()
        if not expanded.is_absolute():
            expanded = home / expanded
        paths.append(expanded)
    if not paths:
        # fallback — canonical 3 vault types only
        return (
            home / "Vault",
            home / "Shared",
            home / "Public",
        )
    return tuple(paths)


def _is_within_path(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _looks_like_doc_library(repo_path: Path) -> bool:
    name = repo_path.name.lower()
    policy = _policy()
    if name in policy["vault_doc_name_hints"]:
        return True

    doc_marker_dirs = policy["doc_marker_dirs"]
    if any((repo_path / marker).exists() for marker in doc_marker_dirs if marker != "docs"):
        return True

    tracked_files = _git_output(repo_path, "ls-files").splitlines()
    if not tracked_files:
        return False

    scan_limit = policy["scan_limits"]["max_git_files_to_scan"]
    doc_exts = policy["doc_file_extensions"]
    code_exts = policy["code_file_extensions"]
    code_marker_files = policy["code_marker_files"]
    threshold = policy["doc_only_threshold"]

    doc_files = 0
    code_files = 0
    for rel in tracked_files[:scan_limit]:
        rel_path = Path(rel)
        suffix = rel_path.suffix.lower()
        if suffix in doc_exts:
            doc_files += 1
        if suffix in code_exts or rel_path.name.lower() in code_marker_files:
            code_files += 1
            if code_files >= 3:
                return False

    return doc_files >= threshold["min_doc_files"] and code_files <= threshold["max_code_files"]


def _has_code_markers(repo_path: Path) -> bool:
    policy = _policy()
    code_marker_files = policy["code_marker_files"]
    code_marker_dirs = policy["code_marker_dirs"]

    if any((repo_path / marker).exists() for marker in code_marker_files):
        return True
    if any(
        (repo_path / marker).exists() and (repo_path / marker).is_dir()
        for marker in code_marker_dirs
    ):
        return True
    return False


def _classify_repo(repo_path: Path) -> str:
    """Classify a repo as core, extension, project, or vault_or_docs."""
    policy = _policy()
    name = repo_path.name.lower()

    # Core: system repos + required extensions
    if name in policy["system_repos"] or name in policy.get("core_repos", []):
        return "core"

    # Extensions: udos-* plugins
    if name in policy.get("extension_repos", []) or name.startswith("udos-"):
        return "extension"

    # Vault/doc libraries
    for root in _vault_non_code_roots():
        if _is_within_path(repo_path, root):
            return "vault_or_docs"

    if _looks_like_doc_library(repo_path):
        return "vault_or_docs"

    # Projects: has code markers, not core or extension
    if _has_code_markers(repo_path):
        return "project"

    return policy.get("fallback_kind", "project")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _git_output(repo_path: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _github_json(repo_path: Path, *args: str) -> Any:
    """Run one read-only gh query against a repository remote."""
    try:
        result = subprocess.run(
            ["gh", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _repo_github_status(repo_name: str) -> dict[str, Any]:
    """Return the GitHub/Actions state used by the Developer surface."""
    repo_path = _repo_path(repo_name)
    branch = _git_output(repo_path, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    repository = _github_json(
        repo_path,
        "repo",
        "view",
        "--json",
        "nameWithOwner,url,defaultBranchRef",
    )
    if not isinstance(repository, dict):
        return {
            "repo": repo_name,
            "configured": False,
            "branch": branch,
            "error": "GitHub CLI is unavailable, unauthenticated, or the remote is not on GitHub",
        }

    runs = _github_json(
        repo_path,
        "run",
        "list",
        "--branch",
        branch,
        "--limit",
        "5",
        "--json",
        "databaseId,workflowName,status,conclusion,headBranch,event,createdAt,url",
    )
    prs = _github_json(
        repo_path,
        "pr",
        "list",
        "--head",
        branch,
        "--state",
        "open",
        "--limit",
        "1",
        "--json",
        "number,title,state,isDraft,url,statusCheckRollup",
    )
    return {
        "repo": repo_name,
        "configured": True,
        "branch": branch,
        "repository": repository,
        "pull_request": prs[0] if isinstance(prs, list) and prs else None,
        "runs": runs if isinstance(runs, list) else [],
    }


def _repo_file_count(repo_path: Path, limit: int = 500) -> int:
    count = 0
    for path in repo_path.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS:
            count += 1
            if count >= limit:
                return count
    return count


def _repo_path(repo_name: str) -> Path:
    repo_path = (settings.udos_root.expanduser() / repo_name).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        raise FileNotFoundError(repo_name)
    return repo_path


def _safe_file_path(repo_name: str, relative_path: str) -> Path:
    repo_path = _repo_path(repo_name)
    file_path = (repo_path / relative_path).resolve()
    if repo_path not in file_path.parents and file_path != repo_path:
        raise ValueError("Path escapes repository root")
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(relative_path)
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")
    return file_path


def _safe_new_file_path(repo_name: str, relative_path: str) -> Path:
    repo_path = _repo_path(repo_name)
    file_path = (repo_path / relative_path).resolve()
    if repo_path not in file_path.parents or file_path == repo_path:
        raise ValueError("Path escapes repository root")
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")
    return file_path


def _file_revision(path: Path) -> str:
    stat = path.stat()
    return f"{stat.st_mtime_ns}:{stat.st_size}"


def _list_repos(scope: str = "code", exclude_system: bool = False) -> list[dict]:
    repos: list[dict] = []
    root = settings.udos_root.expanduser()
    if not root.exists():
        return repos

    for child in sorted(root.iterdir(), key=lambda entry: entry.name.lower()):
        if not child.is_dir() or not (child / ".git").exists():
            continue

        kind = _classify_repo(child)
        if exclude_system and kind in ("core", "system"):
            continue
        if scope == "code" and kind == "vault_or_docs":
            continue
        if scope == "vault" and kind != "vault_or_docs":
            continue
        if scope == "system" and kind not in ("core", "system"):
            continue

        branch = _git_output(child, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
        status_lines = _git_output(child, "status", "--porcelain").splitlines()
        remote = _git_output(child, "remote", "get-url", "origin") or "No remote"
        changes = len([line for line in status_lines if line.strip()])
        repos.append(
            {
                "id": child.name,
                "name": child.name,
                "path": str(child),
                "branch": branch,
                "status": "clean" if changes == 0 else "modified",
                "changes": changes,
                "remote": remote,
                "fileCount": _repo_file_count(child),
                "kind": kind,
            }
        )

    return repos


def _list_repo_files(
    repo_name: str,
    limit: int = 250,
    include_hidden: bool = False,
    include_all_extensions: bool = False,
) -> list[dict]:
    repo_path = _repo_path(repo_name)

    files: list[dict] = []
    for path in repo_path.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        rel_path = path.relative_to(repo_path)
        if not include_hidden and any(part.startswith(".") for part in rel_path.parts):
            continue
        if not path.is_file():
            continue
        if not include_all_extensions and path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        stat = path.stat()
        files.append(
            {
                "id": len(files) + 1,
                "name": str(rel_path),
                "type": path.suffix.lstrip(".").lower() or "file",
                "size": stat.st_size,
                "updatedAt": path.stat().st_mtime,
                "tags": [path.suffix.lstrip(".").lower()] if path.suffix else [],
                "binder": repo_name,
            }
        )
        if len(files) >= limit:
            break

    files.sort(key=lambda item: item["updatedAt"], reverse=True)
    for file in files:
        file["updatedAt"] = (
            __import__("datetime").datetime.fromtimestamp(file["updatedAt"]).isoformat()
        )
    return files


def _search_repo(repo_name: str, query: str, limit: int = 50) -> list[dict[str, Any]]:
    """Search bounded text files through ripgrep without invoking a shell."""
    repo_path = _repo_path(repo_name)
    term = query.strip()
    if not term or len(term) > 500:
        raise ValueError("query must contain between 1 and 500 characters")
    bounded_limit = max(1, min(limit, MAX_SEARCH_RESULTS))
    command = [
        "rg",
        "--line-number",
        "--column",
        "--no-heading",
        "--color",
        "never",
        "--fixed-strings",
        "--max-count",
        str(bounded_limit),
        term,
        ".",
    ]
    try:
        result = subprocess.run(
            command, cwd=repo_path, capture_output=True, text=True, timeout=8, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Repository search is unavailable") from exc
    if result.returncode not in {0, 1}:
        raise RuntimeError((result.stderr or "Repository search failed")[:500])
    matches: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 3)
        if len(parts) != 4:
            continue
        path, line_number, column, preview = parts
        matches.append(
            {
                "path": path.removeprefix("./"),
                "line": int(line_number),
                "column": int(column),
                "preview": preview[:500],
            }
        )
        if len(matches) >= bounded_limit:
            break
    return matches


def _status_label(code: str) -> str:
    code = code.strip()
    if code in {"A", "??"}:
        return "added"
    if code == "D":
        return "deleted"
    return "modified"


def _review_summary(code: str, path: str) -> str:
    if code == "??":
        return f"Untracked file ready to stage: {path}"
    if "R" in code:
        return f"Renamed in working tree: {path}"
    if "D" in code:
        return f"Deleted from working tree: {path}"
    if "A" in code:
        return f"Added in working tree: {path}"
    return f"Modified in working tree: {path}"


def _list_repo_status(repo_name: str) -> dict[str, list[dict[str, Any]]]:
    """Return staged/unstaged status parsed from git porcelain output."""
    repo_path = _repo_path(repo_name)
    status_output = _git_output(repo_path, "status", "--porcelain")

    staged: list[dict[str, Any]] = []
    unstaged: list[dict[str, Any]] = []

    for raw in status_output.splitlines():
        if not raw.strip() or len(raw) < 3:
            continue

        x = raw[0]
        y = raw[1]
        path = raw[3:].lstrip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]

        if x not in {" ", "?"}:
            staged.append(
                {
                    "file": path,
                    "code": x,
                    "status": _status_label(x),
                }
            )

        if y not in {" "}:
            unstaged.append(
                {
                    "file": path,
                    "code": y,
                    "status": _status_label(y),
                }
            )

        if x == "?":
            unstaged.append(
                {
                    "file": path,
                    "code": "??",
                    "status": "added",
                }
            )

    return {"staged": staged, "unstaged": unstaged}


def _list_repo_review(repo_name: str) -> list[dict[str, Any]]:
    repo_path = _repo_path(repo_name)
    status_output = _git_output(repo_path, "status", "--porcelain")
    numstat_output = _git_output(repo_path, "diff", "--numstat")

    line_counts: dict[str, int] = {}
    for line in numstat_output.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_raw, deleted_raw, file_path = parts
        try:
            added = 0 if added_raw == "-" else int(added_raw)
            deleted = 0 if deleted_raw == "-" else int(deleted_raw)
        except ValueError:
            added = 0
            deleted = 0
        line_counts[file_path] = added + deleted

    reviews: list[dict[str, Any]] = []
    for raw in status_output.splitlines():
        if not raw.strip():
            continue
        code = raw[:2]
        path = raw[2:].lstrip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        status = _status_label(code)
        reviews.append(
            {
                "file": path,
                "status": status,
                "lines": line_counts.get(path, 0),
                "summary": _review_summary(code, path),
            }
        )

    return reviews


def _get_repo_file_preview(repo_name: str, relative_path: str) -> dict[str, Any]:
    file_path = _safe_file_path(repo_name, relative_path)
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    truncated = False
    if len(raw.encode("utf-8")) > MAX_PREVIEW_BYTES:
        raw = raw[:MAX_PREVIEW_BYTES]
        truncated = True
    stat = file_path.stat()
    return {
        "repo": repo_name,
        "path": relative_path,
        "content": raw,
        "type": file_path.suffix.lstrip(".").lower() or "file",
        "size": stat.st_size,
        "truncated": truncated,
        "updatedAt": __import__("datetime").datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "revision": _file_revision(file_path),
    }


def _create_repo_file(repo_name: str, relative_path: str, content: str = "") -> dict[str, Any]:
    file_path = _safe_new_file_path(repo_name, relative_path)
    if file_path.exists():
        raise FileExistsError(relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return _get_repo_file_preview(repo_name, relative_path)


def _move_repo_file(repo_name: str, source: str, destination: str) -> dict[str, Any]:
    source_path = _safe_file_path(repo_name, source)
    destination_path = _safe_new_file_path(repo_name, destination)
    if destination_path.exists():
        raise FileExistsError(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.replace(destination_path)
    return _get_repo_file_preview(repo_name, destination)


def _delete_repo_file(repo_name: str, relative_path: str, revision: str) -> dict[str, Any]:
    file_path = _safe_file_path(repo_name, relative_path)
    if not revision or revision != _file_revision(file_path):
        raise FileConflictError("File changed since it was loaded")
    file_path.unlink()
    return {"repo": repo_name, "path": relative_path, "deleted": True}


def _diagnose_repo_file(repo_name: str, relative_path: str) -> dict[str, Any]:
    file_path = _safe_file_path(repo_name, relative_path)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    suffix = file_path.suffix.lower()
    adapter = {".py": "python-ast", ".json": "json", ".yaml": "yaml", ".yml": "yaml"}.get(suffix)
    if adapter is None:
        return {
            "repo": repo_name,
            "path": relative_path,
            "supported": False,
            "adapter": None,
            "diagnostics": [],
        }
    diagnostics: list[dict[str, Any]] = []
    try:
        if suffix == ".py":
            ast.parse(text, filename=relative_path)
        elif suffix == ".json":
            json.loads(text)
        else:
            import yaml

            yaml.safe_load(text)
    except (SyntaxError, json.JSONDecodeError) as exc:
        diagnostics.append(
            {
                "severity": "error",
                "line": getattr(exc, "lineno", 1) or 1,
                "column": getattr(exc, "offset", 1) or 1,
                "message": str(exc)[:500],
            }
        )
    except Exception as exc:
        diagnostics.append({"severity": "error", "line": 1, "column": 1, "message": str(exc)[:500]})
    return {
        "repo": repo_name,
        "path": relative_path,
        "supported": True,
        "adapter": adapter,
        "diagnostics": diagnostics,
    }


def _build_untracked_diff(repo_name: str, relative_path: str) -> str:
    preview = _get_repo_file_preview(repo_name, relative_path)
    header = [
        f"diff --git a/{relative_path} b/{relative_path}",
        "new file mode 100644",
        "index 0000000..0000000",
        "--- /dev/null",
        f"+++ b/{relative_path}",
        "@@ -0,0 +1 @@",
    ]
    body = [f"+{line}" for line in preview["content"].splitlines()]
    if not body:
        body = ["+"]
    return "\n".join(header + body)


def _get_repo_file_diff(repo_name: str, relative_path: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    _safe_file_path(repo_name, relative_path)
    status_output = _git_output(repo_path, "status", "--porcelain", "--", relative_path)
    status_code = status_output[:2] if status_output else "  "

    if status_code == "??":
        diff_text = _build_untracked_diff(repo_name, relative_path)
        baseline = ""
        status = "added"
    else:
        diff_text = _git_output(repo_path, "diff", "--", relative_path)
        if not diff_text:
            diff_text = _git_output(repo_path, "diff", "--cached", "--", relative_path)
        if status_code[1] != " ":
            baseline = _git_output(repo_path, "show", f":{relative_path}")
        else:
            baseline = _git_output(repo_path, "show", f"HEAD:{relative_path}")
        status = _status_label(status_code.strip()) if status_code.strip() else "clean"

    return {
        "repo": repo_name,
        "path": relative_path,
        "status": status,
        "diff": diff_text,
        "hasDiff": bool(diff_text.strip()),
        "baseline": baseline,
    }


def _save_repo_file(
    repo_name: str, relative_path: str, content: str, revision: str = ""
) -> dict[str, Any]:
    file_path = _safe_file_path(repo_name, relative_path)
    if revision and revision != _file_revision(file_path):
        raise FileConflictError("File changed since it was loaded")
    file_path.write_text(content, encoding="utf-8")
    return _get_repo_file_preview(repo_name, relative_path)


def _stage_repo_file(repo_name: str, relative_path: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    _safe_file_path(repo_name, relative_path)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "add", relative_path],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git add failed: {result.stderr}")
    return {"repo": repo_name, "path": relative_path, "action": "staged", "success": True}


def _unstage_repo_file(repo_name: str, relative_path: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    _safe_file_path(repo_name, relative_path)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "reset", "HEAD", relative_path],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git reset failed: {result.stderr}")
    return {"repo": repo_name, "path": relative_path, "action": "unstaged", "success": True}


def _commit_repo_files(repo_name: str, message: str) -> dict[str, Any]:
    repo_path = _repo_path(repo_name)
    result = subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-m", message],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(f"git commit failed: {result.stderr}")
    success = result.returncode == 0
    return {
        "repo": repo_name,
        "action": "commit",
        "success": success,
        "message": message,
        "output": result.stdout or result.stderr,
    }


def _clean_inline(value: Any, limit: int = 220) -> str:
    """Normalize text for compact context lines in prompts/logs."""
    if not isinstance(value, str):
        return ""
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _summarize_binder_context(
    context: dict[str, Any] | None,
    meta: dict[str, Any] | None = None,
) -> str:
    """Return a deterministic summary block for Binder context attachment."""
    if context is None:
        return ""

    repo_raw = context.get("repository")
    lane_raw = context.get("lane")
    focus_raw = context.get("focus")

    repo: dict[str, Any] = repo_raw if isinstance(repo_raw, dict) else {}
    lane: dict[str, Any] = lane_raw if isinstance(lane_raw, dict) else {}
    focus: dict[str, Any] = focus_raw if isinstance(focus_raw, dict) else {}

    version = _clean_inline(context.get("version"), 32)
    fingerprint = _clean_inline(context.get("fingerprint"), 80)
    repo_name = _clean_inline(repo.get("name"), 80)
    repo_branch = _clean_inline(repo.get("branch"), 80)
    lane_name = _clean_inline(lane.get("name"), 80)
    goal = _clean_inline(focus.get("goal"), 220)

    tasks_raw = focus.get("tasks")
    tasks: list[str] = []
    if isinstance(tasks_raw, list):
        tasks = [
            _clean_inline(item, 120) for item in tasks_raw if isinstance(item, str) and item.strip()
        ][:3]

    source_repo = ""
    source_path = ""
    if isinstance(meta, dict):
        source_repo = _clean_inline(meta.get("repo"), 80)
        source_path = _clean_inline(meta.get("path"), 120)

    lines = ["Binder context (compiled):"]
    if version:
        lines.append(f"- Version: {version}")
    if fingerprint:
        lines.append(f"- Fingerprint: {fingerprint}")
    if repo_name or repo_branch:
        lines.append(f"- Repository: {repo_name or 'unknown'} @ {repo_branch or 'unknown'}")
    if lane_name:
        lines.append(f"- Lane: {lane_name}")
    if goal:
        lines.append(f"- Goal: {goal}")
    if tasks:
        lines.append(f"- Top tasks: {' | '.join(tasks)}")
    if source_repo:
        lines.append(f"- Source: {source_repo}{(':' + source_path) if source_path else ''}")

    return "\n".join(lines)


def _announce_dev(status: str) -> None:
    """Broadcast the Developer extension online/offline state to the UI Hub.

    The Developer surface is now self-hosted within uCore — the uDev repo
    has been retired.  This announces the integrated developer capability.
    """
    try:
        from app.api.render_api import publish_event

        publish_event(
            "extension_online" if status == "online" else "extension_offline",
            {
                "id": "ucore-developer",
                "name": "Developer",
                "version": settings.version,
                "status": status,
            },
        )
    except Exception:
        # Best-effort; the frontend polls /api/developer/status as a fallback.
        pass


async def handle_start_developer(request: web.Request) -> web.Response:
    """Start the developer server (DevMode).

    The Developer Surface is now self-hosted within uCore — the Vite dev
    server on port 5175 serves it directly.  The uDev repo has been retired.
    This endpoint returns the current status; no separate process is spawned.
    """
    from app.core.logging import log

    log.info("[DEVMODE] Developer surface is self-hosted within uCore (uDev retired)")

    _announce_dev("online")
    return web.json_response(
        {
            "success": True,
            "message": "Developer surface is integrated into uCore — served by Vite on port 5175",
            "dev_mode": {"active": True, "self_hosted": True},
        }
    )


async def handle_stop_developer(request: web.Request) -> web.Response:
    """Stop the developer server (DevMode).

    The Developer Surface is self-hosted — this simply announces offline
    state.  No external process to kill since uDev was retired.
    """
    from app.core.logging import log

    log.info("[DEVMODE] Developer surface stop requested (self-hosted, no external process)")

    _announce_dev("offline")
    return web.json_response(
        {
            "success": True,
            "message": "Developer surface status set to offline",
            "dev_mode": {"active": False},
        }
    )


async def handle_developer_status(request: web.Request) -> web.Response:
    """Get current DevMode status.

    The Developer Surface is self-hosted on the Vite dev server (port 5175).
    Checks the Vite frontend rather than a separate uDev process.
    """
    import urllib.request

    from app.core.logging import log

    try:
        # Check the Vite dev server that serves the Developer Surface
        req = urllib.request.Request("http://localhost:5175", method="HEAD")
        with urllib.request.urlopen(req, timeout=2) as resp:
            active = resp.status < 500
            if active:
                log.debug("[DEVMODE] Vite dev server is active on :5175")
            return web.json_response(
                {
                    "active": active,
                    "description": "Developer Surface — self-hosted in uCore (Vite :5175)",
                    "icon_visible": active,
                }
            )
    except Exception:
        log.debug("[DEVMODE] Vite dev server not reachable on :5175")
        return web.json_response(
            {
                "active": False,
                "description": "Developer Surface — Vite dev server not running",
                "icon_visible": False,
            }
        )


async def handle_list_repos(request: web.Request) -> web.Response:
    """GET /api/developer/repos — list code repositories under ~/Code."""
    scope = request.query.get("scope", "code")
    exclude_system = _to_bool(
        request.query.get("exclude_system"),
        default=False,
    )
    try:
        repos = _list_repos(scope=scope, exclude_system=exclude_system)
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=500)
    return web.json_response({"repos": repos, "count": len(repos)})


async def handle_repo_github_status(request: web.Request) -> web.Response:
    """GET /api/developer/repos/{repo_name}/github — PR and Actions state."""
    repo_name = request.match_info["repo_name"]
    try:
        payload = _repo_github_status(repo_name)
    except FileNotFoundError:
        return web.json_response(
            {"error": f"Repository not found: {repo_name}"},
            status=404,
        )
    return web.json_response(payload)


async def handle_list_repo_files(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    include_hidden = _to_bool(request.query.get("include_hidden"), default=False)
    include_all_extensions = _to_bool(
        request.query.get("include_all_extensions"),
        default=False,
    )
    try:
        limit = int(request.query.get("limit", "250"))
    except ValueError:
        return web.json_response({"error": "Invalid query param: limit"}, status=400)
    limit = max(1, min(limit, 20000))
    try:
        files = _list_repo_files(
            repo_name,
            limit=limit,
            include_hidden=include_hidden,
            include_all_extensions=include_all_extensions,
        )
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    return web.json_response(
        {
            "repo": repo_name,
            "files": files,
            "limit": limit,
            "include_hidden": include_hidden,
            "include_all_extensions": include_all_extensions,
        }
    )


async def handle_search_repo(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    query = request.query.get("q", "")
    try:
        limit = int(request.query.get("limit", "50"))
        matches = _search_repo(repo_name, query, limit)
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    except (RuntimeError, ValueError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(
        {"repo": repo_name, "query": query, "matches": matches, "count": len(matches)}
    )


async def handle_get_repo_file_preview(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _get_repo_file_preview(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_workspace_switch(request: web.Request) -> web.Response:
    """POST /api/developer/workspace — persist active workspace context.

    Called by the frontend when the user switches between System
    and Project lanes and/or changes the selected project repository.
    The workspace path is stored in-memory so
    that subsequent governed developer operations can use the correct codebase.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"},
            status=400,
        )
    workspace = body.get("workspace", "")
    lane = body.get("lane", "ecosystem")
    if not workspace:
        return web.json_response(
            {"error": "workspace is required"},
            status=400,
        )

    # Store as app-level config for this session
    request.app["_dev_workspace"] = workspace
    request.app["_dev_lane"] = lane
    return web.json_response(
        {
            "success": True,
            "workspace": workspace,
            "lane": lane,
        }
    )


async def handle_update_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    if not isinstance(data.get("content"), str):
        return web.json_response({"error": "Missing string field: content"}, status=400)

    try:
        payload = _save_repo_file(
            repo_name, relative_path, data["content"], str(data.get("revision", ""))
        )
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except FileConflictError as exc:
        return web.json_response({"error": str(exc), "conflict": True}, status=409)
    return web.json_response(payload)


async def handle_create_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        data = await request.json()
        payload = _create_repo_file(
            repo_name, str(data.get("path", "")).strip(), str(data.get("content", ""))
        )
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    except FileExistsError as exc:
        return web.json_response({"error": f"File already exists: {exc}"}, status=409)
    except (TypeError, ValueError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload, status=201)


async def handle_move_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        data = await request.json()
        payload = _move_repo_file(
            repo_name, str(data.get("source", "")).strip(), str(data.get("destination", "")).strip()
        )
    except FileNotFoundError as exc:
        return web.json_response({"error": f"File not found: {exc}"}, status=404)
    except FileExistsError as exc:
        return web.json_response({"error": f"File already exists: {exc}"}, status=409)
    except (TypeError, ValueError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_delete_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    revision = request.headers.get("If-Match", "").strip()
    try:
        payload = _delete_repo_file(repo_name, relative_path, revision)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except FileConflictError as exc:
        return web.json_response({"error": str(exc), "conflict": True}, status=409)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_diagnose_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    try:
        payload = _diagnose_repo_file(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_get_repo_file_diff(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _get_repo_file_diff(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_list_repo_review(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        review = _list_repo_review(repo_name)
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    return web.json_response({"repo": repo_name, "review": review})


async def handle_repo_status(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        status = _list_repo_status(repo_name)
    except FileNotFoundError:
        return web.json_response(
            {"error": f"Repository not found: {repo_name}"},
            status=404,
        )
    return web.json_response({"repo": repo_name, **status})


async def handle_stage_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _stage_repo_file(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except (ValueError, RuntimeError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_unstage_repo_file(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    relative_path = request.query.get("path", "").strip()
    if not relative_path:
        return web.json_response({"error": "Missing required query param: path"}, status=400)
    try:
        payload = _unstage_repo_file(repo_name, relative_path)
    except FileNotFoundError:
        return web.json_response({"error": f"File not found: {relative_path}"}, status=404)
    except (ValueError, RuntimeError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


async def handle_commit_repo_files(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    message = data.get("message", "Update files").strip()
    if not message:
        message = "Update files"
    try:
        payload = _commit_repo_files(repo_name, message)
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    except RuntimeError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(payload)


# ─── Governed ACP Developer operations ───────────────────────────


async def handle_developer_operation_capabilities(request: web.Request) -> web.Response:
    return web.json_response(get_developer_operation_manager().capabilities())


async def handle_list_developer_operations(request: web.Request) -> web.Response:
    repository = request.query.get("repository", "").strip()
    operations = get_developer_operation_manager().list(repository)
    return web.json_response({"operations": operations, "count": len(operations)})


async def handle_create_developer_operation(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        repository = str(body.get("repository", "")).strip()
        if not repository:
            raise ValueError("repository is required")
        _repo_path(repository)  # apply canonical repository policy before launch
        operation = get_developer_operation_manager().create(
            action=str(body.get("action", "")).strip(),
            repository=repository,
            prompt=str(body.get("prompt", "")),
            context=body.get("context") or {},
        )
    except FileNotFoundError:
        return web.json_response({"error": "Repository not found"}, status=404)
    except PermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)
    except (TypeError, ValueError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(operation.public(), status=202)


async def handle_get_developer_operation(request: web.Request) -> web.Response:
    try:
        operation = get_developer_operation_manager().get(request.match_info["operation_id"])
    except KeyError as exc:
        return web.json_response({"error": str(exc)}, status=404)
    return web.json_response(operation.public())


async def handle_decide_developer_operation(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        decision = str(body.get("decision", "")).strip().lower()
        manager = get_developer_operation_manager()
        if decision == "approve":
            operation = manager.approve(request.match_info["operation_id"])
        elif decision == "deny":
            operation = manager.deny(request.match_info["operation_id"])
        else:
            raise ValueError("decision must be approve or deny")
    except KeyError as exc:
        return web.json_response({"error": str(exc)}, status=404)
    except (TypeError, ValueError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(operation.public())


async def handle_cancel_developer_operation(request: web.Request) -> web.Response:
    try:
        operation = await get_developer_operation_manager().cancel(
            request.match_info["operation_id"]
        )
    except KeyError as exc:
        return web.json_response({"error": str(exc)}, status=404)
    return web.json_response(operation.public())


# ─── Dev Chat ───────────────────────────────────────────────────────


def _execute_developer_read_intent(message: str, workspace: str = "") -> str | None:
    """Execute bounded read-only Dev-lane requests before consulting the model."""
    normalized = " ".join(message.lower().split())
    if any(
        phrase in normalized
        for phrase in ("list repos", "list repositories", "show repos", "show repositories")
    ):
        repos = _list_repos(scope="code")
        if not repos:
            return "No repositories were found in the configured code workspace."
        lines = [f"Found {len(repos)} repositories:"]
        for repo in repos:
            branch = repo.get("branch") or "detached"
            state = "dirty" if repo.get("dirty") else "clean"
            lines.append(f"- **{repo['name']}** — `{branch}` ({state})")
        return "\n".join(lines)
    if workspace and any(
        phrase in normalized for phrase in ("repo status", "repository status", "git status")
    ):
        status = _list_repo_status(workspace)
        counts = {key: len(value) for key, value in status.items()}
        return (
            f"Executed status for **{workspace}**: "
            f"{counts.get('staged', 0)} staged, "
            f"{counts.get('unstaged', 0)} unstaged, and "
            f"{counts.get('untracked', 0)} untracked files."
        )
    return None


async def handle_developer_chat(request: web.Request) -> web.Response:
    """POST /api/developer/chat — dev-lane chat completion.

    Body: { "message": "...", "history": [...], "lane": "ecosystem|project", "workspace": "..." }
    Returns: { "response": "...", "model": "...", "usage": {...} }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    message = body.get("message", "")
    if not message:
        return web.json_response({"error": "message is required"}, status=400)

    lane = body.get("lane", "ecosystem")
    workspace = body.get("workspace", "")
    model = body.get("model")
    binder_context = body.get("binder_context")
    binder_meta = body.get("binder_meta")
    binder_summary = _summarize_binder_context(binder_context, binder_meta)

    history = body.get("history") or body.get("messages")
    if not isinstance(history, list):
        history = []

    try:
        executed_response = _execute_developer_read_intent(message, workspace)
    except (FileNotFoundError, ValueError) as exc:
        return web.json_response({"error": str(exc)}, status=400)
    if executed_response is not None:
        return web.json_response(
            {
                "response": executed_response,
                "lane": lane,
                "workspace": workspace,
                "model": "ucore-read-contract",
                "usage": {},
                "executed": True,
            }
        )

    log = __import__("logging").getLogger("ucore.devchat")
    binder_fp = ""
    if isinstance(binder_context, dict):
        binder_fp = _clean_inline(binder_context.get("fingerprint"), 80)
    log.info(
        "Dev chat: lane=%s workspace=%s model=%s binder_fp=%s message=%s...",
        lane,
        workspace,
        model,
        binder_fp or "none",
        message[:80],
    )

    try:
        from ..services.provider_router import ProviderRouter

        router = ProviderRouter()
        dev_system = (
            "You are the uCore Developer Assistant. You work in the Developer Surface "
            "and have access to these APIs (at http://localhost:8484):\n\n"
            "**Repos & Code:**\n"
            "• /api/developer/repos — list code repositories under ~/Code\n"
            "• /api/developer/repos/{name}/files — list files in a repo\n"
            "• /api/developer/repos/{name}/review — git status review of changes\n"
            "• /api/developer/repos/{name}/status — staged/unstaged file status\n"
            "• /api/developer/repos/{name}/github — GitHub PR and Actions status\n"
            "• /api/developer/repos/{name}/diff?path=... — view file diff\n"
            "• /api/developer/repos/{name}/file-preview?path=... — preview file content\n"
            "• /api/developer/repos/{name}/stage — stage a file (POST)\n"
            "• /api/developer/repos/{name}/commit — commit staged files (POST)\n\n"
            "**Skills:**\n"
            "• /api/skills — list governed built-in skills\n"
            "• /api/skills/{skill_id}/run — execute a named skill\n\n"
            "**Health & System:**\n"
            "• /api/control/status — full ecosystem health (Ollama, Hivemind, providers, etc.)\n"
            "• /api/ollama/status — Ollama model status\n"
            "• /api/system — system info\n"
            "• /api/health — health check\n\n"
            f"**Current Context:** Lane={lane}, Workspace={workspace or 'not set'}\n"
            "The Developer Surface has two lanes:\n"
            "- System lane (ecosystem): uCore/uCode with protection guardrails\n"
            "- Project lane: non-system repos under ~/Code\n\n"
            "Be concise and technical. When users ask to review code, check status, "
            "or manage repos, reference the specific endpoints above. "
            "Prefer suggesting API calls and skill executions over generic advice. "
            "You can help with code review, linting, git operations, skill execution, "
            "MCP server management, service health, and deployment."
        )
        if binder_summary:
            dev_system = f"{dev_system}\n\n{binder_summary}"
        chat_messages = [{"role": "system", "content": dev_system}]
        chat_messages.extend(history)
        chat_messages.append({"role": "user", "content": message})
        response = await router.chat(messages=chat_messages, model=model)
        return web.json_response(
            {
                "response": response.get("content", ""),
                "lane": lane,
                "workspace": workspace,
                "model": response.get("model", model),
                "usage": response.get("usage", {}),
            }
        )
    except Exception as e:
        log.error("Dev chat error: %s", e)
        return web.json_response(
            {
                "error": str(e),
                "message": "Dev chat request failed",
            },
            status=500,
        )


async def handle_developer_chat_stream(request: web.Request) -> web.StreamResponse:
    """GET /api/developer/chat/stream?message=...&lane=... — SSE streaming dev chat."""
    message = request.query.get("message", "").strip()
    if not message:
        return web.json_response({"error": "message is required"}, status=400)

    lane = request.query.get("lane", "ecosystem")
    workspace = request.query.get("workspace", "")
    model = request.query.get("model")
    binder_fingerprint = (
        request.query.get("binder_fingerprint", "").strip()
        or request.headers.get("X-Binder-Fingerprint", "").strip()
    )
    binder_lane = (
        request.query.get("binder_lane", "").strip()
        or request.headers.get("X-Binder-Lane", "").strip()
    )
    binder_goal = (
        request.query.get("binder_goal", "").strip()
        or request.headers.get("X-Binder-Goal", "").strip()
    )
    binder_repo = (
        request.query.get("binder_repo", "").strip()
        or request.headers.get("X-Binder-Repo", "").strip()
    )
    binder_tasks_count = (
        request.query.get("binder_tasks_count", "").strip()
        or request.headers.get("X-Binder-Tasks-Count", "").strip()
    )

    log = __import__("logging").getLogger("ucore.devchat")
    log.info(
        "Dev chat stream: lane=%s binder_fp=%s message=%s...",
        lane,
        _clean_inline(binder_fingerprint, 80) or "none",
        message[:80],
    )

    response = web.StreamResponse(
        status=200,
        reason="OK",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    await response.prepare(request)

    try:
        from ..services.provider_router import ProviderRouter

        router = ProviderRouter()
        dev_system = (
            "You are a developer assistant working in uCore. "
            f"Current lane: {lane}. Workspace: {workspace or 'not set'}. "
            "You help with code review, repo management, skills, MCP servers, "
            "service health, build/deploy, and development workflow. "
            "Be concise and technical."
        )
        stream_context_lines = []
        if binder_fingerprint:
            stream_context_lines.append(
                f"- Fingerprint: {_clean_inline(binder_fingerprint, 80)}",
            )
        if binder_lane:
            stream_context_lines.append(
                f"- Lane override: {_clean_inline(binder_lane, 80)}",
            )
        if binder_repo:
            stream_context_lines.append(
                f"- Binder repo: {_clean_inline(binder_repo, 80)}",
            )
        if binder_goal:
            stream_context_lines.append(
                f"- Goal: {_clean_inline(binder_goal, 220)}",
            )
        if binder_tasks_count:
            stream_context_lines.append(
                f"- Tasks count: {_clean_inline(binder_tasks_count, 16)}",
            )

        if stream_context_lines:
            dev_system = f"{dev_system}\n\nBinder context (stream metadata):\n" + "\n".join(
                stream_context_lines
            )
        chat_messages = [
            {"role": "system", "content": dev_system},
            {"role": "user", "content": message},
        ]
        full_response = await router.chat(messages=chat_messages, model=model, stream=False)

        content = full_response.get("content", "")
        # Simulate streaming by sending tokens one at a time
        import asyncio
        import json

        words = content.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            await response.write(f"data: {json.dumps({'token': token})}\n\n".encode())
            await asyncio.sleep(0.01)

        await response.write(b"data: [DONE]\n\n")
    except Exception as e:
        log.error("Dev chat stream error: %s", e)
        await response.write(f'data: {{"error": "{str(e)}"}}\n\n'.encode())
    finally:
        await response.write_eof()

    return response
