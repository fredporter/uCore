<template>
  <div class="devhud" :class="{ 'devhud--minimized': minimized }">
    <!-- Minimized: compact toggle -->
    <button
      v-if="minimized"
      class="devhud-min"
      @click="minimized = false"
      title="Dev HUD"
    >
      <span class="material-symbols-outlined">terminal</span>
      <span v-if="taskTotal > 0" class="devhud-badge">{{ taskTotal }}</span>
    </button>

    <!-- Expanded HUD -->
    <div v-else class="devhud-card">
      <div class="devhud-header">
        <span class="devhud-header-icon material-symbols-outlined"
          >terminal</span
        >
        <strong class="devhud-title">Dev HUD</strong>
        <button class="devhud-close" @click="minimized = true" title="Minimize">
          <span class="material-symbols-outlined">remove</span>
        </button>
      </div>

      <div v-if="loading" class="devhud-section">
        <p class="devhud-muted">Loading...</p>
      </div>

      <template v-else>
        <!-- Tasks -->
        <div class="devhud-section">
          <div class="devhud-section-head">
            <span class="material-symbols-outlined devhud-section-icon"
              >assignment</span
            >
            <span class="devhud-section-label">Tasks</span>
            <span class="devhud-section-count">{{ taskTotal }}</span>
          </div>
          <div v-if="taskStatuses.length > 0" class="devhud-tags">
            <span
              v-for="st in taskStatuses"
              :key="st.status"
              class="devhud-tag"
              :class="`devhud-tag--${st.css}`"
            >
              {{ st.status }}: {{ st.count }}
            </span>
          </div>
          <p v-else class="devhud-muted">No tasks</p>
        </div>

        <!-- Variables -->
        <div class="devhud-section">
          <div class="devhud-section-head">
            <span class="material-symbols-outlined devhud-section-icon"
              >tune</span
            >
            <span class="devhud-section-label">Variables</span>
            <span class="devhud-section-count">{{ varCount }}</span>
          </div>
          <div v-if="varEntries.length > 0" class="devhud-var-list">
            <div
              v-for="[k, v] in varEntries.slice(0, 8)"
              :key="k"
              class="devhud-var-row"
            >
              <span class="devhud-var-key">{{ k }}</span>
              <span class="devhud-var-val">{{ truncate(String(v), 40) }}</span>
            </div>
          </div>
          <p v-else class="devhud-muted">No variables</p>
        </div>

        <!-- Quick Actions -->
        <div class="devhud-section">
          <div class="devhud-section-head">
            <span class="material-symbols-outlined devhud-section-icon"
              >bolt</span
            >
            <span class="devhud-section-label">Quick Actions</span>
          </div>
          <div class="devhud-actions">
            <button
              v-for="action in quickActions"
              :key="action.id"
              class="devhud-action-btn"
              :disabled="runningAction === action.id"
              @click="triggerAction(action)"
            >
              <span class="material-symbols-outlined devhud-action-icon">{{
                action.icon
              }}</span>
              {{ runningAction === action.id ? "..." : action.label }}
            </button>
          </div>
        </div>
      </template>

      <!-- Error -->
      <div v-if="error" class="devhud-error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useDevModeStore } from "../../stores/devMode";
import { SNACKBAR_BASE } from "../../api/base";

const devMode = useDevModeStore();

const minimized = ref(false);
const loading = ref(true);
const error = ref<string | null>(null);
const hudData = ref<any>({});

const taskTotal = computed(() => hudData.value?.tasks?.total ?? 0);
const taskStatuses = computed(() => {
  const byStatus = hudData.value?.tasks?.by_status ?? {};
  const cssMap: Record<string, string> = {
    todo: "info",
    "in-progress": "warning",
    wip: "warning",
    done: "success",
    completed: "success",
    blocked: "error",
    review: "info",
  };
  return Object.entries(byStatus).map(([status, count]) => ({
    status,
    count: count as number,
    css: cssMap[status] || "info",
  }));
});

const varEntries = computed(() => {
  const user = hudData.value?.variables?.user ?? {};
  return Object.entries(user);
});
const varCount = computed(() => varEntries.value.length);

