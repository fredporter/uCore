<template>
  <div class="editor-panel">
    <!-- Document header: prose title + frontmatter table (full-width) -->
    <div class="editor-panel__doc-header">
      <h1 class="editor-panel__doc-title">{{ docTitle }}</h1>
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
        <!-- Preview-only: slim control bar so the document stays reachable -->
        <template v-if="viewMode === 'preview'">
          <div class="editor-panel__preview-bar">
            <EditorToolbar
              :view-mode="viewMode"
              :research-open="researchOpen"
              :edit-mode="localEditMode"
              :read-only="readOnly"
              :sidebar-open="shell.sidebarOpen"
              @update:view-mode="onViewModeChange"
              @toggle-sidebar="shell.toggleSidebar()"
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
        </template>

        <!-- WYSIWYG / code editor pane (controls injected into its toolbar) -->
        <MarkdownEditor
          v-else
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
              :view-mode="viewMode"
              :research-open="researchOpen"
              :edit-mode="localEditMode"
              :read-only="readOnly"
              :sidebar-open="shell.sidebarOpen"
              @update:view-mode="onViewModeChange"
              @toggle-sidebar="shell.toggleSidebar()"
              @toggle-research="researchOpen = !researchOpen"
              @toggle-edit-mode="toggleEditMode"
              @save="handleSave"
              @close="emit('close')"
            />
          </template>
        </MarkdownEditor>

        <!-- Markdown preview pane (split view) -->
        <MarkdownPreview
          v-if="viewMode === 'split'"
          :content="localContent"
          :filename="currentFilename"
          class="editor-panel__preview"
          :class="{ 'editor-panel__preview--split': viewMode === 'split' }"
        />
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
  return String(props.title || "Untitled").replace(
    /\.(md|markdown|txt)$/i,
    "",
  );
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

/* ─── Preview-only control bar (keeps actions reachable without editor) ── */
.editor-panel__preview-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-shrink: 0;
  padding: var(--usx-spacing-2) var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
}

.editor-panel__preview-bar .editor-toolbar {
  margin-left: 0;
  padding-left: 0;
  border-left: none;
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

/* Document header (title + frontmatter table) — full-width block above body */
.editor-panel__doc-header {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  max-height: 40%;
  overflow-y: auto;
  flex-shrink: 0;
}

.editor-panel__doc-title {
  margin: 0;
  padding: 0;
  font-family: var(--usx-font-family-sans);
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-on-surface);
  line-height: 1.2;
  word-break: break-word;
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

.editor-panel__markdown--split,
.editor-panel__preview--split {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.editor-panel__markdown--split {
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
