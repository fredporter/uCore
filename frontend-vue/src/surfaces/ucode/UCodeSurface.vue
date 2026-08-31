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
          aria-label="Reload current uCode view"
          @click="reloadGrid"
        >
          <UIcon name="refresh" />
        </button>
        <button
          class="surface-tab-nav__action-btn"
          title="Save"
          aria-label="Save current uCode document"
          @click="exportGrid"
        >
          <UIcon name="save" />
        </button>
        <button
          class="surface-tab-nav__action-btn"
          title="Load"
          aria-label="Load a uCode document"
          @click="triggerImport"
        >
          <UIcon name="folder_open" />
        </button>
        <button
          class="surface-tab-nav__action-btn preset-toggle"
          title="Viewport presets"
          aria-label="Viewport presets"
          :aria-expanded="showPresets"
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
          <!-- Editing controls belong in the shared sidebar, never above the viewport. -->
          <div v-if="false" class="pixel-toolbar" aria-hidden="true">
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
                :disabled="!pixelCanUndo"
                @click="undoPixel"
              >
                Undo
              </button>
              <button
                class="pixel-toolbar__action-btn"
                title="Redo"
                :disabled="!pixelCanRedo"
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
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="copyPixelSelection">Copy</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="cutPixelSelection">Cut</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelHasClipboard" @click="pastePixelSelection">Paste</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="flipPixelSelection(true)">Flip H</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="flipPixelSelection(false)">Flip V</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="rotatePixelSelection(true)">Rotate ↻</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="movePixelSelection(-1, 0)">←</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="movePixelSelection(1, 0)">→</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="movePixelSelection(0, -1)">↑</button>
              <button class="pixel-toolbar__action-btn" :disabled="!pixelSelection" @click="movePixelSelection(0, 1)">↓</button>
              <button class="pixel-toolbar__action-btn" @click="addPixelFrame">+ Frame</button>
              <button class="pixel-toolbar__action-btn" @click="duplicatePixelFrame">Duplicate</button>
              <button class="pixel-toolbar__action-btn" :disabled="pixelFrameCount <= 1" @click="deletePixelFrame">Delete</button>
              <button class="pixel-toolbar__action-btn" :class="{ active: pixelOnionSkin }" @click="pixelOnionSkin = !pixelOnionSkin; renderPixelBuffer()">Onion</button>
              <button class="pixel-toolbar__action-btn" :class="{ active: pixelPlaying }" @click="togglePixelPlayback">{{ pixelPlaying ? "Stop" : "Play" }}</button>
              <label class="layer-editor__info">
                {{ pixelFrameDuration }}ms
                <input type="range" min="16" max="1000" step="16" :value="pixelFrameDuration" @input="setPixelFrameDuration" />
              </label>
            </div>
            <div class="pixel-toolbar__actions">
              <button
                v-for="(_, index) in pixelFrames"
                :key="index"
                class="pixel-toolbar__action-btn"
                :class="{ active: pixelActiveFrame === index }"
                @click="selectPixelFrame(index)"
              >{{ index + 1 }}</button>
            </div>
            <span class="layer-editor__info">{{ pixelDirty ? "Modified" : "Saved" }}</span>
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
            role="region"
            aria-label="Pixel editor canvas"
            @keydown="onPixelKeydown"
            @pointerdown="pixelIsDragging = true"
            @pointerup="pixelIsDragging = false"
            @pointercancel="pixelIsDragging = false"
            @pointerleave="pixelIsDragging = false"
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
            <h4 class="sidebar-title">Tools · {{ pixelCell.w }}×{{ pixelCell.h }}</h4>
            <div class="sidebar-tool-grid">
              <button v-for="t in PIXEL_TOOLS" :key="t.id" class="pixel-tool-btn" :class="{ active: pixelTool === t.id }" :title="t.label" :aria-label="t.label" @click="pixelTool = t.id"><UIcon :name="t.icon" /></button>
            </div>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">Actions</h4>
            <div class="sidebar-action-grid">
              <button class="sidebar-font-btn" @click="fillPixelEditor">Fill</button>
              <button class="sidebar-font-btn" @click="clearPixelEditor">Clear</button>
              <button class="sidebar-font-btn" :disabled="!pixelCanUndo" @click="undoPixel">Undo</button>
              <button class="sidebar-font-btn" :disabled="!pixelCanRedo" @click="redoPixel">Redo</button>
              <button class="sidebar-font-btn" @click="exportPixelData">Export</button>
              <button class="sidebar-font-btn" @click="triggerSymbolImport">Import</button>
            </div>
            <span class="sidebar-meta">{{ pixelDirty ? "Modified" : "Saved" }}</span>
          </div>
          <div v-if="pixelSelection || pixelHasClipboard" class="sidebar-section">
            <h4 class="sidebar-title">Selection</h4>
            <div class="sidebar-action-grid">
              <button class="sidebar-font-btn" :disabled="!pixelSelection" @click="copyPixelSelection">Copy</button>
              <button class="sidebar-font-btn" :disabled="!pixelSelection" @click="cutPixelSelection">Cut</button>
              <button class="sidebar-font-btn" :disabled="!pixelHasClipboard" @click="pastePixelSelection">Paste</button>
              <button class="sidebar-font-btn" :disabled="!pixelSelection" @click="flipPixelSelection(true)">Flip H</button>
              <button class="sidebar-font-btn" :disabled="!pixelSelection" @click="flipPixelSelection(false)">Flip V</button>
              <button class="sidebar-font-btn" :disabled="!pixelSelection" @click="rotatePixelSelection(true)">Rotate</button>
            </div>
            <div class="sidebar-tool-grid">
              <button class="pixel-tool-btn" :disabled="!pixelSelection" aria-label="Move left" @click="movePixelSelection(-1, 0)">←</button>
              <button class="pixel-tool-btn" :disabled="!pixelSelection" aria-label="Move up" @click="movePixelSelection(0, -1)">↑</button>
              <button class="pixel-tool-btn" :disabled="!pixelSelection" aria-label="Move down" @click="movePixelSelection(0, 1)">↓</button>
              <button class="pixel-tool-btn" :disabled="!pixelSelection" aria-label="Move right" @click="movePixelSelection(1, 0)">→</button>
            </div>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">Animation</h4>
            <div class="sidebar-action-grid">
              <button class="sidebar-font-btn" @click="addPixelFrame">Add frame</button>
              <button class="sidebar-font-btn" @click="duplicatePixelFrame">Duplicate</button>
              <button class="sidebar-font-btn" :disabled="pixelFrameCount <= 1" @click="deletePixelFrame">Delete</button>
              <button class="sidebar-font-btn" :class="{ active: pixelOnionSkin }" @click="pixelOnionSkin = !pixelOnionSkin; renderPixelBuffer()">Onion</button>
              <button class="sidebar-font-btn" :class="{ active: pixelPlaying }" @click="togglePixelPlayback">{{ pixelPlaying ? "Stop" : "Play" }}</button>
            </div>
            <div class="sidebar-tool-grid sidebar-tool-grid--frames">
              <button v-for="(_, index) in pixelFrames" :key="index" class="pixel-tool-btn" :class="{ active: pixelActiveFrame === index }" @click="selectPixelFrame(index)">{{ index + 1 }}</button>
            </div>
            <label class="sidebar-range">Frame {{ pixelFrameDuration }}ms<input type="range" min="16" max="1000" step="16" :value="pixelFrameDuration" @input="setPixelFrameDuration" /></label>
          </div>
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
            <h4 class="sidebar-title">Symbol</h4>
            <div class="sidebar-char-row">
              <input
                class="sidebar-char-input"
                v-model="pixelSymbol"
                aria-label="Glyph or emoji grapheme"
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
          <div class="sidebar-section">
            <div class="sidebar-font-btns">
              <button class="sidebar-font-btn" @click="exportSymbolLibrary">Export library</button>
            </div>
          </div>
          <div class="sidebar-section sidebar-font-chars sidebar-section--glyphs">
            <h4 class="sidebar-title">Glyph library</h4>
            <input v-model="glyphSearch" class="asset-panel__search" type="search" placeholder="Search assets…" aria-label="Search Pixel glyph library" />
            <select v-model="glyphCategory" class="asset-panel__select" aria-label="Pixel asset category">
              <option value="all">All</option><option value="glyph">Glyphs</option><option value="symbol">Symbols</option><option value="icon">Icons</option><option value="emoji">Emoji</option><option value="teletext-mosaic">Mosaics</option><option value="sprite">Sprites</option><option value="bob">BOBs</option>
            </select>
            <div class="sidebar-chars-grid">
              <button
                v-for="item in glyphAllMatches"
                :key="item.id"
                class="sidebar-char-chip"
                :class="{ selected: pixelSymbol === item.preview }"
                :title="`${item.label} · ${item.rendering}`"
                @click="selectPixelSymbol(item.preview)"
              >
                <span v-if="item.bitmap" class="catalogue-bitmap" :style="{ gridTemplateColumns: `repeat(${item.bitmap.width}, 1fr)`, gridTemplateRows: `repeat(${item.bitmap.height}, 1fr)` }" aria-hidden="true">
                  <i v-for="(pixel, index) in item.bitmap.pixels" :key="index" :class="{ active: pixel }"></i>
                </span>
                <template v-else>{{ item.preview }}</template>
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

    <!-- ─── Curated Software Library ─── -->
    <div v-else-if="activeTab === 'library'" class="software-library-layout">
      <main class="software-library-main" aria-label="uCode Software Library">
        <header class="software-library-header">
          <div>
            <span class="software-library-kicker">uCode Software Library</span>
            <h2>Learn from the past. Modify the future.</h2>
          </div>
          <button class="sidebar-font-btn software-library-refresh" :disabled="softwareLibraryLoading" @click="loadSoftwareLibrary">{{ softwareLibraryLoading ? "Loading…" : "Refresh" }}</button>
        </header>
        <p v-if="softwareLibraryError" class="software-library-message software-library-message--error">{{ softwareLibraryError }}</p>
        <p v-else-if="softwareLibraryLoading" class="software-library-message">Loading curated capsules…</p>
        <template v-else>
          <div class="software-library-filters" aria-label="Filter software library">
            <label><span>Search</span><input v-model="softwareLibrarySearch" type="search" placeholder="Title, platform or treatment" aria-label="Search software titles" /></label>
            <label><span>Status</span><select v-model="softwareLibraryStatus" aria-label="Filter by readiness"><option value="all">All</option><option value="launchable">Launchable</option><option value="verified">Verified</option><option value="configured">Configured</option><option value="research">Research</option></select></label>
            <span class="software-library-result-count">{{ filteredSoftwareTitles.length }} title{{ filteredSoftwareTitles.length === 1 ? "" : "s" }}</span>
          </div>
          <div class="software-library-grid" role="listbox" aria-label="Curated software titles">
          <button v-for="title in filteredSoftwareTitles" :key="title.id" class="software-title-card" :class="{ selected: selectedSoftwareTitle?.id === title.id }" role="option" :aria-selected="selectedSoftwareTitle?.id === title.id" @click="selectSoftwareTitle(title.id)">
            <span class="software-title-card__status" :class="`software-title-card__status--${title.status}`">{{ title.status }}</span>
            <strong>{{ title.title }}</strong>
            <span>{{ title.year }} · {{ title.platform }}</span>
            <p>{{ title.summary }}</p>
            <span class="software-title-card__meta">{{ title.treatment }} · {{ title.lensCoverage }}</span>
          </button>
          <p v-if="filteredSoftwareTitles.length === 0" class="software-library-message">No capsules match these filters.</p>
        </div>
        </template>
      </main>
      <aside class="editor-sidebar software-library-sidebar" aria-label="Selected software capsule">
        <template v-if="selectedSoftwareTitle">
          <div class="sidebar-section">
            <h3 class="software-library-sidebar__title">{{ selectedSoftwareTitle.title }}</h3>
            <span class="sidebar-meta">{{ selectedSoftwareTitle.platform }} · {{ selectedSoftwareTitle.year }}</span>
            <p class="sidebar-help">{{ selectedSoftwareTitle.summary }}</p>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">Capsule</h4>
            <dl class="software-capsule-facts">
              <div><dt>Treatment</dt><dd>{{ selectedSoftwareTitle.treatment }}</dd></div>
              <div><dt>Runtime</dt><dd>{{ selectedSoftwareTitle.runtime }}</dd></div>
              <div><dt>Media</dt><dd>{{ selectedSoftwareTitle.mediaPolicy }}</dd></div>
              <div><dt>LENS</dt><dd>{{ selectedSoftwareTitle.lensCoverage }}</dd></div>
            </dl>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">SKINs</h4>
            <div class="software-chip-row"><span v-for="skin in selectedSoftwareTitle.skins" :key="skin" class="software-chip">{{ skin }}</span></div>
          </div>
          <div class="sidebar-section">
            <h4 class="sidebar-title">Input</h4>
            <div class="software-chip-row"><span v-for="control in selectedSoftwareTitle.controls" :key="control" class="software-chip">{{ control }}</span></div>
          </div>
          <div v-if="softwareTitleDetailLoading" class="sidebar-section"><p class="sidebar-help">Loading title record…</p></div>
          <template v-else-if="softwareTitleDetail">
            <details v-if="softwareTitleDetail.source?.available" class="sidebar-section software-library-details">
              <summary>Source · {{ softwareTitleDetail.source.path }}</summary>
              <pre>{{ softwareSourcePreview }}</pre>
            </details>
            <details v-if="softwareTitleDetail.learning.length" class="sidebar-section software-library-details">
              <summary>Learning notes · {{ softwareTitleDetail.learning.length }}</summary>
              <article v-for="document in softwareTitleDetail.learning" :key="document.path"><strong>{{ document.path }}</strong><pre>{{ document.text }}</pre></article>
            </details>
            <details v-if="softwareTitleDetail.evidence" class="sidebar-section software-library-details">
              <summary>Compatibility evidence</summary>
              <dl class="software-capsule-facts">
                <div><dt>Edition</dt><dd>{{ softwareTitleDetail.evidence.edition }}</dd></div>
                <div><dt>Engine</dt><dd>{{ softwareTitleDetail.evidence.engine }}</dd></div>
                <div><dt>Licence</dt><dd>{{ softwareTitleDetail.evidence.licence }}</dd></div>
              </dl>
              <code class="software-evidence-hash">{{ softwareTitleDetail.evidence.entrySha256 }}</code>
            </details>
            <details v-if="softwareTitleDetail.media.policy === 'user-supplied'" open class="sidebar-section software-library-details software-media-guide">
              <summary>Media guide · {{ softwareTitleDetail.media.state }}</summary>
              <p>{{ softwareTitleDetail.media.licenceNotice }}</p>
              <ol><li>Choose an exact supported edition.</li><li>Verify its checksum locally.</li><li>Store the media inside its private capsule; uCode never redistributes it.</li></ol>
              <p>{{ softwareTitleDetail.media.nextStep }}</p>
              <span class="sidebar-meta">Accepted: {{ softwareTitleDetail.media.acceptedExtensions?.join(', ') || 'edition-specific' }}</span>
            </details>
          </template>
          <div class="sidebar-section software-library-launch">
            <div class="software-library-lifecycle">
              <button class="sidebar-font-btn" :disabled="softwareLifecycleLoading" @click="inspectSelectedCapsule('probe')">Probe</button>
              <button class="sidebar-font-btn" :disabled="softwareLifecycleLoading || !selectedSoftwareTitle.evidence" @click="inspectSelectedCapsule('verify')">Verify</button>
            </div>
            <button class="sidebar-font-btn active" :disabled="!selectedSoftwareTitle.launchable || softwareLaunchLoading" @click="launchSelectedSoftware">{{ softwareLaunchLoading ? "Preparing…" : "Launch in Terminal" }}</button>
            <p v-if="softwareLifecycleMessage" class="sidebar-help" aria-live="polite">{{ softwareLifecycleMessage }}</p>
            <p v-if="softwareLaunchMessage" class="sidebar-help" aria-live="polite">{{ softwareLaunchMessage }}</p>
            <p v-else-if="!selectedSoftwareTitle.launchable" class="sidebar-help">{{ selectedSoftwareTitle.mediaPolicy === "user-supplied" ? "Original media is required and is not distributed by uCode." : "Research capsule—not yet verified for launch." }}</p>
          </div>
        </template>
      </aside>
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
          <div v-if="false" class="layer-editor__toolbar" aria-hidden="true">
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
                v-for="t in GRID_PRIMARY_TOOLS"
                :key="t.id"
                class="pixel-tool-btn"
                :class="{ active: currentTool === t.id }"
                :title="t.label"
                :aria-label="t.label"
                @click="currentTool = t.id"
              >
                <UIcon :name="t.icon" />
              </button>
            </div>
            <div class="layer-editor__actions">
              <button
                class="pixel-toolbar__action-btn"
                @click="clearLayer"
                title="Clear layer"
              >
                Clr
              </button>
              <button
                class="pixel-toolbar__action-btn"
                :disabled="!gridCanUndo"
                @click="undoGridEdit"
                title="Undo"
              >
                Undo
              </button>
              <button
                class="pixel-toolbar__action-btn"
                :disabled="!gridCanRedo"
                @click="redoGridEdit"
                title="Redo"
              >
                Redo
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
              {{ layerCursorRow }}) · {{ gridDirty ? "Modified" : "Saved" }}</span
            >
          </div>
          <div
            class="layer-editor__viewport"
            ref="layerViewportRef"
            tabindex="0"
            role="region"
            aria-label="Grid editor canvas"
            @keydown="onLayerKeydown"
            @pointerdown="onLayerPointerDown"
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
          <h4 class="sidebar-title">Grid size</h4>
          <div class="layer-editor__dims">
            <input class="layer-editor__input" type="number" v-model.number="layerCols" min="4" max="256" aria-label="Grid columns" @change="onLayerResize" />
            <span class="layer-editor__sep">×</span>
            <input class="layer-editor__input" type="number" v-model.number="layerRows" min="4" max="256" aria-label="Grid rows" @change="onLayerResize" />
          </div>
          <span class="sidebar-meta">({{ layerCursorCol }}, {{ layerCursorRow }}) · {{ gridDirty ? "Modified" : "Saved" }}</span>
        </div>
        <div class="sidebar-section">
          <h4 class="sidebar-title">Tools</h4>
          <div class="sidebar-tool-grid">
            <button v-for="t in GRID_PRIMARY_TOOLS" :key="t.id" class="pixel-tool-btn" :class="{ active: currentTool === t.id }" :title="t.label" :aria-label="t.label" @click="currentTool = t.id"><UIcon :name="t.icon" /></button>
          </div>
        </div>
        <div class="sidebar-section">
          <h4 class="sidebar-title">Actions</h4>
          <div class="sidebar-action-grid">
            <button class="sidebar-font-btn" @click="clearLayer">Clear</button>
            <button class="sidebar-font-btn" :disabled="!gridCanUndo" @click="undoGridEdit">Undo</button>
            <button class="sidebar-font-btn" :disabled="!gridCanRedo" @click="redoGridEdit">Redo</button>
          </div>
        </div>
        <div class="sidebar-section">
          <h4 class="sidebar-title">Colours</h4>
          <div class="sidebar-chars-grid">
            <button v-for="(c, i) in PALETTE" :key="i" class="sidebar-char-chip sidebar-colour-swatch" :class="{ 'fg-active': selectedFg === i, 'bg-active': selectedBg === i }" :style="{ background: c.hex }" :title="`${c.name} · click foreground · right-click background`" @click="selectedFg = i" @click.right.prevent="selectedBg = i"><span v-if="selectedBg === i" class="colour-marker bg">B</span></button>
          </div>
        </div>
        <div class="sidebar-section">
          <h4 class="sidebar-title">Active Char</h4>
          <div class="sidebar-char-row">
            <input
              class="sidebar-char-input"
              v-model="selectedChar"
              placeholder="Char"
              aria-label="Active brush grapheme"
            />
            <span class="sidebar-char-code">{{ selectedCharCode }}</span>
          </div>
        </div>
        <p class="sidebar-help">Choose a character, then click or drag to draw. Type directly on the canvas. Select uses ⌘/Ctrl+C, X and V.</p>
        <div class="sidebar-section sidebar-font-chars sidebar-section--glyphs">
          <h4 class="sidebar-title">Glyph library</h4>
          <input v-model="glyphSearch" class="asset-panel__search" type="search" placeholder="Search assets…" aria-label="Search Grid glyph library" />
          <select v-model="glyphCategory" class="asset-panel__select" aria-label="Grid asset category">
            <option value="all">All</option><option value="glyph">Glyphs</option><option value="symbol">Symbols</option><option value="icon">Icons</option><option value="emoji">Emoji</option><option value="teletext-mosaic">Mosaics</option><option value="sprite">Sprites</option><option value="bob">BOBs</option>
          </select>
          <div class="sidebar-chars-grid">
            <button v-for="item in glyphAllMatches" :key="item.id" class="sidebar-char-chip" :class="{ selected: selectedChar === item.preview }" :title="`${item.label} · ${item.rendering}`" :aria-pressed="selectedChar === item.preview" @click="selectBrushChar(item.preview)">
              <span v-if="item.bitmap" class="catalogue-bitmap" :style="{ gridTemplateColumns: `repeat(${item.bitmap.width}, 1fr)`, gridTemplateRows: `repeat(${item.bitmap.height}, 1fr)` }" aria-hidden="true">
                <i v-for="(pixel, index) in item.bitmap.pixels" :key="index" :class="{ active: pixel }"></i>
              </span>
              <template v-else>{{ item.preview }}</template>
            </button>
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
              :aria-pressed="viewportIndex === i"
              @click="selectPreset(i)"
            >
              <span class="preset-popover__dims"
                >{{ p.cols }}×{{ p.rows }}</span
              >
              <span class="preset-popover__desc">{{ p.description }}</span>
            </button>
          </div>
        </div>
        <aside v-if="activeTab === 'layer'" class="asset-panel asset-panel--layers" aria-label="World stack">
          <h3 class="asset-panel__title">World stack</h3>
          <p class="sidebar-help">Fixed 40×25 Grids. Each level divides a parent into four exact child maps.</p>
          <div class="asset-panel__section">
            <button v-for="grid in worldGrids" :key="grid.address" class="layer-row" :class="{ active: activeWorldAddress === grid.address }" @click="selectWorldGrid(grid.address)">
              <span class="layer-row__state">{{ grid.address.split('-')[0] }}</span>
              <span class="layer-row__name">{{ grid.name }}</span>
              <span class="layer-row__meta">{{ grid.address }}</span>
            </button>
          </div>
          <div class="asset-panel__row">
            <button class="layer-map-selector__btn" @click="addWorldChild">Add child</button>
            <button class="layer-map-selector__btn" :disabled="worldGrids.length <= 1" @click="deleteWorldGrid">Delete</button>
          </div>
          <button class="layer-map-selector__btn layer-map-selector__btn--primary" @click="editWorldGrid">Edit selected Grid</button>
          <span class="layer-map-selector__label">{{ activeWorldAddress }} · {{ WORLD_GRID_COLS }}×{{ WORLD_GRID_ROWS }}</span>
        </aside>
        <aside v-if="activeTab === 'glyphs'" class="asset-panel asset-panel--glyphs" aria-label="Glyph and asset library">
          <h3 class="asset-panel__title">Glyph library</h3>
          <input
            v-model="glyphSearch"
            class="asset-panel__search"
            type="search"
            placeholder="Search symbols…"
            aria-label="Search character catalogue"
          />
          <select v-model="glyphCategory" class="asset-panel__select" aria-label="Character category">
            <option value="all">All</option>
            <option value="glyph">Glyphs</option>
            <option value="symbol">Symbols</option>
            <option value="icon">Icons</option>
            <option value="emoji">Emoji</option>
            <option value="teletext-mosaic">Mosaics</option>
            <option value="sprite">Sprites</option>
            <option value="bob">BOBs</option>
          </select>
          <div class="asset-panel__row" aria-label="Rendered glyph format">
            <button class="layer-map-selector__btn" :class="{ active: glyphInspectorFont === 'pressstart2p' }" @click="glyphInspectorFont = 'pressstart2p'">Terminal</button>
            <button class="layer-map-selector__btn" :class="{ active: glyphInspectorFont === 'bedstead' }" @click="glyphInspectorFont = 'bedstead'">Teletext</button>
          </div>
          <span class="layer-map-selector__label">{{ glyphAllMatches.length }} assets · {{ glyphInspectorFont === 'bedstead' ? 'Teletext' : 'Terminal' }}</span>
          <div class="asset-panel__catalogue-grid" role="listbox" aria-label="Character selection">
            <button v-for="item in glyphAllMatches" :key="item.id" class="sidebar-char-chip" :title="item.label" @click="selectGlyphEntry(item)">
              <span v-if="item.bitmap" class="catalogue-bitmap" :style="{ gridTemplateColumns: `repeat(${item.bitmap.width}, 1fr)`, gridTemplateRows: `repeat(${item.bitmap.height}, 1fr)` }" aria-hidden="true">
                <i v-for="(pixel, index) in item.bitmap.pixels" :key="index" :class="{ active: pixel }"></i>
              </span>
              <template v-else>{{ item.preview }}</template>
            </button>
          </div>
          <span v-if="selectedGlyphEntry" class="layer-map-selector__label" :title="selectedGlyphEntry.grapheme?.id">{{ selectedGlyphEntry.label }}</span>
          <div class="asset-panel__row">
            <button v-if="selectedGlyphEntry" class="layer-map-selector__btn" @click="editSelectedGlyph">Edit Pixel</button>
            <button v-if="selectedGlyphEntry" class="layer-map-selector__btn" @click="sendSelectedGlyphToGrid">To Grid</button>
            <button v-if="selectedGlyphEntry" class="layer-map-selector__btn" @click="addSelectedGlyphToLayer">To Layer</button>
          </div>
          <div class="asset-panel__row">
            <button class="layer-map-selector__btn" @click="exportCharacterCatalogue">Export</button>
            <button class="layer-map-selector__btn" @click="glyphImportInput?.click()">Import</button>
          </div>
          <input ref="glyphImportInput" hidden type="file" accept="application/json,.json" @change="importCharacterCatalogue" />
          <span v-if="selectedGlyphEntry" class="layer-map-selector__label">{{ selectedGlyphEntry.rendering }} · {{ selectedGlyphEntry.provenance }}</span>
        </aside>
        <div v-if="activeTab === 'teletext'" class="viewport-controls viewport-controls--teletext" aria-label="Teletext controls">
          <button
            class="layer-map-selector__btn"
            :class="{ active: teletextShowControls }"
            :aria-expanded="teletextShowControls"
            @click="teletextShowControls = !teletextShowControls"
          >
            Controls
          </button>
          <button
            v-if="teletextShowControls"
            class="layer-map-selector__btn"
            :class="{ active: teletextMode === 'reader' }"
            @click="setTeletextMode('reader')"
          >
            Reader
          </button>
          <button
            v-if="teletextShowControls"
            class="layer-map-selector__btn"
            :class="{ active: teletextMode === 'graphics' }"
            @click="setTeletextMode('graphics')"
          >
            Graphics
          </button>
          <button
            v-if="teletextShowControls && teletextMode === 'reader'"
            class="layer-map-selector__btn"
            :class="{ active: teletextShowKeypad }"
            :aria-expanded="teletextShowKeypad"
            aria-controls="teletext-keypad"
            @click="teletextShowKeypad = !teletextShowKeypad"
          >
            Keypad
          </button>
          <div
            v-if="teletextMode === 'reader' && teletextShowKeypad"
            id="teletext-keypad"
            class="teletext-keypad"
            aria-label="Teletext page keypad"
          >
            <span class="teletext-keypad__display" aria-live="polite">
              {{ teletextReader.entry || `P${teletextPage}` }}
            </span>
            <button
              v-for="digit in ['1','2','3','4','5','6','7','8','9','0']"
              :key="digit"
              class="teletext-keypad__key"
              :aria-label="`Enter page digit ${digit}`"
              @click="enterTeletextKeypadDigit(digit)"
            >{{ digit }}</button>
            <button class="teletext-keypad__key teletext-keypad__key--wide" @click="teletextGoBack">Back</button>
          </div>
          <template v-if="teletextShowControls && teletextMode === 'graphics'">
            <div class="teletext-graphics-controls" aria-label="Teletext graphics tools">
              <section class="teletext-control-group">
                <span class="teletext-control-group__title">Tool</span>
                <div class="teletext-control-group__grid">
                  <button v-for="tool in TELETEXT_GRAPHICS_TOOLS" :key="tool" class="layer-map-selector__btn" :class="{ active: teletextGraphicsTool === tool }" @click="teletextGraphicsTool = tool">{{ tool }}</button>
                </div>
              </section>
              <section class="teletext-control-group">
                <span class="teletext-control-group__title">Ink</span>
                <div class="teletext-colour-grid">
                  <button v-for="colour in [1, 2, 3, 4, 5, 6, 7]" :key="`teletext-colour-${colour}`" class="teletext-colour-key" :class="{ active: teletextGraphicsColour === colour }" :style="{ background: PALETTE[colour]?.hex }" :aria-label="`Teletext colour ${PALETTE[colour]?.name || colour}`" @click="teletextGraphicsColour = colour"></button>
                </div>
              </section>
              <section class="teletext-control-group">
                <span class="teletext-control-group__title">Edit</span>
                <div class="teletext-control-group__grid teletext-control-group__grid--actions">
                  <button class="layer-map-selector__btn" :disabled="!teletextGraphicsCanUndo" @click="undoTeletextGraphic">Undo</button>
                  <button class="layer-map-selector__btn" :disabled="!teletextGraphicsCanRedo" @click="redoTeletextGraphic">Redo</button>
                  <button class="layer-map-selector__btn" @click="clearTeletextGraphic">Clear</button>
                  <button class="layer-map-selector__btn" @click="triggerTeletextImageImport">Image</button>
                  <button class="layer-map-selector__btn" :disabled="!teletextGraphicsSelection" @click="copyTeletextGraphicSelection">Copy</button>
                  <button class="layer-map-selector__btn" :disabled="!teletextGraphicsSelection" @click="cutTeletextGraphicSelection">Cut</button>
                  <button class="layer-map-selector__btn" :disabled="!teletextGraphicsSelection" @click="saveTeletextGraphicStamp">Save stamp</button>
                </div>
              </section>
              <section class="teletext-control-group teletext-control-group--stamps">
                <span class="teletext-control-group__title">Stamps</span>
                <div class="teletext-control-group__grid">
                  <button v-for="stamp in teletextNamedStamps" :key="stamp.id" class="layer-map-selector__btn" :class="{ active: teletextSelectedStampId === stamp.id }" @click="selectTeletextGraphicStamp(stamp.id)">{{ stamp.label }}</button>
                </div>
              </section>
            </div>
            <input
              ref="teletextImageInput"
              type="file"
              accept="image/*"
              hidden
              @change="importTeletextImage"
            />
          </template>
        </div>
        <div class="surface__canvas">
          <textarea
            v-if="activeTab === 'terminal'"
            ref="terminalInputCapture"
            class="terminal-input-capture"
            aria-label="Terminal keyboard input"
            autocapitalize="off"
            autocomplete="off"
            autocorrect="off"
            spellcheck="false"
            @compositionstart="terminalComposing = true"
            @compositionend="onTerminalCompositionEnd"
            @input="onTerminalTextInput"
            @keydown="onTerminalKeydown"
          ></textarea>
          <div
            ref="gridContainer"
            class="ucode-viewport"
            :class="{ 'ucode-viewport--terminal': activeTab === 'terminal' }"
            role="region"
            tabindex="0"
            :aria-label="`${currentTitle} viewport`"
            @keydown="onSharedKeydown"
            @mousedown="focusGridContainer"
            @pointerdown="onSharedPointerStart"
            @pointermove="onSharedPointerMove"
            @pointerup="onSharedPointerActivate"
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
import { useRoute, useRouter } from "vue-router";
import { UCORE_API } from "../../api/base";
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
import { GridEditor } from "@udos/gridcore/editor";
import {
  BASELINE_LAYER_NAMES,
  deserializeLayerProject,
  LayerComposer,
  serializeLayerProject,
  type BlendMode,
  type ComposedLayer,
  type LayerProjectDocument,
} from "@udos/gridcore/layers";
import { BitmapGlyphRenderer } from "../../grid-core/g0-renderer";
import { GlyphAtlas } from "../../grid-core/glyph-atlas";
import terminalAtlasJson from "../../grid-core/seeds/glyph-atlas.terminal.json";
import bedsteadAtlasJson from "../../grid-core/seeds/glyph-atlas.bedstead.json";
import type { GridBuffer, GridCell } from "@udos/gridcore/buffer/cell";
import {
  CHARACTER_CATALOGUE,
  deserializeCharacterCatalogue,
  searchCharacterCatalogue,
  serializeCharacterCatalogue,
  type CharacterCatalogueCategory,
  type CharacterCatalogueEntry,
  type CharacterRegister,
} from "@udos/gridcore/characters";
import {
  actionFromKey,
  actionFromPoint,
  actionFromSwipe,
  hitTestGridRegions,
  moveGridRegionFocus,
  type GridActionEvent,
  type GridRegion,
} from "@udos/gridcore/interaction";
import {
  registerDotsH,
  registerDotsW,
  TALL_CELL,
} from "@udos/gridcore/coordinates/dot";
import {
  backTeletext,
  createTeletextReaderState,
  enterTeletextDigit,
  navigateTeletext,
  setTeletextStatus,
  stepTeletextSubpage,
  teletextEntryLabel,
  teletextReaderRegions,
  drawMosaicLine,
  drawMosaicRectangle,
  fillMosaicRegion,
  imageToMosaicStamp,
  stampMosaic,
  clearMosaicRect,
  extractMosaicStamp,
  mosaicRect,
  type MosaicPoint,
  type MosaicRect,
  type MosaicStamp,
  type NamedMosaicStamp,
  BUILTIN_MOSAIC_STAMPS,
  nameMosaicStamp,
  renderReaderTeletextPage,
} from "@udos/gridcore/teletext";
import {
  PixelEditor,
  PixelAnimation,
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
import { loadLayerMap, loadLayerMapBuffers } from "../../grid-core/seeds/load-layer-map";
import {
  childWorldAddresses,
  createWorldGrid,
  createWorldStack,
  validateWorldStack,
  WORLD_GRID_COLS,
  WORLD_GRID_ROWS,
  type WorldStackDocument,
} from "@udos/gridcore/world";
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
  buildTeletextLibraries,
  PUBLIC_LIBRARY_DEFS,
  ceefaxClock as gridcoreCeefaxClock,
  docScreens,
  docTitle,
  libraryForPage as gridcoreLibraryForPage,
  readLibrarySearchResponse,
  teletextContent as gridcoreTeletextContent,
} from "../../grid-core/teletext";

