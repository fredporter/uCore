"""REST API endpoints for uCore Sovereign Portal & Headless WordPress."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web

from app.identity.wordpress_rbac import get_current_user, get_user_store
from app.portal.portal_store import SUPPORTED_TAXONOMIES, PortalStore, get_portal_store

log = logging.getLogger("ucore.portal.routes")


def _store() -> PortalStore:
    return get_portal_store()


async def _json_object(request: web.Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(reason="Request body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise web.HTTPBadRequest(reason="Request body must be a JSON object")
    return payload


# ── Taxonomies ────────────────────────────────────────────────────────


async def handle_taxonomies_list(_request: web.Request) -> web.Response:
    """GET /api/portal/taxonomies — List all supported taxonomies."""
    taxonomies = [
        {"name": "category", "label": "Categories", "hierarchical": True},
        {"name": "post_tag", "label": "Tags", "hierarchical": False},
        {"name": "udos_group", "label": "uDos Groups", "hierarchical": False},
        {"name": "format", "label": "Post Formats", "hierarchical": False},
    ]
    return web.json_response({"taxonomies": taxonomies})


async def handle_taxonomy_terms_list(request: web.Request) -> web.Response:
    """GET /api/portal/taxonomies/{taxonomy}/terms — List terms for a taxonomy."""
    taxonomy = request.match_info["taxonomy"]
    terms = _store().get_taxonomy_terms(taxonomy)
    return web.json_response({"terms": terms, "taxonomy": taxonomy})


async def handle_taxonomy_term_create(request: web.Request) -> web.Response:
    """POST /api/portal/taxonomies/{taxonomy}/terms — Create a new term."""
    current_user = get_current_user(request)
    user_store = get_user_store()
    if not user_store.has_capability(current_user, "manage_taxonomies"):
        raise web.HTTPForbidden(reason="manage_taxonomies capability required")

    taxonomy = request.match_info["taxonomy"]
    payload = await _json_object(request)
    name = str(payload.get("name", "")).strip()
    if not name:
        raise web.HTTPBadRequest(reason="name is required")
    slug = payload.get("slug")
    description = str(payload.get("description", "")).strip()
    parent = int(payload.get("parent", 0))

    try:
        term = _store().create_taxonomy_term(
            taxonomy=taxonomy,
            name=name,
            slug=slug,
            description=description,
            parent=parent,
        )
        return web.json_response({"term": term}, status=201)
    except ValueError as exc:
        raise web.HTTPBadRequest(reason=str(exc)) from exc


async def handle_taxonomy_term_get(request: web.Request) -> web.Response:
    """GET /api/portal/taxonomies/{taxonomy}/terms/{term_id} — Get single term."""
    taxonomy = request.match_info["taxonomy"]
    term_id = request.match_info["term_id"]
    term = _store().get_taxonomy_term(taxonomy, term_id)
    if term is None:
        raise web.HTTPNotFound(reason="Taxonomy term not found")
    return web.json_response({"term": term})


async def handle_taxonomy_term_delete(request: web.Request) -> web.Response:
    """DELETE /api/portal/taxonomies/{taxonomy}/terms/{term_id} — Delete term."""
    current_user = get_current_user(request)
    user_store = get_user_store()
    if not user_store.has_capability(current_user, "manage_taxonomies"):
        raise web.HTTPForbidden(reason="manage_taxonomies capability required")

    taxonomy = request.match_info["taxonomy"]
    try:
        term_id = int(request.match_info["term_id"])
    except ValueError as exc:
        raise web.HTTPBadRequest(reason="term_id must be an integer") from exc

    deleted = _store().delete_taxonomy_term(taxonomy, term_id)
    if not deleted:
        raise web.HTTPNotFound(reason="Taxonomy term not found")
    return web.json_response({"success": True, "deleted": term_id})


# ── Posts ────────────────────────────────────────────────────────────


async def handle_posts_list(request: web.Request) -> web.Response:
    """GET /api/portal/posts — List posts matching filter and access control."""
    current_user = get_current_user(request)
    status = request.query.get("status")
    category = request.query.get("category")
    tag = request.query.get("tag")
    udos_group = request.query.get("udos_group")
    search = request.query.get("search")
    limit = min(int(request.query.get("limit", request.query.get("per_page", 50))), 100)
    offset = int(request.query.get("offset", 0))

    posts = _store().list_posts(
        user=current_user,
        status=status,
        category=category,
        tag=tag,
        udos_group=udos_group,
        search=search,
        limit=limit,
        offset=offset,
    )
    return web.json_response({"posts": posts, "total": len(posts)})


async def handle_post_create(request: web.Request) -> web.Response:
    """POST /api/portal/posts — Create a new post or page."""
    current_user = get_current_user(request)
    payload = await _json_object(request)

    try:
        post = _store().create_post(payload, current_user)
        return web.json_response({"post": post}, status=201)
    except PermissionError as exc:
        raise web.HTTPForbidden(reason=str(exc)) from exc


async def handle_post_get(request: web.Request) -> web.Response:
    """GET /api/portal/posts/{post_id} — Get post by ID or slug."""
    current_user = get_current_user(request)
    post_id = request.match_info["post_id"]
    post = _store().get_post(post_id, user=current_user)
    if post is None:
        raise web.HTTPNotFound(reason="Post not found or access denied")
    return web.json_response({"post": post})


async def handle_post_update(request: web.Request) -> web.Response:
    """PATCH /api/portal/posts/{post_id} — Update post."""
    current_user = get_current_user(request)
    post_id = request.match_info["post_id"]
    payload = await _json_object(request)

    try:
        post = _store().update_post(post_id, payload, user=current_user)
        if post is None:
            raise web.HTTPNotFound(reason="Post not found")
        return web.json_response({"post": post})
    except PermissionError as exc:
        raise web.HTTPForbidden(reason=str(exc)) from exc


async def handle_post_delete(request: web.Request) -> web.Response:
    """DELETE /api/portal/posts/{post_id} — Delete post or move to trash."""
    current_user = get_current_user(request)
    post_id = request.match_info["post_id"]
    force = request.query.get("force", "").lower() in ("true", "1")

    try:
        deleted = _store().delete_post(post_id, user=current_user, force=force)
        if not deleted:
            raise web.HTTPNotFound(reason="Post not found")
        return web.json_response({"success": True, "deleted": post_id, "force": force})
    except PermissionError as exc:
        raise web.HTTPForbidden(reason=str(exc)) from exc


async def handle_portal_feed(request: web.Request) -> web.Response:
    """GET /api/portal/feed — Public and shared feed for federation / syndication."""
    current_user = get_current_user(request)
    limit = min(int(request.query.get("limit", 20)), 50)
    feed = _store().get_feed(user=current_user, limit=limit)
    return web.json_response({
        "feed": feed,
        "count": len(feed),
        "service": "udos-portal",
    })


def register_routes(app: web.Application) -> None:
    """Register sovereign portal and WordPress REST compatibility routes."""
    # Sovereign Portal API
    app.router.add_get("/api/portal/taxonomies", handle_taxonomies_list)
    app.router.add_get("/api/portal/taxonomies/{taxonomy}/terms", handle_taxonomy_terms_list)
    app.router.add_post("/api/portal/taxonomies/{taxonomy}/terms", handle_taxonomy_term_create)
    app.router.add_get("/api/portal/taxonomies/{taxonomy}/terms/{term_id}", handle_taxonomy_term_get)
    app.router.add_delete("/api/portal/taxonomies/{taxonomy}/terms/{term_id}", handle_taxonomy_term_delete)

    app.router.add_get("/api/portal/posts", handle_posts_list)
    app.router.add_post("/api/portal/posts", handle_post_create)
    app.router.add_get("/api/portal/posts/{post_id}", handle_post_get)
    app.router.add_patch("/api/portal/posts/{post_id}", handle_post_update)
    app.router.add_delete("/api/portal/posts/{post_id}", handle_post_delete)

    app.router.add_get("/api/portal/feed", handle_portal_feed)

    # WordPress REST API compatibility aliases (wp-json/wp/v2)
    app.router.add_get("/wp-json/wp/v2/posts", handle_posts_list)
    app.router.add_post("/wp-json/wp/v2/posts", handle_post_create)
    app.router.add_get("/wp-json/wp/v2/posts/{post_id}", handle_post_get)
    app.router.add_get("/wp-json/wp/v2/categories", handle_taxonomy_terms_list)
    app.router.add_get("/wp-json/wp/v2/tags", handle_taxonomy_terms_list)
