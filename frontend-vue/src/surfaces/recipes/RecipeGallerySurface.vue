<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  SAMPLE_TASK_LIST,
  SAMPLE_PROSE_DOCUMENT,
  SAMPLE_CARD_MATRIX,
  SAMPLE_SETTINGS_FORM,
  SAMPLE_TELETEXT,
  SAMPLE_TERMINAL,
  type AnyRecipe,
} from '../../recipes/recipes'

import TaskListRecipeView from '../../recipes/components/TaskListRecipeView.vue'
import ProseDocumentRecipeView from '../../recipes/components/ProseDocumentRecipeView.vue'
import CardMatrixRecipeView from '../../recipes/components/CardMatrixRecipeView.vue'
import SettingsFormRecipeView from '../../recipes/components/SettingsFormRecipeView.vue'
import TeletextRecipeView from '../../recipes/components/TeletextRecipeView.vue'
import TerminalRecipeView from '../../recipes/components/TerminalRecipeView.vue'

// Active recipe state
const selectedRecipeKey = ref<string>('task-list')
const selectedTheme = ref<string>('theme-dark')
const selectedViewport = ref<string>('100%')
const showJson = ref<boolean>(false)

const allRecipes: Record<string, AnyRecipe> = {
  'task-list': SAMPLE_TASK_LIST,
  'prose-document': SAMPLE_PROSE_DOCUMENT,
  'card-matrix': SAMPLE_CARD_MATRIX,
  'settings-form': SAMPLE_SETTINGS_FORM,
  'teletext-mode7': SAMPLE_TELETEXT,
  'terminal-ansi': SAMPLE_TERMINAL,
}

const currentRecipe = computed(() => allRecipes[selectedRecipeKey.value])

const currentParadigm = computed(() => currentRecipe.value.paradigm)
</script>

