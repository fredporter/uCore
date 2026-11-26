<template>
  <div class="models-panel-shell">
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">smart_toy</span>
        <div>
          <h3 class="recipe-title">Installed &amp; Tracked Models</h3>
          <p class="recipe-desc">Local Ollama inference models and metered execution calls.</p>
        </div>
      </div>
      <div class="header-meta">
        <button class="usx-btn usx-btn--secondary m3-button" @click="srv.fetchModels">
          <UIcon name="refresh" />
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <div class="table-container-card">
      <div v-if="srv.modelUsage.length === 0" class="server-empty-state">
        <span class="material-symbols-outlined empty-icon">smart_toy</span>
        <p>No model usage data recorded.</p>
      </div>
      <div v-else class="server-table-wrap">
        <table class="usx-table">
          <thead>
            <tr>
              <th>Model Name</th>
              <th>Usage Share</th>
              <th>Inference Calls</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in srv.modelUsage" :key="m.id">
              <td>
                <span class="model-name-cell">
                  <span class="model-icon">
                    <span class="material-symbols-outlined">memory</span>
                  </span>
                  <span class="model-name-text">{{ m.name }}</span>
                </span>
              </td>
              <td>
                <div class="model-usage-cell">
                  <div class="progress-track" v-if="m.pct !== null">
                    <div class="progress-fill" :style="{ width: `${m.pct}%` }"></div>
                  </div>
                  <span class="usage-label">{{ m.pct === null ? 'Unmetered' : `${m.pct}%` }}</span>
                </div>
              </td>
              <td class="model-calls-cell">{{ m.calls ?? "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import UIcon from "../../../skills/atoms/UIcon.vue";

const srv = useSnackbarOpsStore();
</script>

<style scoped>

.models-panel-shell {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  width: 100%;
}

.recipe-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent));
  flex-wrap: wrap;
  gap: 0.75rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  font-size: 28px;
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.recipe-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.recipe-desc {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.m3-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 15%, transparent));
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 4%, transparent));
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
  cursor: pointer;
  transition: all 0.15s ease;
}

.m3-button:hover {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  border-color: var(--usx-color-outline, color-mix(in srgb, var(--usx-color-on-surface) 25%, transparent));
}

.m3-button .material-symbols-outlined {
  font-size: 18px;
}

.table-container-card {
  border-radius: 12px;
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  overflow: hidden;
}

.server-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.server-table-wrap {
  overflow-x: auto;
}

.usx-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.usx-table th {
  text-align: left;
  font-weight: 600;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent));
  background: var(--usx-color-surface, var(--usx-color-surface));
  white-space: nowrap;
}

.usx-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 5%, transparent));
  vertical-align: middle;
}

.usx-table tr:hover {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
}

.model-name-cell {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 500;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.model-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.model-icon .material-symbols-outlined {
  font-size: 16px;
}

.model-name-text {
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.85rem;
}

.model-usage-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  max-width: 280px;
}

.progress-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--usx-color-primary, var(--usx-color-primary));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.usage-label {
  font-size: 0.78rem;
  font-family: var(--usx-font-family-mono, monospace);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  min-width: 40px;
}

.model-calls-cell {
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}
</style>
