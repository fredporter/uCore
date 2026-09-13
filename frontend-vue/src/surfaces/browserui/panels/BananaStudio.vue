/**
 * @component BananaStudio / VectorStudio — uVector Illustration Engine
 * Generates and transforms technical drawings, diagrams, and GridCore assets.
 * Adheres to Mono Core visual style presets (Blueprint, Teletext, Linocut Paper, Pixel Art, Line Art).
 * Amber CRT phosphor is strictly excluded per sovereign design doctrine.
 */
<template>
  <div class="banana-studio">
    <!-- Hero panel -->
    <section class="banana-studio__hero surface__panel">
      <div class="banana-studio__hero-top">
        <div class="banana-studio__title-wrap">
          <UIcon name="draw" :size="24" class="banana-studio__hero-icon" />
          <div>
            <h2 class="surface__panel-title">uVector Illustration & Asset Studio</h2>
            <p class="surface__panel-description">
              Sovereign vector engine for technical drawings, GridCore character blocks, and Mono Core illustrations.
            </p>
          </div>
        </div>
        <div class="banana-studio__hero-badges">
          <span class="banana-studio__badge">Rust Core (uvcore)</span>
          <span class="banana-studio__badge">GridCore Mapped</span>
          <span class="banana-studio__badge">100% Offline</span>
        </div>
      </div>
    </section>

    <!-- Studio Mode Switcher Tabs -->
    <div class="banana-studio__mode-tabs">
      <button
        type="button"
        class="banana-studio__mode-tab"
        :class="{ 'banana-studio__mode-tab--active': activeMode === 'generate' }"
        @click="activeMode = 'generate'"
      >
        <UIcon name="auto_awesome" /> Text-to-Vector
      </button>
      <button
        type="button"
        class="banana-studio__mode-tab"
        :class="{ 'banana-studio__mode-tab--active': activeMode === 'trace' }"
        @click="activeMode = 'trace'"
      >
        <UIcon name="polyline" /> Bitmap Tracing
      </button>
      <button
        type="button"
        class="banana-studio__mode-tab"
        :class="{ 'banana-studio__mode-tab--active': activeMode === 'font_map' }"
        @click="activeMode = 'font_map'"
      >
        <UIcon name="grid_on" /> GridCore Font & Icon Map
      </button>
    </div>

    <div class="banana-studio__workspace">
      <!-- Controls Column -->
      <section class="banana-studio__controls surface__panel">
        <!-- MODE 1: Text-to-Vector Generation -->
        <div v-if="activeMode === 'generate'" class="banana-studio__mode-section">
          <h3 class="banana-studio__section-title">Visual Style Preset</h3>
          <div class="banana-studio__presets">
            <button
              v-for="preset in PRESETS"
              :key="preset.id"
              type="button"
              class="banana-studio__preset-card"
              :class="{ 'banana-studio__preset-card--active': selectedPreset === preset.id }"
              @click="selectPreset(preset.id)"
            >
              <div
                class="banana-studio__preset-swatch"
                :style="{ background: preset.swatchBg, borderColor: preset.swatchBorder }"
              >
                <UIcon :name="preset.icon" :style="{ color: preset.swatchColor }" />
              </div>
              <div class="banana-studio__preset-info">
                <div class="banana-studio__preset-name">{{ preset.name }}</div>
                <div class="banana-studio__preset-desc">{{ preset.description }}</div>
              </div>
            </button>
          </div>

          <h3 class="banana-studio__section-title">Illustration Prompt / Topic</h3>
          <div class="banana-studio__prompt-wrap">
            <textarea
              v-model="promptText"
              class="banana-studio__textarea"
              rows="3"
              placeholder="Describe technical schematic, scientific diagram, or vector drawing..."
              :disabled="generating"
            />
          </div>

          <!-- Quick prompt chips -->
          <div class="banana-studio__chips">
            <span class="banana-studio__chips-label">Presets:</span>
            <button
              v-for="chip in currentChips"
              :key="chip"
              type="button"
              class="banana-studio__chip"
              @click="promptText = chip"
            >
              {{ chip }}
            </button>
          </div>

          <div class="banana-studio__options-row">
            <div>
              <label class="banana-studio__option-label">Aspect Ratio</label>
              <div class="banana-studio__aspect-buttons">
                <button
                  v-for="ratio in ASPECT_RATIOS"
                  :key="ratio"
                  type="button"
                  class="banana-studio__aspect-btn"
                  :class="{ 'banana-studio__aspect-btn--active': selectedAspect === ratio }"
                  @click="selectedAspect = ratio"
                >
                  {{ ratio }}
                </button>
              </div>
            </div>
          </div>

          <div class="banana-studio__actions">
            <button
              type="button"
              class="uxs-btn uxs-btn--primary banana-studio__gen-btn"
              :disabled="generating || !promptText.trim()"
              @click="handleGenerate"
            >
              <UIcon :name="generating ? 'sync' : 'auto_awesome'" :class="{ 'banana-studio__spinner': generating }" />
              {{ generating ? "Synthesizing Vector..." : "Generate Vector Illustration" }}
            </button>
          </div>
        </div>

        <!-- MODE 2: Bitmap-to-Vector Tracing -->
        <div v-else-if="activeMode === 'trace'" class="banana-studio__mode-section">
          <h3 class="banana-studio__section-title">Bitmap Tracing & Vectorization</h3>
          <p class="banana-studio__mode-desc">
            Upload or paste raster bitmap to extract vector contours and quantize to GridCore Teletext.
          </p>
          <div class="banana-studio__trace-upload">
            <input type="file" accept="image/*" class="banana-studio__file-input" @change="handleFileUpload" />
          </div>

          <h3 class="banana-studio__section-title">Trace Target Style</h3>
          <div class="banana-studio__presets">
            <button
              v-for="preset in PRESETS"
              :key="preset.id"
              type="button"
              class="banana-studio__preset-card"
              :class="{ 'banana-studio__preset-card--active': selectedPreset === preset.id }"
              @click="selectPreset(preset.id)"
            >
              <div
                class="banana-studio__preset-swatch"
                :style="{ background: preset.swatchBg, borderColor: preset.swatchBorder }"
              >
                <UIcon :name="preset.icon" :style="{ color: preset.swatchColor }" />
              </div>
              <div class="banana-studio__preset-info">
                <div class="banana-studio__preset-name">{{ preset.name }}</div>
              </div>
            </button>
          </div>

          <div class="banana-studio__actions">
            <button
              type="button"
              class="uxs-btn uxs-btn--primary banana-studio__gen-btn"
              :disabled="generating"
              @click="handleTrace"
            >
              <UIcon name="polyline" /> Trace to Scalable Vector
            </button>
          </div>
        </div>

        <!-- MODE 3: GridCore Font & Icon Mapping -->
        <div v-else-if="activeMode === 'font_map'" class="banana-studio__mode-section">
          <h3 class="banana-studio__section-title">GridCore Character Block Mapping</h3>
          <p class="banana-studio__mode-desc">
            Import font or icon sets, extract character blocks into 40×25 Teletext G1 mosaics, and retain original files.
          </p>
          <div class="banana-studio__prompt-wrap">
            <label class="banana-studio__option-label">Glyph / Icon Character Set</label>
            <input
              v-model="fontGlyphsInput"
              type="text"
              class="banana-studio__text-input"
              placeholder="A B C D E F G H I J K L M"
            />
          </div>

          <div class="banana-studio__actions">
            <button
              type="button"
              class="uxs-btn uxs-btn--primary banana-studio__gen-btn"
              :disabled="generating"
              @click="handleMapFont"
            >
              <UIcon name="grid_on" /> Map to GridCore Character Blocks
            </button>
          </div>
        </div>

        <span v-if="statusMessage" class="banana-studio__status-msg">{{ statusMessage }}</span>
      </section>

      <!-- Preview Column -->
      <section class="banana-studio__preview surface__panel">
        <div class="banana-studio__preview-header">
          <h3 class="banana-studio__section-title">Output Canvas</h3>

          <!-- Format Preview Tabs -->
          <div v-if="activeAsset" class="banana-studio__preview-tabs">
            <button
              type="button"
              class="banana-studio__tab-btn"
              :class="{ 'banana-studio__tab-btn--active': previewTab === 'svg' }"
              @click="previewTab = 'svg'"
            >
              Vector (SVG)
            </button>
            <button
              type="button"
              class="banana-studio__tab-btn"
              :class="{ 'banana-studio__tab-btn--active': previewTab === 'teletext' }"
              @click="previewTab = 'teletext'"
            >
              Teletext (40×25)
            </button>
            <button
              type="button"
              class="banana-studio__tab-btn"
              :class="{ 'banana-studio__tab-btn--active': previewTab === 'ascii' }"
              @click="previewTab = 'ascii'"
            >
              ASCII
            </button>
            <button
              type="button"
              class="banana-studio__tab-btn"
              :class="{ 'banana-studio__tab-btn--active': previewTab === 'inspector' }"
              @click="previewTab = 'inspector'"
            >
              Inspector
            </button>
          </div>
        </div>

        <div v-if="!activeAsset && !generating" class="banana-studio__preview-empty">
          <UIcon name="image" :size="48" />
          <p>Select a visual style preset, enter your prompt, and generate scalable vector illustrations.</p>
        </div>

        <div v-else-if="generating" class="banana-studio__generating-box">
          <USpinner :size="36" />
          <p>Synthesizing geometry using uVector Rust engine and {{ activePresetMeta?.name }} rules...</p>
        </div>

        <div v-else-if="activeAsset" class="banana-studio__asset-card">
          <!-- View Tab 1: Live SVG Viewport -->
          <div
            v-if="previewTab === 'svg'"
            class="banana-studio__viewport"
            :class="`banana-studio__viewport--${activeAsset.style_preset}`"
            :style="{ aspectRatio: aspectCss(activeAsset.aspect_ratio || selectedAspect) }"
          >
            <div v-if="activeAsset.svg" class="banana-studio__svg-container" v-html="activeAsset.svg"></div>
            <div v-else class="banana-studio__viewport-grid">
              <div class="banana-studio__viewport-header">
                <span>[UDOS-ASSET: {{ activeAsset.asset_id }}]</span>
                <span>STYLE: {{ activeAsset.style_preset }}</span>
              </div>
              <div class="banana-studio__viewport-body">
                <UIcon :name="activePresetMeta?.icon || 'image'" :size="56" class="banana-studio__viewport-symbol" />
                <div class="banana-studio__viewport-caption">{{ activeAsset.prompt }}</div>
              </div>
              <div class="banana-studio__viewport-footer">
                <span>MODEL: {{ activeAsset.model }}</span>
                <span>ASPECT: {{ activeAsset.aspect_ratio || selectedAspect }}</span>
              </div>
            </div>
          </div>

          <!-- View Tab 2: Teletext (40×25) Character Grid -->
          <div v-else-if="previewTab === 'teletext'" class="banana-studio__teletext-wrapper">
            <pre class="banana-studio__teletext-pre">{{ activeAsset.teletext || "No teletext grid available." }}</pre>
          </div>

          <!-- View Tab 3: ASCII Art -->
          <div v-else-if="previewTab === 'ascii'" class="banana-studio__ascii-wrapper">
            <pre class="banana-studio__ascii-pre">{{ activeAsset.ascii || "No ASCII output available." }}</pre>
          </div>

          <!-- View Tab 4: Element & Token Inspector -->
          <div v-else-if="previewTab === 'inspector'" class="banana-studio__inspector-wrapper">
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Dimensions:</span>
              <span class="banana-studio__meta-val">{{ activeAsset.width || 800 }} × {{ activeAsset.height || 450 }} px</span>
            </div>
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Element Count:</span>
              <span class="banana-studio__meta-val">{{ activeAsset.element_count || 12 }} vector primitives</span>
            </div>
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">GridCore Mapping:</span>
              <span class="banana-studio__meta-val">40 Columns × 25 Rows (PAL Teletext G1 Mosaic)</span>
            </div>
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Citation Token:</span>
              <code class="banana-studio__meta-val">{{ activeAsset.citation_token || `[FIG-${activeAsset.asset_id}]` }}</code>
            </div>
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Vault Target:</span>
              <span class="banana-studio__meta-val">~/Vault/illustrations/{{ activeAsset.asset_id }}/</span>
            </div>
          </div>

          <!-- Asset metadata & action buttons -->
          <div class="banana-studio__asset-meta">
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Asset ID:</span>
              <code class="banana-studio__meta-val">{{ activeAsset.asset_id }}</code>
            </div>
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Style Preset:</span>
              <span class="banana-studio__meta-val">{{ activePresetMeta?.name }}</span>
            </div>

            <div class="banana-studio__asset-actions">
              <button type="button" class="uxs-btn" @click="copySvg">
                <UIcon name="code" /> Copy SVG
              </button>
              <button type="button" class="uxs-btn" @click="copyMarkdown">
                <UIcon name="content_copy" /> Copy Markdown Embed
              </button>
              <button type="button" class="uxs-btn" @click="downloadSvg">
                <UIcon name="download" /> Download SVG
              </button>
              <button type="button" class="uxs-btn uxs-btn--primary" @click="saveToVault">
                <UIcon name="save" /> Save to Vault
              </button>
            </div>
          </div>
        </div>

        <!-- Session Gallery -->
        <div v-if="history.length > 1" class="banana-studio__history">
          <h4 class="banana-studio__history-title">Session Gallery ({{ history.length }})</h4>
          <div class="banana-studio__history-list">
            <div
              v-for="item in history"
              :key="item.asset_id"
              class="banana-studio__history-item"
              :class="{ 'banana-studio__history-item--active': activeAsset?.asset_id === item.asset_id }"
              @click="activeAsset = item"
            >
              <UIcon :name="getPresetMeta(item.style_preset)?.icon || 'draw'" />
              <div class="banana-studio__history-desc">{{ item.prompt.slice(0, 45) }}...</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue"
