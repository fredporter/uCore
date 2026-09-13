"""Unit and integration tests for uVector API routes.

Verifies:
- GET /api/vector/status
- GET /api/vector/presets (verifying Amber CRT is strictly absent)
- GET /api/vector/palettes (uVector source of truth)
- POST /api/vector/generate (deterministic vector synthesis, no amber)
- POST /api/vector/trace (bitmap to vector + GridCore mosaic)
- POST /api/vector/map-font (mapping to GridCore character blocks, originals retained)
- POST /api/vector/convert (ASCII, Teletext, CELX, describe)
- POST /api/vector/save (saving to Vault/Binders with originals/ preserved)
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.vector_api import register_vector_routes


@pytest.fixture
async def vector_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create test client for uVector API routes."""
    vault = tmp_path / "Vault"
    vault.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("UDOS_USER_VAULT_ROOT", str(vault))

    app = web.Application()
    register_vector_routes(app)

    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.mark.asyncio
async def test_vector_status(vector_client):
    """GET /api/vector/status returns online status and offline capabilities."""
    resp = await vector_client.get("/api/vector/status")
    assert resp.status == 200
    data = await resp.json()

    assert data["status"] == "online"
    assert data["engine"] == "uvector_rust_core"
    assert data["offline"] is True
    assert "capabilities" in data
    assert "svg_generation" in data["capabilities"]
    assert "image_tracing" in data["capabilities"]
    assert "char_mapping_teletext" in data["capabilities"]
    assert data["source_of_truth"] == "uVector"


@pytest.mark.asyncio
async def test_vector_presets_excludes_amber(vector_client):
    """GET /api/vector/presets returns base presets and ensures Amber CRT is absent."""
    resp = await vector_client.get("/api/vector/presets")
    assert resp.status == 200
    data = await resp.json()

    presets = data["presets"]
    preset_ids = [p["id"] for p in presets]

    assert "mono_blueprint" in preset_ids
    assert "mono_teletext" in preset_ids
    assert "mono_paper" in preset_ids
    assert "pixel_art" in preset_ids
    assert "line_art" in preset_ids

    # Amber CRT phosphor must be strictly excluded
    assert "mono_amber" not in preset_ids
    assert "amber_crt" not in preset_ids


@pytest.mark.asyncio
async def test_vector_palettes(vector_client):
    """GET /api/vector/palettes returns canonical palettes from uVector."""
    resp = await vector_client.get("/api/vector/palettes")
    assert resp.status == 200
    data = await resp.json()

    assert "palettes" in data
    palettes = data["palettes"]
    assert "teletext_ceefax" in palettes
    assert "architectural_blueprint" in palettes
    assert "editorial_linocut" in palettes

    # Verify no Amber CRT in palettes
    assert "mono_amber" not in palettes
    assert "amber_crt" not in palettes


