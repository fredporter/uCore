/**
 * Bitmap Glyph Renderer — pixel-crisp character generator.
 *
 * Pre-renders a source font (MODE7GX3, Press Start 2P, …) to a binary
 * glyph bitmap via an offscreen canvas, then renders that bitmap into a
 * target cell with **uniform integer scaling** (true square pixels) and
 * **centring** — no anti-aliasing, no non-uniform stretch.
 *
 * Pipeline:
 *   font → offscreen canvas (glyphW·S × glyphH·S) → threshold → glyphW×glyphH bitmap
 *   → cache → render: NN scale → glyphW·scale × glyphH·scale, centred in cell
 *
 * Teletext (MODE7GX3) glyphs are 12×16 (the font's native advance:em aspect,
 * taller than wide). Terminal (Press Start 2P) glyphs are 8×8. Mosaic blocks
 * (2×3) are generated algorithmically for G0 codes 0x60–0x7F and common
 * Unicode block glyphs.
 *
 * @see docs/GRIDUI_RENDERING_CONTRACT.md
 */

import type { GlyphAtlas } from "./glyph-atlas";

/* ─── Types ────────────────────────────────────────────────────── */

/** A binary glyph bitmap — each byte is 0 (background) or 1 (foreground). */
export type G0Bitmap = Uint8Array;

/** Configuration for a bitmap glyph renderer. */
export interface BitmapGlyphSpec {
  /** Native glyph width in source pixels. */
  glyphW: number;
  /** Native glyph height in source pixels. */
  glyphH: number;
  /** CSS font-family used to rasterise the source glyph. */
  fontFamily: string;
  /** Oversampling factor for the offscreen raster (default 4). */
  cacheScale?: number;
  /** Em-size multiplier so the glyph fills the glyphW×glyphH grid (default 1). */
  fontScale?: number;
  /** Generate 2×3 mosaic blocks for G0 block codes instead of a font glyph. */
  mosaic?: boolean;
  /** Pre-baked glyph atlas. When present, glyphs are read from the atlas. */
  atlas?: GlyphAtlas;
}

/* ─── Mosaic mapping ───────────────────────────────────────────── */

/**
 * 2×3 sextant digit strings, indexed by codepoint − 0x1FB00.
 * Covers U+1FB00–U+1FB3B (all 60 non-empty 2×3 block patterns).
 * Digits: 1=top-left 2=top-right 3=mid-left 4=mid-right 5=bottom-left 6=bottom-right.
 */
const SEXTANT_PATTERNS: string[] = [
  "1",
  "2",
  "12",
  "3",
  "13",
  "23",
  "123",
  "4",
  "14",
  "24",
  "124",
  "34",
  "134",
  "234",
  "1234",
  "5",
  "15",
  "25",
  "125",
  "35",
  "235",
  "1235",
  "45",
  "145",
  "245",
  "1245",
  "345",
  "1345",
  "2345",
  "12345",
  "6",
  "16",
  "26",
  "126",
  "36",
  "136",
  "236",
  "1236",
  "46",
  "146",
  "246",
  "1246",
  "346",
  "1346",
  "2346",
  "12346",
  "56",
  "156",
  "256",
  "1256",
  "356",
  "1356",
  "2356",
  "12356",
  "456",
  "1456",
  "2456",
  "12456",
  "3456",
  "123456",
];

/** Convert a digit string (e.g. "124") to a 6-bit mosaic pattern. */
function digitsToPattern(digits: string): number {
  let pattern = 0;
  for (const ch of digits) {
    const d = ch.charCodeAt(0) - 48; // '1'..'6'
    if (d >= 1 && d <= 6) pattern |= 1 << (d - 1);
  }
  return pattern;
}

/** 6-bit pattern for a character code (Unicode block / sextant glyphs). */
function mosaicPattern(charCode: number): number | null {
  // NOTE: the teletext G0 0x60–0x7F codes are NOT intercepted here — the
  // buffer carries Unicode chars, and 0x60–0x7F is ASCII (a–z, `, {…}),
  // which must render as font glyphs, not mosaic blocks.

  // 2×3 sextant block (U+1FB00–U+1FB3B) → exact 6-bit pattern.
  if (charCode >= 0x1fb00 && charCode <= 0x1fb3b) {
    const idx = charCode - 0x1fb00;
    return digitsToPattern(SEXTANT_PATTERNS[idx]);
  }

  switch (charCode) {
    case 0x2588: // █ full block
      return 0x3f;
    case 0x2580: // ▀ upper half
      return 0x0f;
    case 0x2584: // ▄ lower half
      return 0x3c;
    case 0x258c: // ▌ left half
      return 0x15;
    case 0x2590: // ▐ right half
      return 0x2a;
    case 0x2b1b: // ⬛ full block
      return 0x3f;
    default:
      return null;
  }
}

