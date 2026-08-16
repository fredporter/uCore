/**
 * Glyph Atlas — pre-baked, deterministic glyph bitmaps.
 *
 * The atlas is the single source of truth for the codepoint → glyph-bitmap
 * mapping. It is generated once from the source fonts and committed as seed
 * data (`seeds/gridcore/glyph-atlas.*.json`); at runtime the renderer reads
 * bitmaps from the atlas and never rasterises fonts.
 *
 * Format: ucode-glyph-atlas-v1
 * {
 *   family, glyphW, glyphH, cellW, cellH, scale, offsetX, offsetY,
 *   glyphs: { "U+0041": ["0C","7E", ...] }  // hex rows, glyphW bits per row
 * }
 */

/** Serialised atlas shape (as imported from the seed JSON). */
export interface GlyphAtlasData {
  format: string;
  family: string;
  glyphW: number;
  glyphH: number;
  cellW: number;
  cellH: number;
  scale: number;
  offsetX: number;
  offsetY: number;
  glyphs: Record<string, string[]>;
}

export class GlyphAtlas {
  readonly family: string;
  readonly glyphW: number;
  readonly glyphH: number;
  readonly cellW: number;
  readonly cellH: number;
  readonly scale: number;
  readonly offsetX: number;
  readonly offsetY: number;

  private _cache = new Map<number, Uint8Array>();

  constructor(private readonly data: GlyphAtlasData) {
    this.family = data.family;
    this.glyphW = data.glyphW;
    this.glyphH = data.glyphH;
    this.cellW = data.cellW;
    this.cellH = data.cellH;
    this.scale = data.scale;
    this.offsetX = data.offsetX;
    this.offsetY = data.offsetY;
  }

  /** Get a glyph bitmap (glyphW × glyphH of 0/1) for a character code. */
  getBitmap(charCode: number): Uint8Array {
    const cached = this._cache.get(charCode);
    if (cached) return cached;

    const key = `U+${charCode.toString(16).toUpperCase().padStart(4, "0")}`;
    const rows = this.data.glyphs[key];
    const bitmap = new Uint8Array(this.glyphW * this.glyphH);

    if (rows) {
      const hexLen = Math.ceil(this.glyphW / 4);
      for (let r = 0; r < this.glyphH; r++) {
        const rowHex = (rows[r] || "").padStart(hexLen, "0");
        let value = parseInt(rowHex, 16);
        for (let c = this.glyphW - 1; c >= 0; c--) {
          bitmap[r * this.glyphW + c] = value & 1;
          value >>= 1;
        }
      }
    }

    this._cache.set(charCode, bitmap);
    return bitmap;
  }

  /** Number of glyphs present in the atlas. */
  get size(): number {
    return Object.keys(this.data.glyphs).length;
  }
}
