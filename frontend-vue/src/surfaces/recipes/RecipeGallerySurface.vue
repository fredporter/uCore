<script setup lang="ts">
import { ref, computed } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import {
  SAMPLE_TASK_LIST,
  SAMPLE_PROSE_DOCUMENT,
  SAMPLE_CARD_MATRIX,
  SAMPLE_SETTINGS_FORM,
  SAMPLE_STORY_FORM,
  SAMPLE_SYSTEM_PAGE,
  SAMPLE_ALERTS_SUITE,
  SAMPLE_TELETEXT,
  SAMPLE_TERMINAL,
  SAMPLE_AUTHORING_WORKBENCH,
  type AnyRecipe,
} from '../../recipes/recipes'

import TaskListRecipeView from '../../recipes/components/TaskListRecipeView.vue'
import ProseDocumentRecipeView from '../../recipes/components/ProseDocumentRecipeView.vue'
import CardMatrixRecipeView from '../../recipes/components/CardMatrixRecipeView.vue'
import SettingsFormRecipeView from '../../recipes/components/SettingsFormRecipeView.vue'
import StoryRecipeView from '../../recipes/components/StoryRecipeView.vue'
import SystemPageRecipeView from '../../recipes/components/SystemPageRecipeView.vue'
import AlertsRecipeView from '../../recipes/components/AlertsRecipeView.vue'
import TeletextRecipeView from '../../recipes/components/TeletextRecipeView.vue'
import TerminalRecipeView from '../../recipes/components/TerminalRecipeView.vue'
import AuthoringRecipeView from '../../recipes/components/AuthoringRecipeView.vue'

// Primary Surface Lane: 'usx' vs 'gridcore' (Strict separation)
const selectedLane = ref<'usx' | 'gridcore'>('usx')

// Active recipe keys per lane
const selectedUsxRecipe = ref<string>('task-list')
const selectedGridcoreRecipe = ref<string>('teletext-mode7')

// Active recipe key getter/setter depending on lane
const selectedRecipeKey = computed({
  get() {
    return selectedLane.value === 'usx' ? selectedUsxRecipe.value : selectedGridcoreRecipe.value
  },
  set(val: string) {
    if (selectedLane.value === 'usx') {
      selectedUsxRecipe.value = val
    } else {
      selectedGridcoreRecipe.value = val
    }
  },
})

// USX Appearance Mode: Strictly Light or Dark only (no retro or cross-over palettes)
const usxMode = ref<'dark' | 'light'>('dark')
function toggleUsxMode() {
  usxMode.value = usxMode.value === 'dark' ? 'light' : 'dark'
}

// Viewport simulator
const selectedViewport = ref<string>('100%')
const showJson = ref<boolean>(false)

const allRecipes: Record<string, AnyRecipe> = {
  'task-list': SAMPLE_TASK_LIST,
  'authoring-workbench': SAMPLE_AUTHORING_WORKBENCH,
  'prose-document': SAMPLE_PROSE_DOCUMENT,
  'card-matrix': SAMPLE_CARD_MATRIX,
  'settings-form': SAMPLE_SETTINGS_FORM,
  'story-form': SAMPLE_STORY_FORM,
  'system-page': SAMPLE_SYSTEM_PAGE,
  'alerts-suite': SAMPLE_ALERTS_SUITE,
  'teletext-mode7': SAMPLE_TELETEXT,
  'terminal-ansi': SAMPLE_TERMINAL,
}

const currentRecipe = computed(() => allRecipes[selectedRecipeKey.value])
const currentParadigm = computed(() => currentRecipe.value?.paradigm || selectedLane.value)
</script>

