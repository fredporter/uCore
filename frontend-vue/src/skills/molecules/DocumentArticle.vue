<template>
  <article ref="article" class="reading-article" @click="onLink">
    <details v-if="Object.keys(parsed.frontmatter).length" class="reading-properties"><summary>Document properties</summary><DocumentProperties :frontmatter="parsed.frontmatter" /></details>
    <details v-if="rendered.headings.length > 1" class="reading-contents"><summary>Contents</summary><nav aria-label="Document contents"><button v-for="heading in rendered.headings" :key="heading.id" class="usx-btn" @click="scrollTo(heading.id)">{{ heading.text }}</button></nav></details>
    <div class="reading-prose" v-html="rendered.html" />
  </article>
</template>
<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { parseReadingDocument } from '../../utils/readingDocument';
import { renderProseFast, sanitize } from '../../utils/markdownRenderer';
import { hydrateDiagrams } from '../../utils/diagramHydrator';
import DocumentProperties from './DocumentProperties.vue';
const props = defineProps<{ content: string }>();
const emit = defineEmits<{ navigate: [path: string] }>();
const article = ref<HTMLElement | null>(null);
const parsed = computed(() => parseReadingDocument(props.content));
const rendered = computed(() => {
  const document = new DOMParser().parseFromString(renderProseFast(parsed.value.body), 'text/html');
  const headings = [...document.querySelectorAll('h1,h2,h3')].map((heading, index) => {
    const id = `reading-section-${index}`; heading.id = id;
    return { id, text: heading.textContent || '' };
  });
  document.querySelectorAll('a[href^="http://"], a[href^="https://"]').forEach(link => {
    const citation = document.createElement('span');
    citation.className = 'reading-citation'; citation.textContent = link.textContent; citation.title = link.getAttribute('href') || '';
    link.replaceWith(citation);
  });
  return { headings, html: sanitize(document.body.innerHTML) };
});
function scrollTo(id: string) { article.value?.querySelector(`[id="${id}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
function onLink(event: MouseEvent) {
  const link = (event.target as HTMLElement).closest('a');
  const href = link?.getAttribute('href');
  if (href && !/^(?:[a-z]+:|#|\/\/)/i.test(href)) { event.preventDefault(); emit('navigate', href); }
}
watch(rendered, async () => { await nextTick(); if (article.value) await hydrateDiagrams(article.value); }, { immediate: true });
</script>
<style scoped>
.reading-article { width: min(100%, 72ch); margin-inline: auto; text-align: left; }
.reading-prose { font-family: var(--usx-font-family-reading, var(--usx-font-family-serif, Charter, Georgia, serif)); font-size: var(--usx-font-size-base); line-height: 1.7; overflow-wrap: anywhere; }
.reading-prose :deep(h1), .reading-prose :deep(h2), .reading-prose :deep(h3) { line-height: 1.3; scroll-margin-top: var(--usx-spacing-lg); }
.reading-prose :deep(p) { margin-bottom: 1em; }
.reading-prose :deep(pre), .reading-prose :deep(code) { font-family: var(--usx-font-family-mono); }
.reading-prose :deep(pre) { overflow-x: auto; line-height: 1.45; }
.reading-prose :deep(img) { max-width: 100%; }
.reading-prose :deep(.reading-citation) { border-radius: var(--usx-radius-full); background: var(--usx-color-surface-variant); padding: 2px 8px; font-family: var(--usx-font-family-sans, Inter, sans-serif); font-size: var(--usx-font-size-sm); }
.reading-contents { font-family: var(--usx-font-family-sans, Inter, sans-serif); margin-bottom: var(--usx-spacing-lg); }
.reading-contents nav { display: grid; justify-items: start; } .reading-contents .usx-btn { text-align: left; }
</style>
