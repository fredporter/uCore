<template>
  <div class="agents-panel-shell">
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">support_agent</span>
        <div>
          <h3 class="recipe-title">Active Runtime Agents</h3>
          <p class="recipe-desc">Registered agent roles, autonomous subagents, and capability scope.</p>
        </div>
      </div>
      <div class="header-meta">
        <button class="m3-button" @click="srv.fetchAgents">
          <span class="material-symbols-outlined">refresh</span>
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <div class="table-container-card">
      <div v-if="srv.agents.length === 0" class="server-empty-state">
        <span class="material-symbols-outlined empty-icon">support_agent</span>
        <p>No runtime agents currently registered.</p>
      </div>
      <div v-else class="server-table-wrap">
        <table class="usx-table">
          <thead>
            <tr>
              <th>Agent Persona</th>
              <th>Operational Scope</th>
              <th>Lifecycle State</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in srv.agents" :key="agent.id">
              <td>
                <span class="server-agent-name">
                  <span class="agent-icon">
                    <span class="material-symbols-outlined">{{ agent.icon || 'smart_toy' }}</span>
                  </span>
                  <span class="agent-title-text">{{ agent.name }}</span>
                </span>
              </td>
              <td class="server-agent-desc">{{ agent.description }}</td>
              <td>
                <span
                  class="status-pill"
                  :class="agent.active ? 'status-pill--up' : 'status-pill--neutral'"
                >
                  {{ agent.status || (agent.active ? "running" : "idle") }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";

const srv = useSnackbarOpsStore();
</script>

<style scoped>
@import '@udos/usx-tokens/usx-prose.css';

.agents-panel-shell {
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
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
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
  color: var(--usx-color-primary, #a8c7fa);
}

.recipe-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.recipe-desc {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.m3-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.15));
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.04));
  color: var(--usx-color-on-surface, #e2e2e6);
  cursor: pointer;
  transition: all 0.15s ease;
}

.m3-button:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.08));
  border-color: var(--usx-color-outline, rgba(255, 255, 255, 0.25));
}

.m3-button .material-symbols-outlined {
  font-size: 18px;
}

.table-container-card {
  border-radius: 12px;
  background: var(--usx-color-surface-container, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.08));
  overflow: hidden;
}

.server-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
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
  color: var(--usx-color-on-surface-variant, #8e9199);
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.1));
  background: var(--usx-color-surface, #1e2025);
  white-space: nowrap;
}

.usx-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, rgba(255, 255, 255, 0.05));
  vertical-align: middle;
}

.usx-table tr:hover {
  background: var(--usx-color-surface-container-high, rgba(255, 255, 255, 0.03));
}

.server-agent-name {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 500;
  color: var(--usx-color-on-surface, #e2e2e6);
}

.agent-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(168, 199, 250, 0.12);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, #a8c7fa);
}

.agent-icon .material-symbols-outlined {
  font-size: 16px;
}

.agent-title-text {
  font-size: 0.88rem;
  font-weight: 600;
}

.server-agent-desc {
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, #8e9199);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  letter-spacing: 0.03em;
}

.status-pill--up {
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
}

.status-pill--neutral {
  background: rgba(255, 255, 255, 0.06);
  color: var(--usx-color-on-surface-variant, #8e9199);
}
</style>
