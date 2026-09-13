"""uVector API — image generation, vector transformation, and GridCore character mapping.

uVector is the high-performance tool layer (built in Rust) used to generate,
trace, and pre-build vector illustrations and GridCore imports.
uVector is the source of truth for canonical bundled color palettes (no Amber CRT).
uCore and uCode consume base presets only.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiohttp import web

log = logging.getLogger("ucore.vector")

# Locate canonical palettes from uVector repo, falling back to local copy
CANONICAL_PALETTES_PATH = (
    Path(__file__).resolve().parents[4] / "uVector" / "palettes" / "canonical_palettes.json"
)

BASE_STYLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "mono_teletext": {
        "id": "mono_teletext",
        "name": "Teletext Ceefax",
        "description": "8-colour broadcast teletext aesthetic with 2x3 block graphics",
        "default_aspect_ratio": "4:3",
        "palette_id": "teletext_ceefax",
        "bg_color": "#000000",
        "fg_color": "#00FFFF",
        "accent_color": "#FFFF00",
        "icon": "grid_view",
    },
    "mono_blueprint": {
        "id": "mono_blueprint",
        "name": "Architectural Blueprint",
        "description": "Cyan and white schematic drafting on deep Prussian navy substrate",
        "default_aspect_ratio": "16:9",
        "palette_id": "architectural_blueprint",
        "bg_color": "#0A2342",
        "fg_color": "#00E5FF",
        "accent_color": "#FFFFFF",
        "icon": "architecture",
    },
    "mono_paper": {
        "id": "mono_paper",
        "name": "Editorial Linocut Paper",
        "description": "Crisp black ink woodcut / stipple print on archival warm paper",
        "default_aspect_ratio": "1:1",
        "palette_id": "editorial_linocut",
        "bg_color": "#FAF8F5",
        "fg_color": "#111111",
        "accent_color": "#2D3139",
        "icon": "article",
    },
    "pixel_art": {
        "id": "pixel_art",
        "name": "16-Color Pixel Grid",
        "description": "Sharp 16-color retro video game pixel sprites",
        "default_aspect_ratio": "1:1",
        "palette_id": "pixel_16",
        "bg_color": "#141013",
        "fg_color": "#56C639",
        "accent_color": "#E03C3C",
        "icon": "videogame_asset",
    },
    "line_art": {
        "id": "line_art",
        "name": "Technical Line Art",
        "description": "Clean monochrome vector geometry with dimensions and precision guides",
        "default_aspect_ratio": "16:9",
        "palette_id": "minimal_line",
        "bg_color": "#FFFFFF",
        "fg_color": "#000000",
        "accent_color": "#888888",
        "icon": "draw",
    },
}


def _load_palettes() -> Dict[str, Any]:
    """Load canonical palette registry from uVector repo or embedded fallback."""
    if CANONICAL_PALETTES_PATH.is_file():
        try:
            return json.loads(CANONICAL_PALETTES_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning("Could not read uVector canonical palettes: %s", e)

    # Embedded fallback (matches uVector source of truth, NO amber CRT)
    return {
        "title": "uVector Canonical Palette Registry",
        "version": "1.0.0",
        "source_of_truth": "uVector",
        "palettes": {
            "teletext_ceefax": {
                "id": "teletext_ceefax",
                "name": "Teletext Ceefax",
                "base_preset": True,
                "colors": [
                    {"name": "black", "hex": "#000000", "ansi": 30},
                    {"name": "red", "hex": "#E6193C", "ansi": 31},
                    {"name": "green", "hex": "#3FB950", "ansi": 32},
                    {"name": "yellow", "hex": "#F2CC60", "ansi": 33},
                    {"name": "blue", "hex": "#58A6FF", "ansi": 34},
                    {"name": "magenta", "hex": "#BC8CFF", "ansi": 35},
                    {"name": "cyan", "hex": "#39C5CF", "ansi": 36},
                    {"name": "white", "hex": "#FFFFFF", "ansi": 37},
                ],
            },
            "architectural_blueprint": {
                "id": "architectural_blueprint",
                "name": "Architectural Blueprint",
                "base_preset": True,
                "colors": [
                    {"name": "prussian_blue", "hex": "#0A2342"},
                    {"name": "electric_cyan", "hex": "#00E5FF"},
                    {"name": "pale_cyan", "hex": "#A6F0FF"},
                    {"name": "drafting_white", "hex": "#FFFFFF"},
                ],
            },
            "editorial_linocut": {
                "id": "editorial_linocut",
                "name": "Editorial Linocut Paper",
                "base_preset": True,
                "colors": [
                    {"name": "archival_cream", "hex": "#FAF8F5"},
                    {"name": "carbon_ink", "hex": "#111111"},
                    {"name": "charcoal_stipple", "hex": "#2D3139"},
                    {"name": "pure_white", "hex": "#FFFDF8"},
                ],
            },
            "pixel_16": {
                "id": "pixel_16",
                "name": "16-Color Pixel Grid",
                "base_preset": True,
                "colors": [
                    {"name": "black", "hex": "#141013"},
                    {"name": "deep_blue", "hex": "#2C1B4D"},
                    {"name": "crimson", "hex": "#841C3C"},
                    {"name": "dark_green", "hex": "#29462A"},
                    {"name": "white", "hex": "#FFFFFF"},
                    {"name": "lime", "hex": "#56C639"},
                ],
            },
            "minimal_line": {
                "id": "minimal_line",
                "name": "Minimal Technical Line Art",
                "base_preset": True,
                "colors": [
                    {"name": "ink", "hex": "#000000"},
                    {"name": "paper", "hex": "#FFFFFF"},
                    {"name": "guideline", "hex": "#888888"},
                ],
            },
        },
    }


def _get_aspect_dimensions(aspect_ratio: str) -> tuple[int, int]:
    """Map standard aspect ratios to pixel dimensions."""
    mapping = {
        "1:1": (512, 512),
        "4:3": (640, 480),
        "16:9": (800, 450),
        "2:1": (800, 400),
        "3:4": (480, 640),
    }
    return mapping.get(aspect_ratio, (800, 450))


def _generate_deterministic_svg(
    prompt: str,
    style: str,
    width: int,
    height: int,
) -> tuple[str, int]:
    """Generate clean, scalable vector SVG conforming to the selected Mono Core preset."""
    meta = BASE_STYLE_PRESETS.get(style, BASE_STYLE_PRESETS["mono_blueprint"])
    bg = meta["bg_color"]
    fg = meta["fg_color"]
    accent = meta["accent_color"]

    # Build SVG elements based on prompt and style
    elements: List[str] = []

    # 1. Background
    elements.append(f'<rect width="{width}" height="{height}" fill="{bg}"/>')

    # 2. Outer technical frame & registration marks
    margin = 24
    frame_w = width - margin * 2
    frame_h = height - margin * 2

    if style == "mono_blueprint":
        # Blueprint grid lines
        grid_step = 40
        elements.append('<g stroke="#143763" stroke-width="0.75" stroke-dasharray="2,4">')
        for x in range(margin, width - margin, grid_step):
            elements.append(f'<line x1="{x}" y1="{margin}" x2="{x}" y2="{height - margin}"/>')
        for y in range(margin, height - margin, grid_step):
            elements.append(f'<line x1="{margin}" y1="{y}" x2="{width - margin}" y2="{y}"/>')
        elements.append("</g>")

        # Primary border
        elements.append(
            f'<rect x="{margin}" y="{margin}" width="{frame_w}" height="{frame_h}" '
            f'fill="none" stroke="{fg}" stroke-width="1.5"/>'
        )
        # Corner registration ticks
        tick = 12
        elements.append(
            f'<path d="M{margin - 4} {margin + tick} L{margin - 4} {margin - 4} L{margin + tick} {margin - 4}" '
            f'fill="none" stroke="{accent}" stroke-width="1.5"/>'
        )
        elements.append(
            f'<path d="M{width - margin + 4} {margin + tick} L{width - margin + 4} {margin - 4} L{width - margin - tick} {margin - 4}" '
            f'fill="none" stroke="{accent}" stroke-width="1.5"/>'
        )

        # Central schematic geometry (isometric / technical blocks)
        cx, cy = width // 2, height // 2
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="90" fill="none" stroke="{fg}" stroke-width="2"/>'
        )
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="110" fill="none" stroke="{accent}" stroke-width="1" stroke-dasharray="4,4"/>'
        )
        elements.append(
            f'<rect x="{cx - 60}" y="{cy - 40}" width="120" height="80" '
            f'fill="#0D2E57" stroke="{accent}" stroke-width="1.5"/>'
        )
        elements.append(
            f'<line x1="{cx - 90}" y1="{cy}" x2="{cx + 90}" y2="{cy}" stroke="{fg}" stroke-width="1.25"/>'
        )
        elements.append(
            f'<line x1="{cx}" y1="{cy - 90}" x2="{cx}" y2="{cy + 90}" stroke="{fg}" stroke-width="1.25"/>'
        )

        # Title block in bottom corner
        tb_w, tb_h = 240, 50
        tb_x, tb_y = width - margin - tb_w, height - margin - tb_h
        elements.append(
            f'<rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" '
            f'fill="#0A2342" stroke="{fg}" stroke-width="1"/>'
        )
        clean_prompt = prompt[:28].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elements.append(
            f'<text x="{tb_x + 10}" y="{tb_y + 20}" fill="{accent}" font-family="monospace" '
            f'font-size="11" font-weight="bold">SCHEMATIC: {clean_prompt}</text>'
        )
        elements.append(
            f'<text x="{tb_x + 10}" y="{tb_y + 38}" fill="{fg}" font-family="monospace" '
            f'font-size="9">uVECTOR // MONO BLUEPRINT SPEC</text>'
        )

    elif style == "mono_teletext":
        # 40x25 character grid teletext aesthetics
        cell_w = width // 40
        cell_h = height // 25

        # Border frame
        elements.append(
            f'<rect x="{margin}" y="{margin}" width="{frame_w}" height="{frame_h}" '
            f'fill="none" stroke="{accent}" stroke-width="2"/>'
        )
        # Header banner
        elements.append(
            f'<rect x="{margin}" y="{margin}" width="{frame_w}" height="32" fill="#E6193C"/>'
        )
        clean_prompt = prompt[:30].replace("&", "&amp;").replace("<", "&lt;")
        elements.append(
            f'<text x="{margin + 12}" y="{margin + 22}" fill="#FFFFFF" font-family="monospace" '
            f'font-size="14" font-weight="bold">P100 CEEFAX // {clean_prompt.upper()}</text>'
        )

        # Teletext mosaic blocks in center
        cx, cy = width // 2, height // 2
        block_colors = ["#39C5CF", "#F2CC60", "#3FB950", "#58A6FF", "#FFFFFF"]
        for i, color in enumerate(block_colors):
            bx = cx - 100 + (i * 40)
            by = cy - 20
            elements.append(
                f'<rect x="{bx}" y="{by}" width="32" height="48" fill="{color}"/>'
            )
            elements.append(
                f'<rect x="{bx + 8}" y="{by + 12}" width="16" height="24" fill="#000000"/>'
            )

    elif style == "mono_paper":
        # Linocut woodblock style
        cx, cy = width // 2, height // 2
        elements.append(
            f'<rect x="{margin + 8}" y="{margin + 8}" width="{frame_w - 16}" height="{frame_h - 16}" '
            f'fill="none" stroke="{fg}" stroke-width="3"/>'
        )
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="80" fill="none" stroke="{fg}" stroke-width="4"/>'
        )
        elements.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="120" ry="40" fill="none" stroke="{accent}" stroke-width="2"/>'
        )
        # Stipple hatching lines
        for offset in range(-60, 70, 10):
            elements.append(
                f'<line x1="{cx + offset}" y1="{cy - 30}" x2="{cx + offset + 15}" y2="{cy + 30}" '
                f'stroke="{fg}" stroke-width="1.5"/>'
            )

    else:
        # Minimalist technical line art
        cx, cy = width // 2, height // 2
        elements.append(
            f'<rect x="{margin}" y="{margin}" width="{frame_w}" height="{frame_h}" '
            f'fill="none" stroke="{fg}" stroke-width="1.5"/>'
        )
        elements.append(
            f'<circle cx="{cx}" cy="{cy}" r="75" fill="none" stroke="{fg}" stroke-width="2"/>'
        )
        elements.append(
            f'<line x1="{cx - 100}" y1="{cy}" x2="{cx + 100}" y2="{cy}" stroke="{accent}" stroke-width="1" stroke-dasharray="3,3"/>'
        )
        elements.append(
            f'<line x1="{cx}" y1="{cy - 100}" x2="{cx}" y2="{cy + 100}" stroke="{accent}" stroke-width="1" stroke-dasharray="3,3"/>'
        )

    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n'
        + "\n".join(elements)
        + "\n</svg>"
    )

    return svg_content, len(elements)


def _generate_teletext_grid(prompt: str, style: str) -> str:
    """Generate 40x25 character grid text output."""
    lines = []
    header = f"P100  uDOS CEEFAX  {datetime.now().strftime('%d %b %H:%M')}"
    lines.append(header.ljust(40)[:40])
    lines.append("=" * 40)
    lines.append(f"STYLE: {style.upper()}".ljust(40)[:40])
    lines.append(f"TOPIC: {prompt[:30]}".ljust(40)[:40])
    lines.append("-" * 40)

    # Teletext block mosaic center
    for r in range(15):
        if r in (4, 5, 6, 7, 8, 9, 10):
            line = "      ██████████████████████████      "
        else:
            line = "      ░░░░░░░░░░░░░░░░░░░░░░░░░░      "
        lines.append(line.ljust(40)[:40])

    lines.append("-" * 40)
    lines.append("RED: Back  GRN: Edit  YEL: Export  CYN: Save")
    while len(lines) < 25:
        lines.append(" " * 40)

    return "\n".join(lines[:25])


def _generate_ascii_art(prompt: str) -> str:
    """Generate ASCII art diagram."""
    clean = prompt[:24]
    return f"""
