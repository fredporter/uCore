<template>
  <div class="sidebar-mode" role="group" aria-label="Sidebar content">
    <button v-for="mode in modes" :key="mode.id" class="usx-btn" :aria-pressed="shell.sidebarMode === mode.id" @click="shell.setSidebarMode(mode.id)"><UIcon :name="mode.icon" />{{ mode.label }}</button>
  </div>
</template>
<script setup lang="ts">
import { useShellStore } from '../../stores/shell';
import UIcon from '../atoms/UIcon.vue';
const shell = useShellStore();
const modes = [{ id: 'vault', label: 'Vault', icon: 'folder_open' }, { id: 'workflow', label: 'Binders', icon: 'list_alt' }] as const;
</script>
<style scoped>
.sidebar-mode { display: flex; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); border-bottom: 1px solid var(--usx-color-border); flex-shrink: 0; }
.sidebar-mode .usx-btn { flex: 1; min-width: 0; padding: var(--usx-spacing-xs); font-size: var(--usx-font-size-sm); white-space: nowrap; height: 32px; min-height: 32px; margin: 0; border: 0; box-shadow: none; justify-content: center; }
.sidebar-mode [aria-pressed="true"] { color: var(--usx-color-primary); background: var(--usx-color-surface-hover); }
</style>
