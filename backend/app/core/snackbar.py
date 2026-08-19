from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import pkgutil
import platform as plat_module
import socket
import sys
import time
import urllib.request
from contextlib import suppress
from pathlib import Path

from .logging import log
from .settings import settings

try:
    import yaml
except ImportError:
    yaml = None

try:
    from aiohttp import web
except ImportError:
    log.error("aiohttp required: pip install aiohttp")
    sys.exit(1)

# AppKey instances (avoids NotAppKeyWarning)
BUDGET_MANAGER_KEY = web.AppKey("budget_manager", object)
MAINTENANCE_SCHEDULER_KEY = web.AppKey("maintenance_scheduler", object)


# ─── Helpers ──────────────────────────────────────────────────────


def _load_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _health_is_ready(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/health", timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False


async def _idle_forever() -> None:
    while True:
        await asyncio.sleep(60)


# ─── CORS middleware ──────────────────────────────────────────────


@web.middleware
async def cors_middleware(request: web.Request, handler):
    try:
        if request.method == "OPTIONS":
            response = web.Response()
        else:
            response = await handler(request)
    except web.HTTPException as exc:
        # Catch HTTP errors (404, 405, etc.) so CORS headers are added
        response = exc
    except Exception:
        raise
    if settings.enable_cors:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@web.middleware
async def budget_middleware(request: web.Request, handler):
    """Budget guard for costly API endpoints with usage logging."""
    manager = request.app.get("budget_manager")
    if manager is None:
        return await handler(request)

    path = request.path
    try:
        guarded = manager.policy.guarded_endpoints
    except AttributeError:
        guarded = []
    if path not in guarded:
        return await handler(request)

    estimated_cost = manager.estimate_for_path(path)

    provider = request.headers.get("X-Provider", "").strip()
    model = request.headers.get("X-Model", "").strip()
    if not provider or not model:
        payload = {}
        if request.can_read_body:
            with suppress(Exception):
                payload = await request.json()
        if isinstance(payload, dict):
            if not provider:
                provider = str(
                    payload.get("provider")
                    or payload.get("vendor")
                    or payload.get("engine")
                    or "",
                ).strip()
            if not model:
                params = payload.get("params")
                if isinstance(params, dict):
                    model = str(
                        params.get("model")
                        or params.get("model_name")
                        or "",
                    ).strip()
                if not model:
                    model = str(
                        payload.get("model")
                        or payload.get("model_name")
                        or "",
                    ).strip()

    allowed, reason, _usage = manager.check_budget(
        estimated_cost,
        model=model,
        provider=provider,
    )

    if not allowed:
        manager.record_usage(
            endpoint=path,
            estimated_cost=estimated_cost,
            actual_cost=0.0,
            status_code=429,
            blocked=True,
            provider=provider,
            model=model,
        )
        return web.json_response(
            {
                "error": reason or "Budget limit reached",
                "hint": "See /api/budget/status for current usage.",
            },
            status=429,
        )

    response = await handler(request)

    actual_cost = estimated_cost
    header_cost = response.headers.get("X-Usage-Cost", "").strip()
    if header_cost:
        with suppress(ValueError):
            actual_cost = float(header_cost)

    manager.record_usage(
        endpoint=path,
        estimated_cost=estimated_cost,
        actual_cost=actual_cost,
        status_code=response.status,
        blocked=False,
        provider=provider,
        model=model,
    )
    return response


# ─── Routes ───────────────────────────────────────────────────────


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "service": "uCore",
        "version": settings.version,
    })


async def version_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "app": settings.app_name,
        "version": settings.version,
        "python": plat_module.python_version(),
        "platform": plat_module.system(),
    })


async def info_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "app": settings.app_name,
        "version": settings.version,
        "host": settings.host,
        "port": settings.port,
        "debug": settings.debug,
        "platform": plat_module.system(),
        "machine": plat_module.machine(),
        "python": plat_module.python_version(),
        "uptime": time.time() - _start_time,
    })


async def shutdown_handler(request: web.Request) -> web.Response:
    """POST /api/shutdown — graceful shutdown.

    Protected: only accepts POST with a valid JSON body containing a
    confirmation token to prevent accidental shutdown from misrouted GETs.
    """
    if request.method != "POST":
        return web.json_response(
            {"error": "Use POST /api/shutdown with {\"confirm\": true}"},
            status=405,
        )
    try:
        body = await request.json()
        if not body.get("confirm"):
            return web.json_response(
                {"error": "Send {\"confirm\": true} to confirm shutdown"},
                status=400,
            )
    except Exception:
        return web.json_response(
            {"error": "Send {\"confirm\": true} to confirm shutdown"},
            status=400,
        )
    log.warning("Shutdown requested via API — stopping server")
    asyncio.get_event_loop().stop()
    return web.json_response({"status": "shutting down"})


