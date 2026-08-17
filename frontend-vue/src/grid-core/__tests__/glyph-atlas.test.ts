import { describe, expect, it } from "vitest";
import { GlyphAtlas } from "../glyph-atlas";
import bedsteadAtlasJson from "../seeds/glyph-atlas.bedstead.json";
import terminalAtlasJson from "../seeds/glyph-atlas.terminal.json";

describe("GlyphAtlas (Sprint A)", () => {
  it("loads the terminal atlas (PressStart2P 8x8) with 95 glyphs", () => {
    const atlas = new GlyphAtlas(terminalAtlasJson);
    expect(atlas.glyphW).toBe(8);
    expect(atlas.glyphH).toBe(8);
    expect(atlas.cellW).toBe(24);
    expect(atlas.scale).toBe(3);
    expect(atlas.size).toBe(95);

    const A = atlas.getBitmap("A".charCodeAt(0));
    expect(A.length).toBe(64);
    // PressStart2P 'A' apex at row 0, columns 2-4.
    expect(A[0 * 8 + 2]).toBe(1);
    expect(A[0 * 8 + 4]).toBe(1);
    // Descender row (row 7) is blank.
    expect(A.slice(7 * 8).reduce((a, b) => a + b, 0)).toBe(0);
  });

  it("loads the Bedstead atlas (SAA5050 12x20) with ASCII + graphics", () => {
    const atlas = new GlyphAtlas(bedsteadAtlasJson);
    expect(atlas.glyphW).toBe(12);
    expect(atlas.glyphH).toBe(20);
    expect(atlas.cellW).toBe(24);
    expect(atlas.cellH).toBe(40);
    expect(atlas.scale).toBe(2);
    // ASCII + box-drawing + blocks + 2×3 sextants.
    expect(atlas.size).toBeGreaterThanOrEqual(298);

    const A = atlas.getBitmap("A".charCodeAt(0));
    expect(A.length).toBe(240);
    expect(A.reduce((a, b) => a + b, 0)).toBeGreaterThan(0);

    // Box-drawing and sextant glyphs are baked (authentic SAA5050 shapes).
    expect(atlas.has("─".charCodeAt(0))).toBe(true);
    expect(atlas.has("█".charCodeAt(0))).toBe(true);
    expect(atlas.has(0x1fb00)).toBe(true);
  });

  it("maps space to an all-zero bitmap", () => {
    const atlas = new GlyphAtlas(terminalAtlasJson);
    const sp = atlas.getBitmap(" ".charCodeAt(0));
    expect(sp.reduce((a, b) => a + b, 0)).toBe(0);
  });
});
