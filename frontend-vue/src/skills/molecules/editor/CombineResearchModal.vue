<template><Teleport to="body"><div class="combine-overlay" @click.self="emit('close')"><section role="dialog" aria-modal="true" aria-labelledby="combine-title" class="combine-modal"><h2 id="combine-title">Combine research</h2><p>{{ sources.length }} documents selected</p><ul><li v-for="source in sources" :key="source.path">{{ source.name }}</li></ul><label>Synthesis format<select v-model="format"><option value="report">Report</option><option value="list">Evidence list</option><option value="venn">Venn comparison</option></select></label><footer><button type="button" @click="emit('close')">Cancel</button><button type="button" @click="create">Create synthesis</button></footer></section></div></Teleport></template>
<script setup lang="ts">
import { ref } from "vue";
import { buildResearchSynthesis, type ResearchSource, type SynthesisFormat } from "../../../utils/researchSynthesis";
const props = defineProps<{ sources: ResearchSource[] }>();
const emit = defineEmits<{ close: []; create: [result: { filename: string; content: string }] }>();
const format = ref<SynthesisFormat>("report");
function create() { emit("create", buildResearchSynthesis(props.sources, format.value)); }
</script>
<style scoped>.combine-overlay{position:fixed;inset:0;z-index:2200;display:grid;place-items:center;padding:var(--usx-spacing-lg);background:rgb(0 0 0 / 50%)}.combine-modal{display:grid;gap:var(--usx-spacing-md);width:min(32rem,100%);padding:var(--usx-spacing-lg);border:var(--usx-border-width) solid var(--usx-color-border);border-radius:var(--usx-radius-lg);background:var(--usx-color-surface)}h2{margin:0}label{display:grid;gap:var(--usx-spacing-xs)}select{min-height:var(--usx-touch-min)}footer{display:flex;justify-content:flex-end;gap:var(--usx-spacing-sm)}</style>