const shell = useShellStore();
const route = useRoute();
const router = useRouter();
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
  { id: "library", label: "Library", icon: "local_library" },
];

const VALID_UCODE_TABS = new Set(UCODE_TABS.map((tab) => tab.id));
const routeTab = String(route.query.tab || "");
const activeTab = ref(VALID_UCODE_TABS.has(routeTab) ? routeTab : "terminal");

const tabTitles: Record<string, string> = {
  terminal: "uCode — Terminal",
  teletext: "uCode — Teletext",
  pixel: "uCode — Pixel Editor",
  grid: "uCode — Grid Editor",
  layer: "uCode — Layer Surface",
  glyphs: "uCode — Glyph Inspector",
  library: "uCode — Software Library",
};

const currentTitle = computed(
  () => tabTitles[activeTab.value] || "uCode — GridCore",
);

interface SoftwareTitle {
  id: string;
  title: string;
  summary: string;
  year: number;
  platform: string;
  status: "research" | "configured" | "verified" | "enhanced" | "release";
  treatment: "authentic" | "enhanced" | "adapted";
  runtime: string;
  entry: string;
  evidence?: string;
  mediaPolicy: string;
  lensCoverage: string;
  skins: string[];
  controls: string[];
  available: boolean;
  launchable: boolean;
}

