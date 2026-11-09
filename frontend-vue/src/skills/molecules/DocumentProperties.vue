<template>
  <dl v-if="properties.length" class="document-properties" aria-label="Document properties">
    <div v-for="(property, index) in properties" :key="`${property.key}:${index}`" class="document-properties__box" :class="{ 'document-properties__box--wide': property.value.length > 64 }">
      <dt>{{ property.key.replaceAll('_', ' ') }}</dt><dd>{{ property.value }}</dd>
    </div>
  </dl>
</template>
<script setup lang="ts">
import { computed } from 'vue';
import { readingProperties } from '../../utils/readingDocument';
const props = defineProps<{ frontmatter: Record<string, unknown> }>();
const properties = computed(() => readingProperties(props.frontmatter));
</script>
<style scoped>
.document-properties { display: flex; flex-wrap: wrap; align-items: stretch; gap: 6px; margin: var(--usx-spacing-sm) 0 var(--usx-spacing-lg); padding: 0; font-family: var(--usx-font-family-sans, Inter, sans-serif); font-size: var(--usx-font-size-sm); line-height: 1.45; text-align: left; }
.document-properties__box { display: flex; flex-direction: column; gap: 2px; box-sizing: border-box; min-width: 0; max-width: 100%; margin: 0; padding: 6px 10px; border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface-variant); overflow-wrap: anywhere; }
.document-properties__box--wide { flex-basis: 100%; }
dt { margin: 0; padding: 0; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); line-height: 1.3; }
dd { min-width: 0; margin: 0; padding: 0; color: var(--usx-color-on-surface); line-height: 1.45; }
</style>
