import { describe, expect, it } from "vitest";
import { createBuffer } from "../buffer";
import type { GridSeed } from "../seeds/grid-seed";
import frameSeed from "../seeds/grids/panel-frame.json";
import wordmarkSeed from "../seeds/grids/uCode-wordmark.json";
import { patternToChar, placeSeed, renderSeed } from "../seeds/render-seed";

describe("renderSeed (Sprint B)", () => {
  it("maps 6-bit patterns to the correct sextant/block codepoints", () => {
    // pattern 21 (left half "135") → U+258C ▌
    expect(patternToChar(21).codePointAt(0)).toBe(0x258c);
    // pattern 63 (full block) → U+2588 █
    expect(patternToChar(63).codePointAt(0)).toBe(0x2588);
    // pattern 3 (top row "12") → SEXTANT-12 U+1FB02
    expect(patternToChar(3).codePointAt(0)).toBe(0x1fb02);
    // empty → space
    expect(patternToChar(0)).toBe(" ");
  });

  it("renders the uCode wordmark seed as connected mosaic cells", () => {
    const seed = wordmarkSeed as GridSeed;
    const buf = renderSeed(seed);
    expect(buf.length).toBe(seed.rows);
    expect(buf[0].length).toBe(seed.cols);

    // Count filled cells = 15 (the "UC" mark).
    const filled = buf.flat().filter((c) => c.char !== " ");
    expect(filled.length).toBe(15);
    // Every filled cell is flagged mosaic.
    expect(filled.every((c) => c.mosaic === true)).toBe(true);
    // Colours come from the seed.
    expect(filled.every((c) => c.fg === seed.fg && c.bg === seed.bg)).toBe(
      true,
    );
  });

  it("renders the panel frame seed with full-width top/bottom edges", () => {
    const seed = frameSeed as GridSeed;
    const buf = renderSeed(seed);
    const top = buf[0];
    const bottom = buf[seed.rows - 1];
    // Top and bottom rows are entirely filled (frame edges).
    expect(top.every((c) => c.char !== " ")).toBe(true);
    expect(bottom.every((c) => c.char !== " ")).toBe(true);
    // Interior row has only the left/right columns filled.
    expect(buf[1][0].char).not.toBe(" ");
    expect(buf[1][seed.cols - 1].char).not.toBe(" ");
    expect(buf[1][1].char).toBe(" ");
  });

  it("places a seed centred onto a larger buffer", () => {
    const seed = frameSeed as GridSeed;
    const target = createBuffer(20, 10);
    placeSeed(target, seed, 6, 3);
    // Top-left cell of the frame lands at (6,3).
    expect(target[3][6].char).not.toBe(" ");
    expect(target[3][6].mosaic).toBe(true);
    // Outside the placed area is still empty.
    expect(target[0][0].char).toBe(" ");
  });
});
