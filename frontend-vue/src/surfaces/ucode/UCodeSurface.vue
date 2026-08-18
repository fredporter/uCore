<template>
  <div
    class="surface gridcore-surface"
    :class="[
      gridcorePresetClass,
      { 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' },
    ]"
  >
    <!-- Tab navigation: Terminal | Teletext | Pixel | Grid | Layer -->
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="UCODE_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    >
      <template #actions>
        <span class="ucode-actions-spacer"></span>
        <button
          class="surface-tab-nav__action-btn"
          title="Reload"
          @click="reloadGrid"
        >
          <UIcon name="refresh" />
        </button>
        <button
          class="surface-tab-nav__action-btn"
          title="Save"
          @click="exportGrid"
        >
          <UIcon name="save" />
        </button>
        <button
          class="surface-tab-nav__action-btn"
          title="Load"
          @click="triggerImport"
        >
          <UIcon name="folder_open" />
        </button>
        <button
          class="surface-tab-nav__action-btn preset-toggle"
          title="Viewport presets"
          @click="showPresets = !showPresets"
        >
          <UIcon name="dashboard" />
        </button>
      </template>
    </SurfaceTabNav>

    <!-- ─── Layer tab: full layer surface (shared canvas) ─── -->

    <!-- ─── Pixel Editor tab: true sub-cell 24×24 colour bitmap editor ─── -->
    <div v-if="activeTab === 'pixel'" class="pixel-editor-layout">
      <div class="pixel-editor-body">
        <div class="pixel-editor-main">
          <!-- Toolbar: tools, actions, palette — inside same content div -->
          <div class="pixel-toolbar">
            <div class="pixel-toolbar__dims">
              <span class="pixel-toolbar__label"
                >{{ pixelCell.w }}×{{ pixelCell.h }}</span
              >
            </div>
            <div class="pixel-toolbar__tools">
              <button
                v-for="t in PIXEL_TOOLS"
                :key="t.id"
                class="pixel-tool-btn"
                :class="{ active: pixelTool === t.id }"
                :title="t.label"
                @click="pixelTool = t.id"
              >
                <UIcon :name="t.icon" />
              </button>
            </div>
            <div class="pixel-toolbar__actions">
              <button
                class="pixel-toolbar__action-btn"
                title="Fill all pixels with current colour"
                @click="fillPixelEditor"
              >
                Fill
              </button>
              <button
                class="pixel-toolbar__action-btn"
                title="Clear all pixels"
                @click="clearPixelEditor"
              >
                Clear
              </button>
              <button
                class="pixel-toolbar__action-btn"
                title="Undo"
                @click="undoPixel"
              >
                Undo
              </button>
              <button
                class="pixel-toolbar__action-btn"
                title="Redo"
                @click="redoPixel"
              >
                Redo
              </button>
              <button
                class="pixel-toolbar__action-btn"
                title="Export pixel data"
                @click="exportPixelData"
              >
                Export
              </button>
            </div>
            <div class="pixel-toolbar__palette">
              <button
                class="pixel-tool-btn"
                :class="{ active: showColorPopover }"
                title="Colour Picker"
                @click="showColorPopover = !showColorPopover"
                @blur="hideColorPopover"
              >
                <UIcon name="palette" />
              </button>
              <!-- 32-colour popover -->
              <div
                class="pixel-colour-popover"
                v-if="showColorPopover"
                @mousedown.prevent
              >
                <button
                  v-for="(c, i) in PIXEL_PALETTE"
                  :key="i"
                  class="pixel-colour-popover__swatch"
                  :class="{ 'fg-active': pixelColor === i }"
                  :style="{ background: c.hex }"
                  :title="`${c.name} · ${i}`"
                  @click="pixelColor = i"
                >
                  <span v-if="pixelColor === i" class="colour-marker fg"
                    >●</span
                  >
                </button>
              </div>
            </div>
          </div>
          <div
            class="pixel-canvas-wrapper"
            ref="pixelCanvasRef"
            tabindex="0"
            @mousedown="pixelIsDragging = true"
            @mouseup="pixelIsDragging = false"
            @mouseleave="pixelIsDragging = false"
          >
            <span class="editor-section__label editor-section__label--overlay">
              Pixel Editor · {{ pixelCell.w }}×{{ pixelCell.h }} ·
              {{ pixelSymbol || "?" }} · {{ pixelFontLabel }} · ink
              {{ pixelInk?.w ?? 0 }}×{{ pixelInk?.h ?? 0 }}
            </span>
          </div>
        </div>
        <!-- Sidebar: colours, font, symbol map, library -->
        <aside class="editor-sidebar">
          <div class="sidebar-section">
            <h4 class="sidebar-title">Colours</h4>
            <div class="sidebar-chars-grid">
              <button
                v-for="(c, i) in PIXEL_PALETTE"
                :key="i"
                class="sidebar-char-chip sidebar-colour-swatch"
                :class="{ 'fg-active': pixelColor === i }"
                :style="{ background: c.hex }"
                :title="`${c.name} · ${i}`"
                @click="pixelColor = i"
              >
                <span v-if="pixelColor === i" class="colour-marker fg">●</span>
              </button>
            </div>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">Font</h4>
            <div class="sidebar-font-btns">
              <button
                class="sidebar-font-btn"
                :class="{ active: pixelFont === 'pressstart2p' }"
                @click="pixelFont = 'pressstart2p'"
              >
                Terminal
              </button>
              <button
                class="sidebar-font-btn"
                :class="{ active: pixelFont === 'bedstead' }"
                @click="pixelFont = 'bedstead'"
              >
                Bedstead
              </button>
            </div>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">Symbol</h4>
            <div class="sidebar-char-row">
              <input
                class="sidebar-char-input"
                v-model="pixelSymbol"
                maxlength="1"
              />
              <span class="sidebar-char-code">{{ pixelSymbolCode }}</span>
            </div>
            <div class="sidebar-font-btns">
              <button class="sidebar-font-btn" @click="loadGlyphFromFont">
                Load
              </button>
              <button class="sidebar-font-btn" @click="saveGlyphToMap">
                Save
              </button>
            </div>
          </div>
          <div class="sidebar-section sidebar-font-chars">
            <h4 class="sidebar-title">Library</h4>
            <div class="sidebar-chars-group">
              <div class="sidebar-chars-caption">ASCII</div>
              <div class="sidebar-chars-grid">
                <button
                  v-for="ch in pixelSymbols.ascii"
                  :key="ch"
                  class="sidebar-char-chip"
                  :class="{ selected: pixelSymbol === ch }"
                  :title="symbolCodeLabel(ch)"
                  @click="selectPixelSymbol(ch)"
                >
                  {{ ch }}
                </button>
              </div>
            </div>
            <div class="sidebar-chars-group">
              <div class="sidebar-chars-caption">Symbols &amp; Icons</div>
              <div class="sidebar-chars-grid">
                <button
                  v-for="ch in pixelSymbols.icons"
                  :key="ch"
                  class="sidebar-char-chip"
                  :class="{ selected: pixelSymbol === ch }"
                  :title="symbolCodeLabel(ch)"
                  @click="selectPixelSymbol(ch)"
                >
                  {{ ch }}
                </button>
              </div>
            </div>
            <div class="sidebar-chars-group">
              <div class="sidebar-chars-caption">Emoji</div>
              <div class="sidebar-chars-grid">
                <button
                  v-for="ch in pixelSymbols.emoji"
                  :key="ch"
                  class="sidebar-char-chip"
                  :class="{ selected: pixelSymbol === ch }"
                  :title="symbolCodeLabel(ch)"
                  @click="selectPixelSymbol(ch)"
                >
                  {{ ch }}
                </button>
              </div>
            </div>
          </div>
          <div class="sidebar-section">
            <div class="sidebar-font-btns">
              <button class="sidebar-font-btn" @click="exportSymbolLibrary">
                Export
              </button>
              <button class="sidebar-font-btn" @click="triggerSymbolImport">
                Import
              </button>
            </div>
          </div>
          <input
            ref="symbolImportRef"
            type="file"
            accept=".json"
            class="ucode-import-input"
            @change="onSymbolImportFile"
          />
        </aside>
      </div>
    </div>

    <!-- ─── Grid Builder tab: Layer Editor ─── -->
    <div v-else-if="activeTab === 'grid'" class="grid-editor-layout">
      <!-- Slide-in preset popover (floats over editor) -->
      <div class="preset-popover" :class="{ open: showPresets }">
        <div class="preset-popover__inner">
          <button
            v-for="(p, i) in VIEWPORT_PRESETS"
            :key="p.name"
            class="preset-popover__item"
            :class="{ active: viewportIndex === i }"
            @click="selectPreset(i)"
          >
            <span class="preset-popover__dims">{{ p.cols }}×{{ p.rows }}</span>
            <span class="preset-popover__desc">{{ p.description }}</span>
          </button>
        </div>
      </div>
      <div class="grid-editor-main">
        <!-- Layer Editor — full layer as primary editing surface -->
        <div class="layer-editor-primary">
          <div class="layer-editor__toolbar">
            <div class="layer-editor__dims">
              <input
                class="layer-editor__input"
                type="number"
                v-model.number="layerCols"
                min="4"
                max="256"
                @change="onLayerResize"
              />
              <span class="layer-editor__sep">×</span>
              <input
                class="layer-editor__input"
                type="number"
                v-model.number="layerRows"
                min="4"
                max="256"
                @change="onLayerResize"
              />
            </div>
            <div class="layer-editor__tools">
              <button
                v-for="t in TOOLS"
                :key="t.id"
                class="pixel-tool-btn"
                :class="{ active: currentTool === t.id }"
                :title="t.label"
                @click="currentTool = t.id"
              >
                <UIcon :name="t.icon" />
              </button>
            </div>
            <div class="layer-editor__actions">
              <button
                class="pixel-toolbar__action-btn"
                @click="fillLayer"
                title="Fill all cells"
              >
                Fill
              </button>
              <button
                class="pixel-toolbar__action-btn"
                @click="clearLayer"
                title="Clear layer"
              >
                Clr
              </button>
              <button
                class="pixel-toolbar__action-btn"
                @click="loadSeedDemo('wordmark')"
                title="Load uCode wordmark seed (sextant connected cells)"
              >
                Logo
              </button>
              <button
                class="pixel-toolbar__action-btn"
                @click="loadSeedDemo('frame')"
                title="Load panel frame seed (sextant connected cells)"
              >
                Frame
              </button>
              <button
                class="pixel-toolbar__action-btn"
                @click="exportGrid"
                title="Export as JSON"
              >
                Exp
              </button>
              <button
                class="pixel-toolbar__action-btn"
                @click="triggerImport"
                title="Import JSON"
              >
                Imp
              </button>
            </div>
            <div class="layer-editor__palette">
              <button
                class="pixel-tool-btn"
                :class="{ active: showLayerColorPopover }"
                title="Colour Picker"
                @click="showLayerColorPopover = !showLayerColorPopover"
                @blur="hideLayerColorPopover"
              >
                <UIcon name="palette" />
              </button>
              <!-- 3×3 colour grid popover -->
              <div
                class="layer-colour-popover"
                v-if="showLayerColorPopover"
                @mousedown.prevent
              >
                <button
                  v-for="(c, i) in PALETTE"
                  :key="i"
                  class="layer-colour-popover__swatch"
                  :class="[
                    `layer-colour-popover__swatch--${i}`,
                    {
                      'fg-active': selectedFg === i,
                      'bg-active': selectedBg === i,
                    },
                  ]"
                  :title="
                    c.name +
                    (selectedFg === i ? ' FG' : selectedBg === i ? ' BG' : '') +
                    ' | L-click FG · R-click BG'
                  "
                  @click="selectedFg = i"
                  @click.right.prevent="selectedBg = i"
                >
                  <span v-if="selectedBg === i" class="colour-marker bg"
                    >B</span
                  >
                </button>
                <!-- 9th cell: transparent/empty -->
                <button
                  class="layer-colour-popover__swatch layer-colour-popover__swatch--empty"
                  :class="{ 'bg-active': selectedBg === -1 }"
                  title="Transparent / Empty | R-click BG"
                  @click="selectedFg = -1"
                  @click.right.prevent="selectedBg = -1"
                >
                  <span v-if="selectedBg === -1" class="colour-marker bg"
                    >B</span
                  >
                </button>
              </div>
            </div>
            <span class="layer-editor__info"
              >{{ currentTool }} · ({{ layerCursorCol }},
              {{ layerCursorRow }})</span
            >
          </div>
          <div
            class="layer-editor__viewport"
            ref="layerViewportRef"
            tabindex="0"
            @keydown="onLayerKeydown"
            @mousedown="onLayerMouseDown"
          ></div>
          <input
            ref="importInputRef"
            type="file"
            accept=".json"
            class="ucode-import-input"
            @change="onImportFile"
          />
        </div>
      </div>
      <!-- Sidebar: brush palette for placing chars into grid -->
      <aside class="editor-sidebar">
        <div class="sidebar-section">
          <h4 class="sidebar-title">Brush</h4>
          <div class="sidebar-font-btns">
            <button
              class="sidebar-font-btn"
              :class="{ active: editorFont === 'pressstart2p' }"
              @click="editorFont = 'pressstart2p'"
            >
              Terminal
            </button>
            <button
              class="sidebar-font-btn"
              :class="{ active: editorFont === 'bedstead' }"
              @click="editorFont = 'bedstead'"
            >
              Bedstead
            </button>
          </div>
        </div>
        <div class="sidebar-section sidebar-font-chars">
          <h4 class="sidebar-title">Characters</h4>
          <div class="sidebar-chars-grid">
            <button
              v-for="ch in fontChars"
              :key="ch"
              class="sidebar-char-chip"
              :class="{ selected: selectedChar === ch }"
              :title="`U+${ch.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')}`"
              @click="selectBrushChar(ch)"
            >
              {{ ch }}
            </button>
          </div>
        </div>
        <div class="sidebar-section">
          <h4 class="sidebar-title">Active Char</h4>
          <div class="sidebar-char-row">
            <input
              class="sidebar-char-input"
              v-model="selectedChar"
              maxlength="1"
              placeholder="Char"
            />
            <span class="sidebar-char-code">{{ selectedCharCode }}</span>
          </div>
        </div>
      </aside>
    </div>

    <!-- ─── Terminal / Teletext tabs ─── -->
    <template v-else>
      <div class="surface__body">
        <div class="preset-popover" :class="{ open: showPresets }">
          <div class="preset-popover__inner">
            <button
              v-for="(p, i) in VIEWPORT_PRESETS"
              :key="p.name"
              class="preset-popover__item"
              :class="{ active: viewportIndex === i }"
              @click="selectPreset(i)"
            >
              <span class="preset-popover__dims"
                >{{ p.cols }}×{{ p.rows }}</span
              >
              <span class="preset-popover__desc">{{ p.description }}</span>
            </button>
          </div>
        </div>
        <div v-if="activeTab === 'layer'" class="layer-map-selector">
          <span class="layer-map-selector__label">Map</span>
          <button
            v-for="m in LAYER_MAPS"
            :key="m.id"
            class="layer-map-selector__btn"
            :class="{ active: layerMapName === m.id }"
            @click="loadLayerMapByName(m.id)"
          >
            {{ m.label }}
          </button>
        </div>
        <div v-if="activeTab === 'glyphs'" class="layer-map-selector">
          <span class="layer-map-selector__label">Font</span>
          <button
            class="layer-map-selector__btn"
            :class="{ active: glyphInspectorFont === 'pressstart2p' }"
            @click="setGlyphInspectorFont('pressstart2p')"
          >
            Terminal 8×8
          </button>
          <button
            class="layer-map-selector__btn"
            :class="{ active: glyphInspectorFont === 'bedstead' }"
            @click="setGlyphInspectorFont('bedstead')"
          >
            Bedstead 12×20
          </button>
        </div>
        <div class="surface__canvas">
          <div
            ref="gridContainer"
            class="ucode-viewport"
            :class="{ 'ucode-viewport--terminal': activeTab === 'terminal' }"
            role="region"
            tabindex="0"
            :aria-label="`${currentTitle} viewport`"
            @keydown="onSharedKeydown"
            @mousedown="focusGridContainer"
          ></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * @component UCodeSurface
 * @description uCode bridge surface — unified hub with Pixel Editor, Grid Builder, and Layer Composer.
 * All modes use the framework-agnostic <gridui-canvas> Web Component.
 * @category surfaces
 * @usage Routed at '/ucode'.
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useShellStore } from "../../stores/shell";
import { useGridCoreSettingsStore } from "../../stores/gridcoreSettings";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import type { TabDef } from "../../skills/molecules/SurfaceTabNav.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import {
  createGridUICanvas,
  type GridUICanvasElement,
} from "../../grid-core/gridui-canvas";
import {
  createBuffer,
  writeString,
  fill,
  scroll as scrollBuffer,
  cloneBuffer,
  clear as clearBuffer,
} from "../../grid-core/buffer";
import { scaleBuffer, GRID_PRESETS } from "../../grid-core/algebra";
import { PALETTE_DARK, PALETTE_PIXEL_32 } from "@udos/gridcore/palette";
import { BitmapGlyphRenderer } from "../../grid-core/g0-renderer";
import { GlyphAtlas } from "../../grid-core/glyph-atlas";
import terminalAtlasJson from "../../grid-core/seeds/glyph-atlas.terminal.json";
import bedsteadAtlasJson from "../../grid-core/seeds/glyph-atlas.bedstead.json";
import type { GridBuffer, GridCell } from "@udos/gridcore/buffer/cell";
import {
  PixelEditor,
  createPixelBuffer,
  createSymbolMap,
  deserializeSymbolMap,
  glyphBitmapToPixelBuffer,
  colourGlyphToPixelBuffer,
  gridBufferToPixelBuffer,
  pixelBufferToGridBuffer,
  serializeSymbolMap,
  measureInkBounds,
  type SymbolMap,
} from "@udos/gridcore/pixel";
import {
  renderSeed,
  placeSeed,
  patternToChar,
} from "../../grid-core/seeds/render-seed";
import type { GridSeed } from "../../grid-core/seeds/grid-seed";
import uCodeWordmarkSeed from "../../grid-core/seeds/grids/uCode-wordmark.json";
import panelFrameSeed from "../../grid-core/seeds/grids/panel-frame.json";
import { loadLayerMap } from "../../grid-core/seeds/load-layer-map";
import type { LayerMap } from "../../grid-core/seeds/layer-map";
import worldMapSeed from "../../grid-core/seeds/layers/world-map.json";
import moonMapSeed from "../../grid-core/seeds/layers/moon.json";
import regionMapSeed from "../../grid-core/seeds/layers/region.json";
import {
  type VaultDoc,
  type VaultLibrary,
  TELETEXT_FASTEXT,
  DOC_PAGE_OFFSET,
  DOCS_PER_LIST_PAGE,
  MAX_DOCS_PER_LIBRARY,
  PUBLIC_LIBRARY_DEFS,
} from "../../grid-core/teletext";