/* ─── Renderer ─────────────────────────────────────────────────── */

export class BitmapGlyphRenderer {
  private _glyphW: number;
  private _glyphH: number;
  private _fontFamily: string;
  private _cacheScale: number;
  private _fontScale: number;
  private _mosaic: boolean;
  private _atlas: GlyphAtlas | null;
  private _glyphCache = new Map<number, G0Bitmap>();
  private _canvas: HTMLCanvasElement;
  private _ctx: CanvasRenderingContext2D;

  constructor(spec: BitmapGlyphSpec) {
    this._glyphW = spec.glyphW;
    this._glyphH = spec.glyphH;
    this._fontFamily = spec.fontFamily;
    this._cacheScale = spec.cacheScale ?? 4;
    this._fontScale = spec.fontScale ?? 1;
    this._mosaic = spec.mosaic ?? false;
    this._atlas = spec.atlas ?? null;

    this._canvas = document.createElement("canvas");
    this._canvas.width = this._glyphW * this._cacheScale;
    this._canvas.height = this._glyphH * this._cacheScale;
    const ctx = this._canvas.getContext("2d");
    if (!ctx)
      throw new Error("Failed to create offscreen canvas for glyph renderer");
    this._ctx = ctx;
  }

  get glyphW(): number {
    return this._glyphW;
  }

  get glyphH(): number {
    return this._glyphH;
  }

  /**
   * Get (or generate and cache) a binary glyph bitmap for the character code.
   */
  getBitmap(charCode: number): G0Bitmap {
    const cached = this._glyphCache.get(charCode);
    if (cached) return cached;

    const bitmap = this._generateBitmap(charCode);
    this._glyphCache.set(charCode, bitmap);
    return bitmap;
  }

  /**
   * Render a glyph into a cell on the target canvas.
   *
   * All coordinates and dimensions are in **device pixels** (already
   * multiplied by devicePixelRatio). The glyph is scaled by the largest
   * uniform integer factor that fits the cell, then centred — producing
   * perfectly square, non-anti-aliased pixels.
   *
   * @param ctx - Target canvas 2D context
   * @param cellX - Cell left edge (device px)
   * @param cellY - Cell top edge (device px)
   * @param cellW - Cell width (device px)
   * @param cellH - Cell height (device px)
   * @param charCode - Character code to render
   * @param fg - Foreground hex colour
   */
  render(
    ctx: CanvasRenderingContext2D,
    cellX: number,
    cellY: number,
    cellW: number,
    cellH: number,
    charCode: number,
    fg: string,
  ): void {
    const bitmap = this.getBitmap(charCode);

    // Largest uniform integer scale that fits the glyph in the cell.
    const scale = Math.max(
      1,
      Math.floor(Math.min(cellW / this._glyphW, cellH / this._glyphH)),
    );
    const gw = this._glyphW * scale;
    const gh = this._glyphH * scale;
    const ox = Math.floor((cellW - gw) / 2);
    const oy = Math.floor((cellH - gh) / 2);
    const px = Math.round(cellX) + ox;
    const py = Math.round(cellY) + oy;

    ctx.fillStyle = fg;
    for (let row = 0; row < this._glyphH; row++) {
      const y = py + row * scale;
      for (let col = 0; col < this._glyphW; col++) {
        if (bitmap[row * this._glyphW + col] === 1) {
          ctx.fillRect(px + col * scale, y, scale, scale);
        }
      }
    }
  }

  /**
   * Render one half of a double-height glyph into a cell.
   *
   * A double-height character is a glyph scaled 2× vertically and split
   * across two stacked cells: the upper cell shows the glyph's top half,
   * the lower cell its bottom half. Each half is stretched to fill its own
   * cell height (glyphH/2 source rows × 2·scale device rows each).
   */
  renderHalf(
    ctx: CanvasRenderingContext2D,
    cellX: number,
    cellY: number,
    cellW: number,
    cellH: number,
    charCode: number,
    fg: string,
    half: "top" | "bottom",
  ): void {
    const bitmap = this.getBitmap(charCode);

    const scale = Math.max(
      1,
      Math.floor(Math.min(cellW / this._glyphW, cellH / this._glyphH)),
    );
    const gw = this._glyphW * scale;
    const ox = Math.floor((cellW - gw) / 2);
    const px = Math.round(cellX) + ox;
    const py = Math.round(cellY);

    const halfRows = Math.floor(this._glyphH / 2);
    const startRow = half === "top" ? 0 : halfRows;
    const endRow = half === "top" ? halfRows : this._glyphH;
    const vScale = scale * 2; // each source row stretches to fill 2× scale

    ctx.fillStyle = fg;
    for (let row = startRow; row < endRow; row++) {
      const y = py + (row - startRow) * vScale;
      for (let col = 0; col < this._glyphW; col++) {
        if (bitmap[row * this._glyphW + col] === 1) {
          ctx.fillRect(px + col * scale, y, scale, vScale);
        }
      }
    }
  }

