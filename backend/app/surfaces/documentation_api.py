"""Documentation Surface API routes for doc site discovery, browsing, and export."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aiohttp import web

from app.services.doclang_bridge import export_vault_to_doclang_context

log = logging.getLogger("ucore.documentation")

DOC_SITES_ROOT = Path.home() / "Public" / "doc-sites"
GLOBAL_KNOWLEDGE_ROOT = Path.home() / "Public" / "global-knowledge"
DEFAULT_VAULT_SOURCE = Path.home() / "Vault"
DEFAULT_EXPORT_OUTPUT = GLOBAL_KNOWLEDGE_ROOT / "doclang" / "vault-doclang.jsonl"


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
        if child.name.startswith("."):
            continue
        if child.is_dir() or child.is_file():
            sections.append({
                "id": child.name,
                "name": child.stem.replace("-", " ").replace("_", " ").title(),
                "path": str(child),
            })
    return sections


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
    log.debug("Documentation API routes registered")
