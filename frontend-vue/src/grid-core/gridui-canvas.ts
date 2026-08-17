/**
 * GridCore UI — <gridui-canvas> Web Component
 *
 * Framework-agnostic custom element that renders a character grid
 * to a <canvas> element. Cells are rendered pixel-perfect with
 * NO gaps between tiles — each cell is exactly cellSize × cellSize
 * pixels with no padding, margin, or spacing.
 *
 * Features:
 * - Zero-gap cell rendering (fixes the "big gaps aside and below each tile" issue)
 * - 8-colour palette (foreground + background)
 * - Bold, blink, mosaic modes
 * - Intrinsic sizing: host width/height = cols × cellSize
 * - Emits cell-click and cell-hover events
 * - Supports setBuffer() for external buffer updates
 */

import { BitmapGlyphRenderer } from "./g0-renderer";
import { GlyphAtlas } from "./glyph-atlas";
import { PALETTE_DARK, PALETTE_PIXEL_32, getColour } from "./palette";
import bedsteadAtlasJson from "./seeds/glyph-atlas.bedstead.json";
import terminalAtlasJson from "./seeds/glyph-atlas.terminal.json";
import type { GridBuffer, GridCell } from "./types";

/* ─── Glyph Renderers (singletons) ──────────────────────────────── */
const terminalAtlas = new GlyphAtlas(terminalAtlasJson);
const bedsteadAtlas = new GlyphAtlas(bedsteadAtlasJson);
/** Bedstead (SAA5050) — 12×20 glyphs with 2×3 mosaic support. */
const bedsteadRenderer = new BitmapGlyphRenderer({
  glyphW: 12,
  glyphH: 20,
  fontFamily: '"Bedstead", monospace',
  mosaic: true,
  atlas: bedsteadAtlas,
});
/** Terminal (Press Start 2P) — 8×8 square glyphs, with 2×3 mosaic support so
 *  sextant seeds render identically across views. */
const terminalRenderer = new BitmapGlyphRenderer({
  glyphW: 8,
  glyphH: 8,
  fontFamily: '"Press Start 2P", monospace',
  mosaic: true,
  atlas: terminalAtlas,
});

/* ─── Template ─────────────────────────────────────────────────── */

const template = document.createElement("template");
template.innerHTML = `
  <style>
    :host {
      display: inline-block;  /* shrink-wrap to grid content */
      line-height: 0;
      font-size: 0;
      overflow: hidden;
    }
    canvas {
      display: block;
      image-rendering: pixelated;
      image-rendering: crisp-edges;
    }
  </style>
  <canvas></canvas>
`;

/* ─── Web Component ────────────────────────────────────────────── */

export class GridUICanvasElement extends HTMLElement {
  private _canvas: HTMLCanvasElement;
  private _ctx: CanvasRenderingContext2D | null;
  private _buffer: GridBuffer = [];
  private _cols: number = 40;
  private _rows: number = 25;
  private _cellSize: number = 16;
  /** Cell width in CSS px (glyph-aligned; may differ from height). */
  private _cellWidth: number = 16;
  /** Cell height in CSS px (glyph-aligned; may differ from width). */
  private _cellHeight: number = 16;
  private _font: string = "monospace";
  private _palette = PALETTE_DARK;
  private _blinkState: boolean = true;
  private _blinkInterval: number | null = null;
  private _hoveredCell: { col: number; row: number } | null = null;
  private _resizeObserver: ResizeObserver | null = null;
  /** Configured cellSize from attribute (before any container fitting) */
  private _configuredCellSize: number = 16;
  /** Whether to auto-fit to container (default true, set fit-container="false" to disable) */
  private _fitToContainerEnabled: boolean = true;
  /** Default render width per cell (CSS pixels). Square=cellSize, teletext=cellSize*1.3.
   *  Per-cell GridCell.width overrides this. */
  private _charWidth: number = 0; // 0 = use cellSize
  /** Whether to draw gridlines between cells */
  private _gridlines: boolean = false;
  /** Whether cells are square (glyph fills the square cell). Used for
   *  16:9 teletext so the grid matches the Terminal view's width. */
  private _squareCells: boolean = false;
  /** Fit the grid to the container at a fractional scale (fills exactly). */
  private _fitExact: boolean = false;