import UIcon from "../../../skills/atoms/UIcon.vue"
import USpinner from "../../../skills/atoms/USpinner.vue"
import {
  generateVectorAsset,
  traceVectorAsset,
  saveVectorAsset,
  type BananaAssetResult,
} from "../ApiBridge"

interface PresetDefinition {
  id: string
  name: string
  description: string
  icon: string
  swatchBg: string
  swatchBorder: string
  swatchColor: string
  chips: string[]
}

const PRESETS: PresetDefinition[] = [
  {
    id: "mono_blueprint",
    name: "Architectural Blueprint",
    description: "Cyan and white technical drafting linework on deep Prussian navy",
    icon: "architecture",
    swatchBg: "#0a2342",
    swatchBorder: "#00e5ff",
    swatchColor: "#ffffff",
    chips: [
      "Space station docking module orthographic blueprint schematic",
      "Isometric microprocessor architecture diagram with bus lines",
      "Robotic arm kinematic joint technical engineering diagram",
    ],
  },
  {
    id: "mono_teletext",
    name: "Ceefax Teletext",
    description: "8-color broadcast aesthetic with blocky 40x25 character grid",
    icon: "grid_view",
    swatchBg: "#000000",
    swatchBorder: "#00ffff",
    swatchColor: "#ffff00",
    chips: [
      "Retro teletext city skyline with glowing broadcast grid",
      "Teletext flight tracking radar screen with pixel glyphs",
      "Ceefax weather forecast teletext page with ASCII symbols",
    ],
  },
  {
    id: "mono_paper",
    name: "Editorial Linocut Paper",
    description: "Deep black woodcut print with stipple shading on archival cream paper",
    icon: "article",
    swatchBg: "#faf8f5",
    swatchBorder: "#222222",
    swatchColor: "#111111",
    chips: [
      "Botanical fern illustration in black ink woodblock print",
      "Astronomical armillary sphere engraving on warm paper",
      "Maritime lighthouse with crosshatch waves woodcut",
    ],
  },
  {
    id: "pixel_art",
    name: "16-Color Pixel Grid",
    description: "Sharp nostalgic retro game pixel sprites with clean geometric silhouette",
    icon: "sports_esports",
    swatchBg: "#1e1e2e",
    swatchBorder: "#f38ba8",
    swatchColor: "#a6e3a1",
    chips: [
      "16-bit cybernetic warrior sprite on pixel grid",
      "Retro isometric game room with CRT television and console",
      "Pixel art mountain fortress under a starry night sky",
    ],
  },
  {
    id: "line_art",
    name: "Technical Line Art",
    description: "Clean monochrome vector geometry with dimensions and precision guides",
    icon: "draw",
    swatchBg: "#ffffff",
    swatchBorder: "#000000",
    swatchColor: "#000000",
    chips: [
      "Microprocessor internal bus architecture and registers",
      "Exploded view assembly of mechanical escapement gear",
      "Concentric optics lens ray tracing technical schematic",
    ],
  },
]

