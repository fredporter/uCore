# uCode+ OpenRouter streaming client

This uCore module exposes the OpenRouter transport for a future OK Assistant
integration. The existing assistant routes continue to use their own provider
configuration.

Use uCore's backend development environment with `httpx` and `pytest`
installed. Run these commands from the repository root.

```sh
backend/.venv/bin/python -m pytest -q ucode_plus/tests
```

Set `OPENROUTER_API_KEY` in the calling process environment. The checked-in
`ucode_plus.json` contains example model IDs and the default model. Keep keys
out of the JSON file.

```python
from ucode_plus.client import OpenRouterError, run_chat

try:
    for text in run_chat([{"role": "user", "content": "Summarize these notes."}]):
        print(text, end="", flush=True)
except OpenRouterError as error:
    print(error)
```

The client sends requests to the configured HTTPS endpoint. Check the selected
model and set a spending limit on the API key before running live requests.
The client caps completion length at 4,096 tokens. Rate limits use bounded
exponential backoff. Server and transport failures can retry once before text
is emitted. A caller can use `error.fallback_allowed` to decide whether to
offer a fresh local response after a cloud failure. A partial cloud response
requires the caller to preserve or explicitly replace that response.

For a rejected key or exhausted credits, check the API key and account limits
before retrying. The local tests use mock responses and do not require a key.
