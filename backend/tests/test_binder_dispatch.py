"""Tests for Binder Dispatch Integration & Curated Elements Catalog API.

Verifies:
- GET /api/dispatch/catalog (loading cards, BOBs, dividers)
- POST /api/dispatch/create with binder_id
- GET /api/dispatch/by-binder/{binder_id}
- GET /api/dispatch/catalog/asset/{file} safe fallback
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.dispatch_api import register_dispatch_routes
from app.services.dispatch_store import dispatch_store


@pytest.fixture
async def binder_dispatch_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    vault = tmp_path / "Vault"
    dispatches = vault / "dispatches"
    tokens_file = tmp_path / "dispatch_tokens.json"

    monkeypatch.setattr(dispatch_store, "root_dir", dispatches)
    monkeypatch.setattr(dispatch_store, "token_index_path", tokens_file)
    dispatches.mkdir(parents=True, exist_ok=True)

    app = web.Application()
    register_dispatch_routes(app)

    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.mark.asyncio
async def test_get_catalog(binder_dispatch_client):
    """GET /api/dispatch/catalog returns structured element library."""
    resp = await binder_dispatch_client.get("/api/dispatch/catalog")
    assert resp.status == 200
    data = await resp.json()

    assert "categories" in data
    assert "cards" in data["categories"]
    assert "bobs" in data["categories"]
    assert "dividers" in data["categories"]


@pytest.mark.asyncio
async def test_create_and_list_by_binder(binder_dispatch_client):
    """POST /api/dispatch/create with binder_id and list by binder."""
    binder_id = "binder_proj_alpha"

    # Create dispatch 1 for binder
    resp1 = await binder_dispatch_client.post("/api/dispatch/create", json={
        "title": "Alpha Dispatch 1",
        "story_markdown": "Card 1\n---\nCard 2",
        "binder_id": binder_id,
        "hero_gif_name": "tape_reel_spinner.gif",
    })
    assert resp1.status == 200
    d1 = await resp1.json()
    assert d1["dispatch"]["binder_id"] == binder_id

    # Create dispatch 2 for binder
    resp2 = await binder_dispatch_client.post("/api/dispatch/create", json={
        "title": "Alpha Dispatch 2",
        "story_markdown": "Welcome",
        "binder_id": binder_id,
    })
    assert resp2.status == 200

    # Query dispatches by binder
    list_resp = await binder_dispatch_client.get(f"/api/dispatch/by-binder/{binder_id}")
    assert list_resp.status == 200
    list_data = await list_resp.json()

    assert list_data["binder_id"] == binder_id
    assert len(list_data["dispatches"]) == 2
    assert list_data["dispatches"][0]["title"] in ("Alpha Dispatch 1", "Alpha Dispatch 2")


@pytest.mark.asyncio
async def test_catalog_asset_safe_fallback(binder_dispatch_client):
    """GET /api/dispatch/catalog/asset/{file} handles traversal and fallback."""
    # Traversal test
    trav_resp = await binder_dispatch_client.get("/api/dispatch/catalog/asset/..%2fsecret")
    assert trav_resp.status in (403, 404)

    # Missing file test (returns fallback 1x1 gif)
    fallback_resp = await binder_dispatch_client.get("/api/dispatch/catalog/asset/nonexistent_test.gif")
    assert fallback_resp.status == 200
    assert fallback_resp.content_type == "image/gif"
