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

      <!-- Models — reused from ServerSurface -->
      <ServerModelsPanel v-else-if="activeTab === 'models'" />

      <!-- Agents — reused from ServerSurface -->
      <ServerAgentsPanel v-else-if="activeTab === 'agents'" />

      <!-- Budget — reused from ServerSurface -->
      <ServerBudgetPanel v-else-if="activeTab === 'budget'" />

      <!-- Plugin Store -->
      <div v-else-if="activeTab === 'plugins'" class="intel-panel">
        <h3 class="surface__panel-title">Plugin Store</h3>
        <p class="intel-muted">Browse and manage installed extensions.</p>

        <div v-if="catalogue.length === 0" class="intel-empty">
          <span class="material-symbols-outlined">extension</span>
          <p>
            No plugins available yet. Extensions will appear here when detected.
          </p>
        </div>

        <div v-else class="intel-plugin-grid">
          <div
            v-for="entry in catalogue"
            :key="entry.manifest.id"
            class="intel-plugin-card"
            :class="`intel-plugin-card--${entry.status}`"
          >
            <div class="intel-plugin-card__icon">
              <span class="material-symbols-outlined">{{
                entry.manifest.icon
              }}</span>
            </div>
            <div class="intel-plugin-card__body">
              <div class="intel-plugin-card__header">
                <span class="intel-plugin-card__name">{{
                  entry.manifest.name
                }}</span>
                <span
                  class="intel-plugin-card__badge"
                  :class="`intel-plugin-card__badge--${entry.status}`"
                >
                  {{ statusLabel(entry.status) }}
                </span>
              </div>
              <p
                v-if="entry.manifest.description"
                class="intel-plugin-card__desc"
              >
                {{ entry.manifest.description }}
              </p>
              <p
                v-if="entry.manifest.version"
                class="intel-plugin-card__version"
              >
                v{{ entry.manifest.version }}
              </p>
            </div>
          </div>
        </div>
      </div>

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
import { ref, computed, onMounted } from "vue";
import { useShellStore } from "../../stores/shell";
import { useExtensionStore } from "../../stores/extensions";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import ServerModelsPanel from "../server/panels/ServerModelsPanel.vue";
import ServerAgentsPanel from "../server/panels/ServerAgentsPanel.vue";
import ServerBudgetPanel from "../server/panels/ServerBudgetPanel.vue";

const INTEL_TABS = [
  { id: "chat", label: "Chat", icon: "chat" },
  { id: "models", label: "Models", icon: "smart_toy" },
  { id: "agents", label: "Agents", icon: "group" },
  { id: "budget", label: "Budget", icon: "account_balance" },
  { id: "plugins", label: "Plugins", icon: "extension" },
  { id: "history", label: "History", icon: "history" },
];

const shell = useShellStore();
const extStore = useExtensionStore();
const activeTab = ref("chat");

const systemPrompt = ref("You are a helpful assistant.");
const ctx = ref({ vault: true, tasks: true, surface: true });

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
  padding: var(--usx-spacing-xs) 0;
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

/* Plugin grid */
.intel-plugin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--usx-spacing-md);
  margin-top: var(--usx-spacing-md);
}

.intel-plugin-card {
  display: flex;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  background-color: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  transition: border-color 120ms ease;
}

.intel-plugin-card--running {
  border-color: var(--usx-color-success);
}

.intel-plugin-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  flex-shrink: 0;
}

.intel-plugin-card__icon .material-symbols-outlined {
  font-size: 20px;
  color: var(--usx-color-primary);
}

.intel-plugin-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.intel-plugin-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
}

.intel-plugin-card__name {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.intel-plugin-card__badge {
  font-size: 10px;
  padding: 1px var(--usx-spacing-xs);
  border-radius: var(--usx-radius-full);
  flex-shrink: 0;
}

.intel-plugin-card__badge--running {
  background: color-mix(in srgb, var(--usx-color-success) 15%, transparent);
  color: var(--usx-color-success);
}
.intel-plugin-card__badge--installed {
  background: color-mix(in srgb, var(--usx-color-info) 15%, transparent);
  color: var(--usx-color-info);
}
.intel-plugin-card__badge--available {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
}

.intel-plugin-card__desc {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
  line-height: 1.4;
}

.intel-plugin-card__version {
  font-size: 10px;
  color: var(--usx-color-on-surface-muted);
  margin: 0;
}
</style>
