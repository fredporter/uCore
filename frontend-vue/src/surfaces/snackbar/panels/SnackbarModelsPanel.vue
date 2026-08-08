<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Model Usage</h3>
      <UButton
        variant="secondary"
        size="sm"
        icon="refresh"
        @click="srv.fetchModels"
        >Refresh</UButton
      >
    </div>
    <div v-if="srv.modelUsage.length === 0" class="server-muted-text">
      No model data available.
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Usage</th>
            <th>Calls</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in srv.modelUsage" :key="m.id">
            <td>{{ m.name }}</td>
            <td>
              <div class="model-usage-cell">
                <progress class="model-usage-bar" :value="m.pct" max="100" />
                <span class="server-muted-text">{{ m.pct }}%</span>
              </div>
            </td>
            <td class="model-calls">{{ m.calls }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import UButton from "../../../skills/atoms/UButton.vue";

const srv = useSnackbarOpsStore();
</script>

<style scoped>
.server-muted-text {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-md);
}
.server-table-wrap {
  overflow-x: auto;
}
.server-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-sm);
}
.server-table th {
  text-align: left;
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  white-space: nowrap;
}
.server-table td {
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  vertical-align: middle;
}
.model-usage-cell {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  min-width: calc(var(--usx-touch-min) * 4);
}
.model-usage-bar {
  flex: 1;
  width: 100%;
  height: var(--usx-spacing-sm);
  appearance: none;
  border: none;
  background: var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  overflow: hidden;
}
.model-usage-bar::-webkit-progress-bar {
  background: var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
}
.model-usage-bar::-webkit-progress-value {
  background: var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
}
.model-usage-bar::-moz-progress-bar {
  background: var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
}
.model-calls {
  text-align: right;
  color: var(--usx-color-on-surface-muted);
}
</style>