const shell = useShellStore();
const gridcoreSettings = useGridCoreSettingsStore();
const gridcorePresetClass = computed(
  () => `gridcore-surface--${gridcoreSettings.preset}`,
);

/* ─── Tab Definitions ─────────────────────────────────────────────── */
const UCODE_TABS: TabDef[] = [
  { id: "terminal", label: "Terminal", icon: "terminal" },
  { id: "teletext", label: "Teletext", icon: "tv" },
  { id: "pixel", label: "Pixel", icon: "grid_on" },
  { id: "grid", label: "Grid", icon: "dashboard" },
  { id: "layer", label: "Layer", icon: "layers" },
  { id: "glyphs", label: "Glyphs", icon: "font_download" },
];

const activeTab = ref("terminal");

const tabTitles: Record<string, string> = {
  terminal: "uCode — Terminal",
  teletext: "uCode — Teletext",
  pixel: "uCode — Pixel Editor",
  grid: "uCode — Grid Editor",
  layer: "uCode — Layer Surface",
  glyphs: "uCode — Glyph Inspector",
};

const currentTitle = computed(
  () => tabTitles[activeTab.value] || "uCode — GridCore",
);

/* ─── Grid Configs ────────────────────────────────────────────────── */
const tabConfigs: Record<
  string,
  {
    cols: number;
    rows: number;
    font: string;
    cellSize: number;
    charWidth?: number;
    square?: boolean;
    fitExact?: boolean;
  }
> = {
  terminal: {
    cols: 42,
    rows: 27,
    font: "pressstart2p",
    cellSize: 20,
    square: true,
  },
  teletext: {
    cols: 74,
    rows: 25,
    font: "bedstead",
    cellSize: 20,
    fitExact: true,
  },
  pixel: { cols: 24, rows: 24, font: "bedstead", cellSize: 24 },
  grid: { cols: 40, rows: 25, font: "bedstead", cellSize: 20 },
  layer: { cols: 40, rows: 25, font: "bedstead", cellSize: 20 },
  glyphs: { cols: 16, rows: 7, font: "pressstart2p", cellSize: 24 },
};

/* ─── Single-Canvas Tabs ──────────────────────────────────────────── */
const gridContainer = ref<HTMLDivElement>();
const canvasCache = new Map<string, GridUICanvasElement>();
let activeCanvas: GridUICanvasElement | null = null;
let terminalSocket: WebSocket | null = null;
let terminalCursorX = 0;
let terminalCursorY = 0;

/** Terminal content area (the PTY is 40×25); the grid adds a 1-cell black
 *  margin all round (42×27). */
const TERMINAL_COLS = 40;
const TERMINAL_ROWS = 25;
const TERMINAL_MARGIN = 1;
let terminalBuffer: GridBuffer | null = null;
let terminalAtLineStart = false;

const UCORE_API =
  import.meta.env.VITE_UCORE_URL ||
  import.meta.env.VITE_SNACKBAR_URL ||
  "http://localhost:8484";

/* ─── Shared Brush State (persists across Pixel/Grid tabs) ─────────── */
const PALETTE = PALETTE_DARK; // 8-colour MODE 7 — Grid/Layer editors
const PIXEL_PALETTE = PALETTE_PIXEL_32; // 32-colour — Pixel Editor

const TOOLS = [
  { id: "pencil", label: "Pencil", icon: "edit" },
  { id: "fill", label: "Flood fill", icon: "format_paint" },
  { id: "erase", label: "Eraser", icon: "ink_eraser" },
  { id: "eyedropper", label: "Eyedropper", icon: "colorize" },
] as const;

// Pixel Editor tools (true sub-cell 24×24 colour bitmap)
const PIXEL_TOOLS = [
  { id: "pencil", label: "Pencil", icon: "edit" },
  { id: "fill", label: "Flood fill", icon: "format_paint" },
  { id: "erase", label: "Eraser", icon: "ink_eraser" },
  { id: "eyedropper", label: "Eyedropper", icon: "colorize" },
] as const;

const pixelTool = ref<"pencil" | "fill" | "erase" | "eyedropper">("pencil");
const showColorPopover = ref(false);
const showLayerColorPopover = ref(false);

function hideColorPopover() {
  setTimeout(() => {
    showColorPopover.value = false;
  }, 200);
}
function hideLayerColorPopover() {
  setTimeout(() => {
    showLayerColorPopover.value = false;
  }, 200);
}

// Pixel Editor — fixed 24×24 sub-cell colour bitmap (per gridcore spec)
const pixelColor = ref(7);
const pixelIsDragging = ref(false);

/* ─── Pixel editor — font / symbol character map ───────────────────── */
// Wire the committed glyph atlases (the same deterministic bitmaps used by
// the Glyphs tab) into the Pixel Editor renderers. Without an atlas the
// renderer falls back to runtime fillText rasterisation, which diverges from
// the Glyphs tab and fails for the sextant/box glyphs.
const bedsteadGlyphRenderer = new BitmapGlyphRenderer({
  glyphW: 12,
  glyphH: 20,
  fontFamily: '"Bedstead", monospace',
  mosaic: true,
  atlas: new GlyphAtlas(bedsteadAtlasJson),
});
const terminalGlyphRenderer = new BitmapGlyphRenderer({
  glyphW: 8,
  glyphH: 8,
  fontFamily: '"Press Start 2P", monospace',
  mosaic: true,
  atlas: new GlyphAtlas(terminalAtlasJson),
});

/** Source font used when loading glyphs into the editor. */
const pixelFont = ref<"pressstart2p" | "bedstead">("bedstead");
/**
 * Cell dimensions for the active font (the glyph's true em box).
 * Terminal 8×8 @ 3× = 24×24; Bedstead 12×20 @ 2× = 24×40.
 */
const pixelCell = computed<{ w: number; h: number }>(() =>
  pixelFont.value === "bedstead" ? { w: 24, h: 40 } : { w: 24, h: 24 },
);
/** Human-readable label for the active font. */
const pixelFontLabel = computed(() =>
  pixelFont.value === "bedstead" ? "Bedstead" : "Terminal",
);
/** Currently edited symbol (Unicode char). */
const pixelSymbol = ref("#");
/** The editable symbol library: codepoint → cell-sized bitmap. */
const symbolMap = ref<SymbolMap>(createSymbolMap());

/** Full Unicode code point of a character (astral-safe, e.g. 😀 U+1F600). */
function symbolCodePoint(ch: string): number | null {
  const cp = ch.codePointAt(0);
  return cp === undefined ? null : cp;
}

/** `U+XXXX` label for a character, padded for BMP but astral-safe. */
function symbolCodeLabel(ch: string): string {
  const cp = symbolCodePoint(ch);
  return cp === null
    ? ""
    : `U+${cp.toString(16).toUpperCase().padStart(4, "0")}`;
}

const pixelSymbolCode = computed(() => symbolCodeLabel(pixelSymbol.value));

/**
 * Curated symbol / icon set — monochrome glyphs that rasterise cleanly and
 * map 1:1 onto the 24×24 bitmap (arrows, geometry, blocks, boxes, dingbats).
 */
const PIXEL_SYMBOL_ICONS = [
  "←",
  "↑",
  "→",
  "↓",
  "↔",
  "↕",
  "◄",
  "▲",
  "►",
  "▼",
  "●",
  "○",
  "◐",
  "◑",
  "◒",
  "◓",
  "◔",
  "◕",
  "◖",
  "◗",
  "■",
  "□",
  "▢",
  "△",
  "▽",
  "◁",
  "▷",
  "◆",
  "◇",
  "▱",
  "█",
  "▀",
  "▄",
  "▌",
  "▐",
  "░",
  "▒",
  "▓",
  "⬛",
  "⬜",
  "│",
  "─",
  "┌",
  "┐",
  "└",
  "┘",
  "├",
  "┤",
  "┬",
  "┴",
  "┼",
  "║",
  "═",
  "╔",
  "╗",
  "╚",
  "╝",
  "╠",
  "╣",
  "╦",
  "╩",
  "╬",
  "☀",
  "☾",
  "☁",
  "☂",
  "☃",
  "★",
  "☆",
  "♥",
  "♦",
  "♣",
  "♠",
  "♪",
  "♫",
  "♯",
  "⚑",
  "⚔",
  "⚙",
  "⚡",
  "☠",
  "⌂",
  "♔",
  "♕",
  "♖",
  "♗",
  "♘",
  "♙",
  "♚",
  "♛",
  "♜",
  "♝",
  "♞",
  "♟",
];

/** Common emoji for the symbol map (rasterised as monochrome silhouettes). */
const PIXEL_SYMBOL_EMOJI = [
  "😀",
  "😃",
  "😄",
  "😁",
  "😆",
  "😂",
  "🙂",
  "😉",
  "😊",
  "😎",
  "😍",
  "😭",
  "👍",
  "👎",
  "👏",
  "🙌",
  "🔥",
  "💀",
  "🎉",
  "❤️",
  "💙",
  "💚",
  "💛",
  "💜",
  "⭐",
  "✨",
  "⚡",
  "🌙",
  "☀️",
  "🎮",
  "🕹️",
  "👾",
  "🧱",
  "🔲",
  "🔳",
];

/** Characters offered in the Pixel sidebar library, grouped by class. */
const pixelSymbols = computed(() => {
  const ascii: string[] = [];
  const start = pixelFont.value === "pressstart2p" ? 0x21 : 0x20;
  for (let i = start; i <= 0x7e; i++) ascii.push(String.fromCharCode(i));
  return { ascii, icons: PIXEL_SYMBOL_ICONS, emoji: PIXEL_SYMBOL_EMOJI };
});

