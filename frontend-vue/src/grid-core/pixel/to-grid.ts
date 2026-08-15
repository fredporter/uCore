import type { GridBuffer } from "../types";
import {
  createPixelBuffer,
  getPixel,
  PIXEL_SIZE,
  setPixel,
  type PixelBuffer,
} from "./pixel-buffer";

/**
 * Convert a pixel buffer into a GridBuffer for preview: each pixel becomes
 * one solid-colour cell (fg = bg = colour), renderable by <gridui-canvas>.
 */
export function pixelBufferToGridBuffer(
  buffer: PixelBuffer,
  size = PIXEL_SIZE,
): GridBuffer {
  const grid: GridBuffer = [];
  for (let y = 0; y < size; y++) {
    const row: GridBuffer[number] = [];
    for (let x = 0; x < size; x++) {
      const color = getPixel(buffer, x, y);
      row.push({ char: " ", fg: color, bg: color });
    }
    grid.push(row);
  }
  return grid;
}

/**
 * Inverse of {@link pixelBufferToGridBuffer}: read each solid-colour cell's
 * foreground index back into a PixelBuffer. Used by grid import on the Pixel tab.
 */
export function gridBufferToPixelBuffer(
  buf: GridBuffer,
  size = PIXEL_SIZE,
): PixelBuffer {
  const pixels = createPixelBuffer(0);
  for (let y = 0; y < Math.min(size, buf.length); y++) {
    const row = buf[y];
    if (!row) continue;
    for (let x = 0; x < Math.min(size, row.length); x++) {
      const fg = row[x]?.fg ?? 0;
      setPixel(pixels, x, y, Math.max(0, Math.min(7, fg)));
    }
  }
  return pixels;
}
