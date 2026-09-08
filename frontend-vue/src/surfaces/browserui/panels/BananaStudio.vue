/**
 * @component BananaStudio — Nano Banana / Imagen 3 Asset Generation Studio
 * Adheres to Mono Core visual style presets (Teletext, Blueprint, Linocut Paper).
 */
<template>
  <div class="banana-studio">
    <!-- Hero panel -->
    <section class="banana-studio__hero surface__panel">
      <div class="banana-studio__hero-top">
        <div class="banana-studio__title-wrap">
          <UIcon name="palette" :size="24" class="banana-studio__hero-icon" />
          <div>
            <h2 class="surface__panel-title">Nano Banana Asset Studio</h2>
            <p class="surface__panel-description">
              Generate high-fidelity visual assets powered by Imagen 3, constrained to uDOS Mono Core design aesthetics.
            </p>
          </div>
        </div>
        <div class="banana-studio__hero-badges">
          <span class="banana-studio__badge">Imagen 3</span>
          <span class="banana-studio__badge">Mono Core</span>
          <span class="banana-studio__badge">uGrid Mapped</span>
        </div>
      </div>
    </section>

    <div class="banana-studio__workspace">
      <!-- Controls Column -->
      <section class="banana-studio__controls surface__panel">
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
            <div class="banana-studio__preset-swatch" :style="{ background: preset.swatchBg, borderColor: preset.swatchBorder }">
              <UIcon :name="preset.icon" :style="{ color: preset.swatchColor }" />
            </div>
            <div class="banana-studio__preset-info">
              <div class="banana-studio__preset-name">{{ preset.name }}</div>
              <div class="banana-studio__preset-desc">{{ preset.description }}</div>
            </div>
          </button>
        </div>

        <h3 class="banana-studio__section-title">Generation Prompt</h3>
        <div class="banana-studio__prompt-wrap">
          <textarea
            v-model="promptText"
            class="banana-studio__textarea"
            rows="3"
            placeholder="Describe the visual asset to generate..."
            :disabled="generating"
          />
        </div>

        <!-- Quick prompt chips -->
        <div class="banana-studio__chips">
          <span class="banana-studio__chips-label">Quick prompts:</span>
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
            {{ generating ? "Generating Asset via Imagen 3..." : "Generate Asset" }}
          </button>
          <span v-if="statusMessage" class="banana-studio__status-msg">{{ statusMessage }}</span>
        </div>
      </section>

      <!-- Preview Column -->
      <section class="banana-studio__preview surface__panel">
        <h3 class="banana-studio__section-title">Generated Asset Preview</h3>

        <div v-if="!activeAsset && !generating" class="banana-studio__preview-empty">
          <UIcon name="image" :size="48" />
          <p>Choose a style preset, enter a prompt, and click Generate.</p>
        </div>

        <div v-else-if="generating" class="banana-studio__generating-box">
          <USpinner :size="36" />
          <p>Synthesizing visual asset using Imagen 3 and {{ activePresetMeta?.name }} rules...</p>
        </div>

        <div v-else-if="activeAsset" class="banana-studio__asset-card">
          <!-- Thematic asset viewport -->
          <div
            class="banana-studio__viewport"
            :class="`banana-studio__viewport--${activeAsset.style_preset}`"
            :style="{ aspectRatio: aspectCss(activeAsset.aspect_ratio || selectedAspect) }"
          >
            <div class="banana-studio__viewport-grid">
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

          <!-- Asset metadata & actions -->
          <div class="banana-studio__asset-meta">
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Asset ID:</span>
              <code class="banana-studio__meta-val">{{ activeAsset.asset_id }}</code>
            </div>
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Style Preset:</span>
              <span class="banana-studio__meta-val">{{ activePresetMeta?.name }}</span>
            </div>
            <div class="banana-studio__meta-row">
              <span class="banana-studio__meta-key">Model:</span>
              <span class="banana-studio__meta-val">{{ activeAsset.model }}</span>
            </div>

            <div class="banana-studio__asset-actions">
              <button type="button" class="uxs-btn" @click="copyPrompt">
                <UIcon name="content_copy" /> Copy Prompt
              </button>
              <button type="button" class="uxs-btn" @click="copyMarkdown">
                <UIcon name="code" /> Copy Markdown Embed
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
              <UIcon :name="getPresetMeta(item.style_preset)?.icon || 'image'" />
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
import { generateBananaAsset, type BananaAssetResult } from "../ApiBridge"


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
]