const quickActions = computed(() => hudData.value?.quick_actions ?? []);
const runningAction = ref<string | null>(null);

function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max) + "..." : s;
}

async function loadHud() {
  loading.value = true;
  error.value = null;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/dev-layer/hud`, {
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    hudData.value = await res.json();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function triggerAction(action: { id: string; label: string }) {
  runningAction.value = action.id;
  try {
    await fetch(`${SNACKBAR_BASE}/api/skills/${action.id}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  } catch {
    // best-effort
  } finally {
    runningAction.value = null;
  }
}

// Auto-refresh when Dev Mode is ON
let interval: ReturnType<typeof setInterval> | null = null;

watch(
  () => devMode.mode,
  (mode) => {
    if (mode === "on") {
      loadHud();
      interval = setInterval(loadHud, 30000);
    } else {
      if (interval) clearInterval(interval);
      interval = null;
    }
  },
  { immediate: true },
);

onMounted(() => {
  if (devMode.mode === "on") {
    loadHud();
    interval = setInterval(loadHud, 30000);
  }
});
</script>

<style scoped>
.devhud {
  position: fixed;
  bottom: 80px;
  right: var(--usx-spacing-lg);
  z-index: 998;
  font-family: var(--usx-font-family-sans);
}

.devhud--minimized {
  bottom: 80px;
  right: var(--usx-spacing-lg);
}

.devhud-min {
  width: 44px;
  height: 44px;
  border-radius: var(--usx-radius-full);
  border: 1px solid var(--usx-color-border);
  background: var(--usx-color-primary);
  color: var(--usx-color-background);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.devhud-min span {
  font-size: 20px;
}

.devhud-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--usx-color-danger);
  color: white;
  font-size: 10px;
  font-weight: var(--usx-font-weight-bold);
  width: 18px;
  height: 18px;
  border-radius: var(--usx-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
}

.devhud-card {
  width: 340px;
  max-height: 520px;
  overflow-y: auto;
  background: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.devhud-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
}

.devhud-header-icon {
  color: var(--usx-color-primary);
  font-size: 20px;
}

.devhud-title {
  flex: 1;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
}

.devhud-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--usx-color-on-surface-muted);
  padding: 2px;
}

.devhud-section {
  padding: var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
}

.devhud-section:last-child {
  border-bottom: none;
}

.devhud-section-head {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin-bottom: var(--usx-spacing-sm);
}

.devhud-section-icon {
  font-size: 16px;
  color: var(--usx-color-primary);
}

.devhud-section-label {
  flex: 1;
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.devhud-section-count {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-primary);
}

.devhud-muted {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.devhud-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}

.devhud-tag {
  font-size: var(--usx-font-size-xs);
  padding: 1px var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  font-weight: var(--usx-font-weight-medium);
}

.devhud-tag--info {
  background: color-mix(in srgb, var(--usx-color-info) 20%, transparent);
  color: var(--usx-color-info);
}

.devhud-tag--warning {
  background: color-mix(in srgb, var(--usx-color-warning) 20%, transparent);
  color: var(--usx-color-warning);
}

.devhud-tag--success {
  background: color-mix(in srgb, var(--usx-color-success) 20%, transparent);
  color: var(--usx-color-success);
}

.devhud-tag--error {
  background: color-mix(in srgb, var(--usx-color-danger) 20%, transparent);
  color: var(--usx-color-danger);
}

.devhud-var-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--usx-font-size-xs);
}

.devhud-var-row {
  display: flex;
  align-items: baseline;
  gap: var(--usx-spacing-sm);
}

.devhud-var-key {
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
  min-width: 100px;
  flex-shrink: 0;
}

.devhud-var-val {
  color: var(--usx-color-on-surface-muted);
  font-family: var(--usx-font-family-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.devhud-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}

.devhud-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--usx-font-size-xs);
  padding: 4px var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  cursor: pointer;
  transition: background 0.15s;
}

.devhud-action-btn:hover:not(:disabled) {
  background: var(--usx-color-surface-variant);
}

.devhud-action-icon {
  font-size: 14px;
  color: var(--usx-color-primary);
}

.devhud-error {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  color: var(--usx-color-danger);
  font-size: var(--usx-font-size-xs);
}
</style>
