<template>
  <div class="csection">
    <button class="csection-header" @click="open = !open" :aria-expanded="open">
      <span class="csection-icon material-symbols-outlined">{{
        open ? "expand_more" : "chevron_right"
      }}</span>
      <UIcon :name="icon" />
      <span class="csection-title">{{ title }}</span>
      <UBadge v-if="count > 0" type="info" size="sm">{{ count }}</UBadge>
    </button>
    <div v-show="open" class="csection-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import UIcon from "../atoms/UIcon.vue";
import UBadge from "../atoms/UBadge.vue";

const props = defineProps<{
  title: string;
  count: number;
  icon: string;
  defaultOpen?: boolean;
}>();

const open = ref(props.defaultOpen ?? false);
</script>

<style scoped>
.csection {
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  margin-bottom: var(--usx-spacing-md);
  overflow: hidden;
}

.csection-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  width: 100%;
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: none;
  cursor: pointer;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  text-align: left;
  transition: background 0.15s;
}

.csection-header:hover {
  background: var(--usx-color-surface-variant);
}

.csection-icon {
  font-size: var(--usx-font-size-lg);
  color: var(--usx-color-on-surface-muted);
}

.csection-title {
  flex: 1;
}

.csection-body {
  padding: var(--usx-spacing-md);
  border-top: 1px solid var(--usx-color-border);
  background: var(--usx-color-background);
}
</style>
