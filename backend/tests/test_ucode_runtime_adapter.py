from __future__ import annotations

from app.extensions.adapters import ucode_runtime_adapter as adapter


def test_runtime_resolution_prioritises_active_ucode_checkout(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(adapter, "_ensure_ucode_path", lambda: calls.append("path"))

    class Provider:
        handler = object()

    def import_module(name: str):
        calls.append(f"import:{name}")
        return Provider

    monkeypatch.setattr(adapter.importlib, "import_module", import_module)

    assert adapter._resolve_callable("ucode_runtime.terminal_runtime.handler") is Provider.handler
    assert calls == ["path", "import:ucode_runtime.terminal_runtime"]


def test_register_routes_delegates_ceefax_and_bbcsdl_with_shared_store(monkeypatch):
    app: dict[object, object] = {}
    store_key = object()
    store = object()
    calls: list[tuple[str, object, object] | tuple[str]] = []

    def store_factory():
        calls.append(("factory",))
        return store

    def register_ceefax(received_app, received_store):
        calls.append(("ceefax", received_app, received_store))

    def register_bbcsdl(received_app, received_store):
        calls.append(("bbcsdl", received_app, received_store))

    providers = {
        adapter.DEFAULT_CEEFAX_STORE_FACTORY: store_factory,
        adapter.DEFAULT_CEEFAX_REGISTRAR: register_ceefax,
        adapter.DEFAULT_BBCSDL_REGISTRAR: register_bbcsdl,
    }
    monkeypatch.setattr(adapter, "_resolve_callable", providers.get)

    adapter.register_routes(app, store_key)

    assert app[store_key] is store
    assert calls == [
        ("factory",),
        ("ceefax", app, store),
        ("bbcsdl", app, store),
    ]
