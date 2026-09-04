<template>
  <div class="editor-panel">
    <!-- Document header: prose title + frontmatter table (full-width).
         Hidden when hideHeader is true or in Preview (Prose view). -->
    <div
      v-if="!hideHeader && viewMode !== 'preview'"
      class="editor-panel__doc-header"
    >
      <div class="editor-panel__doc-titlebar">
        <h1 class="editor-panel__doc-title">{{ docTitle }}</h1>
        <button
          v-if="!readOnly"
          class="editor-panel__add-field"
          title="Edit document properties"
          type="button"
          @click="frontmatterEditorOpen = true"
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
      <FrontmatterEditor
        :open="frontmatterEditorOpen"
        :model-value="frontmatter"
        @close="frontmatterEditorOpen = false"
        @save="saveFrontmatter"
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
          v-model="bodyContent"
          :preview="false"
          :read-only="readOnly"
          :edit-mode="localEditMode"
          class="editor-panel__markdown"
          :class="{ 'editor-panel__markdown--split': viewMode === 'split' }"
          @save="handleSave"
          @change="onContentChange"
          @toolbar-action="handleToolbarAction"
          @update:edit-mode="onEditorModeChange"
        >
          <template #toolbar-actions>
            <div class="editor-panel__pane-actions">
              <button v-if="viewMode === 'split'" type="button" title="Collapse code" aria-label="Collapse code" @click="viewMode = 'preview'">
                <UIcon name="left_panel_close" :size="20" />
              </button>
              <button v-if="viewMode === 'edit'" type="button" title="Show prose" aria-label="Show prose" @click="viewMode = 'split'">
                <UIcon name="visibility" :size="20" />
              </button>
              <button type="button" title="Save" aria-label="Save" :disabled="readOnly" @click="handleSave">
                <UIcon name="save" :size="20" />
              </button>
              <button type="button" title="Publish" aria-label="Publish document" @click="emit('publish')">
                <UIcon name="publish" :size="20" />
              </button>
            </div>
          </template>
        </MarkdownEditor>

        <!-- Prose panel: view-research-close toolbar + rendered document -->
        <div
          v-if="viewMode === 'split' || viewMode === 'preview'"
          class="editor-panel__prose"
        >
          <div class="editor-panel__prose-bar">
            <div class="editor-panel__pane-actions">
              <button v-if="viewMode === 'preview'" type="button" title="Show code" aria-label="Show code" @click="openCodePane">
                <UIcon name="edit_note" :size="20" />
              </button>
              <button v-else type="button" title="Collapse prose" aria-label="Collapse prose" @click="viewMode = 'edit'">
                <UIcon name="right_panel_close" :size="20" />
              </button>
              <button type="button" title="Publish" aria-label="Publish document" @click="emit('publish')">
                <UIcon name="publish" :size="20" />
              </button>
            </div>
          </div>
          <MarkdownPreview
            :content="bodyContent"
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
    <SummarizeModal
      v-if="summarizeOpen"
      :content="bodyContent"
      @insert="insertSummary"
      @close="summarizeOpen = false"
    />
    <CitationModal
      v-if="citationOpen"
      :frontmatter="frontmatter"
      @insert="insertCitation"
      @close="citationOpen = false"
    />
    <ToolbarScrapeModal v-if="scraperOpen" @close="scraperOpen = false" @insert="insertScrapedContent" />
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
import FrontmatterPills from "../molecules/editor/FrontmatterPills.vue";
import FrontmatterEditor from "../molecules/editor/FrontmatterEditor.vue";
import MarkdownPreview from "../molecules/MarkdownPreview.vue";
import ResearchPanel from "../molecules/editor/ResearchPanel.vue";
import SummarizeModal from "../molecules/editor/SummarizeModal.vue";
import CitationModal from "../molecules/editor/CitationModal.vue";
import ToolbarScrapeModal from "../molecules/editor/ToolbarScrapeModal.vue";
import { useShellStore } from "../../stores/shell";
import { useToast } from "../../composables/useToast";
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
  /** Hide the title + frontmatter doc header (e.g. compact slide-in panel). */
  hideHeader?: boolean;
  /** Force single-pane edit-only view — no split/prose toggle. */
  singlePane?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  content: "",
  title: "Untitled",
  readOnly: false,
  editMode: "prose",
  hideHeader: false,
  singlePane: false,
});

