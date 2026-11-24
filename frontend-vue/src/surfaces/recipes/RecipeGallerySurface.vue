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

const props = defineProps<{ lane: 'usx' | 'gridcore' }>()
const selectedLane = computed(() => props.lane)

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
const viewports = [
  { width: '360px', label: 'Mobile (360px)', icon: 'smartphone' },
  { width: '768px', label: 'Tablet (768px)', icon: 'tablet' },
  { width: '1200px', label: 'Desktop (1200px)', icon: 'desktop_windows' },
  { width: '100%', label: 'Fluid (100%)', icon: 'fit_screen' },
]
const themeAction = computed(() => usxMode.value === 'dark' ? 'Preview in light' : 'Preview in dark')
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
    <div class="gallery-controls" role="group" aria-label="Recipe preview controls">
      <button
        v-for="viewport in viewports"
        :key="viewport.width"
        type="button"
        class="usx-btn preview-control"
        :aria-pressed="selectedViewport === viewport.width"
        :aria-label="viewport.label"
        :title="viewport.label"
        @click="selectedViewport = viewport.width"
      >
        <UIcon :name="viewport.icon" />
      </button>
      <button
        v-if="selectedLane === 'usx'"
        type="button"
        class="usx-btn preview-control"
        :aria-label="themeAction"
        :title="themeAction"
        @click="toggleUsxMode"
      >
        <UIcon :name="usxMode === 'dark' ? 'light_mode' : 'dark_mode'" />
      </button>
      <button
        type="button"
        class="usx-btn preview-control"
        aria-label="Recipe JSON"
        title="Recipe JSON"
        :aria-expanded="showJson"
        @click="showJson = !showJson"
      >
        <UIcon name="data_object" />
      </button>
    </div>

    <div class="gallery-brand">
      <h3 class="gallery-title">Recipe Gallery</h3>
      <p class="gallery-subtitle">{{ selectedLane === 'usx' ? 'Preview USX surface layouts.' : 'Preview GridCore character layouts.' }}</p>
    </div>
  </header>

  <nav v-if="selectedLane === 'usx'" class="recipe-nav-tabs" aria-label="Prose recipes">
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'task-list'"
      @click="selectedRecipeKey = 'task-list'"
    >
      <UIcon name="checklist" />
      <span>Task List</span>
    </button>
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'authoring-workbench'"
      @click="selectedRecipeKey = 'authoring-workbench'"
    >
      <UIcon name="history_edu" />
      <span>Authoring Workbench</span>
    </button>
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'prose-document'"
      @click="selectedRecipeKey = 'prose-document'"
    >
      <UIcon name="article" />
      <span>Prose Document</span>
    </button>
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'card-matrix'"
      @click="selectedRecipeKey = 'card-matrix'"
    >
      <UIcon name="grid_view" />
      <span>Card Matrix</span>
    </button>
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'settings-form'"
      @click="selectedRecipeKey = 'settings-form'"
    >
      <UIcon name="tune" />
      <span>Settings Form</span>
    </button>
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'system-page'"
      @click="selectedRecipeKey = 'system-page'"
    >
      <UIcon name="search_off" />
      <span>System Page</span>
    </button>

    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'story-form'"
      @click="selectedRecipeKey = 'story-form'"
    >
      <UIcon name="dynamic_form" />
      <span>Story Form</span>
    </button>
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'alerts-suite'"
      @click="selectedRecipeKey = 'alerts-suite'"
    >
      <UIcon name="notifications_active" />
      <span>Alerts & Notifications</span>
    </button>
  </nav>

  <nav v-else class="recipe-nav-tabs recipe-nav-tabs--grid" aria-label="Grid recipes">
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'teletext-mode7'"
      @click="selectedRecipeKey = 'teletext-mode7'"
    >
      <UIcon name="tv" />
      <span>Teletext</span>
    </button>
    <button
      type="button"
      class="usx-btn recipe-tab-btn"
      :aria-pressed="selectedRecipeKey === 'terminal-ansi'"
      @click="selectedRecipeKey = 'terminal-ansi'"
    >
      <UIcon name="terminal" />
      <span>Terminal</span>
    </button>
  </nav>

  <!-- Main Inspection Stage -->
  <div class="gallery-stage" :class="{ 'gallery-stage--task-list': selectedRecipeKey === 'task-list' }" :data-preview-theme="selectedLane === 'usx' ? usxMode : undefined">
    <!-- Simulated Viewport Frame -->
    <div
      class="viewport-frame"
      :class="{ 'gridcore-lane': selectedLane === 'gridcore' }"
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
[data-preview-theme="dark"] {
  color-scheme: dark;
  --usx-color-surface-hover: #2b2e35;
  --usx-color-success: #75c994;
  --usx-color-danger: #ff9b9b;
  --usx-color-warning: #ffd17a;
  --usx-color-background: #14161a;
  --usx-color-surface: var(--usx-color-surface);
  --usx-color-surface-container: #282a30;
  --usx-color-surface-container-high: #32353c;
  --usx-color-on-surface: var(--usx-color-on-surface);
  --usx-color-on-surface-variant: var(--usx-color-on-surface-muted);
  --usx-color-primary: var(--usx-color-primary);
  --usx-color-primary-container: #0842a0;
  --usx-color-on-primary-container: #d3e3fd;
  --usx-color-outline: var(--usx-color-on-surface-muted);
  --usx-color-outline-variant: color-mix(in srgb, var(--usx-color-on-surface) 12%, transparent);
  --usx-color-border: #32353c;
  --usx-color-on-surface-muted: #a7aab2;
}

