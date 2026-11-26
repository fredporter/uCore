"""Synchronous text streaming for OpenRouter chat completions."""

import json
import os
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

CONFIG_PATH = Path(__file__).with_name("ucode_plus.json")
MAX_ATTEMPTS = 4
STATUS_MESSAGES = {
    401: "OpenRouter rejected the API key (401).",
    402: "OpenRouter credits or spending limit exhausted (402).",
    429: "OpenRouter rate limit reached (429).",
}


class OpenRouterError(RuntimeError):
    """A cloud failure with a signal for callers that can switch to a local model."""

    def __init__(self, message: str, *, fallback_allowed: bool = True):
        super().__init__(message)
        self.fallback_allowed = fallback_allowed


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load the module's OpenRouter configuration."""
    try:
        config = json.loads((path or CONFIG_PATH).read_text(encoding="utf-8"))
        if isinstance(config["openrouter"], dict):
            return config
    except (OSError, ValueError, KeyError, TypeError):
        pass
    raise OpenRouterError("OpenRouter configuration could not be loaded.") from None


def _stream_text(response: httpx.Response) -> Iterator[str]:
    for line in response.iter_lines():
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if data == "[DONE]":
            return
        try:
            event = json.loads(data)
            if event.get("error"):
                raise OpenRouterError("OpenRouter reported an error while streaming.")
            for choice in event.get("choices", []):
                if choice.get("finish_reason") == "error":
                    raise OpenRouterError("OpenRouter reported an error while streaming.")
                content = choice.get("delta", {}).get("content")
                if isinstance(content, str) and content:
                    yield content
        except (ValueError, AttributeError, TypeError):
            raise OpenRouterError("OpenRouter returned an invalid stream event.") from None
    raise OpenRouterError("OpenRouter closed the stream before completion.")


def run_chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    timeout: float = 60,
    *,
    config_path: Path | None = None,
) -> Iterator[str]:
    """Yield text chunks and retry eligible failures before emitting any text."""
    config = load_config(config_path)["openrouter"]
    if config.get("enabled") is not True:
        raise OpenRouterError("OpenRouter is disabled.")
    env_name = config.get("api_key_env", "OPENROUTER_API_KEY")
    if not isinstance(env_name, str) or not env_name:
        raise OpenRouterError("OpenRouter API key environment variable is invalid.")
    api_key = os.environ.get(env_name, "").strip()
    if not api_key:
        raise OpenRouterError(f"OpenRouter API key missing. Set {env_name}.")

    base_url = config.get("base_url")
    model = model or config.get("default_model")
    if not isinstance(base_url, str) or not isinstance(model, str) or not model.strip():
        raise OpenRouterError("OpenRouter base URL and model are required.")
    try:
        endpoint = urlsplit(base_url)
        valid_endpoint = (
            endpoint.scheme == "https" and endpoint.hostname and not endpoint.username
            and not endpoint.password and not endpoint.query and not endpoint.fragment
        )
    except ValueError:
        valid_endpoint = False
    if not valid_endpoint:
        raise OpenRouterError("OpenRouter requires a valid HTTPS base URL.")

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream",
        "HTTP-Referer": "https://github.com/fredporter/uCore",
        "X-OpenRouter-Title": "uCode+ integration",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_completion_tokens": 4096,
        "stream": True,
    }
    emitted_text = False
    for attempt in range(MAX_ATTEMPTS):
        try:
            with httpx.stream("POST", url, headers=headers, json=payload, timeout=timeout) as response:
                status = response.status_code
                if status == 200:
                    for content in _stream_text(response):
                        emitted_text = True
                        yield content
                    return
                error = STATUS_MESSAGES.get(status, f"OpenRouter returned HTTP {status}.")
                attempts = MAX_ATTEMPTS if status == 429 else 2 if 500 <= status < 600 else 1
        except httpx.RequestError:
            error = "OpenRouter connection failed."
            attempts = 2
        except OpenRouterError as error:
            raise OpenRouterError(str(error), fallback_allowed=not emitted_text) from None
        if emitted_text or attempt + 1 >= attempts:
            raise OpenRouterError(error, fallback_allowed=not emitted_text) from None
        time.sleep(2 ** attempt)