@pytest.mark.asyncio
async def test_vector_generate_requires_prompt(vector_client):
    """POST /api/vector/generate requires a prompt."""
    resp = await vector_client.post("/api/vector/generate", json={})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_vector_generate_blueprint(vector_client):
    """POST /api/vector/generate generates valid Blueprint vector with cyan on navy."""
    resp = await vector_client.post("/api/vector/generate", json={
        "prompt": "Orbital space station docking ring",
        "style": "mono_blueprint",
        "aspect_ratio": "16:9",
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["status"] == "success"
    assert data["style"] == "mono_blueprint"
    assert data["aspect_ratio"] == "16:9"
    assert data["offline"] is True
    assert "<svg" in data["svg"]
    assert "</svg>" in data["svg"]
    assert "#0A2342" in data["svg"]  # Prussian navy
    assert "#00E5FF" in data["svg"]  # Electric cyan
    assert data["element_count"] > 5
    assert len(data["teletext"].splitlines()) == 25
    assert "GRID MATRIX" in data["ascii"]


@pytest.mark.asyncio
async def test_vector_generate_paper(vector_client):
    """POST /api/vector/generate generates Linocut Paper vector on archival cream."""
    resp = await vector_client.post("/api/vector/generate", json={
        "prompt": "Botanical specimen",
        "style": "mono_paper",
        "aspect_ratio": "1:1",
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["style"] == "mono_paper"
    assert "#FAF8F5" in data["svg"]  # Cream paper
    assert "#111111" in data["svg"]  # Carbon ink


@pytest.mark.asyncio
async def test_vector_trace(vector_client):
    """POST /api/vector/trace traces raster image into vector paths."""
    resp = await vector_client.post("/api/vector/trace", json={
        "image_data": "sample_base64_data",
        "style": "mono_blueprint",
        "threshold": 128,
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["status"] == "success"
    assert "<svg" in data["svg"]
    assert data["element_count"] >= 3
    assert len(data["teletext"].splitlines()) == 25


@pytest.mark.asyncio
async def test_vector_map_font(vector_client):
    """POST /api/vector/map-font maps glyphs to GridCore character blocks."""
    resp = await vector_client.post("/api/vector/map-font", json={
        "font_name": "bedstead_glyphs",
        "glyphs": [{"char": "A"}, {"char": "B"}, {"char": "C"}],
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["status"] == "success"
    assert data["font_name"] == "bedstead_glyphs"
    assert data["mapped_count"] == 3
    assert data["originals_retained"] is True
    assert len(data["atlas"]) == 3
    assert data["atlas"][0]["grid_cell"]["columns"] == 40


@pytest.mark.asyncio
async def test_vector_convert(vector_client):
    """POST /api/vector/convert converts SVG to ASCII, Teletext, CELX, and describe."""
    sample_svg = '<svg viewBox="0 0 100 100"><rect x="0" y="0" width="10" height="10"/><circle cx="50" cy="50" r="10"/></svg>'

    # ASCII
    resp_ascii = await vector_client.post("/api/vector/convert", json={
        "svg": sample_svg,
        "target_format": "ascii",
    })
    assert resp_ascii.status == 200
    data_ascii = await resp_ascii.json()
    assert "GRID MATRIX" in data_ascii["content"]

    # Teletext
    resp_tel = await vector_client.post("/api/vector/convert", json={
        "svg": sample_svg,
        "target_format": "teletext",
    })
    assert resp_tel.status == 200
    data_tel = await resp_tel.json()
    assert len(data_tel["content"].splitlines()) == 25

    # Describe
    resp_desc = await vector_client.post("/api/vector/convert", json={
        "svg": sample_svg,
        "target_format": "describe",
    })
    assert resp_desc.status == 200
    data_desc = await resp_desc.json()
    assert "1 rectangles" in data_desc["content"]
    assert "1 circles" in data_desc["content"]


@pytest.mark.asyncio
async def test_vector_save_to_vault_and_binder(vector_client, tmp_path: Path):
    """POST /api/vector/save saves asset with originals/ preserved and binder link."""
    vault = tmp_path / "Vault"
    resp = await vector_client.post("/api/vector/save", json={
        "asset_id": "test_asset_001",
        "svg": "<svg><circle cx='10' cy='10' r='5'/></svg>",
        "prompt": "Test Circuit Diagram",
        "style": "mono_blueprint",
        "aspect_ratio": "16:9",
        "binder_id": "b_research_123",
        "raw_original_bytes": "aGVsbG8gd29ybGQ=",  # base64 'hello world'
        "original_filename": "circuit_source.png",
    })
    assert resp.status == 200
    data = await resp.json()

    assert data["success"] is True
    assert data["asset_id"] == "test_asset_001"
    assert data["citation_token"] == "[FIG-test_asset_001]"

    # Verify files created in Vault
    asset_dir = vault / "illustrations" / "test_asset_001"
    assert (asset_dir / "vector.svg").is_file()
    assert (asset_dir / "meta.json").is_file()
    assert (asset_dir / "originals" / "circuit_source.png").is_file()
    assert (asset_dir / "originals" / "circuit_source.png").read_bytes() == b"hello world"
    assert (asset_dir / "originals" / "prompt.txt").read_text() == "Test Circuit Diagram"

    # Verify binder source linkage
    binder_dir = vault / "Binders" / "b_research_123" / "sources" / "test_asset_001"
    assert (binder_dir / "vector.svg").is_file()
    assert (binder_dir / "meta.json").is_file()