interface SoftwareTextAsset {
  path: string;
  available: boolean;
  text?: string;
  bytes?: number;
  reason?: string;
}

interface SoftwareTitleDetail {
  format: "ucode-library-title/1";
  title: SoftwareTitle;
  source: SoftwareTextAsset | null;
  learning: SoftwareTextAsset[];
  evidence: null | { edition?: string; engine?: string; licence?: string; entrySha256?: string };
  media: {
    policy: string;
    state: string;
    edition?: string;
    acceptedExtensions?: string[];
    checksums?: string[];
    licenceNotice?: string;
    nextStep?: string;
  };
}

const softwareTitles = ref<SoftwareTitle[]>([]);
const selectedSoftwareTitleId = ref<string | null>(null);
const softwareLibrarySearch = ref("");
const softwareLibraryStatus = ref("all");
const softwareLibraryLoading = ref(false);
const softwareLibraryError = ref<string | null>(null);
const softwareLaunchLoading = ref(false);
const softwareLaunchMessage = ref<string | null>(null);
const softwareLifecycleLoading = ref(false);
const softwareLifecycleMessage = ref<string | null>(null);
const softwareTitleDetail = ref<SoftwareTitleDetail | null>(null);
const softwareTitleDetailLoading = ref(false);
const selectedSoftwareTitle = computed(() =>
  softwareTitles.value.find((title) => title.id === selectedSoftwareTitleId.value) ??
  softwareTitles.value[0] ??
  null,
);
const filteredSoftwareTitles = computed(() => {
  const query = softwareLibrarySearch.value.trim().toLocaleLowerCase();
  return softwareTitles.value.filter((title) => {
    const statusMatches =
      softwareLibraryStatus.value === "all" ||
      (softwareLibraryStatus.value === "launchable" && title.launchable) ||
      title.status === softwareLibraryStatus.value;
    if (!statusMatches) return false;
    if (!query) return true;
    return [title.title, title.summary, title.platform, title.treatment, title.runtime]
      .join(" ")
      .toLocaleLowerCase()
      .includes(query);
  });
});
const softwareSourcePreview = computed(() => {
  const text = softwareTitleDetail.value?.source?.text || "";
  return text.length > 20_000 ? `${text.slice(0, 20_000)}\n… preview truncated` : text;
});

function selectSoftwareTitle(titleId: string): void {
  selectedSoftwareTitleId.value = titleId;
  softwareLaunchMessage.value = null;
  softwareLifecycleMessage.value = null;
  void loadSoftwareTitleDetail(titleId);
}

async function loadSoftwareTitleDetail(titleId: string): Promise<void> {
  softwareTitleDetailLoading.value = true;
  softwareTitleDetail.value = null;
  try {
    const response = await fetch(`${UCORE_API}/api/ucode/library/${encodeURIComponent(titleId)}`);
    if (!response.ok) throw new Error(`Title API returned ${response.status}`);
    const payload = await response.json() as SoftwareTitleDetail;
    if (payload.format !== "ucode-library-title/1") throw new Error("Unsupported title record");
    if (selectedSoftwareTitleId.value === titleId) softwareTitleDetail.value = payload;
  } catch (error) {
    if (selectedSoftwareTitleId.value === titleId) {
      softwareLifecycleMessage.value = error instanceof Error ? error.message : String(error);
    }
  } finally {
    if (selectedSoftwareTitleId.value === titleId) softwareTitleDetailLoading.value = false;
  }
}

async function inspectSelectedCapsule(action: "probe" | "verify"): Promise<void> {
  const title = selectedSoftwareTitle.value;
  if (!title) return;
  softwareLifecycleLoading.value = true;
  softwareLifecycleMessage.value = null;
  try {
    const response = await fetch(
      `${UCORE_API}/api/ucode/library/${encodeURIComponent(title.id)}/${action}`,
      { method: "POST" },
    );
    const payload = await response.json() as { state?: string; verified?: boolean; engine?: string; reason?: string };
    if (action === "verify") {
      softwareLifecycleMessage.value = payload.verified
        ? `Verified · ${payload.engine || title.runtime}`
        : payload.reason || "Compatibility evidence did not verify.";
    } else {
      softwareLifecycleMessage.value = payload.state === "available"
        ? `Available · ${title.runtime}`
        : payload.reason || "Capsule runtime is unavailable.";
    }
  } catch (error) {
    softwareLifecycleMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    softwareLifecycleLoading.value = false;
  }
}

async function loadSoftwareLibrary(): Promise<void> {
  softwareLibraryLoading.value = true;
  softwareLibraryError.value = null;
  try {
    const infoResponse = await fetch(`${UCORE_API}/api/ucode/info`);
    if (infoResponse.status === 404) {
      throw new Error("The running backend predates this uCode build. Restart uCore, then refresh the Library.");
    }
    if (!infoResponse.ok) throw new Error(`uCode runtime check returned ${infoResponse.status}`);
    const runtimeInfo = await infoResponse.json() as { format?: string; capabilities?: string[] };
    if (
      runtimeInfo.format !== "ucode-runtime/1" ||
      !runtimeInfo.capabilities?.includes("software-library.title-detail")
    ) {
      throw new Error("The running backend does not support this Software Library contract. Update or restart uCore.");
    }
    const response = await fetch(`${UCORE_API}/api/ucode/library`);
    if (!response.ok) throw new Error(`Library API returned ${response.status}`);
    const payload = await response.json() as { format?: string; titles?: SoftwareTitle[] };
    if (payload.format !== "ucode-library/1" || !Array.isArray(payload.titles)) {
      throw new Error("Library API returned an unsupported catalogue");
    }
    softwareTitles.value = payload.titles;
    if (!selectedSoftwareTitleId.value || !softwareTitles.value.some((title) => title.id === selectedSoftwareTitleId.value)) {
      selectedSoftwareTitleId.value = softwareTitles.value[0]?.id ?? null;
    }
    if (selectedSoftwareTitleId.value) void loadSoftwareTitleDetail(selectedSoftwareTitleId.value);
  } catch (error) {
    softwareLibraryError.value = error instanceof Error ? error.message : String(error);
  } finally {
    softwareLibraryLoading.value = false;
  }
}

async function launchSelectedSoftware(): Promise<void> {
  const title = selectedSoftwareTitle.value;
  if (!title || !title.launchable) return;
  softwareLaunchLoading.value = true;
  softwareLaunchMessage.value = null;
  try {
    const response = await fetch(`${UCORE_API}/api/ucode/library/${encodeURIComponent(title.id)}/launch`, { method: "POST" });
    const payload = await response.json() as { launchable?: boolean; protocol?: string; session?: string; titleId?: string; reason?: string };
    if (!response.ok || !payload.launchable || payload.protocol !== "ucode-session/1" || payload.session !== "capsule" || !payload.titleId) {
      throw new Error(payload.reason || `Launch API returned ${response.status}`);
    }
    softwareLaunchMessage.value = `Opening ${title.title} in Terminal…`;
    terminalSessionKind = "capsule";
    terminalActiveCapsuleId = payload.titleId;
    activeTab.value = "terminal";
    await nextTick();
    terminalClearScreen(true);
    connectTerminalRuntime(payload.titleId);
  } catch (error) {
    softwareLaunchMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    softwareLaunchLoading.value = false;
  }
}

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
  glyphs: { cols: 16, rows: 12, font: "pressstart2p", cellSize: 24 },
};

/* ─── Single-Canvas Tabs ──────────────────────────────────────────── */
const gridContainer = ref<HTMLDivElement>();
const terminalInputCapture = ref<HTMLTextAreaElement>();
const canvasCache = new Map<string, GridUICanvasElement>();
let activeCanvas: GridUICanvasElement | null = null;
type TerminalSnapshot = {
  buffer: GridBuffer;
  scrollback: GridBuffer;
  scrollOffset: number;
  cursorX: number;
  cursorY: number;
  atLineStart: boolean;
};

let terminalSocket: WebSocket | null = null;
const terminalRuntimeState = ref("disconnected");
let terminalReconnectTimer: number | null = null;
let terminalReconnectAttempt = 0;
let terminalSessionKind: "shell" | "capsule" = "shell";
let terminalActiveCapsuleId: string | null = null;
let terminalSnapshot: TerminalSnapshot | null = null;
let terminalPendingInput = "";
let terminalComposing = false;
let terminalCursorX = 0;
let terminalCursorY = 0;

/** Terminal content area (the PTY is 40×25); the grid adds a 1-cell black
 *  margin all round (42×27). */
const TERMINAL_COLS = 40;
const TERMINAL_ROWS = 25;
const TERMINAL_MARGIN = 1;
let terminalBuffer: GridBuffer | null = null;
let terminalScrollback: GridBuffer = [];
let terminalScrollOffset = 0;
const TERMINAL_SCROLLBACK_LIMIT = 1000;
let terminalAtLineStart = false;

/* ─── Shared Brush State (persists across Pixel/Grid tabs) ─────────── */
const PALETTE = PALETTE_DARK; // 8-colour MODE 7 — Grid/Layer editors
const PIXEL_PALETTE = PALETTE_PIXEL_32; // 32-colour — Pixel Editor

const TOOLS = [
  { id: "pencil", label: "Pencil", icon: "edit" },
  { id: "fill", label: "Flood fill", icon: "format_paint" },
  { id: "erase", label: "Eraser", icon: "ink_eraser" },
  { id: "eyedropper", label: "Eyedropper", icon: "colorize" },
  { id: "select", label: "Select", icon: "select_all" },
] as const;
const GRID_PRIMARY_TOOLS = TOOLS.filter((tool) =>
  ["pencil", "erase", "fill", "select"].includes(tool.id),
);

// Pixel Editor tools (true sub-cell 24×24 colour bitmap)
const PIXEL_TOOLS = [
  { id: "pencil", label: "Pencil", icon: "edit" },
  { id: "fill", label: "Flood fill", icon: "format_paint" },
  { id: "erase", label: "Eraser", icon: "ink_eraser" },
  { id: "eyedropper", label: "Eyedropper", icon: "colorize" },
  { id: "select", label: "Select", icon: "select_all" },
] as const;

const pixelTool = ref<
  "pencil" | "fill" | "erase" | "eyedropper" | "select"
>("pencil");
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
const pixelFont = ref<"pressstart2p" | "bedstead">("pressstart2p");
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
  pixelEditor.markSaved();
  pixelHistoryTick.value++;
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
const editorFont = ref<"pressstart2p" | "bedstead">("pressstart2p");
const currentTool = ref<
  "pencil" | "fill" | "erase" | "eyedropper" | "select"
>("pencil");

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
let gridDocument = new GridEditor(layerBuffer);
const gridHistoryTick = ref(0);
const gridCanUndo = computed(() => {
  void gridHistoryTick.value;
  return gridDocument.canUndo;
});
const gridCanRedo = computed(() => {
  void gridHistoryTick.value;
  return gridDocument.canRedo;
});
const gridDirty = computed(() => {
  void gridHistoryTick.value;
  return gridDocument.dirty;
});
const gridSelection = computed(() => {
  void gridHistoryTick.value;
  return gridDocument.getSelection();
});
const gridHasClipboard = computed(() => {
  void gridHistoryTick.value;
  return gridDocument.hasClipboard;
});
let layerIsDragging = false;
let gridSelectionStart: { col: number; row: number } | null = null;

/* ─── Canvas refs & elements ──────────────────────────────────────── */
const layerViewportRef = ref<HTMLDivElement>();
const pixelCanvasRef = ref<HTMLDivElement>();
const importInputRef = ref<HTMLInputElement>();
const symbolImportRef = ref<HTMLInputElement>();

let layerCanvas: GridUICanvasElement | null = null;
let pixelCanvas: GridUICanvasElement | null = null;
let gridInitialized = false;

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
let pixelAnimation: PixelAnimation | null = null;
const pixelOnionSkin = ref(false);
const pixelPlaying = ref(false);
let pixelPlaybackTimer: number | null = null;
let pixelPlaybackStartedAt = 0;
const pixelFrameTick = ref(0);
const pixelActiveFrame = computed(() => {
  void pixelFrameTick.value;
  return pixelAnimation?.active ?? 0;
});
const pixelFrameCount = computed(() => {
  void pixelFrameTick.value;
  return pixelAnimation?.length ?? 1;
});
const pixelFrames = computed(() => {
  void pixelFrameTick.value;
  return pixelAnimation?.list() ?? [];
});
const pixelFrameDuration = computed(() => {
  void pixelFrameTick.value;
  return pixelAnimation?.current().durationMs ?? 120;
});
let pixelSelectionStart: { x: number; y: number } | null = null;
const pixelHistoryTick = ref(0);
const pixelCanUndo = computed(() => {
  void pixelHistoryTick.value;
  return pixelEditor?.canUndo ?? false;
});
const pixelCanRedo = computed(() => {
  void pixelHistoryTick.value;
  return pixelEditor?.canRedo ?? false;
});
const pixelDirty = computed(() => {
  void pixelHistoryTick.value;
  return pixelEditor?.dirty ?? false;
});
const pixelSelection = computed(() => {
  void pixelHistoryTick.value;
  return pixelEditor?.getSelection() ?? null;
});
const pixelHasClipboard = computed(() => {
  void pixelHistoryTick.value;
  return pixelEditor?.hasClipboard ?? false;
});
/** Preview buffer: each pixel as a solid-colour cell for <gridui-canvas>. */
let pixelBuffer: GridBuffer = createBuffer(24, 24);
/** Ink bounding box of the current glyph (variable-width readout). */
const pixelInk = ref<{ w: number; h: number } | null>(null);

function renderPixelBuffer() {
  if (!pixelCanvas || !pixelEditor) return;
  const { w, h } = pixelCell.value;
  const pixels = pixelEditor.buffer;
  pixelAnimation?.update(pixels);
  pixelBuffer = pixelBufferToGridBuffer(pixels, w, h);
  if (pixelOnionSkin.value) {
    const previous = pixelAnimation?.previous()?.pixels;
    if (previous) {
      for (let index = 0; index < pixels.length; index++) {
        if (pixels[index] !== 0 || previous[index] === 0) continue;
        const row = Math.floor(index / w);
        const col = index % w;
        pixelBuffer[row][col] = { char: "█", fg: 5, bg: 0 };
      }
    }
  }
  const selection = pixelEditor.getSelection();
  if (selection) {
    for (let row = selection.y; row < selection.y + selection.height; row++) {
      for (let col = selection.x; col < selection.x + selection.width; col++) {
        const cell = pixelBuffer[row]?.[col];
        if (cell) pixelBuffer[row][col] = { ...cell, fg: cell.bg, bg: cell.fg, bold: true };
      }
    }
  }
  pixelCanvas.setBuffer(cloneBuffer(pixelBuffer));
  const b = measureInkBounds(pixels, w, h);
  pixelInk.value = b
    ? { w: b.maxX - b.minX + 1, h: b.maxY - b.minY + 1 }
    : null;
  pixelHistoryTick.value++;
}

function initPixelEditor() {
  if (!pixelCanvasRef.value) return;
  pixelCanvas?.remove();
  const { w, h } = pixelCell.value;
  const needsDocument = !pixelEditor || !pixelAnimation;
  if (needsDocument) {
    pixelEditor = new PixelEditor(createPixelBuffer(0, w, h), w, h);
    pixelAnimation = new PixelAnimation(pixelEditor.buffer, w, h);
    pixelFrameTick.value++;
  }
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
  if (needsDocument) loadGlyphFromFont();
  else renderPixelBuffer();
}

function paintPixelAt(x: number, y: number) {
  if (!pixelEditor) return;
  if (pixelTool.value === "select") {
    if (!pixelSelectionStart) pixelSelectionStart = { x, y };
    const left = Math.min(pixelSelectionStart.x, x);
    const top = Math.min(pixelSelectionStart.y, y);
    pixelEditor.select(
      left,
      top,
      Math.abs(x - pixelSelectionStart.x) + 1,
      Math.abs(y - pixelSelectionStart.y) + 1,
    );
    renderPixelBuffer();
    return;
  }
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
  if (pixelTool.value === "select") pixelSelectionStart = null;
}

function onPixelCellHover(e: CustomEvent) {
  if (!pixelIsDragging.value) return;
  const { col, row } = e.detail || {};
  if (typeof col === "number" && typeof row === "number")
    paintPixelAt(col, row);
}

