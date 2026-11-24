# Prose and GridCore Content Contract — Baseline

Status: Active baseline
Created: 2026-11-23
Checker: `scripts/check_content_contract.py` (`ucdev` → `check-content`)

The ecosystem has two style contracts:

| Domain | Standard | Namespace | Stylesheet |
| --- | --- | --- | --- |
| Prose | `PROSE-STANDARDS.md` | `--usx-*` | `usx-prose.css` |
| GridCore | `GRIDCORE-LATTICE-SPEC.md` + `.json` | `--gridcore-*` | `gridcore.css` |

Surfaces, themes, palettes and display profiles are consumers of those two contracts.
This file records the first measured state so later phases shrink it rather than
re-litigate it.

## How to read the checker

```sh
python3 scripts/check_content_contract.py            # summary, first 40 findings per severity
python3 scripts/check_content_contract.py --json     # full finding list
python3 scripts/check_content_contract.py --root ../HomeNook/apps/console/src
```

Exit codes: `0` clean, `1` violations, `2` unusable input. Definitions are always
read from `packages/usx-tokens` and `frontend-vue/src/styles/gridcore.css`, so a
second app can be checked without passing its own token sources.

Rules in this phase: `prose.reference`, `prose.literals`, `gridcore.palette`,
`contract.contrast`. Namespace grammar, prose measure, lattice px integrity and
spec-to-code sync are deferred to Phases B–D.

## Measured state

### uCore (default scan)

| Rule | Errors | Warnings |
| --- | --- | --- |
| `prose.reference` | 0 | 0 |
| `prose.literals` | 0 | 0 |
| `prose.namespace` | 0 | 0 |
| `gridcore.palette` | 0 | 0 |
| `contract.contrast` | 0 | 17 |

Phase A baseline was 22 references / 1019 literals / 1 palette / 5 contrast errors.
Every rule is clean; the 17 warnings are the two retro palettes, which
`USX-STYLE-SPEC.md` scopes to the GridCore viewport.

### HomeNook console (`--root ../HomeNook/apps/console/src`)

| Rule | Errors | Warnings |
| --- | --- | --- |
| `prose.reference` | 0 | 0 |
| `prose.literals` | 0 | 0 |
| `prose.namespace` | 0 | 0 |
| `gridcore.palette` | 0 | 0 |
| `contract.contrast` | 0 | 17 |

HomeNook is now a pure consumer of the canonical package: no vendored tokens, no
rogue namespaces, no literals, and it carries the ten-foot display profile.

## Completed in Phase D

| Change | Effect |
| --- | --- |
| De-vendored `HomeNook/packages/usx-tokens` | One token source; console reaches uCore through the `@udos/usx-tokens` alias |
| Deleted `homenest-theme.css` | 1001 lines, 0 `var(--usx-*)`, 34 literals, and the `--gh-*`/`--hn-*`/`--bs-*` palettes |
| Deleted `apps/console/src/views/*.tsx`, `App.tsx`, `main.tsx` | Unreferenced React remnants reading `--gh-*` |
| `prose.namespace` rule | A local prefix may not be read outside the files that define it; 48 findings triaged to 0 |
| `GRIDCORE_VARIABLEIZATION_SPEC.md` §4.8–4.9, §5.5–5.7 | Lattice geometry, bridge groups, one-way reference, palette canon, integer zoom |
| Launcher tiles | Four hexes plus the `color + '44'` alpha hack replaced with role tokens |
| Teletext screen | Colours from `--gridcore-palette-*` instead of black/white literals |


## Completed in Phase B

| Change | Effect |
| --- | --- |
| `usx-prose.css` rewritten on tokens only | Prose literals 40 → 0; Material-3 names removed |
| `usx-prose.css` added to `files` and `exports` | The file is installable; five in-component `@import`s were scoped and dead |
| One global import in `main.ts` | Prose renders from a single contract, after `usx-standard.css` |
| `--usx-font-family-reading`, `--usx-line-height-code` | Reading stack and code rhythm are now tokens |
| PROSE-STANDARDS.md §1–2 | Bundled stack: Inter / Merriweather / JetBrains Mono |
| `--usx-btn-padding`, `.usx-btn` base, `--secondary`/`--danger` | Buttons had zero padding and no base class |
| `--usx-z-index-*` scale | Seven overlay levels replace four ad-hoc names |
| `--usx-color-scrim` / `--usx-color-on-scrim` | Video letterbox is theme-independent |
| 20 orphan references renamed or defined | `prose.reference` 22 errors → 0 |
| `--gridcore-color-danger` bridge, palette 7 = `#FFFFFF` | `gridcore.palette` 1 → 0 |

## Findings of record

### Theme contrast — resolved via Bootstrap 6

`tokens-color.css` now carries the Bootstrap 6 palette and role mapping, so the
five failures below are fixed rather than patched:

| Theme | Pair | Before | After |
| --- | --- | --- | --- |
| light | warning text on canvas | 1.63:1 | 5.19:1 (amber-700) |
| light | info text on canvas | 1.96:1 | 6.03:1 (cyan-700) |
| dark | success text on canvas | 4.13:1 | 8.03:1 (green-400) |
| dark | danger text on canvas | 4.14:1 | 5.97:1 (red-400) |
| dark | label on primary | 3.00:1 | 6.47:1 (blue-900 on blue-400) |

