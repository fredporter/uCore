"""Sprint 1G – OpenRouter stream endpoint and cloud model listing.

Adds:
  POST /api/chat/stream      — SSE streaming chat, routes to OpenRouter or Ollama
  GET  /api/models/cloud     — returns only OpenRouter models from provider_router
"""
from __future__ import annotations

import asyncio
import json
import logging

from aiohttp import web

log = logging.getLogger("ucore.chat_openrouter")


def _is_openrouter_model(model: str | None) -> bool:
    if not model:
        return False
    openrouter_providers = {
        "cognitivecomputations", "microsoft", "deepseek", "mistralai",
        "anthropic", "google", "openai", "meta-llama", "qwen",
    }
    return any(model.startswith(p + "/") for p in openrouter_providers)


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

    message: str = body.get("message", "").strip()
    if not message:
        return web.Response(status=400, text="message is required")

    model: str | None = body.get("model")
    history: list = body.get("history") or body.get("messages") or []
    history = [
        {"role": m["role"], "content": str(m.get("content", ""))[:16000]}
        for m in history[-16:]
        if isinstance(m, dict) and m.get("role") in {"user", "assistant"}
    ]

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
    use_openrouter = _is_openrouter_model(model)
    provider = "openrouter" if use_openrouter else "ollama"
    effective_model = model

    try:
        # Check if provider_router supports async streaming
        if hasattr(router, "chat_stream"):
            async for token in router.chat_stream(
                messages=chat_messages, model=effective_model, provider=provider
            ):
                await emit({"token": token})
        else:
            # Fallback: single non-streaming call, emit full response as one token
            response = await router.chat(
                messages=chat_messages, model=effective_model, provider=provider
            )
            if response.get("error") and use_openrouter:
                raise RuntimeError(response["error"])
            content = response.get("content", "")
            # Emit word-by-word for a streaming feel
            for word in content.split(" "):
                await emit({"token": word + " "})
                await asyncio.sleep(0)

    except Exception as exc:
        if use_openrouter:
            log.warning("OpenRouter failed (%s), falling back to Ollama", exc)
            await emit({"system": "OpenRouter unavailable – switched to local model."})
            # Retry with Ollama
            try:
                response = await router.chat(
                    messages=chat_messages, model=None, provider="ollama"
                )
                content = response.get("content", "")
                for word in content.split(" "):
                    await emit({"token": word + " "})
                    await asyncio.sleep(0)
            except Exception as fallback_exc:
                await emit({"error": f"Fallback also failed: {fallback_exc}"})
        else:
            await emit({"error": str(exc)})

    await resp.write(b"data: [DONE]\n\n")
    await resp.write_eof()
    return resp


async def handle_models_cloud(request: web.Request) -> web.Response:
    """GET /api/models/cloud — list OpenRouter cloud models with cost tier."""
    from ..services.provider_router import ProviderRouter

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
