<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <h3 class="surface__panel-title">Runtime Snacks</h3>
      <UButton variant="secondary" size="sm" icon="refresh" @click="srv.fetchSnacks">Refresh</UButton>
    </div>

    <div v-if="srv.snacks.length === 0" class="server-muted-text">No queued snacks.</div>
    <div v-else class="server-snacks-list">
      <div v-for="snack in srv.snacks" :key="snack.id" class="surface__panel server-snack-row">
        <div class="usx-flex-row usx-gap-sm">
          <UIcon :name="snack.type === 'workflow' ? 'account_tree' : snack.type === 'clipboard' ? 'content_paste' : 'restaurant_menu'" />
          <span class="server-snack-type">{{ snack.type }}</span>
          <UBadge type="info" size="sm">{{ snack.priority }}</UBadge>
          <UBadge :type="snack.status === 'queued' ? 'warning' : snack.status === 'active' ? 'success' : 'neutral'" size="sm">
            {{ snack.status }}
          </UBadge>
        </div>
        <div class="server-snack-meta">
          <span>{{ snack.source }}</span>
          <span>{{ snack.timestamp || 'pending' }}</span>
        </div>
      </div>
    </div>

    <div class="surface__panel usx-mt-md">
      <h4 class="surface__panel-title server-subheading">System Snacks</h4>
      <div v-if="srv.systemSnacks.length === 0" class="server-muted-text">No system snacks discovered.</div>
      <div v-else class="server-system-snacks">
        <div v-for="snack in srv.systemSnacks" :key="snack.id" class="server-system-snack-row">
          <span class="server-system-snack-name">{{ snack.name }}</span>
          <UBadge type="info" size="sm">{{ snack.kind }}</UBadge>
        </div>
      </div>
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
.server-muted-text {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-md);
}
.server-snacks-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}
.server-snack-row {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}
.server-snack-type {
  font-weight: var(--usx-font-weight-semibold);
}
.server-snack-meta {
  display: flex;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}
.server-subheading {
  margin-bottom: var(--usx-spacing-sm);
}
.server-system-snacks {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}
.server-system-snack-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) 0;
}
.server-system-snack-name {
  font-size: var(--usx-font-size-sm);
}
</style>