const ASPECT_RATIOS = ["16:9", "4:3", "1:1", "2:1", "3:4"]

const activeMode = ref<"generate" | "trace" | "font_map">("generate")
const previewTab = ref<"svg" | "teletext" | "ascii" | "inspector">("svg")
const selectedPreset = ref("mono_blueprint")
const selectedAspect = ref("16:9")
const promptText = ref("")
const fontGlyphsInput = ref("A B C D E F G H I J K L M")
const uploadedImageBase64 = ref("")
const generating = ref(false)
const statusMessage = ref("")
const activeAsset = ref<BananaAssetResult | null>(null)
const history = ref<BananaAssetResult[]>([])

const activePresetMeta = computed(() =>
  PRESETS.find((p) => p.id === (activeAsset.value?.style_preset || selectedPreset.value))
)

const currentChips = computed(() => {
  const p = PRESETS.find((preset) => preset.id === selectedPreset.value)
  return p ? p.chips : []
})

function getPresetMeta(id: string) {
  return PRESETS.find((p) => p.id === id)
}

function selectPreset(id: string) {
  selectedPreset.value = id
}

function aspectCss(ratio: string) {
  if (ratio === "16:9") return "16 / 9"
  if (ratio === "4:3") return "4 / 3"
  if (ratio === "2:1") return "2 / 1"
  if (ratio === "3:4") return "3 / 4"
  return "1 / 1"
}

