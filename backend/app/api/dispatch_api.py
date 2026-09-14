"""Dispatch API — Sovereign communication, interactive story tokens, and device calculation.

POST /api/dispatch/create            — create a dispatch and stage an ephemeral token
GET  /api/dispatch/token/{token}     — load story document for guest token
POST /api/dispatch/rsvp/{token}      — submit guest RSVP / responses
GET  /api/dispatch/preview-email/{id} — render bulletproof single-column Prose HTML email
GET  /api/dispatch/responses/{id}    — get collected responses for host
POST /api/dispatch/calculate-display — calculate grid & prose capabilities for a viewport
POST /api/dispatch/calculate-storage — calculate vault knowledge & capsule capacity
GET  /api/dispatch/asset/{id}/{file} — serve preserved original asset
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

from aiohttp import web

from app.services.device_calc import calc_display_capability, calc_storage_capacity
from app.services.dispatch_store import dispatch_store
from app.services.email_dispatch import compile_prose_email

log = logging.getLogger("ucore.dispatch_api")


async def handle_create_dispatch(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    title = data.get("title", "").strip()
    if not title:
        return web.json_response({"error": "Title is required"}, status=400)

    story_md = data.get("story_markdown", "").strip()
    lead_text = data.get("lead_text", "").strip()
    burn_after_read = bool(data.get("burn_after_read", False))
    expires_in = data.get("expires_in_seconds")
    mode_default = data.get("mode_default", "card")
    binder_id = data.get("binder_id")
    hero_gif_name = data.get("hero_gif_name")

    hero_gif_bytes = None
    if data.get("hero_gif_base64"):
        try:
            hero_gif_bytes = base64.b64decode(data["hero_gif_base64"])
        except Exception as exc:
            log.warning("Invalid base64 in hero_gif: %s", exc)

    manifest = dispatch_store.create_dispatch(
        title=title,
        story_markdown=story_md,
        lead_text=lead_text,
        hero_gif_bytes=hero_gif_bytes,
        hero_gif_name=hero_gif_name,
        expires_in_seconds=int(expires_in) if expires_in else None,
        burn_after_read=burn_after_read,
        mode_default=mode_default,
        binder_id=binder_id,
    )

    return web.json_response({
        "status": "ok",
        "dispatch": manifest,
        "token": manifest["token"],
        "story_url": f"/p/{manifest['token']}",
    })


async def handle_get_by_token(request: web.Request) -> web.Response:
    token = request.match_info.get("token", "").strip()
    if not token:
        return web.json_response({"error": "Token is required"}, status=400)

    record = dispatch_store.get_dispatch_by_token(token)
    if record.get("status") == "not_found":
        return web.json_response(record, status=404)

    return web.json_response(record)


async def handle_submit_rsvp(request: web.Request) -> web.Response:
    token = request.match_info.get("token", "").strip()
    if not token:
        return web.json_response({"error": "Token is required"}, status=400)

    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    result = dispatch_store.submit_rsvp(token, payload)
    if result.get("status") == "not_found":
        return web.json_response(result, status=404)
    if result.get("status") in ("expired", "burned"):
        return web.json_response(result, status=410)

    return web.json_response(result)


async def handle_preview_email(request: web.Request) -> web.Response:
    dispatch_id = request.match_info.get("id", "").strip()
    dispatch_dir = dispatch_store.root_dir / dispatch_id
    manifest_path = dispatch_dir / "dispatch.json"

    if not manifest_path.exists():
        return web.Response(text="Dispatch not found", status=404)

    import json
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    story_path = dispatch_dir / "originals" / "source.story.md"
    story_md = story_path.read_text(encoding="utf-8") if story_path.exists() else ""

    token = manifest.get("token", "")
    action_url = f"/p/{token}"
    hero_src = manifest.get("hero_asset")

    html_email = compile_prose_email(
        title=manifest.get("title", "Sovereign Dispatch"),
        lead_text=manifest.get("lead_text", ""),
        body_html=f"<p>{story_md[:400]}...</p>" if len(story_md) > 400 else f"<p>{story_md}</p>",
        action_label="Open Interactive Story",
        action_url=action_url,
        hero_gif_src=hero_src,
        theme="dark",
    )

    return web.Response(text=html_email, content_type="text/html")


async def handle_get_responses(request: web.Request) -> web.Response:
    dispatch_id = request.match_info.get("id", "").strip()
    responses = dispatch_store.get_responses(dispatch_id)
    return web.json_response({"id": dispatch_id, "responses": responses})


async def handle_calculate_display(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    w = int(data.get("width", 1920))
    h = int(data.get("height", 1080))
    dev_type = data.get("device_type")
    res = calc_display_capability(w, h, dev_type)
    return web.json_response(res)


async def handle_calculate_storage(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    total_bytes = int(data.get("total_bytes", 4_000_000_000))
    sys_bytes = data.get("sys_bytes")
    res = calc_storage_capacity(total_bytes, int(sys_bytes) if sys_bytes is not None else None)
    return web.json_response(res)


async def handle_serve_asset(request: web.Request) -> web.Response:
    dispatch_id = request.match_info.get("id", "").strip()
    filename = request.match_info.get("file", "").strip()

    # Prevent traversal
    if ".." in dispatch_id or ".." in filename or "/" in filename or "\\" in filename:
        return web.Response(text="Forbidden", status=403)

    target_file = dispatch_store.root_dir / dispatch_id / "originals" / filename
    if not target_file.exists() or not target_file.is_file():
        return web.Response(text="Asset not found", status=404)

    content_type = "image/gif" if filename.endswith(".gif") else "application/octet-stream"
    return web.Response(body=target_file.read_bytes(), content_type=content_type)


async def handle_get_catalog(request: web.Request) -> web.Response:
    catalog = dispatch_store.load_catalog()
    return web.json_response(catalog)


async def handle_get_by_binder(request: web.Request) -> web.Response:
    binder_id = request.match_info.get("binder_id", "").strip()
    dispatches = dispatch_store.get_dispatches_by_binder(binder_id)
    return web.json_response({"binder_id": binder_id, "dispatches": dispatches})


async def handle_serve_catalog_asset(request: web.Request) -> web.Response:
    filename = request.match_info.get("file", "").strip()
    if ".." in filename or "/" in filename or "\\" in filename:
        return web.Response(text="Forbidden", status=403)

    from app.core.settings import settings
    target_file = settings.public_vault_root / "global-knowledge" / "elements" / filename
    if not target_file.exists() or not target_file.is_file():
        # Fallback 1x1 transparent gif if asset not present
        transparent_gif_1x1 = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        return web.Response(body=transparent_gif_1x1, content_type="image/gif")

    content_type = "image/gif" if filename.endswith(".gif") else "image/svg+xml"
    return web.Response(body=target_file.read_bytes(), content_type=content_type)


async def handle_get_feed_rss(request: web.Request) -> web.Response:
    host_url = f"{request.scheme}://{request.host}"
    from app.services.dispatch_feed import dispatch_feed_service
    rss_xml = dispatch_feed_service.generate_rss_2_0(host_url)
    return web.Response(text=rss_xml, content_type="application/rss+xml")


async def handle_get_feed_json(request: web.Request) -> web.Response:
    host_url = f"{request.scheme}://{request.host}"
    from app.services.dispatch_feed import dispatch_feed_service
    json_feed = dispatch_feed_service.generate_json_feed(host_url)
    return web.json_response(json_feed)


async def handle_get_motifs(request: web.Request) -> web.Response:
    import sys
    uvector_py = Path(__file__).resolve().parents[4] / "uVector" / "python"
    if uvector_py.exists() and str(uvector_py) not in sys.path:
        sys.path.insert(0, str(uvector_py))

    try:
        from uvector_bob import MOTIF_PRESETS
        return web.json_response({"status": "ok", "motifs": MOTIF_PRESETS})
    except Exception as exc:
        log.warning("Could not load uVector motifs: %s", exc)
        return web.json_response({"status": "ok", "motifs": {}})


async def handle_generate_bob(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    motif = data.get("motif", "zen_envelope")
    palette_id = data.get("palette_id", "teletext_ceefax")
    steps = int(data.get("steps", 4))
    delay_ms = int(data.get("delay_ms", 100))

    import sys
    uvector_py = Path(__file__).resolve().parents[4] / "uVector" / "python"
    if uvector_py.exists() and str(uvector_py) not in sys.path:
        sys.path.insert(0, str(uvector_py))

    try:
        from uvector_bob import compile_svg_to_bob, compile_svgs_to_gif, generate_vector_motif
        frames = generate_vector_motif(motif, palette_id=palette_id, steps=steps)
        gif_bytes = compile_svgs_to_gif(frames, delay_ms=delay_ms, palette_id=palette_id)
        bob_def = compile_svg_to_bob(frames[0], id=f"bob_{motif}", name=f"{motif.title()} BOB", palette_id=palette_id)

        from app.core.settings import settings
        asset_name = f"bob-{motif}-{palette_id}.gif"
        elements_dir = settings.public_vault_root / "global-knowledge" / "elements"
        elements_dir.mkdir(parents=True, exist_ok=True)
        (elements_dir / asset_name).write_bytes(gif_bytes)

        return web.json_response({
            "status": "ok",
            "asset_name": asset_name,
            "asset_url": f"/api/dispatch/catalog/asset/{asset_name}",
            "gif_size_bytes": len(gif_bytes),
            "bob_definition": bob_def,
        })
    except Exception as exc:
        log.error("Failed to generate BOB: %s", exc)
        return web.json_response({"error": str(exc)}, status=500)


async def handle_ingest_inbound(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    token = data.get("token")
    if not token:
        return web.json_response({"error": "Token is required in response payload"}, status=400)

    res = dispatch_store.submit_rsvp(token, data)
    return web.json_response(res)


async def handle_export_offline(request: web.Request) -> web.Response:
    dispatch_id = request.match_info.get("id", "").strip()
    from app.services.dispatch_offline import export_offline_bundle
    try:
        result = export_offline_bundle(dispatch_id)
        return web.json_response(result)
    except Exception as exc:
        log.error("Offline export failed for %s: %s", dispatch_id, exc)
        return web.json_response({"error": str(exc)}, status=400)


def register_dispatch_routes(app: web.Application) -> None:
    """Register all dispatch, feed, and device capability routes."""
    app.router.add_post("/api/dispatch/create", handle_create_dispatch)
    app.router.add_get("/api/dispatch/token/{token}", handle_get_by_token)
    app.router.add_post("/api/dispatch/rsvp/{token}", handle_submit_rsvp)
    app.router.add_get("/api/dispatch/preview-email/{id}", handle_preview_email)
    app.router.add_get("/api/dispatch/responses/{id}", handle_get_responses)
    app.router.add_post("/api/dispatch/calculate-display", handle_calculate_display)
    app.router.add_post("/api/dispatch/calculate-storage", handle_calculate_storage)
    app.router.add_get("/api/dispatch/asset/{id}/{file}", handle_serve_asset)
    app.router.add_get("/api/dispatch/catalog", handle_get_catalog)
    app.router.add_get("/api/dispatch/catalog/asset/{file}", handle_serve_catalog_asset)
    app.router.add_get("/api/dispatch/by-binder/{binder_id}", handle_get_by_binder)
    app.router.add_get("/api/dispatch/feed.xml", handle_get_feed_rss)
    app.router.add_get("/api/dispatch/feed.json", handle_get_feed_json)
    app.router.add_get("/api/dispatch/motifs", handle_get_motifs)
    app.router.add_post("/api/dispatch/generate-bob", handle_generate_bob)
    app.router.add_post("/api/dispatch/inbox/ingest", handle_ingest_inbound)
    app.router.add_post("/api/dispatch/export-offline/{id}", handle_export_offline)