async def migrate_admin_handler(request: web.Request) -> web.Response:
    """GET /api/admin/migrate — run database migration"""
    try:
        from app.core.database import migrate_db
        result = migrate_db()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ─── Popcorn Orchestration ────────────────────────────────────────


async def popcorn_status_handler(request: web.Request) -> web.Response:
    """GET /api/surfaces/popcorn/status — get Popcorn status"""
    try:
        if plat_module.system() != "Darwin":
            return web.json_response(
                {"error": "Popcorn is macOS-only"}, status=501
            )

        from app.services.popcorn_manager import get_popcorn_status
        status = get_popcorn_status()
        return web.json_response(status)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def popcorn_action_handler(request: web.Request) -> web.Response:
    """POST /api/surfaces/popcorn/{action} — control Popcorn"""
    try:
        if plat_module.system() != "Darwin":
            return web.json_response(
                {"error": "Popcorn is macOS-only"}, status=501
            )

        action = request.match_info.get("action", "").lower()
        from app.services.popcorn_manager import perform_action

        result = perform_action(action)
        status_code = 200 if result.get("success") else 400
        return web.json_response(result, status=status_code)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ─── Health Monitoring ────────────────────────────────────────────


async def health_status_handler(request: web.Request) -> web.Response:
    """GET /api/health/status — detailed health status"""
    try:
        from app.services.health_monitor import get_health_monitor
        monitor = get_health_monitor()
        status = monitor.get_status()
        return web.json_response(status)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def health_logs_handler(request: web.Request) -> web.Response:
    """GET /api/health/logs — get recent health monitor logs"""
    try:
        from app.services.health_monitor import get_health_monitor
        monitor = get_health_monitor()
        lines = int(request.query.get("lines", 100))
        logs = monitor.get_logs(lines)
        return web.json_response({"logs": logs})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ─── Self-Healing Skills ──────────────────────────────────────────


async def diagnostics_handler(request: web.Request) -> web.Response:
    """GET /api/diagnostics — system diagnostics"""
    try:
        from app.services.process_manager import get_process_manager
        pm = get_process_manager()
        diag = pm.get_system_diagnostics()
        # Convert to JSON-serializable format
        diag_str = json.dumps(diag, default=str)
        return web.Response(text=diag_str, content_type="application/json")
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def ports_handler(request: web.Request) -> web.Response:
    """GET /api/diagnostics/ports — port conflict report"""
    try:
        from app.services.process_manager import get_process_manager
        pm = get_process_manager()
        report = pm.get_port_conflict_report()
        return web.json_response(report)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ─── Unified Health & Repair ─────────────────────────────────────


async def full_health_handler(request: web.Request) -> web.Response:
    """GET /api/health/full — unified system health report."""
    try:
        from app.services.system_health import get_full_health
        report = await get_full_health()
        return web.json_response(report)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def system_repair_handler(request: web.Request) -> web.Response:
    """POST /api/system/repair — attempt automatic system repair."""
    try:
        from app.services.system_health import run_self_repair
        report = await run_self_repair()
        return web.json_response(report)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# ─── Dynamic module loader ──────────────────────────────────────

_MODULES_PACKAGE = "app.snackbar.modules"


def _load_modules(app: web.Application) -> list[str]:
    """Dynamically import and register all route modules.

    Each module in ``app/snackbar/modules/`` must expose a ``register(app)``
    callable.  Modules are loaded in alphabetical order for determinism.
    """
    loaded: list[str] = []

    try:
        pkg = importlib.import_module(_MODULES_PACKAGE)
    except ImportError as exc:
        log.warning("Snackbar modules package not found: %s", exc)
        return loaded

    for mod_info in pkgutil.iter_modules(pkg.__path__):
        mod_name = mod_info.name
        if mod_name.startswith("_"):
            continue
        full_name = f"{_MODULES_PACKAGE}.{mod_name}"
        try:
            module = importlib.import_module(full_name)
            register_fn = getattr(module, "register", None)
            if register_fn is None:
                log.debug("Skipping %s (no register function)", full_name)
                continue
            register_fn(app)
            loaded.append(mod_name)
            log.debug("Loaded snackbar module: %s", mod_name)
        except Exception as exc:
            log.error("Failed to load snackbar module %s: %s", full_name, exc)

    log.info("Loaded %d snackbar modules: %s", len(loaded), ", ".join(loaded))
    return loaded


# ─── App factory ──────────────────────────────────────────────────


_start_time: float = time.time()


