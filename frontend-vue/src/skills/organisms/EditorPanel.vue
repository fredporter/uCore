<template>
  <div class="editor-panel">
    <!-- Top toolbar: title, engine chip, essential controls -->
    <div class="editor-panel__toolbar">
      <div class="editor-panel__toolbar-left">
        <button
          class="editor-panel__nav-btn"
          :class="{ 'editor-panel__nav-btn--active': sidebarOpen }"
          title="Toggle file tree"
          @click="sidebarOpen = !sidebarOpen"
        >
          <UIcon name="account_tree" />
        </button>
        <UIcon name="article" />
        <span class="editor-panel__title">{{ title || "Untitled" }}</span>
      </div>
      <div class="editor-panel__toolbar-center">
        <!-- Edit / Preview mode tabs -->
        <div class="editor-panel__mode-tabs">
          <button
            class="editor-panel__mode-tab"
            :class="{ 'editor-panel__mode-tab--active': viewMode === 'edit' }"
            @click="viewMode = 'edit'"
          >
            <UIcon name="edit" /> Edit
          </button>
          <button
            class="editor-panel__mode-tab"
            :class="{
              'editor-panel__mode-tab--active': viewMode === 'preview',
            }"
            @click="viewMode = 'preview'"
          >
            <UIcon name="visibility" /> Preview
          </button>
          <button
            class="editor-panel__mode-tab"
            :class="{ 'editor-panel__mode-tab--active': viewMode === 'split' }"
            title="Side-by-side"
            @click="viewMode = 'split'"
          >
            <UIcon name="vertical_split" /> Split
          </button>
        </div>
      </div>
      <div class="editor-panel__toolbar-right">
        <button
          v-if="!readOnly"
          class="editor-panel__nav-btn editor-panel__nav-btn--save"
          title="Save (Ctrl+S)"
          @click="handleSave"
        >
          <UIcon name="save" />
        </button>
        <button
          class="editor-panel__nav-btn"
          :class="{
            'editor-panel__nav-btn--active': localEditMode === 'prose',
          }"
          :title="
            localEditMode === 'prose'
              ? 'Switch to code view'
              : 'Switch to prose view'
          "
          @click="toggleEditMode"
        >
          <UIcon :name="localEditMode === 'prose' ? 'notes' : 'code'" />
        </button>
        <button
          class="editor-panel__nav-btn"
          title="Close editor"
          @click="emit('close')"
        >
          <UIcon name="close" />
        </button>
      </div>
    </div>

    <!-- 3-column body: sidebar | editor | (future research panel) -->
    <div class="editor-panel__body">
      <!-- Workspace tree sidebar -->
      <transition name="editor-sidebar">
        <div v-if="sidebarOpen" class="editor-panel__sidebar">
          <WorkspaceTree />
        </div>
      </transition>

      <!-- Main editor column -->
      <div
        class="editor-panel__main"
        :class="`editor-panel__main--${viewMode}`"
      >
        <!-- Frontmatter pills (when metadata present) -->
        <FrontmatterPills
          v-if="hasFrontmatter"
          v-model="frontmatter"
          :can-edit="!readOnly"
          @update:model-value="onFrontmatterChange"
        />

        <!-- WYSIWYG editor pane -->
        <BangleEditor
          v-if="viewMode !== 'preview'"
          v-model="localContent"
          :preview="false"
          :read-only="readOnly"
          :edit-mode="localEditMode"
          class="editor-panel__bangle"
          :class="{ 'editor-panel__bangle--split': viewMode === 'split' }"
          @save="handleSave"
          @change="onContentChange"
        />

        <!-- Markdown preview pane -->
        <MarkdownPreview
          v-if="viewMode !== 'edit'"
          :content="localContent"
          :filename="currentFilename"
          class="editor-panel__preview"
          :class="{ 'editor-panel__preview--split': viewMode === 'split' }"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component EditorPanel
 * @description Simplified markdown editor using Bangle WYSIWYG as the primary interface.
 *   - Full-width Bangle editor with unified toolbar
 *   - Essential controls: save, mode toggle, close
 *   - No preview pane (WYSIWYG eliminates need for side-by-side preview)
 * @category skills/organisms
 * @props {string} content - Markdown content (v-model)
 * @props {string} title - Display title
 * @props {boolean} readOnly - Disable edits
 * @props {'prose' | 'code'} editMode - Edit mode preference
 * @emits {string} update:content - v-model update
 * @emits {void} save - Save requested
 * @emits {void} close - Close entire editor
 */
import { ref, watch, computed } from "vue";
import UIcon from "../atoms/UIcon.vue";
import BangleEditor from "../molecules/editor/BangleEditor.vue";
import WorkspaceTree from "../molecules/editor/WorkspaceTree.vue";
import FrontmatterPills from "../molecules/editor/FrontmatterPills.vue";
import MarkdownPreview from "../molecules/MarkdownPreview.vue";
import {
  parseDocument,
  serializeDocument,
  type Frontmatter,
} from "../../utils/frontmatterParser";

