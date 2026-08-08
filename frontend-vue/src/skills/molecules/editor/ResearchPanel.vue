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
      <button
        v-for="file in researchFiles"
        :key="file.id"
        class="research-item"
        :class="{ 'research-item--active': ws.selectedId === file.id }"
        @click="ws.selectFile(file)"
      >
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
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import UIcon from "../../atoms/UIcon.vue";
import UBadge from "../../atoms/UBadge.vue";
import SummarizeModal from "./SummarizeModal.vue";
import { useWorkspaceStore } from "../../../stores/workspace";
import { getEditorSurface } from "../../../composables/useEditorSurface";
import { parseDocument } from "../../../utils/frontmatterParser";
import { useToast } from "../../../composables/useToast";
import { SNACKBAR_BASE } from "../../../api/base";

const ws = useWorkspaceStore();
const editorSurface = getEditorSurface();
const { toast } = useToast();
const showSummarize = ref(false);

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
        source: "bangle-editor",
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
  flex-direction: column;
  gap: 2px;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background-color 100ms ease;
}

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
