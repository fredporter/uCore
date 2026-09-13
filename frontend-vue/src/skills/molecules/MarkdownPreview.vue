<template>
  <div ref="rootRef" class="md-preview" :class="`md-preview--${format}`">
    <!-- Story format: slide viewer with navigation -->
    <template v-if="format === 'story' && slides.length > 1">
      <div class="md-preview__slide-bar">
        <button
          class="md-preview__slide-btn"
          :disabled="currentSlide === 0"
          @click="currentSlide--"
        >
          <span class="material-symbols-outlined">chevron_left</span>
        </button>
        <span class="md-preview__slide-counter">
          {{ currentSlide + 1 }} / {{ slides.length }}
        </span>
        <button
          class="md-preview__slide-btn"
          :disabled="currentSlide === slides.length - 1"
          @click="currentSlide++"
        >
          <span class="material-symbols-outlined">chevron_right</span>
        </button>
      </div>
      <div class="md-preview__slide-content" v-html="slides[currentSlide]" />
    </template>

    <!-- Prose / fallback: full rendered HTML -->
    <div v-else class="md-preview__prose" v-html="html" />

    <!-- Loading state -->
    <div v-if="loading" class="md-preview__loading">
      <span class="material-symbols-outlined">refresh</span>
      Rendering…
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component MarkdownPreview
 * @description Renders markdown as HTML via markdownRenderer. Supports prose and story formats,
 * diagrams (Mermaid, declarative SVG charts), Teletext character grids, and KaTeX math.
 */
import { ref, watch, onMounted, nextTick } from "vue";
import {
  renderDocument,
  type MarkdownFormat,
} from "../../utils/markdownRenderer";
import { hydrateDiagrams } from "../../utils/diagramHydrator";

const props = defineProps<{
  content: string;
  filename?: string;
}>();

const rootRef = ref<HTMLElement | null>(null);
const html = ref("");
const format = ref<MarkdownFormat>("prose");
const slides = ref<string[]>([]);
const currentSlide = ref(0);
const loading = ref(false);

async function update() {
  if (!props.content) {
    html.value = "";
    return;
  }
  loading.value = true;
  try {
    const result = await renderDocument(props.content, props.filename);
    html.value = result.html;
    format.value = result.format;

    // Split story HTML into individual slide sections
    if (result.format === "story") {
      const parser = new DOMParser();
      const doc = parser.parseFromString(result.html, "text/html");
      const sections = doc.querySelectorAll("section");
      if (sections.length > 1) {
        slides.value = Array.from(sections).map((s) => s.outerHTML);
        currentSlide.value = 0;
      } else {
        slides.value = [];
      }
    } else {
      slides.value = [];
    }
  } finally {
    loading.value = false;
  }

  await nextTick();
  if (rootRef.value) {
    await hydrateDiagrams(rootRef.value);
  }
}

watch(currentSlide, async () => {
  await nextTick();
  if (rootRef.value) {
    await hydrateDiagrams(rootRef.value);
  }
});

watch(() => props.content, update, { immediate: false });
onMounted(update);
</script>

<style>
/* ─── Prose content styles (global: apply inside v-html) ─────────── */

.md-preview__prose h1,
.md-preview__prose h2,
.md-preview__prose h3,
.md-preview__prose h4 {
  color: var(--usx-color-on-surface);
  margin: var(--usx-spacing-lg) 0 var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  line-height: 1.3;
}

.md-preview__prose h1 {
  font-size: var(--usx-font-size-2xl);
}
.md-preview__prose h2 {
  font-size: var(--usx-font-size-xl);
  border-bottom: 1px solid var(--usx-color-border);
  padding-bottom: var(--usx-spacing-xs);
}
.md-preview__prose h3 {
  font-size: var(--usx-font-size-lg);
}

.md-preview__prose p {
  margin: var(--usx-spacing-sm) 0;
  color: var(--usx-color-on-surface);
  line-height: 1.7;
}

.md-preview__prose a {
  color: var(--usx-color-primary);
}

.md-preview__prose code {
  font-family: var(--usx-font-family-mono);
  font-size: 0.875em;
  background-color: var(--usx-color-surface-variant);
  padding: 2px 5px;
  border-radius: var(--usx-radius-sm);
}

.md-preview__prose pre {
  background-color: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-md);
  overflow-x: auto;
  margin: var(--usx-spacing-md) 0;
}

.md-preview__prose pre code {
  background: none;
  padding: 0;
  font-size: var(--usx-font-size-sm);
}

.md-preview__prose blockquote {
  border-left: 3px solid var(--usx-color-border);
  margin: var(--usx-spacing-md) 0;
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
}

.md-preview__prose table {
  width: 100%;
  border-collapse: collapse;
  margin: var(--usx-spacing-md) 0;
  font-size: var(--usx-font-size-sm);
}

.md-preview__prose th,
.md-preview__prose td {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
}

.md-preview__prose th {
  background-color: var(--usx-color-surface-variant);
  font-weight: var(--usx-font-weight-semibold);
}

.md-preview__prose ul,
.md-preview__prose ol {
  padding-left: var(--usx-spacing-xl);
  margin: var(--usx-spacing-sm) 0;
}

.md-preview__prose li {
  margin: var(--usx-spacing-xs) 0;
  line-height: 1.6;
}

.md-preview__prose hr {
  border: none;
  border-top: 1px solid var(--usx-color-border);
  margin: var(--usx-spacing-xl) 0;
}

