# GridCore Character Catalogue Golden Images

Committed pixel baselines for the character catalogue (`/ucode` → Glyphs tab),
captured and diffed automatically by `@playwright/test`.

| File                  | Content                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------- |
| `glyphs-terminal.png` | First catalogue page in the square Terminal register (PressStart2P 8×8).                |
| `glyphs-bedstead.png` | First catalogue page in the rectangular reading register (Bedstead/SAA5050 12×20).     |
| `terminal.png`        | (legacy) Terminal tab screenshot — kept for reference, not asserted by the harness.     |
| `teletext-data.png`   | Deterministic 40×25 Teletext data/dashboard composition.                               |
| `teletext-map.png`    | Deterministic 40×25 mosaic map composition.                                             |
| `teletext-graphics.png` | Deterministic 40×25 mosaic graphics showcase.                                         |

## Running the harness

```sh
pnpm test:golden                      # run diffs against committed baselines
pnpm test:golden --update-snapshots   # regenerate baselines
pnpm exec playwright install chromium # one-time browser install
```

The harness (`e2e/golden.spec.ts`) navigates to `/ucode`, opens the Glyphs tab,
and screenshots the visible `<gridui-canvas>` `<canvas>` element. Baselines are
captured at a fixed viewport (1280×800, deviceScaleFactor 1) and are
deterministic because the 16×12 catalogue page fits the glyph grid at a
uniform integer device-pixel scale.

Teletext goldens freeze the reader clock and use static editorial pages so
vault changes cannot create unrelated image diffs. A separate narrow-viewport
interaction test verifies that the touch keypad resolves a three-digit page
and dismisses itself.

The authoritative pixel source is the glyph atlas
(`src/grid-core/seeds/glyph-atlas.*.json`), verified by
`src/grid-core/__tests__/glyph-atlas.test.ts`. The PNGs above are the rendered
snapshot used for visual regression.
