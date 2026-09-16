<template>
  <div class="groovebox-surface-wrapper">
    <header class="groovebox-header">
      <div class="groovebox-header__title-group">
        <h1 class="groovebox-header__title">Groovebox</h1>
        <span
          class="groovebox-surface-status"
          :class="`is-${connectionStatus}`"
          role="status"
          aria-live="polite"
        >
          <span class="groovebox-surface-status-dot" aria-hidden="true" />
          {{ connectionStatusLabel }}
        </span>
      </div>
      <div class="groovebox-header__actions">
        <a
          class="usx-btn usx-btn--sm usx-btn--secondary"
          :href="grooveboxUrl"
          target="_blank"
          title="Open Groovebox in new tab"
        >
          <UIcon name="open_in_new" />
          <span>External</span>
        </a>
      </div>
    </header>
    <iframe
      :key="iframeKey"
      ref="iframeRef"
      :src="grooveboxUrl"
      class="groovebox-surface-iframe"
      title="Groovebox"
      @load="onLoad"
      @error="onError"
      allow="clipboard-read; clipboard-write"
    />
    <div v-if="loading" class="groovebox-surface-loading">
      Loading Groovebox&#x2026;
    </div>
    <div
      v-if="loadError"
      class="groovebox-surface-error"
      role="status"
      aria-live="polite"
    >
      <div class="groovebox-surface-error-title">Groovebox is unavailable</div>
      <div class="groovebox-surface-error-body">{{ loadError }}</div>
      <div class="groovebox-surface-error-actions">
        <button class="usx-btn usx-btn--sm usx-btn--primary" @click="retryLoad">
          <UIcon name="refresh" />
          <span>Retry</span>
        </button>
        <a
          class="usx-btn usx-btn--sm usx-btn--secondary"
          :href="grooveboxUrl"
          target="_blank"
          rel="noopener"
        >
          <UIcon name="open_in_new" />
          <span>Open directly</span>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component GrooveboxSurface
 * @description uCore surface wrapper for Groovebox (port 8888).
 * Embeds the Groovebox Vue app via iframe with a minimal toolbar.
 * @category surfaces
 * @usage Routed at '/groovebox'
 */
import { computed, ref, onBeforeUnmount, onMounted } from "vue";
import UIcon from "../../skills/atoms/UIcon.vue";
const iframeRef = ref<HTMLIFrameElement | null>(null);
const loading = ref(true);
const loadError = ref<string | null>(null);
const iframeKey = ref(0);
const defaultGrooveboxUrl = "http://localhost:8888";
const grooveboxUrl = (
  import.meta.env.VITE_GROOVEBOX_URL?.trim() || defaultGrooveboxUrl
).replace(/\/+$/, "");
let loadTimer: number | null = null;

const connectionStatus = computed<"loading" | "online" | "offline">(() => {
  if (loading.value) return "loading";
  if (loadError.value) return "offline";
  return "online";
});

const connectionStatusLabel = computed(() => {
  if (connectionStatus.value === "loading") return "Connecting";
  if (connectionStatus.value === "offline") return "Unavailable";
  return "Online";
});

function clearLoadTimer() {
  if (loadTimer !== null) {
    window.clearTimeout(loadTimer);
    loadTimer = null;
  }
}

function startLoadTimeout() {
  clearLoadTimer();
  loadTimer = window.setTimeout(() => {
    if (loading.value) {
      loading.value = false;
      loadError.value = `Could not reach ${grooveboxUrl}. Ensure Groovebox dev server is running.`;
    }
  }, 8000);
}

function onLoad() {
  clearLoadTimer();
  loading.value = false;
  loadError.value = null;
}

function onError() {
  clearLoadTimer();
  loading.value = false;
  loadError.value = `Failed to load ${grooveboxUrl}.`;
}

function retryLoad() {
  loading.value = true;
  loadError.value = null;
  iframeKey.value += 1;
  startLoadTimeout();
}

onMounted(() => {
  startLoadTimeout();
});

onBeforeUnmount(() => {
  clearLoadTimer();
});
</script>

<style scoped>
.groovebox-surface-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: var(--usx-color-background);
  position: relative;
}

.groovebox-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}

.groovebox-header__title-group {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
}

.groovebox-header__title {
  font-size: var(--usx-font-size-xl);
  font-weight: 600;
  margin: 0;
  color: var(--usx-color-on-surface);
}

.groovebox-header__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.groovebox-surface-status {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  background: var(--usx-color-surface-variant);
}

.groovebox-surface-status-dot {
  width: var(--usx-spacing-sm);
  height: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-warning);
}

.groovebox-surface-status.is-online {
  border-color: var(--usx-color-success);
  color: var(--usx-color-success);
}

.groovebox-surface-status.is-online .groovebox-surface-status-dot {
  background: var(--usx-color-success);
}

.groovebox-surface-status.is-offline {
  border-color: var(--usx-color-danger);
  color: var(--usx-color-danger);
}

.groovebox-surface-status.is-offline .groovebox-surface-status-dot {
  background: var(--usx-color-danger);
}

.groovebox-surface-status.is-loading {
  border-color: var(--usx-color-warning);
  color: var(--usx-color-warning);
}

.groovebox-surface-iframe {
  flex: 1;
  width: 100%;
  border: none;
  background: var(--usx-color-surface-variant);
}

.groovebox-surface-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-lg);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.groovebox-surface-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(90vw, var(--usx-error-panel-max-width));
  padding: var(--usx-spacing-lg);
  border: var(--usx-border-width) solid var(--usx-color-danger);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  display: grid;
  gap: var(--usx-spacing-sm);
}

.groovebox-surface-error-title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
}

.groovebox-surface-error-body {
  color: var(--usx-color-on-surface-muted);
  overflow-wrap: anywhere;
}

.groovebox-surface-error-actions {
  display: flex;
  gap: var(--usx-spacing-sm);
  align-items: center;
}

.groovebox-surface-retry,
.groovebox-surface-open {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  text-decoration: none;
}

.groovebox-surface-retry {
  cursor: pointer;
}

.groovebox-surface-retry:hover,
.groovebox-surface-open:hover {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}
</style>
