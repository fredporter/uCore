"""Sprint 1G – OpenRouter stream endpoint and cloud model listing.

Adds:
  POST /api/chat/stream      — SSE streaming chat, routes to OpenRouter or Ollama
  GET  /api/models/cloud     — returns only OpenRouter models from provider_router
"""
from __future__ import annotations

import json
import logging

from aiohttp import web

from .local_assistant_api import active_assistant_profile

log = logging.getLogger("ucore.chat_openrouter")


async def handle_chat_stream(request: web.Request) -> web.StreamResponse:
    """POST /api/chat/stream — SSE streaming chat.

    Body: { "message": "...", "model": "...", "history": [...] }

    Streams tokens as: data: {"token": "..."}\n\n
    Ends with:         data: [DONE]\n\n

    On OpenRouter error, falls back to Ollama and signals with a system token:
      data: {"system": "OpenRouter unavailable – switched to local model."}\n\n
    """
    try:
        body = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON body")

    if not isinstance(body, dict) or not isinstance(body.get("message"), str):
        return web.Response(status=400, text="message is required")
    message = body["message"].strip()
    if not message:
        return web.Response(status=400, text="message is required")

    model: str | None = body.get("model")
    history: list = body.get("history") or body.get("messages") or []
    if not isinstance(history, list):
        history = []
    if model is not None and not isinstance(model, str):
        return web.Response(status=400, text="Invalid model")
    history = [
        {"role": m["role"], "content": str(m.get("content", ""))[:16000]}
        for m in history[-16:]
        if isinstance(m, dict) and m.get("role") in {"user", "assistant"}
    ]

    active_assistant_profile(request, "local_models")

    # Build messages list
    from .chat import _select_system_prompt
    chat_messages: list[dict] = [
        {"role": "system", "content": _select_system_prompt("chat")},
        *history,
        {"role": "user", "content": message},
    ]

    # Prepare SSE response
    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
    await resp.prepare(request)

    async def emit(data: dict) -> None:
        await resp.write(f"data: {json.dumps(data)}\n\n".encode())

    from ..services.provider_router import ProviderRouter

    router = ProviderRouter()
    use_openrouter = bool(model and (
        model.startswith("openrouter/")
        or any(item["id"] == model and item["provider"].startswith("openrouter")
               for item in router.list_models())
    ))
    provider = "openrouter" if use_openrouter else "ollama"
    emitted = False

    try:
        async for token in router.chat_stream(messages=chat_messages, model=model, provider=provider):
            if token:
                await emit({"token": token})
                emitted = True
    except Exception as exc:
        log.warning("Chat stream failed for %s: %s", provider, type(exc).__name__)
        if use_openrouter and not emitted:
            await emit({"system": "OpenRouter unavailable. Switching to a local model."})
            try:
                async for token in router.chat_stream(messages=chat_messages, provider="ollama"):
                    await emit({"token": token})
            except Exception:
                await emit({"error": "The local model is also unavailable."})
        else:
            await emit({"error": "The model stopped responding. Try again when it is available."})

    await resp.write(b"data: [DONE]\n\n")
    await resp.write_eof()
    return resp


async def handle_models_cloud(request: web.Request) -> web.Response:
    """GET /api/models/cloud — list OpenRouter cloud models with cost tier."""
    from ..services.provider_router import ProviderRouter

    active_assistant_profile(request, "local_models")
    try:
        router = ProviderRouter()
        all_models = router.list_models()
        cloud_models = [
            m for m in all_models
            if m.get("provider", "").startswith("openrouter")
        ]
        return web.json_response({"models": cloud_models, "count": len(cloud_models)})
    except Exception as exc:
        log.error("Cloud models error: %s", exc)
        return web.json_response({"models": [], "count": 0, "error": str(exc)})