[data-preview-theme="light"] {
  color-scheme: light;
  --usx-color-surface-hover: #f0f2f5;
  --usx-color-success: #237443;
  --usx-color-danger: #b42935;
  --usx-color-warning: #825800;
  --usx-color-background: #f8f9fa;
  --usx-color-surface: var(--usx-color-on-surface);
  --usx-color-surface-container: #edeef2;
  --usx-color-surface-container-high: #e2e3e7;
  --usx-color-on-surface: #191c20;
  --usx-color-on-surface-variant: #44474e;
  --usx-color-primary: #0b57d0;
  --usx-color-primary-container: #d3e3fd;
  --usx-color-on-primary-container: #041e49;
  --usx-color-outline: #74777f;
  --usx-color-outline-variant: color-mix(in srgb, var(--usx-color-scrim) 12%, transparent);
  --usx-color-border: #d7d9df;
  --usx-color-on-surface-muted: #595e68;
}

/* GridCore lane root container */
.gridcore-lane {
  --usx-color-background: #0f1115;
  --usx-color-surface: #16181d;
  --usx-color-surface-container: var(--usx-color-surface);
  --usx-color-surface-container-high: #282a30;
  --usx-color-on-surface: var(--usx-color-on-surface);
  --usx-color-on-surface-variant: var(--usx-color-on-surface-muted);
  --usx-color-primary: #00ff66;
  --usx-color-outline-variant: color-mix(in srgb, var(--usx-color-on-surface) 12%, transparent);
}

/* Gallery controls inherit the active workspace theme. */
.gallery-topbar,
.gallery-brand {
  display: grid;
  min-width: 0;
  gap: var(--usx-spacing-xs);
}

.gallery-topbar {
  gap: 0;
  margin: 0;
  padding: 0;
}

.gallery-brand {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}

.gallery-title,
.gallery-subtitle {
  margin: 0;
}

.gallery-subtitle {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.gallery-controls {
  display: grid;
  margin: 0;
  padding: 0;
  grid-auto-flow: column;
  grid-auto-columns: minmax(0, var(--usx-touch-min-sm));
  justify-content: start;
  align-items: center;
}

.usx-btn.preview-control {
  display: inline-grid;
  place-items: center;
  width: 100%;
  min-width: 0;
  min-height: var(--usx-touch-min-sm);
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
  transform: none;
  color: var(--usx-color-on-surface-muted);
}

.usx-btn.preview-control:hover,
.usx-btn.preview-control[aria-pressed="true"],
.usx-btn.preview-control[aria-expanded="true"] {
  color: var(--usx-color-primary);
}

.recipe-nav-tabs {
  display: flex;
  flex-shrink: 0;
  justify-content: flex-start;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin: 0;
  padding: 0;
  overflow-x: auto;
  scrollbar-width: thin;
}

.recipe-nav-tabs .usx-btn.recipe-tab-btn {
  flex: 0 0 auto;
  width: auto;
  min-height: var(--usx-touch-min-sm);
  margin: 0;
  padding: 0 var(--usx-spacing-sm);
}

.recipe-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.recipe-tab-btn:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.recipe-tab-btn[aria-pressed="true"] {
  color: var(--usx-color-primary);
}

.recipe-nav-tabs--grid {
  justify-content: center;
  gap: var(--usx-spacing-sm);
}

.recipe-nav-tabs--grid .usx-btn.recipe-tab-btn {
  justify-content: center;
  min-width: 6rem;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
}

.recipe-nav-tabs--grid .usx-btn.recipe-tab-btn:hover,
.recipe-nav-tabs--grid .usx-btn.recipe-tab-btn[aria-pressed="true"] {
  background: var(--usx-color-surface-hover);
}

.recipe-nav-tabs--grid .usx-btn.recipe-tab-btn[aria-pressed="true"] {
  color: var(--usx-color-primary);
}

.recipe-nav-tabs .usx-btn.recipe-tab-btn:focus {
  outline: none;
  box-shadow: none;
}

.recipe-nav-tabs .usx-btn.recipe-tab-btn:focus-visible {
  outline: var(--usx-border-width) dashed var(--usx-color-on-surface);
  outline-offset: calc(-1 * var(--usx-spacing-xs));
}

.recipe-tab-btn .material-symbols-outlined {
  font-size: 18px;
}

/* Inspection Stage */
.gallery-topbar,
.recipe-nav-tabs {
  flex-shrink: 0;
}

.gallery-stage {
  flex: 1 0 auto;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: flex-start;
  gap: var(--usx-spacing-md);
  position: relative;
  padding: 0;
  box-sizing: border-box;
}

.gallery-stage[data-preview-theme] {
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  border-radius: var(--usx-radius-md);
}

.gallery-stage--task-list[data-preview-theme="dark"] {
  --usx-color-background: #121212;
  --usx-color-surface: #1e1e1e;
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
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent));
  border-radius: 12px;
  background: var(--usx-color-surface, var(--usx-color-surface));
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
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent));
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
  background: var(--usx-color-primary, var(--usx-color-primary));
  color: #041e49;
  font-weight: 700;
}

.json-content {
  flex: 1;
  margin: 0;
  padding: 1rem;
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  background: var(--usx-color-surface-container, #282a30);
  overflow-y: auto;
  line-height: 1.5;
}
</style>
