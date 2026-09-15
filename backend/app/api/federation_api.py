"""Knowledge Overlay Federation REST API routes.

Provides endpoints for:
- Cascading resolution across Layer 2 (Personal) > Layer 1 (Shared) > Layer 0 (Canon)
- Saving non-destructive personal overrides in ~/Vault/knowledge/
- Reverting personal overrides to restore canonical baseline
- Automated AI preflight linting (privacy scrub, Prose casing, offline assets)
- Cryptographic submission bundle packaging for community/wizard contribution
"""

from __future__ import annotations

import logging
from aiohttp import web

from app.services.knowledge_overlay import KnowledgeOverlayResolver

log = logging.getLogger("ucore.api.federation")

_resolver = KnowledgeOverlayResolver()


def get_resolver() -> KnowledgeOverlayResolver:
    global _resolver
    return _resolver


def set_resolver(resolver: KnowledgeOverlayResolver) -> None:
    """Setter for testing isolation."""
    global _resolver
    _resolver = resolver


async def handle_federation_summary(_request: web.Request) -> web.Response:
    """GET /api/knowledge/federation/summary — overall layers and federation status."""
    resolver = get_resolver()
    summary = resolver.get_federation_summary()
    return web.json_response(summary)


async def handle_federation_overlays(_request: web.Request) -> web.Response:
    """GET /api/knowledge/federation/overlays — list active personal and shared overlays."""
    resolver = get_resolver()
    overlays = resolver.list_overlays()
    return web.json_response({"overlays": overlays, "count": len(overlays)})


async def handle_federation_resolve(request: web.Request) -> web.Response:
    """GET /api/knowledge/federation/resolve?path=...&canonical=... — resolve document."""
    path = request.query.get("path", "").strip()
    if not path:
        return web.json_response({"error": "Query parameter 'path' is required"}, status=400)

    prefer_canon = request.query.get("canonical", "").lower() in ("true", "1", "yes")
    resolver = get_resolver()

    try:
        resolved = resolver.resolve(path, prefer_canon=prefer_canon)
        if not resolved["found"]:
            return web.json_response({"error": f"Document not found: {path}", "resolved": resolved}, status=404)
        return web.json_response(resolved)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)


async def handle_federation_save_overlay(request: web.Request) -> web.Response:
    """POST /api/knowledge/federation/overlay — create or update personal overlay.

    Layer 0 is strictly read-only and will return HTTP 403.
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    path = str(body.get("path") or "").strip()
    content = body.get("content")
    layer = int(body.get("layer", 2))

    if not path:
        return web.json_response({"error": "'path' is required"}, status=400)
    if content is None:
        return web.json_response({"error": "'content' is required"}, status=400)

    resolver = get_resolver()
    try:
        updated = resolver.create_or_update_overlay(path, str(content), layer=layer)
        return web.json_response({"success": True, "overlay": updated})
    except PermissionError as e:
        return web.json_response({"error": str(e)}, status=403)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.exception("Error saving knowledge overlay: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_federation_revert_overlay(request: web.Request) -> web.Response:
    """POST /api/knowledge/federation/revert — revert overlay and restore canon."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    path = str(body.get("path") or "").strip()
    layer = int(body.get("layer", 2))

    if not path:
        return web.json_response({"error": "'path' is required"}, status=400)

    resolver = get_resolver()
    try:
        reverted = resolver.revert_overlay(path, layer=layer)
        return web.json_response({"success": True, "resolved": reverted})
    except PermissionError as e:
        return web.json_response({"error": str(e)}, status=403)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.exception("Error reverting knowledge overlay: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_federation_preflight(request: web.Request) -> web.Response:
    """POST /api/knowledge/federation/preflight — automated linting on document text."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    content = str(body.get("content") or "")
    path = str(body.get("path") or "")

    resolver = get_resolver()
    result = resolver.lint_preflight(content, path)
    return web.json_response(result)


async def handle_federation_export_submission(request: web.Request) -> web.Response:
    """POST /api/knowledge/federation/export-submission — export cryptographic submission package."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    path = str(body.get("path") or "").strip()
    author = str(body.get("author") or "sovereign-user").strip()
    notes = str(body.get("notes") or "").strip()
    submission_type = str(body.get("submission_type") or "canonical_patch").strip()

    if not path:
        return web.json_response({"error": "'path' is required"}, status=400)

    resolver = get_resolver()
    try:
        package = resolver.export_submission_package(
            rel_path=path,
            author=author,
            notes=notes,
            submission_type=submission_type,
        )
        return web.json_response({"success": True, "package": package}, status=201)
    except FileNotFoundError as e:
        return web.json_response({"error": str(e)}, status=404)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=422)
    except Exception as e:
        log.exception("Error exporting submission package: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_federation_submissions(_request: web.Request) -> web.Response:
    """GET /api/knowledge/federation/submissions — list exported submission packages."""
    resolver = get_resolver()
    submissions = resolver.list_submissions()
    return web.json_response({"submissions": submissions, "count": len(submissions)})


def register_federation_routes(app: web.Application) -> None:
    """Register Knowledge Federation endpoints."""
    app.router.add_get("/api/knowledge/federation/summary", handle_federation_summary)
    app.router.add_get("/api/knowledge/federation/overlays", handle_federation_overlays)
    app.router.add_get("/api/knowledge/federation/resolve", handle_federation_resolve)
    app.router.add_post("/api/knowledge/federation/overlay", handle_federation_save_overlay)
    app.router.add_post("/api/knowledge/federation/revert", handle_federation_revert_overlay)
    app.router.add_post("/api/knowledge/federation/preflight", handle_federation_preflight)
    app.router.add_post("/api/knowledge/federation/export-submission", handle_federation_export_submission)
    app.router.add_get("/api/knowledge/federation/submissions", handle_federation_submissions)
    log.info("Registered Knowledge Federation API routes")
