<template>
  <div class="research-panel">
    <div class="research-panel__header">
      <span class="research-panel__heading">Research</span>
      <UBadge type="info" size="sm">{{ researchFiles.length }}</UBadge>
    </div>

    <!-- Empty state -->
    <div v-if="!researchFiles.length" class="research-panel__empty">
      <UIcon name="science" />
      <p>No research docs yet.</p>
      <p class="research-panel__hint">
        Open a card from BrowserUI to create one.
      </p>
    </div>

    <!-- Research doc list -->
    <div v-else class="research-panel__list">
      <div
        v-for="file in researchFiles"
        :key="file.id"
        class="research-item"
        :class="{ 'research-item--active': ws.selectedId === file.id }"
      >
        <input v-model="selectedIds" type="checkbox" :value="file.id" :aria-label="`Select ${displayTitle(file)}`" />
        <button type="button" class="research-item__open" @click="ws.selectFile(file)">
        <div class="research-item__title">{{ displayTitle(file) }}</div>
        <div v-if="fileSource(file)" class="research-item__source">
          <UIcon name="public" />
          {{ fileSource(file) }}
        </div>
        <div v-if="fileDate(file)" class="research-item__date">
          {{ fileDate(file) }}
        </div>
        </button>
      </div>
    </div>
    <button v-if="selectedIds.length >= 2" type="button" class="research-panel__combine" @click="showCombine = true">Combine Research ({{ selectedIds.length }})</button>

    <!-- Actions -->
    <div
      v-if="ws.selectedId && selectedIsResearch"
      class="research-panel__actions"
    >
      <button
        class="research-panel__action-btn"
        title="Summarize"
        @click="openSummarize"
      >
        <UIcon name="summarize" /> Summarize
      </button>
      <button
        class="research-panel__action-btn"
        title="Copy to Binder"
        @click="copyToBinder"
      >
        <UIcon name="folder_copy" /> Copy to Binder
      </button>
    </div>

    <!-- Summarize modal -->
    <SummarizeModal
      v-if="showSummarize"
      :content="currentContent"
      @insert="onInsertSummary"
      @close="showSummarize = false"
    />
    <CombineResearchModal v-if="showCombine" :sources="selectedSources" @close="showCombine = false" @create="createSynthesis" />
    <div v-if="variantParent" class="research-panel__variant"><span>Variant of {{ variantParent.name }}</span><button type="button" @click="syncMetadata">Sync metadata</button><button type="button" @click="showVariantDiff = true">Compare</button></div>
    <Teleport to="body"><div v-if="showVariantDiff && variantParent" class="variant-diff-overlay" @click.self="showVariantDiff = false"><section role="dialog" aria-modal="true" aria-label="Compare variant" class="variant-diff"><button type="button" @click="showVariantDiff = false">Close</button><DiffEditorPanel :original="variantParent.content || ''" :modified="currentContent" has-repository-diff /></section></div></Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import UIcon from "../../atoms/UIcon.vue";
import UBadge from "../../atoms/UBadge.vue";
import SummarizeModal from "./SummarizeModal.vue";
import CombineResearchModal from "./CombineResearchModal.vue";
import DiffEditorPanel from "./DiffEditorPanel.vue";
import { useWorkspaceStore } from "../../../stores/workspace";
import { getEditorSurface } from "../../../composables/useEditorSurface";
import { parseDocument } from "../../../utils/frontmatterParser";
import { useToast } from "../../../composables/useToast";
import { SNACKBAR_BASE } from "../../../api/base";
import { syncVariantMetadata } from "../../../utils/documentVariant";

const ws = useWorkspaceStore();
const editorSurface = getEditorSurface();
const { toast } = useToast();
const showSummarize = ref(false);
const showCombine = ref(false);
const selectedIds = ref<string[]>([]);
const showVariantDiff = ref(false);

// Files tagged type: research in frontmatter
const researchFiles = computed(() =>
  ws.tree
    .flatMap((n) => [n, ...(n.children ?? [])])
    .filter((n) => {
      if (n.type !== "file") return false;
      const { frontmatter } = parseDocument(n.content ?? "");
      return frontmatter.type === "research";
    }),
);

const selectedIsResearch = computed(() =>
  researchFiles.value.some((f) => f.id === ws.selectedId),
);

