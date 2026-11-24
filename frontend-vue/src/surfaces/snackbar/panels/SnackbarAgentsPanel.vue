<template>
  <div class="agents-panel-shell">
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">support_agent</span>
        <div>
          <h3 class="recipe-title">Active Runtime Agents</h3>
          <p class="recipe-desc">Agents and their permissions.</p>
        </div>
      </div>
      <div class="header-meta">
        <button class="usx-btn usx-btn--secondary m3-button" @click="srv.fetchAgents">
          <UIcon name="refresh" />
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
import UIcon from "../../../skills/atoms/UIcon.vue";

const srv = useSnackbarOpsStore();
</script>

<style scoped>

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

.server-agent-name {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 500;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.agent-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, var(--usx-color-primary));
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
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
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
  background: color-mix(in srgb, var(--usx-color-success) 15%, transparent);
  color: var(--usx-color-success);
}

.status-pill--neutral {
  background: color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}
</style>