Every role is now checked in both directions — foreground on canvas, foreground on
its surface, and the contrast partner on the fill. Light, dark and high-contrast
pass at `4.5:1`; `c64` and `teletext` remain warnings because retro palettes belong
inside the GridCore viewport.

### GridCore owns its standards

The lattice palette and geometry moved into `GRIDCORE-STANDARDS.json` (`palette`,
`geometry`). The checker reads that file as canon, verifies `--gridcore-palette-0..7`
against it, and reports drift between it and the display copy in `USX-STANDARDS.json`.
Lattice scaling is integer-only via `[data-lattice]` and `--gridcore-zoom`.

### HomeNook is the ten-foot surface

`home-nest/display-profiles.css` implements `DEVICE-DISPLAY-STANDARDS.md` §C:
`[data-display="ten-foot"]` sets an 18px root at 1080p scaling to 36px at 2160p,
64px controller targets, a 50ch reading measure, and a letterboxed `.hn-stage`.
HomeNook's document root carries `data-display="ten-foot"` and imports the profile
after the console grid. Lattices inside the profile keep `font-size: 1rem` and
integer zoom, so the dot lattice is never scaled fractionally.


### Raw colour, largest sources

| Findings | File |
| --- | --- |
| 197 | `frontend-vue/src/surfaces/documentation/LocalWikiReader.vue` |
| 147 | `frontend-vue/src/surfaces/workflow/panels/NotebookBinderPanel.vue` |
| 82 | `frontend-vue/src/surfaces/snackbar/panels/SnackbarDashboardPanel.vue` |
| 61 | `frontend-vue/src/surfaces/dispatch/DispatchStoryView.vue` |
| 60 | `frontend-vue/src/surfaces/snackbar/panels/SnackbarServicesPanel.vue` |
| 56 | `frontend-vue/src/surfaces/recipes/RecipeGallerySurface.vue` |
| 48 | `frontend-vue/src/surfaces/google/GoogleStudioSurface.vue` |
| 39 | `frontend-vue/src/utils/svgChartRenderer.ts` |
| 33 | `frontend-vue/src/surfaces/snackbar/panels/SnackbarBudgetPanel.vue` |
| 30 | `frontend-vue/src/styles/gridcore.css` |

The Prose contract itself (`usx-prose.css`) and every `[data-lattice]` renderer are
now clean; the remaining load is surface chrome and chart utilities.

## Shrink targets

| Phase | Target | Gate | State |
| --- | --- | --- | --- |
| B | Prose contract on tokens, published, duplicates removed | `prose.reference` = 0, Prose literals = 0 | **done** |
| C | `gridcore.css` bridge without GitHub fallbacks; lattice geometry tokens | `gridcore.palette` = 0 | **done** (bridge fallbacks next) |
| D | `GRIDCORE_VARIABLEIZATION_SPEC.md` §4 sync; rogue namespaces removed | `contract.sync`, namespace = 0 | **done** |
| E | Bootstrap 6 palette, role tokens, contrast-corrected statuses | `contract.contrast` errors = 0 | **done** |
| F | Ten-foot profile for HomeNook with integer-only lattice zoom | visual pass 720p–2160p | profile wired, visual pass pending |
| G | Surface literal migration | `prose.literals` = 0 | **done** |

## Completed in Phase G

Three palettes were hardcoded across the app; each was mapped to contract tokens:

| Source palette | Example | Reached |
| --- | --- | --- |
| GitHub Dark | `#0d1117`, `#30363d`, `#58a6ff` | background, border, primary |
| Material-ish | `#a8c7fa`, `#e2e2e6` | snackbar panels |
| Tailwind slate | `#0f172a`, `#94a3b8`, `#ef4444` | binder, dispatch |

Alpha colours became `color-mix(in srgb, <token> <n>%, transparent)`, so overlays and
shadows follow the theme instead of assuming black.

Seven paths are exempt, each for a stated reason: `tokens/`, `themes/`, `palettes/`,
`recipes/`, `styles/themes/` (canon), `flowbite-skin.css` (a skin *is* a palette),
`surfaces/recipes/` and `surfaces/google/` and `BananaStudio.vue` (preview or vendor
brand content), the chart renderers (series colours are data), `grid-core/` and
`gridcore.css` (renderer behaviour and the GridCore contract itself). Test fixtures
are excluded from the scan because they assert on colours rather than render them.

`gridcore.css` lost its `var(--usx-*, #hex)` fallbacks: the tokens always exist, and
the fallbacks were quietly reintroducing the GitHub palette.

### Post-migration audit

A property/token audit ran over the migrated CSS looking for inverted semantics
(surface colour used as text, text colour painted as a background, shadow colours).
85 pairings were reviewed; the surviving patterns are all deliberate — 1px dividers
painted with `--usx-color-border`, status dots, knockout labels on coloured fills,
focus rings, and `color-mix` hover tints. Two were sharpened: the dispatch active
button now uses `on-primary` rather than the canvas colour, and the filepicker move
button hovers on `surface-hover` rather than the border colour.

`vitest`: 185 tests across 53 files, all passing. One test needed updating because an
in-flight refactor in `AuthoringRecipeView.vue` (present in the working tree before
this work) replaced the mode buttons' text labels with `UIcon` plus `aria-label`; the
test now queries the accessible label instead of the button text.

Progress is tracked by re-running `check-content`; percentage improvements are not
recorded here so the numbers stay the single source.
