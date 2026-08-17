/**
 * Layer Map Loader — compose a layer map into a frontend GridBuffer.
 *
 * Layers are composed bottom-up (earlier layers first, later layers paint over
 * them). Each cell becomes a mosaic cell (mosaic = sextant char) with the
 * layer's colour (or the cell's fg/bg override).
 *
 * @see layer-map.ts
 */

import type { GridBuffer, GridCell } from "@udos/gridcore/buffer/cell";
import { createBuffer } from "../buffer";
import type { LayerMap } from "./layer-map";
import { patternToChar } from "./render-seed";

/** Compose all layers of a map into a GridBuffer. */
export function loadLayerMap(map: LayerMap): GridBuffer {
  const buf = createBuffer(map.cols, map.rows);
  for (const layer of map.layers) {
    for (const cell of layer.cells) {
      if (cell.col < 0 || cell.col >= map.cols) continue;
      if (cell.row < 0 || cell.row >= map.rows) continue;
      const pattern = cell.pattern;
      const fg = cell.fg ?? layer.colour;
      const bg = cell.bg ?? 0;
      const gc: GridCell =
        pattern === 0
          ? { char: " ", fg, bg }
          : { char: patternToChar(pattern), fg, bg, mosaic: true };
      buf[cell.row][cell.col] = gc;
    }
  }
  return buf;
}
