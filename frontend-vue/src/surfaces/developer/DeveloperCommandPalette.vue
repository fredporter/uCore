<template>
  <div v-if="open" class="palette-backdrop" @click.self="$emit('close')">
    <section class="palette" role="dialog" aria-modal="true" aria-labelledby="palette-title">
      <header><strong id="palette-title">Go to file</strong><kbd>Esc</kbd></header>
      <input ref="input" v-model="query" aria-label="Search repository files" placeholder="Type a file name or path…" @keydown.escape="$emit('close')" @keydown.down.prevent="move(1)" @keydown.up.prevent="move(-1)" @keydown.enter.prevent="choose(results[selected])" />
      <ul role="listbox">
        <li v-for="(path, index) in results" :key="path">
          <button :class="{ active: index === selected }" @mouseenter="selected = index" @click="choose(path)">
            <UIcon name="description" /><span>{{ path }}</span>
          </button>
        </li>
      </ul>
      <p v-if="!results.length">No matching files.</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import UIcon from "../../skills/atoms/UIcon.vue";

const props = defineProps<{ open: boolean; files: string[] }>();
const emit = defineEmits<{ close: []; select: [path: string] }>();
const query = ref("");
const selected = ref(0);
const input = ref<HTMLInputElement | null>(null);
const results = computed(() => {
  const terms = query.value.toLowerCase().split(/\s+/).filter(Boolean);
  return props.files.filter((path) => terms.every((term) => path.toLowerCase().includes(term))).slice(0, 30);
});
function move(delta: number) { selected.value = Math.max(0, Math.min(results.value.length - 1, selected.value + delta)); }
function choose(path?: string) { if (path) { emit("select", path); emit("close"); } }
watch(() => props.open, async (open) => { if (open) { query.value = ""; selected.value = 0; await nextTick(); input.value?.focus(); } });
watch(query, () => { selected.value = 0; });
</script>

<style scoped>
.palette-backdrop { position: fixed; inset: 0; z-index: 1000; display: grid; place-items: start center; padding-top: 12vh; background: rgba(0,0,0,.55); }
.palette { width: min(42rem, calc(100vw - 2rem)); max-height: 68vh; overflow: hidden; background: var(--usx-color-surface); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); box-shadow: var(--usx-shadow-lg); }
.palette header { display: flex; justify-content: space-between; padding: var(--usx-spacing-sm) var(--usx-spacing-md); }
.palette input { width: calc(100% - 2 * var(--usx-spacing-md)); margin: 0 var(--usx-spacing-md) var(--usx-spacing-sm); padding: var(--usx-spacing-sm); background: var(--usx-color-background); color: var(--usx-color-on-surface); border: var(--usx-border-width) solid var(--usx-color-primary); border-radius: var(--usx-radius-sm); }
.palette ul { list-style: none; margin: 0; padding: var(--usx-spacing-xs); overflow-y: auto; max-height: 52vh; }
.palette li button { width: 100%; display: flex; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border: 0; background: transparent; color: var(--usx-color-on-surface); text-align: left; }
.palette li button.active { background: var(--usx-color-surface-variant); color: var(--usx-color-primary); }
.palette p { padding: var(--usx-spacing-md); color: var(--usx-color-on-surface-muted); }
</style>