/* In uDOS prose, thematic/page-break markers remain authoring metadata.
   Story/print renderers retain their own separators and pagination. */
.md-preview--prose .md-preview__prose hr {
  display: none;
}

.md-preview--prose .md-preview__prose h2 {
  border-bottom: 0;
  padding-bottom: 0;
}

/* ─── Callouts ───────────────────────────────────────────────────── */

.md-callout {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  margin: var(--usx-spacing-md) 0;
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  border-left: 4px solid var(--usx-color-info);
  background-color: color-mix(in srgb, var(--usx-color-info) 8%, transparent);
}

.md-callout--warning {
  border-left-color: var(--usx-color-warning);
  background-color: color-mix(
    in srgb,
    var(--usx-color-warning) 8%,
    transparent
  );
}

.md-callout--caution {
  border-left-color: var(--usx-color-danger);
  background-color: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
}

.md-callout--tip {
  border-left-color: var(--usx-color-success);
  background-color: color-mix(
    in srgb,
    var(--usx-color-success) 8%,
    transparent
  );
}

.md-callout--important {
  border-left-color: var(--usx-color-primary);
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    transparent
  );
}

.md-callout__label {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-sm);
}

.md-callout__label .material-symbols-outlined {
  font-size: 16px;
}

.md-callout--note .md-callout__label {
  color: var(--usx-color-info);
}
.md-callout--warning .md-callout__label {
  color: var(--usx-color-warning);
}
.md-callout--caution .md-callout__label {
  color: var(--usx-color-danger);
}
.md-callout--tip .md-callout__label {
  color: var(--usx-color-success);
}
.md-callout--important .md-callout__label {
  color: var(--usx-color-primary);
}

.md-callout__body {
  font-size: var(--usx-font-size-sm);
  line-height: 1.6;
  color: var(--usx-color-on-surface);
}

.md-callout__body p {
  margin: 0;
}
</style>

<style scoped>
.md-preview {
  height: 100%;
  overflow-y: auto;
  background-color: var(--usx-color-background);
}

.md-preview__prose {
  padding: clamp(var(--usx-spacing-md), 4vw, calc(var(--usx-spacing-2xl) * 1.5));
  max-width: 72ch;
  margin: 0 auto;
}

/* ─── Story slide viewer ──────────────────────────────────────── */

.md-preview__slide-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface-variant);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.md-preview__slide-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  cursor: pointer;
  color: var(--usx-color-on-surface);
}

.md-preview__slide-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.md-preview__slide-counter {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  min-width: 56px;
  text-align: center;
}

.md-preview__slide-content {
  padding: var(--usx-spacing-2xl);
  min-height: 300px;
}

/* ─── Loading ─────────────────────────────────────────────────── */

.md-preview__loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  justify-content: center;
  padding: var(--usx-spacing-xl);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

/* ─── Scrollbar ───────────────────────────────────────────────── */

.md-preview::-webkit-scrollbar {
  width: 6px;
}
.md-preview::-webkit-scrollbar-thumb {
  background-color: var(--usx-color-border);
  border-radius: 3px;
}

/* ─── Diagram & Chart containers ───────────────────────────────── */

.md-diagram {
  margin: var(--usx-spacing-lg) 0;
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface, #0b1120);
  border: 1px solid var(--usx-color-border, #334155);
  overflow: hidden;
  position: relative;
}

.md-diagram__viewport {
  padding: var(--usx-spacing-md);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow-x: auto;
}

.md-diagram__viewport svg,
.md-diagram--chart svg {
  max-width: 100%;
  height: auto;
}

.md-diagram__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: var(--usx-color-surface-variant, #1e293b);
  border-bottom: 1px solid var(--usx-color-border, #334155);
  font-size: 11px;
  font-family: var(--usx-font-family-mono, monospace);
}

.md-diagram__label {
  color: var(--usx-color-primary, #00e5ff);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-size: 10px;
}

.md-diagram__actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.md-diagram__btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--usx-radius-sm, 4px);
  background: transparent;
  border: 1px solid var(--usx-color-border, #334155);
  color: var(--usx-color-text-muted, #94a3b8);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.md-diagram__btn:hover {
  background: var(--usx-color-surface-hover, #334155);
  color: var(--usx-color-text, #f8fafc);
  border-color: var(--usx-color-primary, #00e5ff);
}

.md-diagram__source {
  padding: var(--usx-spacing-sm);
  border-top: 1px solid var(--usx-color-border, #334155);
  background: #0b1120;
}

.md-diagram__source pre {
  margin: 0;
  padding: 0;
  background: transparent;
}

.md-diagram__error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: var(--usx-spacing-sm);
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  font-size: 12px;
}

/* ─── Teletext Screen Display ──────────────────────────────────── */

.teletext-screen {
  background: #000000 !important;
  color: #ffffff !important;
  font-family: "VT323", "Press Start 2P", monospace !important;
  font-size: 16px !important;
  line-height: 1.25 !important;
  letter-spacing: 0.05em;
  padding: var(--usx-spacing-md) !important;
  border: 2px solid #334155;
  border-radius: 4px;
  overflow-x: auto;
}

/* ─── KaTeX Math Display ───────────────────────────────────────── */

.katex-display {
  margin: var(--usx-spacing-md) 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: var(--usx-spacing-xs) 0;
}
</style>
