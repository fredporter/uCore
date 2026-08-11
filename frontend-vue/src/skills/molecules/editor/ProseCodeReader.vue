/** * @component ProseCodeReader * @description Read-only file viewer — renders
Markdown as styled prose * or syntax-highlighted code in a read-only CodeMirror
pane. * Used in the Repository tab of the Developer Surface. */
<template>
  <div class="prose-code-reader">
    <!-- Empty state -->
    <div v-if="!fileName" class="prose-code-reader__empty">
      <UIcon name="description" class="prose-code-reader__empty-icon" />
      <p>Select a file in the sidebar to preview</p>
    </div>

    <!-- Loading -->
    <div v-else-if="loading" class="prose-code-reader__loading">
      <UIcon name="sync" class="prose-code-reader__loading-spinner" />
      <span>Loading {{ fileName }}...</span>
    </div>

    <!-- Markdown prose view -->
    <div v-else-if="isMarkdown" class="prose-code-reader__prose">
      <div class="prose-code-reader__prose-header">
        <UIcon :name="fileIcon" class="prose-code-reader__prose-header-icon" />
        <span class="prose-code-reader__prose-header-name">{{ fileName }}</span>
        <span class="prose-code-reader__prose-header-lang">Markdown</span>
      </div>
      <div class="prose-code-reader__prose-body" v-html="renderedMarkdown" />
    </div>

    <!-- Code read-only view -->
    <CodeEditorCore
      v-else
      :model-value="content"
      :filename="fileName"
      :read-only="true"
      :show-fold-gutter="true"
      :show-active-line="false"
      placeholder=""
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Marked } from "marked";
import UIcon from "../../atoms/UIcon.vue";
import CodeEditorCore from "./CodeEditorCore.vue";
import { languageFor } from "./codeLanguages";

// ── Configure marked (v18 API) ──────────────────────────────────────
// marked.setOptions() is removed in v18; use the instance constructor

const markedInstance = new Marked({
  breaks: true,
  gfm: true,
});

// ── Props ─────────────────────────────────────────────────────────────

interface Props {
  fileName?: string;
  content?: string;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  fileName: "",
  content: "",
  loading: false,
});

// ── Computed ──────────────────────────────────────────────────────────

const MARKDOWN_EXTS = new Set([
  "md",
  "mdx",
  "markdown",
  "mdown",
  "mkdn",
  "mkd",
]);

const isMarkdown = computed(() => {
  if (!props.fileName) return false;
  const ext = props.fileName.split(".").pop()?.toLowerCase() ?? "";
  return MARKDOWN_EXTS.has(ext);
});

const renderedMarkdown = computed(() => {
  if (!isMarkdown.value || !props.content) return "";
  try {
    return markedInstance.parse(props.content) as string;
  } catch {
    return `<pre>${escapeHtml(props.content)}</pre>`;
  }
});

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const fileIcon = computed(() => {
  if (!props.fileName) return "description";
  const lang = languageFor(props.fileName);
  if (lang === "markdown") return "article";
  if (lang === "python") return "code";
  if (lang === "javascript" || lang === "typescript") return "javascript";
  if (lang === "html") return "html";
  if (lang === "css" || lang === "scss") return "css";
  return "description";
});
</script>

<style scoped>
.prose-code-reader {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: var(--usx-color-background);
}

/* ── Empty ─────────────────────────────────── */

.prose-code-reader__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
}

.prose-code-reader__empty-icon {
  font-size: 48px;
  opacity: 0.3;
}

.prose-code-reader__empty p {
  margin: 0;
  font-size: var(--usx-font-size-base);
}

/* ── Loading ───────────────────────────────── */

.prose-code-reader__loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.prose-code-reader__loading-spinner {
  animation: pcr-spin 1s linear infinite;
}

@keyframes pcr-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* ── Prose (Markdown) ───────────────────────── */

.prose-code-reader__prose {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.prose-code-reader__prose-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.prose-code-reader__prose-header-icon {
  color: var(--usx-color-primary);
}

.prose-code-reader__prose-header-name {
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  flex: 1;
}

.prose-code-reader__prose-header-lang {
  font-size: var(--usx-font-size-xs);
  padding: 1px 6px;
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
}

.prose-code-reader__prose-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-lg) var(--usx-spacing-xl);
  font-family: var(--usx-font-family-sans);
  font-size: var(--usx-font-size-base);
  line-height: 1.7;
  color: var(--usx-color-on-surface);
}

/* Markdown content styling */
.prose-code-reader__prose-body :deep(h1) {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  margin: 0 0 var(--usx-spacing-md);
  padding-bottom: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.prose-code-reader__prose-body :deep(h2) {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-semibold);
  margin: var(--usx-spacing-xl) 0 var(--usx-spacing-sm);
}

.prose-code-reader__prose-body :deep(h3) {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: var(--usx-spacing-lg) 0 var(--usx-spacing-sm);
}

.prose-code-reader__prose-body :deep(p) {
  margin: 0 0 var(--usx-spacing-sm);
}

.prose-code-reader__prose-body :deep(a) {
  color: var(--usx-color-primary);
  text-decoration: none;
}

.prose-code-reader__prose-body :deep(a:hover) {
  text-decoration: underline;
}

.prose-code-reader__prose-body :deep(code) {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  padding: 2px 6px;
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

.prose-code-reader__prose-body :deep(pre) {
  margin: var(--usx-spacing-md) 0;
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  overflow-x: auto;
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  line-height: 1.5;
}

.prose-code-reader__prose-body :deep(pre code) {
  padding: 0;
  background: none;
  font-size: inherit;
}

.prose-code-reader__prose-body :deep(blockquote) {
  margin: var(--usx-spacing-md) 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-left: 3px solid var(--usx-color-primary);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
}

.prose-code-reader__prose-body :deep(img) {
  max-width: 100%;
  border-radius: var(--usx-radius-md);
}

.prose-code-reader__prose-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: var(--usx-spacing-md) 0;
}

.prose-code-reader__prose-body :deep(th),
.prose-code-reader__prose-body :deep(td) {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  text-align: left;
}

.prose-code-reader__prose-body :deep(th) {
  background: var(--usx-color-surface-variant);
  font-weight: var(--usx-font-weight-semibold);
}

.prose-code-reader__prose-body :deep(ul),
.prose-code-reader__prose-body :deep(ol) {
  padding-left: var(--usx-spacing-xl);
  margin: var(--usx-spacing-sm) 0;
}

.prose-code-reader__prose-body :deep(li) {
  margin-bottom: var(--usx-spacing-xs);
}

.prose-code-reader__prose-body :deep(hr) {
  border: none;
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  margin: var(--usx-spacing-xl) 0;
}
</style>
