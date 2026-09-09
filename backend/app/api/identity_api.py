"""Identity API — uDos Identity System endpoints.

Spec: UDN-IDENTITY-API-001
"""
from __future__ import annotations

from aiohttp import web

from app.services.identity import (
    ensure_identity,
    get_full_identity,
    load_identity,
    login,
    logout,
    save_identity,
    switch_profile,
    update_profile,
)


async def handle_get_identity(request: web.Request) -> web.Response:
    """GET /api/identity — Return full identity info."""
    identity = get_full_identity()
    resp = web.json_response(identity)
    # Identity headers for downstream routing
    resp.headers["X-Udos-User"] = identity.get("user_id", "")
    resp.headers["X-Udos-Install"] = identity.get("install_id", "")
    resp.headers["X-Udos-Session"] = identity.get("session_id", "")
    resp.headers["X-Udos-Profile"] = identity.get("active_profile_id", "")
    return resp


async def handle_init_identity(request: web.Request) -> web.Response:
    """POST /api/identity/init — Initialize or re-initialize identity."""
    body = await request.json() if request.can_read_body else {}
    identity = load_identity()

    if identity.is_valid() and not body.get("force"):
        return web.json_response({
            "success": True,
            "message": "Identity already exists",
            "identity": identity.to_dict(),
        })

    ensure_identity()
    identity = load_identity()
    return web.json_response({
        "success": True,
        "message": "Identity initialized",
        "identity": identity.to_dict(),
    })


async def handle_set_codeword(request: web.Request) -> web.Response:
    """POST /api/identity/codeword — Set a friendly codeword for this device."""
    body = await request.json() if request.can_read_body else {}
    codeword = (body.get("codeword") or "").strip()
    if not codeword:
        return web.json_response({"success": False, "error": "codeword is required"}, status=400)

    identity = load_identity()
    identity.codeword = codeword
    save_identity(identity)

    return web.json_response({"success": True, "codeword": codeword})


async def handle_switch_profile(request: web.Request) -> web.Response:
    """POST /api/identity/switch — Switch to another local profile."""
    body = await request.json() if request.can_read_body else {}
    profile_id = (body.get("profile_id") or body.get("profileId") or "").strip()
    if not profile_id:
        return web.json_response({"success": False, "error": "profile_id is required"}, status=400)

    updated = switch_profile(profile_id)
    return web.json_response({"success": True, "identity": updated})


async def handle_logout(request: web.Request) -> web.Response:
    """POST /api/identity/logout — Clear session to enter unauthenticated state."""
    updated = logout()
    return web.json_response({"success": True, "identity": updated})


async def handle_login(request: web.Request) -> web.Response:
    """POST /api/identity/login — Log in to specified profile."""
    body = await request.json() if request.can_read_body else {}
    profile_id = (body.get("profile_id") or body.get("profileId") or "default").strip()
    updated = login(profile_id)
    return web.json_response({"success": True, "identity": updated})


async def handle_update_profile(request: web.Request) -> web.Response:
    """POST /api/identity/profile — Create or update profile metadata."""
    body = await request.json() if request.can_read_body else {}
    profile_id = (body.get("profile_id") or body.get("profileId") or "").strip()
    if not profile_id:
        return web.json_response({"success": False, "error": "profile_id is required"}, status=400)
    name = body.get("name")
    role = body.get("role")
    updated = update_profile(profile_id, name=name, role=role)
    return web.json_response({"success": True, "identity": updated})


def register_identity_routes(app: web.Application) -> None:
    """Register identity API routes."""
    app.router.add_get("/api/identity", handle_get_identity)
    app.router.add_get("/api/identity/me", handle_get_identity)
    app.router.add_post("/api/identity/init", handle_init_identity)
    app.router.add_post("/api/identity/codeword", handle_set_codeword)
    app.router.add_post("/api/identity/switch", handle_switch_profile)
    app.router.add_post("/api/identity/logout", handle_logout)
    app.router.add_post("/api/identity/login", handle_login)
    app.router.add_post("/api/identity/profile", handle_update_profile)
