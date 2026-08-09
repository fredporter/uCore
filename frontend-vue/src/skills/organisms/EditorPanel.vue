<template>
  <div class="editor-panel">
    <!-- Document header: prose title + frontmatter table (full-width).
         Hidden in Preview (Prose view) — the rendered document takes over. -->
    <div v-if="viewMode !== 'preview'" class="editor-panel__doc-header">
      <div class="editor-panel__doc-titlebar">
        <h1 class="editor-panel__doc-title">{{ docTitle }}</h1>
        <button
          v-if="!readOnly"
          class="editor-panel__add-field"
          title="Add frontmatter field"
          @click="handleAddField"
        >
          <UIcon name="add" />
        </button>
      </div>
      <FrontmatterPills
        v-if="hasFrontmatter"
        v-model="frontmatter"
        :can-edit="!readOnly"
        @update:model-value="onFrontmatterChange"
      />
    </div>

    <!-- Body: editor | preview | research panel (no redundant topbar —
         controls live in the MarkdownEditor toolbar below) -->
    <div class="editor-panel__body">
      <!-- Main editor column -->
      <div
        class="editor-panel__main"
        :class="`editor-panel__main--${viewMode}`"
      >
        <!-- Editor pane: formatting toolbar. In editor-only view the
             view-research-close toolbar sits right-aligned next to it. -->
        <MarkdownEditor
          v-if="viewMode !== 'preview'"
          v-model="localContent"
          :preview="false"
          :read-only="readOnly"
          :edit-mode="localEditMode"
          class="editor-panel__markdown"
          :class="{ 'editor-panel__markdown--split': viewMode === 'split' }"
          @save="handleSave"
          @change="onContentChange"
        >
          <template #toolbar-actions>
            <EditorToolbar
              v-if="viewMode === 'edit'"
              right
              :view-mode="viewMode"
              :research-open="researchOpen"
              :edit-mode="localEditMode"
              :read-only="readOnly"
              @update:view-mode="onViewModeChange"
              @toggle-research="researchOpen = !researchOpen"
              @toggle-edit-mode="toggleEditMode"
              @save="handleSave"
              @close="emit('close')"
            />
          </template>
        </MarkdownEditor>

        <!-- Prose panel: view-research-close toolbar + rendered document -->
        <div
          v-if="viewMode === 'split' || viewMode === 'preview'"
          class="editor-panel__prose"
        >
          <div class="editor-panel__prose-bar">
            <EditorToolbar
              bare
              :view-mode="viewMode"
              :research-open="researchOpen"
              :edit-mode="localEditMode"
              :read-only="readOnly"
              @update:view-mode="onViewModeChange"
              @toggle-research="researchOpen = !researchOpen"
              @toggle-edit-mode="toggleEditMode"
              @save="handleSave"
              @close="emit('close')"
            />
          </div>
          <MarkdownPreview
            :content="localContent"
            :filename="currentFilename"
            class="editor-panel__preview"
          />
        </div>
      </div>

      <!-- Research panel (right column) -->
      <transition name="editor-sidebar">
        <div v-if="researchOpen" class="editor-panel__research">
          <ResearchPanel />
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component EditorPanel
 * @description Markdown editor using Markdown WYSIWYG as the primary interface.
 *   - Split view (editor + preview) shown by default
 *   - No redundant topbar: controls live in the MarkdownEditor toolbar below
 *   - Prose (WYSIWYG) and code (raw markdown, line breaks preserved) modes
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
import MarkdownEditor from "../molecules/editor/MarkdownEditor.vue";
import EditorToolbar from "../molecules/editor/EditorToolbar.vue";
import FrontmatterPills from "../molecules/editor/FrontmatterPills.vue";
import MarkdownPreview from "../molecules/MarkdownPreview.vue";
import ResearchPanel from "../molecules/editor/ResearchPanel.vue";
import { useShellStore } from "../../stores/shell";
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

const shell = useShellStore();

// ─── State ───────────────────────────────────────────────────────────
const localContent = ref(props.content);
const localEditMode = ref<"prose" | "code">(props.editMode);
const viewMode = ref<"edit" | "preview" | "split">("split");
const researchOpen = ref(false);

const currentFilename = computed(() => props.title || "Untitled.md");

/** Prose document title: frontmatter title if present, else filename stem. */
const docTitle = computed(() => {
  const fmTitle = frontmatter.value?.title;
  if (typeof fmTitle === "string" && fmTitle.trim()) {
    return fmTitle.trim();
  }
  return String(props.title || "Untitled").replace(/\.(md|markdown|txt)$/i, "");
});

function onViewModeChange(mode: "edit" | "preview" | "split") {
  viewMode.value = mode;
}

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

/** Add a new frontmatter field (triggered by the header add icon). */
function handleAddField() {
  const key = window.prompt("New field name (e.g. status, author):");
  if (!key?.trim()) return;
  const value = window.prompt(`Value for "${key}":`);
  if (value === null) return;
  onFrontmatterChange({ ...frontmatter.value, [key.trim()]: value });
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

/* ─── Prose panel: view-research-close bar + rendered document ───── */
.editor-panel__prose {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.editor-panel__prose-bar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-shrink: 0;
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  overflow-x: auto;
}

.editor-panel__prose-bar .editor-toolbar {
  flex-shrink: 0;
}

.editor-panel__prose .editor-panel__preview {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* ─── 2-column body layout ───────────────────────────────────────── */
.editor-panel__body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.editor-panel__research {
  width: 200px;
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

/* Document header (title + frontmatter table) — full-width block above body.
   No background so it blends with the editor/page background. Even vertical
   padding above and below the title. */
.editor-panel__doc-header {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-lg) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  background: transparent;
  max-height: 40%;
  overflow-y: auto;
  flex-shrink: 0;
}

.editor-panel__doc-titlebar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.editor-panel__doc-title {
  margin: 0;
  padding: 0;
  flex: 1;
  min-width: 0;
  font-family: var(--usx-font-family-sans);
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-on-surface);
  line-height: 1.2;
  word-break: break-word;
}

/* Add-frontmatter-field icon at the right of the doc title */
.editor-panel__add-field {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  min-height: 0;
  padding: 0;
  border: 1px dashed var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition:
    color var(--usx-transition-fast),
    border-color var(--usx-transition-fast);
}

.editor-panel__add-field:hover {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
}

/* Split view: Markdown + Preview side-by-side */
.editor-panel__main--split {
  flex-direction: row;
}

/* The editor pane fills its container — disable the standalone
   --usx-editor-min-height so it never overflows the split body */
.editor-panel__markdown {
  --usx-editor-min-height: 0;
}

.editor-panel__markdown--split {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  border-right: 1px solid var(--usx-color-border);
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
</style>
