# Terminal Golden Images

Committed pixel baselines for the Terminal tab and glyph inspector.

| File | Content |
|------|---------|
| `terminal.png` | Terminal tab — welcome banner + shell `>` prompt (PressStart2P 8×8). |
| `glyphs-terminal.png` | Glyph inspector — all printable ASCII (32–126) in the Terminal font. |
| `glyphs-teletext.png` | Glyph inspector — all printable ASCII (32–126) in the Teletext font (MODE7GX3 12×16). |

## Regenerating

These are captured from the running frontend dev server (`/ucode`) at a fixed
viewport. The authoritative pixel source is the glyph atlas
(`src/grid-core/seeds/glyph-atlas.*.json`), verified by
`src/grid-core/__tests__/glyph-atlas.test.ts`. The PNGs above are a rendered
snapshot for visual regression.

To regenerate, capture the `<canvas>` inside the visible `<gridui-canvas>`
element for each view. An automated `@playwright/test` harness that captures
and diffs these against the committed baselines is tracked as a follow-up
(deferred until Playwright is added as a dev dependency).
