/**
 * @component PreviewTab — Prose-style rendered markdown preview with citations.
 */
<template>
  <div class="preview-tab">
    <div class="preview-tab__toolbar">
      <button class="usx-btn" @click="$emit('edit')">Edit</button>
      <button class="usx-btn" @click="$emit('chatui')">Send to ChatUI</button>
    </div>
    <div class="preview-tab__meta" v-if="meta?.source">
      <span>Source: <a :href="meta?.source" target="_blank">{{ sourceLabel }}</a></span>
      <span v-if="meta?.score !== undefined">Score: {{ meta.score }}/5</span>
    </div>
    <div class="preview-tab__content prose" v-html="rendered"></div>
    <div v-if="meta?.tags?.length" class="preview-tab__tags">
      <span v-for="t in meta.tags" :key="t" class="preview-tab__tag">{{ t }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"

const props = defineProps<{
  content: string
  meta?: { source?: string; score?: number; tags?: string[]; title?: string }
}>()

defineEmits<{ edit: []; chatui: [] }>()

const sourceLabel = computed(() => {
  try { return new URL(props.meta?.source || "").hostname.replace(/^www\./, "") }
  catch { return "" }
})

const rendered = computed(() => {
  // Simple markdown-to-HTML renderer
  let html = props.content
    .replace(/^### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^## (.+)$/gm, "<h3>$1</h3>")
    .replace(/^# (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/\n\n/g, "</p><p>")
  return `<p>${html}</p>`
})
</script>

<style scoped>
.preview-tab { padding: var(--usx-spacing-sm); }
.preview-tab__toolbar { display: flex; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-sm); }
.preview-tab__meta { display: flex; gap: var(--usx-spacing-sm); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-sm); }
.preview-tab__meta a { color: var(--usx-color-primary); }
/* Markdown typography comes from the Prose contract (@udos/usx-tokens/usx-prose.css). */
.preview-tab__tags { display: flex; gap: var(--usx-spacing-xs); margin-top: var(--usx-spacing-md); }
.preview-tab__tag { font-size: var(--usx-font-size-xs); min-height: calc(var(--usx-touch-min-sm) - var(--usx-spacing-sm)); padding: 0 var(--usx-spacing-sm); border-radius: var(--usx-radius-full); background: var(--usx-color-surface-variant); display: inline-flex; align-items: center; }
.usx-btn { border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); min-height: var(--usx-control-size-sm); padding: 0 var(--usx-spacing-sm); cursor: pointer; background: var(--usx-color-surface); font-size: var(--usx-font-size-xs); transition: all var(--usx-transition-base); }
.usx-btn:hover { background: var(--usx-color-surface-hover); border-color: var(--usx-color-primary); }
</style>
