"""Settings app inventory and Snackbar-owned local exchange endpoints."""

from aiohttp import web

from app.services.connections.store import CollectionStore


def owner(request):
    from app.api.connections_api import profile

    return profile(request)


async def apps(request):
    owner(request)
    from app.services.app_catalog import catalog

    return web.json_response(catalog())


async def sync_status(request):
    profile = owner(request)
    return web.json_response(
        {
            "coordinator": "snackbar",
            "connections": CollectionStore().connections(profile),
            "browser_mode": "manual-file-exchange",
        }
    )


async def sync_run(request):
    profile = owner(request)
    body = await request.json()
    if not isinstance(body, dict):
        raise web.HTTPBadRequest(text="Expected an object")
    from app.services.snackbar_sync import sync_connection

    try:
        return web.json_response(
            await sync_connection(profile, body.get("connection", ""), manual=True)
        )
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None


async def browser_import(request):
    profile = owner(request)
    body = await request.json()
    if not isinstance(body, dict):
        raise web.HTTPBadRequest(text="Expected an object")
    import asyncio

    from app.services.browser_library import import_html

    try:
        return web.json_response(
            await asyncio.to_thread(
                import_html,
                CollectionStore(),
                profile,
                body.get("html"),
                body.get("source", "browser"),
                body.get("selection", "all"),
            )
        )
    except (ValueError, TypeError) as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None


async def browser_export(request):
    profile = owner(request)
    from app.services.browser_library import export_html

    return web.Response(
        text=export_html(CollectionStore().records(profile)),
        content_type="text/html",
        headers={
            "Content-Disposition": 'attachment; filename="udos-bookmarks.html"',
            "Content-Security-Policy": "default-src 'none'",
        },
    )


def register(app):
    app.router.add_get("/api/apps", apps)
    app.router.add_get("/api/snackbar/sync", sync_status)
    app.router.add_post("/api/snackbar/sync", sync_run)
    app.router.add_post("/api/snackbar/sync/browser/import", browser_import)
    app.router.add_get("/api/snackbar/sync/browser/export", browser_export)
