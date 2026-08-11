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


async def handle_research_stream(request: web.Request) -> web.StreamResponse:
    """GET /api/research/stream/{job_id} — SSE streaming for job progress."""
    job_id = request.match_info.get("job_id", "").strip()
    if not job_id:
        return web.json_response({"error": "job_id required"}, status=400)
    q = get_queue()
    resp = web.StreamResponse(
        status=200, reason="OK",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    await resp.prepare(request)
    import asyncio, json
    last_state = None
    for _ in range(60):  # max 60 seconds
        status = await q.status(job_id)
        if status is None:
            await resp.write(b"data: {\"error\":\"not found\"}\n\n")
            break
        if status["state"] != last_state:
            await resp.write(f"data: {json.dumps(status)}\n\n".encode())
            last_state = status["state"]
        if status["state"] in ("completed", "failed"):
            break
        await asyncio.sleep(1)
    return resp


async def handle_binder_search(request: web.Request) -> web.Response:
    """GET /api/binder/search?q=... — cross-binder full-text search."""
    query = request.query.get("q", "").strip().lower()
    if not query:
        return web.json_response({"results": [], "count": 0})
    from pathlib import Path
    vault = Path.home() / "Vault"
    results = []
    if vault.exists():
        for md in vault.rglob("*.md"):
            try:
                text = md.read_text(encoding="utf-8", errors="ignore").lower()
                if query in text:
                    rel = str(md.relative_to(vault))
                    binder = rel.split("/")[0] if "/" in rel else "root"
                    results.append({
                        "path": f"~/Vault/{rel}",
                        "binder": binder,
                        "title": md.stem.replace("-", " ").title(),
                        "snippet": text[max(0, text.find(query)-40):text.find(query)+len(query)+80],
                    })
            except Exception:
                continue
    results = results[:20]
    return web.json_response({"results": results, "count": len(results)})


async def handle_vault_scan(request: web.Request) -> web.Response:
    """GET /api/research/vault-scan — scan binders for gaps and freshness."""
    from pathlib import Path
    from datetime import UTC, datetime, timedelta
    import json
    vault = Path.home() / "Vault"
    gaps = []
    now = datetime.now(UTC)
    if vault.exists():
        for d in sorted(vault.iterdir()):
            if not d.is_dir():
                continue
            bj = d / "binder.json"
            meta = {}
            if bj.exists():
                try:
                    meta = json.loads(bj.read_text())
                except Exception:
                    pass
            score = meta.get("score", 0)
            sources = meta.get("sources", [])
            updated = meta.get("updated", "")
            # Low quality
            if score < 2:
                gaps.append({
                    "topic": d.name,
                    "reason": f"Low quality score ({score}/5) — needs research",
                    "priority": "high" if score == 0 else "medium",
                })
            # No sources
            elif not sources:
                gaps.append({
                    "topic": d.name,
                    "reason": "No sources — needs initial research",
                    "priority": "high",
                })
            # Stale (older than 30 days)
            elif updated:
                try:
                    dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    age = (now - dt).days
                    if age > 30:
                        gaps.append({
                            "topic": d.name,
                            "reason": f"Stale ({age} days old) — consider re-research",
                            "priority": "low",
                        })
                except Exception:
                    pass
    gaps.sort(key=lambda g: {"high": 0, "medium": 1, "low": 2}[g["priority"]])
    return web.json_response({"gaps": gaps, "count": len(gaps)})


