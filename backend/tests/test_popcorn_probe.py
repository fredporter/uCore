"""Liveness probe for the local Vite frontend."""
from __future__ import annotations

import urllib.request


class _FakeResponse:
    status = 200

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


def test_probe_accepts_lowercase_doctype(monkeypatch):
    """Vite serves `<!doctype html>` in lower case; the probe must not miss it."""
    from app.services import popcorn_manager

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(b"<!doctype html><html></html>"),
    )
    assert popcorn_manager._is_frontend_alive() is True


def test_probe_uses_loopback_address():
    from app.services import popcorn_manager

    assert popcorn_manager.FRONTEND_PROBE_URL.startswith("http://127.0.0.1:5175")


def test_probe_rejects_non_html(monkeypatch):
    from app.services import popcorn_manager

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(b"upstream error"),
    )
    assert popcorn_manager._is_frontend_alive() is False
