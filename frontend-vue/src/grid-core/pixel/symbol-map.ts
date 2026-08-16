import {
  createPixelBuffer,
  PIXEL_SIZE,
  setPixel,
  type PixelBuffer,
} from "./pixel-buffer";

/**
 * A symbol map: Unicode codepoint → 24×24 colour-index bitmap.
 * This is the "font / symbol character map" that ties a glyph (symbol) to its
 * editable 24×24 pixel definition.
 */
export type SymbolMap = Map<number, PixelBuffer>;

export function createSymbolMap(): SymbolMap {
  return new Map();
}

/**
 * Scale a native glyph bitmap (gw×gh of 0/1 bits) up to the 24×24 pixel grid.
 * The glyph is scaled by the largest integer factor that fits and then
 * centred — consistent alignment for every loaded font glyph.
 */
export function glyphBitmapToPixelBuffer(
  bitmap: Uint8Array,
  gw: number,
  gh: number,
  colour = 7,
): PixelBuffer {
  const out = createPixelBuffer(0);
  const scale = Math.max(
    1,
    Math.min(Math.floor(PIXEL_SIZE / gw), Math.floor(PIXEL_SIZE / gh)),
  );
  const ox = Math.floor((PIXEL_SIZE - gw * scale) / 2);
  const oy = Math.floor((PIXEL_SIZE - gh * scale) / 2);

  for (let y = 0; y < gh; y++) {
    for (let x = 0; x < gw; x++) {
      if (bitmap[y * gw + x] === 1) {
        for (let dy = 0; dy < scale; dy++) {
          for (let dx = 0; dx < scale; dx++) {
            setPixel(out, ox + x * scale + dx, oy + y * scale + dy, colour);
          }
        }
      }
    }
  }
  return out;
}

/** Serialise a symbol map to a plain object for export. */
export function serializeSymbolMap(map: SymbolMap): {
  format: string;
  glyphs: Record<string, number[]>;
} {
  const glyphs: Record<string, number[]> = {};
  for (const [code, buf] of map) {
    const key = `U+${code.toString(16).toUpperCase().padStart(4, "0")}`;
    glyphs[key] = Array.from(buf);
  }
  return { format: "ucode-symbol-map-v1", glyphs };
}

/** Deserialise a plain object into a symbol map. */
export function deserializeSymbolMap(data: unknown): SymbolMap {
  const map = createSymbolMap();
  if (!data || typeof data !== "object") return map;
  const obj = data as { format?: string; glyphs?: Record<string, unknown> };
  if (obj.format !== "ucode-symbol-map-v1" || !obj.glyphs) return map;

  for (const [key, value] of Object.entries(obj.glyphs)) {
    const code = parseInt(key.replace(/^U\+/, ""), 16);
    if (Number.isNaN(code) || !Array.isArray(value)) continue;
    const buf = createPixelBuffer(0);
    for (let i = 0; i < Math.min(value.length, buf.length); i++) {
      const n = Number(value[i]);
      buf[i] = Number.isFinite(n) ? Math.max(0, Math.min(7, n)) : 0;
    }
    map.set(code, buf);
  }
  return map;
}