function currentGlyphRenderer(): BitmapGlyphRenderer {
  return pixelFont.value === "bedstead"
    ? bedsteadGlyphRenderer
    : terminalGlyphRenderer;
}

/** Load the selected symbol's glyph from the font into the editor. */
function loadGlyphFromFont() {
  const renderer = currentGlyphRenderer();
  const code = symbolCodePoint(pixelSymbol.value);
  if (code === null) return;
  const { w, h } = pixelCell.value;
  if (renderer.hasGlyph(code)) {
    // Deterministic atlas / mosaic glyph → binary bitmap, white ink, fills
    // the cell (8×8→24×24 @3×, 12×16→24×32 @2×) with no side bearings.
    const bitmap = renderer.getBitmap(code);
    pixelEditor = new PixelEditor(
      glyphBitmapToPixelBuffer(
        bitmap,
        renderer.glyphW,
        renderer.glyphH,
        7,
        w,
        h,
      ),
      w,
      h,
    );
  } else {
    // Colour glyph (emoji/symbol): rasterise at the cell size and quantise
    // to the 32-colour palette, preserving the emoji's own colours.
    const rgba = renderer.rasterizeColour(code, w, h);
    pixelEditor = new PixelEditor(
      colourGlyphToPixelBuffer(rgba, PIXEL_PALETTE, w, h),
      w,
      h,
    );
  }
  renderPixelBuffer();
}

/** Store the current editor bitmap under the selected symbol. */
function saveGlyphToMap() {
  if (!pixelEditor) return;
  const code = symbolCodePoint(pixelSymbol.value);
  if (code === null) return;
  symbolMap.value.set(code, pixelEditor.buffer);
}

/** Select a symbol: load its edited bitmap if present, else load the font glyph. */
function selectPixelSymbol(ch: string) {
  pixelSymbol.value = ch;
  const code = symbolCodePoint(ch);
  const stored = code === null ? undefined : symbolMap.value.get(code);
  const { w, h } = pixelCell.value;
  if (stored) {
    pixelEditor = new PixelEditor(stored, w, h);
    renderPixelBuffer();
  } else {
    loadGlyphFromFont();
  }
}

function exportSymbolLibrary() {
  const data = serializeSymbolMap(symbolMap.value);
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "ucode-symbol-map.json";
  a.click();
  URL.revokeObjectURL(url);
}

function triggerSymbolImport() {
  symbolImportRef.value?.click();
}

function onSymbolImportFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      symbolMap.value = deserializeSymbolMap(
        JSON.parse(reader.result as string),
      );
    } catch (err) {
      console.error("Symbol map import failed:", err);
    }
  };
  reader.readAsText(file);
  (e.target as HTMLInputElement).value = "";
}

const selectedFg = ref(7);
const selectedBg = ref(0);
const selectedChar = ref("#");
const editorFont = ref<"pressstart2p" | "bedstead">("bedstead");
const currentTool = ref<"pencil" | "fill" | "erase" | "eyedropper">("pencil");

const selectedCharCode = computed(() =>
  selectedChar.value
    ? `U+${selectedChar.value.charCodeAt(0).toString(16).toUpperCase().padStart(4, "0")}`
    : "",
);

/** Characters shown in the Grid sidebar font char set */
const fontChars = computed(() => {
  if (editorFont.value === "bedstead") {
    const chars: string[] = [];
    for (let i = 0x20; i <= 0x7e; i++) chars.push(String.fromCharCode(i));
    chars.push("█", "▄", "▀", "▐", "▌", "░", "▒", "▓", "│", "─", "║", "═");
    chars.push("╔", "╗", "╚", "╝", "╠", "╣", "╦", "╩", "╬");
    return chars;
  }
  const chars: string[] = [];
  for (let i = 0x21; i <= 0x7e; i++) chars.push(String.fromCharCode(i));
  return chars;
});

/** Set brush char (used by the Grid tab sidebar). */
function selectBrushChar(ch: string) {
  selectedChar.value = ch;
}

/* ─── Grid Layer State ────────────────────────────────────────────── */
let LAYER_COLS = 40;
let LAYER_ROWS = 25;
const layerCols = ref(LAYER_COLS);
const layerRows = ref(LAYER_ROWS);

const VIEWPORT_PRESETS = GRID_PRESETS.filter((p) =>
  [
    "editor",
    "teletext",
    "terminal",
    "terminal-retro",
    "teletext-retro",
    "square-60",
    "square-80",
    "classic-40x30",
    "classic-80x60",
    "widescreen-80x45",
    "widescreen-128x72",
    "ultrawide-160x91",
  ].includes(p.name),
);
const viewportIndex = ref(0);
const currentPreset = computed(() => VIEWPORT_PRESETS[viewportIndex.value]);
const showPresets = ref(false);

function selectPreset(i: number) {
  viewportIndex.value = i;
  showPresets.value = false;
}

watch(viewportIndex, () => onPresetChange(currentPreset.value.name));

const layerCursorCol = ref(0);
const layerCursorRow = ref(0);
let layerBuffer: GridBuffer = createBuffer(LAYER_COLS, LAYER_ROWS);
let layerIsDragging = false;

/* ─── Canvas refs & elements ──────────────────────────────────────── */
const layerViewportRef = ref<HTMLDivElement>();
const pixelCanvasRef = ref<HTMLDivElement>();
const importInputRef = ref<HTMLInputElement>();
const symbolImportRef = ref<HTMLInputElement>();

let layerCanvas: GridUICanvasElement | null = null;
let pixelCanvas: GridUICanvasElement | null = null;

/* ─── Watchers ────────────────────────────────────────────────────── */
watch(editorFont, (font) => {
  if (layerCanvas) layerCanvas.setAttribute("font", font);
});

// Reload the current symbol's glyph when the Pixel Editor font changes so
// the canvas always reflects the selected font's atlas bitmaps.
watch(pixelFont, () => {
  if (activeTab.value === "pixel") loadGlyphFromFont();
});

/* ─── Pixel Editor (true sub-cell colour bitmap) ─────────────────── */
let pixelEditor: PixelEditor | null = null;
/** Preview buffer: each pixel as a solid-colour cell for <gridui-canvas>. */
let pixelBuffer: GridBuffer = createBuffer(24, 24);
/** Ink bounding box of the current glyph (variable-width readout). */
const pixelInk = ref<{ w: number; h: number } | null>(null);

function renderPixelBuffer() {
  if (!pixelCanvas || !pixelEditor) return;
  const { w, h } = pixelCell.value;
  pixelBuffer = pixelBufferToGridBuffer(pixelEditor.buffer, w, h);
  pixelCanvas.setBuffer(cloneBuffer(pixelBuffer));
  const b = measureInkBounds(pixelEditor.buffer, w, h);
  pixelInk.value = b
    ? { w: b.maxX - b.minX + 1, h: b.maxY - b.minY + 1 }
    : null;
}

function initPixelEditor() {
  if (!pixelCanvasRef.value) return;
  pixelCanvas?.remove();
  const { w, h } = pixelCell.value;
  pixelEditor = new PixelEditor(createPixelBuffer(0, w, h), w, h);
  pixelCanvas = createGridUICanvas({
    cols: w,
    rows: h,
    font: "pressstart2p",
    cellSize: 24,
    gridlines: true,
    palette: "pixel",
  });
  pixelCanvas.style.flexShrink = "0";
  pixelCanvas.addEventListener("cell-click", onPixelCellClick as EventListener);
  pixelCanvas.addEventListener("cell-hover", onPixelCellHover as EventListener);
  pixelCanvasRef.value.appendChild(pixelCanvas);
  // Load the current symbol's glyph so the editor immediately reflects the
  // committed glyph atlas (same bitmaps as the Glyphs tab).
  loadGlyphFromFont();
}

function paintPixelAt(x: number, y: number) {
  if (!pixelEditor) return;
  if (pixelTool.value === "eyedropper") {
    pixelColor.value = pixelEditor.buffer[y * pixelEditor.width + x] ?? 0;
    pixelTool.value = "pencil";
    renderPixelBuffer();
    return;
  }
  if (pixelTool.value === "fill") {
    pixelEditor.floodFill(x, y, pixelColor.value);
  } else if (pixelTool.value === "erase") {
    pixelEditor.erase(x, y);
  } else {
    pixelEditor.paint(x, y, pixelColor.value);
  }
  renderPixelBuffer();
}

function onPixelCellClick(e: CustomEvent) {
  const { col, row } = e.detail || {};
  if (typeof col === "number" && typeof row === "number")
    paintPixelAt(col, row);
}

function onPixelCellHover(e: CustomEvent) {
  if (!pixelIsDragging.value) return;
  const { col, row } = e.detail || {};
  if (typeof col === "number" && typeof row === "number")
    paintPixelAt(col, row);
}

function fillPixelEditor() {
  pixelEditor?.fill(pixelColor.value);
  renderPixelBuffer();
}

function clearPixelEditor() {
  pixelEditor?.clear();
  renderPixelBuffer();
}

function undoPixel() {
  pixelEditor?.undo();
  renderPixelBuffer();
}

function redoPixel() {
  pixelEditor?.redo();
  renderPixelBuffer();
}