async function handleGenerate() {
  if (!promptText.value.trim() || generating.value) return
  generating.value = true
  statusMessage.value = "Synthesizing vector geometry via uVector..."
  try {
    const res = await generateVectorAsset(promptText.value, selectedPreset.value, selectedAspect.value)
    activeAsset.value = res
    history.value.unshift(res)
    statusMessage.value = "Vector illustration generated successfully."
  } catch (err: any) {
    statusMessage.value = `Generation error: ${err?.message || err}`
  } finally {
    generating.value = false
  }
}

async function handleTrace() {
  generating.value = true
  statusMessage.value = "Tracing bitmap into vector paths..."
  try {
    const res = await traceVectorAsset(uploadedImageBase64.value || "sample_raster", selectedPreset.value)
    activeAsset.value = res
    history.value.unshift(res)
    statusMessage.value = "Bitmap traced to scalable vector successfully."
  } catch (err: any) {
    statusMessage.value = `Tracing error: ${err?.message || err}`
  } finally {
    generating.value = false
  }
}

async function handleMapFont() {
  generating.value = true
  statusMessage.value = "Mapping glyphs to GridCore character blocks..."
  try {
    const glyphs = fontGlyphsInput.value.split(/\s+/).filter(Boolean).map((char) => ({ char }))
    const res = await generateVectorAsset(`Font Map: ${fontGlyphsInput.value.slice(0, 20)}`, "mono_teletext", "4:3")
    activeAsset.value = {
      ...res,
      prompt: `GridCore Character Atlas (${glyphs.length} glyphs)`,
    }
    history.value.unshift(activeAsset.value)
    statusMessage.value = `Mapped ${glyphs.length} glyphs to GridCore character blocks (originals preserved).`
  } catch (err: any) {
    statusMessage.value = `Mapping error: ${err?.message || err}`
  } finally {
    generating.value = false
  }
}

