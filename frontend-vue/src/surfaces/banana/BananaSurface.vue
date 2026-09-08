<template>
  <div class="surface banana-surface">
    <div class="surface__content">
      <BananaStudio />
    </div>
  </div>
</template>

<script setup lang="ts">
import BananaStudio from "../browserui/panels/BananaStudio.vue"
</script>

<style scoped>
.banana-surface {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
}

.banana-surface .surface__content {
  padding: var(--usx-spacing-lg);
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}
</style>
