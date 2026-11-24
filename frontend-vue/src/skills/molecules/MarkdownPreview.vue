<template>
  <div ref="rootRef" class="md-preview" :class="`md-preview--${format}`">
    <slot name="metadata" />
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
    <div v-else class="md-preview__prose usx-prose" v-html="html" />

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

/* Typography is owned by the Prose contract
   (@udos/usx-tokens/usx-prose.css). Only uDOS document policy lives here. */


/* In uDOS prose, thematic/page-break markers remain authoring metadata.
   Story/print renderers retain their own separators and pagination. */
.md-preview--prose :is(.md-preview__prose, .usx-prose) hr {
  display: none;
}

.md-preview--prose :is(.md-preview__prose, .usx-prose) h2 {
  border-block-end: 0;
  padding-block-end: 0;
}

/* ─── Callouts ───────────────────────────────────────────────────── */

.md-callout {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  margin-block: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  border-inline-start: calc(var(--usx-border-width-thick) * 2) solid
    var(--usx-color-info);
  background-color: color-mix(in srgb, var(--usx-color-info) 8%, var(--usx-color-surface));
}

.md-callout--warning {
  border-inline-start-color: var(--usx-color-warning);
  background-color: color-mix(
    in srgb,
    var(--usx-color-warning) 8%,
    var(--usx-color-surface)
  );
}

.md-callout--caution {
  border-inline-start-color: var(--usx-color-danger);
  background-color: color-mix(in srgb, var(--usx-color-danger) 8%, var(--usx-color-surface));
}

.md-callout--tip {
  border-inline-start-color: var(--usx-color-success);
  background-color: color-mix(
    in srgb,
    var(--usx-color-success) 8%,
    var(--usx-color-surface)
  );
}

.md-callout--important {
  border-inline-start-color: var(--usx-color-primary);
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    var(--usx-color-surface)
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
  font-size: var(--usx-icon-size-sm);
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
  line-height: var(--usx-line-height-normal);
  color: var(--usx-color-on-surface);
}

.md-callout__body p {
  margin: 0;
}
</style>

<style scoped>
.md-preview {
  font-family: var(--usx-font-family-reading, var(--usx-font-family-serif));
  height: 100%;
  overflow-y: auto;
  background-color: var(--usx-color-background);
}

.md-preview__prose {
  padding: clamp(var(--usx-spacing-md), 4vw, calc(var(--usx-spacing-2xl) * 1.5));
  max-inline-size: var(--usx-prose-width);
  margin-inline: auto;
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
  margin-block: var(--usx-spacing-lg);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
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
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-block-end: var(--usx-border-width) solid var(--usx-color-border);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
}

.md-diagram__label {
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-semibold);
  letter-spacing: var(--usx-letter-spacing-wide);
  text-transform: uppercase;
  font-size: var(--usx-font-size-xs);
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
  border-radius: var(--usx-radius-sm);
  background: transparent;
  border: var(--usx-border-width) solid var(--usx-color-border);
  color: var(--usx-color-on-surface-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.md-diagram__btn:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
  border-color: var(--usx-color-primary);
}

.md-diagram__source {
  padding: var(--usx-spacing-sm);
  border-block-start: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-background);
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
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
  font-size: 12px;
}

/* ─── Teletext Screen Display ──────────────────────────────────── */

.teletext-screen {
  /* Lattice palette is canon, not theme (GRIDCORE-STANDARDS.json). */
  background: var(--gridcore-palette-0) !important;
  color: var(--gridcore-palette-7) !important;
  font-family: "VT323", "Press Start 2P", monospace !important;
  font-size: 16px !important;
  line-height: var(--usx-line-height-tight) !important;
  letter-spacing: var(--usx-letter-spacing-wide);
  padding: var(--usx-spacing-md) !important;
  border: var(--usx-border-width-thick) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
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
