"""Documentation Surface API routes for doc site discovery, browsing, and export."""
from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from aiohttp import web

from app.services.doclang_bridge import export_vault_to_doclang_context

log = logging.getLogger("ucore.documentation")

DOC_SITES_ROOT = Path.home() / "Public" / "doc-sites"
GLOBAL_KNOWLEDGE_ROOT = Path.home() / "Public" / "global-knowledge"
LEARNING_ROOT = Path.home() / "Public" / "learning"
DEFAULT_VAULT_SOURCE = Path.home() / "Vault"
DEFAULT_EXPORT_OUTPUT = GLOBAL_KNOWLEDGE_ROOT / "doclang" / "vault-doclang.jsonl"

# Repos to scan for documentation indexing
REPO_DOC_ROOTS: dict[str, Path] = {
    "uCore": Path.home() / "Code" / "uCore" / "docs",
    "uFlow": Path.home() / "Code" / "uFlow" / "docs",
    "uCode": Path.home() / "Code" / "uCode" / "docs",
    "uKnowledge": Path.home() / "Code" / "uKnowledge" / "docs",
}

# Courses frontmatter field extraction
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _safe_name(value: str) -> str:
    """Allow only simple path-segment names for route params."""
    return "".join(ch for ch in value if ch.isalnum() or ch in {"-", "_", "."})


def _site_built(site_path: Path) -> bool:
    """A doc site is considered built when it has a root index.html."""
    return (site_path / "index.html").is_file()


