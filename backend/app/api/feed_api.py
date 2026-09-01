"""Feed API — REST endpoints for the Feed System (Pod/Nugget/Seed/Slate/Spool).

GET  /api/feed/query     — query activities by source, timeframe, importance
POST /api/feed/ingest    — ingest a user activity event
GET  /api/feed/suggest   — generate binder suggestions from feed activity
POST /api/feed/link      — link a .tasker task to a feed activity
"""
from __future__ import annotations

import logging

from aiohttp import web

log = logging.getLogger("ucore.api.feed")

# Lazy singleton
_feed_server = None


def _get_feed_server():
    global _feed_server
    if _feed_server is None:
        from app.services.feed_store import FeedServer
        _feed_server = FeedServer()
    return _feed_server


async def handle_feed_ingest(request: web.Request) -> web.Response:
    """POST /api/feed/ingest — ingest an activity event."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )

    source = body.get("source", "")
    activity_type = body.get("type", "")
    if not source or not activity_type:
        return web.json_response(
            {"error": "source and type are required"}, status=400,
        )

    try:
        importance = float(body.get("importance", 0.5))
    except (TypeError, ValueError):
        return web.json_response({"error": "importance must be a number"}, status=400)
    if not 0 <= importance <= 1:
        return web.json_response({"error": "importance must be between 0 and 1"}, status=400)

    server = _get_feed_server()
    result = await server.ingest_activity(
        source=source,
        type=activity_type,
        title=body.get("title", ""),
        content=body.get("content", ""),
        url=body.get("url", ""),
        contact_name=body.get("contact_name", ""),
        importance=importance,
        metadata=body.get("metadata"),
        external_id=body.get("external_id"),
    )

    # Bridge to Spool
    try:
        from app.services.feed_consumer import FeedConsumer
        consumer = FeedConsumer()
        consumer.consume_activity(body)
    except ImportError:
        log.debug("FeedConsumer not available, skipping spool bridge")

    return web.json_response(result)


async def handle_feed_query(request: web.Request) -> web.Response:
    """GET /api/feed/query — query activities."""
    source = request.query.get("source")
    since = request.query.get("since")
    try:
        limit = max(1, min(int(request.query.get("limit", "50")), 500))
        importance_min = float(request.query.get("importance_min", "0"))
    except (TypeError, ValueError):
        return web.json_response(
            {"error": "limit and importance_min must be numeric"}, status=400
        )
    processed_value = request.query.get("processed")
    if processed_value is None:
        processed = None
    elif processed_value.lower() in {"true", "1"}:
        processed = True
    elif processed_value.lower() in {"false", "0"}:
        processed = False
    else:
        return web.json_response({"error": "processed must be true or false"}, status=400)

    server = _get_feed_server()
    activities = await server.query_feed(
        source=source,
        since=since,
        limit=limit,
        importance_min=importance_min,
        processed=processed,
    )
    return web.json_response({"activities": activities, "count": len(activities)})


async def handle_feed_suggest(request: web.Request) -> web.Response:
    """GET /api/feed/suggest — generate binder suggestions."""
    min_confidence = float(request.query.get("min_confidence", "0.5"))

    server = _get_feed_server()
    suggestions = await server.suggest_binders(
        min_confidence=min_confidence,
    )
    return web.json_response(
        {"suggestions": suggestions, "count": len(suggestions)},
    )


async def handle_feed_link(request: web.Request) -> web.Response:
    """POST /api/feed/link — link a task to an activity."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON body"}, status=400,
        )

    task_id = body.get("task_id", "")
    activity_id = body.get("activity_id")
    if not task_id or activity_id is None:
        return web.json_response(
            {"error": "task_id and activity_id are required"}, status=400,
        )

    server = _get_feed_server()
    result = await server.link_task_to_activity(
        task_id=task_id,
        activity_id=int(activity_id),
        link_type=body.get("link_type", "source"),
    )
    return web.json_response(result)


async def handle_feed_promote(request: web.Request) -> web.Response:
    """Promote one feed item into the canonical markdown Tasker inbox."""
    try:
        body = await request.json()
        activity_id = int(body.get("activity_id"))
    except Exception:
        return web.json_response({"error": "activity_id is required"}, status=400)

    server = _get_feed_server()
    rows = await server.query_feed(limit=500)
    activity = next((row for row in rows if int(row["id"]) == activity_id), None)
    if not activity:
        return web.json_response({"error": "Activity not found"}, status=404)

    from app.services.feed_workflow import promote_activity_to_task

    promoted = promote_activity_to_task(
        activity,
        title=body.get("title"),
        board=str(body.get("board") or "inbox"),
        priority=str(body.get("priority") or "medium"),
        binder=str(body.get("binder") or "Sandbox"),
    )
    await server.link_task_to_activity(task_id=promoted["task_id"], activity_id=activity_id)
    return web.json_response({"ok": True, **promoted})


