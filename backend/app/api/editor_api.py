"""
Editor API — web scraping and document operations for the Bangle editor surface.

POST /api/editor/scrape-web     — fetch URL and extract article text
POST /api/editor/summarize      — AI-powered text summarization
POST /api/editor/save-to-binder — export document to Binder
"""
from __future__ import annotations

import logging
from typing import Any

from aiohttp import web, ClientSession, ClientTimeout

log = logging.getLogger("ucore.editor")


async def handle_scrape_web(request: web.Request) -> web.Response:
    """POST /api/editor/scrape-web — fetch and extract article content from a URL.

    Body: { "url": "https://..." }
    Returns: { "title": "...", "description": "...", "text": "...", "url": "..." }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    url: str = body.get("url", "").strip()
    if not url or not url.startswith(("http://", "https://")):
        return web.json_response({"error": "Valid 'url' field required"}, status=400)

    try:
        timeout = ClientTimeout(total=10)
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; uCore-Scraper/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        }
        async with ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as resp:
                if not resp.ok:
                    return web.json_response(
                        {"error": f"HTTP {resp.status}", "url": url}, status=502
                    )
                html = await resp.text(errors="replace")
    except Exception as e:
        return web.json_response({"error": str(e), "url": url}, status=502)

    title, description, text = _extract_article(html, url)
    return web.json_response({
        "url": url,
        "title": title,
        "description": description,
        "text": text,
        "html": html[:4000],  # truncated raw HTML for reference
    })


async def handle_summarize(request: web.Request) -> web.Response:
    """POST /api/editor/summarize — AI text summarization.

    Body: { "text": "...", "style": "bullets"|"paragraph" }
    Returns: { "summary": "..." }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    text: str = body.get("text", "").strip()
    if not text:
        return web.json_response({"error": "'text' field required"}, status=400)

    style = body.get("style", "bullets")

    try:
        from app.services.provider_router import ProviderRouter
        router = ProviderRouter()
        prompt = (
            f"Summarize the following text as {'bullet points' if style == 'bullets' else 'a concise paragraph'}. "
            f"Be brief and factual.\n\nText:\n{text[:8000]}"
        )
        summary = await router.complete(prompt, max_tokens=512)
        return web.json_response({"summary": summary})
    except Exception as e:
        log.warning("Summarize error: %s", e)
        # Fallback: extract first few sentences
        sentences = text.split(". ")[:3]
        return web.json_response({"summary": ". ".join(sentences) + ".", "fallback": True})


async def handle_save_to_binder(request: web.Request) -> web.Response:
    """POST /api/editor/save-to-binder — save document to Binder project.

    Body: { "title": "...", "content": "...", "project": "...", "tags": [...] }
    Returns: { "ok": true, "id": "..." }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    title = body.get("title", "Untitled")
    content = body.get("content", "")
    if not content:
        return web.json_response({"error": "'content' field required"}, status=400)

    try:
        from app.knowledge.knowledge_layer import KnowledgeLayer
        layer = KnowledgeLayer()
        doc_id = await layer.save_document(
            title=title,
            content=content,
            tags=body.get("tags", []),
            project=body.get("project"),
            source="bangle-editor",
        )
        return web.json_response({"ok": True, "id": doc_id})
    except Exception as e:
        log.warning("Save to Binder error: %s", e)
        return web.json_response({"ok": False, "error": str(e)}, status=500)


# ─── HTML extraction helpers ─────────────────────────────────────────


def _extract_article(html: str, url: str) -> tuple[str, str, str]:
    """Extract title, description, and main text from raw HTML without dependencies."""
    import re

    # Title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', html, re.I)
    title = (og_title.group(1) if og_title else title_match.group(1) if title_match else url).strip()

    # Description
    og_desc = re.search(r'<meta[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])[^>]+content=["\'](.*?)["\']', html, re.I)
    description = og_desc.group(1).strip() if og_desc else ""

    # Body text: strip tags, collapse whitespace
    body_match = re.search(r"<(?:article|main|body)[^>]*>([\s\S]*?)</(?:article|main|body)>", html, re.I)
    raw = body_match.group(1) if body_match else html
    # Remove scripts/styles
    raw = re.sub(r"<(script|style|nav|header|footer|aside)[^>]*>[\s\S]*?</\1>", "", raw, flags=re.I)
    # Strip all tags
    text = re.sub(r"<[^>]+>", " ", raw)
    # Collapse whitespace
    text = re.sub(r"\s{3,}", "\n\n", text).strip()

    return title, description, text[:6000]
