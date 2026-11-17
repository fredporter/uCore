<template>
  <div class="editor-panel">
    <header v-if="!hideHeader || viewMode === 'preview'" class="editor-panel__doc-header">
      <div class="editor-panel__reading-header">
        <h1 class="editor-panel__reading-title" tabindex="0">{{ previewDocument.title }}</h1>
        <div class="editor-panel__pane-actions">
          <button v-if="viewMode === 'preview'" type="button" :title="canEditCopy ? 'Edit a copy' : 'Show code'" :aria-label="canEditCopy ? 'Edit a copy' : 'Show code'" @click="openCodePane">
            <UIcon name="edit_note" :size="20" />
          </button>
          <button v-else-if="viewMode === 'split'" type="button" title="Collapse prose" aria-label="Collapse prose" @click="viewMode = 'edit'">
            <UIcon name="right_panel_close" :size="20" />
          </button>
          <button v-if="viewMode !== 'preview'" type="button" title="Read document" aria-label="Read document" @click="viewMode = 'preview'">
            <UIcon name="visibility" :size="20" />
          </button>
          <button v-if="viewMode !== 'preview' && !readOnly" type="button" title="Save" aria-label="Save" @click="handleSave">
            <UIcon name="save" :size="20" />
          </button>
          <button v-if="!readOnly" type="button" title="Edit document properties" aria-label="Edit document properties" @click="frontmatterEditorOpen = true">
            <UIcon name="tune" :size="20" />
          </button>
          <button type="button" title="Publish" aria-label="Publish document" @click="emit('publish')">
            <UIcon name="publish" :size="20" />
          </button>
        </div>
      </div>
      <div v-if="hasKnowledgeMetadata" class="editor-panel__metadata">
        <div v-if="readingPills.length || previewDocument.needs.length" class="editor-panel__metadata-row" aria-label="Document metadata">
          <span v-for="pill in readingPills" :key="pill" class="editor-panel__tag">{{ pill }}</span>
          <RouterLink v-for="need in previewDocument.needs" :key="need" class="usx-btn editor-panel__tag"
            :to="{ path: '/workflow', query: { tab: 'skills', skill: skillForNeed(need) } }">{{ need }}</RouterLink>
        </div>
        <details v-if="originFields.length">
          <summary>Document identity and origin</summary>
          <dl><template v-for="[label, value] in originFields" :key="label"><dt>{{ label }}</dt><dd>{{ value }}</dd></template></dl>
        </details>
      </div>
    </header>
    <FrontmatterEditor
      :open="frontmatterEditorOpen"
      :model-value="frontmatter"
      @close="frontmatterEditorOpen = false"
      @save="saveFrontmatter"
    />

    <!-- Editing tools remain with the Markdown input. -->
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
          <template v-if="hideHeader" #toolbar-actions>
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
          <MarkdownPreview
            :content="previewDocument.body"
            :filename="currentFilename"
            class="editor-panel__preview"
          >

          </MarkdownPreview>
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
    <CombineResearchModal
      v-if="combineOpen"
      :sources="availableResearchSources"
      @create="handleCreateSynthesis"
      @close="combineOpen = false"
    />
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
import FrontmatterEditor from "../molecules/editor/FrontmatterEditor.vue";
import MarkdownPreview from "../molecules/MarkdownPreview.vue";
import ResearchPanel from "../molecules/editor/ResearchPanel.vue";
import SummarizeModal from "../molecules/editor/SummarizeModal.vue";
import CitationModal from "../molecules/editor/CitationModal.vue";
import ToolbarScrapeModal from "../molecules/editor/ToolbarScrapeModal.vue";
import CombineResearchModal from "../molecules/editor/CombineResearchModal.vue";
import { useSettingsStore } from "../../stores/settings";
import { useShellStore } from "../../stores/shell";
import { useToast } from "../../composables/useToast";
import { useWorkspaceStore, type FileNode } from "../../stores/workspace";
import { createVariantDocument } from "../../utils/documentVariant";
import {
  parseDocument,
  serializeDocument,
  type Frontmatter,
} from "../../utils/frontmatterParser";

// ─── Props ───────────────────────────────────────────────────────────
interface Props {
  content?: string;
  title?: string;
  documentPath?: string;
  readOnly?: boolean;
  canEditCopy?: boolean;
  startInEdit?: boolean;
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
  editCopy: [];
  /** Fired when the split button is clicked in singlePane mode. */
  openSplit: [];
}>();