function copyPixelSelection(): void {
  pixelEditor?.copy();
  pixelHistoryTick.value++;
}

function cutPixelSelection(): void {
  pixelEditor?.cut();
  renderPixelBuffer();
}

function pastePixelSelection(): void {
  const selection = pixelEditor?.getSelection();
  pixelEditor?.paste(selection?.x ?? 0, selection?.y ?? 0);
  renderPixelBuffer();
}

function flipPixelSelection(horizontal: boolean): void {
  pixelEditor?.flipSelection(horizontal);
  renderPixelBuffer();
}

function rotatePixelSelection(clockwise: boolean): void {
  pixelEditor?.rotateSelection(clockwise);
  renderPixelBuffer();
}

function movePixelSelection(dx: number, dy: number): void {
  pixelEditor?.moveSelection(dx, dy);
  renderPixelBuffer();
}

function addPixelFrame(): void {
  if (!pixelAnimation || !pixelEditor) return;
  pixelAnimation.update(pixelEditor.buffer);
  const frame = pixelAnimation.add();
  pixelEditor = new PixelEditor(frame.pixels, pixelCell.value.w, pixelCell.value.h);
  pixelFrameTick.value++;
  renderPixelBuffer();
}

function duplicatePixelFrame(): void {
  if (!pixelAnimation || !pixelEditor) return;
  pixelAnimation.update(pixelEditor.buffer);
  const frame = pixelAnimation.duplicate();
  pixelEditor = new PixelEditor(frame.pixels, pixelCell.value.w, pixelCell.value.h);
  pixelFrameTick.value++;
  renderPixelBuffer();
}

function deletePixelFrame(): void {
  if (!pixelAnimation) return;
  pixelAnimation.delete();
  const frame = pixelAnimation.current();
  pixelEditor = new PixelEditor(frame.pixels, pixelCell.value.w, pixelCell.value.h);
  pixelFrameTick.value++;
  renderPixelBuffer();
}

function selectPixelFrame(index: number): void {
  if (!pixelAnimation || !pixelEditor) return;
  pixelAnimation.update(pixelEditor.buffer);
  pixelAnimation.select(index);
  const frame = pixelAnimation.current();
  pixelEditor = new PixelEditor(frame.pixels, pixelCell.value.w, pixelCell.value.h);
  pixelFrameTick.value++;
  renderPixelBuffer();
}

function setPixelFrameDuration(event: Event): void {
  pixelAnimation?.setDuration(Number((event.target as HTMLInputElement).value));
  pixelFrameTick.value++;
}

function togglePixelPlayback(): void {
  if (pixelPlaying.value) {
    stopPixelPlayback();
    return;
  }
  if (!pixelAnimation || pixelAnimation.length < 2) return;
  pixelAnimation.update(pixelEditor?.buffer ?? pixelAnimation.current().pixels);
  pixelPlaying.value = true;
  pixelPlaybackStartedAt = performance.now();
  pixelPlaybackTimer = window.setInterval(() => {
    if (!pixelAnimation || activeTab.value !== "pixel") return;
    const index = pixelAnimation.frameIndexAt(performance.now() - pixelPlaybackStartedAt);
    if (index !== pixelAnimation.active) {
      pixelAnimation.select(index);
      const frame = pixelAnimation.current();
      pixelEditor = new PixelEditor(frame.pixels, pixelCell.value.w, pixelCell.value.h);
      pixelFrameTick.value++;
      renderPixelBuffer();
    }
  }, 16);
}

function stopPixelPlayback(): void {
  pixelPlaying.value = false;
  if (pixelPlaybackTimer !== null) {
    clearInterval(pixelPlaybackTimer);
    pixelPlaybackTimer = null;
  }
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

function onPixelKeydown(event: KeyboardEvent): void {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") {
    event.preventDefault();
    if (event.shiftKey) redoPixel();
      else undoPixel();
    return;
  }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "c") {
    event.preventDefault();
    copyPixelSelection();
  } else if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "x") {
    event.preventDefault();
    cutPixelSelection();
  } else if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "v") {
    event.preventDefault();
    pastePixelSelection();
  }
}

function exportPixelData() {
  if (!pixelEditor || !pixelAnimation) return;
  const { w, h } = pixelCell.value;
  pixelAnimation.update(pixelEditor.buffer);
  downloadJson(pixelAnimation.serialize(), `pixel-animation-${w}x${h}.json`);
  pixelEditor.markSaved();
  pixelHistoryTick.value++;
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

  if (!gridInitialized) {
    loadGridEditorDemo();
    gridInitialized = true;
  }
  renderLayerBuffer();
}

function loadGridEditorDemo() {
  layerBuffer = createBuffer(LAYER_COLS, LAYER_ROWS);
  resetGridDocument(layerBuffer);
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
  resetGridDocument(layerBuffer, false);
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
  const selection = gridDocument.getSelection();
  if (selection) {
    for (let row = selection.y; row < selection.y + selection.h; row++) {
      for (let col = selection.x; col < selection.x + selection.w; col++) {
        const cell = buf[row]?.[col];
        if (cell) buf[row][col] = { ...cell, fg: cell.bg, bg: cell.fg, bold: true };
      }
    }
  }
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

function resetGridDocument(buffer: GridBuffer, saved = true): void {
  layerBuffer = cloneBuffer(buffer);
  gridDocument = new GridEditor(layerBuffer);
  if (saved) gridDocument.markSaved();
  gridHistoryTick.value++;
}

function commitGridEdit(operation: (draft: GridBuffer) => void): void {
  gridDocument.mutate(operation);
  layerBuffer = gridDocument.buffer;
  gridHistoryTick.value++;
  renderLayerBuffer();
}

function undoGridEdit(): void {
  gridDocument.undo();
  layerBuffer = gridDocument.buffer;
  gridHistoryTick.value++;
  renderLayerBuffer();
}

function redoGridEdit(): void {
  gridDocument.redo();
  layerBuffer = gridDocument.buffer;
  gridHistoryTick.value++;
  renderLayerBuffer();
}

/* ─── Grid Tab — Interaction ──────────────────────────────────────── */

function onLayerKeydown(e: KeyboardEvent) {
  if (activeTab.value !== "grid") return;
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") {
    e.preventDefault();
    if (e.shiftKey) redoGridEdit();
    else undoGridEdit();
    return;
  }
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "c") {
    e.preventDefault();
    copyGridSelection();
    return;
  }
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "x") {
    e.preventDefault();
    cutGridSelection();
    return;
  }
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "v") {
    e.preventDefault();
    pasteGridSelection();
    return;
  }
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
          commitGridEdit((draft) => {
            draft[ly][lx] = {
              char: e.key,
              fg: selectedFg.value,
              bg: selectedBg.value,
            };
          });
        }
      }
      break;
  }
}

function onLayerPointerDown(e: PointerEvent) {
  layerIsDragging = true;
  const start = layerCellFromMouse(e);
  if (currentTool.value === "select" && start) {
    gridSelectionStart = start;
    gridDocument.select(start.col, start.row, 1, 1);
    gridHistoryTick.value++;
    renderLayerBuffer();
  }
  const onMove = (ev: PointerEvent) => {
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
      if (currentTool.value === "select" && gridSelectionStart) {
        const x = Math.min(gridSelectionStart.col, col);
        const y = Math.min(gridSelectionStart.row, row);
        gridDocument.select(
          x,
          y,
          Math.abs(col - gridSelectionStart.col) + 1,
          Math.abs(row - gridSelectionStart.row) + 1,
        );
        gridHistoryTick.value++;
        renderLayerBuffer();
      } else {
        doLayerPaint();
      }
    }
  };
  const onUp = () => {
    layerIsDragging = false;
    gridSelectionStart = null;
    document.removeEventListener("pointermove", onMove);
    document.removeEventListener("pointerup", onUp);
    document.removeEventListener("pointercancel", onUp);
  };
  document.addEventListener("pointermove", onMove);
  document.addEventListener("pointerup", onUp);
  document.addEventListener("pointercancel", onUp);
}

function layerCellFromMouse(event: PointerEvent): { col: number; row: number } | null {
  if (!layerCanvas) return null;
  const rect = layerCanvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const col = Math.floor(((event.clientX - rect.left) / rect.width) * LAYER_COLS);
  const row = Math.floor(((event.clientY - rect.top) / rect.height) * LAYER_ROWS);
  return col >= 0 && col < LAYER_COLS && row >= 0 && row < LAYER_ROWS
    ? { col, row }
    : null;
}

function doLayerPaint() {
  const lx = layerCursorCol.value;
  const ly = layerCursorRow.value;
  if (lx < 0 || lx >= LAYER_COLS || ly < 0 || ly >= LAYER_ROWS) return;
  const tool = currentTool.value;
  if (tool === "select") {
    return;
  }
  if (tool === "eyedropper") {
    const cell = layerBuffer[ly][lx];
    selectedFg.value = cell.fg;
    selectedBg.value = cell.bg;
    selectedChar.value = cell.char;
    currentTool.value = "pencil";
    return;
  }
  if (tool === "erase") {
    commitGridEdit((draft) => {
      draft[ly][lx] = { char: " ", fg: 7, bg: 0 };
    });
    return;
  }
  commitGridEdit((draft) => {
    draft[ly][lx] = {
      char: selectedChar.value,
      fg: selectedFg.value,
      bg: selectedBg.value,
    };
  });
}

function onLayerCellClick(e: CustomEvent) {
  const { col, row } = e.detail;
  layerCursorCol.value = col;
  layerCursorRow.value = row;
  if (col < 0 || col >= LAYER_COLS || row < 0 || row >= LAYER_ROWS) return;
  const tool = currentTool.value;
  if (tool === "select") {
    if (!gridSelectionStart) gridDocument.select(col, row, 1, 1);
    gridHistoryTick.value++;
    renderLayerBuffer();
    return;
  }
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
    commitGridEdit((draft) => {
      draft[row][col] = { char: " ", fg: 7, bg: 0 };
    });
    return;
  }
  if (tool === "fill") {
    commitGridEdit((draft) =>
      floodFillBuffer(
        draft,
        col,
        row,
        selectedFg.value,
        selectedBg.value,
        selectedChar.value,
      ),
    );
    return;
  }
  commitGridEdit((draft) => {
    draft[row][col] = {
      char: selectedChar.value,
      fg: selectedFg.value,
      bg: selectedBg.value,
    };
  });
}

function floodFillBuffer(
  buffer: GridBuffer,
  startX: number,
  startY: number,
  fg: number,
  bg: number,
  char: string,
) {
  const targetChar = buffer[startY][startX].char;
  const targetFg = buffer[startY][startX].fg;
  if (targetChar === char && targetFg === fg) return;
  const stack: [number, number][] = [[startX, startY]];
  const visited = new Set<number>();
  while (stack.length > 0) {
    const [cx, cy] = stack.pop()!;
    const key = cy * LAYER_COLS + cx;
    if (visited.has(key)) continue;
    visited.add(key);
    if (cx < 0 || cx >= LAYER_COLS || cy < 0 || cy >= LAYER_ROWS) continue;
    const cell = buffer[cy][cx];
    if (cell.char !== targetChar || cell.fg !== targetFg) continue;
    buffer[cy][cx] = { char, fg, bg };
    stack.push([cx - 1, cy], [cx + 1, cy], [cx, cy - 1], [cx, cy + 1]);
  }
}

function clearLayer() {
  gridDocument.replace(createBuffer(LAYER_COLS, LAYER_ROWS));
  layerBuffer = gridDocument.buffer;
  gridHistoryTick.value++;
  renderLayerBuffer();
}

function copyGridSelection(): void {
  gridDocument.copy();
  gridHistoryTick.value++;
}

function cutGridSelection(): void {
  gridDocument.cut();
  layerBuffer = gridDocument.buffer;
  gridHistoryTick.value++;
  renderLayerBuffer();
}

function pasteGridSelection(): void {
  gridDocument.paste(layerCursorCol.value, layerCursorRow.value);
  layerBuffer = gridDocument.buffer;
  gridHistoryTick.value++;
  renderLayerBuffer();
}
function fillLayer() {
  commitGridEdit((draft) => {
    for (let r = 0; r < LAYER_ROWS; r++)
      for (let c = 0; c < LAYER_COLS; c++)
        draft[r][c] = {
          char: selectedChar.value,
          fg: selectedFg.value,
          bg: selectedBg.value,
        };
  });
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
    resetGridDocument(layerBuffer, false);
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
  resetGridDocument(layerBuffer, false);
  layerCursorCol.value = Math.min(layerCursorCol.value, newCols - 1);
  layerCursorRow.value = Math.min(layerCursorRow.value, newRows - 1);
  destroyGridEditor();
  nextTick(() => initGridEditor());
}

/* ─── Lifecycle ───────────────────────────────────────────────────── */
onMounted(() => {
  if (activeTab.value === "pixel") initPixelEditor();
  else if (activeTab.value === "grid") initGridEditor();
  else if (activeTab.value === "library") void loadSoftwareLibrary();
  else if (gridContainer.value) initGrid(activeTab.value);
  startTeletextClock();
  window.addEventListener("online", updateTeletextConnectivity);
  window.addEventListener("offline", updateTeletextConnectivity);
});

onUnmounted(() => {
  stopTeletextClock();
  stopPixelPlayback();
  window.removeEventListener("online", updateTeletextConnectivity);
  window.removeEventListener("offline", updateTeletextConnectivity);
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
    if (tabId === "glyphs") {
      el.addEventListener("cell-click", onGlyphCellClick as EventListener);
    }
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

watch(activeTab, (newTab, oldTab) => {
  if (oldTab === "grid" && newTab === "layer" && editingWorldAddress) {
    const grids = worldStack.value.grids.map((grid) =>
      grid.address === editingWorldAddress ? { ...grid, buffer: cloneBuffer(layerBuffer) } : grid,
    );
    worldStack.value = { ...worldStack.value, grids };
    editingWorldAddress = null;
  }
  if (route.query.tab !== newTab) {
    router.replace({ query: { ...route.query, tab: newTab } });
  }
  if (oldTab === "terminal" && newTab !== "terminal") {
    saveTerminalView();
    disconnectTerminalRuntime();
  }
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
    else if (newTab === "library") void loadSoftwareLibrary();
    else if (gridContainer.value) initGrid(newTab);
  });
});

watch(
  () => route.query.tab,
  (tab) => {
    const normalized = String(tab || "terminal");
    if (VALID_UCODE_TABS.has(normalized)) activeTab.value = normalized;
  },
);

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
      initializeWorldStack();
      renderWorldGrid();
      break;
    case "glyphs":
      loadGlyphInspector();
      break;
  }
}

function reloadGrid() {
  if (activeTab.value === "pixel") {
    initPixelEditor();
  } else if (activeTab.value === "grid") {
    loadGridEditorDemo();
  } else if (activeTab.value === "layer") {
    worldStackReady.value = false;
    initializeWorldStack();
    renderWorldGrid();
  } else if (activeTab.value === "teletext") {
    vaultLoaded.value = false;
    vaultDocCache.clear();
    void loadVaultContent();
  } else if (activeTab.value === "library") {
    void loadSoftwareLibrary();
  } else loadTabContent();
}

/* ─── Export/Import ────────────────────────────────────────────────── */
function getExportBuffer(): GridBuffer {
  if (activeTab.value === "pixel") return pixelBuffer;
  if (activeTab.value === "grid") return layerBuffer;
  if (activeTab.value === "layer") return layerComposer.compose();
  if (activeCanvas) return activeCanvas.buffer;
  return createBuffer(40, 25);
}

function exportGrid() {
  if (activeTab.value === "pixel") {
    exportPixelData();
    return;
  }
  if (activeTab.value === "layer") {
    downloadJson(worldStack.value, "ucode-world-stack.json");
    return;
  }
  const buf = getExportBuffer();
  const cols = buf.length > 0 ? buf[0].length : 40;
  const rows = buf.length;
  const data = {
    format: "ucode-grid-v1",
    cols,
    rows,
    cells: buf.map((row) => row.map((c) => ({ c: c.char, f: c.fg, b: c.bg }))),
  };
  downloadJson(data, `ucode-grid-${cols}x${rows}.json`);
  if (activeTab.value === "grid") {
    gridDocument.markSaved();
    gridHistoryTick.value++;
  }
}

function downloadJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
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
      if (activeTab.value === "layer" && data.format === "ucode-world-stack-v1") {
        if (!validateWorldStack(data)) throw new Error("Invalid World stack document");
        worldStack.value = data;
        worldStackReady.value = true;
        renderWorldGrid();
        return;
      }
      if (activeTab.value === "pixel" && data.format === "ucode-pixel-animation-v1") {
        const restored = PixelAnimation.deserialize(data);
        const { w, h } = pixelCell.value;
        if (data.width !== w || data.height !== h) throw new Error(`Pixel document is ${data.width}×${data.height}; this editor is ${w}×${h}`);
        pixelAnimation = restored;
        const frame = restored.current();
        pixelEditor = new PixelEditor(frame.pixels, w, h);
        pixelFrameTick.value++;
        renderPixelBuffer();
        return;
      }
      if (activeTab.value === "layer" && data.format === "ucode-layer-project-v1") {
        const restored = deserializeLayerProject(data);
        layerComposer = restored.composer;
        selectedComposedLayerId.value = restored.selectedLayerId;
        resetComposedLayerHistory();
        renderComposedLayers();
        return;
      }
      if (data.format !== "ucode-grid-v1" || !data.cells) return;
      if (activeTab.value === "grid") {
        const cols = Math.max(4, Math.min(256, Number(data.cols) || 40));
        const rows = Math.max(4, Math.min(256, Number(data.rows) || 25));
        const imported = createBuffer(cols, rows);
        for (let row = 0; row < rows; row++) for (let col = 0; col < cols; col++) {
          const src = data.cells[row]?.[col];
          if (src) imported[row][col] = { char: src.c || " ", fg: src.f ?? 7, bg: src.b ?? 0 };
        }
        LAYER_COLS = cols;
        LAYER_ROWS = rows;
        layerCols.value = cols;
        layerRows.value = rows;
        resetGridDocument(imported, true);
        gridInitialized = true;
        destroyGridEditor();
        nextTick(() => initGridEditor());
        return;
      }
      const isPixel = activeTab.value === "pixel";
      const isGridLayer = false;
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
const teletextReader = ref(createTeletextReaderState(100));
const teletextShowControls = ref(false);
const teletextShowKeypad = ref(false);
const teletextPage = computed({
  get: () => teletextReader.value.page,
  set: (page: number) => {
    teletextReader.value = { ...teletextReader.value, page };
  },
});
let teletextRegions: GridRegion[] = [];
const teletextFocusedRegionId = ref<string | null>(null);
let teletextPointerStart: { x: number; y: number } | null = null;
let teletextClockTimer: number | null = null;
const teletextOnline = ref(typeof navigator === "undefined" || navigator.onLine);
const teletextImageInput = ref<HTMLInputElement>();
type TeletextMode = "reader" | "graphics";
type TeletextGraphicsTool =
  | "paint"
  | "erase"
  | "line"
  | "rectangle"
  | "fill"
  | "select"
  | "stamp";
const TELETEXT_GRAPHICS_TOOLS: TeletextGraphicsTool[] = [
  "paint",
  "erase",
  "line",
  "rectangle",
  "fill",
  "select",
  "stamp",
];
const teletextMode = ref<TeletextMode>("reader");
const teletextGraphicsTool = ref<TeletextGraphicsTool>("paint");
const teletextGraphicsColour = ref(6);
let teletextGraphicsBuffer: GridBuffer | null = null;
let teletextGraphicsEditor: GridEditor | null = null;
let teletextGraphicsWorkingBuffer: GridBuffer | null = null;
let teletextGraphicsStart: MosaicPoint | null = null;
const teletextGraphicsSelection = ref<MosaicRect | null>(null);
let teletextGraphicsClipboard: MosaicStamp | null = null;
const teletextNamedStamps = ref<NamedMosaicStamp[]>([
  ...BUILTIN_MOSAIC_STAMPS.map((stamp) => ({ ...stamp, pixels: [...stamp.pixels] })),
]);
const teletextSelectedStampId = ref<string | null>(null);
let teletextCustomStampCount = 0;
const teletextGraphicsHistoryTick = ref(0);
const teletextGraphicsCanUndo = computed(() => {
  void teletextGraphicsHistoryTick.value;
  return teletextGraphicsEditor?.canUndo ?? false;
});
const teletextGraphicsCanRedo = computed(() => {
  void teletextGraphicsHistoryTick.value;
  return teletextGraphicsEditor?.canRedo ?? false;
});

// Note: TELETEXT_FASTEXT, VaultDoc, VaultLibrary, PUBLIC_LIBRARY_DEFS,
// DOCS_PER_LIST_PAGE, MAX_DOCS_PER_LIBRARY, DOC_PAGE_OFFSET, DOC_SCREEN_LINES
// are imported from @/grid-core/teletext.

const vaultLibraries = ref<VaultLibrary[]>([]);
const vaultLoaded = ref(false);
const vaultError = ref<string | null>(null);
/** path → full file content, cached after first read. */
const vaultDocCache = new Map<string, string>();

/** Library that owns a given page number (by hundred-block). */
const currentTeletextLibrary = (page: number): VaultLibrary | undefined =>
  gridcoreLibraryForPage(page, vaultLibraries.value);

/** Rotating subpage index (0-based) within the current page. */
const teletextSubpage = computed({
  get: () => teletextReader.value.subpage,
  set: (subpage: number) => {
    teletextReader.value = { ...teletextReader.value, subpage };
  },
});
/** Tick counter for subpage auto-rotation. */
let teletextTick = 0;

const currentDocScreens = (doc: VaultDoc): string[][] =>
  docScreens(doc, vaultDocCache);

/** Fetch one library source's document list. */
async function fetchVaultSource(source: string): Promise<VaultDoc[]> {
  const res = await fetch(
    `${UCORE_API}/api/library/search?q=*&source=${encodeURIComponent(source)}&limit=400`,
  );
  return readLibrarySearchResponse(res, source);
}

/** Fetch the published vault index and group docs into libraries. */
async function loadVaultContent(): Promise<void> {
  vaultLoaded.value = false;
  teletextReader.value = setTeletextStatus(
    teletextReader.value,
    teletextOnline.value ? "loading" : "offline",
    teletextOnline.value ? "Loading published content" : "Network unavailable",
  );
  renderTeletextPage();
  if (!teletextOnline.value) {
    vaultError.value = "offline";
    vaultLoaded.value = true;
    renderTeletextPage();
    return;
  }
  try {
    const sources = new Set(PUBLIC_LIBRARY_DEFS.map((def) => def.source));
    const fetched = new Map<string, VaultDoc[]>();
    await Promise.all(
      Array.from(sources).map(async (source) => {
        fetched.set(source, await fetchVaultSource(source));
      }),
    );
    vaultLibraries.value = buildTeletextLibraries(fetched);
    vaultError.value = null;
    teletextReader.value = setTeletextStatus(teletextReader.value, "ready");
  } catch (e) {
    vaultError.value = e instanceof Error ? e.message : String(e);
    teletextReader.value = setTeletextStatus(
      teletextReader.value,
      "error",
      vaultError.value,
    );
  } finally {
    vaultLoaded.value = true;
  }
  renderTeletextPage();
}

function updateTeletextConnectivity(): void {
  teletextOnline.value = navigator.onLine;
  if (!teletextOnline.value) {
    teletextReader.value = setTeletextStatus(
      teletextReader.value,
      "offline",
      "Network unavailable",
    );
    renderTeletextPage();
  } else if (teletextReader.value.status === "offline") {
    void loadVaultContent();
  }
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
  const lib = currentTeletextLibrary(page);
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
  if (teletextMode.value === "graphics") {
    if (!teletextGraphicsEditor) {
      teletextGraphicsEditor = new GridEditor(createBuffer(c, r));
    }
    if (!teletextGraphicsBuffer) teletextGraphicsBuffer = teletextGraphicsEditor.buffer;
    const display = cloneBuffer(teletextGraphicsBuffer);
    const selection = teletextGraphicsSelection.value;
    if (selection) {
      const left = Math.floor(selection.x / 2);
      const right = Math.floor((selection.x + selection.width - 1) / 2);
      const top = Math.floor(selection.y / 3);
      const bottom = Math.floor((selection.y + selection.height - 1) / 3);
      for (let row = top; row <= bottom; row++) {
        for (let col = left; col <= right; col++) {
          const cell = display[row]?.[col];
          if (cell) display[row][col] = { ...cell, fg: cell.bg, bg: cell.fg, bold: true };
        }
      }
    }
    activeCanvas.setBuffer(display);
    gridContainer.value?.setAttribute(
      "aria-label",
      `Teletext graphics editor, ${teletextGraphicsTool.value} tool`,
    );
    return;
  }
  const page = teletextPage.value;
  const clock = gridcoreCeefaxClock();

  const content = gridcoreTeletextContent(page, {
    vaultLibraries: vaultLibraries.value,
    vaultLoaded: vaultLoaded.value,
    vaultError: vaultError.value,
    vaultDocCache,
    teletextSubpage: teletextSubpage.value,
  });
  teletextRegions = teletextReaderRegions(
    content.lines,
    c,
    r,
    TELETEXT_FASTEXT,
  );
  let buf = renderReaderTeletextPage(page, content, {
    cols: c,
    rows: r,
    clock,
    subpage: teletextSubpage.value,
  });

  // Row r-1 — status bar (blue): page, channel, subpage, clock.
  const subpages = content.subpages ?? 1;
  const entryLabel = teletextEntryLabel(teletextReader.value);
  const stateLabel =
    teletextReader.value.status === "loading"
      ? "LOADING"
      : teletextReader.value.status === "offline"
        ? "OFFLINE"
        : teletextReader.value.status === "error"
          ? "RETRY R"
          : "";
  const subLabel =
    entryLabel ||
    (subpages > 1
      ? `${teletextSubpage.value + 1}/${subpages}`
      : stateLabel || `P${page}`);
  buf = writeString(buf, 12, r - 1, subLabel, 7, 4);

  const focused = teletextRegions.find(
    (region) => region.id === teletextFocusedRegionId.value,
  );
  if (focused) {
    const latticeWidth = registerDotsW(TALL_CELL);
    const latticeHeight = registerDotsH(TALL_CELL);
    const startCol = Math.floor(focused.bounds.x / latticeWidth);
    const endCol = Math.ceil(
      (focused.bounds.x + focused.bounds.width) / latticeWidth,
    );
    const startRow = Math.floor(focused.bounds.y / latticeHeight);
    const endRow = Math.ceil(
      (focused.bounds.y + focused.bounds.height) / latticeHeight,
    );
    for (let row = startRow; row < endRow && row < r; row++) {
      for (let col = startCol; col < endCol && col < c; col++) {
        const cell = buf[row]?.[col];
        if (cell) buf[row][col] = { ...cell, fg: cell.bg, bg: cell.fg, bold: true };
      }
    }
    gridContainer.value?.setAttribute(
      "aria-label",
      `${currentTitle.value} viewport, ${focused.label}`,
    );
  } else {
    gridContainer.value?.setAttribute(
      "aria-label",
      `${currentTitle.value} viewport`,
    );
  }

  activeCanvas.setBuffer(buf);
}

function setTeletextMode(mode: TeletextMode): void {
  teletextMode.value = mode;
  teletextFocusedRegionId.value = null;
  renderTeletextPage();
}

function clearTeletextGraphic(): void {
  const cfg = tabConfigs.teletext;
  if (!teletextGraphicsEditor) {
    teletextGraphicsEditor = new GridEditor(createBuffer(cfg.cols, cfg.rows));
  } else {
    teletextGraphicsEditor.replace(createBuffer(cfg.cols, cfg.rows));
  }
  teletextGraphicsBuffer = teletextGraphicsEditor.buffer;
  teletextGraphicsSelection.value = null;
  teletextGraphicsHistoryTick.value++;
  renderTeletextPage();
}

function copyTeletextGraphicSelection(): void {
  if (!teletextGraphicsSelection.value || !teletextGraphicsBuffer) return;
  teletextGraphicsClipboard = extractMosaicStamp(
    teletextGraphicsBuffer,
    teletextGraphicsSelection.value,
  );
  teletextSelectedStampId.value = null;
  teletextGraphicsTool.value = "stamp";
}

function saveTeletextGraphicStamp(): void {
  if (!teletextGraphicsSelection.value || !teletextGraphicsBuffer) return;
  const stamp = extractMosaicStamp(
    teletextGraphicsBuffer,
    teletextGraphicsSelection.value,
  );
  teletextCustomStampCount++;
  const named = nameMosaicStamp(
    stamp,
    `custom-${teletextCustomStampCount}`,
    `Stamp ${teletextCustomStampCount}`,
  );
  teletextNamedStamps.value.push(named);
  teletextGraphicsClipboard = named;
  teletextSelectedStampId.value = named.id;
  teletextGraphicsTool.value = "stamp";
}

function selectTeletextGraphicStamp(id: string): void {
  const stamp = teletextNamedStamps.value.find((item) => item.id === id);
  if (!stamp) return;
  teletextGraphicsClipboard = stamp;
  teletextSelectedStampId.value = id;
  teletextGraphicsTool.value = "stamp";
}

function cutTeletextGraphicSelection(): void {
  if (!teletextGraphicsSelection.value || !teletextGraphicsEditor) return;
  copyTeletextGraphicSelection();
  const next = teletextGraphicsEditor.buffer;
  clearMosaicRect(
    next,
    teletextGraphicsSelection.value,
    teletextGraphicsColour.value,
  );
  teletextGraphicsEditor.replace(next);
  teletextGraphicsBuffer = teletextGraphicsEditor.buffer;
  teletextGraphicsSelection.value = null;
  teletextGraphicsHistoryTick.value++;
  renderTeletextPage();
}

function undoTeletextGraphic(): void {
  teletextGraphicsEditor?.undo();
  if (teletextGraphicsEditor) teletextGraphicsBuffer = teletextGraphicsEditor.buffer;
  teletextGraphicsHistoryTick.value++;
  renderTeletextPage();
}

function redoTeletextGraphic(): void {
  teletextGraphicsEditor?.redo();
  if (teletextGraphicsEditor) teletextGraphicsBuffer = teletextGraphicsEditor.buffer;
  teletextGraphicsHistoryTick.value++;
  renderTeletextPage();
}

function triggerTeletextImageImport(): void {
  teletextImageInput.value?.click();
}

async function importTeletextImage(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;

  const bitmap = await createImageBitmap(file);
  try {
    const source = document.createElement("canvas");
    source.width = bitmap.width;
    source.height = bitmap.height;
    const context = source.getContext("2d", { willReadFrequently: true });
    if (!context) return;
    context.drawImage(bitmap, 0, 0);
    const image = context.getImageData(0, 0, bitmap.width, bitmap.height);
    const cfg = tabConfigs.teletext;
    const stamp = imageToMosaicStamp(image, {
      width: cfg.cols * 2,
      height: cfg.rows * 3,
    });
    if (!teletextGraphicsEditor) {
      teletextGraphicsEditor = new GridEditor(createBuffer(cfg.cols, cfg.rows));
    }
    const next = teletextGraphicsEditor.buffer;
    stampMosaic(next, { x: 0, y: 0 }, stamp, {
      colour: teletextGraphicsColour.value,
    });
    teletextGraphicsEditor.replace(next);
    teletextGraphicsBuffer = teletextGraphicsEditor.buffer;
    teletextGraphicsHistoryTick.value++;
    renderTeletextPage();
  } finally {
    bitmap.close();
  }
}

function teletextMosaicPoint(event: PointerEvent): MosaicPoint | null {
  if (!activeCanvas) return null;
  const rect = activeCanvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const cfg = tabConfigs.teletext;
  return {
    x: Math.floor(((event.clientX - rect.left) / rect.width) * cfg.cols * 2),
    y: Math.floor(((event.clientY - rect.top) / rect.height) * cfg.rows * 3),
  };
}

function applyTeletextGraphicsTool(from: MosaicPoint, to: MosaicPoint): void {
  const target = teletextGraphicsWorkingBuffer ?? teletextGraphicsBuffer;
  if (!target) return;
  const options = {
    colour: teletextGraphicsColour.value,
    erase: teletextGraphicsTool.value === "erase",
  };
  if (teletextGraphicsTool.value === "line") {
    drawMosaicLine(target, from, to, options);
  } else if (teletextGraphicsTool.value === "rectangle") {
    drawMosaicRectangle(target, from, to, options);
  } else if (teletextGraphicsTool.value === "fill") {
    fillMosaicRegion(target, to, options);
  } else if (teletextGraphicsTool.value === "stamp") {
    if (teletextGraphicsClipboard) {
      stampMosaic(target, to, teletextGraphicsClipboard, options);
    }
  } else {
    drawMosaicLine(target, from, to, options);
  }
  teletextGraphicsBuffer = target;
  renderTeletextPage();
}

function commitTeletextGraphicsStroke(): void {
  if (!teletextGraphicsWorkingBuffer || !teletextGraphicsEditor) return;
  teletextGraphicsEditor.replace(teletextGraphicsWorkingBuffer);
  teletextGraphicsBuffer = teletextGraphicsEditor.buffer;
  teletextGraphicsWorkingBuffer = null;
  teletextGraphicsHistoryTick.value++;
  renderTeletextPage();
}

async function teletextNavigate(page: number) {
  if (page < 100 || page > 899) return;
  teletextReader.value = navigateTeletext(teletextReader.value, page);
  teletextTick = 0;
  renderTeletextPage();
  await fetchDocContentForPage(page);
}

async function teletextGoBack() {
  const previousPage = teletextReader.value.page;
  teletextReader.value = backTeletext(teletextReader.value);
  if (teletextReader.value.page === previousPage) return;
  teletextTick = 0;
  renderTeletextPage();
  await fetchDocContentForPage(teletextReader.value.page);
}

