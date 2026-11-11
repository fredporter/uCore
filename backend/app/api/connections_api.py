"""Profile-owned connection setup and the combined local collection."""

from __future__ import annotations

import asyncio
import json
import platform

from aiohttp import web

from app.services.connections.engine import SyncEngine
from app.services.connections.providers import provider_capabilities
from app.services.connections.google_auth import disconnect_credentials, finish, require_direct_google, start
from app.services.connections.reconcile import duplicate_candidates
from app.services.connections.store import CollectionStore
from app.services.identity import get_full_identity


def profile(request):
    identity = get_full_identity()
    if not identity.get("authenticated") or not identity.get("active_profile_id"):
        raise web.HTTPUnauthorized(text="Choose a local user profile first")
    # The caller cannot select another profile through a header or query string.
    if request.method not in {"GET", "HEAD"}:
        origin = request.headers.get("Origin", "")
        from urllib.parse import urlparse

        if origin and urlparse(origin).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise web.HTTPForbidden(text="Local connection setup required")
    return identity["active_profile_id"]


async def state(request):
    owner = profile(request)
    store = CollectionStore()
    records = store.records(owner)
    from app.identity.story_store import IdentityStoryStore

    identity_store = IdentityStoryStore(profile_id=owner)
    setup_state = store.setup(owner)
    story = (
        identity_store.get_story(setup_state.get("story_id", ""))
        if setup_state.get("story_id")
        else None
    )
    from app.services.connections.google_auth import AESGCM, client

    try:
        google_configured = bool(client()) and AESGCM is not None
    except ValueError:
        google_configured = False
    try:
        require_direct_google(owner)
        google_direct_allowed = True
    except PermissionError:
        google_direct_allowed = False
    host_platform = platform.system()
    return web.json_response(
        {
            "providers": {
                "apple": {
                    "available": host_platform == "Darwin",
                    "mode": "local-apps",
                    "capabilities": provider_capabilities("apple", host_platform=host_platform),
                },
                "google": {
                    "available": True,
                    "mode": "direct-cloud",
                    "direct_access_allowed": google_direct_allowed,
                    "capabilities": provider_capabilities("google", host_platform=host_platform),
                },
            },
            "coordinator": "snackbar",
            "setup": setup_state,
            "user_profile": identity_store.get_variables(),
            "setup_story": story,
            "google_auth_configured": google_configured,
            "connections": store.connections(owner),
            "counts": {
                kind: sum(r["kind"] == kind and not r["data"].get("merged_into") for r in records)
                for kind in ["tasks", "contacts", "notes", "calendar", "mail"]
            },
            "pending_exports": store.pending_exports(owner),
            "duplicates": duplicate_candidates(records),
            "conflicts": store.conflicts(owner),
        }
    )


