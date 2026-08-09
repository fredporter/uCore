<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Events</h3>
      <UButton
        variant="secondary"
        size="sm"
        icon="refresh"
        @click="srv.fetchSnacks"
        >Refresh</UButton
      >
    </div>
    <p class="server-muted-text">
      Feed-spool queue — messages, tasks, commands and notifications flowing
      through the system.
    </p>

    <div v-if="srv.snacks.length === 0" class="server-muted-text">
      No queued events.
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Source</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="snack in srv.snacks" :key="snack.id">
            <td>
              <span class="server-snack-type">
                <UIcon
                  :name="
                    snack.type === 'workflow'
                      ? 'account_tree'
                      : snack.type === 'clipboard'
                        ? 'content_paste'
                        : 'rss_feed'
                  "
                />
                <span>{{ snack.type }}</span>
              </span>
            </td>
            <td>
              <UBadge type="info" size="sm">{{ snack.priority }}</UBadge>
            </td>
            <td>
              <UBadge
                :type="
                  snack.status === 'queued'
                    ? 'warning'
                    : snack.status === 'active'
                      ? 'success'
                      : 'neutral'
                "
                size="sm"
              >
                {{ snack.status }}
              </UBadge>
            </td>
            <td class="server-muted-text">{{ snack.source }}</td>
            <td class="server-muted-text">
              {{ snack.timestamp || "pending" }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
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
.server-snack-type {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  font-weight: var(--usx-font-weight-semibold);
}
.server-subheading {
  margin-bottom: var(--usx-spacing-sm);
}
.server-system-snack-name {
  font-size: var(--usx-font-size-sm);
}
</style>
