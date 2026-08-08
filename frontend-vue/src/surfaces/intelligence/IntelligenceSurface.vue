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
    <div class="surface__content">
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

      <!-- History -->
      <div v-else-if="activeTab === 'history'" class="intel-panel">
        <h3 class="surface__panel-title">Chat History</h3>
        <p class="intel-muted">
          Conversation log — search, replay, and export.
        </p>

        <div class="intel-empty">
          <span class="material-symbols-outlined">history</span>
          <p>Chat history will appear here. Conversations are saved locally.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useShellStore } from "../../stores/shell";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import SnackbarModelsPanel from "../snackbar/panels/SnackbarModelsPanel.vue";
import SnackbarAgentsPanel from "../snackbar/panels/SnackbarAgentsPanel.vue";
import SnackbarBudgetPanel from "../snackbar/panels/SnackbarBudgetPanel.vue";

const INTEL_TABS = [
  { id: "chat", label: "Chat", icon: "chat" },
  { id: "models", label: "Models", icon: "smart_toy" },
  { id: "agents", label: "Agents", icon: "group" },
  { id: "budget", label: "Budget", icon: "account_balance" },
  { id: "history", label: "History", icon: "history" },
];

const shell = useShellStore();
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
  const saved = localStorage.getItem("ucore-chat-prompt");
  if (saved) systemPrompt.value = saved;
  try {
    const ctxSaved = localStorage.getItem("ucore-chat-context");
    if (ctxSaved) ctx.value = { ...ctx.value, ...JSON.parse(ctxSaved) };
  } catch {}
});
</script>

<style scoped>
.intel-panel {
  max-width: 720px;
  padding: var(--usx-spacing-xl);
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
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background-color: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  resize: vertical;
  line-height: 1.5;
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
  padding: var(--usx-spacing-sm) var(--usx-spacing-xl);
  background-color: var(--usx-color-primary);
  color: white;
  border: none;
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
}

.intel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-2xl);
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}

.intel-empty .material-symbols-outlined {
  font-size: 40px;
  opacity: 0.4;
}
</style>