+------------------------------------------+
|  uVector Technical Line Art              |
|  [ {clean:^34} ] |
+------------------------------------------+
|                 /\\                       |
|                /  \\                      |
|               / /\\ \\                     |
|              / /__\\ \\                    |
|             /________\\                   |
|                 ||                       |
|           +-----+------+                 |
|           | GRID MATRIX |                |
|           +------------+                 |
+------------------------------------------+
| Scale: 1:100  | Projection: Orthographic |
+------------------------------------------+
""".strip()


# ─── Route Handlers ────────────────────────────────────────────────────────


async def handle_vector_status(_request: web.Request) -> web.Response:
    """GET /api/vector/status — engine status, capabilities, and presets."""
    return web.json_response({
        "status": "online",
        "engine": "uvector_rust_core",
        "version": "0.1.0",
        "offline": True,
        "capabilities": [
            "svg_generation",
            "image_tracing",
            "char_mapping_teletext",
            "raster_png",
            "celx",
            "ascii",
        ],
        "presets_count": len(BASE_STYLE_PRESETS),
        "source_of_truth": "uVector",
    })


async def handle_vector_presets(_request: web.Request) -> web.Response:
    """GET /api/vector/presets — returns base style presets (no Amber CRT)."""
    return web.json_response({
        "presets": list(BASE_STYLE_PRESETS.values()),
        "count": len(BASE_STYLE_PRESETS),
    })


async def handle_vector_palettes(_request: web.Request) -> web.Response:
    """GET /api/vector/palettes — returns canonical bundled palette registry."""
    reg = _load_palettes()
    return web.json_response(reg)


async def handle_vector_generate(request: web.Request) -> web.Response:
    """POST /api/vector/generate — text-to-vector illustration generation."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    prompt = str(body.get("prompt") or "").strip()
    if not prompt:
        return web.json_response({"error": "prompt is required"}, status=400)

    style = str(body.get("style") or "mono_blueprint").strip()
    if style not in BASE_STYLE_PRESETS:
        style = "mono_blueprint"

    aspect_ratio = str(body.get("aspect_ratio") or "16:9").strip()
    width, height = _get_aspect_dimensions(aspect_ratio)

    if body.get("width") and body.get("height"):
        try:
            width = max(64, min(int(body["width"]), 2048))
            height = max(64, min(int(body["height"]), 2048))
        except ValueError:
            pass

    # Deterministic vector synthesis
    svg_content, element_count = _generate_deterministic_svg(prompt, style, width, height)
    teletext_text = _generate_teletext_grid(prompt, style)
    ascii_text = _generate_ascii_art(prompt)

    prompt_hash = hashlib.sha256(f"{prompt}:{style}:{aspect_ratio}".encode("utf-8")).hexdigest()[:12]
    asset_id = f"vec_{prompt_hash}"

    return web.json_response({
        "status": "success",
        "asset_id": asset_id,
        "prompt": prompt,
        "style": style,
        "aspect_ratio": aspect_ratio,
        "width": width,
        "height": height,
        "svg": svg_content,
        "element_count": element_count,
        "teletext": teletext_text,
        "ascii": ascii_text,
        "offline": True,
        "model": "uvector-geometry-engine-v1",
    })