  /* ─── Observed Attributes ─────────────────────────────────────── */

  static get observedAttributes(): string[] {
    return [
      "cols",
      "rows",
      "cell-size",
      "char-width",
      "font",
      "palette",
      "gridlines",
      "square-cells",
      "fit-exact",
    ];
  }

  /* ─── Constructor ─────────────────────────────────────────────── */

  constructor() {
    super();
    const shadow = this.attachShadow({ mode: "open" });
    shadow.appendChild(template.content.cloneNode(true));

    this._canvas = shadow.querySelector("canvas")!;
    this._ctx = this._canvas.getContext("2d");

    // Bind event handlers
    this._canvas.addEventListener("click", this._onClick.bind(this));
    this._canvas.addEventListener("mousemove", this._onMouseMove.bind(this));
    this._canvas.addEventListener("mouseleave", this._onMouseLeave.bind(this));
  }

  /* ─── Lifecycle ───────────────────────────────────────────────── */

  connectedCallback(): void {
    this._parseAttributes();
    this._startBlink();
    // Observe container for responsive fitting
    this._resizeObserver = new ResizeObserver(() => this._fitToContainer());
    this._resizeObserver.observe(this.parentElement || this);
    // Size canvas and render
    this._fitToContainer();
    this._render();
  }

  disconnectedCallback(): void {
    this._stopBlink();
    this._resizeObserver?.disconnect();
    this._resizeObserver = null;
  }

  attributeChangedCallback(): void {
    this._parseAttributes();
    this._render();
  }

  /* ─── Attribute Parsing ───────────────────────────────────────── */

  private _parseAttributes(): void {
    this._cols = parseInt(this.getAttribute("cols") || "40", 10);
    this._rows = parseInt(this.getAttribute("rows") || "25", 10);
    this._cellSize = parseInt(this.getAttribute("cell-size") || "16", 10);
    this._configuredCellSize = this._cellSize;
    this._font = this.getAttribute("font") || "monospace";
    this._fitToContainerEnabled =
      this.getAttribute("fit-container") !== "false";
    this._charWidth = parseInt(this.getAttribute("char-width") || "0");
    const gridlinesAttr = this.getAttribute("gridlines");
    this._gridlines = gridlinesAttr !== null && gridlinesAttr !== "false";
    this._squareCells = this.getAttribute("square-cells") !== null;
    this._fitExact = this.getAttribute("fit-exact") !== null;
    // Palette: "pixel" selects the 32-colour palette, otherwise MODE 7 8-colour.
    this._palette =
      this.getAttribute("palette") === "pixel"
        ? PALETTE_PIXEL_32
        : PALETTE_DARK;

    // Ensure buffer matches dimensions
    if (this._buffer.length === 0) {
      this._buffer = this._createEmptyBuffer();
    }
  }