const ASPECT_RATIOS = ["1:1", "16:9", "4:3", "9:16"]

const selectedPreset = ref("mono_teletext")
const selectedAspect = ref("4:3")
const promptText = ref("")
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
  if (id === "mono_blueprint") selectedAspect.value = "16:9"
  else if (id === "mono_paper" || id === "pixel_art") selectedAspect.value = "1:1"
  else selectedAspect.value = "4:3"
}

function aspectCss(ratio: string) {
  if (ratio === "16:9") return "16 / 9"
  if (ratio === "4:3") return "4 / 3"
  if (ratio === "9:16") return "9 / 16"
  return "1 / 1"
}

async function handleGenerate() {
  if (!promptText.value.trim() || generating.value) return
  generating.value = true
  statusMessage.value = "Synthesizing asset via Imagen 3..."
  try {
    const res = await generateBananaAsset(promptText.value, selectedPreset.value, selectedAspect.value)
    activeAsset.value = res
    history.value.unshift(res)
    statusMessage.value = "Asset generated successfully."
  } catch (err: any) {
    statusMessage.value = `Generation error: ${err?.message || err}`
  } finally {
    generating.value = false
  }
}

function copyPrompt() {
  if (!activeAsset.value) return
  navigator.clipboard.writeText(activeAsset.value.prompt)
  statusMessage.value = "Prompt copied to clipboard."
}

function copyMarkdown() {
  if (!activeAsset.value) return
  const md = `![${activeAsset.value.prompt}](asset://${activeAsset.value.asset_id})`
  navigator.clipboard.writeText(md)
  statusMessage.value = "Markdown embed copied."
}

function saveToVault() {
  if (!activeAsset.value) return
  statusMessage.value = `Asset ${activeAsset.value.asset_id} queued for Vault binder.`
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

.banana-studio__textarea {
  width: 100%;
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  font-size: var(--usx-font-size-sm);
  font-family: inherit;
  resize: vertical;
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
  padding: var(--usx-spacing-md);
  position: relative;
}

.banana-studio__viewport--mono_teletext {
  background: #000000;
  color: #00ffff;
  border: 2px solid #ff00ff;
  font-family: monospace;
}

.banana-studio__viewport--mono_blueprint {
  background: #0a2342;
  color: #00e5ff;
  border: 2px solid #00e5ff;
  font-family: monospace;
}

.banana-studio__viewport--mono_amber {
  background: #120b00;
  color: #ffb000;
  border: 2px solid #ff8000;
  font-family: monospace;
  box-shadow: inset 0 0 20px rgba(255, 176, 0, 0.2);
}

.banana-studio__viewport--mono_paper {
  background: #faf8f5;
  color: #111111;
  border: 2px solid #222222;
  font-family: serif;
}

.banana-studio__viewport--pixel_art {
  background: #1e1e2e;
  color: #a6e3a1;
  border: 2px solid #f38ba8;
  font-family: monospace;
}

.banana-studio__viewport-grid {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.banana-studio__viewport-header,
.banana-studio__viewport-footer {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  letter-spacing: 0.05em;
  opacity: 0.8;
}

.banana-studio__viewport-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  text-align: center;
  padding: var(--usx-spacing-sm);
}

.banana-studio__viewport-caption {
  font-size: var(--usx-font-size-sm);
  max-width: 80%;
  line-height: 1.3;
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
