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
  for (const layer of map.layers) if (layer.visible !== false) applyLayer(buf, layer);
  return buf;
}

/** Materialise each sparse source layer as its own editable buffer. */
export function loadLayerMapBuffers(map: LayerMap): Map<string, GridBuffer> {
  const buffers = new Map<string, GridBuffer>();
  for (const layer of map.layers) {
    const buffer = createBuffer(map.cols, map.rows);
    applyLayer(buffer, layer);
    buffers.set(layer.id, buffer);
  }
  return buffers;
}

function applyLayer(buf: GridBuffer, layer: LayerMap["layers"][number]): void {
    for (const cell of layer.cells) {
      if (cell.col < 0 || cell.col >= (buf[0]?.length ?? 0)) continue;
      if (cell.row < 0 || cell.row >= buf.length) continue;
      const pattern = cell.pattern ?? 0;
      const fg = cell.fg ?? layer.colour;
      const bg = cell.bg ?? 0;
      const gc: GridCell =
        cell.char
          ? { char: cell.char, fg, bg }
          : pattern === 0
          ? { char: " ", fg, bg }
          : { char: patternToChar(pattern), fg, bg, mosaic: true };
      buf[cell.row][cell.col] = gc;
    }
}