// ─── Props ───────────────────────────────────────────────────────────
interface Props {
  content?: string;
  title?: string;
  readOnly?: boolean;
  editMode?: "prose" | "code";
}

const props = withDefaults(defineProps<Props>(), {
  content: "",
  title: "Untitled",
  readOnly: false,
  editMode: "prose",
});

const emit = defineEmits<{
  "update:content": [value: string];
  "update:editMode": [value: "prose" | "code"];
  save: [value: string];
  close: [];
}>();

// ─── State ───────────────────────────────────────────────────────────
const localContent = ref(props.content);
const localEditMode = ref<"prose" | "code">(props.editMode);
const sidebarOpen = ref(true);
const viewMode = ref<"edit" | "preview" | "split">("edit");

const currentFilename = computed(() => props.title || "Untitled.md");

// ─── Frontmatter ─────────────────────────────────────────────────────
const parsed = computed(() => parseDocument(props.content || ""));
const frontmatter = ref<Frontmatter>(parsed.value.frontmatter);
const hasFrontmatter = computed(
  () => Object.keys(frontmatter.value).length > 0,
);

function onFrontmatterChange(updated: Frontmatter) {
  frontmatter.value = updated;
  // Re-serialize document with updated frontmatter
  const doc = parseDocument(localContent.value);
  const newMarkdown = serializeDocument(doc.body, updated);
  localContent.value = newMarkdown;
  emit("update:content", newMarkdown);
}

// ─── Sync props ──────────────────────────────────────────────────────
watch(
  () => props.content,
  (val) => {
    localContent.value = val;
    const p = parseDocument(val);
    frontmatter.value = p.frontmatter;
  },
);

watch(
  () => props.editMode,
  (val) => {
    localEditMode.value = val;
  },
);

// ─── Handlers ────────────────────────────────────────────────────────
function onContentChange(value: string) {
  localContent.value = value;
  emit("update:content", value);
}

function handleSave() {
  emit("save", localContent.value);
}

function toggleEditMode() {
  const next = localEditMode.value === "prose" ? "code" : "prose";
  localEditMode.value = next;
  emit("update:editMode", next);
}
</script>

<style scoped>
.editor-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
  background: var(--usx-color-background);
}

/* ─── Toolbar — compact, essential controls only ─────────────────── */
.editor-panel__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
  min-height: var(--usx-touch-min-sm);
  gap: var(--usx-spacing-sm);
}

.editor-panel__toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
  font-size: 1.25em;
}

.editor-panel__title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.editor-panel__toolbar-center {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  flex: 1;
  justify-content: center;
}

.editor-panel__engine-chip {
  display: inline-flex;
  align-items: center;
  padding: var(--usx-spacing-2) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
}

.editor-panel__toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-2);
  flex-shrink: 0;
}

/* ─── Nav buttons — icon-only, transparent, hover highlights ───────── */
.editor-panel__nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  padding: 0;
  border: none;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: 1.25em;
  transition:
    color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.editor-panel__nav-btn:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.editor-panel__nav-btn--active {
  color: var(--usx-color-primary);
  background: var(--usx-color-primary-disabled);
}

.editor-panel__nav-btn--save {
  color: var(--usx-color-primary);
}

.editor-panel__nav-btn--save:hover {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

/* ─── 3-column body layout ───────────────────────────────────────── */
.editor-panel__body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.editor-panel__sidebar {
  width: 220px;
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-panel__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* Split view: Bangle + Preview side-by-side */
.editor-panel__main--split {
  flex-direction: row;
}

.editor-panel__bangle--split,
.editor-panel__preview--split {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.editor-panel__bangle--split {
  border-right: 1px solid var(--usx-color-border);
}

/* ─── Mode tabs ───────────────────────────────────────────────────── */

.editor-panel__mode-tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  background-color: var(--usx-color-background);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: 3px;
}

.editor-panel__mode-tab {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 3px var(--usx-spacing-md);
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  color: var(--usx-color-on-surface-muted);
  transition: all 120ms ease;
  white-space: nowrap;
}

.editor-panel__mode-tab:hover {
  color: var(--usx-color-on-surface);
  background-color: var(--usx-color-surface-variant);
}

.editor-panel__mode-tab--active {
  background-color: var(--usx-color-surface);
  color: var(--usx-color-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* ─── Sidebar slide transition ────────────────────────────────────── */
.editor-sidebar-enter-active,
.editor-sidebar-leave-active {
  transition:
    width 200ms ease,
    opacity 200ms ease;
  overflow: hidden;
}

.editor-sidebar-enter-from,
.editor-sidebar-leave-to {
  width: 0;
  opacity: 0;
}

/* ─── Mobile: collapse sidebar below 640px ────────────────────────── */
@media (max-width: 640px) {
  .editor-panel__sidebar {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 100;
    width: 280px;
    box-shadow: 4px 0 16px rgba(0, 0, 0, 0.15);
  }
}
</style>