async def setup(request):
    owner, body = profile(request), await request.json()
    if not isinstance(body, dict):
        raise web.HTTPBadRequest(text="Expected setup answers")
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    from app.identity.story_store import IdentityStoryStore
    from app.services.identity import update_profile

    store = CollectionStore()
    previous = store.setup(owner)
    name = str(body.get("display_name", previous.get("display_name", ""))).strip()[:100]
    answers = body.get("answers", {})
    if not isinstance(answers, dict):
        raise web.HTTPBadRequest(text="Expected story answers")
    clean = {
        key: str(value).strip()[:160]
        for key, value in answers.items()
        if key
        in {
            "city",
            "country",
            "locale",
            "host_timezone",
            "start_surface",
            "theme_mode",
            "font_size",
            "location_seeded",
            "location_timezone",
            "country_code",
            "email",
            "default_model",
            "starter_workflow",
        }
    }
    if "grid_location" in answers:
        from app.services.setup_location import seed_readiness

        value = answers["grid_location"]
        maps = seed_readiness()["maps"]
        mapping = next(
            (m for m in maps if isinstance(value, dict) and m["id"] == value.get("map")), None
        )
        if value is not None:
            if not mapping or not all(
                type(value.get(k)) is int and 0 <= value[k] < mapping[bound]
                for k, bound in [("column", "cols"), ("row", "rows")]
            ):
                raise web.HTTPBadRequest(
                    text="Choose a location linked to an installed GridCore map"
                )
            clean["grid_location"] = {
                "map": mapping["id"],
                "column": value["column"],
                "row": value["row"],
                "precision": "place-seed",
                "source": "system-iana-tzdata",
                "format": "ucode-layer-map-v1",
            }
        else:
            clean["grid_location"] = None
    from app.services.workflow_starters import STARTERS

    if clean.get("starter_workflow") and clean["starter_workflow"] not in STARTERS:
        raise web.HTTPBadRequest(text="Choose an available starter workflow")
    if clean.get("email") and (
        "@" not in clean["email"] or any(c.isspace() for c in clean["email"])
    ):
        raise web.HTTPBadRequest(text="Enter an email address or leave it blank")
    if clean.get("host_timezone"):
        try:
            ZoneInfo(clean["host_timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            raise web.HTTPBadRequest(text="Timezone must be a valid host timezone") from None
    if clean.get("start_surface") and clean["start_surface"] not in {
        "workflow",
        "knowledge",
        "ucode",
        "research",
    }:
        raise web.HTTPBadRequest(text="Choose a starting surface")
    try:
        step = max(0, min(int(body.get("step", previous.get("step", 0))), 6))
        if "font_size" in clean and not 12 <= int(clean["font_size"]) <= 24:
            raise ValueError()
    except (ValueError, TypeError):
        raise web.HTTPBadRequest(text="Invalid setup step or text size") from None
    if clean.get("theme_mode") and clean["theme_mode"] not in {"auto", "dark", "light"}:
        raise web.HTTPBadRequest(text="Choose an appearance")
    if body.get("self_contact"):
        contact = store.record(owner, body["self_contact"])
        if not contact or contact["kind"] != "contacts":
            raise web.HTTPBadRequest(text="Choose a contact from this profile")
    completed = bool(body.get("completed", previous.get("completed", False)))
    if completed and not name:
        raise web.HTTPBadRequest(text="Your name is required")
    identity_store = IdentityStoryStore(profile_id=owner)
    story_id = previous.get("story_id")
    if not story_id:
        story_id = identity_store.create_story("user-setup-v4", {"display_name": name})["id"]
    identity_store.update_story(
        story_id,
        step=step,
        status="published" if completed else "in_progress",
        responses={"display_name": name, **clean},
    )
    if completed:
        if clean.get("starter_workflow") and not previous.get("completed"):
            from app.services.workflow_starters import install_starter

            await asyncio.to_thread(install_starter, owner, clean["starter_workflow"])
        update_profile(owner, name=name)
        if "email" in clean:
            from app.services.settings_manager import get_settings_manager

            get_settings_manager().update_scope(
                "user", {"email": clean["email"], "displayName": name}, profile_id=owner
            )
        identity_store.update_variables(
            {
                **{k: v for k, v in clean.items() if k not in {"theme_mode", "font_size"}},
                "timezone_source": "host",
            }
        )
    try:
        return web.json_response(
            store.setup(
                owner,
                {
                    **previous,
                    **body,
                    "display_name": name,
                    "completed": completed,
                    "story_id": story_id,
                    "step": step,
                },
            )
        )
    except ValueError as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None


async def configure(request):
    owner, body = profile(request), await request.json()
    try:
        if body.get("provider") == "google" and body.get("config", {}).get("enabled"):
            require_direct_google(owner)
        if (
            body.get("provider") == "apple"
            and platform.system() != "Darwin"
            and (not body.get("id") or body.get("config", {}).get("enabled"))
        ):
            raise ValueError("Local Apple app connections are available only on macOS")
        return web.json_response(
            CollectionStore().configure(
                owner, body.get("provider"), body.get("config", {}), body.get("id")
            )
        )
    except PermissionError as exc:
        raise web.HTTPForbidden(text=str(exc)) from None
    except (ValueError, TypeError) as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None


async def action(request):
    owner, body = profile(request), await request.json() if request.body_exists else {}
    store = CollectionStore()
    connection = store.connection(owner, request.match_info["connection"])
    if not connection:
        raise web.HTTPNotFound()
    command = request.match_info["action"]
    if command in {"discover", "preview", "sync", "authorize", "link"}:
        if connection["provider"] == "google":
            try:
                require_direct_google(owner)
            except PermissionError as exc:
                raise web.HTTPForbidden(text=str(exc)) from None
        capabilities = provider_capabilities(connection["provider"], host_platform=platform.system())
        if not capabilities["adapter_available"]:
            raise web.HTTPBadRequest(text="Provider adapter is unavailable on this host")
    engine = SyncEngine(store)
    try:
        if command == "discover":
            result = await asyncio.to_thread(
                engine.adapters[connection["provider"]].discover, connection
            )
            store.health(connection["id"], state="scope_required", error="")
            return web.json_response({"collections": result})
        if command == "preview":
            kind = body.get("kind")
            scope = connection["config"]["collections"].get(kind)
            if not scope:
                raise ValueError("Choose a collection first")
            result = await asyncio.to_thread(
                engine.adapters[connection["provider"]].pull, connection, kind, scope
            )
            return web.json_response({"records": result})
        if command == "sync":
            from app.services.snackbar_sync import sync_connection

            return web.json_response(
                await sync_connection(owner, connection["id"], manual=True, store=store)
            )
        if command == "authorize" and connection["provider"] == "google":
            # Fixed loopback destination: never derive OAuth redirects from Host input.
            from app.core.settings import settings

            url = start(
                connection, f"http://127.0.0.1:{settings.port}/api/connections/google/callback"
            )
            opened = False
            if body.get("open_browser"):
                import webbrowser

                opened = await asyncio.to_thread(webbrowser.open, url)
            return web.json_response({"url": url, "opened": opened})
        if command == "disconnect":
            store.configure(
                owner,
                connection["provider"],
                {**connection["config"], "enabled": False},
                connection["id"],
            )
            if connection["provider"] == "google":
                disconnect_credentials(connection)
            store.health(connection["id"], state="disconnected", error="")
            return web.json_response({"state": "disconnected"})
        if command == "link":
            return web.json_response(
                await asyncio.to_thread(
                    engine.link, owner, connection["id"], body.get("record"), body.get("remote")
                )
            )
        if command == "resolve":
            return web.json_response(
                engine.resolve(owner, connection["id"], body.get("remote"), body.get("choice"))
            )
        raise web.HTTPBadRequest(text="Unknown connection action")
    except (ValueError, RuntimeError) as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None


async def callback(request):
    # State is short-lived, one-use, and bound to a profile + connection + PKCE verifier.
    try:
        await asyncio.to_thread(
            finish, request.query.get("state", ""), request.query.get("code", "")
        )
        return web.Response(
            text="Google connected. Return to uCore Settings → Connections to choose lists and enable sync."
        )
    except (ValueError, RuntimeError, PermissionError):
        return web.Response(
            text="Google connection was not completed. Return to Connections and try again.",
            status=400,
        )


async def records(request):
    owner, store = profile(request), CollectionStore()
    if request.method == "GET":
        account = request.query.get("account")
        if not account:
            engine = SyncEngine(store)
            await asyncio.to_thread(engine.refresh_tasks, owner)
            await asyncio.to_thread(engine.refresh_notes, owner)
        items = [
            r
            for r in store.records(owner, request.query.get("kind"))
            if not r["data"].get("merged_into")
        ]
        if request.query.get("id"):
            items = [r for r in items if r["id"] == request.query["id"]]
        import hashlib

        from app.core.settings import settings

        connections = store.connections(owner)
        if account:
            connections = [connection for connection in connections if connection["id"] == account]
            if not connections:
                raise web.HTTPNotFound()
        replicas = {connection["id"]: store.replicas(connection["id"]) for connection in connections}
        if account:
            local_items = {item["id"]: item for item in items}
            return web.json_response({"records": [
                {
                    "id": replica["remote"],
                    "local_record_id": item["id"],
                    "kind": item["kind"],
                    "data": json.loads(replica["base"]),
                }
                for replica in replicas[account]
                if (item := local_items.get(replica["record"])) is not None
            ]})
        sources = {cid: {replica["record"] for replica in rows} for cid, rows in replicas.items()}
        for item in items:
            item["sources"] = [
                {
                    "provider": c["provider"],
                    "account": c["health"].get("account", ""),
                    "connection": c["id"],
                }
                for c in connections
                if item["id"] in sources[c["id"]]
            ]
            if item["kind"] == "notes":
                item["file_path"] = str(
                    settings.vault_root
                    / "Connections"
                    / hashlib.sha256(owner.encode()).hexdigest()[:10]
                    / (item["id"] + ".md")
                )
        return web.json_response({"records": items})
    body = await request.json()
    try:
        if body.get("merge"):
            return web.json_response(
                SyncEngine(store).merge(owner, body["merge"]["keep"], body["merge"]["other"])
            )
        result = store.save(
            owner, body.get("kind"), body.get("data"), body.get("id"), body.get("revision")
        )
        SyncEngine(store).project(owner, result)
        return web.json_response(result)
    except (ValueError, KeyError) as exc:
        raise web.HTTPBadRequest(text=str(exc)) from None


async def setup_locations(request):
    profile(request)
    from app.services.setup_location import location_catalog, seed_readiness, timezone_suggestion

    catalog, readiness = await asyncio.gather(
        asyncio.to_thread(location_catalog), asyncio.to_thread(seed_readiness)
    )
    return web.json_response(
        {
            **catalog,
            "suggestion": timezone_suggestion(request.query.get("timezone", ""), catalog),
            "readiness": readiness,
        }
    )


async def oauth_settings(request):
    """Installation-owned OAuth app configuration; never return credential values."""
    owner = profile(request)
    from app.core.settings import settings
    from app.services.connections import google_auth

    if request.method == "POST":
        try:
            require_direct_google(owner, administrator=True)
        except PermissionError as exc:
            raise web.HTTPForbidden(text=str(exc)) from None
        if google_auth.AESGCM is None:
            raise web.HTTPBadRequest(text="Encrypted credential storage is required")
        body = await request.json()
        if not isinstance(body, dict):
            raise web.HTTPBadRequest(text="Expected OAuth app settings")
        import re

        cid = str(body.get("client_id", "")).strip()
        secret = str(body.get("client_secret", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]+[.]apps[.]googleusercontent[.]com", cid):
            raise web.HTTPBadRequest(text="Enter a Google Desktop app client ID")
        if len(secret) > 4096:
            raise web.HTTPBadRequest(text="Client secret is too long")
        vault = google_auth.get_store()
        try:
            previous = google_auth.client()
        except ValueError:
            previous = {}
        if previous.get("client_id") and previous["client_id"] != cid:
            raise web.HTTPBadRequest(
                text="A different OAuth app is already configured. Manage replacement in Advanced Secrets and reconnect accounts."
            )
        vault.set("GOOGLE_OAUTH_CLIENT_ID", cid)
        if secret:
            vault.set("GOOGLE_OAUTH_CLIENT_SECRET", secret)
        vault.save()
    try:
        configured = google_auth.client()
    except ValueError:
        configured = {}
    return web.json_response(
        {
            "configured": bool(configured) and google_auth.AESGCM is not None,
            "client_id_present": bool(configured.get("client_id")),
            "client_secret_present": bool(configured.get("client_secret")),
            "encrypted_storage": google_auth.AESGCM is not None,
            "callback": f"http://127.0.0.1:{settings.port}/api/connections/google/callback",
        }
    )


def register(app):
    from app.api.apps_api import register as register_apps

    register_apps(app)
    app.router.add_get("/api/connections/oauth-settings", oauth_settings)
    app.router.add_post("/api/connections/oauth-settings", oauth_settings)
    app.router.add_get("/api/connections", state)
    app.router.add_post("/api/connections", configure)
    app.router.add_post("/api/connections/setup", setup)
    app.router.add_get("/api/connections/setup/locations", setup_locations)
    app.router.add_get("/api/connections/records", records)
    app.router.add_post("/api/connections/records", records)
    app.router.add_get("/api/connections/google/callback", callback)
    app.router.add_post("/api/connections/{connection}/{action}", action)