/** Fetch a doc-content page's full file body (cached, once per path). */
async function fetchDocContentForPage(page: number): Promise<void> {
  const lib = currentTeletextLibrary(page);
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

function dispatchTeletextAction(event: GridActionEvent): void {
  const action = event.action;
  if (action.type === "input" && /^\d$/.test(action.text)) {
    const result = enterTeletextDigit(teletextReader.value, action.text);
    teletextReader.value = result.state;
    renderTeletextPage();
    if (result.requestedPage !== null) void teletextNavigate(result.requestedPage);
  } else if (action.type === "page") {
    const page = action.page ?? teletextPage.value + (action.delta ?? 0);
    void teletextNavigate(page);
  } else if (action.type === "fasttext") {
    teletextFastext(action.index);
  } else if (action.type === "back") {
    void teletextGoBack();
  } else if (action.type === "subpage") {
    teletextStepSubpage(action.delta);
  } else if (action.type === "move") {
    const focused = moveGridRegionFocus(
      teletextRegions,
      teletextFocusedRegionId.value,
      action.direction,
    );
    if (focused) {
      teletextFocusedRegionId.value = focused.id;
      renderTeletextPage();
    }
  } else if (action.type === "activate") {
    const focused = teletextRegions.find(
      (region) => region.id === teletextFocusedRegionId.value,
    );
    if (focused) {
      dispatchTeletextAction({ ...event, action: focused.action });
    }
  } else if (action.type === "input" && /^r$/i.test(action.text)) {
    void loadVaultContent();
  }
}

function enterTeletextKeypadDigit(digit: string): void {
  const completesPageNumber = teletextReader.value.entry.length === 2;
  dispatchTeletextAction({
    action: { type: "input", text: digit },
    source: "pointer",
    timestamp: performance.now(),
  });
  if (completesPageNumber) {
    teletextShowKeypad.value = false;
    teletextShowControls.value = false;
  }
}

function startTeletextClock() {
  stopTeletextClock();
  teletextClockTimer = window.setInterval(() => {
    if (activeTab.value !== "teletext") return;
    teletextTick++;
    // Auto-rotate subpages every ~4s for multi-screen docs (Ceefax-style).
    if (teletextTick % 4 === 0) {
      const lib = currentTeletextLibrary(teletextPage.value);
      if (lib) {
        const docIdx = teletextPage.value - lib.page - DOC_PAGE_OFFSET;
        if (docIdx >= 0 && docIdx < lib.docs.length) {
          const total = currentDocScreens(lib.docs[docIdx]).length;
          if (total > 1) {
            teletextReader.value = stepTeletextSubpage(
              teletextReader.value,
              1,
              total,
            );
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
  if (teletextMode.value === "graphics") {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") {
      event.preventDefault();
      if (event.shiftKey) redoTeletextGraphic();
      else undoTeletextGraphic();
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "c") {
      event.preventDefault();
      copyTeletextGraphicSelection();
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "x") {
      event.preventDefault();
      cutTeletextGraphicSelection();
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "v") {
      event.preventDefault();
      if (teletextGraphicsClipboard) teletextGraphicsTool.value = "stamp";
      return;
    }
    const tools: Record<string, TeletextGraphicsTool> = {
      p: "paint",
      e: "erase",
      l: "line",
      r: "rectangle",
      f: "fill",
      s: "select",
      v: "stamp",
    };
    if (event.key === "Escape") {
      event.preventDefault();
      setTeletextMode("reader");
      return;
    }
    const tool = tools[event.key.toLowerCase()];
    if (tool) {
      event.preventDefault();
      teletextGraphicsTool.value = tool;
    }
    return;
  }
  if (/^F[1-4]$/.test(event.key)) {
    event.preventDefault();
    dispatchTeletextAction({
      action: { type: "fasttext", index: Number(event.key.slice(1)) - 1 },
      source: "keyboard",
      timestamp: event.timeStamp,
    });
  } else if (event.key === "b" || event.key === "B") {
    event.preventDefault();
    dispatchTeletextAction({
      action: { type: "back" },
      source: "keyboard",
      timestamp: event.timeStamp,
    });
  } else if (event.key === "." || event.key === "n" || event.key === "N") {
    event.preventDefault();
    dispatchTeletextAction({
      action: { type: "subpage", delta: 1 },
      source: "keyboard",
      timestamp: event.timeStamp,
    });
  } else if (event.key === "," || event.key === "p" || event.key === "P") {
    event.preventDefault();
    dispatchTeletextAction({
      action: { type: "subpage", delta: -1 },
      source: "keyboard",
      timestamp: event.timeStamp,
    });
  } else {
    const action = actionFromKey(event);
    if (action) {
      event.preventDefault();
      dispatchTeletextAction(action);
    }
  }
}

function teletextLatticePoint(event: PointerEvent) {
  if (!activeCanvas) return null;
  const rect = activeCanvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const cfg = tabConfigs.teletext;
  return {
    x:
    ((event.clientX - rect.left) / rect.width) *
    cfg.cols *
    registerDotsW(TALL_CELL),
    y:
    ((event.clientY - rect.top) / rect.height) *
    cfg.rows *
    registerDotsH(TALL_CELL),
  };
}

function onSharedPointerStart(event: PointerEvent) {
  if (activeTab.value === "terminal") {
    // Pointer and touch both focus the hidden text capture synchronously so
    // mobile browsers can open their software keyboard from a real gesture.
    terminalInputCapture.value?.focus();
    return;
  }
  if (activeTab.value === "layer") return;
  if (activeTab.value !== "teletext") return;
  if (teletextMode.value === "graphics") {
    const point = teletextMosaicPoint(event);
    if (!point) return;
    if (!teletextGraphicsEditor) {
      const cfg = tabConfigs.teletext;
      teletextGraphicsEditor = new GridEditor(createBuffer(cfg.cols, cfg.rows));
    }
    teletextGraphicsWorkingBuffer = teletextGraphicsEditor.buffer;
    teletextGraphicsBuffer = teletextGraphicsWorkingBuffer;
    teletextGraphicsStart = point;
    activeCanvas?.setPointerCapture?.(event.pointerId);
    if (
      teletextGraphicsTool.value === "paint" ||
      teletextGraphicsTool.value === "erase" ||
      teletextGraphicsTool.value === "fill" ||
      teletextGraphicsTool.value === "stamp"
    ) {
      applyTeletextGraphicsTool(point, point);
    }
    event.preventDefault();
    return;
  }
  teletextPointerStart = { x: event.clientX, y: event.clientY };
}

function onSharedPointerMove(event: PointerEvent) {
  if (activeTab.value === "layer") return;
  if (activeTab.value !== "teletext") return;
  if (teletextMode.value === "graphics") {
    if (!teletextGraphicsStart || !event.buttons) return;
    const point = teletextMosaicPoint(event);
    if (!point) return;
    if (
      teletextGraphicsTool.value === "paint" ||
      teletextGraphicsTool.value === "erase"
    ) {
      applyTeletextGraphicsTool(teletextGraphicsStart, point);
      teletextGraphicsStart = point;
    } else if (teletextGraphicsTool.value === "select") {
      teletextGraphicsSelection.value = mosaicRect(
        teletextGraphicsStart,
        point,
      );
      renderTeletextPage();
    } else if (
      teletextGraphicsTool.value === "line" ||
      teletextGraphicsTool.value === "rectangle"
    ) {
      teletextGraphicsWorkingBuffer = teletextGraphicsEditor?.buffer ?? null;
      applyTeletextGraphicsTool(teletextGraphicsStart, point);
    }
    event.preventDefault();
    return;
  }
  if (event.pointerType === "touch") return;
  const point = teletextLatticePoint(event);
  if (!point) return;
  const focused = hitTestGridRegions(teletextRegions, point);
  const nextId = focused?.id ?? null;
  if (teletextFocusedRegionId.value !== nextId) {
    teletextFocusedRegionId.value = nextId;
    renderTeletextPage();
  }
}

function onSharedPointerActivate(event: PointerEvent) {
  if (activeTab.value === "layer") return;
  if (activeTab.value !== "teletext" || !activeCanvas) return;
  if (teletextMode.value === "graphics") {
    const point = teletextMosaicPoint(event);
    if (
      point &&
      teletextGraphicsStart &&
      teletextGraphicsTool.value === "select"
    ) {
      teletextGraphicsSelection.value = mosaicRect(
        teletextGraphicsStart,
        point,
      );
      teletextGraphicsWorkingBuffer = null;
      teletextGraphicsStart = null;
      renderTeletextPage();
      event.preventDefault();
      return;
    }
    if (
      point &&
      teletextGraphicsStart &&
      (teletextGraphicsTool.value === "line" ||
        teletextGraphicsTool.value === "rectangle")
    ) {
      applyTeletextGraphicsTool(teletextGraphicsStart, point);
    }
    teletextGraphicsStart = null;
    commitTeletextGraphicsStroke();
    event.preventDefault();
    return;
  }
  if (event.pointerType === "touch" && teletextPointerStart) {
    const dx = event.clientX - teletextPointerStart.x;
    const dy = event.clientY - teletextPointerStart.y;
    teletextPointerStart = null;
    if (Math.max(Math.abs(dx), Math.abs(dy)) >= 24) {
      const swipe = actionFromSwipe(dx, dy);
      if (swipe) dispatchTeletextAction(swipe);
      return;
    }
  }
  const point = teletextLatticePoint(event);
  if (!point) return;
  const source =
    event.pointerType === "touch"
      ? "touch"
      : event.pointerType === "pen"
        ? "pen"
        : "pointer";
  const focused = hitTestGridRegions(
    teletextRegions,
    point,
    source === "touch" ? 1 : 0,
  );
  if (focused) teletextFocusedRegionId.value = focused.id;
  const action = actionFromPoint(teletextRegions, point.x, point.y, source);
  if (action) {
    event.preventDefault();
    dispatchTeletextAction(action);
  }
}

/** Step the current page's subpage (clamped), for multi-screen docs. */
function teletextStepSubpage(delta: number): void {
  const lib = currentTeletextLibrary(teletextPage.value);
  if (!lib) return;
  const docIdx = teletextPage.value - lib.page - DOC_PAGE_OFFSET;
  if (docIdx < 0 || docIdx >= lib.docs.length) return;
  const total = currentDocScreens(lib.docs[docIdx]).length;
  if (total <= 1) return;
  teletextReader.value = stepTeletextSubpage(
    teletextReader.value,
    delta,
    total,
  );
  teletextTick = 0;
  renderTeletextPage();
}

function onSharedKeydown(event: KeyboardEvent) {
  if (activeTab.value === "teletext") {
    handleTeletextKeydown(event);
  } else if (activeTab.value === "terminal") {
    onTerminalKeydown(event);
  } else if (activeTab.value === "layer" && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") {
    event.preventDefault();
    if (event.shiftKey) redoComposedLayerEdit();
    else undoComposedLayerEdit();
  }
}

/** Keep keyboard focus on the grid viewport when the user clicks the canvas
 *  (the canvas lives inside a shadow root, so a plain click does not focus
 *  the focusable viewport host — this made Terminal input appear dead). */
function focusGridContainer() {
  if (activeTab.value === "terminal") terminalInputCapture.value?.focus();
  else gridContainer.value?.focus();
}

/* ─── Terminal Tab ────────────────────────────────────────────────── */
function terminalWebSocketUrl() {
  const url = new URL("/api/terminal/runtime/ws", UCORE_API);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

function sessionWebSocketUrl() {
  const url = new URL("/api/ucode/runtime/ws", UCORE_API);
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
  const liveContent = ensureTerminalBuffer(); // 40×25
  const timeline = [...terminalScrollback, ...liveContent];
  const maxOffset = Math.max(0, timeline.length - TERMINAL_ROWS);
  terminalScrollOffset = Math.min(terminalScrollOffset, maxOffset);
  const start = Math.max(
    0,
    timeline.length - TERMINAL_ROWS - terminalScrollOffset,
  );
  const content = timeline.slice(start, start + TERMINAL_ROWS);

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
  if (terminalCursorVisible && terminalScrollOffset === 0) {
    const cell = grid[cy][cx];
    // Inverted-video block cursor.
    grid[cy][cx] = { char: cell.char, fg: cell.bg, bg: cell.fg };
  }
  activeCanvas.setBuffer(grid);
}

function terminalScrollLiveBuffer(buffer: GridBuffer): GridBuffer {
  const firstRow = buffer[0]?.map((cell) => ({ ...cell }));
  if (firstRow) {
    terminalScrollback.push(firstRow);
    if (terminalScrollback.length > TERMINAL_SCROLLBACK_LIMIT) {
      terminalScrollback.splice(
        0,
        terminalScrollback.length - TERMINAL_SCROLLBACK_LIMIT,
      );
    }
  }
  terminalScrollOffset = 0;
  return scrollBuffer(buffer, 1);
}

function stepTerminalScrollback(delta: number) {
  const maximum = terminalScrollback.length;
  terminalScrollOffset = Math.max(
    0,
    Math.min(maximum, terminalScrollOffset + delta),
  );
  terminalRender();
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
    buf = terminalScrollLiveBuffer(buf);
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
    buf = terminalScrollLiveBuffer(buf);
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
    buf = terminalScrollLiveBuffer(buf);
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

function terminalClearScreen(clearHistory = false) {
  if (!activeCanvas) return;
  terminalCursorX = 0;
  terminalCursorY = 0;
  terminalBuffer = createBuffer(TERMINAL_COLS, TERMINAL_ROWS);
  if (clearHistory) terminalScrollback = [];
  terminalScrollOffset = 0;
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

function terminalClearDisplayFromCursor() {
  if (!activeCanvas) return;
  const buf = ensureTerminalBuffer();
  for (let row = terminalCursorY; row < TERMINAL_ROWS; row++) {
    const start = row === terminalCursorY ? terminalCursorX : 0;
    for (let col = start; col < TERMINAL_COLS; col++) {
      buf[row][col] = { char: " ", fg: 7, bg: 0 };
    }
  }
  terminalBuffer = buf;
  terminalRender();
}

function handleTerminalControlSequence(params: string, command: string) {
  if (command === "H" || command === "f") {
    const [row = "1", col = "1"] = params.split(";");
    terminalCursorY = Math.min(TERMINAL_ROWS - 1, Math.max(0, Number(row) - 1));
    terminalCursorX = Math.min(TERMINAL_COLS - 1, Math.max(0, Number(col) - 1));
  } else if (command === "J" && (params === "2" || params === "3")) {
    terminalClearScreen(params === "3");
  } else if (command === "J" && (params === "" || params === "0")) {
    terminalClearDisplayFromCursor();
  } else if (command === "K") {
    terminalClearLineFromCursor();
  } else if (command === "n" && params === "6") {
    // VT100 Device Status Report. BBC BASIC Console uses this to discover
    // the cursor location before presenting its immediate-mode prompt.
    sendTerminalInput(`\x1B[${terminalCursorY + 1};${terminalCursorX + 1}R`);
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
  terminalScrollback = [];
  terminalScrollOffset = 0;
  terminalCursorX = 0;
  terminalCursorY = 0;
  terminalBuffer = createBuffer(TERMINAL_COLS, TERMINAL_ROWS);
  terminalRender();
  terminalPrintCentered("**** UCODE GRIDCORE TERMINAL ****", 4, 0);
  terminalPrintCentered("SHELL + BBC BASIC · TYPE BASIC", 7, 0);
  terminalPrintLine("READY.", 4, 0);
  terminalPrintLine("", 7, 0); // line gap before the prompt
  terminalCursorY = 4;
  terminalCursorX = 0;
  terminalAtLineStart = true;
  startTerminalCursorBlink();
}

function loadTerminalRuntime() {
  if (terminalActiveCapsuleId) {
    terminalSnapshot = null;
    terminalClearScreen(true);
    startTerminalCursorBlink();
    connectTerminalRuntime(terminalActiveCapsuleId);
    return;
  }
  const snapshot = terminalSnapshot;
  if (snapshot) {
    terminalBuffer = cloneBuffer(snapshot.buffer);
    terminalScrollback = cloneBuffer(snapshot.scrollback);
    terminalScrollOffset = snapshot.scrollOffset;
    terminalCursorX = snapshot.cursorX;
    terminalCursorY = snapshot.cursorY;
    terminalAtLineStart = snapshot.atLineStart;
    terminalRender();
    startTerminalCursorBlink();
  } else {
    loadTerminalWelcome();
  }
  connectTerminalRuntime(terminalActiveCapsuleId ?? undefined);
}

function saveTerminalView() {
  terminalSnapshot = {
    buffer: cloneBuffer(ensureTerminalBuffer()),
    scrollback: cloneBuffer(terminalScrollback),
    scrollOffset: terminalScrollOffset,
    cursorX: terminalCursorX,
    cursorY: terminalCursorY,
    atLineStart: terminalAtLineStart,
  };
}

function connectTerminalRuntime(capsuleId?: string) {
  if (terminalReconnectTimer !== null) {
    window.clearTimeout(terminalReconnectTimer);
    terminalReconnectTimer = null;
  }
  const requestedKind = capsuleId ? "capsule" : "shell";
  if (
    terminalSocket &&
    terminalSocket.readyState <= WebSocket.OPEN &&
    terminalSessionKind === requestedKind &&
    (!capsuleId || terminalActiveCapsuleId === capsuleId)
  ) return;
  if (terminalSocket) terminalSocket.close(1000, "Changing Terminal session");
  terminalSessionKind = requestedKind;
  terminalActiveCapsuleId = capsuleId ?? null;
  terminalRuntimeState.value = "connecting";
  try {
    terminalSocket = new WebSocket(capsuleId ? sessionWebSocketUrl() : terminalWebSocketUrl());
  } catch (err) {
    terminalRuntimeState.value = "unavailable";
    terminalPrintLine(`Runtime socket unavailable: ${String(err)}`, 1, 0);
    return;
  }
  const socket = terminalSocket;
  socket.addEventListener("open", () => {
    terminalReconnectAttempt = 0;
    terminalRuntimeState.value = "connected";
    if (terminalSessionKind === "capsule" && terminalActiveCapsuleId) {
      socket.send(JSON.stringify({
        protocol: "ucode-session/1",
        type: "start",
        session: "capsule",
        titleId: terminalActiveCapsuleId,
        cols: TERMINAL_COLS,
        rows: TERMINAL_ROWS,
      }));
    }
    if (terminalPendingInput) {
      socket.send(JSON.stringify(
        terminalSessionKind === "capsule"
          ? { protocol: "ucode-session/1", type: "input", channel: "keyboard", data: terminalPendingInput }
          : { type: "input", data: terminalPendingInput },
      ));
      terminalPendingInput = "";
    }
    terminalInputCapture.value?.focus();
  });
  socket.addEventListener("message", (event) => {
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
      else if (payload.type === "state" && payload.session === "capsule" && payload.state === "running")
        terminalRuntimeState.value = "connected";
      else if (payload.type === "error")
        terminalPrintLine(String(payload.message || "Runtime error"), 1, 0);
    } catch (err) {
      terminalPrintLine(`Runtime message error: ${String(err)}`, 1, 0);
    }
  });
  socket.addEventListener("close", () => {
    if (terminalSocket !== socket) return;
    terminalRuntimeState.value = "disconnected";
    terminalSocket = null;
    if (activeTab.value === "terminal") {
      terminalPrintLine("[runtime disconnected; reconnecting…]", 3, 0);
      scheduleTerminalReconnect();
    }
  });
  socket.addEventListener("error", () => {
    terminalRuntimeState.value = "error";
  });
}

function scheduleTerminalReconnect(): void {
  if (activeTab.value !== "terminal" || terminalReconnectTimer !== null) return;
  const delay = Math.min(500 * 2 ** terminalReconnectAttempt, 8_000);
  terminalReconnectAttempt += 1;
  terminalReconnectTimer = window.setTimeout(() => {
    terminalReconnectTimer = null;
    if (activeTab.value === "terminal" && !terminalSocket) {
      connectTerminalRuntime(terminalActiveCapsuleId ?? undefined);
    }
  }, delay);
}

function disconnectTerminalRuntime(reason = "Terminal tab inactive") {
  if (terminalReconnectTimer !== null) {
    window.clearTimeout(terminalReconnectTimer);
    terminalReconnectTimer = null;
  }
  terminalReconnectAttempt = 0;
  stopTerminalCursorBlink();
  terminalRuntimeState.value = "disconnected";
  if (!terminalSocket) return;
  terminalSocket.close(1000, reason);
  terminalSocket = null;
  terminalSessionKind = "shell";
  terminalActiveCapsuleId = null;
}

function sendTerminalInput(data: string) {
  if (!terminalSocket || terminalSocket.readyState !== WebSocket.OPEN) {
    terminalPendingInput = (terminalPendingInput + data).slice(-8192);
    connectTerminalRuntime(terminalActiveCapsuleId ?? undefined);
    return;
  }
  terminalSocket.send(JSON.stringify(
    terminalSessionKind === "capsule"
      ? { protocol: "ucode-session/1", type: "input", channel: "keyboard", data }
      : { type: "input", data },
  ));
}

const TERMINAL_KEY_SEQUENCES: Record<string, string> = {
  ArrowUp: "\x1B[A",
  ArrowDown: "\x1B[B",
  ArrowRight: "\x1B[C",
  ArrowLeft: "\x1B[D",
  Home: "\x1B[H",
  End: "\x1B[F",
  Insert: "\x1B[2~",
  Delete: "\x1B[3~",
};

function onTerminalTextInput(event: Event) {
  const input = event.target as HTMLTextAreaElement;
  if (terminalComposing) return;
  if (input.value) sendTerminalInput(input.value);
  input.value = "";
}

function onTerminalCompositionEnd(event: CompositionEvent) {
  terminalComposing = false;
  const input = event.target as HTMLTextAreaElement;
  const data = input.value || event.data;
  if (data) sendTerminalInput(data);
  input.value = "";
}

function onTerminalKeydown(event: KeyboardEvent) {
  if (activeTab.value !== "terminal") return;
  if (event.metaKey || event.altKey) return;
  if (event.ctrlKey && event.key.length === 1) {
    const code = event.key.toUpperCase().charCodeAt(0);
    if (code >= 64 && code <= 95) {
      event.preventDefault();
      sendTerminalInput(String.fromCharCode(code - 64));
    }
    return;
  }
  if (event.key === "PageUp") {
    event.preventDefault();
    stepTerminalScrollback(TERMINAL_ROWS - 2);
  } else if (event.key === "PageDown") {
    event.preventDefault();
    stepTerminalScrollback(-(TERMINAL_ROWS - 2));
  } else if (event.key === "End" && terminalScrollOffset > 0) {
    event.preventDefault();
    terminalScrollOffset = 0;
    terminalRender();
  } else if (event.key in TERMINAL_KEY_SEQUENCES) {
    event.preventDefault();
    sendTerminalInput(TERMINAL_KEY_SEQUENCES[event.key]);
  } else if (event.key === "Enter") {
    event.preventDefault();
    sendTerminalInput("\r");
  } else if (event.key === "Backspace") {
    event.preventDefault();
    sendTerminalInput("\x7F");
  } else if (event.key === "Tab") {
    event.preventDefault();
    sendTerminalInput("\t");
  } else if (
    event.currentTarget !== terminalInputCapture.value &&
    event.key.length === 1
  ) {
    event.preventDefault();
    sendTerminalInput(event.key);
  }
}

/* ─── Layer Tab ───────────────────────────────────────────────────── */
const worldStack = ref<WorldStackDocument>(createWorldStack());
const worldStackReady = ref(false);
let editingWorldAddress: string | null = null;
const activeWorldAddress = computed(() => worldStack.value.activeAddress);
const worldGrids = computed(() => worldStack.value.grids);

function initializeWorldStack(): void {
  if (worldStackReady.value) return;
  const root = createWorldGrid("L200-5533", "World overview");
  root.buffer = loadLayerMap(worldMapSeed as LayerMap);
  const regional = createWorldGrid(childWorldAddresses(root.address)[0], "Regional map");
  regional.buffer = loadLayerMap(regionMapSeed as LayerMap);
  worldStack.value = {
    format: "ucode-world-stack-v1",
    version: 1,
    cols: WORLD_GRID_COLS,
    rows: WORLD_GRID_ROWS,
    activeAddress: root.address,
    grids: [root, regional],
  };
  worldStackReady.value = true;
}

function activeWorldGrid() {
  return worldStack.value.grids.find((grid) => grid.address === worldStack.value.activeAddress) ?? null;
}

function renderWorldGrid(): void {
  const grid = activeWorldGrid();
  if (activeCanvas && grid) activeCanvas.setBuffer(cloneBuffer(grid.buffer));
}

function selectWorldGrid(address: string): void {
  worldStack.value = { ...worldStack.value, activeAddress: address };
  renderWorldGrid();
}

function addWorldChild(): void {
  const parent = activeWorldGrid();
  if (!parent) return;
  const address = childWorldAddresses(parent.address).find(
    (candidate) => !worldStack.value.grids.some((grid) => grid.address === candidate),
  );
  if (!address) return;
  const child = createWorldGrid(address, `Grid ${address}`);
  worldStack.value = { ...worldStack.value, activeAddress: address, grids: [...worldStack.value.grids, child] };
  renderWorldGrid();
}

function deleteWorldGrid(): void {
  if (worldStack.value.grids.length <= 1) return;
  const grids = worldStack.value.grids.filter((grid) => grid.address !== worldStack.value.activeAddress);
  worldStack.value = { ...worldStack.value, grids, activeAddress: grids[0].address };
  renderWorldGrid();
}

function editWorldGrid(): void {
  const grid = activeWorldGrid();
  if (!grid) return;
  editingWorldAddress = grid.address;
  LAYER_COLS = WORLD_GRID_COLS;
  LAYER_ROWS = WORLD_GRID_ROWS;
  layerCols.value = WORLD_GRID_COLS;
  layerRows.value = WORLD_GRID_ROWS;
  resetGridDocument(grid.buffer, true);
  gridInitialized = true;
  activeTab.value = "grid";
}

/* ─── Layer Map Seeds ──────────────────────────────────────────────── */
const layerMapName = ref<"world" | "moon" | "region">("world");
let layerComposer = new LayerComposer();
let composedLayerInitialized = false;
let layerUndoStack: LayerProjectDocument[] = [];
let layerRedoStack: LayerProjectDocument[] = [];
const layerComposerTick = ref(0);
const selectedComposedLayerId = ref<string | null>(null);
const composedLayers = computed<ComposedLayer[]>(() => {
  void layerComposerTick.value;
  return layerComposer.list();
});
const selectedComposedLayer = computed(() => {
  void layerComposerTick.value;
  return selectedComposedLayerId.value
    ? layerComposer.getLayer(selectedComposedLayerId.value)
    : null;
});
const canMergeComposedLayer = computed(() => {
  const layers = composedLayers.value;
  const index = layers.findIndex(
    (layer) => layer.id === selectedComposedLayerId.value,
  );
  return index > 0;
});

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
  const r = map.seed.rows;
  const c = map.seed.cols;
  const buffers = loadLayerMapBuffers(map.seed);
  layerComposer = new LayerComposer();
  for (const [zIndex, id] of BASELINE_LAYER_NAMES.entries()) {
    const source = map.seed.layers.find((layer) => layer.id === id);
    let buffer = buffers.get(id) ?? createBuffer(c, r);
    if (id === "foreground") {
      buffer = writeString(buffer, 0, r - 1, `${map.seed.name} · ${c}×${r}`, 7, 1);
    }
    const layer = layerComposer.createLayer({
      name: source?.name ?? id[0].toUpperCase() + id.slice(1),
      zIndex,
      buffer,
      visible: source?.visible ?? id === "terrain",
      opacity: source?.opacity ?? 1,
      blendMode: source?.blendMode ?? "normal",
      locked: source?.locked ?? false,
    });
    if (id === "terrain") selectedComposedLayerId.value = layer.id;
  }
  layerComposerTick.value++;
  composedLayerInitialized = true;
  resetComposedLayerHistory();
  renderComposedLayers();
}

function resetComposedLayerHistory(): void {
  layerUndoStack = [];
  layerRedoStack = [];
}

function checkpointComposedLayers(): void {
  layerUndoStack.push(serializeLayerProject(layerComposer, selectedComposedLayerId.value));
  if (layerUndoStack.length > 100) layerUndoStack.shift();
  layerRedoStack = [];
}

function restoreComposedLayerDocument(document: LayerProjectDocument): void {
  const restored = deserializeLayerProject(document);
        layerComposer = restored.composer;
        composedLayerInitialized = true;
  selectedComposedLayerId.value = restored.selectedLayerId;
  renderComposedLayers();
}

function undoComposedLayerEdit(): void {
  const previous = layerUndoStack.pop();
  if (!previous) return;
  layerRedoStack.push(serializeLayerProject(layerComposer, selectedComposedLayerId.value));
  restoreComposedLayerDocument(previous);
}

function redoComposedLayerEdit(): void {
  const next = layerRedoStack.pop();
  if (!next) return;
  layerUndoStack.push(serializeLayerProject(layerComposer, selectedComposedLayerId.value));
  restoreComposedLayerDocument(next);
}

function layerCellPoint(event: PointerEvent): { col: number; row: number } | null {
  if (!activeCanvas) return null;
  const rect = activeCanvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const cfg = tabConfigs.layer;
  return {
    col: Math.max(0, Math.min(cfg.cols - 1, Math.floor(((event.clientX - rect.left) / rect.width) * cfg.cols))),
    row: Math.max(0, Math.min(cfg.rows - 1, Math.floor(((event.clientY - rect.top) / rect.height) * cfg.rows))),
  };
}

function paintSelectedLayer(event: PointerEvent): void {
  const layer = selectedComposedLayer.value;
  const point = layerCellPoint(event);
  if (!layer || !point || layer.locked || !layer.visible) return;
  checkpointComposedLayers();
  const buffer = cloneBuffer(layer.buffer);
  const erase = currentTool.value === "erase";
  buffer[point.row][point.col] = erase
    ? { char: " ", fg: 7, bg: 0 }
    : { char: selectedChar.value || " ", fg: selectedFg.value, bg: selectedBg.value };
  layerComposer.setLayerBuffer(layer.id, buffer);
  renderComposedLayers();
}

function renderComposedLayers(): void {
  if (!activeCanvas) return;
  activeCanvas.setBuffer(layerComposer.compose());
  layerComposerTick.value++;
}

function addComposedLayer(): void {
  checkpointComposedLayers();
  const cfg = tabConfigs.layer;
  const layer = layerComposer.createLayer({
    name: `Layer ${composedLayers.value.length + 1}`,
    cols: cfg.cols,
    rows: cfg.rows,
  });
  selectedComposedLayerId.value = layer.id;
  renderComposedLayers();
}

function duplicateComposedLayer(): void {
  if (!selectedComposedLayerId.value) return;
  checkpointComposedLayers();
  const layer = layerComposer.duplicateLayer(selectedComposedLayerId.value);
  if (layer) selectedComposedLayerId.value = layer.id;
  renderComposedLayers();
}

function deleteComposedLayer(): void {
  if (!selectedComposedLayerId.value || composedLayers.value.length <= 1) return;
  checkpointComposedLayers();
  const current = selectedComposedLayerId.value;
  layerComposer.deleteLayer(current);
  selectedComposedLayerId.value = layerComposer.list().at(-1)?.id ?? null;
  renderComposedLayers();
}

function moveComposedLayer(delta: number): void {
  if (!selectedComposedLayerId.value) return;
  const layers = layerComposer.list();
  const index = layers.findIndex((layer) => layer.id === selectedComposedLayerId.value);
  if (index < 0) return;
  checkpointComposedLayers();
  layerComposer.reorderLayer(selectedComposedLayerId.value, index + delta);
  renderComposedLayers();
}

function toggleComposedLayerVisibility(): void {
  const layer = selectedComposedLayer.value;
  if (!layer) return;
  checkpointComposedLayers();
  layerComposer.setLayerVisibility(layer.id, !layer.visible);
  renderComposedLayers();
}

function toggleComposedLayerLock(): void {
  const layer = selectedComposedLayer.value;
  if (!layer) return;
  checkpointComposedLayers();
  if (layer.locked) layerComposer.unlockLayer(layer.id);
  else layerComposer.lockLayer(layer.id);
  renderComposedLayers();
}

function setComposedLayerBlend(event: Event): void {
  const id = selectedComposedLayerId.value;
  if (!id) return;
  checkpointComposedLayers();
  const blendMode = (event.target as HTMLSelectElement).value as BlendMode;
  layerComposer.setLayerBlendMode(id, blendMode);
  renderComposedLayers();
}

function setComposedLayerOpacity(event: Event): void {
  const id = selectedComposedLayerId.value;
  if (!id) return;
  checkpointComposedLayers();
  const opacity = Number((event.target as HTMLInputElement).value);
  layerComposer.setLayerOpacity(id, opacity);
  renderComposedLayers();
}

function mergeComposedLayerDown(): void {
  const layers = layerComposer.list();
  const index = layers.findIndex(
    (layer) => layer.id === selectedComposedLayerId.value,
  );
  if (index <= 0) return;
  checkpointComposedLayers();
  const merged = layerComposer.mergeLayers(layers[index - 1].id, layers[index].id);
  if (merged) selectedComposedLayerId.value = merged.id;
  renderComposedLayers();
}

function loadLayerDemo() {
  loadLayerMapByName(layerMapName.value);
}

/* ─── Glyph Inspector ─────────────────────────────────────────────── */
const glyphInspectorFont = ref<"pressstart2p" | "bedstead">("pressstart2p");
const glyphCatalogue = ref<CharacterCatalogueEntry[]>([...CHARACTER_CATALOGUE]);
const glyphImportInput = ref<HTMLInputElement>();
const glyphSearch = ref("");
const glyphCategory = ref<CharacterCatalogueCategory>("glyph");
const selectedGlyphEntry = ref<CharacterCatalogueEntry | null>(null);
const glyphLibraryRegister = computed<CharacterRegister>(() => {
  if (activeTab.value === "pixel" || activeTab.value === "grid") return "square";
  if (activeTab.value === "teletext") return "reading";
  return glyphInspectorFont.value === "bedstead" ? "reading" : "square";
});
const glyphAllMatches = computed(() =>
  searchCharacterCatalogue(glyphCatalogue.value, {
    text: glyphSearch.value,
    category: glyphCategory.value,
    ...(activeTab.value === "glyphs" ? {} : { register: glyphLibraryRegister.value }),
  }),
);
const glyphRenderedMatches = computed(() =>
  searchCharacterCatalogue(glyphCatalogue.value, {
    text: glyphSearch.value,
    category: glyphCategory.value,
    register: glyphLibraryRegister.value,
  }),
);

watch([glyphSearch, glyphCategory, glyphLibraryRegister], () => {
  selectedGlyphEntry.value = null;
  if (activeTab.value === "glyphs") loadGlyphInspector();
});

function loadGlyphInspector() {
  if (!activeCanvas) return;
  const cfg = tabConfigs.glyphs;
  const c = cfg.cols; // 16
  const matches = glyphRenderedMatches.value;
  const rows = Math.max(cfg.rows, Math.ceil(matches.length / c) + 1);
  activeCanvas.setAttribute("rows", String(rows));
  let buf = createBuffer(c, rows);
  const label = `${glyphLibraryRegister.value === "square" ? "TERMINAL" : "TELETEXT"} ${glyphCategory.value.toUpperCase()} ${matches.length}`;
  buf = writeString(buf, 0, 0, label.slice(0, c), 6, 0, true);
  let index = 0;
  for (let r = 1; r < rows && index < matches.length; r++) {
    for (let col = 0; col < c && index < matches.length; col++) {
      const item = matches[index++];
      buf[r][col] = {
        char: item.preview,
        fg: item.kind === "emoji" ? 3 : item.kind === "teletext-mosaic" ? 6 : 7,
        bg: 0,
        mosaic: item.kind === "teletext-mosaic",
      };
      if (selectedGlyphEntry.value?.id === item.id) {
        const cell = buf[r][col];
        buf[r][col] = { ...cell, fg: cell.bg, bg: cell.fg, bold: true };
      }
    }
  }
  activeCanvas.setBuffer(buf);
  // Re-fit so switching font re-sizes cells to the new glyph aspect.
  activeCanvas.setAttribute("font", glyphInspectorFont.value);
  nextTick(() => activeCanvas?.refit());
}

function selectGlyphEntry(item: CharacterCatalogueEntry): void {
  selectedGlyphEntry.value = item;
  editSelectedGlyph();
}

function onGlyphCellClick(event: CustomEvent): void {
  if (activeTab.value !== "glyphs") return;
  const { col, row } = event.detail ?? {};
  if (typeof col !== "number" || typeof row !== "number" || row < 1) return;
  selectedGlyphEntry.value =
    glyphRenderedMatches.value[(row - 1) * tabConfigs.glyphs.cols + col] ?? null;
  if (selectedGlyphEntry.value) editSelectedGlyph();
}

function editSelectedGlyph(): void {
  const item = selectedGlyphEntry.value;
  if (!item?.preview) return;
  pixelSymbol.value = item.preview;
  pixelFont.value = glyphInspectorFont.value;
  activeTab.value = "pixel";
  if (item.bitmap) {
    nextTick(() => nextTick(() => loadCatalogueBitmapInPixel(item)));
  }
}

function catalogueBitmapBuffer(
  bitmap: NonNullable<CharacterCatalogueEntry["bitmap"]>,
): ReturnType<typeof createPixelBuffer> {
  const { w, h } = pixelCell.value;
  const buffer = createPixelBuffer(0, w, h);
  const scale = Math.max(1, Math.min(
    Math.floor((w - 2) / bitmap.width),
    Math.floor((h - 2) / bitmap.height),
  ));
  const drawWidth = bitmap.width * scale;
  const drawHeight = bitmap.height * scale;
  const originX = Math.floor((w - drawWidth) / 2);
  const originY = Math.floor((h - drawHeight) / 2);
  bitmap.pixels.forEach((enabled, index) => {
    if (!enabled) return;
    const sourceX = index % bitmap.width;
    const sourceY = Math.floor(index / bitmap.width);
    for (let dy = 0; dy < scale; dy++) for (let dx = 0; dx < scale; dx++) {
      buffer[(originY + sourceY * scale + dy) * w + originX + sourceX * scale + dx] = 7;
    }
  });
  return buffer;
}

function loadCatalogueBitmapInPixel(item: CharacterCatalogueEntry): void {
  if (!item.bitmap) return;
  const { w, h } = pixelCell.value;
  const first = catalogueBitmapBuffer(item.bitmap);
  pixelEditor = new PixelEditor(first, w, h);
  pixelAnimation = new PixelAnimation(first, w, h);
  for (const frame of item.frames?.slice(1) ?? []) {
    pixelAnimation.add(catalogueBitmapBuffer(frame));
  }
  pixelAnimation.select(0);
  pixelFrameTick.value++;
  renderPixelBuffer();
}

function sendSelectedGlyphToGrid(): void {
  const item = selectedGlyphEntry.value;
  if (!item) return;
  selectedChar.value = item.preview;
  currentTool.value = "pencil";
  activeTab.value = "grid";
}

function addSelectedGlyphToLayer(): void {
  const item = selectedGlyphEntry.value;
  if (!item) return;
  activeTab.value = "layer";
  nextTick(() => nextTick(() => {
    const base = layerComposer.list()[0];
    const cols = base?.buffer[0]?.length ?? tabConfigs.layer.cols;
    const rows = base?.buffer.length ?? tabConfigs.layer.rows;
    let buffer = createBuffer(cols, rows);
    buffer = writeString(
      buffer,
      Math.max(0, Math.floor(cols / 2)),
      Math.max(0, Math.floor(rows / 2)),
      item.preview,
      7,
      0,
    );
    checkpointComposedLayers();
    const layer = layerComposer.createLayer({ name: item.label, buffer });
    selectedComposedLayerId.value = layer.id;
    renderComposedLayers();
  }));
}

function exportCharacterCatalogue(): void {
  const catalogueDocument = serializeCharacterCatalogue(glyphCatalogue.value);
  const blob = new Blob([JSON.stringify(catalogueDocument, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "ucode-character-catalogue-v1.json";
  anchor.click();
  URL.revokeObjectURL(url);
}

function importCharacterCatalogue(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const imported = deserializeCharacterCatalogue(JSON.parse(String(reader.result)));
      const merged = new Map(glyphCatalogue.value.map((item) => [item.id, item]));
      for (const item of imported) merged.set(item.id, item);
      glyphCatalogue.value = [...merged.values()];
      loadGlyphInspector();
    } catch (error) {
      console.error("Character catalogue import failed", error);
    }
  };
  reader.readAsText(file);
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
.layer-advanced {
  width: 100%;
  padding: 8px 0;
  border-top: var(--gridcore-border);
  color: var(--gridcore-color-text-muted);
  font-size: var(--gridcore-font-size-xs);
}
.layer-advanced summary {
  cursor: pointer;
  user-select: none;
}
.layer-advanced[open] summary {
  margin-bottom: 8px;
}
.terminal-input-capture {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  opacity: 0;
  pointer-events: none;
  resize: none;
}

/* ─── View-integrated panels and controls ──────────────────────── */
.asset-panel {
  position: absolute;
  inset: 0 0 0 auto;
  z-index: 5;
  width: min(var(--gridcore-sidebar-width), 34vw);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: var(--gridcore-space-xs);
  padding: var(--gridcore-space-md);
  overflow: auto;
  background: var(--gridcore-color-surface);
  border-left: var(--gridcore-border);
}
.surface__body:has(.asset-panel) .surface__canvas {
  margin-right: min(var(--gridcore-sidebar-width), 34vw);
}
.asset-panel__title {
  margin: 0 0 var(--gridcore-space-sm);
  font-size: var(--gridcore-font-size-md);
  color: var(--gridcore-color-text);
}
.asset-panel__section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--gridcore-space-xs);
  padding-bottom: var(--gridcore-space-sm);
  border-bottom: var(--gridcore-border);
}
.asset-panel__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--gridcore-space-xs);
}
.asset-panel__pagination {
  justify-content: space-between;
}
.asset-panel__catalogue-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--gridcore-space-1);
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: var(--gridcore-space-xs);
}
.asset-panel__catalogue-grid .sidebar-char-chip {
  min-height: 32px;
}
.layer-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--gridcore-space-xs);
  width: 100%;
  min-height: 34px;
  padding: var(--gridcore-space-xs) var(--gridcore-space-sm);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  color: var(--gridcore-color-text);
  background: var(--gridcore-color-background-alt);
  cursor: pointer;
  text-align: left;
}
.layer-row.active {
  border-color: var(--gridcore-color-primary);
  background: var(--gridcore-selection-bg);
}
.layer-row__state {
  color: var(--gridcore-color-primary);
}
.layer-row__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.layer-row__meta {
  font-size: var(--gridcore-font-size-xs);
  color: var(--gridcore-color-text-muted);
}
.asset-panel__search,
.asset-panel__select {
  width: 100%;
  min-height: var(--gridcore-control-height);
  padding: 0 var(--gridcore-space-sm);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  color: var(--gridcore-color-text);
  background: var(--gridcore-color-background-alt);
  font: inherit;
}
.viewport-controls {
  position: absolute;
  z-index: 6;
  top: var(--gridcore-space-sm);
  right: var(--gridcore-space-sm);
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--gridcore-space-xs);
  max-width: min(70%, 620px);
  padding: var(--gridcore-space-xs);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  background: color-mix(in srgb, var(--gridcore-color-background-alt) 92%, transparent);
  box-shadow: var(--gridcore-popover-shadow);
}
.teletext-keypad {
  flex-basis: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(2.5rem, 1fr));
  gap: var(--gridcore-space-xs);
  width: min(14rem, 70vw);
}
.teletext-keypad__display {
  grid-column: 1 / -1;
  min-height: var(--gridcore-control-height);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gridcore-color-primary);
  background: #000;
  border: var(--gridcore-border);
  font-family: var(--gridcore-font-family-mono);
  letter-spacing: 0.12em;
}
.teletext-keypad__key {
  min-height: 2.5rem;
  color: var(--gridcore-color-text);
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-sm);
  cursor: pointer;
  font: var(--gridcore-font-weight-semibold) var(--gridcore-font-size-md)
    var(--gridcore-font-family-mono);
}
.teletext-keypad__key:hover,
.teletext-keypad__key:focus-visible {
  color: var(--gridcore-color-primary);
  border-color: var(--gridcore-color-primary);
}
.teletext-keypad__key--wide {
  grid-column: span 2;
}
.teletext-graphics-controls {
  flex-basis: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--gridcore-space-sm);
  width: min(30rem, 76vw);
  max-height: min(30rem, 72vh);
  overflow-y: auto;
  padding-top: var(--gridcore-space-xs);
  border-top: var(--gridcore-border);
}
.teletext-control-group {
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-xs);
  min-width: 0;
}
.teletext-control-group--stamps {
  grid-column: 1 / -1;
}
.teletext-control-group__title {
  color: var(--gridcore-color-text-muted);
  font: var(--gridcore-font-weight-semibold) var(--gridcore-font-size-xs)
    var(--gridcore-font-family-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.teletext-control-group__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--gridcore-space-xs);
}
.teletext-control-group__grid--actions {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.teletext-colour-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(2.5rem, 1fr));
  gap: var(--gridcore-space-xs);
}
.teletext-colour-key {
  min-height: 2.5rem;
  border: 2px solid transparent;
  border-radius: var(--gridcore-radius-sm);
  cursor: pointer;
}
.teletext-colour-key.active {
  border-color: #fff;
  box-shadow: 0 0 0 2px var(--gridcore-color-primary);
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

@media (max-width: 50em) {
  .asset-panel {
    width: min(42vw, 240px);
  }
  .surface__body:has(.asset-panel) .surface__canvas {
    margin-right: min(42vw, 240px);
  }
  .viewport-controls {
    max-width: calc(100% - (2 * var(--gridcore-space-sm)));
  }
  .teletext-graphics-controls {
    grid-template-columns: 1fr;
    width: min(18rem, 82vw);
  }
  .teletext-control-group--stamps {
    grid-column: auto;
  }
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
  touch-action: none;
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
  touch-action: none;
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
.sidebar-section--glyphs {
  /* The character catalogue is the final, expandable editor section. */
  min-height: 10rem;
}
.sidebar-tool-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--gridcore-control-inline-gap);
}
.sidebar-tool-grid--frames {
  max-height: 7rem;
  overflow-y: auto;
}
.sidebar-action-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--gridcore-sidebar-font-btn-gap);
}
.sidebar-meta,
.sidebar-range {
  font: var(--gridcore-font-size-xs) var(--gridcore-font-family-mono);
  color: var(--gridcore-color-text-muted);
}

