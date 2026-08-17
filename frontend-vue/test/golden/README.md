# Terminal Golden Images

Committed pixel baselines for the Glyph Inspector (`/ucode` → Glyphs tab),
captured and diffed automatically by `@playwright/test`.

| File                  | Content                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------- |
| `glyphs-terminal.png` | Glyph inspector — all printable ASCII (32–126) in the Terminal font (PressStart2P 8×8). |
| `glyphs-bedstead.png` | Glyph inspector — all printable ASCII (32–126) in the Bedstead font (SAA5050 12×20).    |
| `terminal.png`        | (legacy) Terminal tab screenshot — kept for reference, not asserted by the harness.     |

## Running the harness

```sh
pnpm test:golden                      # run diffs against committed baselines
pnpm test:golden --update-snapshots   # regenerate baselines
pnpm exec playwright install chromium # one-time browser install
```

The harness (`e2e/golden.spec.ts`) navigates to `/ucode`, opens the Glyphs tab,
and screenshots the visible `<gridui-canvas>` `<canvas>` element. Baselines are
captured at a fixed viewport (1280×800, deviceScaleFactor 1) and are
deterministic because the viewport fits the glyph grid at a uniform integer
device-pixel scale.

The authoritative pixel source is the glyph atlas
(`src/grid-core/seeds/glyph-atlas.*.json`), verified by
`src/grid-core/__tests__/glyph-atlas.test.ts`. The PNGs above are the rendered
snapshot used for visual regression.