function exportPixelData() {
  if (!pixelEditor) return;
  const { w, h } = pixelCell.value;
  const data = {
    format: "ucore-pixel-v1",
    width: w,
    height: h,
    pixels: Array.from(pixelEditor.buffer),
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `pixel-${w}x${h}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/* ─── Grid Tab (Layer Editor) ─────────────────────────────────────── */

function initGridEditor() {
  destroyGridEditor();
  if (!layerViewportRef.value) return;

  layerCanvas = createGridUICanvas({
    cols: LAYER_COLS,
    rows: LAYER_ROWS,
    font: editorFont.value,
    cellSize: 24,
  });
  layerCanvas.setAttribute("gridlines", "");
  layerCanvas.style.flexShrink = "0";
  layerCanvas.addEventListener("cell-click", onLayerCellClick as EventListener);
  layerViewportRef.value.appendChild(layerCanvas);

  loadGridEditorDemo();
  renderLayerBuffer();
}

function loadGridEditorDemo() {
  layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS);
  layerBuffer = writeString(layerBuffer, 1, 0, "uCode Grid", 7, 5, true);
  layerBuffer = fill(layerBuffer, 0, 1, LAYER_COLS, LAYER_ROWS - 2, ".", 4, 0);
  const layers = [
    { label: "Terrain", color: 2, y: 3, fillChar: "#" },
    { label: "Structures", color: 3, y: 8, fillChar: "&" },
    { label: "Units", color: 1, y: 13, fillChar: "@" },
  ];
  for (const lyr of layers) {
    layerBuffer = fill(
      layerBuffer,
      4,
      lyr.y,
      30,
      3,
      lyr.fillChar,
      lyr.color,
      0,
    );
    layerBuffer = writeString(
      layerBuffer,
      4,
      lyr.y + 1,
      `  ~ ${lyr.label} ~  `,
      7,
      lyr.color,
      true,
    );
  }
}

/** Load a connected-cell seed (wordmark / panel frame) into the layer buffer. */
function loadSeedDemo(name: "wordmark" | "frame") {
  const seed: GridSeed =
    name === "wordmark"
      ? (uCodeWordmarkSeed as GridSeed)
      : (panelFrameSeed as GridSeed);
  layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS);
  const originCol = Math.max(0, Math.floor((LAYER_COLS - seed.cols) / 2));
  const originRow = Math.max(1, Math.floor((LAYER_ROWS - seed.rows) / 2));
  placeSeed(layerBuffer, seed, originCol, originRow);
  layerCursorCol.value = 0;
  layerCursorRow.value = 0;
  renderLayerBuffer();
}

function destroyGridEditor() {
  layerCanvas?.remove();
  layerCanvas = null;
}

function renderLayerBuffer() {
  if (!layerCanvas) return;
  const buf = cloneBuffer(layerBuffer);
  // Highlight cursor cell
  const cr = layerCursorRow.value;
  const cc = layerCursorCol.value;
  if (cr >= 0 && cr < LAYER_ROWS && cc >= 0 && cc < LAYER_COLS) {
    const cell = buf[cr][cc];
    buf[cr][cc] = {
      ...cell,
      fg: cell.bg,
      bg: cell.fg === cell.bg ? (cell.fg === 0 ? 7 : 0) : cell.fg,
    };
  }
  layerCanvas.setBuffer(buf);
}

/* ─── Grid Tab — Interaction ──────────────────────────────────────── */

function onLayerKeydown(e: KeyboardEvent) {
  if (activeTab.value !== "grid") return;
  switch (e.key) {
    case "ArrowLeft":
      e.preventDefault();
      layerCursorCol.value = Math.max(0, layerCursorCol.value - 1);
      renderLayerBuffer();
      break;
    case "ArrowRight":
      e.preventDefault();
      layerCursorCol.value = Math.min(LAYER_COLS - 1, layerCursorCol.value + 1);
      renderLayerBuffer();
      break;
    case "ArrowUp":
      e.preventDefault();
      layerCursorRow.value = Math.max(0, layerCursorRow.value - 1);
      renderLayerBuffer();
      break;
    case "ArrowDown":
      e.preventDefault();
      layerCursorRow.value = Math.min(LAYER_ROWS - 1, layerCursorRow.value + 1);
      renderLayerBuffer();
      break;
    case "Tab":
      e.preventDefault();
      {
        const tools = TOOLS.map((t) => t.id);
        const idx = tools.indexOf(currentTool.value);
        currentTool.value = tools[
          (idx + 1) % tools.length
        ] as typeof currentTool.value;
      }
      break;
    default:
      if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        const lx = layerCursorCol.value;
        const ly = layerCursorRow.value;
        if (lx >= 0 && lx < LAYER_COLS && ly >= 0 && ly < LAYER_ROWS) {
          layerBuffer[ly][lx] = {
            char: e.key,
            fg: selectedFg.value,
            bg: selectedBg.value,
          };
          renderLayerBuffer();
        }
      }
      break;
  }
}

function onLayerMouseDown(e: MouseEvent) {
  layerIsDragging = true;
  const onMove = (ev: MouseEvent) => {
    if (!layerIsDragging || !layerCanvas) return;
    const rect = layerCanvas.getBoundingClientRect();
    const localX = ev.clientX - rect.left;
    const localY = ev.clientY - rect.top;
    const cssW = parseFloat(layerCanvas.style.width || "0");
    const cssH = parseFloat(layerCanvas.style.height || "0");
    if (!cssW || !cssH) return;
    const cellW = cssW / LAYER_COLS;
    const cellH = cssH / LAYER_ROWS;
    const col = Math.floor(localX / cellW);
    const row = Math.floor(localY / cellH);
    if (col >= 0 && col < LAYER_COLS && row >= 0 && row < LAYER_ROWS) {
      layerCursorCol.value = col;
      layerCursorRow.value = row;
      doLayerPaint();
    }
  };
  const onUp = () => {
    layerIsDragging = false;
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
  };
  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}

function doLayerPaint() {
  const lx = layerCursorCol.value;
  const ly = layerCursorRow.value;
  if (lx < 0 || lx >= LAYER_COLS || ly < 0 || ly >= LAYER_ROWS) return;
  const tool = currentTool.value;
  if (tool === "eyedropper") {
    const cell = layerBuffer[ly][lx];
    selectedFg.value = cell.fg;
    selectedBg.value = cell.bg;
    selectedChar.value = cell.char;
    currentTool.value = "pencil";
    return;
  }
  if (tool === "erase") {
    layerBuffer[ly][lx] = { char: " ", fg: 7, bg: 0 };
    renderLayerBuffer();
    return;
  }
  layerBuffer[ly][lx] = {
    char: selectedChar.value,
    fg: selectedFg.value,
    bg: selectedBg.value,
  };
  renderLayerBuffer();
}

function onLayerCellClick(e: CustomEvent) {
  const { col, row } = e.detail;
  layerCursorCol.value = col;
  layerCursorRow.value = row;
  if (col < 0 || col >= LAYER_COLS || row < 0 || row >= LAYER_ROWS) return;
  const tool = currentTool.value;
  if (tool === "eyedropper") {
    const cell = layerBuffer[row][col];
    selectedFg.value = cell.fg;
    selectedBg.value = cell.bg;
    selectedChar.value = cell.char;
    currentTool.value = "pencil";
    renderLayerBuffer();
    return;
  }
  if (tool === "erase") {
    layerBuffer[row][col] = { char: " ", fg: 7, bg: 0 };
    renderLayerBuffer();
    return;
  }
  if (tool === "fill") {
    floodFill(col, row, selectedFg.value, selectedBg.value, selectedChar.value);
    renderLayerBuffer();
    return;
  }
  layerBuffer[row][col] = {
    char: selectedChar.value,
    fg: selectedFg.value,
    bg: selectedBg.value,
  };
  renderLayerBuffer();
}

function floodFill(
  startX: number,
  startY: number,
  fg: number,
  bg: number,
  char: string,
) {
  const targetChar = layerBuffer[startY][startX].char;
  const targetFg = layerBuffer[startY][startX].fg;
  if (targetChar === char && targetFg === fg) return;
  const stack: [number, number][] = [[startX, startY]];
  const visited = new Set<number>();
  while (stack.length > 0) {
    const [cx, cy] = stack.pop()!;
    const key = cy * LAYER_COLS + cx;
    if (visited.has(key)) continue;
    visited.add(key);
    if (cx < 0 || cx >= LAYER_COLS || cy < 0 || cy >= LAYER_ROWS) continue;
    const cell = layerBuffer[cy][cx];
    if (cell.char !== targetChar || cell.fg !== targetFg) continue;
    layerBuffer[cy][cx] = { char, fg, bg };
    stack.push([cx - 1, cy], [cx + 1, cy], [cx, cy - 1], [cx, cy + 1]);
  }
}

function clearLayer() {
  layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS);
  renderLayerBuffer();
}
function fillLayer() {
  for (let r = 0; r < LAYER_ROWS; r++)
    for (let c = 0; c < LAYER_COLS; c++)
      layerBuffer[r][c] = {
        char: selectedChar.value,
        fg: selectedFg.value,
        bg: selectedBg.value,
      };
  renderLayerBuffer();
}

function onPresetChange(name: string) {
  const p = GRID_PRESETS.find((x) => x.name === name);
  if (!p) return;
  const oldBuffer = cloneBuffer(layerBuffer);
  LAYER_COLS = p.cols;
  LAYER_ROWS = p.rows;
  layerCols.value = p.cols;
  layerRows.value = p.rows;
  if (activeTab.value === "grid" || activeTab.value === "layer") {
    layerBuffer = scaleBuffer(oldBuffer, p.cols, p.rows);
    layerCursorCol.value = 0;
    layerCursorRow.value = 0;
    destroyGridEditor();
    nextTick(() => initGridEditor());
  } else {
    const cfg = tabConfigs[activeTab.value];
    if (cfg) {
      cfg.cols = p.cols;
      cfg.rows = p.rows;
    }
    const tab = activeTab.value;
    const old = canvasCache.get(tab);
    if (old) {
      old.remove();
      canvasCache.delete(tab);
    }
    nextTick(() => initGrid(tab));
  }
}

/* ─── Layer resize ──────────────────────────────────────────────── */
function onLayerResize() {
  const newCols = Math.max(4, Math.min(256, layerCols.value));
  const newRows = Math.max(4, Math.min(256, layerRows.value));
  if (newCols === LAYER_COLS && newRows === LAYER_ROWS) return;
  const oldBuffer = cloneBuffer(layerBuffer);
  LAYER_COLS = newCols;
  LAYER_ROWS = newRows;
  layerCols.value = newCols;
  layerRows.value = newRows;
  layerBuffer = scaleBuffer(oldBuffer, newCols, newRows);
  layerCursorCol.value = Math.min(layerCursorCol.value, newCols - 1);
  layerCursorRow.value = Math.min(layerCursorRow.value, newRows - 1);
  destroyGridEditor();
  nextTick(() => initGridEditor());
}

/* ─── Lifecycle ───────────────────────────────────────────────────── */
onMounted(() => {
  if (activeTab.value === "pixel") initPixelEditor();
  else if (activeTab.value === "grid") initGridEditor();
  else if (gridContainer.value) initGrid(activeTab.value);
  startTeletextClock();
});

onUnmounted(() => {
  stopTeletextClock();
  disconnectTerminalRuntime();
  canvasCache.forEach((el) => el.remove());
  canvasCache.clear();
  activeCanvas = null;
  layerCanvas?.remove();
  pixelCanvas?.remove();
  layerCanvas = null;
  pixelCanvas = null;
});

/* ─── Single-Canvas Tab Management ────────────────────────────────── */
function initGrid(tabId: string) {
  if (!gridContainer.value) return;
  const cfg = tabConfigs[tabId];
  const font = cfg.font;
  if (activeCanvas) activeCanvas.style.display = "none";
  let el = canvasCache.get(tabId);
  if (!el) {
    el = createGridUICanvas({
      cols: cfg.cols,
      rows: cfg.rows,
      font,
      cellSize: cfg.cellSize,
      squareCells: cfg.square,
      fitExact: cfg.fitExact,
    });
    if (cfg.charWidth) el.setAttribute("char-width", String(cfg.charWidth));
    el.style.flexShrink = "0";
    gridContainer.value.appendChild(el);
    canvasCache.set(tabId, el);
    activeCanvas = el;
    loadTabContent(tabId);
    const canvas = el;
    nextTick(() => canvas.refit());
  } else {
    el.setAttribute("cols", String(cfg.cols));
    el.setAttribute("rows", String(cfg.rows));
    el.setAttribute("font", font);
    if (cfg.square) el.setAttribute("square-cells", "");
    else el.removeAttribute("square-cells");
    if (cfg.fitExact) el.setAttribute("fit-exact", "");
    else el.removeAttribute("fit-exact");
    if (cfg.charWidth) el.setAttribute("char-width", String(cfg.charWidth));
    else el.removeAttribute("char-width");
    el.style.display = "";
    void el.offsetHeight;
    if (!gridContainer.value.contains(el)) gridContainer.value.appendChild(el);
    activeCanvas = el;
    loadTabContent(tabId);
    const canvas = el;
    nextTick(() => canvas.refit());
  }
}

watch(activeTab, (newTab) => {
  if (newTab !== "terminal") disconnectTerminalRuntime();
  terminalCursorX = 0;
  terminalCursorY = 0;
  // Tear down previous grid editor
  layerCanvas?.remove();
  layerCanvas = null;
  // Tear down pixel editor if leaving
  if (newTab !== "pixel") {
    pixelCanvas?.remove();
    pixelCanvas = null;
  }
  nextTick(() => {
    if (newTab === "pixel") initPixelEditor();
    else if (newTab === "grid") initGridEditor();
    else if (gridContainer.value) initGrid(newTab);
  });
});

function loadTabContent(tabId?: string) {
  const id = tabId || activeTab.value;
  switch (id) {
    case "terminal":
      loadTerminalRuntime();
      break;
    case "teletext":
      renderTeletextPage();
      if (!vaultLoaded.value) void loadVaultContent();
      break;
    case "layer":
      loadLayerDemo();
      break;
    case "glyphs":
      loadGlyphInspector();
      break;
  }
}

function reloadGrid() {
  if (activeTab.value === "pixel") {
    initPixelEditor();
  } else if (activeTab.value === "grid" || activeTab.value === "layer") {
    layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS);
    renderLayerBuffer();
  } else if (activeTab.value === "teletext") {
    vaultLoaded.value = false;
    vaultDocCache.clear();
    void loadVaultContent();
  } else loadTabContent();
}

/* ─── Export/Import ────────────────────────────────────────────────── */
function getExportBuffer(): GridBuffer {
  if (activeTab.value === "pixel") return pixelBuffer;
  if (activeTab.value === "grid" || activeTab.value === "layer")
    return layerBuffer;
  if (activeCanvas) return activeCanvas.buffer;
  return createBuffer(40, 25);
}

function exportGrid() {
  const buf = getExportBuffer();
  const cols = buf.length > 0 ? buf[0].length : 40;
  const rows = buf.length;
  const data = {
    format: "ucode-grid-v1",
    cols,
    rows,
    cells: buf.map((row) => row.map((c) => ({ c: c.char, f: c.fg, b: c.bg }))),
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `ucode-grid-${cols}x${rows}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function triggerImport() {
  importInputRef.value?.click();
}

function onImportFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result as string);
      if (data.format !== "ucode-grid-v1" || !data.cells) return;
      const isPixel = activeTab.value === "pixel";
      const isGridLayer =
        activeTab.value === "grid" || activeTab.value === "layer";
      const target = isPixel
        ? pixelBuffer
        : isGridLayer
          ? layerBuffer
          : activeCanvas?.buffer || null;
      if (!target) return;
      const cols = Math.min(data.cols, target[0]?.length || 40);
      const rows = Math.min(data.rows, target.length);
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const src = data.cells[r]?.[c];
          if (src)
            target[r][c] = {
              char: src.c || " ",
              fg: src.f ?? 7,
              bg: src.b ?? 0,
            };
        }
      }
      if (isPixel) {
        pixelEditor = new PixelEditor(gridBufferToPixelBuffer(pixelBuffer));
        renderPixelBuffer();
      } else if (isGridLayer) {
        layerBuffer = cloneBuffer(layerBuffer);
        renderLayerBuffer();
      } else if (activeCanvas) {
        activeCanvas.setBuffer(cloneBuffer(target));
      }
    } catch (err) {
      console.error("Import failed:", err);
    }
  };
  reader.readAsText(file);
  (e.target as HTMLInputElement).value = "";
}

/* ─── Teletext Tab ────────────────────────────────────────────────── */
const teletextPage = ref(100);
const teletextHistory: number[] = [];
let teletextDigitBuffer = "";
let teletextClockTimer: number | null = null;

// Note: TELETEXT_FASTEXT, VaultDoc, VaultLibrary, PUBLIC_LIBRARY_DEFS,
// DOCS_PER_LIST_PAGE, MAX_DOCS_PER_LIBRARY, DOC_PAGE_OFFSET, DOC_SCREEN_LINES
// are imported from @/grid-core/teletext.

const vaultLibraries = ref<VaultLibrary[]>([]);
const vaultLoaded = ref(false);
const vaultError = ref<string | null>(null);
/** path → full file content, cached after first read. */
const vaultDocCache = new Map<string, string>();

function docTitle(doc: VaultDoc): string {
  const base = doc.filename.replace(/\.[^.]+$/, "");
  const title = base.replace(/[-_]+/g, " ").trim();
  return title || doc.filename;
}

/** Library that owns a given page number (by hundred-block). */
function libraryForPage(page: number): VaultLibrary | undefined {
  const base = Math.floor(page / 100) * 100;
  return vaultLibraries.value.find((lib) => lib.page === base);
}

/** Rotating subpage index (0-based) within the current page. */
const teletextSubpage = ref(0);
/** Tick counter for subpage auto-rotation. */
let teletextTick = 0;

const DOC_SCREEN_LINES = 15;

/** Split a document's wrapped body into screens of ~15 lines. */
function docScreens(doc: VaultDoc): string[][] {
  const body = vaultDocCache.get(doc.path) ?? doc.preview;
  const wrapped = wrapText(body, 38);
  const screens: string[][] = [];
  for (let i = 0; i < wrapped.length; i += DOC_SCREEN_LINES) {
    screens.push(wrapped.slice(i, i + DOC_SCREEN_LINES));
  }
  return screens.length > 0 ? screens : [[]];
}

/** Fetch one library source's document list. */
async function fetchVaultSource(source: string): Promise<VaultDoc[]> {
  const res = await fetch(
    `${UCORE_API}/api/library/search?q=*&source=${encodeURIComponent(source)}&limit=400`,
  );
  if (!res.ok) throw new Error(`HTTP ${res.status} (${source})`);
  const data = await res.json();
  const raw: unknown[] = Array.isArray(data.results) ? data.results : [];
  return raw.map((d) => {
    const item = d as Record<string, unknown>;
    const tags = Array.isArray(item.tags) ? (item.tags as string[]) : [];
    return {
      path: String(item.path ?? ""),
      filename: String(item.filename ?? ""),
      binder: item.binder ? String(item.binder) : null,
      tags,
      preview: String(item.preview ?? ""),
      extension: String(item.extension ?? ""),
    };
  });
}

