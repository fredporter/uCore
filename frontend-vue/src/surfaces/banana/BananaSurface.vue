<template>
  <div class="surface banana-surface">
    <div class="surface__content">
      <BananaStudio class="banana-surface__studio" scope="vector" />
      <SimulatedTapPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import BananaStudio from "../browserui/panels/BananaStudio.vue"
import SimulatedTapPanel from "./SimulatedTapPanel.vue"
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
  display: grid;
  gap: var(--usx-spacing-md);
  box-sizing: border-box;
  padding: var(--usx-spacing-md);
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}
.banana-surface__studio {
  padding: 0;
}
</style>