async def health_monitor_ctx(app: web.Application):
    """Start the HealthMonitor background check loop on app startup."""
    from app.services.health_monitor import get_health_monitor

    monitor = get_health_monitor()
    await monitor.start()
    log.info("Health monitor started (5s check interval)")
    try:
        yield
    finally:
        await monitor.stop()
        log.info("Health monitor stopped")


async def maintenance_scheduler_ctx(app: web.Application):
    """Run the lightweight overnight maintenance scheduler in the background.

    Wrapped in try/except to prevent a single scheduler failure from
    crashing the entire server. Launchd will auto-restart the process
    if the event loop exits — we log the error but keep running.
    """
    from app.services.maintenance_scheduler import (
        MaintenanceScheduler,
        set_maintenance_scheduler,
    )

    scheduler = MaintenanceScheduler()
    set_maintenance_scheduler(scheduler)
    app[MAINTENANCE_SCHEDULER_KEY] = scheduler
    try:
        await scheduler.start()
        log.info("Maintenance scheduler started successfully")
    except Exception as exc:
        log.error("Maintenance scheduler failed to start: %s", exc)
        log.error("Server will continue without scheduled maintenance")
        # Don't crash — the app still works without the scheduler
    try:
        yield
    finally:
        try:
            await scheduler.stop()
        except Exception as exc:
            log.warning("Maintenance scheduler stop error: %s", exc)
        set_maintenance_scheduler(None)


def create_app() -> web.Application:
    """Build and return a configured aiohttp application.

    Route modules are loaded dynamically from ``snackbar/modules/``.
    Only routes unique to core (not covered by any module) are registered inline.
    """
    app = web.Application(middlewares=[budget_middleware, cors_middleware])
    app.cleanup_ctx.append(maintenance_scheduler_ctx)
    app.cleanup_ctx.append(health_monitor_ctx)

    # Budget manager (usage logging + enforcement scaffold)
    try:
        from app.services.budget_manager import BudgetManager

        app[BUDGET_MANAGER_KEY] = BudgetManager()
        log.debug("Budget manager initialized")
    except Exception as e:
        app[BUDGET_MANAGER_KEY] = None
        log.warning("Budget manager unavailable: %s", e)

    # ── Load all modular route handlers ────────────────────────
    # Covers: health, version, info, shutdown, admin/migrate,
    # popcorn, health/status, health/logs, diagnostics, skills
    _load_modules(app)

    # ── Routes unique to core (not covered by any module) ──────
    app.router.add_get("/api/health/full", full_health_handler)
    app.router.add_post("/api/system/repair", system_repair_handler)

    # Run database migration on startup
    from app.core.database import migrate_db
    migration = migrate_db()
    log.info("Database migration: v%s (%s tables)", migration["version"], "surfaces, snacks, containers")

    # Register API module routes (non-overlapping with core)
    try:
        from ..api.routes import register_routes
        register_routes(app)
        log.debug("API module routes registered")
    except ImportError as e:
        log.debug("API module not yet available: %s", e)

    # Register catalog routes
    try:
        from ..api.catalog import setup_routes
        setup_routes(app)
        log.debug("Catalog routes registered")
    except ImportError as e:
        log.debug("Catalog API not yet available: %s", e)

    # ── Budget Manager ──────────────────────────────────────────
    try:
        from app.services.budget_manager import BudgetManager
        app[BUDGET_MANAGER_KEY] = BudgetManager()
        log.info("✅ Budget manager attached to app")
    except Exception as exc:
        log.warning("⚠️  Budget manager init failed: %s", exc)

    return app


# ─── Main entry ──────────────────────────────────────────────────


def main():
    """Start the uCore snackbar daemon."""
    parser = argparse.ArgumentParser(description="uCore snackbar daemon")
    parser.add_argument("--host", default=settings.host, help="Bind host")
    parser.add_argument("--port", type=int, default=settings.port, help="Bind port")
    parser.add_argument(
        "--auto-start",
        action="store_true",
        default=settings.auto_start,
        help="Enable auto-start behavior",
    )
    args = parser.parse_args()

    settings.host = args.host
    settings.port = args.port
    settings.auto_start = args.auto_start

    log.info("Starting uCore snackbar on %s:%d", settings.host, settings.port)

    if _port_in_use(settings.host, settings.port):
        if _health_is_ready(settings.host, settings.port):
            log.info(
                "Detected healthy uCore already listening on %s:%d; attaching in idle mode",
                settings.host,
                settings.port,
            )
            asyncio.run(_idle_forever())
            return
        raise RuntimeError(
            f"Port {settings.port} is already in use and no healthy uCore instance responded"
        )

    app = create_app()
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
