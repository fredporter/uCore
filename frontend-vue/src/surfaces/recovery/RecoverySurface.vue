<template>
  <section class="surface recovery-surface" aria-labelledby="recovery-heading">
    <div class="surface__content recovery-content">
      <UIcon :name="unavailable ? 'error_outline' : 'link_off'" :size="32" aria-hidden="true" />
      <h1 id="recovery-heading">{{ unavailable ? 'This page couldn’t load' : 'Page not found' }}</h1>
      <p>{{ unavailable
        ? 'Try opening this page again, or return to Mission Control.'
        : 'Check the address or return to Mission Control to continue.' }}</p>
      <div class="recovery-actions">
        <button v-if="unavailable" class="usx-btn usx-btn--primary" type="button" @click="emit('retry')">
          <UIcon name="refresh" /> Try again
        </button>
        <RouterLink class="usx-btn" :to="{ name: 'dashboard' }">
          <UIcon name="home" /> Mission Control
        </RouterLink>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router';
import UIcon from '../../skills/atoms/UIcon.vue';

defineProps<{ unavailable?: boolean }>();
const emit = defineEmits<{ retry: [] }>();
</script>

<style scoped>
.recovery-surface {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
}

.recovery-content {
  display: grid;
  gap: var(--usx-spacing-md);
  justify-items: start;
  padding: var(--usx-spacing-lg);
}

.recovery-content h1,
.recovery-content p { margin: 0; }
.recovery-content h1 { font-size: var(--usx-font-size-xl); }
.recovery-content p { color: var(--usx-color-on-surface-muted); }

.recovery-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.recovery-actions a {
  display: inline-flex;
  gap: var(--usx-icon-gap);
  align-items: center;
  min-height: var(--usx-touch-min);
  padding: var(--usx-btn-padding);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  color: var(--usx-color-on-surface);
  text-decoration: none;
}

.recovery-actions a:hover { border-color: var(--usx-color-primary); }
</style>
