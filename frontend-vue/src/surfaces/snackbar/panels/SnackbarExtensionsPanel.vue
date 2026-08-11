<template>
  <div class="snackbar-plugins">
    <div class="snackbar-plugins__head">
      <h3 class="surface__panel-title">Extensions</h3>
      <button
        class="snackbar-plugins__refresh"
        :disabled="refreshing"
        @click="refresh()"
      >
        <span
          class="material-symbols-outlined"
          :class="{ spinning: refreshing }"
        >
          refresh
        </span>
        Refresh
      </button>
    </div>
    <p class="snackbar-plugins__muted">
      Browse, toggle, install and repair extensions detected under ~/Code/.
    </p>

    <div v-if="alwaysActiveSurfaces.length > 0" class="snackbar-plugins__core">
      <div class="snackbar-plugins__core-head">
        <span class="material-symbols-outlined">verified</span>
        <span>Always Active</span>
      </div>
      <p class="snackbar-plugins__core-note">
        Required surfaces are managed by uCore and stay on across sessions.
      </p>
      <div class="snackbar-plugins__core-list">
        <span
          v-for="surface in alwaysActiveSurfaces"
          :key="surface.id"
          class="snackbar-plugins__core-pill"
        >
          {{ surface.name }}
        </span>
      </div>
    </div>

    <!-- Action message toast -->
    <div v-if="extStore.actionMessage" class="snackbar-plugins__toast">
      {{ extStore.actionMessage }}
      <button
        class="snackbar-plugins__toast-close"
        @click="extStore.actionMessage = ''"
      >
        &times;
      </button>
    </div>

    <div v-if="catalogueItems.length === 0" class="snackbar-plugins__empty">
      <span class="material-symbols-outlined">extension</span>
      <p>No extensions detected yet. Click Refresh to probe the filesystem.</p>
    </div>

    <div v-else class="snackbar-plugins__grid">
      <div
        v-for="ext in catalogueItems"
        :key="ext.id"
        class="snackbar-plugins__card"
        :class="`snackbar-plugins__card--${ext.status}`"
      >
        <div class="snackbar-plugins__icon">
          <span class="material-symbols-outlined">{{ ext.icon }}</span>
        </div>
        <div class="snackbar-plugins__body">
          <div class="snackbar-plugins__header">
            <span class="snackbar-plugins__name">{{ ext.name }}</span>
            <span
              class="snackbar-plugins__badge"
              :class="`snackbar-plugins__badge--${ext.status}`"
            >
              {{ statusLabel(ext.status) }}
            </span>
          </div>
          <p v-if="ext.description" class="snackbar-plugins__desc">
            {{ ext.description }}
          </p>
          <p v-if="ext.version" class="snackbar-plugins__version">
            v{{ ext.version }}
          </p>
        </div>
        <!-- Actions column -->
        <div class="snackbar-plugins__actions">
          <!-- Toggle switch -->
          <label class="snackbar-plugins__toggle">
            <input
              type="checkbox"
              :checked="ext.enabled || ext.status === 'running'"
              :disabled="loadingAction(ext.id) !== ''"
              @change="onToggle(ext)"
            />
            <span class="snackbar-plugins__toggle-slider"></span>
            <span class="snackbar-plugins__toggle-label">
              {{ ext.enabled || ext.status === "running" ? "On" : "Off" }}
            </span>
          </label>

          <!-- Install / Repair buttons -->
          <div class="snackbar-plugins__action-btns">
            <button
              v-if="!ext.is_installed"
              class="snackbar-plugins__btn snackbar-plugins__btn--install"
              :disabled="loadingAction(ext.id) !== ''"
              @click="onInstall(ext)"
            >
              <span
                v-if="loadingAction(ext.id) === 'installing'"
                class="material-symbols-outlined spinning"
                >progress_activity</span
              >
              <span v-else class="material-symbols-outlined">download</span>
              Install
            </button>
            <button
              v-else
              class="snackbar-plugins__btn snackbar-plugins__btn--repair"
              :disabled="loadingAction(ext.id) !== ''"
              @click="onRepair(ext)"
            >
              <span
                v-if="loadingAction(ext.id) === 'repairing'"
                class="material-symbols-outlined spinning"
                >progress_activity</span
              >
              <span v-else class="material-symbols-outlined">build</span>
              Repair
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SnackbarExtensionsPanel
 * @description Extensions catalogue — full-width cards with toggle on/off,
 *   install (clone+setup), and repair (re-clone+reinstall) buttons.
 *   Fetches live filesystem probe data from Snackbar backend.
 * @category surfaces/snackbar
 */
import { computed, onMounted, ref } from "vue";
import { useExtensionStore } from "../../../stores/extensions";

const extStore = useExtensionStore();
const refreshing = ref(false);

const alwaysActiveSurfaces = computed(() =>
  extStore.all
    .filter(
      (entry) =>
        entry.manifest.required &&
        (entry.manifest.kind === "core" || entry.manifest.kind === "surface"),
    )
    .map((entry) => ({ id: entry.manifest.id, name: entry.manifest.name })),
);

// Merge known manifest entries with runtime catalogue from backend
const catalogueItems = computed(() => {
  const runtime = extStore.runtimeCatalogue;
  const known = extStore.catalogue;
  const merged = new Map<string, any>();

  // Start with known entries (from built-in manifests)
  for (const entry of known) {
    merged.set(entry.manifest.id, {
      ...entry.manifest,
      status: entry.status,
      is_installed: entry.status === "running" || entry.status === "installed",
      enabled: entry.status === "running",
    });
  }

  // Overlay runtime probe data (filesystem truth)
  for (const ext of runtime) {
    const existing = merged.get(ext.id);
    if (existing) {
      Object.assign(existing, ext);
    } else {
      merged.set(ext.id, ext);
    }
  }

  return [...merged.values()].filter((e) => e.kind === "plugin" || !e.required);
});

