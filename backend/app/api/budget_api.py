"""Budget API endpoints."""
from __future__ import annotations

from aiohttp import web

from app.core.snackbar import BUDGET_MANAGER_KEY


def _get_manager(request: web.Request):
    manager = request.app.get(BUDGET_MANAGER_KEY)
    if manager is None:
        raise web.HTTPServiceUnavailable(
            text='{"error":"budget manager unavailable"}',
            content_type="application/json",
        )
    return manager


async def handle_budget_status(request: web.Request) -> web.Response:
    manager = _get_manager(request)
    status = manager.get_status()
    monthly = status.get("monthly", {})
    daily = status.get("daily", {})
    session = status.get("session", {})
    return web.json_response(
        {
            "usage": {
                "total_cost": monthly.get("spend", 0.0),
                "daily_cost": daily.get("spend", 0.0),
                "session_cost": session.get("spend", 0.0),
            },
            "policy": {
                "monthly_usd_limit": monthly.get("budget", 50.0),
                "daily_budget_usd": daily.get("budget", 0.0),
                "session_budget_usd": session.get("budget", 0.0),
            },
            "status": status,
            "remaining": monthly.get("remaining", 0.0),
            "used": monthly.get("spend", 0.0),
            "limit": monthly.get("budget", 50.0),
            "over_limit": bool(status.get("circuit_breaker_open", False)),
        },
    )


async def handle_budget_usage(request: web.Request) -> web.Response:
    manager = _get_manager(request)
    raw_limit = request.query.get("limit", "100")
    try:
        limit = int(raw_limit)
    except ValueError:
        limit = 100
    rows = manager.get_spend_report(limit=limit)
    return web.json_response({"entries": rows, "count": len(rows)})


async def handle_budget_reload(request: web.Request) -> web.Response:
    manager = _get_manager(request)
    policy = manager.reload_policy()
    return web.json_response(
        {
            "status": "reloaded",
            "policy": {
                "monthly_usd_limit": policy.get("monthly_budget_usd", 50.0),
                "daily_budget_usd": policy.get("daily_budget_usd", 0.0),
                "session_budget_usd": policy.get("session_budget_usd", 0.0),
                "per_agent": policy.get("per_agent", {}),
            },
        },
    )
