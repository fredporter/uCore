/**
 * Seed Renderer — render a connected-cell seed into a GridBuffer.
 *
 * Each 6-bit pattern maps to a Unicode sextant block character (or the
 * full/left/right half block elements) that the bitmap glyph renderers
 * interpret as a 2×3 mosaic. The pattern table is the single source of
 * truth: seeds/gridcore/sextant-patterns.json.
 *
 * @see seeds/gridcore/grids/*.json
 */

import { createBuffer } from "../buffer";
import type { GridBuffer, GridCell } from "../types";
import type { GridSeed } from "./grid-seed";
import sextantPatternsJson from "./sextant-patterns.json";

/** Build the 6-bit pattern → Unicode codepoint map from the pattern table. */
function buildPatternMap(): Map<number, number> {
  const map = new Map<number, number>();
  const patterns = (
    sextantPatternsJson as { patterns: Record<string, { unicode: string }> }
  ).patterns;
  for (const [key, value] of Object.entries(patterns)) {
    const pattern = parseInt(key, 10);
    const code = parseInt(value.unicode.slice(2), 16);
    map.set(pattern, code);
  }
  return map;
}

const PATTERN_TO_CODE = buildPatternMap();

/** Convert a 6-bit pattern to its display character (space for empty). */
export function patternToChar(pattern: number): string {
  if (pattern <= 0) return " ";
  const code = PATTERN_TO_CODE.get(pattern);
  return code !== undefined ? String.fromCodePoint(code) : " ";
}

/**
 * Render a seed into a GridBuffer. Empty cells (pattern 0) become spaces;
 * filled cells become sextant/block mosaic cells in the seed's colours.
 */
export function renderSeed(seed: GridSeed): GridBuffer {
  const { cols, rows } = seed;
  const fg = seed.fg ?? 7;
  const bg = seed.bg ?? 0;
  const buf = createBuffer(cols, rows);

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const pattern = seed.cells[r * cols + c] ?? 0;
      const cell: GridCell =
        pattern === 0
          ? { char: " ", fg, bg }
          : { char: patternToChar(pattern), fg, bg, mosaic: true };
      buf[r][c] = cell;
    }
  }
  return buf;
}

/** Centre a seed's buffer onto a larger target buffer at the given offset. */
export function placeSeed(
  target: GridBuffer,
  seed: GridSeed,
  originCol: number,
  originRow: number,
): GridBuffer {
  const src = renderSeed(seed);
  for (let r = 0; r < seed.rows; r++) {
    for (let c = 0; c < seed.cols; c++) {
      const tr = originRow + r;
      const tc = originCol + c;
      if (tr >= 0 && tr < target.length && tc >= 0 && tc < target[0].length) {
        target[tr][tc] = src[r][c];
      }
    }
  }
  return target;
}