const shell = useShellStore();
const settings = useSettingsStore();
const { toast } = useToast();
const workspace = useWorkspaceStore();

// ─── State ───────────────────────────────────────────────────────────
const initialDocument = parseDocument(props.content || "");
const bodyContent = ref(initialDocument.body);
const localEditMode = ref<"prose" | "code">(props.editMode);
const viewMode = ref<"edit" | "preview" | "split">(
  props.singlePane || props.startInEdit ? "edit" : "preview",
);
const researchOpen = ref(false);
const frontmatterEditorOpen = ref(false);
const summarizeOpen = ref(false);
const citationOpen = ref(false);
const scraperOpen = ref(false);
const combineOpen = ref(false);

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
  if (props.canEditCopy) emit("editCopy");
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

function skillForNeed(need: string) {
  return { formatting: "attach_context", enhancement: "attach_context", research: "ask_vault" }[need.toLowerCase()];
}

const previewDocument = computed(() => {
  const fm = frontmatter.value;
  const body = bodyContent.value;
  const legacyBlock = /^(\s*(?:#[ \t][^\r\n]+\r?\n\s*)?)((?:\*\*(?:Topic|Category|Difficulty|Generated):\*\*[^\r\n]*\r?\n?)+)/;
  const legacy: Record<string, string> = {};
  const renderedBody = body.replace(legacyBlock, (_, heading: string, metadata: string) => {
    for (const [, label, value] of metadata.matchAll(/^\*\*(Topic|Category|Difficulty|Generated):\*\*[ \t]+([^\r\n]+)/gm)) {
      legacy[label] = value.trim();
    }
    return heading;
  });
  const topicFolder = props.documentPath?.split("/global-knowledge/")[1]?.split("/").slice(0, -1);
  const list = (value: unknown): string[] => (Array.isArray(value) ? value : [value])
    .filter((item): item is string => typeof item === "string" && Boolean(item.trim())).map(item => item.trim());
  const needs = new Set(list(fm.needs));
  if (topicFolder?.length && /\[Placeholder\s*-/i.test(body)) needs.add("enhancement");
  if (topicFolder?.[0] === "contributor" && !/^#\s/m.test(body) && body.trim()) needs.add("formatting");
  return {
    title: typeof fm.title === "string" && fm.title.trim()
      ? fm.title.trim()
      : (renderedBody.match(/^\s*#[ \t]+([^\r\n]+)/)?.[1]?.trim()
        || docTitle.value.replace(/[+_]+/g, " ")),
    body: renderedBody.replace(/^\s*#[ \t]+[^\r\n]+(?:\r?\n|$)/, ""),
    topic: String(fm.topic || fm.category || legacy.Topic || legacy.Category || topicFolder?.[0] || ""),
    tags: [...new Set(list(fm.tags))],
    difficulty: String(fm.difficulty || legacy.Difficulty || ""),
    generated: legacy.Generated || "",
    status: String(fm.status || (needs.size ? "Needs review" : "")),
    needs: [...needs],
  };
});

const difficultyValue = computed(() => {
  const value = previewDocument.value.difficulty;
  if (settings.terminologyPack !== "storytelling") return value;
  const levels: Record<string, string> = { basic: "Apprentice", beginner: "Apprentice", intermediate: "Guide", advanced: "Sage", expert: "Sage" };
  return levels[value.toLowerCase()] || value;
});

const originFields = computed(() => {
  const fm = frontmatter.value;
  return [
    ["Universal ID", fm.uid], ["Origin date", fm.origin_date || previewDocument.value.generated || fm.created],
    ["Origin time", fm.origin_time], ["Origin place", fm.origin_place],
    ["Version", fm.version], ["Revision", fm.revision],
  ].flatMap(([label, value]): [string, string][] =>
    typeof label === "string" && value !== "" && (typeof value === "string" || typeof value === "number")
      ? [[label, String(value)]] : [],
  );
});

const readingPills = computed(() => {
  const { topic, tags, status } = previewDocument.value;
  return [...new Set([topic, ...tags, difficultyValue.value, status].filter(Boolean))];
});

const hasKnowledgeMetadata = computed(() => {
  const meta = previewDocument.value;
  return Boolean(meta.topic || meta.tags.length || meta.difficulty || meta.status || meta.needs.length || originFields.value.length);
});

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

watch(() => props.documentPath, () => {
  if (props.readOnly && !props.singlePane) viewMode.value = "preview";
});

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
  if (action === "combine") {
    combineOpen.value = true;
    return;
  }
  if (action === "variant") {
    void createVariant();
    return;
  }
  toast(`${action.replaceAll("-", " ")} is available through its governed workflow.`, "info");
}

function collectMarkdownFiles(nodes: FileNode[]): Array<{ path: string; name: string; content: string }> {
  const result: Array<{ path: string; name: string; content: string }> = [];
  for (const node of nodes) {
    if (node.type === "file" && node.name.endsWith(".md")) {
      result.push({
        path: node.path,
        name: node.name,
        content: node.content || `# ${node.name}\n\nNotes from ${node.name}.`,
      });
    }
    if (node.children?.length) {
      result.push(...collectMarkdownFiles(node.children));
    }
  }
  return result;
}

const availableResearchSources = computed(() => {
  const sources: Array<{ path: string; name: string; content: string }> = [];
  if (bodyContent.value) {
    sources.push({
      path: workspace.selectedFile?.path || "/current.md",
      name: currentFilename.value,
      content: serializeDocument(bodyContent.value, frontmatter.value),
    });
  }
  const treeFiles = collectMarkdownFiles(workspace.tree);
  for (const file of treeFiles) {
    if (file.name !== currentFilename.value && file.path !== workspace.selectedFile?.path) {
      sources.push(file);
    }
  }
  return sources;
});

async function handleCreateSynthesis(result: { filename: string; content: string }) {
  combineOpen.value = false;
  const parentFolder =
    workspace.selectedFile?.path.slice(
      0,
      workspace.selectedFile?.path.lastIndexOf("/"),
    ) || "/";
  const node = await workspace.createFile(parentFolder, result.filename);
  workspace.updateFileContent(node.id, result.content);
  await workspace.saveFile(node.path, result.content);
  toast("Research synthesis created", "success");
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

async function createVariant() {
  const parent = workspace.selectedFile;
  if (!parent) { toast("Save the document before creating a variant.", "warning"); return; }
  const stem = parent.name.replace(/\.md$/i, "");
  const variantId = `variant-${Date.now()}`;
  const filename = `${stem}-${variantId}.md`;
  const parentFolder = parent.path.slice(0, parent.path.lastIndexOf("/")) || "/";
  const content = createVariantDocument(serializeDocument(bodyContent.value, frontmatter.value), parent.path, variantId);
  const node = await workspace.createFile(parentFolder, filename);
  workspace.updateFileContent(node.id, content);
  await workspace.saveFile(node.path, content);
  toast("Variant created", "success");
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
.editor-panel__reading-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-sm);
}
.editor-panel__reading-header .editor-panel__pane-actions { flex: 0 0 auto; }
.editor-panel__reading-title {
  flex: 1;
  min-inline-size: 0;
  margin: 0;
  max-inline-size: 100%;
  overflow-x: auto;
  white-space: nowrap;
  font-size: var(--usx-font-size-xl);
}

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
  box-sizing: border-box;
  width: 32px;
  height: 32px;
  min-height: 32px;
  margin: 0;
  box-shadow: none;
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

.editor-panel__preview :deep(.md-preview__prose),
.editor-panel__preview :deep(.md-preview__slide-content) {
  padding: var(--document-editor-inset);
  max-width: none;
}

.editor-panel__preview :deep(.md-preview__prose > :first-child),
.editor-panel__preview :deep(.md-preview__slide-content > :first-child) {
  margin-block-start: 0;
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
  --document-editor-inset: clamp(var(--usx-spacing-md), 4vw, calc(var(--usx-spacing-2xl) * 1.5));
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.editor-panel__doc-header {
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  flex-shrink: 0;
  min-width: 0;
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
.editor-panel__metadata { font-size: var(--usx-font-size-sm); overflow-wrap: anywhere; }
.editor-panel__metadata-row { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; margin-bottom: 6px; }
.editor-panel__tag { background: var(--usx-color-surface-variant); border: 1px solid var(--usx-color-border); padding: 2px 8px; border-radius: 999px; }
.editor-panel__metadata summary { cursor: pointer; }
.editor-panel__metadata dl { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 4px 8px; }
.editor-panel__metadata dd { margin: 0; }
</style>
