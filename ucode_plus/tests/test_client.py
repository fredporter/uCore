import json
from contextlib import contextmanager

import httpx
import pytest

from ucode_plus import client

MESSAGES = [{"role": "user", "content": "Hi"}]
SUCCESS = (
    ': OpenRouter processing\n\n'
    'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
    'data: {"choices":[{"delta":{"content":" world"}}]}\n\n'
    'data: [DONE]\n\n'
)


@pytest.fixture
def config(tmp_path, monkeypatch):
    path = tmp_path / "ucode_plus.json"
    path.write_text(json.dumps({
        "openrouter": {
            "enabled": True,
            "api_key_env": "TEST_UCODE_PLUS_KEY",
            "base_url": "https://openrouter.ai/api/v1",
            "default_model": "example/default",
        }
    }), encoding="utf-8")
    monkeypatch.setenv("TEST_UCODE_PLUS_KEY", "test-key")
    return path


@pytest.fixture
def calls(monkeypatch):
    requests = []
    delays = []
    responses = []
    real_client = httpx.Client

    def handle(request):
        requests.append(request)
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        status, body = result
        return httpx.Response(status, text=body)

    @contextmanager
    def stream(method, url, *, timeout, **kwargs):
        with real_client(transport=httpx.MockTransport(handle), timeout=timeout) as http:
            with http.stream(method, url, **kwargs) as response:
                yield response

    monkeypatch.setattr(client.httpx, "stream", stream)
    monkeypatch.setattr(client.time, "sleep", delays.append)
    return requests, delays, responses


def test_missing_key(config, calls, monkeypatch):
    monkeypatch.delenv("TEST_UCODE_PLUS_KEY")
    with pytest.raises(client.OpenRouterError, match="API key missing") as error:
        list(client.run_chat(MESSAGES, config_path=config))
    assert error.value.fallback_allowed
    assert not calls[0]


def test_stream_and_payload(config, calls):
    requests, _, responses = calls
    responses.append((200, SUCCESS))
    assert list(client.run_chat(MESSAGES, config_path=config)) == ["Hello", " world"]
    request, = requests
    assert request.method == "POST"
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-key"
    payload = json.loads(request.content)
    assert payload["model"] == "example/default"
    assert payload["messages"] == MESSAGES
    assert payload["stream"] is True
    assert payload["max_completion_tokens"] == 4096


@pytest.mark.parametrize(("status", "attempts", "expected_delays"), [
    (401, 1, []),
    (402, 1, []),
    (429, 4, [1, 2, 4]),
    (503, 2, [1]),
])
def test_http_errors(config, calls, status, attempts, expected_delays):
    requests, delays, responses = calls
    responses.extend([(status, "provider detail")] * attempts)
    with pytest.raises(client.OpenRouterError, match=str(status)) as error:
        list(client.run_chat(MESSAGES, config_path=config))
    assert "provider detail" not in str(error.value)
    assert error.value.fallback_allowed
    assert len(requests) == attempts
    assert delays == expected_delays


def test_transport_retry_can_recover(config, calls):
    requests, delays, responses = calls
    responses.extend([httpx.ConnectError("network detail"), (200, SUCCESS)])
    assert list(client.run_chat(MESSAGES, "example/explicit", config_path=config)) == ["Hello", " world"]
    assert len(requests) == 2
    assert json.loads(requests[1].content)["model"] == "example/explicit"
    assert delays == [1]


@pytest.mark.parametrize("tail", ['data: {"error":{"message":"provider detail"}}\n\n', ""])
def test_incomplete_stream_cannot_retry_or_fallback_after_text(config, calls, tail):
    requests, delays, responses = calls
    responses.append((200, 'data: {"choices":[{"delta":{"content":"Partial"}}]}\n\n' + tail))
    stream = client.run_chat(MESSAGES, config_path=config)
    assert next(stream) == "Partial"
    with pytest.raises(client.OpenRouterError) as error:
        next(stream)
    assert not error.value.fallback_allowed
    assert "provider detail" not in str(error.value)
    assert len(requests) == 1
    assert not delays