/* ─── Software Library ─────────────────────────────────────────── */
.software-library-layout {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  overflow: hidden;
  background: var(--gridcore-color-background);
}
.software-library-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: clamp(1rem, 3vw, 2.5rem);
}
.software-library-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--gridcore-space-md);
  margin-bottom: var(--gridcore-space-lg);
}
.software-library-header h2 {
  margin: var(--gridcore-space-xs) 0 0;
  color: var(--gridcore-color-text);
  font-size: clamp(1.25rem, 2.5vw, 2rem);
}
.software-library-kicker {
  color: var(--gridcore-color-primary);
  font: var(--gridcore-font-weight-semibold) var(--gridcore-font-size-xs)
    var(--gridcore-font-family-mono);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.software-library-refresh {
  flex: 0 0 auto;
}
.software-library-filters {
  display: grid;
  grid-template-columns: minmax(12rem, 1fr) minmax(9rem, 0.4fr) auto;
  align-items: end;
  gap: var(--gridcore-space-sm);
  margin-bottom: var(--gridcore-space-md);
}
.software-library-filters label {
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-xs);
  color: var(--gridcore-color-text-muted);
  font: var(--gridcore-font-size-xs) var(--gridcore-font-family-mono);
  text-transform: uppercase;
}
.software-library-filters input,
.software-library-filters select {
  min-height: 2.35rem;
  padding: 0 var(--gridcore-space-sm);
  color: var(--gridcore-color-text);
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  border-radius: 0;
  font: var(--gridcore-font-size-sm) var(--gridcore-font-family-mono);
}
.software-library-result-count {
  padding-bottom: 0.6rem;
  color: var(--gridcore-color-text-muted);
  font: var(--gridcore-font-size-xs) var(--gridcore-font-family-mono);
  white-space: nowrap;
}
.software-library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 17rem), 1fr));
  gap: var(--gridcore-space-md);
}
.software-title-card {
  min-height: 12rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--gridcore-space-xs);
  padding: var(--gridcore-space-md);
  color: var(--gridcore-color-text);
  text-align: left;
  background: var(--gridcore-color-surface);
  border: var(--gridcore-border);
  border-radius: var(--gridcore-radius-md);
  cursor: pointer;
}
.software-title-card:hover,
.software-title-card:focus-visible,
.software-title-card.selected {
  border-color: var(--gridcore-color-primary);
  outline: none;
}
.software-title-card.selected {
  box-shadow: inset 0 0 0 1px var(--gridcore-color-primary);
}
.software-title-card strong {
  font-size: var(--gridcore-font-size-lg);
}
.software-title-card p {
  margin: var(--gridcore-space-xs) 0;
  color: var(--gridcore-color-text-muted);
  line-height: 1.45;
}
.software-title-card__status {
  padding: 0.15rem 0.45rem;
  color: var(--gridcore-color-text-muted);
  border: var(--gridcore-border);
  font: var(--gridcore-font-size-xs) var(--gridcore-font-family-mono);
  text-transform: uppercase;
}
.software-title-card__status--configured,
.software-title-card__status--verified,
.software-title-card__status--enhanced,
.software-title-card__status--release {
  color: var(--gridcore-color-primary);
  border-color: var(--gridcore-color-primary);
}
.software-title-card__meta,
.software-library-message {
  color: var(--gridcore-color-text-muted);
  font: var(--gridcore-font-size-xs) var(--gridcore-font-family-mono);
}
.software-library-message--error {
  color: var(--gridcore-color-danger, #e35d6a);
}
.software-library-sidebar__title {
  margin: 0;
  color: var(--gridcore-color-text);
}
.software-capsule-facts {
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-xs);
  margin: 0;
}
.software-capsule-facts div {
  display: flex;
  justify-content: space-between;
  gap: var(--gridcore-space-sm);
  border-bottom: var(--gridcore-border);
  padding-bottom: var(--gridcore-space-xs);
}
.software-capsule-facts dt {
  color: var(--gridcore-color-text-muted);
}
.software-capsule-facts dd {
  margin: 0;
  color: var(--gridcore-color-text);
  text-align: right;
}
.software-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--gridcore-space-xs);
}
.software-chip {
  padding: 0.2rem 0.4rem;
  color: var(--gridcore-color-text-muted);
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  font-size: var(--gridcore-font-size-xs);
}
.software-library-launch {
  margin-top: auto;
}
.software-library-lifecycle {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--gridcore-space-xs);
}
.software-library-details {
  padding: var(--gridcore-space-sm) 0;
}
.software-library-details summary {
  color: var(--gridcore-color-text);
  cursor: pointer;
  font: var(--gridcore-font-size-xs) var(--gridcore-font-family-mono);
  text-transform: uppercase;
}
.software-library-details pre {
  max-height: 18rem;
  margin: var(--gridcore-space-sm) 0 0;
  padding: var(--gridcore-space-sm);
  overflow: auto;
  color: var(--gridcore-color-text-muted);
  background: var(--gridcore-color-background-alt);
  border: var(--gridcore-border);
  font: 0.7rem/1.45 var(--gridcore-font-family-mono);
  white-space: pre-wrap;
}
.software-library-details article + article {
  margin-top: var(--gridcore-space-md);
}
.software-evidence-hash {
  display: block;
  margin-top: var(--gridcore-space-sm);
  overflow-wrap: anywhere;
  color: var(--gridcore-color-text-muted);
  font-size: 0.65rem;
}
.software-media-guide p,
.software-media-guide ol {
  color: var(--gridcore-color-text-muted);
  font-size: var(--gridcore-font-size-xs);
  line-height: 1.45;
}
@media (max-width: 50em) {
  .software-library-layout {
    flex-direction: column;
    overflow-y: auto;
  }
  .software-library-main {
    flex: none;
    overflow: visible;
  }
  .software-library-sidebar {
    width: 100%;
    max-height: none;
    border-left: none;
    border-top: var(--gridcore-border);
  }
  .software-library-filters {
    grid-template-columns: 1fr;
  }
  .software-library-result-count {
    padding-bottom: 0;
  }
}
.sidebar-range {
  display: flex;
  flex-direction: column;
  gap: var(--gridcore-space-xs);
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
.catalogue-bitmap {
  display: grid;
  width: 18px;
  height: 18px;
  gap: 0;
}
.catalogue-bitmap i {
  min-width: 0;
  min-height: 0;
  background: transparent;
}
.catalogue-bitmap i.active {
  background: currentColor;
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