  /**
   * Fit the grid to the available container space.
   * Uses the configured cellSize when container is large enough,
   * shrinks cells proportionally when container is small.
   * Dynamically sizes the grid to the available output-panel space while
   * preserving the grid's aspect ratio (cols·glyphW : rows·glyphH). The scale
   * is a whole number of device pixels per glyph pixel so glyphs stay crisp at
   * every DPR — the grid grows or shrinks in discrete steps as the panel
   * resizes. The configured cell-size is used only as a fallback when the
   * container has no measurable size yet.
   * Disable with fit-container="false" attribute.
   */
  private _fitToContainer(): void {
    const renderer = this._getGlyphRenderer();
    const dpr = window.devicePixelRatio || 1;

    // Fallback scale from the configured cell size.
    let scale = Math.max(
      1,
      Math.floor((this._configuredCellSize * dpr) / renderer.glyphH),
    );

    if (this._fitToContainerEnabled && this.parentElement) {
      const parent = this.parentElement;
      const cs = getComputedStyle(parent);
      const padX =
        (parseFloat(cs.paddingLeft) || 0) + (parseFloat(cs.paddingRight) || 0);
      const padY =
        (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0);
      // Content box in device pixels (clientWidth includes padding).
      const availW = Math.max(0, (parent.clientWidth - padX) * dpr);
      const availH = Math.max(0, (parent.clientHeight - padY) * dpr);
      if (availW > 0 && availH > 0) {
        if (this._squareCells) {
          // Square cells: cols×rows of equal-size squares (16:9 teletext grid
          // that matches the Terminal view's width). Scale = device px/cell.
          scale = Math.max(
            1,
            Math.min(
              Math.floor(availW / this._cols),
              Math.floor(availH / this._rows),
            ),
          );
        } else if (this._fitExact) {
          // Fractional scale fills the panel exactly. Glyphs still render at
          // their native aspect (uniform scale), so text stays tall and crisp
          // enough — no horizontal stretch, no gaps.
          const maxScaleW = availW / (this._cols * renderer.glyphW);
          const maxScaleH = availH / (this._rows * renderer.glyphH);
          scale = Math.max(0.25, Math.min(maxScaleW, maxScaleH));
        } else {
          const maxScaleW = Math.floor(availW / (this._cols * renderer.glyphW));
          const maxScaleH = Math.floor(availH / (this._rows * renderer.glyphH));
          // Fit the grid to the panel, keeping aspect ratio (uniform scale).
          scale = Math.max(1, Math.min(maxScaleW, maxScaleH));
        }
      }
    }

    // Cell dimensions in whole device px. Square cells share one integer side;
    // native cells follow the glyph aspect (fractional scales are rounded so
    // the canvas backing store and the per-cell draw agree exactly).
    const cellW = this._squareCells
      ? Math.round(scale)
      : Math.round(renderer.glyphW * scale);
    const cellH = this._squareCells
      ? Math.round(scale)
      : Math.round(renderer.glyphH * scale);
    const pixelWidth = this._cols * cellW;
    const pixelHeight = this._rows * cellH;

    this._cellWidth = cellW / dpr; // CSS px (for hit-testing)
    this._cellHeight = cellH / dpr;
    this._cellSize = this._cellWidth;

    if (
      this._canvas.width !== pixelWidth ||
      this._canvas.height !== pixelHeight
    ) {
      this._canvas.width = pixelWidth;
      this._canvas.height = pixelHeight;
    }
    this._canvas.style.width = `${pixelWidth / dpr}px`;
    this._canvas.style.height = `${pixelHeight / dpr}px`;
    this.style.width = `${pixelWidth / dpr}px`;
    this.style.height = `${pixelHeight / dpr}px`;
  }

  /* ─── Blink Support ───────────────────────────────────────────── */

  private _startBlink(): void {
    this._blinkState = true;
    this._blinkInterval = window.setInterval(() => {
      this._blinkState = !this._blinkState;
      this._render();
    }, 500);
  }

  private _stopBlink(): void {
    if (this._blinkInterval !== null) {
      clearInterval(this._blinkInterval);
      this._blinkInterval = null;
    }
  }

  /* ─── Buffer Management ───────────────────────────────────────── */

  private _createEmptyBuffer(): GridBuffer {
    const buf: GridBuffer = [];
    for (let r = 0; r < this._rows; r++) {
      const row: GridCell[] = [];
      for (let c = 0; c < this._cols; c++) {
        row.push({ char: " ", fg: 7, bg: 0 });
      }
      buf.push(row);
    }
    return buf;
  }

  /**
   * Get the current grid buffer.
   */
  get buffer(): GridBuffer {
    return this._buffer;
  }

  /**
   * Set the grid buffer and re-render.
   * This is the primary API for external code to update the display.
   */
  setBuffer(buf: GridBuffer): void {
    this._buffer = buf;
    this._cols = buf.length > 0 ? buf[0].length : this._cols;
    this._rows = buf.length;
    this._render();
  }

  /**
   * Clear the buffer (fill with spaces).
   */
  clear(): void {
    this._buffer = this._createEmptyBuffer();
    this._render();
  }

