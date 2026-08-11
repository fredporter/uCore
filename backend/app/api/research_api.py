"""Research API — BrowserUI research queue endpoints.

POST /api/research/start   — enqueue a scrape+summarise+save job
GET  /api/research/status  — poll job progress
GET  /api/research/list    — list all jobs
POST /api/research/process — process next pending job
"""
from __future__ import annotations

import logging

from aiohttp import web

from ..services.research_queue import ResearchQueue

log = logging.getLogger("ucore.research_api")
_queue: ResearchQueue | None = None


def get_queue() -> ResearchQueue:
    global _queue
    if _queue is None:
        _queue = ResearchQueue()
    return _queue


async def handle_research_start(request: web.Request) -> web.Response:
    """POST /api/research/start — enqueue a new research job."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    url = body.get("url", "").strip()
    if not url or not url.startswith(("http://", "https://")):
        return web.json_response({"error": "Valid URL required"}, status=400)

    binder = body.get("binder", "research").strip() or "research"
    tags = body.get("tags", [])
    mode = body.get("mode", "summarise")

    q = get_queue()
    job_id = await q.enqueue(url=url, binder=binder, tags=tags, mode=mode)
    return web.json_response({"job_id": job_id, "state": "pending", "binder": binder})


async def handle_research_status(request: web.Request) -> web.Response:
    """GET /api/research/status?job_id=... — poll job status."""
    job_id = request.query.get("job_id", "").strip()
    if not job_id:
        return web.json_response({"error": "job_id query param required"}, status=400)
    q = get_queue()
    status = await q.status(job_id)
    if status is None:
        return web.json_response({"error": "Job not found"}, status=404)
    return web.json_response(status)


async def handle_research_list(request: web.Request) -> web.Response:
    """GET /api/research/list?state=...&binder=... — list jobs."""
    state = request.query.get("state")
    binder = request.query.get("binder")
    q = get_queue()
    jobs = await q.list_jobs(state=state, binder=binder)
    return web.json_response({"jobs": jobs, "count": len(jobs)})


async def handle_research_process(request: web.Request) -> web.Response:
    """POST /api/research/process — process next pending job."""
    q = get_queue()
    result = await q.process_next()
    if result is None:
        return web.json_response({"processed": False, "message": "No pending jobs"})
    return web.json_response({"processed": True, "job": result})


async def handle_research_enhance(request: web.Request) -> web.Response:
    """POST /api/research/enhance — enhance existing content via ChatUI.

    Body: { title: "...", content: "...", binder: "..." }
    Returns: { enhanced: "...", suggested_tags: [...] }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    title = body.get("title", "").strip()
    content = body.get("content", "").strip()
    if not content:
        return web.json_response({"error": "content required"}, status=400)
    try:
        from .chat import get_router
        router = get_router()
        prompt = (
            f"Expand and enhance the following document with deeper analysis, "
            f"additional context, and relevant citations. "
            f"Add 3-5 suggested tags with # prefix. Use markdown.\n\n"
            f"Title: {title}\n\n{content[:3000]}"
        )
        sr = await router.chat(
            messages=[{"role": "user", "content": prompt}],
            model="ollama/qwen2.5-coder:3b", temperature=0.3,
        )
        enhanced = sr.get("content", content)
        # Extract hashtags
        import re
        tags = re.findall(r"#\w+", enhanced)
        return web.json_response({
            "enhanced": enhanced,
            "original": content,
            "suggested_tags": list(set(tags))[:10],
        })
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