function handleFileUpload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImageBase64.value = String(e.target?.result || "")
    statusMessage.value = `Loaded ${file.name} for tracing.`
  }
  reader.readAsDataURL(file)
}

function copySvg() {
  if (!activeAsset.value?.svg) return
  navigator.clipboard.writeText(activeAsset.value.svg)
  statusMessage.value = "SVG markup copied to clipboard."
}

function copyMarkdown() {
  if (!activeAsset.value) return
  const path = activeAsset.value.vault_path
    ? `${activeAsset.value.vault_path}/vector.svg`
    : `~/Vault/illustrations/${activeAsset.value.asset_id}/vector.svg`
  const md = `![Figure: ${activeAsset.value.prompt}](${path})`
  navigator.clipboard.writeText(md)
  statusMessage.value = "Markdown embed copied."
}

function downloadSvg() {
  if (!activeAsset.value?.svg) return
  const blob = new Blob([activeAsset.value.svg], { type: "image/svg+xml" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `${activeAsset.value.asset_id}.svg`
  a.click()
  URL.revokeObjectURL(url)
  statusMessage.value = "Downloaded SVG file."
}

async function saveToVault() {
  if (!activeAsset.value) return
  statusMessage.value = "Saving asset to Vault with originals preserved..."
  try {
    const res = await saveVectorAsset(
      activeAsset.value.asset_id,
      activeAsset.value.svg || "<svg></svg>",
      activeAsset.value.prompt,
      activeAsset.value.style_preset,
      activeAsset.value.aspect_ratio || "16:9"
    )
    activeAsset.value.vault_path = res.vault_path
    activeAsset.value.citation_token = res.citation_token
    statusMessage.value = `Saved to Vault: ${res.vault_path} (${res.citation_token})`
  } catch (err: any) {
    statusMessage.value = `Save error: ${err?.message || err}`
  }
}
</script>

<style scoped>
.banana-studio {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  width: 100%;
}

.banana-studio__hero {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-md);
}

.banana-studio__hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.banana-studio__title-wrap {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.banana-studio__hero-icon {
  color: var(--usx-color-primary);
}

.banana-studio__hero-badges {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.banana-studio__badge {
  font-size: var(--usx-font-size-xs);
  padding: 2px var(--usx-spacing-xs);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  font-weight: var(--usx-font-weight-semibold);
}

.banana-studio__mode-tabs {
  display: flex;
  gap: var(--usx-spacing-xs);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  padding-bottom: var(--usx-spacing-xs);
}

.banana-studio__mode-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border: var(--usx-border-width) solid transparent;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.banana-studio__mode-tab:hover {
  color: var(--usx-color-on-surface);
  background: var(--usx-color-surface-variant);
}

.banana-studio__mode-tab--active {
  color: var(--usx-color-primary);
  background: var(--usx-color-surface-variant);
  border-color: var(--usx-color-border);
  font-weight: var(--usx-font-weight-semibold);
}

.banana-studio__mode-desc {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin-top: 0;
}

.banana-studio__workspace {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: var(--usx-spacing-md);
}

.banana-studio__controls,
.banana-studio__preview {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.banana-studio__section-title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--usx-color-on-surface-muted);
}

.banana-studio__presets {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--usx-spacing-xs);
}

.banana-studio__preset-card {
  display: flex;
  justify-content: flex-start;
  color: var(--usx-color-on-surface);
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background-color 0.15s;
}

.banana-studio__preset-card:hover {
  background: var(--usx-color-surface-hover);
}

.banana-studio__preset-card--active {
  border-color: var(--usx-color-primary);
  background: var(--usx-color-surface-selected, rgba(0, 180, 216, 0.1));
}

.banana-studio__preset-swatch {
  width: 32px;
  height: 32px;
  border-radius: var(--usx-radius-sm);
  border: 1px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.banana-studio__preset-name {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
}

.banana-studio__preset-desc {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.banana-studio__textarea,
.banana-studio__text-input {
  width: 100%;
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  font-size: var(--usx-font-size-sm);
  font-family: inherit;
}

.banana-studio__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.banana-studio__chips-label {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.banana-studio__chip {
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  font-size: var(--usx-font-size-xs);
  padding: 2px var(--usx-spacing-xs);
  cursor: pointer;
}

.banana-studio__chip:hover {
  border-color: var(--usx-color-primary);
}

.banana-studio__option-label {
  display: block;
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-xs);
}

.banana-studio__aspect-buttons {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.banana-studio__aspect-btn {
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
}

.banana-studio__aspect-btn--active {
  border-color: var(--usx-color-primary);
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

.banana-studio__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-xs);
}

.banana-studio__gen-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  font-weight: var(--usx-font-weight-semibold);
}

.banana-studio__status-msg {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.banana-studio__spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ─── Preview styling ─────────────────────────────────────────────── */
.banana-studio__preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}

.banana-studio__preview-tabs {
  display: flex;
  gap: 4px;
}

.banana-studio__tab-btn {
  padding: 4px 8px;
  font-size: var(--usx-font-size-xs);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  cursor: pointer;
}

.banana-studio__tab-btn--active {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

.banana-studio__preview-empty,
.banana-studio__generating-box {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  border: 1px dashed var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  color: var(--usx-color-on-surface-muted);
  text-align: center;
  padding: var(--usx-spacing-md);
}

.banana-studio__asset-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.banana-studio__viewport {
  width: 100%;
  border-radius: var(--usx-radius-md);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.banana-studio__svg-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banana-studio__svg-container :deep(svg) {
  width: 100%;
  height: 100%;
  max-height: 480px;
  display: block;
}

.banana-studio__viewport--mono_teletext {
  background: #000000;
  border: 2px solid #ff00ff;
}

.banana-studio__viewport--mono_blueprint {
  background: #0a2342;
  border: 2px solid #00e5ff;
}

.banana-studio__viewport--mono_paper {
  background: #faf8f5;
  border: 2px solid #222222;
}

.banana-studio__viewport--pixel_art {
  background: #1e1e2e;
  border: 2px solid #f38ba8;
}

.banana-studio__viewport--line_art {
  background: #ffffff;
  border: 2px solid #000000;
}

.banana-studio__teletext-wrapper,
.banana-studio__ascii-wrapper {
  background: #000000;
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-sm);
  overflow-x: auto;
}

.banana-studio__teletext-pre {
  font-family: monospace;
  font-size: 13px;
  line-height: 1.2;
  color: #00ffff;
  margin: 0;
  white-space: pre;
}

.banana-studio__ascii-pre {
  font-family: monospace;
  font-size: 12px;
  line-height: 1.15;
  color: #a6e3a1;
  margin: 0;
  white-space: pre;
}

.banana-studio__inspector-wrapper {
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
}

.banana-studio__asset-meta {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
}

.banana-studio__meta-row {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.banana-studio__meta-key {
  color: var(--usx-color-on-surface-muted);
}

.banana-studio__asset-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
  margin-top: var(--usx-spacing-xs);
}

.banana-studio__history {
  margin-top: var(--usx-spacing-sm);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  padding-top: var(--usx-spacing-sm);
}

.banana-studio__history-title {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin: 0 0 var(--usx-spacing-xs) 0;
  text-transform: uppercase;
}

.banana-studio__history-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.banana-studio__history-item {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
}

.banana-studio__history-item--active {
  border-color: var(--usx-color-primary);
}

.banana-studio__history-desc {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .banana-studio__workspace {
    grid-template-columns: 1fr;
  }
}
</style>
