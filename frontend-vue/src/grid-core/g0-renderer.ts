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
 * Teletext (MODE7GX3) glyphs are 12×10. Terminal (Press Start 2P) glyphs
 * are 8×8. Mosaic blocks (2×3) are generated algorithmically for G0 codes
 * 0x60–0x7F and common Unicode block glyphs.
 *
 * @see docs/GRIDUI_RENDERING_CONTRACT.md
 */

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
}

/* ─── Mosaic mapping ───────────────────────────────────────────── */

/** 6-bit pattern for a character code (Unicode block glyphs only). */
function mosaicPattern(charCode: number): number | null {
  // Unicode block glyphs → equivalent 2×3 mosaic pattern.
  // NOTE: the teletext G0 0x60–0x7F codes are NOT intercepted here — the
  // buffer carries Unicode chars, and 0x60–0x7F is ASCII (a–z, `, {…}),
  // which must render as font glyphs, not mosaic blocks.
  switch (charCode) {
    case 0x2588: // █ full block
      return 0x3f;
    case 0x2580: // ▀ upper half
      return 0x03;
    case 0x2584: // ▄ lower half
      return 0x30;
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

/* ─── Teletext G0 Renderer (MODE7GX3, 12×10) ───────────────────── */

export class G0Renderer extends BitmapGlyphRenderer {
  constructor() {
    super({
      glyphW: 12,
      glyphH: 10,
      fontFamily: '"MODE7GX3", monospace',
      // MODE7GX3 glyphs sit on a wider em than their 12px G0 advance;
      // 1.6× em fills the 12×10 grid edge-to-edge.
      fontScale: 1.6,
      mosaic: true,
    });
  }
}
