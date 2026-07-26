<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Runtime Agents</h3>
      <UButton variant="secondary" size="sm" icon="refresh" @click="srv.fetchAgents">Refresh</UButton>
    </div>
    <div v-if="srv.agents.length === 0" class="server-muted-text">No agents available.</div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Description</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="agent in srv.agents" :key="agent.id">
            <td>
              <span class="server-agent-name">
                <UIcon :name="agent.icon" />
                <span>{{ agent.name }}</span>
              </span>
            </td>
            <td class="server-agent-desc">{{ agent.description }}</td>
            <td>
              <UBadge :type="agent.active ? 'success' : 'info'" size="sm">{{ agent.active ? 'running' : 'idle' }}</UBadge>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useServerStore } from '../../../stores/server'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'
import UButton from '../../../skills/atoms/UButton.vue'

const srv = useServerStore()
</script>

<style scoped>
.server-muted-text { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); padding: var(--usx-spacing-md); }
.server-table-wrap { overflow-x: auto; }
.server-table { width: 100%; border-collapse: collapse; font-size: var(--usx-font-size-sm); }
.server-table th { text-align: left; font-weight: var(--usx-font-weight-semibold); color: var(--usx-color-on-surface-muted); padding: var(--usx-spacing-sm); border-bottom: var(--usx-border-width) solid var(--usx-color-border); white-space: nowrap; }
.server-table td { padding: var(--usx-spacing-sm); border-bottom: var(--usx-border-width) solid var(--usx-color-border); vertical-align: middle; }
.server-agent-name { display: inline-flex; align-items: center; gap: var(--usx-spacing-sm); font-weight: var(--usx-font-weight-semibold); }
.server-agent-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin: 0; }
</style>