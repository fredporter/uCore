# GridCore canonical migration — uCore surface → uCode packages

Status: not-started
Priority: P1
Area: uCode / GridCore / viewport-renderer
Created: 2026-08-14

## Goal

uCode's `@udos/gridcore` + `@udos/viewport-renderer` are canonical. Remove
uCore's remaining local grid implementation (`frontend-vue/src/grid-core/`) and
rewire `UCodeSurface.vue` onto the uCode packages via the existing Vite aliases
(`@udos/gridcore`, `@udos/viewport-renderer`).

## Current state (2026-08-14)

- uCore's dead duplicates already removed: `frontend-vue/src/vendor/gridui-canvas/`
  and the unused viewer components (`GridCoreUI.vue`, `MultiColumnViewer.vue`,
  `ProseViewer.vue`, `SlideViewer.vue`).
- Live uCore grid code (still used by `UCodeSurface.vue`):
  - `frontend-vue/src/grid-core/{buffer,types,algebra,palette,g0-renderer,gridui-canvas,index}.ts`
- Canonical uCode packages:
  - `~/Code/uCode/packages/gridcore/src/` — geometry, buffer, layers, teletext,
    terminal, viewport, spatial, editor, fonts, bridge
  - `~/Code/uCode/packages/viewport-renderer/src/` — CanvasViewport, DOMViewport,
    ViewportWidget, TeletextWidget, TerminalWidget, fonts, palette/usx

## API mismatch (the reason this is a migration, not an import swap)

| uCore `grid-core` | uCode `@udos/gridcore` |
|---|---|
| `GridCell` = `{char, fg, bg, ...}` (uCore shape) | `BufferCell` = `{char, fg, bg, bold, flash, doubleHeight, doubleWidth}` |
| `createBuffer`, `writeString`, `fill`, `scroll`, `clear`, `cloneBuffer`, `bufferToString`, `stringToBuffer` | `createBuffer`, `createBufferCell`, `cloneBuffer`, `getBufferDimensions`, `sameDimensions` (no writeString/fill/scroll/clear) |
| `PALETTE_DARK`, `PALETTE_LIGHT`, `getColour`, `colourCSS` | `@udos/viewport-renderer` `palette/usx` |
| `GRID_PRESETS`, `getGridPreset`, `resolveColumns`, `calcViewport`, column algebra | `viewport/calculator` |
| `G0Renderer`, `<gridui-canvas>` Web Component | `viewport-renderer` canvas/dom/widgets |

## Migration steps

1. **uCode side (canonical home):** add the missing string/grid primitives to
   `@udos/gridcore` — `writeString`, `fill`, `scroll`, `clear`, `bufferToString`,
   `stringToBuffer`, and a viewport/preset helper (`resolveColumns`, `calcViewport`)
   — operating on the canonical `BufferCell` shape. Rebuild the package (tsup).
2. **Renderer:** confirm `@udos/viewport-renderer` provides a drop-in for the
   `<gridui-canvas>` Web Component (or port the element into viewport-renderer),
   then replace `grid-core/gridui-canvas.ts` usage in `UCodeSurface.vue`.
3. **uCore side:** rewire `UCodeSurface.vue` imports from
   `../../grid-core/*` → `@udos/gridcore` + `@udos/viewport-renderer`.
4. Delete `frontend-vue/src/grid-core/` and `frontend-vue/src/styles/gridcore.css`
   only after the surface renders identically (browser-verify grid + terminal tabs).
5. Remove the now-unused `@uCode3` Vite alias (points at a repo that may not exist).

## Acceptance criteria

- `UCodeSurface.vue` imports only `@udos/*` — no local `grid-core/` imports.
- uCore's `frontend-vue/src/grid-core/` directory is deleted.
- GridCore canvas, column/prose/slide modes, and the terminal tab render as before.
- Frontend type-check + production build pass; vitest grid tests green.