  /** Clear the glyph cache (e.g. after a font change). */
  clearCache(): void {
    this._glyphCache.clear();
  }

  /* ─── Bitmap generation ──────────────────────────────────────── */

  private _generateBitmap(charCode: number): G0Bitmap {
    const bitmap = new Uint8Array(this._glyphW * this._glyphH);

    const pattern = this._mosaic ? mosaicPattern(charCode) : null;
    if (pattern !== null) {
      this._renderMosaicBlock(bitmap, pattern);
      return bitmap;
    }

    // Deterministic path: read the glyph from the committed atlas.
    if (this._atlas) {
      const atlasBitmap = this._atlas.getBitmap(charCode);
      bitmap.set(atlasBitmap.subarray(0, this._glyphW * this._glyphH));
      return bitmap;
    }

    // Fallback: rasterise the font glyph (used only when no atlas is wired).
    this._renderFontGlyph(bitmap, charCode);
    return bitmap;
  }

  /**
   * Render a 2×3 mosaic block pattern into the bitmap grid.
   * Sub-cells are glyphW/2 wide and glyphH/3 tall (last row absorbs remainder).
   */
  private _renderMosaicBlock(bitmap: Uint8Array, pattern: number): void {
    const subW = this._glyphW / 2;
    const subH = this._glyphH / 3;

    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 2; c++) {
        const bitIndex = r * 2 + c;
        if (((pattern >> bitIndex) & 1) === 0) continue;

        const startCol = Math.round(c * subW);
        const endCol = Math.round((c + 1) * subW);
        const startRow = Math.round(r * subH);
        const endRow = r < 2 ? Math.round((r + 1) * subH) : this._glyphH;

        for (let row = startRow; row < endRow; row++) {
          for (let col = startCol; col < endCol; col++) {
            if (
              col >= 0 &&
              col < this._glyphW &&
              row >= 0 &&
              row < this._glyphH
            ) {
              bitmap[row * this._glyphW + col] = 1;
            }
          }
        }
      }
    }
  }

  /**
   * Rasterise a font glyph to the offscreen canvas, threshold to binary,
   * and downscale to glyphW × glyphH.
   */
  private _renderFontGlyph(bitmap: Uint8Array, charCode: number): void {
    const ctx = this._ctx;
    const cacheW = this._glyphW * this._cacheScale;
    const cacheH = this._glyphH * this._cacheScale;

    // Clear to TRANSPARENT so the alpha channel marks glyph ink only.
    ctx.clearRect(0, 0, cacheW, cacheH);
    ctx.font = `${Math.round(cacheH * this._fontScale)}px ${this._fontFamily}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(String.fromCharCode(charCode), cacheW / 2, cacheH / 2);

    const imageData = ctx.getImageData(0, 0, cacheW, cacheH);
    const pixels = imageData.data;
    const area = this._cacheScale * this._cacheScale;

    for (let row = 0; row < this._glyphH; row++) {
      for (let col = 0; col < this._glyphW; col++) {
        let sumAlpha = 0;
        for (let dy = 0; dy < this._cacheScale; dy++) {
          for (let dx = 0; dx < this._cacheScale; dx++) {
            const sx = col * this._cacheScale + dx;
            const sy = row * this._cacheScale + dy;
            sumAlpha += pixels[(sy * cacheW + sx) * 4 + 3];
          }
        }
        bitmap[row * this._glyphW + col] = sumAlpha / area > 127 ? 1 : 0;
      }
    }
  }
}

/* ─── Teletext G0 Renderer (MODE7GX3, 12×16) ────────────────────── */

export class G0Renderer extends BitmapGlyphRenderer {
  constructor(atlas?: GlyphAtlas) {
    super({
      glyphW: 12,
      glyphH: 16,
      fontFamily: '"MODE7GX3", monospace',
      // MODE7GX3's native aspect is advance:em = 780:1000 (taller than wide).
      // The 12×16 glyph grid reproduces those proportions: capitals occupy
      // ~10 columns × ~11 rows, with the baseline around row 12.
      fontScale: 1.0,
      mosaic: true,
      atlas,
    });
  }
}