def _list_doc_sites() -> list[dict[str, Any]]:
    if not DOC_SITES_ROOT.exists() or not DOC_SITES_ROOT.is_dir():
        return []

    sites: list[dict[str, Any]] = []
    for child in sorted(DOC_SITES_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        sites.append({
            "id": child.name,
            "name": child.name.replace("-", " ").replace("_", " ").title(),
            "path": str(child),
            "description": "Published documentation site",
            "built": _site_built(child),
        })
    return sites


def _list_knowledge_sections() -> list[dict[str, Any]]:
    if not GLOBAL_KNOWLEDGE_ROOT.exists() or not GLOBAL_KNOWLEDGE_ROOT.is_dir():
        return []

    sections: list[dict[str, Any]] = []
    for child in sorted(GLOBAL_KNOWLEDGE_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        if child.is_dir():
            sections.append({
                "id": child.name,
                "name": child.name.replace("-", " ").replace("_", " ").title(),
                "path": str(child),
            })
    return sections


def _extract_frontmatter(markdown: str) -> dict[str, Any]:
    """Extract YAML front matter from markdown text as a flat dict."""
    match = FRONTMATTER_RE.match(markdown)
    if not match:
        return {}
    try:
        import yaml
        parsed = yaml.safe_load(match.group(1))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def _list_courses() -> list[dict[str, Any]]:
    """Scan learning, vault, and archived docs for course/guide markdown."""
    roots: dict[str, Path] = {
        "learning": LEARNING_ROOT,
        "vault": Path.home() / "Vault",
        "archive": Path.home() / "Code" / "uCore" / "docs" / "archive",
    }

    courses: list[dict[str, Any]] = []
    for source, root in roots.items():
        if not root.exists() or not root.is_dir():
            continue
        for md_file in sorted(
            root.rglob("*.md"),
            key=lambda p: p.name.lower(),
        ):
            if md_file.name.startswith("."):
                continue
            if any(part in (".git", "node_modules") for part in md_file.parts):
                continue
            try:
                text = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            fm = _extract_frontmatter(text)
            course: dict[str, Any] = {
                "name": (
                    md_file.stem.replace("-", " ")
                    .replace("_", " ")
                    .title()
                ),
                "path": str(md_file.relative_to(root)),
                "source": source,
                "level": fm.get("level", "basic"),
                "relevance": int(fm.get("relevance", 50)),
            }
            if fm.get("title"):
                course["title"] = fm["title"]
            if fm.get("category"):
                course["category"] = fm["category"]
            if fm.get("description"):
                course["description"] = fm["description"]
            courses.append(course)

    return courses


def _list_notebooks() -> list[dict[str, Any]]:
    """Discover .ipynb notebooks from knowledge directories.

    Searches multiple candidate paths since uDev has been retired.
    """
    candidates = [
        Path.home() / "Public" / "global-knowledge",
        Path.home() / "Vault",
        Path.home() / "Code" / "uCore" / "notebooks",
    ]
    knowledge_root = None
    for cand in candidates:
        if cand.exists() and cand.is_dir():
            knowledge_root = cand
            break
    if knowledge_root is None:
        return []
    if not knowledge_root.exists() or not knowledge_root.is_dir():
        return []

    notebooks: list[dict[str, Any]] = []
    for nb_file in sorted(knowledge_root.rglob("*.ipynb"), key=lambda p: p.name.lower()):
        stat = nb_file.stat()
        notebooks.append({
            "name": nb_file.name,
            "stem": nb_file.stem,
            "path": str(nb_file.relative_to(knowledge_root)),
            "full_path": str(nb_file),
            "size": stat.st_size,
            "mtime": stat.st_mtime,
        })
    return notebooks


def _list_repo_docs() -> list[dict[str, Any]]:
    """Index documentation markdown files from known repository docs/ directories."""
    repos: list[dict[str, Any]] = []

    for repo_name, docs_root in REPO_DOC_ROOTS.items():
        if not docs_root.exists() or not docs_root.is_dir():
            continue

        docs: list[dict[str, Any]] = []
        for md_file in sorted(docs_root.rglob("*.md"), key=lambda p: p.name.lower()):
            if md_file.name.startswith("."):
                continue
            if "archive" in md_file.parts or "archived" in md_file.parts:
                # Skip archived docs
                continue
            rel = str(md_file.relative_to(docs_root))
            docs.append({
                "name": md_file.stem.replace("-", " ").replace("_", " ").title(),
                "path": rel,
                "size": md_file.stat().st_size,
            })

        if docs:
            repos.append({
                "repo": repo_name,
                "root": str(docs_root),
                "docs": docs,
                "count": len(docs),
            })

    return repos


def _serve_directory_index(root: Path, section_name: str) -> web.Response:
    safe = _safe_name(section_name)
    if not safe or safe != section_name:
        raise web.HTTPBadRequest(reason="Invalid section name")

    target = (root / safe).resolve()
    try:
        if not target.is_relative_to(root.resolve()):
            raise web.HTTPForbidden(reason="Path outside allowed root")
    except Exception as exc:
        if isinstance(exc, web.HTTPException):
            raise
        raise web.HTTPForbidden(reason="Path outside allowed root") from exc

    if not target.exists():
        raise web.HTTPNotFound(reason="Section not found")

    if target.is_file():
        return web.FileResponse(path=target)

    index_path = target / "index.html"
    if index_path.is_file():
        return web.FileResponse(path=index_path)

    readme = target / "README.md"
    if readme.is_file():
        return web.FileResponse(path=readme)

    entries = sorted(p.name for p in target.iterdir() if not p.name.startswith("."))
    return web.json_response({"section": safe, "entries": entries, "path": str(target)})


async def handle_docs_root(_request: web.Request) -> web.Response:
    """GET /api/docs - return route docs for the Documentation surface."""
    endpoints = [
        {
            "method": "GET",
            "path": "/api/docs",
            "description": "Documentation API index and route reference",
        },
        {
            "method": "GET",
            "path": "/api/docs/sites",
            "description": "List doc sites under ~/Public/doc-sites",
        },
        {
            "method": "GET",
            "path": "/api/docs/serve/{site}/",
            "description": "Serve a doc site index from ~/Public/doc-sites",
        },
        {
            "method": "GET",
            "path": "/api/docs/global-knowledge",
            "description": "List sections under ~/Public/global-knowledge",
        },
        {
            "method": "GET",
            "path": "/api/docs/global-knowledge/{section}/",
            "description": "Serve a section from ~/Public/global-knowledge",
        },
        {
            "method": "GET",
            "path": "/api/docs/courses",
            "description": "List learning courses from ~/Public/learning",
        },
        {
            "method": "GET",
            "path": "/api/docs/notebooks",
            "description": "List Jupyter notebooks from knowledge directories",
        },
        {
            "method": "GET",
            "path": "/api/docs/repo-docs",
            "description": "Index documentation from ~/Code/* repos",
        },
        {
            "method": "POST",
            "path": "/api/docs/export",
            "description": "Export ~/Vault markdown to DocLang jsonl",
        },
    ]
    return web.json_response({"endpoints": endpoints})


async def handle_docs_sites(_request: web.Request) -> web.Response:
    """GET /api/docs/sites - list discovered documentation sites."""
    sites = _list_doc_sites()
    return web.json_response({
        "root": str(DOC_SITES_ROOT),
        "exists": DOC_SITES_ROOT.exists(),
        "sites": sites,
        "count": len(sites),
    })


async def handle_docs_global_knowledge(_request: web.Request) -> web.Response:
    """GET /api/docs/global-knowledge - list knowledge sections."""
    sections = _list_knowledge_sections()
    return web.json_response({
        "root": str(GLOBAL_KNOWLEDGE_ROOT),
        "exists": GLOBAL_KNOWLEDGE_ROOT.exists(),
        "sections": sections,
        "count": len(sections),
    })


async def handle_docs_serve_site(request: web.Request) -> web.Response:
    """GET /api/docs/serve/{site}/ - serve static doc site content."""
    site = request.match_info.get("site", "")
    return _serve_directory_index(DOC_SITES_ROOT, site)


async def handle_docs_serve_global_knowledge(request: web.Request) -> web.Response:
    """GET /api/docs/global-knowledge/{section}/ - serve section content."""
    section = request.match_info.get("section", "")
    return _serve_directory_index(GLOBAL_KNOWLEDGE_ROOT, section)


async def handle_docs_export(request: web.Request) -> web.Response:
    """POST /api/docs/export - export markdown vault to DocLang output."""
    payload: dict[str, Any] = {}
    if request.method == "POST":
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    source_dir = str(payload.get("source_dir", DEFAULT_VAULT_SOURCE))
    output_path = str(payload.get("output_path", DEFAULT_EXPORT_OUTPUT))
    tags = payload.get("tags")
    if tags is not None and not isinstance(tags, list):
        return web.json_response({"error": "tags must be a list of strings"}, status=400)

    result = export_vault_to_doclang_context(
        source_dir=source_dir,
        output_path=output_path,
        tags=tags,
    )

    if result.get("error"):
        return web.json_response(result, status=400)

    return web.json_response({
        "message": "Vault export completed",
        **result,
    })


async def handle_docs_courses(_request: web.Request) -> web.Response:
    """GET /api/docs/courses - list learning courses from ~/Public/learning/."""
    courses = _list_courses()
    return web.json_response({
        "root": str(LEARNING_ROOT),
        "exists": LEARNING_ROOT.exists(),
        "courses": courses,
        "count": len(courses),
    })


async def handle_docs_notebooks(_request: web.Request) -> web.Response:
    """GET /api/docs/notebooks - list Jupyter notebooks from knowledge directories."""
    notebooks = _list_notebooks()
    return web.json_response({
        "notebooks": notebooks,
        "count": len(notebooks),
    })


async def handle_docs_repo_docs(_request: web.Request) -> web.Response:
    """GET /api/docs/repo-docs - index documentation from ~/Code/* repos."""
    repo_docs = _list_repo_docs()
    return web.json_response({
        "repos": repo_docs,
        "count": len(repo_docs),
    })


async def handle_docs_mirror_sync(_request: web.Request) -> web.Response:
    """POST /api/docs/mirror/sync - pull component docs into the mirror."""
    from app.services.docs_mirror import sync_from_repos

    result = await asyncio.to_thread(sync_from_repos)
    return web.json_response(result)


async def handle_docs_mirror_status(_request: web.Request) -> web.Response:
    """GET /api/docs/mirror/status - return the mirror index status."""
    from app.services.docs_mirror import mirror_status

    return web.json_response(mirror_status())


async def handle_docs_mirror_push(request: web.Request) -> web.Response:
    """POST /api/docs/mirror/push - write a mirrored doc back to its repo."""
    from app.services.docs_mirror import push_to_repo

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    repo = str(body.get("repo", "")).strip()
    path = str(body.get("path", "")).strip()
    content = body.get("content")
    if not repo or not path or not isinstance(content, str):
        return web.json_response(
            {"error": "repo, path, and content are required"},
            status=400,
        )

    result = await asyncio.to_thread(push_to_repo, repo, path, content)
    if result.get("success"):
        return web.json_response(result)
    if "Dev Mode" in str(result.get("error", "")):
        return web.json_response(result, status=403)
    return web.json_response(result, status=400)


async def handle_docs_mirror_diff(request: web.Request) -> web.Response:
    """GET /api/docs/mirror/diff/{repo}/{path} - repo-vs-mirror drift."""
    from app.services.docs_mirror import diff_entry

    repo = request.match_info.get("repo", "")
    path = request.match_info.get("path", "")
    result = await asyncio.to_thread(diff_entry, repo, path)
    return web.json_response(result)


_CONTENT_ROOTS: dict[str, Path] = {
    "learning": LEARNING_ROOT,
    "vault": Path.home() / "Vault",
    "knowledge": GLOBAL_KNOWLEDGE_ROOT,
    "archive": Path.home() / "Code" / "uCore" / "docs" / "archive",
    "mirror": Path.home() / ".ucore" / "docs-mirror",
}


def _read_doc_content(source: str, path: str) -> dict[str, Any]:
    """Read markdown content from a doc source for the side-panel viewer."""
    root = _CONTENT_ROOTS.get(source)
    if root is None:
        return {"error": f"Unknown source: {source}", "status": "not_found"}

    rel = path.strip().lstrip("/")
    if not rel or ".." in rel.split("/"):
        return {"error": "Invalid path", "status": "bad_path"}

    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return {"error": "Path outside source root", "status": "bad_path"}

    if not target.exists():
        return {"error": "Not found", "status": "not_found"}

    if target.is_dir():
        for name in ("README.md", "index.md"):
            candidate = target / name
            if candidate.is_file():
                return _doc_payload(candidate, source, rel)
        entries: list[dict[str, Any]] = []
        for p in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            if p.name.startswith("."):
                continue
            child_rel = f"{rel.rstrip('/')}/{p.name}" if rel else p.name
            entries.append(
                {
                    "name": p.name,
                    "path": child_rel,
                    "is_dir": p.is_dir(),
                }
            )
        return {
            "content": "",
            "title": target.name.replace("-", " ").replace("_", " ").title(),
            "path": rel,
            "source": source,
            "is_dir": True,
            "listing": entries,
        }

    return _doc_payload(target, source, rel)


def _doc_payload(file_path: Path, source: str, rel: str) -> dict[str, Any]:
    return {
        "content": file_path.read_text(encoding="utf-8", errors="replace"),
        "title": file_path.stem.replace("-", " ").replace("_", " ").title(),
        "path": rel,
        "source": source,
        "is_dir": False,
    }


async def handle_docs_content(request: web.Request) -> web.Response:
    """GET /api/docs/content?source=...&path=... - markdown for the viewer."""
    source = request.query.get("source", "learning")
    path = request.query.get("path", "")
    result = await asyncio.to_thread(_read_doc_content, source, path)
    return web.json_response(result)


def register_documentation_routes(app: web.Application) -> None:
    """Register Documentation surface API routes."""
    app.router.add_get("/api/docs", handle_docs_root)
    app.router.add_get("/api/docs/sites", handle_docs_sites)
    app.router.add_get("/api/docs/global-knowledge", handle_docs_global_knowledge)
    app.router.add_get("/api/docs/serve/{site}/", handle_docs_serve_site)
    app.router.add_get(
        "/api/docs/global-knowledge/{section}/",
        handle_docs_serve_global_knowledge,
    )
    app.router.add_post("/api/docs/export", handle_docs_export)
    # Add GET parity for health/probing scripts that check endpoint existence.
    app.router.add_get("/api/docs/export", handle_docs_export)
    app.router.add_get("/api/docs/courses", handle_docs_courses)
    app.router.add_get("/api/docs/notebooks", handle_docs_notebooks)
    app.router.add_get("/api/docs/repo-docs", handle_docs_repo_docs)
    app.router.add_post("/api/docs/mirror/sync", handle_docs_mirror_sync)
    app.router.add_get("/api/docs/mirror/status", handle_docs_mirror_status)
    app.router.add_post("/api/docs/mirror/push", handle_docs_mirror_push)
    app.router.add_get(
        "/api/docs/mirror/diff/{repo}/{path:.+}",
        handle_docs_mirror_diff,
    )
    app.router.add_get("/api/docs/content", handle_docs_content)
    log.debug("Documentation API routes registered")