const STATUS_LABELS: Record<string, string> = {
  unknown: "unknown",
  available: "available",
  installed: "installed",
  running: "active",
};

function statusLabel(s: string) {
  return STATUS_LABELS[s] ?? s;
}

function loadingAction(id: string): string {
  return extStore.loading[id] ?? "";
}

async function refresh() {
  refreshing.value = true;
  await extStore.fetchCatalogue();
  refreshing.value = false;
}

async function onToggle(ext: any) {
  const newEnabled = !(ext.enabled || ext.status === "running");
  await extStore.toggleExtension(ext.id, newEnabled);
  await extStore.fetchCatalogue();
}

async function onInstall(ext: any) {
  await extStore.installExtension(ext.id);
}

async function onRepair(ext: any) {
  await extStore.repairExtension(ext.id);
}

onMounted(() => {
  void extStore.fetchCatalogue();
});
</script>

<style scoped>
.snackbar-plugins {
  max-width: 100%;
  padding: var(--usx-spacing-xl);
}

.snackbar-plugins__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  margin-bottom: var(--usx-spacing-xs);
}

.snackbar-plugins__refresh {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
  border: var(--usx-border-width) solid
    color-mix(in srgb, var(--usx-color-primary) 25%, transparent);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  transition: background var(--usx-transition-fast);
}

.snackbar-plugins__refresh:hover:not(:disabled) {
  background: color-mix(in srgb, var(--usx-color-primary) 20%, transparent);
}

.snackbar-plugins__refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.snackbar-plugins__muted {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.snackbar-plugins__core {
  margin-top: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
}

.snackbar-plugins__core-head {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.snackbar-plugins__core-head .material-symbols-outlined {
  font-size: 18px;
  color: var(--usx-color-success);
}

.snackbar-plugins__core-note {
  margin: var(--usx-spacing-xs) 0 0;
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.snackbar-plugins__core-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
  margin-top: var(--usx-spacing-sm);
}

.snackbar-plugins__core-pill {
  display: inline-flex;
  align-items: center;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-success) 12%, transparent);
  color: var(--usx-color-success);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
}

/* Toast */
.snackbar-plugins__toast {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
}

.snackbar-plugins__toast-close {
  margin-left: auto;
  background: none;
  border: none;
  font-size: var(--usx-font-size-lg);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  line-height: 1;
  padding: 0 var(--usx-spacing-xs);
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

/* Full-width card grid */
.snackbar-plugins__grid {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-md);
}

.snackbar-plugins__card {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  background-color: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  transition: border-color var(--usx-transition-fast);
  width: 100%;
  box-sizing: border-box;
}

.snackbar-plugins__card--running {
  border-color: var(--usx-color-success);
}

.snackbar-plugins__card--available {
  opacity: 0.75;
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
  font-size: 22px;
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
  gap: var(--usx-spacing-sm);
}

.snackbar-plugins__name {
  font-size: var(--usx-font-size-base);
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

/* Actions column */
.snackbar-plugins__actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--usx-spacing-sm);
  flex-shrink: 0;
  min-width: 110px;
}

/* Toggle switch */
.snackbar-plugins__toggle {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  cursor: pointer;
  user-select: none;
}

.snackbar-plugins__toggle input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.snackbar-plugins__toggle-slider {
  position: relative;
  width: 40px;
  height: 22px;
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast);
  flex-shrink: 0;
}

.snackbar-plugins__toggle-slider::after {
  content: "";
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: var(--usx-color-on-surface-muted);
  border-radius: var(--usx-radius-full);
  transition:
    transform var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.snackbar-plugins__toggle input:checked + .snackbar-plugins__toggle-slider {
  background: var(--usx-color-success);
  border-color: var(--usx-color-success);
}

.snackbar-plugins__toggle
  input:checked
  + .snackbar-plugins__toggle-slider::after {
  transform: translateX(18px);
  background: var(--usx-color-background);
}

.snackbar-plugins__toggle input:disabled + .snackbar-plugins__toggle-slider {
  opacity: 0.4;
  cursor: not-allowed;
}

.snackbar-plugins__toggle-label {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface-muted);
  min-width: 24px;
}

.snackbar-plugins__toggle input:checked ~ .snackbar-plugins__toggle-label {
  color: var(--usx-color-success);
}

/* Action buttons */
.snackbar-plugins__action-btns {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.snackbar-plugins__btn {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast);
  white-space: nowrap;
}

.snackbar-plugins__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.snackbar-plugins__btn .material-symbols-outlined {
  font-size: 16px;
}

.snackbar-plugins__btn--install {
  color: var(--usx-color-primary);
  border-color: color-mix(in srgb, var(--usx-color-primary) 30%, transparent);
}

.snackbar-plugins__btn--install:hover:not(:disabled) {
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
}

.snackbar-plugins__btn--repair {
  color: var(--usx-color-warning);
  border-color: color-mix(in srgb, var(--usx-color-warning) 30%, transparent);
}

.snackbar-plugins__btn--repair:hover:not(:disabled) {
  background: color-mix(in srgb, var(--usx-color-warning) 12%, transparent);
}

/* Spinner */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