<template>
  <header class="gallery-topbar">
    <div class="gallery-brand">
      <h3 class="gallery-title">Recipe Gallery</h3>
      <p class="gallery-subtitle">Preview USX and GridCore recipes.</p>
    </div>

    <!-- Primary Lane Switcher: USX vs GridCore (Strictly Separated) -->
    <div class="lane-switcher">
      <button
        class="usx-btn lane-btn"
        :aria-pressed="selectedLane === 'usx'"
        @click="selectedLane = 'usx'"
      >
        <UIcon name="web" />
        <span>USX Layouts</span>
      </button>
      <button
        class="usx-btn lane-btn"
        :aria-pressed="selectedLane === 'gridcore'"
        @click="selectedLane = 'gridcore'"
      >
        <UIcon name="grid_on" />
        <span>GridCore Layouts</span>
      </button>
    </div>

    <!-- Controls: Viewport, Theme (USX Only), & JSON -->
    <div class="gallery-controls">
      <!-- Viewport Switcher -->
      <div class="control-group">
        <span class="control-label">Viewport:</span>
        <div class="segmented-btn-group">
          <button
            class="usx-btn seg-btn"
            :class="{ active: selectedViewport === '360px' }"
            @click="selectedViewport = '360px'"
            title="Mobile (360px)"
          >
            <UIcon name="smartphone" />
          </button>
          <button
            class="usx-btn seg-btn"
            :class="{ active: selectedViewport === '768px' }"
            @click="selectedViewport = '768px'"
            title="Tablet (768px)"
          >
            <UIcon name="tablet" />
          </button>
          <button
            class="usx-btn seg-btn"
            :class="{ active: selectedViewport === '1200px' }"
            @click="selectedViewport = '1200px'"
            title="Desktop (1200px)"
          >
            <UIcon name="desktop_windows" />
          </button>
          <button
            class="usx-btn seg-btn"
            :class="{ active: selectedViewport === '100%' }"
            @click="selectedViewport = '100%'"
            title="Fluid (100%)"
          >
            <UIcon name="fit_screen" />
          </button>
        </div>
      </div>

      <!-- USX Mode Toggle: Strictly Light / Dark mode (Never on GridCore) -->
      <div v-if="selectedLane === 'usx'" class="control-group">
        <button
          class="usx-btn mode-toggle-btn"
          @click="toggleUsxMode"
          :title="`Switch to ${usxMode === 'dark' ? 'Light' : 'Dark'} mode`"
        >
          <UIcon :name="usxMode === 'dark' ? 'light_mode' : 'dark_mode'" />
          <span>{{ usxMode === 'dark' ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>
      </div>

      <!-- JSON Inspector Toggle -->
      <button
        class="usx-btn json-toggle-btn"
        :class="{ active: showJson }"
        @click="showJson = !showJson"
      >
        <UIcon name="data_object" />
        <span>Recipe JSON</span>
      </button>
    </div>
  </header>

  <!-- Sub-Navigation: USX Recipes Lane -->
  <nav v-if="selectedLane === 'usx'" class="recipe-nav-tabs">
    <div class="paradigm-group">
      <span class="paradigm-label">USX Core Surfaces:</span>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'task-list' }"
        @click="selectedRecipeKey = 'task-list'"
      >
        <UIcon name="checklist" />
        <span>Task List</span>
      </button>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'authoring-workbench' }"
        @click="selectedRecipeKey = 'authoring-workbench'"
      >
        <UIcon name="history_edu" />
        <span>Authoring Workbench</span>
      </button>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'prose-document' }"
        @click="selectedRecipeKey = 'prose-document'"
      >
        <UIcon name="article" />
        <span>Prose Document</span>
      </button>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'card-matrix' }"
        @click="selectedRecipeKey = 'card-matrix'"
      >
        <UIcon name="grid_view" />
        <span>Card Matrix</span>
      </button>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'settings-form' }"
        @click="selectedRecipeKey = 'settings-form'"
      >
        <UIcon name="tune" />
        <span>Settings Form</span>
      </button>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'system-page' }"
        @click="selectedRecipeKey = 'system-page'"
      >
        <UIcon name="search_off" />
        <span>System Page (S100)</span>
      </button>
    </div>

    <div class="paradigm-group">
      <span class="paradigm-label">Intake & Overlays:</span>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'story-form' }"
        @click="selectedRecipeKey = 'story-form'"
      >
        <UIcon name="dynamic_form" />
        <span>Story Form (Typeform)</span>
      </button>
      <button
        class="usx-btn recipe-tab-btn"
        :class="{ active: selectedRecipeKey === 'alerts-suite' }"
        @click="selectedRecipeKey = 'alerts-suite'"
      >
        <UIcon name="notifications_active" />
        <span>Alerts & Notifications</span>
      </button>
    </div>
  </nav>

  <!-- Sub-Navigation: GridCore Lane (Dedicated Character Matrix Recipes) -->
  <nav v-else class="recipe-nav-tabs gridcore-nav-tabs">
    <div class="paradigm-group">
      <span class="paradigm-label">GridCore Character Matrix:</span>
      <button
        class="usx-btn recipe-tab-btn tab-retro"
        :class="{ active: selectedRecipeKey === 'teletext-mode7' }"
        @click="selectedRecipeKey = 'teletext-mode7'"
      >
        <UIcon name="tv" />
        <span>Teletext (Mode 7 / BBC Ceefax)</span>
      </button>
      <button
        class="usx-btn recipe-tab-btn tab-retro"
        :class="{ active: selectedRecipeKey === 'terminal-ansi' }"
        @click="selectedRecipeKey = 'terminal-ansi'"
      >
        <UIcon name="terminal" />
        <span>Terminal (ANSI / C64)</span>
      </button>
    </div>
    <div class="gridcore-info-chip">
      <UIcon name="info" />
      <span>GridCore executes on fixed 40×25 or 42×27 cell matrix canvases without USX styling crossover.</span>
    </div>
  </nav>

  <!-- Main Inspection Stage -->
  <div class="gallery-stage">
    <!-- Simulated Viewport Frame -->
    <div
      class="viewport-frame"
      :class="selectedLane === 'usx' ? 'theme-' + usxMode : 'gridcore-lane'"
      :style="{ maxWidth: selectedViewport }"
    >
        <!-- USX Recipe Components -->
      <template v-if="selectedLane === 'usx'">
        <TaskListRecipeView
          v-if="selectedRecipeKey === 'task-list'"
          :recipe="currentRecipe as any"
        />
        <AuthoringRecipeView
          v-else-if="selectedRecipeKey === 'authoring-workbench'"
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
        <StoryRecipeView
          v-else-if="selectedRecipeKey === 'story-form'"
          :recipe="currentRecipe as any"
        />
        <SystemPageRecipeView
          v-else-if="selectedRecipeKey === 'system-page'"
          :recipe="currentRecipe as any"
        />
        <AlertsRecipeView
          v-else-if="selectedRecipeKey === 'alerts-suite'"
          :recipe="currentRecipe as any"
        />
      </template>

      <!-- GridCore Recipe Components -->
      <template v-else>
        <TeletextRecipeView
          v-if="selectedRecipeKey === 'teletext-mode7'"
          :recipe="currentRecipe as any"
        />
        <TerminalRecipeView
          v-else-if="selectedRecipeKey === 'terminal-ansi'"
          :recipe="currentRecipe as any"
        />
      </template>
    </div>

    <!-- JSON Inspector Drawer -->
    <aside v-if="showJson" class="json-inspector-drawer">
      <div class="json-drawer-header">
        <h3>Declarative Recipe Payload</h3>
        <span class="paradigm-pill">{{ currentParadigm.toUpperCase() }}</span>
      </div>
      <pre class="json-content"><code>{{ JSON.stringify(currentRecipe, null, 2) }}</code></pre>
    </aside>
  </div>