const emit = defineEmits<{
  "update:content": [value: string];
  "update:editMode": [value: "prose" | "code"];
  save: [value: string];
  close: [];
  publish: [];
  /** Fired when the split button is clicked in singlePane mode. */
  openSplit: [];
}>();

const shell = useShellStore();
const { toast } = useToast();

// ─── State ───────────────────────────────────────────────────────────
const initialDocument = parseDocument(props.content || "");
const bodyContent = ref(initialDocument.body);
const localEditMode = ref<"prose" | "code">(props.editMode);
const viewMode = ref<"edit" | "preview" | "split">(
  props.singlePane ? "edit" : "preview",
);
const researchOpen = ref(false);
const frontmatterEditorOpen = ref(false);
const summarizeOpen = ref(false);
const citationOpen = ref(false);
const scraperOpen = ref(false);

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
  if (props.singlePane) {
    // Allow edit ↔ preview toggle (single-pane code/prose).
    // Split opens the full Editor tab — emit openSplit instead.
    if (mode === "split") {
      emit("openSplit");
      return;
    }
    viewMode.value = mode; // "edit" or "preview"
    return;
  }
  viewMode.value = mode;
}

function openCodePane() {
  localEditMode.value = "code";
  emit("update:editMode", "code");
  viewMode.value = props.singlePane ? "edit" : "split";
}

function onEditorModeChange(mode: "prose" | "code") {
  localEditMode.value = mode;
  emit("update:editMode", mode);
}

// ─── Frontmatter ─────────────────────────────────────────────────────
const frontmatter = ref<Frontmatter>(initialDocument.frontmatter);
const hasFrontmatter = computed(
  () => Object.keys(frontmatter.value).length > 0,
);

function onFrontmatterChange(updated: Frontmatter) {
  frontmatter.value = updated;
  emitDocumentUpdate();
}

function saveFrontmatter(updated: Frontmatter) {
  onFrontmatterChange(updated);
  frontmatterEditorOpen.value = false;
}

// ─── Sync props ──────────────────────────────────────────────────────
watch(
  () => props.content,
  (val) => {
    const p = parseDocument(val);
    bodyContent.value = p.body;
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
  bodyContent.value = value;
  emitDocumentUpdate();
}

function handleSave() {
  emit("save", serializeDocument(bodyContent.value, frontmatter.value));
}

function handleToolbarAction(action: string) {
  if (action === "summarize") {
    summarizeOpen.value = true;
    return;
  }
  if (action === "scrape") {
    scraperOpen.value = true;
    return;
  }
  if (action === "outline") {
    researchOpen.value = !researchOpen.value;
    return;
  }
  if (action === "citation") {
    citationOpen.value = true;
    return;
  }
  toast(`${action.replaceAll("-", " ")} is available through its governed workflow.`, "info");
}

function insertSummary(summary: string) {
  bodyContent.value = `${bodyContent.value.replace(/\s*$/, "")}\n\n## Summary\n\n${summary}\n`;
  summarizeOpen.value = false;
  emitDocumentUpdate();
  toast("Summary inserted", "success");
}

function insertCitation(citation: string) {
  bodyContent.value = `${bodyContent.value.replace(/\s*$/, "")}\n\n${citation}\n`;
  citationOpen.value = false;
  emitDocumentUpdate();
  toast("Citation inserted", "success");
}

function insertScrapedContent(content: string) {
  bodyContent.value = `${bodyContent.value.replace(/\s*$/, "")}\n\n${content}\n`;
  scraperOpen.value = false;
  emitDocumentUpdate();
  toast("Research inserted", "success");
}

function emitDocumentUpdate() {
  emit("update:content", serializeDocument(bodyContent.value, frontmatter.value));
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
  min-height: var(--usx-control-size-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: 0;
  background: color-mix(in srgb, var(--usx-color-surface) 58%, transparent);
  overflow-x: auto;
}

.editor-panel__prose-bar .editor-toolbar {
  flex-shrink: 0;
}

.editor-panel__pane-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin-left: auto;
}

.editor-panel__pane-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  min-height: 0;
  padding: 0;
  border: var(--usx-border-width) solid transparent;
  border-radius: var(--usx-radius-md);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
}

.editor-panel__pane-actions button:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.editor-panel__pane-actions button:disabled {
  opacity: .4;
  cursor: default;
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
  padding: 0 var(--usx-spacing-lg) var(--usx-spacing-md);
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
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  min-height: 0;
  padding: 0;
  border: var(--usx-border-width) dashed var(--usx-color-border);
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