<template>
  <div class="gallery-page" :class="[selectedTheme]">
    <!-- Top Gallery Control Bar -->
    <header class="gallery-topbar">
      <div class="gallery-brand">
        <span class="material-symbols-outlined gallery-logo-icon">style</span>
        <div>
          <h1 class="gallery-title">USX & GridCore Recipe Gallery</h1>
          <span class="gallery-subtitle">Sprint 4B Predictable Surface System Showroom</span>
        </div>
      </div>

      <!-- Controls: Theme, Viewport & JSON -->
      <div class="gallery-controls">
        <!-- Viewport Switcher -->
        <div class="control-group">
          <span class="control-label">Viewport:</span>
          <div class="segmented-btn-group">
            <button
              class="seg-btn"
              :class="{ active: selectedViewport === '360px' }"
              @click="selectedViewport = '360px'"
              title="Mobile (360px)"
            >
              <span class="material-symbols-outlined">smartphone</span>
            </button>
            <button
              class="seg-btn"
              :class="{ active: selectedViewport === '768px' }"
              @click="selectedViewport = '768px'"
              title="Tablet (768px)"
            >
              <span class="material-symbols-outlined">tablet</span>
            </button>
            <button
              class="seg-btn"
              :class="{ active: selectedViewport === '1200px' }"
              @click="selectedViewport = '1200px'"
              title="Desktop (1200px)"
            >
              <span class="material-symbols-outlined">desktop_windows</span>
            </button>
            <button
              class="seg-btn"
              :class="{ active: selectedViewport === '100%' }"
              @click="selectedViewport = '100%'"
              title="Fluid (100%)"
            >
              <span class="material-symbols-outlined">fit_screen</span>
            </button>
          </div>
        </div>

        <!-- Theme Switcher -->
        <div class="control-group">
          <span class="control-label">Theme:</span>
          <select v-model="selectedTheme" class="control-select">
            <option value="theme-dark">Dark (Material 3)</option>
            <option value="theme-light">Light (Material 3)</option>
            <option value="theme-c64">C64 Retro</option>
            <option value="theme-teletext">Teletext Matrix</option>
            <option value="theme-high-contrast">High Contrast</option>
          </select>
        </div>

        <!-- JSON Inspector Toggle -->
        <button
          class="json-toggle-btn"
          :class="{ active: showJson }"
          @click="showJson = !showJson"
        >
          <span class="material-symbols-outlined">data_object</span>
          <span>Recipe JSON</span>
        </button>
      </div>
    </header>

    <!-- Recipe Navigation Tabs -->
    <nav class="recipe-nav-tabs">
      <div class="paradigm-group">
        <span class="paradigm-label">USX (DOM / Material 3 + Prose):</span>
        <button
          class="recipe-tab-btn"
          :class="{ active: selectedRecipeKey === 'task-list' }"
          @click="selectedRecipeKey = 'task-list'"
        >
          <span class="material-symbols-outlined">checklist</span>
          <span>Task List</span>
        </button>
        <button
          class="recipe-tab-btn"
          :class="{ active: selectedRecipeKey === 'prose-document' }"
          @click="selectedRecipeKey = 'prose-document'"
        >
          <span class="material-symbols-outlined">article</span>
          <span>Prose Document</span>
        </button>
        <button
          class="recipe-tab-btn"
          :class="{ active: selectedRecipeKey === 'card-matrix' }"
          @click="selectedRecipeKey = 'card-matrix'"
        >
          <span class="material-symbols-outlined">grid_view</span>
          <span>Card Matrix</span>
        </button>
        <button
          class="recipe-tab-btn"
          :class="{ active: selectedRecipeKey === 'settings-form' }"
          @click="selectedRecipeKey = 'settings-form'"
        >
          <span class="material-symbols-outlined">tune</span>
          <span>Settings Form</span>
        </button>
      </div>

      <div class="paradigm-group">
        <span class="paradigm-label">GridCore (Matrix / Retro & CLI):</span>
        <button
          class="recipe-tab-btn tab-retro"
          :class="{ active: selectedRecipeKey === 'teletext-mode7' }"
          @click="selectedRecipeKey = 'teletext-mode7'"
        >
          <span class="material-symbols-outlined">tv</span>
          <span>Teletext Mode 7</span>
        </button>
        <button
          class="recipe-tab-btn tab-retro"
          :class="{ active: selectedRecipeKey === 'terminal-ansi' }"
          @click="selectedRecipeKey = 'terminal-ansi'"
        >
          <span class="material-symbols-outlined">terminal</span>
          <span>Terminal ANSI</span>
        </button>
      </div>
    </nav>

    <!-- Main Inspection Stage -->
    <main class="gallery-stage">
      <!-- Simulated Viewport Frame -->
      <div
        class="viewport-frame"
        :style="{ maxWidth: selectedViewport }"
      >
        <div class="viewport-canvas">
          <!-- Render Selected Component -->
          <TaskListRecipeView
            v-if="selectedRecipeKey === 'task-list'"
            :recipe="currentRecipe as any"
          />
          <ProseDocumentRecipeView
            v-else-if="selectedRecipeKey === 'prose-document'"
            :recipe="currentRecipe as any"
          />
          <CardMatrixRecipeView
            v-else-if="selectedRecipeKey === 'card-matrix'"
            :recipe="currentRecipe as any"
          />
          <SettingsFormRecipeView
            v-else-if="selectedRecipeKey === 'settings-form'"
            :recipe="currentRecipe as any"
          />
          <TeletextRecipeView
            v-else-if="selectedRecipeKey === 'teletext-mode7'"
            :recipe="currentRecipe as any"
          />
          <TerminalRecipeView
            v-else-if="selectedRecipeKey === 'terminal-ansi'"
            :recipe="currentRecipe as any"
          />
        </div>
      </div>

      <!-- JSON Inspector Drawer -->
      <aside v-if="showJson" class="json-inspector-drawer">
        <div class="json-drawer-header">
          <h3>Declarative Recipe Payload</h3>
          <span class="paradigm-pill">{{ currentParadigm.toUpperCase() }}</span>
        </div>
        <pre class="json-content"><code>{{ JSON.stringify(currentRecipe, null, 2) }}</code></pre>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.gallery-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--usx-color-background, #111318);
  color: var(--usx-color-on-surface, #e2e2e6);
  font-family: var(--usx-font-family-sans, sans-serif);
}

/* Theme classes for live switching */
.theme-light {
  --usx-color-background: #f8f9fa;
  --usx-color-surface: #ffffff;
  --usx-color-surface-container: #edeef2;
  --usx-color-surface-container-high: #e2e3e7;
  --usx-color-on-surface: #191c20;
  --usx-color-on-surface-variant: #44474e;
  --usx-color-primary: #0b57d0;
  --usx-color-outline: #74777f;
  --usx-color-outline-variant: rgba(0, 0, 0, 0.12);
}