async def handle_feed_rules(request: web.Request) -> web.Response:
    """Preview enabled rules against unprocessed Feed items."""
    from app.services.feed_rules import evaluate_feed_rules, load_feed_rules

    rules, config = load_feed_rules()
    rows = await _get_feed_server().query_feed(limit=200)
    pending = [row for row in rows if not row.get("processed")]
    proposals = evaluate_feed_rules(pending, rules)
    return web.json_response(
        {
            "rules": [{"id": rule.id, "enabled": rule.enabled, "action": rule.action} for rule in rules],
            "proposals": proposals,
            "count": len(proposals),
            "config": config,
        }
    )


async def handle_feed_rules_apply(request: web.Request) -> web.Response:
    """Explicitly apply task proposals; never called by status/query operations."""
    from app.services.feed_rules import evaluate_feed_rules, load_feed_rules
    from app.services.feed_workflow import promote_activity_to_task

    server = _get_feed_server()
    rules, config = load_feed_rules()
    rows = await server.query_feed(limit=200)
    by_id = {int(row["id"]): row for row in rows if not row.get("processed")}
    proposals = evaluate_feed_rules(list(by_id.values()), rules)
    created = []
    handled: set[int] = set()
    for proposal in proposals:
        if proposal["activity_id"] in handled:
            continue
        if proposal["action"] not in {"propose-task", "create-task"}:
            continue
        activity = by_id[proposal["activity_id"]]
        promoted = promote_activity_to_task(
            activity,
            title=proposal["title"],
            board=proposal["board"],
            priority=proposal["priority"],
            binder=proposal["binder"],
            rule_id=proposal["rule_id"],
        )
        await server.link_task_to_activity(
            task_id=promoted["task_id"], activity_id=proposal["activity_id"], link_type="rule"
        )
        created.append({**proposal, **promoted})
        handled.add(proposal["activity_id"])
    return web.json_response({"ok": True, "created": created, "count": len(created), "config": config})


async def handle_feed_runtime(request: web.Request) -> web.Response:
    """User-facing status for the Feed/Snackmachine workflow conduit."""
    from app.services.apple_feed_sync import AppleFeedSync
    from app.services.feed_rules import load_feed_rules
    from snackmachine.scheduler import get_maintenance_scheduler

    rules, config = load_feed_rules()
    scheduler = get_maintenance_scheduler()
    server = _get_feed_server()
    return web.json_response(
        {
            "status": "ready",
            "runtime": "snackmachine",
            "feed_pod": str(server.pod_path),
            "sources": AppleFeedSync(server).source_status(),
            "rules": {
                "enabled": sum(1 for rule in rules if rule.enabled),
                "total": len(rules),
                "auto_execute": config["auto_execute"],
                "path": config["path"],
            },
            "scheduler": scheduler.status() if scheduler else {"status": "stopped"},
        }
    )


def register_feed_routes(app: web.Application) -> None:
    """Register Feed API routes."""
    app.router.add_post("/api/feed/ingest", handle_feed_ingest)
    app.router.add_get("/api/feed/query", handle_feed_query)
    app.router.add_get("/api/feed/suggest", handle_feed_suggest)
    app.router.add_post("/api/feed/link", handle_feed_link)
    app.router.add_post("/api/feed/promote", handle_feed_promote)
    app.router.add_get("/api/feed/rules", handle_feed_rules)
    app.router.add_post("/api/feed/rules/apply", handle_feed_rules_apply)
    app.router.add_get("/api/feed/runtime", handle_feed_runtime)
    app.router.add_get("/api/feed/sources", handle_feed_sources)
    app.router.add_post("/api/feed/sources/{source}/sync", handle_feed_source_sync)
    log.info("Feed API routes registered: ingest, query, suggest, link")


async def handle_feed_sources(request: web.Request) -> web.Response:
    """Describe source availability without prompting for macOS permissions."""
    from app.services.apple_feed_sync import AppleFeedSync

    return web.json_response({"sources": AppleFeedSync(_get_feed_server()).source_status()})


async def handle_feed_source_sync(request: web.Request) -> web.Response:
    """Run one explicit, user-initiated source import into Feeds."""
    from app.services.apple_feed_sync import AppleFeedSync

    source = request.match_info["source"]
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        result = await AppleFeedSync(_get_feed_server()).sync(
            source,
            limit=max(1, min(int(body.get("limit", 50)), 200)),
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(result, status=200 if result.get("ok") else 503)
