# USX Token Alignment — uCore ↔ HomeNest (July 2026)

**Status:** Active
**Last updated:** 2026-07-08

## Summary

The USX token system has been extracted from `uCore/frontend-vue/src/styles/` into a **shared npm package**: `@udos/usx-tokens` v3.1.0.

This package is now hosted in the **uCore monorepo** (`uDosGo/uCore`, path `packages/usx-tokens/`) and is consumed by both uCore and HomeNest.

## What Changed

| Before                                           | After                                                                   |
| ------------------------------------------------ | ----------------------------------------------------------------------- |
| Tokens live in `frontend-vue/src/styles/tokens/` | Tokens live in `packages/usx-tokens/tokens/` in uCore                   |
| `usx-standard.css` in uCore only                 | `usx-standard.css` shared via npm package                               |
| No 10-foot console support                       | `home-nest/` additions for console grid, controller focus, media player |
| Ad-hoc PicoCSS mapping                           | Formal PicoCSS → USX mapping layer in `tokens-color.css`                |

## Path Mapping

| uCore current path                        | `@udos/usx-tokens` import path       |
| ----------------------------------------- | ------------------------------------ |
| `src/styles/tokens/tokens-color.css`      | `@udos/usx-tokens/tokens/color`      |
| `src/styles/tokens/tokens-components.css` | `@udos/usx-tokens/tokens/components` |
| `src/styles/tokens/tokens-spacing.css`    | `@udos/usx-tokens/tokens/spacing`    |
| `src/styles/tokens/tokens-touch.css`      | `@udos/usx-tokens/tokens/touch`      |
| `src/styles/tokens/tokens-typography.css` | `@udos/usx-tokens/tokens/typography` |
| `src/styles/usx-standard.css`             | `@udos/usx-tokens` (default export)  |
| `src/styles/themes/dark.css`              | `@udos/usx-tokens/themes/dark`       |
| `src/styles/themes/*.css`                 | `@udos/usx-tokens/themes/*`          |

**Last updated:** 2026-07-08 (Sprint 3 complete)

## ✅ Completed (2026-07-08)

1. ✅ Installed `@udos/usx-tokens` as `file:` dependency in uCore
2. ✅ Replaced direct imports with package imports in `main.ts`
3. ✅ Removed local copies: `styles/tokens/*.css`, `styles/themes/base.css`, `styles/usx-standard.css`
4. ✅ Created `styles/usx-extensions.css` for uCore-only patterns
5. ✅ Synced c64, teletext, high-contrast themes into the shared package (v3.1.0)
6. ✅ Published PUBLISH.md with publishing instructions

## Remaining

- [ ] `npm publish --access public` from `~/Code/uCore/packages/usx-tokens/` — requires `npm login`
- [ ] Optionally switch uCore from local workspace dependency to `@udos/usx-tokens@^3.1.0` after publish
- [ ] Optionally remove Vite alias for `@udos/usx-tokens` in `vite.config.ts` after switching to versioned dependency

## Design Decisions

- **PicoCSS is the base framework.** We keep it. USX tokens layer on top via `var(--usx-*)` custom properties.
- **Themes only swap variable values** — the CSS rules (in `usx-standard.css`) don't change per theme.
- **HomeNest extends, never forks.** uCore token behavior is unchanged. HomeNest scales typography and touch targets up for 10-foot viewing but keeps the same variable names.
- **uCore's `--pico-*` compatibility mappings** are preserved in `tokens-color.css` so PicoCSS-based components resolve to USX colors transparently.

## Layout Alignment Rules (2026-08)

### Left-Alignment (Default)

All surface content is **left-aligned** by default. The tab bar left edge and content area left edge must match:

| Token                           | Value                            | Scope                           |
| ------------------------------- | -------------------------------- | ------------------------------- |
| `--usx-surface-content-padding` | `var(--usx-spacing-md)` (16px)   | Content area horizontal padding |
| `--usx-surface-tab-bar-padding` | `0 var(--usx-spacing-md)` (16px) | Tab bar horizontal padding      |

Both resolve to the same 16px left edge so tab links align with content headers.

### Center-Alignment (Card Grids)

Center alignment via `max-width: var(--usx-max-width); margin: 0 auto` is only used for card-grid landing layouts (Dashboard hub). Tab bars are never center-aligned.

### Surface Panel Nesting

`.surface__panel` (card: padding + background + border + border-radius) is for **sub-grouping within a panel**. Surface orchestrators must never wrap entire child panels in `.surface__panel` — only the panel's own internal sections use it.

```
.surface > .surface__content          ← outer padding context
  .server-tab-shell                    ← layout wrapper only
    .server-dashboard                  ← panel content
      .surface__panel                  ← internal section card ✅
      .surface__panel                  ← internal section card ✅
```

### Content Width Guidelines

| Content Type               | Width                             | Alignment |
| -------------------------- | --------------------------------- | --------- |
| Full-width tables/services | 100%                              | Left      |
| Prose/forms                | `max-width: 720px`                | Left      |
| Card grids                 | `max-width: var(--usx-max-width)` | Center    |
| Dashboard hub              | `max-width: var(--usx-max-width)` | Center    |

## Repository

- **Package source:** `github.com/uDosGo/uCore` → `packages/usx-tokens/`
- **Published as:** `@udos/usx-tokens` on npm/GitHub Packages
