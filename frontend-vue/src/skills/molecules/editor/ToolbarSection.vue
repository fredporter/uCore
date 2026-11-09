<template>
  <div class="toolbar-section" role="group" :aria-label="label">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string }>();
</script>

<style scoped>
.toolbar-section { margin: 0; min-height: 32px; display: inline-flex; flex: 0 0 auto; align-items: center; gap: 2px; padding-inline-end: var(--usx-spacing-xs); border-inline-end: 0; }
.toolbar-section:last-child { border-inline-end: 0; }
</style>