  /**
   * Re-fit the grid to its container and re-render.
   * Call after the element becomes visible (e.g. when its tab is activated)
   * so the grid re-measures against the now-available panel size.
   */
  refit(): void {
    this._fitToContainer();
    this._render();
  }

  /**
   * Resolve the bitmap glyph renderer for the current font.
   * Every font renders as bitmaps — square pixels, no anti-aliasing.
   */
  private _getGlyphRenderer(): BitmapGlyphRenderer {
    if (this._font === "bedstead") return bedsteadRenderer;
    return terminalRenderer;
  }

  /* ─── Rendering ───────────────────────────────────────────────── */

  /**
   * Render the grid buffer to the canvas.
   *
   * CRITICAL: Each cell is drawn as a filled rectangle of exactly
   * cellSize × cellSize pixels, with NO gaps between adjacent cells.
   * The background colour fills the entire cell, then the character
   * is drawn on top in the foreground colour.
   *
   * FIX: letterSpacing is NOT a standard CanvasRenderingContext2D property.
   * It was being used incorrectly, causing no actual effect (silently ignored).
   * The proper approach is to set font size correctly for monospace chars
   * and rely on fillRect for exact pixel positioning.
   */
  private _render(): void {
    if (!this._ctx) return;

    const ctx = this._ctx;
    const dpr = window.devicePixelRatio || 1;

    // Ensure canvas is sized to fit container
    this._fitToContainer();

    // Disable canvas smoothing for pixel-perfect rendering — prevents
    // anti-aliased seams between adjacent filled rectangles.
    ctx.imageSmoothingEnabled = false;

    // Cell dimensions in device pixels (integer, glyph-aligned).
    const cellW = Math.round(this._cellWidth * dpr);
    const cellH = Math.round(this._cellHeight * dpr);

    // Clear canvas
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, this._canvas.width, this._canvas.height);

    // Pick the bitmap glyph renderer for this font. Every glyph is drawn as
    // a binary bitmap at uniform integer scale — true square pixels, centred
    // in its cell, with zero anti-aliasing.
    const glyphRenderer = this._getGlyphRenderer();

    // Draw each cell — ZERO gaps between cells.
    // Background fills overlap by 1px to eliminate anti-aliased seam lines
    // that can appear between adjacent rectangles on some GPUs/browsers.
    for (let r = 0; r < this._rows && r < this._buffer.length; r++) {
      const row = this._buffer[r];
      if (!row) continue;

      for (let c = 0; c < this._cols && c < row.length; c++) {
        const cell = row[c];
        if (!cell) continue;

        const x = c * cellW;
        const y = r * cellH;

        // Skip blink cells when blink state is off
        if (cell.blink && !this._blinkState) {
          ctx.fillStyle = getColour(cell.bg, this._palette);
          ctx.fillRect(x, y, cellW + 1, cellH + 1);
          continue;
        }

        // Draw background — fills entire cell + 1px overlap to kill seams
        ctx.fillStyle = getColour(cell.bg, this._palette);
        ctx.fillRect(x, y, cellW + 1, cellH + 1);

        // Draw character glyph (bitmap, square pixels, centred)
        if (cell.char && cell.char !== " " && glyphRenderer) {
          const fg = getColour(cell.fg, this._palette);
          // Use the full Unicode code point (supports astral glyphs such as
          // the U+1FB00 block sextants used for mosaic graphics).
          const charCode = cell.char.codePointAt(0) ?? cell.char.charCodeAt(0);
          if (cell.dh === "top" || cell.dh === "bottom") {
            // Double-height glyph: render only this cell's half, stretched
            // vertically so a top/bottom pair forms one 2×-tall character.
            glyphRenderer.renderHalfStretched(
              ctx,
              x,
              y,
              cellW,
              cellH,
              charCode,
              fg,
              cell.dh,
            );
          } else {
            glyphRenderer.renderStretched(
              ctx,
              x,
              y,
              cellW,
              cellH,
              charCode,
              fg,
            );
            if (cell.bold) {
              // Double-stroke: shift one device pixel right.
              glyphRenderer.renderStretched(
                ctx,
                x + dpr,
                y,
                cellW,
                cellH,
                charCode,
                fg,
              );
            }
          }
        }
      }
    }

