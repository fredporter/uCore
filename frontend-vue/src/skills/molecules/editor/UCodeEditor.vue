/** * @component UCodeEditor * @description Unified split-panel code editor for
the Developer Surface. * Supports side-by-side diff, Jupyter cell mode, file
tabs, and syntax highlighting. * Matches the uCore Workflow editor split-panel
layout. */
<template>
  <div class="ucode-editor">
    <!-- Toolbar: file tabs + actions -->
    <EditorToolbar
      :tabs="openTabs"
      :active-tab-id="activeTabId"
      :dirty="isDirty"
      :read-only="readOnly"
      :diff-active="showDiff"
      :cells-active="showCells"
      :show-diff="activeTabId !== ''"
      :show-cells="activeTabId !== ''"
      :show-close-secondary="showSecondaryPanel"
      :show-add-tab="showAddTab"
      @select-tab="selectTab"
      @close-tab="closeTab"
      @toggle-diff="toggleDiff"
      @toggle-cells="toggleCells"
      @close-secondary="closeSecondaryPanel"
      @save="$emit('save')"
    />

    <!-- Main editor area with optional split -->
    <div
      class="ucode-editor__main"
      :class="{ 'ucode-editor__main--split': showSecondaryPanel }"
    >
      <!-- Primary panel -->
      <div class="ucode-editor__primary">
        <CodeEditorCore
          v-if="activeTab && activeTab.id"
          :key="activeTab.id"
          v-model="activeContent"
          :filename="activeTab.filename"
          :read-only="readOnly"
          :placeholder="`Edit ${activeTab.filename}...`"
          @save="$emit('save')"
          @change="onContentChange"
        />
        <div v-else class="ucode-editor__empty">
          <UIcon name="code" class="ucode-editor__empty-icon" />
          <p>Select a file to start editing</p>
        </div>
      </div>

      <!-- Resizable splitter -->
      <ResizableSplitter
        v-if="showSecondaryPanel"
        direction="horizontal"
        @resize="onSplitterResize"
      />

      <!-- Secondary panel -->
      <div
        v-if="showSecondaryPanel"
        class="ucode-editor__secondary"
        :style="{ width: secondaryPanelWidth + 'px' }"
      >
        <DiffEditorPanel
          v-if="showDiff && activeTab"
          :original="diffOriginal"
          :modified="activeContent"
          :status="diffStatus"
          :has-repository-diff="hasRepositoryDiff"
          @update:modified="onModifiedInDiff"
        />
        <JupyterCellsPanel
          v-else-if="showCells"
          :cells="notebookCells"
          :default-language="detectedLanguage"
          @update:cell-source="onCellSourceUpdate"
          @toggle-cell-type="onCellTypeToggle"
          @add-cell="onAddCell"
          @delete-cell="onDeleteCell"
        />
      </div>
    </div>

    <!-- Status bar -->
    <EditorStatusBar
      :language="detectedLanguage"
      :cursor="cursorPosition"
      :line-count="lineCount"
      :dirty="isDirty"
      :read-only="readOnly"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from "vue";
import type { EditorTab } from "./EditorToolbar.vue";
import type { NotebookCell } from "./JupyterCellsPanel.vue";
import CodeEditorCore from "./CodeEditorCore.vue";
import DiffEditorPanel from "./DiffEditorPanel.vue";
import JupyterCellsPanel from "./JupyterCellsPanel.vue";
import EditorToolbar from "./EditorToolbar.vue";
import EditorStatusBar from "./EditorStatusBar.vue";
import ResizableSplitter from "./ResizableSplitter.vue";
import UIcon from "../../atoms/UIcon.vue";
import { languageFor } from "./codeLanguages";

// ── Props ────────────────────────────────────────────────────────────

interface Props {
  fileContent?: string;
  fileName?: string;
  filePath?: string;
  fileRepo?: string;
  readOnly?: boolean;
  diffOriginal?: string;
  diffStatus?: "clean" | "modified" | "added" | "deleted";
  hasRepositoryDiff?: boolean;
  saveRevision?: number;
  notebookCells?: NotebookCell[];
  showAddTab?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  fileContent: "",
  fileName: "",
  filePath: "",
  fileRepo: "",
  readOnly: false,
  diffOriginal: "",
  diffStatus: "clean",
  hasRepositoryDiff: false,
  saveRevision: 0,
  notebookCells: () => [],
  showAddTab: false,
});

const emit = defineEmits<{
  "update:fileContent": [value: string];
  "update:notebookCells": [cells: NotebookCell[]];
  save: [];
  "close-file": [];
}>();

// ── Open tabs ─────────────────────────────────────────────────────────

const openTabs = ref([] as EditorTab[]);
const activeTabId = ref<string>("");
const tabCounter = ref(0);
const tabContents = ref({} as Record<string, string>);
const isDirty = ref(false);

const activeTab = computed(
  () => openTabs.value.find((t) => t.id === activeTabId.value) ?? null,
);

const activeContent = computed({
  get: () =>
    activeTabId.value
      ? tabContents.value[activeTabId.value] || ""
      : props.fileContent,
  set: (val) => {
    if (activeTabId.value) tabContents.value[activeTabId.value] = val;
    emit("update:fileContent", val);
  },
});

