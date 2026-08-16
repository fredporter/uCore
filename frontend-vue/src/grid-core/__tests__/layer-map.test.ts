import { describe, expect, it } from "vitest";
import {
  colToLon,
  isLayerMap,
  latToRow,
  lonToCol,
  rowToLat,
  type LayerMap,
} from "../seeds/layer-map";
import moonMapSeed from "../seeds/layers/moon.json";
import regionMapSeed from "../seeds/layers/region.json";
import worldMapSeed from "../seeds/layers/world-map.json";
import { loadLayerMap } from "../seeds/load-layer-map";

describe("layer maps (Sprint C)", () => {
  it("validates the ucode-layer-map-v1 documents", () => {
    expect(isLayerMap(worldMapSeed)).toBe(true);
    expect(isLayerMap(moonMapSeed)).toBe(true);
    expect(isLayerMap(regionMapSeed)).toBe(true);
  });

  it("loads the world map into a buffer of mosaic cells", () => {
    const map = worldMapSeed as LayerMap;
    const buf = loadLayerMap(map);
    expect(buf.length).toBe(map.rows);
    expect(buf[0].length).toBe(map.cols);

    const terrain = map.layers[0];
    expect(terrain.cells.length).toBeGreaterThan(300);
    // Every terrain cell is non-empty and flagged mosaic.
    const filled = buf.flat().filter((c) => c.char !== " ");
    expect(filled.length).toBe(terrain.cells.length);
    expect(filled.every((c) => c.mosaic === true)).toBe(true);
    // Terrain colour (green=2).
    expect(filled.every((c) => c.fg === 2)).toBe(true);
  });

  it("maps gcell coordinates ↔ lat/lon (equirectangular round-trip)", () => {
    const map = worldMapSeed as LayerMap;
    // London ~ (lon -0.12, lat 51.5).
    const col = lonToCol(map, -0.12);
    const row = latToRow(map, 51.5);
    expect(col).toBeGreaterThan(0);
    expect(col).toBeLessThan(map.cols);
    expect(row).toBeGreaterThan(0);
    expect(row).toBeLessThan(map.rows);
    // Centre of that cell maps back near the input.
    expect(Math.abs(colToLon(map, col) + 0.12)).toBeLessThan(10);
    expect(Math.abs(rowToLat(map, row) - 51.5)).toBeLessThan(10);
  });

  it("Australia region map has land in the middle and sea at the edges", () => {
    const map = regionMapSeed as LayerMap;
    const buf = loadLayerMap(map);
    const mid = buf[12][20];
    expect(mid.char).not.toBe(" ");
    // Top-left corner is ocean (Indian Ocean north-west of Australia).
    expect(buf[2][2].char).toBe(" ");
  });

  it("moon map is a filled disk with an empty surround", () => {
    const map = moonMapSeed as LayerMap;
    const buf = loadLayerMap(map);
    expect(buf[12][10].char).not.toBe(" "); // disk, clear of craters
    expect(buf[0][0].char).toBe(" "); // outside disk
    expect(buf[0][20].char).toBe(" "); // outside disk
  });
});