</template>

<style scoped>
/* ── USX Themes: Dark & Light Mode Only ── */
.theme-dark {
  --usx-color-background: #14161a;
  --usx-color-surface: #1e2025;
  --usx-color-surface-container: #282a30;
  --usx-color-surface-container-high: #32353c;
  --usx-color-on-surface: #e2e2e6;
  --usx-color-on-surface-variant: #8e9199;
  --usx-color-primary: #a8c7fa;
  --usx-color-primary-container: #0842a0;
  --usx-color-on-primary-container: #d3e3fd;
  --usx-color-outline: #8e9199;
  --usx-color-outline-variant: rgba(255, 255, 255, 0.12);
  --usx-border-color: #32353c;
}

.theme-light {
  --usx-color-background: #f8f9fa;
  --usx-color-surface: #ffffff;
  --usx-color-surface-container: #edeef2;
  --usx-color-surface-container-high: #e2e3e7;
  --usx-color-on-surface: #191c20;
  --usx-color-on-surface-variant: #44474e;
  --usx-color-primary: #0b57d0;
  --usx-color-primary-container: #d3e3fd;
  --usx-color-on-primary-container: #041e49;
  --usx-color-outline: #74777f;
  --usx-color-outline-variant: rgba(0, 0, 0, 0.12);
  --usx-border-color: #e2e3e7;
}