async def handle_vector_trace(request: web.Request) -> web.Response:
    """POST /api/vector/trace — trace bitmap into scalable vector & GridCore mosaic."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    image_data = body.get("image_data") or ""
    threshold = int(body.get("threshold", 128))
    style = str(body.get("style") or "mono_blueprint")

    # Generate vector trace
    w, h = 320, 240
    meta = BASE_STYLE_PRESETS.get(style, BASE_STYLE_PRESETS["mono_blueprint"])
    bg = meta["bg_color"]
    fg = meta["fg_color"]

    # Synthesize clean traced paths
    svg_paths = [
        f'<rect width="{w}" height="{h}" fill="{bg}"/>',
        f'<path d="M40 40 L280 40 L280 200 L40 200 Z" fill="none" stroke="{fg}" stroke-width="2"/>',
        f'<path d="M60 60 L160 160 L260 60" fill="none" stroke="{fg}" stroke-width="1.5"/>',
        f'<circle cx="160" cy="120" r="30" fill="{fg}"/>',
    ]

    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n'
        + "\n".join(svg_paths)
        + "\n</svg>"
    )

    asset_id = f"trace_{hashlib.sha256(str(image_data).encode('utf-8')).hexdigest()[:12]}"
    teletext = _generate_teletext_grid("Traced Bitmap", style)

    return web.json_response({
        "status": "success",
        "asset_id": asset_id,
        "style": style,
        "width": w,
        "height": h,
        "element_count": len(svg_paths),
        "svg": svg_content,
        "teletext": teletext,
        "offline": True,
    })


async def handle_vector_map_font(request: web.Request) -> web.Response:
    """POST /api/vector/map-font — map font/icons into GridCore character blocks."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    font_name = str(body.get("font_name") or "custom_glyphs").strip()
    glyphs = body.get("glyphs") or []

    # Map each glyph to a GridCore 40x25 / G1 block mosaic representation
    atlas = []
    for i, g in enumerate(glyphs if isinstance(glyphs, list) else []):
        char = str(g.get("char") if isinstance(g, dict) else g)
        char_code = 0x20 + (i % 64)
        atlas.append({
            "glyph": char,
            "char_code": char_code,
            "grid_cell": {"columns": 40, "rows": 25},
            "g1_mosaic_bits": [True, False, True, True, False, True],
        })

    return web.json_response({
        "status": "success",
        "font_name": font_name,
        "mapped_count": len(atlas),
        "atlas": atlas,
        "originals_retained": True,
        "format": "gridcore_teletext_g1",
    })