/** Fetch the published vault index and group docs into libraries. */
async function loadVaultContent(): Promise<void> {
  try {
    const sources = new Set(PUBLIC_LIBRARY_DEFS.map((def) => def.source));
    const fetched = new Map<string, VaultDoc[]>();
    await Promise.all(
      Array.from(sources).map(async (source) => {
        fetched.set(source, await fetchVaultSource(source));
      }),
    );
    vaultLibraries.value = PUBLIC_LIBRARY_DEFS.map((def) => {
      const all = fetched.get(def.source) ?? [];
      const tag = def.tag;
      const docs = (tag ? all.filter((d) => d.tags.includes(tag)) : all)
        .filter((d) => d.extension === "md" || d.extension === "markdown")
        .slice(0, MAX_DOCS_PER_LIBRARY);
      return { ...def, docs };
    });
    vaultError.value = null;
  } catch (e) {
    vaultError.value = e instanceof Error ? e.message : String(e);
  } finally {
    vaultLoaded.value = true;
  }
  renderTeletextPage();
}

/** Ceefax-style clock: `Mon 16 Aug 21:00/12`. */
function ceefaxClock(): string {
  const d = new Date();
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const dd = String(d.getDate()).padStart(2, " ");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${days[d.getDay()]} ${dd} ${months[d.getMonth()]} ${hh}:${mm}/${ss}`;
}

/** Write a double-height string: top half in row y, bottom half in row y+1. */
function writeDoubleHeight(
  buf: GridBuffer,
  x: number,
  y: number,
  text: string,
  fg: number,
  bg: number,
): void {
  const cols = buf[0]?.length ?? 0;
  for (let i = 0; i < text.length && x + i < cols; i++) {
    if (y >= 0 && y < buf.length)
      buf[y][x + i] = { char: text[i], fg, bg, dh: "top" };
    if (y + 1 >= 0 && y + 1 < buf.length)
      buf[y + 1][x + i] = { char: text[i], fg, bg, dh: "bottom" };
  }
}

/** Write a full-width horizontal rule of mosaic blocks (▀ upper-half). */
function writeMosaicRule(buf: GridBuffer, y: number, color: number): void {
  const cols = buf[0]?.length ?? 0;
  if (y < 0 || y >= buf.length) return;
  for (let c = 0; c < cols; c++) {
    buf[y][c] = { char: "\u2580", fg: color, bg: 0, mosaic: true };
  }
}

/** Write a full-width separated-graphics bar (top-row sextant blocks). */
function writeSeparatedBar(buf: GridBuffer, y: number, color: number): void {
  const cols = buf[0]?.length ?? 0;
  if (y < 0 || y >= buf.length) return;
  for (let c = 0; c < cols; c++) {
    buf[y][c] = { char: patternToChar(3), fg: color, bg: 0, mosaic: true };
  }
}

/** Draw a boxed double-height title using 2×3 sextant edges. */
function writeBoxedDoubleHeightTitle(
  buf: GridBuffer,
  title: string,
  colour: number,
): void {
  const c = buf[0]?.length ?? 0;
  const t = title.slice(0, 18);
  const innerW = Math.max(t.length + 2, 4); // title + left/right border
  const x = Math.max(0, Math.floor((c - innerW) / 2));
  const set = (row: number, col: number, pattern: number): void => {
    if (row >= 0 && row < buf.length && col >= 0 && col < c) {
      buf[row][col] = {
        char: patternToChar(pattern),
        fg: colour,
        bg: 0,
        mosaic: true,
      };
    }
  };
  // Top border + corners.
  set(2, x, 23);
  for (let i = 1; i < innerW - 1; i++) set(2, x + i, 3);
  set(2, x + innerW - 1, 43);
  // Left/right walls (rows 3-4).
  set(3, x, 21);
  set(4, x, 21);
  set(3, x + innerW - 1, 42);
  set(4, x + innerW - 1, 42);
  // Bottom border + corners.
  set(5, x, 53);
  for (let i = 1; i < innerW - 1; i++) set(5, x + i, 48);
  set(5, x + innerW - 1, 58);
  // Double-height title inside (yellow).
  for (let i = 0; i < t.length; i++) {
    const col = x + 1 + i;
    buf[3][col] = { char: t[i], fg: 3, bg: 0, dh: "top" };
    buf[4][col] = { char: t[i], fg: 3, bg: 0, dh: "bottom" };
  }
}

interface TeletextPage {
  title: string;
  lines: string[];
  /** Show a flashing NEWFLASH banner below the header. */
  flash?: boolean;
  /** Section accent colour (palette index) for the title box + bar. */
  colour?: number;
  /** Number of rotating subpages (multi-screen content); 1 = single. */
  subpages?: number;
}

/** Wrap prose to a fixed column width. */
function wrapText(text: string, width: number): string[] {
  const out: string[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.replace(/\s+/g, " ").trim();
    if (!line) {
      out.push("");
      continue;
    }
    let rest = line;
    while (rest.length > width) {
      const cut = rest.lastIndexOf(" ", width);
      const at = cut < 1 ? width : cut;
      out.push(rest.slice(0, at).trimEnd());
      rest = rest.slice(at).trimStart();
    }
    if (rest) out.push(rest);
  }
  return out;
}

/** Main index — libraries from the public vault + static pages. */
function mainIndexPage(): TeletextPage {
  const libs = vaultLibraries.value;
  if (!vaultLoaded.value) {
    return {
      title: "uCode",
      colour: 6,
      lines: ["", "  Loading published content...", "  (vault index)"],
    };
  }
  if (vaultError.value) {
    return {
      title: "uCode",
      colour: 1,
      lines: [
        "",
        `  Vault unavailable: ${vaultError.value.slice(0, 30)}`,
        "",
        "  NEWS ............... 101",
        "  HELP ............... 888",
        "  INDEX .............. 199",
      ],
    };
  }
  const lines: string[] = [
    "  uCODE TELETEXT READER",
    "  Published vault content",
    "",
  ];
  for (const lib of libs) {
    const count = lib.docs.length;
    lines.push(
      `  ${lib.label.toUpperCase()} ${"".padEnd(Math.max(1, 18 - lib.label.length), ".")} ${lib.page}  (${count})`,
    );
  }
  lines.push("");
  lines.push("  NEWS ............... 101");
  lines.push("  HELP ............... 888");
  lines.push("  INDEX .............. 199");
  lines.push("");
  lines.push("  Type 0-9 for page number");
  lines.push("  F1-F4 fastext shortcuts");
  return { title: "uCode", colour: 6, lines };
}

/** A library's doc list (paginated). */
function docListPage(lib: VaultLibrary, listIdx: number): TeletextPage {
  const docs = lib.docs;
  if (!vaultLoaded.value) {
    return {
      title: lib.label,
      colour: lib.colour,
      lines: ["", "  Loading published content..."],
    };
  }
  const start = listIdx * DOCS_PER_LIST_PAGE;
  const pageDocs = docs.slice(start, start + DOCS_PER_LIST_PAGE);
  const lines: string[] = [
    `  ${lib.label.toUpperCase()} (${docs.length} docs)`,
    "",
  ];
  if (pageDocs.length === 0) {
    lines.push("  No documents indexed yet.");
    lines.push("  Add files under the Public");
    lines.push("  vault and rebuild the index.");
  } else {
    pageDocs.forEach((doc, i) => {
      const readPage = lib.page + DOC_PAGE_OFFSET + start + i;
      lines.push(
        `  ${String(readPage).padStart(3, " ")}  ${docTitle(doc).slice(0, 29)}`,
      );
      lines.push(`       ${doc.preview.slice(0, 32)}`);
    });
  }
  const nextStart = start + DOCS_PER_LIST_PAGE;
  if (nextStart < docs.length) {
    lines.push("");
    lines.push(`  MORE ............... ${lib.page + 1 + listIdx + 1}`);
  }
  return { title: lib.label, colour: lib.colour, lines };
}

/** A single document rendered as a Ceefax page (rotating subpages). */
function docContentPage(lib: VaultLibrary, docIdx: number): TeletextPage {
  const doc = lib.docs[docIdx];
  if (!doc) {
    return {
      title: "P??",
      colour: lib.colour,
      lines: ["  Document not found."],
    };
  }
  const screens = docScreens(doc);
  const total = screens.length;
  const screen = Math.min(teletextSubpage.value, total - 1);
  const lines: string[] = [
    `  ${docTitle(doc).slice(0, 36)}`,
    `  ${doc.filename.slice(0, 36)}`,
    "",
  ];
  for (const line of screens[screen]) lines.push(`  ${line.slice(0, 38)}`);
  lines.push("");
  lines.push(`  Back: ${lib.page}  ·  ESC to go back`);
  return {
    title: docTitle(doc).slice(0, 14),
    colour: lib.colour,
    lines,
    subpages: total,
  };
}

function newsPage(): TeletextPage {
  return {
    title: "NEWS",
    flash: true,
    colour: 2,
    lines: [
      "  Teletext reader wired to the",
      "  public vault index.",
      "",
      "  DOCUMENTATION ....... 200",
      "  GLOBAL KNOWLEDGE .... 300",
      "  LEARNING ............ 400",
      "",
      "  Type a 3-digit page number",
      "  to browse published content.",
    ],
  };
}

function subIndexPage(): TeletextPage {
  return {
    title: "INDEX",
    colour: 3,
    lines: [
      "  100  Main Index",
      "  101  News Headlines",
      "  200  Documentation",
      "  300  Global Knowledge",
      "  400  Learning",
      "  888  Help and About",
    ],
  };
}

function helpPage(): TeletextPage {
  return {
    title: "HELP",
    colour: 4,
    lines: [
      "  Number keys 0-9 navigate",
      "  F1-F4 fastext shortcuts",
      "  ESC or B goes back",
      "",
      "  uCode GridCore teletext",
      "  reader with G0 rendering",
      "",
      "  Content from the public",
      "  vault (published docs).",
    ],
  };
}

function teletextContent(page: number): TeletextPage {
  const lib = libraryForPage(page);
  if (lib) {
    const docIdx = page - lib.page - DOC_PAGE_OFFSET;
    if (docIdx >= 0 && docIdx < lib.docs.length) {
      return docContentPage(lib, docIdx);
    }
    const listIdx = page - lib.page - 1;
    if (listIdx >= 0) return docListPage(lib, listIdx);
    return docListPage(lib, 0);
  }

  switch (page) {
    case 100:
      return mainIndexPage();
    case 101:
      return newsPage();
    case 199:
      return subIndexPage();
    case 888:
      return helpPage();
    default:
      return {
        title: `P${page}`,
        colour: 6,
        lines: ["  Press 100 for Main Index", "  Press 199 for Full Index"],
      };
  }
}

function renderTeletextPage() {
  if (!activeCanvas) return;
  const cfg = tabConfigs.teletext;
  const c = cfg.cols;
  const r = cfg.rows;
  const page = teletextPage.value;
  const clock = ceefaxClock();

  let buf = createBuffer(c, r);
  const content = teletextContent(page);

  // Row 0 — header bar (blue background, white bold text).
  buf = fill(buf, 0, 0, c, 1, " ", 7, 4);
  buf = writeString(buf, 1, 0, `P${page} CEEFAX ${page}`, 7, 4, true);
  buf = writeString(buf, c - clock.length - 1, 0, clock, 7, 4);

  // Row 1 — flashing NEWFLASH banner (red bg, white text), or blank.
  if (content.flash) {
    buf = fill(buf, 0, 1, c, 1, " ", 7, 1);
    buf = writeString(buf, 1, 1, "NEWFLASH", 7, 1, true);
    for (let x = 0; x < c; x++) buf[1][x].blink = true;
  }

  // Row 1 — separated-graphics colour bar under the header (unless flashing).
  if (!content.flash) {
    writeSeparatedBar(buf, 1, content.colour ?? 6);
  }

  // Rows 2–5 — boxed double-height title (sextant edges).
  writeBoxedDoubleHeightTitle(buf, content.title, content.colour ?? 6);

  // Rows 6.. — body lines.
  const lines = content.lines;
  for (let i = 0; i < lines.length && 6 + i < r - 2; i++) {
    buf = writeString(buf, 1, 6 + i, lines[i], 7, 0);
  }

  // Row r-2 — fastext (coloured navigation links).
  const seg = Math.floor(c / TELETEXT_FASTEXT.length);
  TELETEXT_FASTEXT.forEach((ft, i) => {
    const label = ` ${ft.label} `.padEnd(seg).slice(0, seg);
    buf = writeString(buf, i * seg, r - 2, label, 7, ft.color);
  });

  // Row r-1 — status bar (blue): page, channel, subpage, clock.
  const subpages = content.subpages ?? 1;
  const subLabel =
    subpages > 1 ? `${teletextSubpage.value + 1}/${subpages}` : `P${page}`;
  buf = fill(buf, 0, r - 1, c, 1, " ", 7, 4);
  buf = writeString(buf, 0, r - 1, `P${page}`, 7, 4);
  buf = writeString(buf, 6, r - 1, "BBC1", 7, 4);
  buf = writeString(buf, 12, r - 1, subLabel, 7, 4);
  buf = writeString(buf, c - clock.length - 1, r - 1, clock, 7, 4);

  activeCanvas.setBuffer(buf);
}

async function teletextNavigate(page: number) {
  if (page < 100 || page > 899) return;
  teletextHistory.push(teletextPage.value);
  teletextPage.value = page;
  teletextSubpage.value = 0;
  teletextTick = 0;
  renderTeletextPage();
  await fetchDocContentForPage(page);
}

async function teletextGoBack() {
  const prev = teletextHistory.pop();
  if (prev === undefined) return;
  teletextPage.value = prev;
  teletextSubpage.value = 0;
  teletextTick = 0;
  renderTeletextPage();
  await fetchDocContentForPage(prev);
}

/** Fetch a doc-content page's full file body (cached, once per path). */
async function fetchDocContentForPage(page: number): Promise<void> {
  const lib = libraryForPage(page);
  if (!lib) return;
  const docIdx = page - lib.page - DOC_PAGE_OFFSET;
  if (docIdx < 0 || docIdx >= lib.docs.length) return;
  const doc = lib.docs[docIdx];
  if (vaultDocCache.has(doc.path)) return;
  try {
    const res = await fetch(
      `${UCORE_API}/api/library/file?path=${encodeURIComponent(doc.path)}`,
    );
    if (!res.ok) return;
    const data = await res.json();
    if (typeof data.content === "string") {
      vaultDocCache.set(doc.path, data.content);
      if (teletextPage.value === page) renderTeletextPage();
    }
  } catch {
    /* keep the preview */
  }
}

function teletextFastext(index: number) {
  const ft = TELETEXT_FASTEXT[index];
  if (ft) teletextNavigate(ft.page);
}

function startTeletextClock() {
  stopTeletextClock();
  teletextClockTimer = window.setInterval(() => {
    if (activeTab.value !== "teletext") return;
    teletextTick++;
    // Auto-rotate subpages every ~4s for multi-screen docs (Ceefax-style).
    if (teletextTick % 4 === 0) {
      const lib = libraryForPage(teletextPage.value);
      if (lib) {
        const docIdx = teletextPage.value - lib.page - DOC_PAGE_OFFSET;
        if (docIdx >= 0 && docIdx < lib.docs.length) {
          const total = docScreens(lib.docs[docIdx]).length;
          if (total > 1) {
            teletextSubpage.value = (teletextSubpage.value + 1) % total;
          }
        }
      }
    }
    renderTeletextPage();
  }, 1000);
}

function stopTeletextClock() {
  if (teletextClockTimer !== null) {
    clearInterval(teletextClockTimer);
    teletextClockTimer = null;
  }
}

function handleTeletextKeydown(event: KeyboardEvent) {
  if (event.key >= "0" && event.key <= "9") {
    event.preventDefault();
    teletextDigitBuffer += event.key;
    if (teletextDigitBuffer.length >= 3) {
      const page = parseInt(teletextDigitBuffer, 10);
      teletextDigitBuffer = "";
      teletextNavigate(page);
    }
  } else if (event.key === "F1") {
    event.preventDefault();
    teletextFastext(0);
  } else if (event.key === "F2") {
    event.preventDefault();
    teletextFastext(1);
  } else if (event.key === "F3") {
    event.preventDefault();
    teletextFastext(2);
  } else if (event.key === "F4") {
    event.preventDefault();
    teletextFastext(3);
  } else if (event.key === "Escape" || event.key === "b" || event.key === "B") {
    event.preventDefault();
    teletextGoBack();
  } else if (event.key === "." || event.key === "n" || event.key === "N") {
    // Next subpage (manual advance).
    event.preventDefault();
    teletextStepSubpage(1);
  } else if (event.key === "," || event.key === "p" || event.key === "P") {
    // Previous subpage.
    event.preventDefault();
    teletextStepSubpage(-1);
  }
}

/** Step the current page's subpage (clamped), for multi-screen docs. */
function teletextStepSubpage(delta: number): void {
  const lib = libraryForPage(teletextPage.value);
  if (!lib) return;
  const docIdx = teletextPage.value - lib.page - DOC_PAGE_OFFSET;
  if (docIdx < 0 || docIdx >= lib.docs.length) return;
  const total = docScreens(lib.docs[docIdx]).length;
  if (total <= 1) return;
  teletextSubpage.value = (teletextSubpage.value + delta + total) % total;
  teletextTick = 0;
  renderTeletextPage();
}

function onSharedKeydown(event: KeyboardEvent) {
  if (activeTab.value === "teletext") {
    handleTeletextKeydown(event);
  } else if (activeTab.value === "terminal") {
    onTerminalKeydown(event);
  }
}

/** Keep keyboard focus on the grid viewport when the user clicks the canvas
 *  (the canvas lives inside a shadow root, so a plain click does not focus
 *  the focusable viewport host — this made Terminal input appear dead). */
function focusGridContainer() {
  gridContainer.value?.focus();
}

/* ─── Terminal Tab ────────────────────────────────────────────────── */
function terminalWebSocketUrl() {
  const url = new URL("/api/terminal/runtime/ws", UCORE_API);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

/** Block cursor visibility + the initial blink-then-solid behaviour. */
let terminalCursorVisible = true;
let terminalCursorBlinkTimer: number | null = null;

function ensureTerminalBuffer(): GridBuffer {
  if (
    !terminalBuffer ||
    terminalBuffer.length !== TERMINAL_ROWS ||
    terminalBuffer[0]?.length !== TERMINAL_COLS
  ) {
    terminalBuffer = createBuffer(TERMINAL_COLS, TERMINAL_ROWS);
  }
  return terminalBuffer;
}

/** Render the 40×25 content inside a 42×27 grid with a 1-cell black margin,
 *  plus the inverted block cursor. */
function terminalRender() {
  if (!activeCanvas) return;
  const cfg = tabConfigs.terminal; // 42×27
  const content = ensureTerminalBuffer(); // 40×25

  const grid = createBuffer(cfg.cols, cfg.rows); // black margin ring
  for (let r = 0; r < TERMINAL_ROWS; r++) {
    for (let c = 0; c < TERMINAL_COLS; c++) {
      grid[r + TERMINAL_MARGIN][c + TERMINAL_MARGIN] = content[r][c];
    }
  }

  const cy =
    Math.max(0, Math.min(TERMINAL_ROWS - 1, terminalCursorY)) + TERMINAL_MARGIN;
  const cx =
    Math.max(0, Math.min(TERMINAL_COLS - 1, terminalCursorX)) + TERMINAL_MARGIN;
  if (terminalCursorVisible) {
    const cell = grid[cy][cx];
    // Inverted-video block cursor.
    grid[cy][cx] = { char: cell.char, fg: cell.bg, bg: cell.fg };
  }
  activeCanvas.setBuffer(grid);
}

/** Blink the block cursor continuously while the terminal is active. */
function startTerminalCursorBlink() {
  terminalCursorVisible = true;
  terminalRender();
  if (terminalCursorBlinkTimer) clearInterval(terminalCursorBlinkTimer);
  terminalCursorBlinkTimer = window.setInterval(() => {
    terminalCursorVisible = !terminalCursorVisible;
    terminalRender();
  }, 500);
}

function stopTerminalCursorBlink() {
  if (terminalCursorBlinkTimer) clearInterval(terminalCursorBlinkTimer);
  terminalCursorBlinkTimer = null;
  terminalCursorVisible = true;
}

function terminalPrintLine(text: string, fg = 7, bg = 0) {
  if (!activeCanvas) return;
  let buf = ensureTerminalBuffer();
  if (terminalCursorY >= TERMINAL_ROWS) {
    buf = scrollBuffer(buf, 1);
    terminalCursorY = TERMINAL_ROWS - 1;
  }
  buf = writeString(buf, 0, terminalCursorY, text, fg, bg);
  terminalBuffer = buf;
  terminalCursorX = 0;
  terminalCursorY++;
  terminalRender();
}

function terminalPutChar(char: string, fg = 7, bg = 0) {
  if (!activeCanvas) return;
  let buf = ensureTerminalBuffer();
  if (terminalCursorY >= TERMINAL_ROWS) {
    buf = scrollBuffer(buf, 1);
    terminalCursorY = TERMINAL_ROWS - 1;
  }
  if (terminalCursorX >= TERMINAL_COLS) terminalNewLine();
  buf = terminalBuffer || buf;
  buf[terminalCursorY][terminalCursorX] = { char, fg, bg };
  terminalBuffer = buf;
  terminalCursorX++;
  terminalRender();
}

function terminalNewLine() {
  if (!activeCanvas) return;
  let buf = ensureTerminalBuffer();
  terminalCursorX = 0;
  terminalCursorY++;
  if (terminalCursorY >= TERMINAL_ROWS) {
    buf = scrollBuffer(buf, 1);
    terminalCursorY = TERMINAL_ROWS - 1;
  }
  terminalBuffer = buf;
  terminalRender();
}

function terminalBackspace() {
  if (!activeCanvas || terminalCursorX <= 0) return;
  terminalCursorX--;
  const buf = ensureTerminalBuffer();
  buf[terminalCursorY][terminalCursorX] = { char: " ", fg: 7, bg: 0 };
  terminalBuffer = buf;
  terminalRender();
}

function terminalClearScreen() {
  if (!activeCanvas) return;
  terminalCursorX = 0;
  terminalCursorY = 0;
  terminalBuffer = createBuffer(TERMINAL_COLS, TERMINAL_ROWS);
  terminalRender();
}

function terminalClearLineFromCursor() {
  if (!activeCanvas) return;
  const buf = ensureTerminalBuffer();
  for (let col = terminalCursorX; col < TERMINAL_COLS; col++) {
    buf[terminalCursorY][col] = { char: " ", fg: 7, bg: 0 };
  }
  terminalBuffer = buf;
  terminalRender();
}

function handleTerminalControlSequence(params: string, command: string) {
  if (command === "H" || command === "f") {
    const [row = "1", col = "1"] = params.split(";");
    terminalCursorY = Math.max(0, Number(row) - 1);
    terminalCursorX = Math.max(0, Number(col) - 1);
  } else if (command === "J" && (params === "2" || params === "3")) {
    terminalClearScreen();
  } else if (command === "K") {
    terminalClearLineFromCursor();
  }
}

function terminalWriteOutput(text: string) {
  let index = 0;
  while (index < text.length) {
    if (text[index] === "\x1B" && text[index + 1] === "]") {
      const bellEnd = text.indexOf("\x07", index + 2);
      const stEnd = text.indexOf("\x1B\\", index + 2);
      const end =
        bellEnd >= 0 ? bellEnd + 1 : stEnd >= 0 ? stEnd + 2 : text.length;
      index = end;
      continue;
    }
    if (text[index] === "\x1B" && text[index + 1] === "[") {
      const match = text.slice(index).match(/^\x1B\[([0-?]*)([ -/]*)([@-~])/);
      if (match) {
        handleTerminalControlSequence(match[1], match[3]);
        index += match[0].length;
        continue;
      }
    }
    const char = text[index];
    if (char === "\r") {
      terminalCursorX = 0;
      terminalAtLineStart = true;
    } else if (char === "\n") {
      terminalNewLine();
      terminalAtLineStart = true;
    } else if (char === "\b" || char === "\x7F") {
      terminalBackspace();
      terminalAtLineStart = false;
    } else if (char >= " ") {
      // Strip the shell's " > " prompt at the start of a line.
      if (terminalAtLineStart && char === ">" && text[index + 1] === " ") {
        terminalAtLineStart = false;
        index += 2;
        continue;
      }
      terminalAtLineStart = false;
      terminalPutChar(char);
    }
    index++;
  }
}

function centerText(text: string, width = TERMINAL_COLS): string {
  const pad = Math.max(0, Math.floor((width - text.length) / 2));
  return " ".repeat(pad) + text;
}

function terminalPrintCentered(text: string, fg = 7, bg = 0) {
  terminalPrintLine(centerText(text), fg, bg);
}

/** Overwrite a whole row without disturbing the cursor position. */
function terminalWriteRow(row: number, text: string, fg = 7, bg = 0) {
  if (row < 0 || row >= TERMINAL_ROWS) return;
  const padded = (centerText(text) + " ".repeat(TERMINAL_COLS)).slice(
    0,
    TERMINAL_COLS,
  );
  terminalBuffer = writeString(ensureTerminalBuffer(), 0, row, padded, fg, bg);
  terminalRender();
}

/** C64-style boot banner: title, system stats, READY., then a blank line
 *  before the prompt. */
function loadTerminalWelcome() {
  if (!activeCanvas) return;
  terminalCursorX = 0;
  terminalCursorY = 0;
  terminalBuffer = createBuffer(TERMINAL_COLS, TERMINAL_ROWS);
  terminalRender();
  terminalPrintCentered("**** UCODE GRIDCORE TERMINAL ****", 4, 0);
  terminalPrintCentered("40X25 GRID · 8X8 CELL · PRESS START 2P", 7, 0);
  terminalPrintLine("READY.", 4, 0);
  terminalPrintLine("", 7, 0); // line gap before the prompt
  terminalCursorY = 4;
  terminalCursorX = 0;
  terminalAtLineStart = true;
  startTerminalCursorBlink();
}

function loadTerminalRuntime() {
  loadTerminalWelcome();
  connectTerminalRuntime();
}

function connectTerminalRuntime() {
  if (terminalSocket && terminalSocket.readyState <= WebSocket.OPEN) return;
  try {
    terminalSocket = new WebSocket(terminalWebSocketUrl());
  } catch (err) {
    terminalPrintLine(`Runtime socket unavailable: ${String(err)}`, 1, 0);
    return;
  }
  terminalSocket.addEventListener("open", () => {
    gridContainer.value?.focus();
  });
  terminalSocket.addEventListener("message", (event) => {
    try {
      const payload = JSON.parse(String(event.data));
      if (payload.type === "ready")
        terminalWriteRow(
          1,
          `40X25 GRID · 8X8 CELL · ${String(
            payload.runtime || "runtime",
          ).toUpperCase()}`,
          7,
          0,
        );
      else if (payload.type === "output")
        terminalWriteOutput(String(payload.data || ""));
      else if (payload.type === "error")
        terminalPrintLine(String(payload.message || "Runtime error"), 1, 0);
    } catch (err) {
      terminalPrintLine(`Runtime message error: ${String(err)}`, 1, 0);
    }
  });
  terminalSocket.addEventListener("close", () => {
    if (activeTab.value === "terminal")
      terminalPrintLine("[runtime disconnected]", 3, 0);
    terminalSocket = null;
  });
  terminalSocket.addEventListener("error", () => {
    terminalPrintLine(
      "Runtime socket error; demo canvas remains available.",
      1,
      0,
    );
  });
}

function disconnectTerminalRuntime() {
  stopTerminalCursorBlink();
  if (!terminalSocket) return;
  terminalSocket.close(1000, "Terminal tab inactive");
  terminalSocket = null;
}

function sendTerminalInput(data: string) {
  if (!terminalSocket || terminalSocket.readyState !== WebSocket.OPEN) return;
  terminalSocket.send(JSON.stringify({ type: "input", data }));
}

function onTerminalKeydown(event: KeyboardEvent) {
  if (activeTab.value !== "terminal") return;
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key === "Enter") {
    event.preventDefault();
    sendTerminalInput("\r");
  } else if (event.key === "Backspace") {
    event.preventDefault();
    sendTerminalInput("\x7F");
  } else if (event.key === "Tab") {
    event.preventDefault();
    sendTerminalInput("\t");
  } else if (event.key.length === 1) {
    event.preventDefault();
    sendTerminalInput(event.key);
  }
}

/* ─── Layer Tab ───────────────────────────────────────────────────── */
/* ─── Layer Map Seeds ──────────────────────────────────────────────── */
const layerMapName = ref<"world" | "moon" | "region">("world");

const LAYER_MAPS: {
  id: "world" | "moon" | "region";
  label: string;
  seed: LayerMap;
}[] = [
  { id: "world", label: "World", seed: worldMapSeed as LayerMap },
  { id: "moon", label: "Moon", seed: moonMapSeed as LayerMap },
  { id: "region", label: "Region", seed: regionMapSeed as LayerMap },
];

function loadLayerMapByName(name: "world" | "moon" | "region") {
  layerMapName.value = name;
  if (!activeCanvas) return;
  const map = LAYER_MAPS.find((m) => m.id === name);
  if (!map) return;
  let buf = loadLayerMap(map.seed);
  const r = map.seed.rows;
  const c = map.seed.cols;
  buf = writeString(
    buf,
    0,
    r - 1,
    `${map.seed.name} · ${c}×${r} · ${map.seed.projection}`,
    7,
    1,
  );
  activeCanvas.setBuffer(buf);
}

function loadLayerDemo() {
  loadLayerMapByName(layerMapName.value);
}

/* ─── Glyph Inspector ─────────────────────────────────────────────── */
const glyphInspectorFont = ref<"pressstart2p" | "bedstead">("pressstart2p");

function loadGlyphInspector() {
  if (!activeCanvas) return;
  const cfg = tabConfigs.glyphs;
  const c = cfg.cols; // 16
  const rows = cfg.rows; // 7: 1 header + 6 glyph rows (96 cells)
  let buf = createBuffer(c, rows);
  // Row 0 — header label (font name).
  const label =
    glyphInspectorFont.value === "pressstart2p"
      ? "TERMINAL 8x8"
      : "BEDSTEAD 12x20";
  buf = writeString(buf, 0, 0, label, 6, 0, true);
  // Rows 1..6 — printable ASCII 32..126, 16 per row.
  let code = 32;
  for (let r = 1; r < rows && code <= 126; r++) {
    for (let col = 0; col < c && code <= 126; col++) {
      buf[r][col] = { char: String.fromCharCode(code), fg: 7, bg: 0 };
      code++;
    }
  }
  activeCanvas.setBuffer(buf);
  // Re-fit so switching font re-sizes cells to the new glyph aspect.
  activeCanvas.setAttribute("font", glyphInspectorFont.value);
  nextTick(() => activeCanvas?.refit());
}

function setGlyphInspectorFont(font: "pressstart2p" | "bedstead") {
  glyphInspectorFont.value = font;
  loadGlyphInspector();
}

/* ─── Common ──────────────────────────────────────────────────────── */
function clearGrid() {
  activeCanvas?.clear();
}
</script>

<style scoped>
/* ─── uCode bridge chrome: compact USX controls around GridCore ───── */
.gridcore-surface {
  min-width: 0;
  overflow: hidden;
}

.gridcore-surface :deep(.surface-tab-nav) {
  min-width: 0;
  min-height: var(--gridcore-toolbar-min-height);
  padding: var(--gridcore-toolbar-padding-y) var(--gridcore-toolbar-padding-x);
  overflow-x: auto;
  scrollbar-width: thin;
}

.gridcore-surface :deep(button),
.gridcore-surface :deep(a) {
  box-shadow: none;
}

.gridcore-surface :deep(.surface-tab-nav__link) {
  min-height: var(--gridcore-toolbar-min-height);
  padding: var(--gridcore-space-xs) var(--gridcore-space-sm);
  gap: var(--gridcore-control-inline-gap);
  font-size: var(--gridcore-font-size-md);
  line-height: var(--gridcore-line-height-tight);
}

.gridcore-surface :deep(.surface-tab-nav__icon) {
  width: var(--gridcore-tool-btn-size);
  height: var(--gridcore-tool-btn-size);
  font-size: var(--gridcore-font-size-lg);
}

.gridcore-surface :deep(.surface-tab-nav__icon .material-symbols-outlined) {
  font-size: var(--gridcore-font-size-lg);
}

.gridcore-surface :deep(.surface-tab-nav__actions) {
  position: sticky;
  right: 0;
  gap: var(--gridcore-actions-gap);
  padding-left: var(--gridcore-space-sm);
  background: var(--gridcore-color-surface);
}

.gridcore-surface :deep(.surface-tab-nav__toggle) {
  width: var(--gridcore-tool-btn-size);
  height: var(--gridcore-tool-btn-size);
  padding: var(--gridcore-space-xs);
  font-size: var(--gridcore-font-size-lg);
}

/* ─── Single-canvas viewport ────────────────────────────────────── */
.ucode-viewport {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 2%;
  background: #000000;
}
/* Terminal: wider C64-style border (darker blue bezel around the grid). */
.ucode-viewport--terminal {
  padding: 4%;
  background: #2c4a8c;
}
.ucode-viewport gridui-canvas {
  flex-shrink: 0;
}

/* ─── Layer map selector ───────────────────────────────────────── */
.layer-map-selector {
  display: flex;
  align-items: center;
  gap: var(--gridcore-space-xs);
  padding: var(--gridcore-space-xs) var(--gridcore-space-sm);
  flex-shrink: 0;
  background: var(--gridcore-color-surface);
  border-bottom: var(--gridcore-border);
}
.layer-map-selector__label {
  font-size: var(--gridcore-font-size-sm);
  color: var(--gridcore-color-text-muted);
  margin-right: var(--gridcore-space-xs);
}
.layer-map-selector__btn {
  padding: 2px 10px;
  font-size: var(--gridcore-font-size-sm);
  color: var(--gridcore-color-text);
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  cursor: pointer;
}
.layer-map-selector__btn.active {
  color: var(--gridcore-color-surface);
  background: var(--gridcore-color-primary);
}

/* ─── Pixel Editor Layout ───────────────────────────────────────── */
.pixel-editor-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  gap: 0;
}

.pixel-editor-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pixel-editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* ─── Pixel Toolbar (inside main content div) ───────────────────── */
.pixel-toolbar {
  display: flex;
  align-items: center;
  gap: var(--gridcore-toolbar-gap);
  padding: var(--gridcore-toolbar-padding-y) var(--gridcore-toolbar-padding-x);
  background: var(--gridcore-color-surface);
  border-bottom: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md) var(--gridcore-radius-md) 0 0;
  flex-shrink: 0;
  min-height: var(--gridcore-toolbar-min-height);
  flex-wrap: nowrap;
}
.pixel-toolbar__dims {
  display: flex;
  align-items: center;
  gap: var(--gridcore-control-inline-gap);
}
.pixel-toolbar__label {
  font-size: var(--gridcore-font-size-xs);
  font-weight: var(--gridcore-font-weight-semibold);
  color: var(--gridcore-color-text-muted);
  text-transform: uppercase;
  height: var(--gridcore-control-height);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.pixel-toolbar__input {
  width: var(--gridcore-control-input-width);
  height: var(--gridcore-control-height);
  padding: 0 var(--gridcore-control-input-pad-x);
  font-size: var(--gridcore-font-size-sm);
  font-family: var(--gridcore-font-family-mono);
  background: var(--gridcore-color-background-alt);
  color: var(--gridcore-color-text);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-control-radius);
  text-align: center;
  line-height: var(--gridcore-control-height);
}
.pixel-toolbar__sep {
  font-size: var(--gridcore-font-size-md);
  color: var(--gridcore-color-text-muted);
  font-weight: var(--gridcore-font-weight-semibold);
  height: var(--gridcore-control-height);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
.pixel-toolbar__palette {
  position: relative;
  display: flex;
  align-items: center;
  margin-left: auto;
  padding-left: var(--gridcore-control-divider-pad-left);
  border-left: var(--gridcore-border);
}

/* ─── Colour Picker Popover ─────────────────────────────────────── */
.pixel-colour-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--gridcore-popover-offset-y);
  display: grid;
  grid-template-columns: repeat(8, var(--gridcore-popover-cell-size));
  grid-template-rows: repeat(4, var(--gridcore-popover-cell-size));
  gap: var(--gridcore-popover-gap);
  padding: var(--gridcore-popover-padding);
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md);
  box-shadow: var(--gridcore-popover-shadow);
  z-index: 100;
}
.pixel-colour-popover__swatch {
  width: var(--gridcore-popover-cell-size);
  height: var(--gridcore-popover-cell-size);
  border-radius: var(--gridcore-popover-radius);
  border: var(--gridcore-border);
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}
.pixel-colour-popover__swatch:hover {
  border-color: var(--gridcore-color-text-muted);
}
.pixel-colour-popover__swatch.fg-active {
  box-shadow: inset 0 0 0 var(--gridcore-active-ring-width)
    var(--gridcore-marker-fg-color);
}
.pixel-colour-popover__swatch.bg-active {
  box-shadow: inset 0 0 0 var(--gridcore-active-ring-width)
    var(--gridcore-marker-bg-color);
}
.pixel-colour-popover__swatch--empty {
  background-image:
    linear-gradient(45deg, var(--gridcore-checker-color) 25%, transparent 25%),
    linear-gradient(-45deg, var(--gridcore-checker-color) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, var(--gridcore-checker-color) 75%),
    linear-gradient(-45deg, transparent 75%, var(--gridcore-checker-color) 75%);
  background-size: var(--gridcore-checker-size) var(--gridcore-checker-size);
  background-position:
    0 0,
    0 calc(var(--gridcore-checker-size) / 2),
    calc(var(--gridcore-checker-size) / 2)
      calc(var(--gridcore-checker-size) / -2),
    calc(var(--gridcore-checker-size) / -2) 0;
}
.pixel-colour-popover__swatch .colour-marker {
  position: absolute;
  font-size: var(--gridcore-marker-font-size);
  font-weight: var(--gridcore-font-weight-bold);
  line-height: 1;
  text-shadow: var(--gridcore-marker-shadow);
}
.pixel-colour-popover__swatch .colour-marker.fg {
  top: var(--gridcore-marker-offset-sm);
  left: var(--gridcore-marker-offset-md);
  color: var(--gridcore-marker-fg-color);
}
.pixel-colour-popover__swatch .colour-marker.bg {
  bottom: var(--gridcore-marker-offset-sm);
  right: var(--gridcore-marker-offset-md);
  color: var(--gridcore-marker-bg-color);
}
.pixel-toolbar__tools {
  display: flex;
  gap: var(--gridcore-control-inline-gap);
  padding: 0 var(--gridcore-control-segment-pad-x);
  border-left: var(--gridcore-border);
}
.pixel-toolbar__actions {
  display: flex;
  gap: var(--gridcore-actions-gap);
}
.pixel-tool-btn {
  width: var(--gridcore-tool-btn-size);
  height: var(--gridcore-tool-btn-size);
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: var(--gridcore-border);
  border-radius: 0;
  color: var(--gridcore-color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
}
.pixel-tool-btn:hover {
  color: var(--gridcore-color-text);
  background: var(--gridcore-color-background-alt);
}
.pixel-tool-btn.active {
  color: var(--gridcore-color-primary);
  border-color: var(--gridcore-color-primary);
  background: var(--gridcore-color-background-alt);
}
.pixel-toolbar__action-btn {
  height: 22px;
  padding: 0 10px;
  font-size: var(--gridcore-font-size-xs);
  font-weight: var(--gridcore-font-weight-semibold);
  background: var(--gridcore-color-background-alt);
  color: var(--gridcore-color-text-muted);
  border: var(--gridcore-border);
  border-radius: 0;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  line-height: 22px;
}
.pixel-toolbar__action-btn:hover {
  color: var(--gridcore-color-text);
  border-color: var(--gridcore-color-text-muted);
}

.pixel-canvas-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: var(--gridcore-color-background-alt);
  border-radius: var(--gridcore-radius-md);
  outline: none;
  padding: var(--gridcore-space-md);
  flex: 1;
  align-self: stretch;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}
.pixel-canvas-wrapper:focus {
  outline: var(--gridcore-focus-outline-width) solid
    var(--gridcore-color-primary);
  outline-offset: var(--gridcore-focus-outline-offset);
}

/* Overlay label floats over the top-left corner of the editing grid.
   It must be absolutely positioned — as an in-flow flex item it sits NEXT
   to the grid and steals width, shrinking the editing surface. */
.editor-section__label--overlay {
  position: absolute;
  top: var(--gridcore-space-sm);
  left: var(--gridcore-space-sm);
  z-index: 2;
  padding: 2px 8px;
  font-size: var(--gridcore-font-size-xs);
  font-family: var(--gridcore-font-family-mono);
  color: var(--gridcore-color-text-muted);
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  pointer-events: none;
  user-select: none;
  white-space: nowrap;
}

/* ─── Grid Editor Layout ────────────────────────────────────────── */
.grid-editor-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  gap: 0;
  background: var(--gridcore-color-background);
}
.grid-editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  gap: 0;
}

/* ─── Layer Editor (primary pane) ────────────────────────────────── */
.layer-editor-primary {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  padding: var(--gridcore-space-sm);
  background: var(--gridcore-color-background);
}
.layer-editor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--gridcore-toolbar-gap-lg);
  padding: var(--gridcore-toolbar-padding-y) var(--gridcore-toolbar-padding-x);
  flex-shrink: 0;
  border: var(--gridcore-border);
  border-bottom: none;
  border-radius: var(--gridcore-radius-md) var(--gridcore-radius-md) 0 0;
  background: var(--gridcore-color-surface);
  min-height: var(--gridcore-toolbar-min-height);
  flex-wrap: nowrap;
}
.layer-editor__dims {
  display: flex;
  align-items: center;
  gap: var(--gridcore-control-inline-gap);
}
.layer-editor__input {
  width: var(--gridcore-control-input-width);
  height: var(--gridcore-control-height);
  padding: 0 var(--gridcore-control-input-pad-x);
  font-size: var(--gridcore-font-size-sm);
  font-family: var(--gridcore-font-family-mono);
  background: var(--gridcore-color-background-alt);
  color: var(--gridcore-color-text);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-control-radius);
  text-align: center;
  line-height: var(--gridcore-control-height);
}
.layer-editor__sep {
  font-size: var(--gridcore-font-size-md);
  color: var(--gridcore-color-text-muted);
  font-weight: var(--gridcore-font-weight-semibold);
  height: var(--gridcore-control-height);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
.layer-editor__tools {
  display: flex;
  gap: var(--gridcore-control-inline-gap);
  padding: 0 var(--gridcore-control-segment-pad-x);
  border-left: var(--gridcore-border);
}
.layer-editor__actions {
  display: flex;
  gap: var(--gridcore-actions-gap);
}
.layer-editor__palette {
  position: relative;
  display: flex;
  align-items: center;
  padding-left: var(--gridcore-control-divider-pad-left);
  border-left: var(--gridcore-border);
}
.layer-editor__info {
  margin-left: auto;
  font-size: var(--gridcore-font-size-sm);
  font-family: var(--gridcore-font-family-mono);
  color: var(--gridcore-color-text-muted);
  opacity: 0.7;
  white-space: nowrap;
}
.layer-editor__viewport {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  border-top: none;
  border-radius: 0 0 var(--gridcore-radius-md) var(--gridcore-radius-md);
  outline: none;
}
.layer-editor__viewport:focus {
  outline: var(--gridcore-focus-outline-width) solid
    var(--gridcore-color-primary);
  outline-offset: var(--gridcore-focus-outline-offset);
}

/* ─── Layer Colour Picker Popover ────────────────────────────────── */
.layer-colour-popover {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--gridcore-popover-offset-y);
  display: grid;
  grid-template-columns: repeat(3, var(--gridcore-popover-cell-size));
  grid-template-rows: repeat(3, var(--gridcore-popover-cell-size));
  gap: var(--gridcore-popover-gap);
  padding: var(--gridcore-popover-padding);
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md);
  box-shadow: var(--gridcore-popover-shadow);
  z-index: 100;
}
.layer-colour-popover__swatch {
  width: var(--gridcore-popover-cell-size);
  height: var(--gridcore-popover-cell-size);
  border-radius: var(--gridcore-popover-radius);
  border: var(--gridcore-border);
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}
.layer-colour-popover__swatch:hover {
  border-color: var(--gridcore-color-text-muted);
}
.layer-colour-popover__swatch.fg-active {
  box-shadow: inset 0 0 0 var(--gridcore-active-ring-width)
    var(--gridcore-marker-fg-color);
}
.layer-colour-popover__swatch.bg-active {
  box-shadow: inset 0 0 0 var(--gridcore-active-ring-width)
    var(--gridcore-marker-bg-color);
}
.layer-colour-popover__swatch--empty {
  background-image:
    linear-gradient(45deg, var(--gridcore-checker-color) 25%, transparent 25%),
    linear-gradient(-45deg, var(--gridcore-checker-color) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, var(--gridcore-checker-color) 75%),
    linear-gradient(-45deg, transparent 75%, var(--gridcore-checker-color) 75%);
  background-size: var(--gridcore-checker-size) var(--gridcore-checker-size);
  background-position:
    0 0,
    0 calc(var(--gridcore-checker-size) / 2),
    calc(var(--gridcore-checker-size) / 2)
      calc(var(--gridcore-checker-size) / -2),
    calc(var(--gridcore-checker-size) / -2) 0;
}
.layer-colour-popover__swatch .colour-marker {
  position: absolute;
  font-size: var(--gridcore-marker-font-size);
  font-weight: var(--gridcore-font-weight-bold);
  font-family: var(--gridcore-font-family-mono);
  line-height: 1;
  padding: var(--gridcore-marker-pad-y) var(--gridcore-marker-pad-x);
  border-radius: var(--gridcore-sidebar-char-radius);
  pointer-events: none;
}
.layer-colour-popover__swatch .colour-marker.bg {
  bottom: var(--gridcore-marker-offset-sm);
  right: var(--gridcore-marker-offset-md);
  color: var(--gridcore-marker-bg-color);
}

/* ─── Sidebar ───────────────────────────────────────────────────── */
.editor-sidebar {
  width: var(--gridcore-sidebar-width);
  flex-shrink: 0;
  overflow-y: auto;
  border-left: var(--gridcore-border);
  background: var(--gridcore-color-surface);
  padding: var(--gridcore-sidebar-padding);
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-md);
}
.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-xs);
  flex-shrink: 0;
}
.sidebar-title {
  font-size: var(--gridcore-sidebar-title-size);
  font-weight: var(--gridcore-font-weight-semibold);
  margin: 0;
  color: var(--gridcore-color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Font mapping */
.sidebar-font-btns {
  display: flex;
  gap: var(--gridcore-sidebar-font-btn-gap);
}
.sidebar-font-btn {
  flex: 1;
  padding: var(--gridcore-sidebar-font-btn-padding-y) var(--gridcore-space-xs);
  border: var(--gridcore-border);
  background: var(--gridcore-color-surface);
  color: var(--gridcore-color-text);
  cursor: pointer;
  border-radius: var(--gridcore-control-radius);
  font-size: var(--gridcore-sidebar-font-btn-size);
  font-family: var(--gridcore-font-family-mono);
  transition:
    background var(--gridcore-transition-fast),
    border-color var(--gridcore-transition-fast);
}
.sidebar-font-btn:hover {
  background: var(--gridcore-hover-bg);
  border-color: var(--gridcore-color-primary);
}
.sidebar-font-btn.active {
  background: var(--gridcore-color-primary);
  color: var(--gridcore-color-on-primary);
  border-color: var(--gridcore-color-primary);
}

/* Font character grid */
.sidebar-font-chars {
  flex: 1;
  min-height: 140px;
  overflow-y: auto;
}
.sidebar-chars-group {
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-xs);
}
.sidebar-chars-group + .sidebar-chars-group {
  margin-top: var(--gridcore-space-sm);
}
.sidebar-chars-caption {
  font-size: var(--gridcore-font-size-xs);
  font-weight: var(--gridcore-font-weight-semibold);
  color: var(--gridcore-color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.sidebar-chars-grid {
  display: grid;
  grid-template-columns: repeat(
    var(--gridcore-sidebar-char-columns),
    minmax(0, 1fr)
  );
  gap: var(--gridcore-sidebar-char-gap);
}
.sidebar-char-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 24px;
  min-width: 0;
  min-height: 0;
  margin: 0;
  padding: 0;
  border: var(--gridcore-border);
  border-radius: var(--gridcore-sidebar-char-radius);
  background: var(--gridcore-color-surface);
  color: var(--gridcore-color-text);
  cursor: pointer;
  font-family: var(--gridcore-font-family-mono);
  font-size: var(--gridcore-sidebar-char-font-size);
  transition:
    background var(--gridcore-transition-fast),
    border-color var(--gridcore-transition-fast);
}
.sidebar-char-chip:hover {
  background: var(--gridcore-hover-bg);
  border-color: var(--gridcore-color-primary);
}
.sidebar-char-chip.selected {
  border-color: var(--gridcore-color-primary);
  background: var(--gridcore-selection-bg);
}

/* Sidebar colour swatches (Pixel tab) */
.sidebar-colour-swatch {
  position: relative;
}
.sidebar-colour-swatch.fg-active {
  box-shadow: inset 0 0 0 2px #ffffff;
  border-color: #ffffff;
}
.sidebar-colour-swatch .colour-marker.fg {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 10px;
  line-height: 1;
  color: #ffffff;
  text-shadow: 0 0 2px #000000;
}

/* Sidebar helper text */
.sidebar-help {
  margin: 0;
  font-size: var(--gridcore-font-size-xs);
  color: var(--gridcore-color-text-muted);
  line-height: 1.5;
}

/* Canvas character preview */
.sidebar-char-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: var(--gridcore-sidebar-preview-min-height);
  background: var(--gridcore-color-background-alt);
  border-radius: var(--gridcore-radius-sm);
  padding: var(--gridcore-space-xs);
  border: var(--gridcore-border);
}

/* Character input */
.sidebar-char-row {
  display: flex;
  gap: var(--gridcore-space-xs);
  align-items: center;
}
.sidebar-char-input {
  width: var(--gridcore-sidebar-char-input-width);
  text-align: center;
  font-size: var(--gridcore-sidebar-char-input-size);
  font-family: var(--gridcore-font-family-mono);
  padding: var(--gridcore-space-xs);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  background: var(--gridcore-color-surface);
  color: var(--gridcore-color-text);
}
.sidebar-char-code {
  font-size: var(--gridcore-font-size-xs);
  font-family: var(--gridcore-font-family-mono);
  color: var(--gridcore-color-text-muted);
}

/* Colour markers */
.colour-marker {
  position: absolute;
  font-size: var(--gridcore-marker-font-size);
  font-weight: var(--gridcore-font-weight-bold);
  font-family: var(--gridcore-font-family-mono);
  line-height: 1;
  padding: var(--gridcore-marker-pad-y) var(--gridcore-marker-pad-x);
  border-radius: var(--gridcore-sidebar-char-radius);
  pointer-events: none;
}
.colour-marker.fg {
  top: var(--gridcore-marker-offset-sm);
  left: var(--gridcore-marker-offset-sm);
  background: var(--gridcore-marker-fg-bg);
  color: var(--gridcore-marker-fg-color);
}
.colour-marker.bg {
  bottom: var(--gridcore-marker-offset-sm);
  right: var(--gridcore-marker-offset-sm);
  background: var(--gridcore-marker-bg-bg);
  color: var(--gridcore-marker-bg-color);
}

/* Layer Composer prose stub */
.layer-composer-prose {
  max-width: var(--gridcore-prose-width);
  margin: var(--gridcore-space-xl) auto;
  padding: var(--gridcore-space-xl);
}
.layer-composer-prose h2 {
  font-size: var(--gridcore-prose-heading-size);
  margin: 0 0 var(--gridcore-space-md);
  color: var(--gridcore-color-text);
}
.layer-composer-prose p {
  margin: 0 0 var(--gridcore-space-md);
  color: var(--gridcore-color-text);
  line-height: var(--gridcore-line-height-body);
}
.layer-composer-prose ul {
  margin: 0;
  padding-left: var(--gridcore-space-lg);
}
.layer-composer-prose a {
  color: var(--gridcore-color-primary);
  text-decoration: underline;
}

/* ─── Shared ────────────────────────────────────────────────────── */
.ucode-info {
  font-size: var(--gridcore-font-size-sm);
  color: var(--gridcore-color-text-muted);
  font-family: var(--gridcore-font-family-mono);
  margin-left: var(--gridcore-space-xs);
  white-space: nowrap;
}
.surface-tab-nav__action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--gridcore-tool-btn-size);
  height: var(--gridcore-tool-btn-size);
  min-width: var(--gridcore-tool-btn-size);
  min-height: var(--gridcore-tool-btn-size);
  padding: 0;
  border: none;
  background: transparent;
  color: var(--gridcore-color-text-muted);
  cursor: pointer;
  border-radius: var(--gridcore-radius-sm);
  transition:
    color var(--gridcore-transition-fast),
    background var(--gridcore-transition-fast);
  -webkit-appearance: none;
  appearance: none;
  flex-shrink: 0;
}
.surface-tab-nav__action-btn:hover {
  color: var(--gridcore-color-primary);
  background: var(--gridcore-hover-bg);
}
.surface-tab-nav__action-btn:active {
  color: var(--gridcore-color-primary-active);
}
.surface-tab-nav__action-btn .u-icon {
  font-size: var(--gridcore-font-size-lg);
}

/* ─── Viewport preset floating popover ────────────────────────── */
.ucode-actions-spacer {
  flex: 1;
}
.surface__body,
.grid-editor-layout,
.pixel-editor-layout {
  position: relative;
}

/* The canvas wrapper must be a flex container so the viewport (flex:1)
   stretches to fill the available output-panel height. Without this the
   viewport collapses to the grid's intrinsic size and the grid can never
   grow to fit the window. */
.surface__body,
.surface__canvas {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
}
.surface__canvas {
  position: relative;
  overflow: hidden;
}
.preset-popover {
  position: absolute;
  top: 0;
  right: 0;
  left: auto;
  z-index: 10;
  max-height: 0;
  max-width: 100%;
  overflow: hidden;
  transition: max-height var(--gridcore-popover-transition);
}
.preset-popover.open {
  max-height: var(--gridcore-preset-popover-max-height);
}
.preset-popover__inner {
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-preset-popover-gap);
  padding: var(--gridcore-space-xs);
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: 0 0 var(--gridcore-radius-sm) var(--gridcore-radius-sm);
  box-shadow: var(--gridcore-preset-popover-shadow);
  min-width: var(--gridcore-preset-popover-min-width);
  max-width: 100%;
  max-height: var(--gridcore-preset-popover-max-height);
  overflow: auto;
}
.preset-popover__item {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--gridcore-space-xs);
  width: 100%;
  padding: var(--gridcore-space-xs) var(--gridcore-space-sm);
  border: var(--gridcore-border-width) solid transparent;
  border-radius: var(--gridcore-radius-sm);
  background: transparent;
  color: var(--gridcore-color-text);
  cursor: pointer;
  font-size: var(--gridcore-font-size-sm);
  font-family: var(--gridcore-font-family-mono);
  white-space: nowrap;
  text-align: right;
  transition:
    background var(--gridcore-transition-fast),
    border-color var(--gridcore-transition-fast);
}
.preset-popover__item:hover {
  background: var(--gridcore-hover-bg);
  border-color: var(--gridcore-color-primary);
}
.preset-popover__item.active {
  border-color: var(--gridcore-color-primary);
  background: var(--gridcore-selection-bg-muted);
}
.preset-popover__dims {
  font-weight: var(--gridcore-font-weight-semibold);
}
.preset-popover__desc {
  color: var(--gridcore-color-text-muted);
}

@media (max-width: 50em) {
  .gridcore-surface :deep(.surface-tab-nav__label) {
    display: none;
  }

  .gridcore-surface :deep(.surface-tab-nav__link) {
    min-width: var(--gridcore-tool-btn-size);
    justify-content: center;
  }

  .preset-popover__item {
    justify-content: flex-start;
    text-align: left;
  }
}
</style>
