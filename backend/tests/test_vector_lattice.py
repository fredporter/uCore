"""Tests for GridCore Dot Lattice, V2B Quantizer & uVector API.

Verifies:
1. Dot Lattice geometry invariants (1 dot = 4x4 px, square=2x2, tall=3x5, super=6x10).
2. Quantization of 2D points and SVG path coordinates to lattice coordinates.
3. Teletext G1 mosaic quantization (40x25 characters, 2x3 block mosaics).
4. Canonical BOB (Blitter Object) sprite JSON compilation.
"""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.vector_api import register_vector_routes


@pytest.fixture
async def client():
    app = web.Application()
    register_vector_routes(app)
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    yield client
    await client.close()


async def test_vector_lattice_spec(client):
    """Verify dot lattice geometry specification endpoint."""
    resp = await client.get("/api/vector/lattice/spec")
    assert resp.status == 200
    spec = await resp.json()

    assert spec["dot_px"] == 4
    assert "cell_registers" in spec
    square = spec["cell_registers"]["square"]
    assert square["width_px"] == 8
    assert square["height_px"] == 8
    assert square["dots_w"] == 2
    assert square["dots_h"] == 2

    tall = spec["cell_registers"]["tall"]
    assert tall["width_px"] == 12
    assert tall["height_px"] == 20
    assert tall["dots_w"] == 3
    assert tall["dots_h"] == 5

    assert spec["super_cell"]["width_px"] == 24
    assert spec["super_cell"]["height_px"] == 40
    assert spec["teletext_screen"]["columns"] == 40
    assert spec["teletext_screen"]["rows"] == 25


async def test_vector_quantize_lattice_points_and_svg(client):
    """Verify snapping points and SVG path coordinates to the dot lattice."""
    payload = {
        "cell_mode": "dot",  # 4px step
        "points": [[3.1, 7.8], [11.9, 16.2]],
        "svg": '<svg><path d="M 3.2 7.9 L 12.1 15.8 Z"/></svg>',
    }
    resp = await client.post("/api/vector/quantize/lattice", json=payload)
    assert resp.status == 200
    data = await resp.json()

    assert data["step_x_px"] == 4.0
    assert data["step_y_px"] == 4.0
    # [3.1, 7.8] -> [4.0, 8.0]; [11.9, 16.2] -> [12.0, 16.0]
    assert data["snapped_points"] == [[4.0, 8.0], [12.0, 16.0]]
    assert 'd="M 4 8 L 12 16 Z"' in data["snapped_svg"]


async def test_vector_quantize_teletext_g1(client):
    """Verify 40x25 Teletext G1 mosaic quantization."""
    svg = '<svg width="120" height="100"><rect width="120" height="100" fill="#FFFFFF"/></svg>'
    resp = await client.post("/api/vector/quantize/teletext-g1", json={"svg": svg})
    assert resp.status == 200
    data = await resp.json()

    assert data["format"] == "teletext_g1"
    assert data["columns"] == 40
    assert data["rows"] == 25
    assert len(data["plain_text"].splitlines()) == 25


async def test_vector_quantize_bob(client):
    """Verify compiling vector SVG into canonical BOB Blitter definition."""
    svg = '<svg width="32" height="32"><circle cx="16" cy="16" r="10" fill="#E6193C"/></svg>'
    payload = {
        "svg": svg,
        "id": "bob_orb",
        "name": "Orb BOB",
        "palette": "teletext_ceefax",
        "width_dots": 8,
        "height_dots": 8,
    }
    resp = await client.post("/api/vector/quantize/bob", json=payload)
    assert resp.status == 200
    data = await resp.json()

    assert data["status"] == "success"
    bob = data["bob"]
    assert bob["id"] == "bob_orb"
    assert bob["width_dots"] == 8
    assert bob["height_dots"] == 8
    assert bob["width_px"] == 32
    assert bob["height_px"] == 32
    assert len(bob["frames"]) >= 1
    assert len(bob["frames"][0]["dots"]) == 64
    assert bob["fits_budget"] is True