/* GridCore lane root container */
.gridcore-lane {
  --usx-color-background: #0f1115;
  --usx-color-surface: #16181d;
  --usx-color-surface-container: #1e2025;
  --usx-color-surface-container-high: #282a30;
  --usx-color-on-surface: #e2e2e6;
  --usx-color-on-surface-variant: #8e9199;
  --usx-color-primary: #00ff66;
  --usx-color-outline-variant: rgba(255, 255, 255, 0.12);
}

/* Gallery controls inherit the active workspace theme. */
.gallery-topbar,
.gallery-brand {
  display: grid;
  min-width: 0;
  gap: var(--usx-spacing-md);
}

.gallery-brand {
  gap: var(--usx-spacing-xs);
}

.gallery-title,
.gallery-subtitle {
  margin: 0;
}

.gallery-subtitle {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.lane-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.usx-btn.lane-btn {
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: 0;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  box-shadow: none;
}

.usx-btn.lane-btn:hover {
  border-color: var(--usx-color-on-surface-muted);
  box-shadow: none;
}

.usx-btn.lane-btn[aria-pressed="true"] {
  border-color: var(--usx-color-primary);
}

.gallery-controls {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
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
  background: var(--usx-color-surface-container, #282a30);
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.12));
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

/* Mode Toggle Button for USX (Light / Dark only) */
.mode-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  background: var(--usx-color-surface-container, #282a30);
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  color: var(--usx-color-on-surface, #e2e2e6);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.mode-toggle-btn:hover {
  background: var(--usx-color-surface-container-high, #32353c);
  color: var(--usx-color-primary, #a8c7fa);
}

.mode-toggle-btn .material-symbols-outlined {
  font-size: 18px;
}

.json-toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  background: var(--usx-color-surface-container, #282a30);
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

/* Recipe Navigation Tabs */
.recipe-nav-tabs {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface, #1e2025);
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  overflow-x: auto;
  scrollbar-width: thin;
}

.gridcore-nav-tabs {
  justify-content: space-between;
}

.gridcore-info-chip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  padding: 0.3rem 0.75rem;
  border-radius: 9999px;
  background: rgba(0, 255, 102, 0.08);
  border: 1px solid rgba(0, 255, 102, 0.2);
  color: #00ff66;
}

.gridcore-info-chip .material-symbols-outlined {
  font-size: 1rem;
}

.paradigm-group {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.paradigm-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--usx-color-on-surface-variant, #8e9199);
  font-weight: 600;
  margin-right: 0.25rem;
  white-space: nowrap;
}

.recipe-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--usx-color-on-surface-variant, #8e9199);
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.recipe-tab-btn:hover {
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.04));
  color: var(--usx-color-on-surface, #e2e2e6);
}

.recipe-tab-btn.active {
  background: var(--usx-color-surface-container-high, #32353c);
  color: var(--usx-color-primary, #a8c7fa);
  border-color: var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  font-weight: 500;
}

.recipe-tab-btn .material-symbols-outlined {
  font-size: 18px;
}

.tab-retro.active {
  color: #00ff66 !important;
  border-color: rgba(0, 255, 102, 0.4) !important;
}

/* Inspection Stage */
.gallery-stage {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: flex-start;
  gap: var(--usx-spacing-md);
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0;
  box-sizing: border-box;
}

.viewport-frame {
  width: 100%;
  min-width: 0;
  color: var(--usx-color-on-surface);
  transition: max-width 0.25s ease-in-out;
}

/* JSON Drawer */
.json-inspector-drawer {
  width: min(100%, 360px);
  flex-shrink: 0;
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  border-radius: 12px;
  background: var(--usx-color-surface, #1e2025);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  max-height: calc(100vh - 160px);
  z-index: 10;
  overflow: hidden;
}

.json-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  flex-shrink: 0;
}

.json-drawer-header h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
}

.paradigm-pill {
  font-size: 0.68rem;
  font-family: var(--usx-font-family-mono, monospace);
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--usx-color-primary, #a8c7fa);
  color: #041e49;
  font-weight: 700;
}

.json-content {
  flex: 1;
  margin: 0;
  padding: 1rem;
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
  background: var(--usx-color-surface-container, #282a30);
  overflow-y: auto;
  line-height: 1.5;
}
</style>
