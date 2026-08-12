# USX Surface Baseline Spec

Status: Active
Last Updated: 2026-08-12

## Purpose

This document defines the canonical base sizes, layout primitives, and component styling for USX surfaces in uCore.

Use this document as the first comparison target when asked to:
- review a surface for USX compliance
- build a new surface in USX standard style

## Scope and Precedence

Precedence order:
1. This document
2. Token files in packages/usx-tokens/tokens/
3. Shared primitives in packages/usx-tokens/usx-standard.css

If there is a mismatch, token files and usx-standard.css are implementation truth and this doc must be updated.

## Canonical Token Scales

### Spacing

From packages/usx-tokens/tokens/tokens-spacing.css:
- --usx-spacing-xs: 4px
- --usx-spacing-sm: 8px
- --usx-spacing-md: 16px
- --usx-spacing-lg: 24px
- --usx-spacing-xl: 32px
- --usx-spacing-2xl: 48px

### Typography

From packages/usx-tokens/tokens/tokens-typography.css:
- --usx-font-size-xs: 0.75rem
- --usx-font-size-sm: 0.875rem
- --usx-font-size-base: 1rem
- --usx-font-size-lg: 1.125rem
- --usx-font-size-xl: 1.25rem
- --usx-font-size-2xl: 1.5rem
- --usx-font-size-3xl: 2rem

Font weights:
- --usx-font-weight-normal: 400
- --usx-font-weight-medium: 500
- --usx-font-weight-semibold: 600
- --usx-font-weight-bold: 700

Line heights:
- --usx-line-height-none: 1
- --usx-line-height-tight: 1.25
- --usx-line-height-normal: 1.5
- --usx-line-height-relaxed: 1.75

### Touch Targets and Controls

From packages/usx-tokens/tokens/tokens-touch.css and tokens-components.css:
- --usx-touch-min: 48px
- --usx-touch-min-sm: 40px
- --usx-control-size-sm: 32px
- --usx-control-size-md: 44px

### Radius and Borders

From packages/usx-tokens/tokens/tokens-components.css:
- --usx-radius-sm: 0.25rem
- --usx-radius-md: 0.5rem
- --usx-radius-lg: 0.75rem
- --usx-radius-xl: 1rem
- --usx-radius-2xl: 1.5rem
- --usx-radius-full: 9999px
- --usx-border-width: 1px
- --usx-border-width-thick: 2px

### Layout Widths

From packages/usx-tokens/tokens/tokens-components.css:
- --usx-max-width: 1280px
- --usx-prose-width: 72ch
- --usx-grid-min-col-width: 280px
- --usx-dropdown-min-width: 180px
- --usx-breakpoint-md: 768px
- --usx-breakpoint-lg: 1024px

## Surface Layout Baseline

Required primitives from packages/usx-tokens/usx-standard.css:
- .surface
- .surface__body
- .surface__header
- .surface__title
- .surface__description
- .surface__content
- .surface__topbar
- .surface--tab-nav-vertical

Required behavior:
- Surface shells use flex column and min-height: 0 contexts.
- Main scroll area is content, not the global page shell.
- Surface sections use tokenized padding and borders.
- Interactive controls satisfy minimum touch target requirements.

## Panel and Section Baseline

Use this structure for panelized surfaces:
- surface panel block with title and description
- stats row/grid for high-level counts
- section blocks with section title and grouped controls/content

Recommended class-level pattern:
- .surface__panel for internal grouped card sections
- .surface__panel-title for section heading
- .surface__panel-description for section subtitle/body context

## Card Baseline

Cards should use:
- tokenized border, radius, background, padding
- clear header row alignment
- consistent vertical rhythm between title, description, meta, and actions
- action row pinned predictably (avoid jumpy card heights)

Minimum standards:
- no hardcoded px for spacing where token exists
- no raw color literals in component CSS
- no inline style with hardcoded visual values

## Controls Baseline

Form and action controls should use:
- tokenized size, spacing, border, radius, color
- unified control heights within the same toolbar row
- clear focus state using tokenized border/shadow colors
- icon-only actions only when paired with proper aria-label/title

## Color and Icon Rules

- Use only var(--usx-color-*) in component CSS.
- Do not use --pico-* in new component-level styles.
- Use UIcon with Material Symbols; do not use emoji as UI icons.

## Compliance Rubric

When reviewing USX compliance, evaluate in this order:
1. Token usage correctness
2. Layout primitive usage (.surface and panel patterns)
3. Spacing/typography scale adherence
4. Control sizing and accessibility minimums
5. Visual consistency (cards/sections/stats)

A surface fails compliance if any of the following occur:
- hardcoded color literal where USX token exists
- hardcoded spacing/typography value where token exists
- non-tokenized border/radius in standard UI blocks
- touch targets below minimum without documented exception

## Build Workflow for New Surfaces

1. Start from surface primitives in usx-standard.css.
2. Compose with panel -> stats -> sections before custom ornamentation.
3. Apply only var(--usx-*) tokens in local CSS.
4. Keep responsive behavior aligned to --usx-breakpoint-md/lg.
5. Validate with typecheck and a visual pass at desktop and mobile widths.

## Source References

- packages/usx-tokens/tokens/tokens-color.css
- packages/usx-tokens/tokens/tokens-spacing.css
- packages/usx-tokens/tokens/tokens-typography.css
- packages/usx-tokens/tokens/tokens-touch.css
- packages/usx-tokens/tokens/tokens-components.css
- packages/usx-tokens/usx-standard.css