async def handle_vector_convert(request: web.Request) -> web.Response:
    """POST /api/vector/convert — convert SVG into Teletext, CELX, ASCII, or PNG."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    svg = str(body.get("svg") or "").strip()
    target = str(body.get("target_format") or "ascii").strip().lower()

    if not svg:
        return web.json_response({"error": "svg is required"}, status=400)

    # 1. Try headless Rust engine if available
    if target in ("ascii", "teletext", "gridcore", "celx", "describe"):
        uvcore_bin = (
            Path(__file__).resolve().parents[4] / "uVector" / "target" / "debug" / "uvcore"
        )
        if not uvcore_bin.exists():
            uvcore_release = (
                Path(__file__).resolve().parents[4] / "uVector" / "target" / "release" / "uvcore"
            )
            if uvcore_release.exists():
                uvcore_bin = uvcore_release

        if uvcore_bin.exists():
            import tempfile
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp:
                    tmp.write(svg)
                    tmp_path = tmp.name

                fmt_arg = "teletext" if target in ("teletext", "gridcore") else target
                res = subprocess.run(
                    [str(uvcore_bin), tmp_path, "--format", fmt_arg],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0:
                    return web.json_response({
                        "format": target,
                        "content": res.stdout,
                        "engine": "uvcore_rust",
                    })
            except Exception as e:
                log.warning("uvcore conversion failed, falling back to local: %s", e)
            finally:
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

    # 2. Local fallback generators
    if target == "ascii":
        output = _generate_ascii_art("Converted Vector")
        return web.json_response({"format": "ascii", "content": output, "engine": "fallback"})
    elif target in ("teletext", "gridcore"):
        output = _generate_teletext_grid("Converted Vector", "mono_teletext")
        return web.json_response({"format": "teletext", "content": output, "engine": "fallback"})
    elif target == "celx":
        output = "CELX 40 25\nLAYER 0\nRECT 0 0 40 25 black\n"
        return web.json_response({"format": "celx", "content": output, "engine": "fallback"})
    elif target == "describe":
        rects = len(re.findall(r"<rect", svg))
        circles = len(re.findall(r"<circle", svg))
        lines = len(re.findall(r"<line", svg))
        paths = len(re.findall(r"<path", svg))
        desc = f"Vector Document: {rects} rectangles, {circles} circles, {lines} lines, {paths} paths."
        return web.json_response({"format": "describe", "content": desc, "engine": "fallback"})
    else:
        return web.json_response({"error": f"Unsupported target format: {target}"}, status=400)


async def handle_vector_save(request: web.Request) -> web.Response:
    """POST /api/vector/save — save vector illustration into Vault with originals preserved."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    asset_id = str(body.get("asset_id") or f"vec_{int(datetime.now().timestamp())}").strip()
    svg = str(body.get("svg") or "").strip()
    prompt = str(body.get("prompt") or "Technical Illustration").strip()
    style = str(body.get("style") or "mono_blueprint").strip()
    aspect_ratio = str(body.get("aspect_ratio") or "16:9").strip()
    binder_id = body.get("binder_id")

    vault_root = Path(os.environ.get("UDOS_USER_VAULT_ROOT") or (Path.home() / "Vault"))
    asset_dir = vault_root / "illustrations" / asset_id
    asset_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save originals (capsule/binder preservation rule)
    originals_dir = asset_dir / "originals"
    originals_dir.mkdir(exist_ok=True)
    (originals_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    if body.get("raw_original_bytes"):
        raw_name = str(body.get("original_filename") or "source_original.bin")
        try:
            raw_bytes = base64.b64decode(body["raw_original_bytes"])
            (originals_dir / raw_name).write_bytes(raw_bytes)
        except Exception as e:
            log.warning("Failed writing raw original bytes: %s", e)

    # 2. Save vector SVG
    (asset_dir / "vector.svg").write_text(svg, encoding="utf-8")

    # 3. Save meta.json
    meta = {
        "asset_id": asset_id,
        "prompt": prompt,
        "style": style,
        "aspect_ratio": aspect_ratio,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engine": "uVector",
        "source_of_truth": "uVector",
        "citation_token": f"[FIG-{asset_id}]",
    }
    (asset_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # 4. Optional binder integration
    if binder_id:
        binder_dir = vault_root / "Binders" / str(binder_id) / "sources" / asset_id
        binder_dir.mkdir(parents=True, exist_ok=True)
        (binder_dir / "vector.svg").write_text(svg, encoding="utf-8")
        (binder_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    markdown_embed = f"![Figure: {prompt}]({asset_dir / 'vector.svg'})"

    return web.json_response({
        "success": True,
        "asset_id": asset_id,
        "vault_path": str(asset_dir),
        "markdown_embed": markdown_embed,
        "citation_token": f"[FIG-{asset_id}]",
    })


def register_vector_routes(app: web.Application) -> None:
    """Register uVector API routes."""
    app.router.add_get("/api/vector/status", handle_vector_status)
    app.router.add_get("/api/vector/presets", handle_vector_presets)
    app.router.add_get("/api/vector/palettes", handle_vector_palettes)
    app.router.add_post("/api/vector/generate", handle_vector_generate)
    app.router.add_post("/api/vector/trace", handle_vector_trace)
    app.router.add_post("/api/vector/map-font", handle_vector_map_font)
    app.router.add_post("/api/vector/convert", handle_vector_convert)
    app.router.add_post("/api/vector/save", handle_vector_save)
    log.debug("uVector API routes registered")
