"""Route registrar for uCore internal identity subsystem."""

from __future__ import annotations

from datetime import datetime

from aiohttp import web

from app.services.identity import get_full_identity, get_or_create_session

from .story_store import IdentityStoryStore
from .wordpress_mapper import map_from_wordpress, map_to_wordpress

STORY_STATUSES = {"draft", "in_progress", "review", "published", "archived"}
VISIBILITIES = {"private", "shared", "public"}


def _store() -> IdentityStoryStore:
    return IdentityStoryStore()


async def _json_object(request: web.Request) -> dict:
    try:
        payload = await request.json()
    except Exception as exc:
        raise web.HTTPBadRequest(reason="Request body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise web.HTTPBadRequest(reason="Request body must be a JSON object")
    return payload


async def handle_identity_plugin_profile(_request: web.Request) -> web.Response:
    """GET /api/identity/plugin/profile."""
    identity = get_full_identity()
    return web.json_response(
        {
            "plugin": "udos-identity",
            "identity": identity,
        }
    )


async def handle_identity_plugin_session(_request: web.Request) -> web.Response:
    """GET /api/identity/plugin/session."""
    session = get_or_create_session().to_dict()
    return web.json_response(
        {
            "plugin": "udos-identity",
            "session": session,
        }
    )


async def handle_profile_variables_get(_request: web.Request) -> web.Response:
    """GET /api/identity/variables."""
    variables = _store().get_variables()
    return web.json_response({"variables": variables})


async def handle_profile_variables_put(request: web.Request) -> web.Response:
    """PUT /api/identity/variables."""
    payload = await _json_object(request)
    variables = payload.get("variables", payload)
    if not isinstance(variables, dict):
        raise web.HTTPBadRequest(reason="variables must be a JSON object")
    updated = _store().update_variables(variables)
    return web.json_response({"variables": updated})


async def handle_story_create(request: web.Request) -> web.Response:
    """POST /api/identity/stories."""
    payload = await _json_object(request)
    form_id = str(payload.get("form_id", "")).strip()
    responses = payload.get("responses", {})
    if not form_id:
        raise web.HTTPBadRequest(reason="form_id is required")
    if not isinstance(responses, dict):
        raise web.HTTPBadRequest(reason="responses must be a JSON object")
    story = _store().create_story(form_id, responses)
    return web.json_response({"story": story}, status=201)


async def handle_story_get(request: web.Request) -> web.Response:
    """GET /api/identity/stories/{story_id}."""
    story = _store().get_story(request.match_info["story_id"])
    if story is None:
        raise web.HTTPNotFound(reason="Story not found")
    return web.json_response({"story": story})


async def handle_story_update(request: web.Request) -> web.Response:
    """PATCH /api/identity/stories/{story_id}."""
    payload = await _json_object(request)
    step = payload.get("step")
    status = payload.get("status")
    responses = payload.get("responses")

    if step is not None and (not isinstance(step, int) or step < 0):
        raise web.HTTPBadRequest(reason="step must be a non-negative integer")
    if status is not None and status not in STORY_STATUSES:
        raise web.HTTPBadRequest(reason="status is invalid")
    if responses is not None and not isinstance(responses, dict):
        raise web.HTTPBadRequest(reason="responses must be a JSON object")

    story = _store().update_story(
        request.match_info["story_id"],
        step=step,
        status=status,
        responses=responses,
    )
    if story is None:
        raise web.HTTPNotFound(reason="Story not found")
    return web.json_response({"story": story})


async def handle_privacy_get(request: web.Request) -> web.Response:
    """GET /api/identity/privacy/{resource_id}."""
    policy = _store().get_privacy(request.match_info["resource_id"])
    return web.json_response({"policy": policy})


async def handle_privacy_put(request: web.Request) -> web.Response:
    """PUT /api/identity/privacy/{resource_id}."""
    payload = await _json_object(request)
    visibility = str(payload.get("visibility", "")).strip()
    expires_at = payload.get("expires_at")
    if visibility not in VISIBILITIES:
        raise web.HTTPBadRequest(reason="visibility must be private, shared, or public")
    if expires_at is not None:
        if not isinstance(expires_at, str):
            raise web.HTTPBadRequest(reason="expires_at must be an ISO-8601 string or null")
        try:
            datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise web.HTTPBadRequest(reason="expires_at must be valid ISO-8601") from exc
    policy = _store().set_privacy(
        request.match_info["resource_id"],
        visibility=visibility,
        expires_at=expires_at,
    )
    return web.json_response({"policy": policy})


async def handle_wordpress_map_outbound(request: web.Request) -> web.Response:
    """POST /api/identity/wordpress/map-outbound."""
    payload = await _json_object(request)
    profile = payload.get("profile", {})
    variables = payload.get("variables", {})
    groups = payload.get("groups", [])
    if not isinstance(profile, dict):
        raise web.HTTPBadRequest(reason="profile must be a JSON object")
    if not isinstance(variables, dict):
        raise web.HTTPBadRequest(reason="variables must be a JSON object")
    if not isinstance(groups, list):
        raise web.HTTPBadRequest(reason="groups must be a JSON array")
    mapping = map_to_wordpress(profile=profile, variables=variables, groups=groups)
    return web.json_response({"wordpress": mapping})


async def handle_wordpress_map_inbound(request: web.Request) -> web.Response:
    """POST /api/identity/wordpress/map-inbound."""
    payload = await _json_object(request)
    mapping = map_from_wordpress(payload)
    return web.json_response({"identity": mapping})


async def handle_roles_list(_request: web.Request) -> web.Response:
    """GET /api/identity/roles."""
    from .wordpress_rbac import ROLE_CAPABILITIES
    roles = [
        {"role": role, "capabilities": sorted(caps)}
        for role, caps in ROLE_CAPABILITIES.items()
    ]
    return web.json_response({"roles": roles})


async def handle_users_list(request: web.Request) -> web.Response:
    """GET /api/identity/users."""
    from .wordpress_rbac import get_current_user, get_user_store
    current_user = get_current_user(request)
    store = get_user_store()
    role_filter = request.query.get("role")

    if not store.has_capability(current_user, "manage_users"):
        users = store.list_users(role=role_filter)
        safe_users = [
            {"id": u["id"], "username": u["username"], "display_name": u["display_name"], "role": u["role"]}
            for u in users
        ]
        return web.json_response({"users": safe_users})

    users = store.list_users(role=role_filter)
    return web.json_response({"users": users})


async def handle_users_create(request: web.Request) -> web.Response:
    """POST /api/identity/users."""
    from .wordpress_rbac import get_current_user, get_user_store
    current_user = get_current_user(request)
    store = get_user_store()
    if not store.has_capability(current_user, "manage_users"):
        raise web.HTTPForbidden(reason="manage_users capability required")

    payload = await _json_object(request)
    username = str(payload.get("username", "")).strip()
    if not username:
        raise web.HTTPBadRequest(reason="username is required")
    display_name = str(payload.get("display_name", "")).strip() or username
    email = str(payload.get("email", "")).strip()
    role = str(payload.get("role", "subscriber")).strip()
    meta = payload.get("meta") or {}

    user = store.create_user(
        username=username,
        display_name=display_name,
        email=email,
        role=role,
        meta=meta,
    )
    return web.json_response({"user": user}, status=201)


async def handle_user_get(request: web.Request) -> web.Response:
    """GET /api/identity/users/{user_id}."""
    from .wordpress_rbac import get_current_user, get_user_store
    current_user = get_current_user(request)
    store = get_user_store()
    target_id = request.match_info["user_id"]
    user = store.get_user(target_id)
    if user is None:
        raise web.HTTPNotFound(reason="User not found")
    if current_user.get("id") != target_id and not store.has_capability(current_user, "manage_users"):
        return web.json_response({
            "user": {
                "id": user["id"],
                "username": user["username"],
                "display_name": user["display_name"],
                "role": user["role"],
            }
        })
    return web.json_response({"user": user})


async def handle_user_update(request: web.Request) -> web.Response:
    """PATCH /api/identity/users/{user_id}."""
    from .wordpress_rbac import get_current_user, get_user_store
    current_user = get_current_user(request)
    store = get_user_store()
    target_id = request.match_info["user_id"]
    is_self = current_user.get("id") == target_id
    is_admin = store.has_capability(current_user, "manage_users")
    if not (is_self or is_admin):
        raise web.HTTPForbidden(reason="Permission denied")

    payload = await _json_object(request)
    role = payload.get("role")
    if role is not None and not is_admin:
        raise web.HTTPForbidden(reason="Changing role requires manage_users capability")

    display_name = payload.get("display_name")
    email = payload.get("email")
    meta = payload.get("meta")

    updated = store.update_user(
        target_id,
        display_name=display_name,
        email=email,
        role=role,
        meta=meta,
    )
    if updated is None:
        raise web.HTTPNotFound(reason="User not found")
    return web.json_response({"user": updated})


async def handle_user_delete(request: web.Request) -> web.Response:
    """DELETE /api/identity/users/{user_id}."""
    from .wordpress_rbac import get_current_user, get_user_store
    current_user = get_current_user(request)
    store = get_user_store()
    if not store.has_capability(current_user, "manage_users"):
        raise web.HTTPForbidden(reason="manage_users capability required")

    target_id = request.match_info["user_id"]
    deleted = store.delete_user(target_id)
    if not deleted:
        raise web.HTTPBadRequest(reason="Cannot delete user (user not found or sovereign owner)")
    return web.json_response({"success": True, "deleted": target_id})


async def handle_user_capabilities(request: web.Request) -> web.Response:
    """GET /api/identity/users/me/capabilities."""
    from .wordpress_rbac import get_current_user
    current_user = get_current_user(request)
    return web.json_response({
        "user_id": current_user.get("id"),
        "role": current_user.get("role"),
        "capabilities": current_user.get("capabilities", []),
    })


def register_routes(app: web.Application) -> None:
    """Register identity subsystem routes."""
    app.router.add_get("/api/identity/plugin/profile", handle_identity_plugin_profile)
    app.router.add_get("/api/identity/plugin/session", handle_identity_plugin_session)
    app.router.add_get("/api/identity/variables", handle_profile_variables_get)
    app.router.add_put("/api/identity/variables", handle_profile_variables_put)
    app.router.add_post("/api/identity/stories", handle_story_create)
    app.router.add_get("/api/identity/stories/{story_id}", handle_story_get)
    app.router.add_patch("/api/identity/stories/{story_id}", handle_story_update)
    app.router.add_get("/api/identity/privacy/{resource_id}", handle_privacy_get)
    app.router.add_put("/api/identity/privacy/{resource_id}", handle_privacy_put)
    app.router.add_post(
        "/api/identity/wordpress/map-outbound",
        handle_wordpress_map_outbound,
    )
    app.router.add_post(
        "/api/identity/wordpress/map-inbound",
        handle_wordpress_map_inbound,
    )

    # Sovereign WordPress RBAC & User Management (Milestone P8)
    app.router.add_get("/api/identity/roles", handle_roles_list)
    app.router.add_get("/api/identity/users", handle_users_list)
    app.router.add_post("/api/identity/users", handle_users_create)
    app.router.add_get("/api/identity/users/me/capabilities", handle_user_capabilities)
    app.router.add_get("/api/identity/users/{user_id}", handle_user_get)
    app.router.add_patch("/api/identity/users/{user_id}", handle_user_update)
    app.router.add_delete("/api/identity/users/{user_id}", handle_user_delete)