    // Gridlines: draw 1px lines at cell boundaries (device-pixel crisp)
    if (this._gridlines) {
      ctx.strokeStyle = "rgba(255,255,255,0.30)";
      ctx.lineWidth = 1;
      const gw = this._cols * cellW;
      const gh = this._rows * cellH;
      ctx.beginPath();
      for (let c = 1; c < this._cols; c++) {
        const lx = Math.round(c * cellW) + 0.5;
        ctx.moveTo(lx, 0);
        ctx.lineTo(lx, gh);
      }
      for (let r = 1; r < this._rows; r++) {
        const ly = Math.round(r * cellH) + 0.5;
        ctx.moveTo(0, ly);
        ctx.lineTo(gw, ly);
      }
      ctx.stroke();
    }
  }

  /* ─── Event Handling ──────────────────────────────────────────── */

  private _getCellFromEvent(
    event: MouseEvent,
  ): { col: number; row: number } | null {
    const rect = this._canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Cell dimensions in CSS pixels (glyph-aligned: width may differ from height)
    const col = Math.floor(x / this._cellWidth);
    const row = Math.floor(y / this._cellHeight);

    if (col >= 0 && col < this._cols && row >= 0 && row < this._rows) {
      return { col, row };
    }
    return null;
  }

  private _onClick(event: MouseEvent): void {
    const cell = this._getCellFromEvent(event);
    if (cell) {
      this.dispatchEvent(
        new CustomEvent("cell-click", {
          detail: cell,
          bubbles: true,
          composed: true,
        }),
      );
    }
  }

  private _onMouseMove(event: MouseEvent): void {
    const cell = this._getCellFromEvent(event);
    if (cell) {
      const prev = this._hoveredCell;
      if (!prev || prev.col !== cell.col || prev.row !== cell.row) {
        this._hoveredCell = cell;
        this.dispatchEvent(
          new CustomEvent("cell-hover", {
            detail: cell,
            bubbles: true,
            composed: true,
          }),
        );
      }
    }
  }

  private _onMouseLeave(): void {
    this._hoveredCell = null;
    this.dispatchEvent(
      new CustomEvent("cell-hover", {
        detail: null,
        bubbles: true,
        composed: true,
      }),
    );
  }
}

/* ─── Registration ─────────────────────────────────────────────── */

if (!customElements.get("gridui-canvas")) {
  customElements.define("gridui-canvas", GridUICanvasElement);
}

/* ─── Factory Function ─────────────────────────────────────────── */

/**
 * Create a <gridui-canvas> element with the given options.
 *
 * This is the primary API for Vue/React integration.
 */
export function createGridUICanvas(
  options: {
    cols?: number;
    rows?: number;
    cellSize?: number;
    font?: string;
    /** Draw 1px gridlines at cell boundaries (default false). */
    gridlines?: boolean;
    /** Colour palette: "pixel" = 32-colour, otherwise 8-colour MODE 7. */
    palette?: string;
    /** Render square cells (glyph fills the square cell) instead of the
     *  glyph's native aspect — used for 16:9 teletext grids. */
    squareCells?: boolean;
    /** Fit to the container at a fractional scale so the grid fills it
     *  exactly (glyphs keep their native aspect). */
    fitExact?: boolean;
  } = {},
): GridUICanvasElement {
  const el = document.createElement("gridui-canvas") as GridUICanvasElement;
  if (options.cols !== undefined) el.setAttribute("cols", String(options.cols));
  if (options.rows !== undefined) el.setAttribute("rows", String(options.rows));
  if (options.cellSize !== undefined)
    el.setAttribute("cell-size", String(options.cellSize));
  if (options.font !== undefined) el.setAttribute("font", options.font);
  if (options.gridlines) el.setAttribute("gridlines", "");
  if (options.palette !== undefined)
    el.setAttribute("palette", options.palette);
  if (options.squareCells) el.setAttribute("square-cells", "");
  if (options.fitExact) el.setAttribute("fit-exact", "");
  return el;
}
