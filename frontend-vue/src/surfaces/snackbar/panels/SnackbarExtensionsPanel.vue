<template>
  <div class="snackbar-plugins">
    <h3 class="surface__panel-title">Extensions</h3>
    <p class="snackbar-plugins__muted">
      Browse and manage installed extensions.
    </p>

    <div v-if="catalogue.length === 0" class="snackbar-plugins__empty">
      <span class="material-symbols-outlined">extension</span>
      <p>
        No extensions available yet. Extensions will appear here when detected.
      </p>
    </div>

    <div v-else class="snackbar-plugins__grid">
      <div
        v-for="entry in catalogue"
        :key="entry.manifest.id"
        class="snackbar-plugins__card"
        :class="`snackbar-plugins__card--${entry.status}`"
      >
        <div class="snackbar-plugins__icon">
          <span class="material-symbols-outlined">{{
            entry.manifest.icon
          }}</span>
        </div>
        <div class="snackbar-plugins__body">
          <div class="snackbar-plugins__header">
            <span class="snackbar-plugins__name">{{
              entry.manifest.name
            }}</span>
            <span
              class="snackbar-plugins__badge"
              :class="`snackbar-plugins__badge--${entry.status}`"
            >
              {{ statusLabel(entry.status) }}
            </span>
          </div>
          <p v-if="entry.manifest.description" class="snackbar-plugins__desc">
            {{ entry.manifest.description }}
          </p>
          <p v-if="entry.manifest.version" class="snackbar-plugins__version">
            v{{ entry.manifest.version }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SnackbarPluginsPanel
 * @description Plugin store — installed/available uDOS extensions catalogue.
 * Moved from IntelligenceSurface when the Snackbar surface absorbed Plugins.
 * @category surfaces/snackbar
 */
import { computed } from "vue";
import { useExtensionStore } from "../../../stores/extensions";

const extStore = useExtensionStore();
const catalogue = computed(() => extStore.catalogue);

const STATUS_LABELS: Record<string, string> = {
  unknown: "unknown",
  available: "available",
  installed: "installed",
  running: "running",
};
function statusLabel(s: string) {
  return STATUS_LABELS[s] ?? s;
}
</script>

<style scoped>
.snackbar-plugins {
  max-width: 720px;
  padding: var(--usx-spacing-xl);
}

.snackbar-plugins__muted {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.snackbar-plugins__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-2xl);
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}

.snackbar-plugins__empty .material-symbols-outlined {
  font-size: 40px;
  opacity: 0.4;
}

/* Plugin grid */
.snackbar-plugins__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--usx-spacing-md);
  margin-top: var(--usx-spacing-md);
}

.snackbar-plugins__card {
  display: flex;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  background-color: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  transition: border-color var(--usx-transition-fast);
}

.snackbar-plugins__card--running {
  border-color: var(--usx-color-success);
}

.snackbar-plugins__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min-sm);
  height: var(--usx-touch-min-sm);
  background-color: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  flex-shrink: 0;
}

.snackbar-plugins__icon .material-symbols-outlined {
  font-size: 20px;
  color: var(--usx-color-primary);
}

.snackbar-plugins__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  min-width: 0;
}

.snackbar-plugins__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
}

.snackbar-plugins__name {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.snackbar-plugins__badge {
  font-size: var(--usx-font-size-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  flex-shrink: 0;
}

.snackbar-plugins__badge--running {
  background: color-mix(in srgb, var(--usx-color-success) 15%, transparent);
  color: var(--usx-color-success);
}
.snackbar-plugins__badge--installed {
  background: color-mix(in srgb, var(--usx-color-info) 15%, transparent);
  color: var(--usx-color-info);
}
.snackbar-plugins__badge--available {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
}

.snackbar-plugins__desc {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
  line-height: 1.4;
}

.snackbar-plugins__version {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
}
</style>