const currentContent = computed(
  () => editorSurface.currentFile.value?.content ?? "",
);
const selectedSources = computed(() => researchFiles.value.filter((file) => selectedIds.value.includes(file.id)).map((file) => ({ path: file.path, name: file.name, content: file.content ?? "" })));
const allFiles = computed(() => {
  const result: typeof ws.tree = [];
  const visit = (nodes: typeof ws.tree) => nodes.forEach((node) => { if (node.type === "file") result.push(node); if (node.children) visit(node.children); });
  visit(ws.tree); return result;
});
const variantParent = computed(() => {
  const current = editorSurface.currentFile.value;
  if (!current) return null;
  const parentPath = String(parseDocument(current.content).frontmatter.parent || "");
  return allFiles.value.find((file) => file.path === parentPath) || null;
});
async function syncMetadata() {
  const current = editorSurface.currentFile.value;
  if (!current || !variantParent.value) return;
  const content = syncVariantMetadata(variantParent.value.content ?? "", current.content);
  editorSurface.updateContent(content);
  await ws.saveFile(current.path, content, current.version);
  toast("Variant metadata synchronized", "success");
}

async function createSynthesis(result: { filename: string; content: string }) {
  const node = await ws.createFile("/research", result.filename);
  ws.updateFileContent(node.id, result.content);
  await ws.saveFile(node.path, result.content);
  showCombine.value = false;
  selectedIds.value = [];
  toast("Research synthesis created", "success");
}

function displayTitle(file: { name: string; content?: string }): string {
  const { frontmatter } = parseDocument(file.content ?? "");
  return (frontmatter.title as string) || file.name.replace(/\.md$/, "");
}

function fileSource(file: { content?: string }): string {
  const { frontmatter } = parseDocument(file.content ?? "");
  try {
    return frontmatter.site
      ? String(frontmatter.site)
      : frontmatter.source
        ? new URL(String(frontmatter.source)).hostname.replace(/^www\./, "")
        : "";
  } catch {
    return "";
  }
}

function fileDate(file: { content?: string }): string {
  const { frontmatter } = parseDocument(file.content ?? "");
  return frontmatter.date ? String(frontmatter.date).slice(0, 10) : "";
}

function openSummarize() {
  showSummarize.value = true;
}

function onInsertSummary(summary: string) {
  const current = editorSurface.currentFile.value;
  if (!current) return;
  const appended = `${current.content}\n\n---\n\n## Summary\n\n${summary}`;
  editorSurface.updateContent(appended);
  showSummarize.value = false;
  toast("Summary inserted", "success");
}

async function copyToBinder() {
  const current = editorSurface.currentFile.value;
  if (!current) return;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/editor/save-to-binder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: current.filename,
        content: current.content,
        source: "markdown-editor",
      }),
      signal: AbortSignal.timeout(10000),
    });
    if (res.ok) {
      toast(`"${current.filename}" saved to Binder`, "success");
    } else {
      toast("Failed to save to Binder", "error");
    }
  } catch {
    toast("Backend unavailable", "error");
  }
}
</script>

<style scoped>
.research-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--usx-color-surface-variant);
  border-left: 1px solid var(--usx-color-border);
  overflow: hidden;
}

.research-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
  flex-shrink: 0;
}

.research-panel__heading {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--usx-color-on-surface-muted);
}

.research-panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: var(--usx-spacing-xl);
  color: var(--usx-color-on-surface-muted);
  text-align: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
}

.research-panel__hint {
  font-size: var(--usx-font-size-xs);
  opacity: 0.7;
}

.research-panel__list {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-xs) 0;
}

.research-item {
  width: 100%;
  display: flex;
  flex-direction: row;
  gap: 2px;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background-color 100ms ease;
}
.research-item__open { display:flex;flex:1;min-width:0;flex-direction:column;align-items:flex-start;padding:0;border:0;background:transparent;text-align:left;cursor:pointer; }
.research-panel__combine { margin:var(--usx-spacing-sm);min-height:var(--usx-touch-min); }
.research-panel__variant{display:flex;align-items:center;justify-content:space-between;gap:var(--usx-spacing-sm);padding:var(--usx-spacing-sm);border-top:var(--usx-border-width) solid var(--usx-color-border)}.variant-diff-overlay{position:fixed;inset:0;z-index:2200;display:grid;place-items:center;padding:var(--usx-spacing-lg);background:rgb(0 0 0 / 50%)}.variant-diff{display:flex;flex-direction:column;width:min(70rem,100%);height:min(44rem,90vh);padding:var(--usx-spacing-md);background:var(--usx-color-surface)}

.research-item:hover {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    transparent
  );
}

.research-item--active {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 14%,
    transparent
  );
  border-left: 3px solid var(--usx-color-primary);
}

.research-item__title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.research-item--active .research-item__title {
  color: var(--usx-color-primary);
}

.research-item__source,
.research-item__date {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.research-panel__actions {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-top: 1px solid var(--usx-color-border);
  flex-shrink: 0;
}

.research-panel__action-btn {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 120ms ease;
  width: 100%;
}

.research-panel__action-btn:hover {
  background-color: var(--usx-color-surface);
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}
</style>