.theme-c64 {
  --usx-color-background: #40318d;
  --usx-color-surface: #8b7bd9;
  --usx-color-surface-container: #50419d;
  --usx-color-on-surface: #ffffff;
  --usx-color-primary: #9ce6ff;
  --usx-color-outline-variant: rgba(255, 255, 255, 0.2);
}

.theme-teletext {
  --usx-color-background: #000000;
  --usx-color-surface: #111111;
  --usx-color-surface-container: #222222;
  --usx-color-on-surface: #ffffff;
  --usx-color-primary: #ffff00;
  --usx-color-outline-variant: rgba(255, 255, 0, 0.3);
}

.theme-high-contrast {
  --usx-color-background: #000000;
  --usx-color-surface: #0a0a0a;
  --usx-color-surface-container: #1a1a1a;
  --usx-color-on-surface: #ffffff;
  --usx-color-primary: #00ffff;
  --usx-color-outline: #ffffff;
  --usx-color-outline-variant: #ffffff;
}

/* Topbar */
.gallery-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.5rem;
  background: var(--usx-color-surface, #1e2025);
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  flex-wrap: wrap;
  gap: 1rem;
}

.gallery-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.gallery-logo-icon {
  font-size: 32px;
  color: var(--usx-color-primary, #a8c7fa);
}

.gallery-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
}

.gallery-subtitle {
  font-size: 0.78rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.gallery-controls {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.control-label {
  font-size: 0.8rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  font-weight: 500;
}

.segmented-btn-group {
  display: flex;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  padding: 2px;
}

.seg-btn {
  background: transparent;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  color: var(--usx-color-on-surface-variant, #8e9199);
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.15s ease;
}

.seg-btn.active {
  background: var(--usx-color-primary, #a8c7fa);
  color: #041e49;
}

.seg-btn .material-symbols-outlined {
  font-size: 18px;
}

.control-select {
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  color: var(--usx-color-on-surface, #e2e2e6);
  font-size: 0.8rem;
}

.json-toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  color: var(--usx-color-on-surface, #e2e2e6);
  font-size: 0.8rem;
  cursor: pointer;
  font-weight: 500;
}

.json-toggle-btn.active {
  background: rgba(168, 199, 250, 0.15);
  border-color: var(--usx-color-primary, #a8c7fa);
  color: var(--usx-color-primary, #a8c7fa);
}

.json-toggle-btn .material-symbols-outlined {
  font-size: 18px;
}

/* Recipe Nav Tabs */
.recipe-nav-tabs {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.65rem 1.5rem;
  background: var(--usx-color-surface-container, #16181d);
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  overflow-x: auto;
}

.paradigm-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.paradigm-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--usx-color-on-surface-variant, #8e9199);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-right: 0.25rem;
  white-space: nowrap;
}

.recipe-tab-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.04);
  color: var(--usx-color-on-surface-variant, #c4c6d0);
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.recipe-tab-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.recipe-tab-btn.active {
  background: var(--usx-color-primary, #a8c7fa);
  color: #041e49;
  font-weight: 600;
}

.tab-retro.active {
  background: #ffcc00;
  color: #000000;
}

.recipe-tab-btn .material-symbols-outlined {
  font-size: 18px;
}

/* Stage */
.gallery-stage {
  display: flex;
  flex: 1;
  padding: 2rem;
  gap: 1.5rem;
  justify-content: center;
  align-items: flex-start;
  overflow-y: auto;
}

.viewport-frame {
  width: 100%;
  transition: max-width 0.25s ease;
  display: flex;
  justify-content: center;
}

.viewport-canvas {
  width: 100%;
  padding: 1.5rem;
  border-radius: 12px;
  background: var(--usx-color-surface, #1e2025);
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

/* JSON Drawer */
.json-inspector-drawer {
  width: 360px;
  flex-shrink: 0;
  padding: 1rem;
  border-radius: 12px;
  background: var(--usx-color-surface, #1e2025);
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
}

.json-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
}

.json-drawer-header h3 {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 600;
}

.paradigm-pill {
  font-size: 0.65rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: var(--usx-color-primary, #a8c7fa);
  color: #041e49;
  font-weight: 700;
}

.json-content {
  margin: 0;
  padding: 0.75rem;
  border-radius: 8px;
  background: #0d1117;
  color: #58a6ff;
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.75rem;
  max-height: 600px;
  overflow: auto;
  line-height: 1.4;
}
</style>
