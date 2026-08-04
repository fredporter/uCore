"""Developer API — local repo discovery and workspace file listing."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aiohttp import web

from app.core.settings import settings
from app.utils.config_loader import load_developer_repo_policy

# ─── File discovery constants (stable, not policy-driven) ────────

ALLOWED_EXTENSIONS = {
    ".md", ".json", ".yaml", ".yml", ".txt", ".csv",
    ".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".sh", ".toml",
}
IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", ".venv", "venv",
    "__pycache__", ".pytest_cache", ".mypy_cache",
}
MAX_PREVIEW_BYTES = 200_000

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
    if any(
        (repo_path / marker).exists()
        for marker in doc_marker_dirs if marker != "docs"
    ):
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

    return (
        doc_files >= threshold["min_doc_files"]
        and code_files <= threshold["max_code_files"]
    )


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
    policy = _policy()
    name = repo_path.name.lower()
    if name in policy["system_repos"]:
        return "system"

    for root in _vault_non_code_roots():
        if _is_within_path(repo_path, root):
            return "vault_or_docs"

    if _looks_like_doc_library(repo_path):
        return "vault_or_docs"

    if _has_code_markers(repo_path):
        return "code"

    # Fall back to configurable default for uncertain repositories.
    return policy.get("fallback_kind", "code")


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


def _list_repos(scope: str = "code", exclude_system: bool = False) -> list[dict]:
    repos: list[dict] = []
    root = settings.udos_root.expanduser()
    if not root.exists():
        return repos

    for child in sorted(root.iterdir(), key=lambda entry: entry.name.lower()):
        if not child.is_dir() or not (child / ".git").exists():
            continue

        kind = _classify_repo(child)
        if exclude_system and kind == "system":
            continue
        if scope == "code" and kind == "vault_or_docs":
            continue
        if scope == "vault" and kind != "vault_or_docs":
            continue
        if scope == "system" and kind != "system":
            continue

        branch = _git_output(child, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
        status_lines = _git_output(child, "status", "--porcelain").splitlines()
        remote = _git_output(child, "remote", "get-url", "origin") or "No remote"
        changes = len([line for line in status_lines if line.strip()])
        repos.append({
            "id": child.name,
            "name": child.name,
            "path": str(child),
            "branch": branch,
            "status": "clean" if changes == 0 else "modified",
            "changes": changes,
            "remote": remote,
            "fileCount": _repo_file_count(child),
            "kind": kind,
        })

    return repos


def _list_repo_files(repo_name: str, limit: int = 250) -> list[dict]:
    repo_path = _repo_path(repo_name)

    files: list[dict] = []
    for path in repo_path.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        rel_path = path.relative_to(repo_path)
        stat = path.stat()
        files.append({
            "id": len(files) + 1,
            "name": str(rel_path),
            "type": path.suffix.lstrip(".").lower() or "file",
            "size": stat.st_size,
            "updatedAt": path.stat().st_mtime,
            "tags": [path.suffix.lstrip(".").lower()] if path.suffix else [],
            "binder": repo_name,
        })
        if len(files) >= limit:
            break

    files.sort(key=lambda item: item["updatedAt"], reverse=True)
    for file in files:
        file["updatedAt"] = __import__("datetime").datetime.fromtimestamp(
            file["updatedAt"]).isoformat()
    return files


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
            staged.append({
                "file": path,
                "code": x,
                "status": _status_label(x),
            })

        if y not in {" "}:
            unstaged.append({
                "file": path,
                "code": y,
                "status": _status_label(y),
            })

        if x == "?":
            unstaged.append({
                "file": path,
                "code": "??",
                "status": "added",
            })

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
        reviews.append({
            "file": path,
            "status": status,
            "lines": line_counts.get(path, 0),
            "summary": _review_summary(code, path),
        })

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
    status_code = status_output[:2].strip() if status_output else ""

    if status_code == "??":
        diff_text = _build_untracked_diff(repo_name, relative_path)
    else:
        diff_text = _git_output(repo_path, "diff", "--", relative_path)
        if not diff_text:
            diff_text = _git_output(repo_path, "diff", "--cached", "--", relative_path)

    return {
        "repo": repo_name,
        "path": relative_path,
        "status": _status_label(status_code) if status_code else "modified",
        "diff": diff_text,
        "hasDiff": bool(diff_text.strip()),
    }


def _save_repo_file(repo_name: str, relative_path: str, content: str) -> dict[str, Any]:
    file_path = _safe_file_path(repo_name, relative_path)
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
    return f"{compact[:limit - 3]}..."


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
        tasks = [_clean_inline(item, 120) for item in tasks_raw if isinstance(item, str) and item.strip()][:3]

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


async def handle_start_developer(request: web.Request) -> web.Response:
    """Start the developer server (DevMode).

    DevMode is internal dev ops - when active:
    - Dev server (Vite) runs on port 5174
    - Developer Surface is accessible at /developer
    - DevMode icon appears in global toolbar
    """
    import subprocess
    from pathlib import Path

    from app.core.logging import log

    try:
        # Check if already running
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:5174/developer", method="HEAD")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status < 500:
                    return web.json_response({
                        "success": True,
                        "message": "Developer server already running",
                        "dev_mode": {"active": True}
                    })
        except Exception:
            pass

        # Start Vite dev server
        frontend_dir = Path(__file__).resolve().parents[3] / "frontend"
        if not frontend_dir.exists():
            return web.json_response({
                "success": False,
                "error": "Frontend directory not found"
            }, status=404)

        log.info("🚀 [DEVMODE] Starting developer server (internal dev ops)")

        # Start in background
        subprocess.Popen(
            ["pnpm", "dev"],
            cwd=str(frontend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        return web.json_response({
            "success": True,
            "message": "Developer server starting",
            "dev_mode": {"active": True, "starting": True}
        })
    except Exception as e:
        log.error(f"❌ [DEVMODE] Failed to start developer server: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def handle_stop_developer(request: web.Request) -> web.Response:
    """Stop the developer server (DevMode).

    Logs the stop operation for audit trail.
    """
    import subprocess

    from app.core.logging import log

    try:
        log.info("🛑 [DEVMODE] Stopping developer server (internal dev ops)")

        # Find and kill Vite process
        subprocess.run(
            ["pkill", "-f", "vite.*5174"],
            capture_output=True,
            text=True,
            timeout=5
        )

        return web.json_response({
            "success": True,
            "message": "Developer server stopped",
            "dev_mode": {"active": False}
        })
    except Exception as e:
        log.error(f"❌ [DEVMODE] Failed to stop developer server: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def handle_developer_status(request: web.Request) -> web.Response:
    """Get current DevMode status.

    Returns whether the developer server is running and accessible.
    """
    import urllib.request

    from app.core.logging import log

    try:
        req = urllib.request.Request("http://localhost:5174/developer", method="HEAD")
        with urllib.request.urlopen(req, timeout=2) as resp:
            active = resp.status < 500
            if active:
                log.debug("✅ [DEVMODE] Developer server is active")
            return web.json_response({
                "active": active,
                "description": "Internal dev ops - Developer Surface active",
                "icon_visible": active
            })
    except Exception:
        log.debug("⏸️  [DEVMODE] Developer server is inactive")
        return web.json_response({
            "active": False,
            "description": "Internal dev ops - Developer Surface inactive",
            "icon_visible": False
        })


async def handle_list_repos(request: web.Request) -> web.Response:
    scope = request.query.get("scope", "code").strip().lower() or "code"
    if scope not in {"code", "all", "vault", "system"}:
        return web.json_response({"error": f"Invalid scope: {scope}"}, status=400)
    exclude_system = _to_bool(request.query.get("exclude_system"), default=False)
    repos = _list_repos(scope=scope, exclude_system=exclude_system)
    return web.json_response({
        "repos": repos,
        "root": str(settings.udos_root),
        "scope": scope,
        "exclude_system": exclude_system,
    })


async def handle_list_repo_files(request: web.Request) -> web.Response:
    repo_name = request.match_info["repo_name"]
    try:
        files = _list_repo_files(repo_name)
    except FileNotFoundError:
        return web.json_response({"error": f"Repository not found: {repo_name}"}, status=404)
    return web.json_response({"repo": repo_name, "files": files})


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
    that subsequent skill executions (dev-mode-executor, file-edit, etc.)
    can operate on the correct codebase.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )
    workspace = body.get("workspace", "")
    lane = body.get("lane", "ecosystem")
    if not workspace:
        return web.json_response(
            {"error": "workspace is required"}, status=400,
        )

    # Store as app-level config for this session
    request.app["_dev_workspace"] = workspace
    request.app["_dev_lane"] = lane
    return web.json_response({
        "success": True,
        "workspace": workspace,
        "lane": lane,
    })


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
        payload = _save_repo_file(repo_name, relative_path, data["content"])
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


# ─── Dev Chat ───────────────────────────────────────────────────────

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

    log = __import__("logging").getLogger("ucore.devchat")
    binder_fp = ""
    if isinstance(binder_context, dict):
        binder_fp = _clean_inline(binder_context.get("fingerprint"), 80)
    log.info(
        "Dev chat: lane=%s workspace=%s model=%s binder_fp=%s message=%s...",
        lane, workspace, model, binder_fp or "none", message[:80],
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
            "• /api/developer/repos/{name}/diff?path=... — view file diff\n"
            "• /api/developer/repos/{name}/file-preview?path=... — preview file content\n"
            "• /api/developer/repos/{name}/stage — stage a file (POST)\n"
            "• /api/developer/repos/{name}/commit — commit staged files (POST)\n\n"
            "**Skills & MCP:**\n"
            "• /api/skills — list all 54+ built-in skills\n"
            "• /api/skills/{skill_id}/run — execute a named skill\n"
            "• /api/mcp/tools — list MCP server tools\n"
            "• /api/mcp/diagnostics — MCP health diagnostics\n\n"
            "**Health & System:**\n"
            "• /api/control/status — full ecosystem health (Cline, Ollama, Hivemind, etc.)\n"
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
        return web.json_response({
            "response": response.get("content", ""),
            "lane": lane,
            "workspace": workspace,
            "model": response.get("model", model),
            "usage": response.get("usage", {}),
        })
    except Exception as e:
        log.error("Dev chat error: %s", e)
        return web.json_response({
            "error": str(e),
            "message": "Dev chat request failed",
        }, status=500)


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
            dev_system = (
                f"{dev_system}\n\nBinder context (stream metadata):\n"
                + "\n".join(stream_context_lines)
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
        await response.write(f"data: {{\"error\": \"{str(e)}\"}}\n\n".encode())
    finally:
        await response.write_eof()

    return response
