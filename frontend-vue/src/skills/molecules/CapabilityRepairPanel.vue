<template>
  <section class="repair-panel" role="alert" aria-live="polite">
    <div class="repair-panel__header">
      <div class="repair-panel__title-wrap">
        <UIcon name="warning" />
        <h3 class="repair-panel__title">Repair Required</h3>
      </div>
      <UButton size="sm" variant="secondary" @click="$emit('retry')">
        Re-check
      </UButton>
    </div>

    <p class="repair-panel__subtitle">
      Some capabilities are blocked. Complete these steps, then run preflight
      again.
    </p>

    <div
      v-for="item in items"
      :key="item.capability"
      class="repair-panel__capability"
    >
      <div class="repair-panel__capability-head">
        <UBadge type="warning" size="sm">{{ item.capability }}</UBadge>
        <span v-if="item.error" class="repair-panel__error">{{
          item.error
        }}</span>
      </div>

      <ul class="repair-panel__list">
        <li
          v-for="card in toRepairCards(item)"
          :key="card.key"
          class="repair-panel__item"
        >
          <div class="repair-panel__item-title">{{ card.title }}</div>
          <div class="repair-panel__item-detail">{{ card.detail }}</div>
          <div class="repair-panel__item-action">{{ card.actionLabel }}</div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { CapabilityPreflightResult } from "@/api/preflight";
import { toRepairCards } from "@/api/preflight";
import UBadge from "@/skills/atoms/UBadge.vue";
import UButton from "@/skills/atoms/UButton.vue";
import UIcon from "@/skills/atoms/UIcon.vue";

defineProps<{
  items: CapabilityPreflightResult[];
}>();

defineEmits<{
  (event: "retry"): void;
}>();
</script>

<style scoped>
.repair-panel {
  border: var(--usx-border-width) solid var(--usx-color-warning);
  border-radius: var(--usx-radius-md);
  background: color-mix(
    in srgb,
    var(--usx-color-warning) 10%,
    var(--usx-color-surface)
  );
  padding: var(--usx-spacing-lg);
  margin-bottom: var(--usx-spacing-md);
}

.repair-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
}

.repair-panel__title-wrap {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.repair-panel__title {
  margin: 0;
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.repair-panel__subtitle {
  margin: var(--usx-spacing-sm) 0 var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.repair-panel__capability {
  padding-top: var(--usx-spacing-md);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
}

.repair-panel__capability + .repair-panel__capability {
  margin-top: var(--usx-spacing-md);
}

.repair-panel__capability-head {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.repair-panel__error {
  color: var(--usx-color-danger);
  font-size: var(--usx-font-size-sm);
}

.repair-panel__list {
  margin: var(--usx-spacing-sm) 0 0;
  padding-left: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.repair-panel__item-title {
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
}

.repair-panel__item-detail,
.repair-panel__item-action {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}
</style>
