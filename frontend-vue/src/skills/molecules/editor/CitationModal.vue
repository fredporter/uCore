<template>
  <Teleport to="body">
    <div class="citation-overlay" @click.self="emit('close')">
      <section class="citation-modal" role="dialog" aria-modal="true" aria-labelledby="citation-title">
        <header><h2 id="citation-title">Insert citation</h2><button type="button" aria-label="Close citation generator" @click="emit('close')"><UIcon name="close" /></button></header>
        <label>Source URL<input v-model="url" type="url" placeholder="https://…" /></label>
        <label>Title<input v-model="title" /></label>
        <label>Author<input v-model="author" /></label>
        <label>Format<select v-model="format"><option>APA</option><option>MLA</option><option>Chicago</option></select></label>
        <div class="citation-modal__preview" aria-live="polite">{{ preview }}</div>
        <footer><button type="button" @click="emit('close')">Cancel</button><button type="button" :disabled="!url.trim() || loading" @click="enrich">{{ loading ? "Reading metadata…" : "Read metadata" }}</button><button type="button" :disabled="!url.trim()" @click="insert">Insert citation</button></footer>
      </section>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import UIcon from "../../atoms/UIcon.vue";
import { citationGenerator, generateCitation, type CitationFormat } from "../../../utils/citationGenerator";
import type { Frontmatter } from "../../../utils/frontmatterParser";

const props = defineProps<{ frontmatter: Frontmatter }>();
const emit = defineEmits<{ close: []; insert: [citation: string] }>();
const url = ref(String(props.frontmatter.source || props.frontmatter.url || ""));
const title = ref(String(props.frontmatter.title || ""));
const author = ref(String(props.frontmatter.author || ""));
const format = ref<CitationFormat>("APA");
const loading = ref(false);
const enrichedCitation = ref("");
const metadata = computed(() => ({ url: url.value, title: title.value, author: author.value, site: String(props.frontmatter.site || ""), published: String(props.frontmatter.date || "") }));
const preview = computed(() => enrichedCitation.value || (url.value.trim() ? citationGenerator(metadata.value, format.value) : "Add a source URL to preview the citation."));
watch([url, title, author, format], () => { enrichedCitation.value = ""; });
async function enrich() { loading.value = true; try { enrichedCitation.value = await generateCitation(metadata.value, format.value); } finally { loading.value = false; } }
function insert() { if (url.value.trim()) emit("insert", preview.value); }
</script>

<style scoped>
.citation-overlay { position: fixed; inset: 0; z-index: 2100; display: grid; place-items: center; padding: var(--usx-spacing-lg); background: rgb(0 0 0 / 50%); }
.citation-modal { display: grid; gap: var(--usx-spacing-md); width: min(32rem, 100%); padding: var(--usx-spacing-lg); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); }
header, footer { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-sm); } h2 { margin: 0; } label { display: grid; gap: var(--usx-spacing-xs); } input, select { min-height: var(--usx-touch-min); } header button { margin-left: auto; } footer { justify-content: flex-end; }
.citation-modal__preview { padding: var(--usx-spacing-md); border-radius: var(--usx-radius-md); background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); }
</style>