function onContentChange() {
  isDirty.value = true;
  if (activeTab.value) activeTab.value.dirty = true;
}

function openFile(filename: string, path: string, content: string) {
  const existing = openTabs.value.find((t) => t.path === path);
  if (existing) {
    activeTabId.value = existing.id;
    return;
  }
  tabCounter.value++;
  const id = `tab-${tabCounter.value}`;
  const tab: EditorTab = {
    id,
    filename,
    path,
    dirty: false,
    language: languageFor(filename),
  };
  openTabs.value.push(tab);
  tabContents.value[id] = content;
  activeTabId.value = id;
  isDirty.value = false;
}

function selectTab(id: string) {
  activeTabId.value = id;
  isDirty.value = activeTab.value?.dirty ?? false;
}

function closeTab(id: string) {
  const idx = openTabs.value.findIndex((t) => t.id === id);
  if (idx === -1) return;
  openTabs.value.splice(idx, 1);
  delete tabContents.value[id];
  if (activeTabId.value === id) {
    if (openTabs.value.length > 0) {
      activeTabId.value =
        openTabs.value[Math.min(idx, openTabs.value.length - 1)].id;
    } else {
      activeTabId.value = "";
      emit("close-file");
    }
  }
}

// ── Secondary panel ───────────────────────────────────────────────────

const showDiff = ref(false);
const showCells = ref(false);
const showSecondaryPanel = ref(false);
const secondaryPanelWidth = ref(300);

function toggleDiff() {
  showDiff.value = !showDiff.value;
  if (showDiff.value) {
    showCells.value = false;
    showSecondaryPanel.value = true;
  } else if (!showCells.value) showSecondaryPanel.value = false;
}

function toggleCells() {
  showCells.value = !showCells.value;
  if (showCells.value) {
    showDiff.value = false;
    showSecondaryPanel.value = true;
  } else if (!showDiff.value) showSecondaryPanel.value = false;
}

function closeSecondaryPanel() {
  showDiff.value = false;
  showCells.value = false;
  showSecondaryPanel.value = false;
}

function onSplitterResize(delta: number) {
  secondaryPanelWidth.value = Math.max(
    200,
    Math.min(800, secondaryPanelWidth.value + delta),
  );
}

function onModifiedInDiff(value: string) {
  if (activeTabId.value) tabContents.value[activeTabId.value] = value;
  emit("update:fileContent", value);
  onContentChange();
}

// ── Notebook cells ─────────────────────────────────────────────────

const notebookCells = computed({
  get: () => props.notebookCells,
  set: (val) => emit("update:notebookCells", val),
});

function onCellSourceUpdate(idx: number, source: string) {
  const cells = [...notebookCells.value];
  if (cells[idx]) {
    cells[idx] = { ...cells[idx], source };
    emit("update:notebookCells", cells);
    isDirty.value = true;
  }
}

function onCellTypeToggle(idx: number) {
  const cells = [...notebookCells.value];
  if (cells[idx]) {
    cells[idx] = {
      ...cells[idx],
      type: (cells[idx].type === "code" ? "markdown" : "code") as
        | "code"
        | "markdown",
    };
    emit("update:notebookCells", cells);
  }
}

function onAddCell(type: "code" | "markdown") {
  const cells = [
    ...notebookCells.value,
    {
      id: `cell-${Date.now()}`,
      type,
      source: "",
      language: props.fileName ? languageFor(props.fileName) : "python",
    },
  ];
  emit("update:notebookCells", cells);
}

function onDeleteCell(idx: number) {
  emit(
    "update:notebookCells",
    notebookCells.value.filter((_, i) => i !== idx),
  );
}

// ── Status bar state ───────────────────────────────────────────────

const cursorPosition = ref({ line: 1, col: 1 });
const lineCount = ref(0);
const detectedLanguage = computed(() =>
  activeTab.value ? languageFor(activeTab.value.filename) : "markdown",
);

// ── Watch external file changes ───────────────────────────────────

watch(
  () => ({
    name: props.fileName,
    path: props.filePath,
    content: props.fileContent,
  }),
  (info) => {
    if (info.name || info.path) openFile(info.name, info.path, info.content);
  },
  { immediate: true },
);

watch(
  () => props.saveRevision,
  () => {
    isDirty.value = false;
    if (activeTab.value) activeTab.value.dirty = false;
  },
);

defineExpose({
  openFile,
  selectTab,
  closeTab,
  toggleDiff,
  toggleCells,
  showSecondary: () => showSecondaryPanel.value,
});

onBeforeUnmount(() => {
  openTabs.value = [];
  tabContents.value = {};
});
</script>

<style scoped>
.ucode-editor {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: var(--usx-color-background);
}
.ucode-editor__main {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}
.ucode-editor__main--split {
}
.ucode-editor__primary {
  flex: 1;
  min-width: 0;
  display: flex;
  overflow: hidden;
}
.ucode-editor__secondary {
  flex-shrink: 0;
  overflow: hidden;
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
}
.ucode-editor__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  background: var(--usx-color-background);
}
.ucode-editor__empty-icon {
  font-size: 48px;
  opacity: 0.3;
}
.ucode-editor__empty p {
  margin: 0;
  font-size: var(--usx-font-size-base);
}
</style>
