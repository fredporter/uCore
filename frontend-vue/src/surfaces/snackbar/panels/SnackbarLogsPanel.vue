<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Service Logs</h3>
      <UButton
        variant="secondary"
        size="sm"
        icon="refresh"
        @click="() => srv.fetchLogs(20)"
        >Refresh</UButton
      >
    </div>
    <div v-if="srv.logs.length === 0" class="server-muted-text">
      No log entries available.
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table server-table--mono">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Service</th>
            <th>Level</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(log, i) in srv.logs" :key="i">
            <td class="log-timestamp">{{ log.timestamp }}</td>
            <td class="log-service">{{ log.service }}</td>
            <td>
              <span class="log-level" :class="'log-level--' + log.level">{{
                log.level
              }}</span>
            </td>
            <td class="log-message">{{ log.message }}</td>
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
.server-table--mono {
  font-family: var(--usx-font-family-mono);
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
  vertical-align: top;
}
.log-timestamp {
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
}
.log-service {
  color: var(--usx-color-primary);
  white-space: nowrap;
}
.log-level {
  display: inline-block;
  min-width: 6ch;
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  font-size: var(--usx-font-size-sm);
}
.log-level--info {
  color: var(--usx-color-primary);
}
.log-level--warn {
  color: var(--usx-color-warning);
}
.log-level--error {
  color: var(--usx-color-danger);
}
.log-message {
  color: var(--usx-color-on-surface);
}
</style>
