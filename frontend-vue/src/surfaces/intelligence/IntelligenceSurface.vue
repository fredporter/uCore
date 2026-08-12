<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="INTEL_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content intel-content">
      <section class="surface__panel intel-header">
        <div class="intel-header__row">
          <h3 class="surface__panel-title">Intelligence</h3>
          <span class="intel-header__badge">AI & Chat Config</span>
        </div>
        <p class="surface__panel-description">
          Configure chat models, agents, budget limits, and review history.
        </p>
      </section>

      <!-- Chat Settings -->
      <div v-if="activeTab === 'chat'" class="intel-panel">
        <h3 class="surface__panel-title">Chat Settings</h3>
        <p class="intel-muted">
          System prompt, context sources, and persona configuration.
        </p>

        <div class="intel-form-section">
          <h4 class="intel-section-label">System Prompt</h4>
          <textarea
            v-model="systemPrompt"
            class="intel-textarea"
            rows="6"
            placeholder="You are a helpful assistant. You answer questions clearly and concisely…"
          />
        </div>

        <div class="intel-form-section">
          <h4 class="intel-section-label">Context Sources</h4>
          <div class="intel-checkbox-row">
            <label
              ><input v-model="ctx.vault" type="checkbox" /> Vault
              documents</label
            >
          </div>
          <div class="intel-checkbox-row">
            <label
              ><input v-model="ctx.tasks" type="checkbox" /> Active tasks</label
            >
          </div>
          <div class="intel-checkbox-row">
            <label
              ><input v-model="ctx.surface" type="checkbox" /> Current
              surface</label
            >
          </div>
        </div>

        <button class="intel-save-btn" @click="savePrompt">
          Save Chat Settings
        </button>
      </div>

      <!-- Models — reused from SnackbarSurface -->
      <SnackbarModelsPanel v-else-if="activeTab === 'models'" />

      <!-- Agents — reused from SnackbarSurface -->
      <SnackbarAgentsPanel v-else-if="activeTab === 'agents'" />

      <!-- Budget — reused from SnackbarSurface -->
      <SnackbarBudgetPanel v-else-if="activeTab === 'budget'" />

      <!-- Combined History -->
      <CombinedHistoryPanel v-else-if="activeTab === 'history'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useShellStore } from "../../stores/shell";
import { useSnackbarOpsStore } from "../../stores/snackbarOps";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import SnackbarModelsPanel from "../snackbar/panels/SnackbarModelsPanel.vue";
import SnackbarAgentsPanel from "../snackbar/panels/SnackbarAgentsPanel.vue";
import SnackbarBudgetPanel from "../snackbar/panels/SnackbarBudgetPanel.vue";
import CombinedHistoryPanel from "./panels/CombinedHistoryPanel.vue";

const INTEL_TABS = [
  { id: "chat", label: "Chat", icon: "chat" },
  { id: "models", label: "Models", icon: "smart_toy" },
  { id: "agents", label: "Agents", icon: "group" },
  { id: "budget", label: "Budget", icon: "account_balance" },
  { id: "history", label: "History", icon: "history" },
];

const shell = useShellStore();
const srv = useSnackbarOpsStore();
const activeTab = ref("chat");

const systemPrompt = ref("You are a helpful assistant.");
const ctx = ref({ vault: true, tasks: true, surface: true });

function savePrompt() {
  try {
    localStorage.setItem("ucore-chat-prompt", systemPrompt.value);
  } catch {}
  try {
    localStorage.setItem("ucore-chat-context", JSON.stringify(ctx.value));
  } catch {}
}

onMounted(() => {
  srv.fetchAll();
  const saved = localStorage.getItem("ucore-chat-prompt");
  if (saved) systemPrompt.value = saved;
  try {
    const ctxSaved = localStorage.getItem("ucore-chat-context");
    if (ctxSaved) ctx.value = { ...ctx.value, ...JSON.parse(ctxSaved) };
  } catch {}
});
</script>

<style scoped>
.intel-content {
  display: grid;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-lg);
}

.intel-header {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--usx-color-primary) 4%, transparent) 0%,
    transparent 78%
  );
}

.intel-header__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.intel-header__badge {
  display: inline-flex;
  align-items: center;
  min-height: calc(var(--usx-touch-min) - var(--usx-spacing-sm));
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  background: color-mix(in srgb, var(--usx-color-surface-variant) 75%, var(--usx-color-surface));
}

.intel-panel {
  max-width: var(--usx-prose-width);
}

.intel-muted {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-lg);
}

.intel-form-section {
  margin-bottom: var(--usx-spacing-lg);
}

.intel-section-label {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  margin-bottom: var(--usx-spacing-sm);
}

.intel-textarea {
  width: 100%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background-color: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  resize: vertical;
  line-height: var(--usx-line-height-normal);
}

.intel-checkbox-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-1) 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
}

.intel-save-btn {
  min-height: var(--usx-touch-min);
  padding: 0 var(--usx-spacing-xl);
  background-color: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border: var(--usx-border-width) solid var(--usx-color-primary);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
}

/* Shared USX layer for Snackbar panels inside Intelligence */
.intel-content :deep(.surface__panel) {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-surface) 96%, var(--usx-color-background));
  padding: var(--usx-spacing-md);
  box-shadow: 0 1px 0 color-mix(in srgb, var(--usx-color-border) 40%, transparent);
}

.intel-content :deep(.surface__panel-title) {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.intel-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  overflow: hidden;
  background: var(--usx-color-surface);
}

.intel-content :deep(th),
.intel-content :deep(td) {
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  font-size: var(--usx-font-size-sm);
  text-align: left;
}

.intel-content :deep(th) {
  color: var(--usx-color-on-surface-muted);
  background: color-mix(in srgb, var(--usx-color-surface-variant) 78%, var(--usx-color-surface));
  font-weight: var(--usx-font-weight-medium);
}
</style>
