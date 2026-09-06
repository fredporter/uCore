<template>
  <div class="toolbar-section" role="group" :aria-label="label">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string }>();
</script>

<style scoped>
.toolbar-section { display: inline-flex; align-items: center; gap: var(--usx-spacing-1); padding-inline-end: var(--usx-spacing-xs); border-inline-end: var(--usx-border-width) solid var(--usx-color-border); }
.toolbar-section:last-child { border-inline-end: 0; }
</style>
