"""Local endpoints for code-only NFC fixtures."""
from __future__ import annotations

import math
import re

from aiohttp import web

from app.services.spatial_service import get_spatial_service

from .connections_api import profile

_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}")


async def _read_object(request: web.Request) -> dict:
    try:
        payload = await request.json()
    except (ValueError, UnicodeError):
        raise web.HTTPBadRequest(text="Invalid JSON object") from None
    if not isinstance(payload, dict):
        raise web.HTTPBadRequest(text="Invalid JSON object")
    return payload


def _identifier(value: object) -> bool:
    return isinstance(value, str) and _IDENTIFIER.fullmatch(value) is not None


async def handle_spatial_tap(request: web.Request) -> web.Response:
    """Resolve a simulated tap against fixture permissions for the active profile."""
    owner = profile(request)
    payload = await _read_object(request)
    envelope = payload.get("marker_envelope")
    event_id = payload.get("event_id")
    position = payload.get("simulated_position")

    if not _identifier(event_id) or (
        not isinstance(envelope, dict) or set(envelope) != {"version", "marker_id"}
        or envelope["version"] != "1.0" or not _identifier(envelope["marker_id"])
    ):
        raise web.HTTPBadRequest(text="Invalid tap event or marker envelope")

    if position is not None and (
        not isinstance(position, dict) or set(position) != {"lat", "lon"}
        or not all(
            type(position[key]) in {int, float} and -bound <= position[key] <= bound
            for key, bound in (("lat", 90), ("lon", 180))
        )
    ):
        raise web.HTTPBadRequest(text="Invalid simulated position")

    receipt = get_spatial_service().resolve_tap(owner, event_id, envelope, position)
    return web.json_response(receipt, status=200 if receipt["outcome"] == "success" else 403)


async def handle_spatial_handshake_challenge(request: web.Request) -> web.Response:
    """Issue a challenge for the simulated peer exchange."""
    profile(request)
    body = await _read_object(request)
    peer = body.get("peer_id")
    audience = body.get("audience")
    if not _identifier(peer) or not _identifier(audience):
        raise web.HTTPBadRequest(text="Invalid peer or audience")
    return web.json_response(get_spatial_service().generate_handshake_challenge(peer, audience))


async def handle_spatial_handshake_verify(request: web.Request) -> web.Response:
    """Verify a simulated peer response without granting library access."""
    profile(request)
    body = await _read_object(request)
    fields = ("peer_id", "audience", "nonce", "signature", "protocol_version")
    expiry = body.get("expiry")
    if not all(_identifier(body.get(field)) for field in fields) or (
        type(expiry) not in {int, float} or not 0 < expiry < 10**12 or not math.isfinite(expiry)
    ):
        raise web.HTTPBadRequest(text="Invalid peer response")

    result = get_spatial_service().verify_handshake_response(
        **{field: body[field] for field in fields}, expiry=expiry,
    )
    return web.json_response(result, status=200 if result["outcome"] == "accepted" else 403)
