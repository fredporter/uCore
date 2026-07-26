<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">All Services</h3>
      <UButton variant="secondary" size="sm" icon="refresh" @click="srv.fetchServices">Refresh</UButton>
    </div>
    <div v-if="srv.services.length === 0" class="server-muted-text-sm">No services available.</div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
        <thead>
          <tr>
            <th>Service</th>
            <th>Description</th>
            <th>Port</th>
            <th>Uptime</th>
            <th>Type</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="svc in srv.services" :key="svc.name">
            <td>
              <span class="server-service-name-cell">
                <UIcon :name="svc.type === 'system' ? 'settings' : 'person'" />
                <span>{{ svc.name }}</span>
              </span>
            </td>
            <td class="server-muted-text-sm">{{ svc.description }}</td>
            <td class="server-muted-text-sm">:{{ svc.port || 'N/A' }}</td>
            <td class="server-muted-text-sm">{{ svc.uptime }}%</td>
            <td class="server-muted-text-sm">{{ svc.type }}</td>
            <td>
              <UBadge :type="svc.status === 'up' ? 'success' : svc.status === 'degraded' ? 'warning' : 'error'" size="sm">
                {{ svc.status }}
              </UBadge>
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
.server-muted-text-sm { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.server-table-wrap { overflow-x: auto; }
.server-table { width: 100%; border-collapse: collapse; font-size: var(--usx-font-size-sm); }
.server-table th { text-align: left; font-weight: var(--usx-font-weight-semibold); color: var(--usx-color-on-surface-muted); padding: var(--usx-spacing-sm); border-bottom: var(--usx-border-width) solid var(--usx-color-border); white-space: nowrap; }
.server-table td { padding: var(--usx-spacing-sm); border-bottom: var(--usx-border-width) solid var(--usx-color-border); vertical-align: middle; }
.server-service-name-cell { display: inline-flex; align-items: center; gap: var(--usx-spacing-sm); font-weight: var(--usx-font-weight-semibold); min-width: 0; overflow-wrap: anywhere; }
</style>