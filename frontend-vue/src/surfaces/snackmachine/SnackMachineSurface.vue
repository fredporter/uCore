<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="SNACKMACHINE_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />

    <div class="surface__content">
      <div class="surface__panel sm-consolidation-banner">
        <h3 class="surface__panel-title sm-heading">SnackMachine Consolidation</h3>
        <p class="sm-muted-copy">
          SnackMachine is being consolidated. This launcher keeps legacy tabs while routing each capability to its new canonical surface.
        </p>
      </div>

      <div class="surface__panel sm-launcher-card">
        <h4 class="sm-title">{{ activeGuide.title }}</h4>
        <p class="sm-muted-copy">{{ activeGuide.description }}</p>

        <div class="sm-actions">
          <UButton
            v-for="action in activeGuide.actions"
            :key="action.label"
            :variant="action.primary ? 'primary' : 'secondary'"
            size="sm"
            @click="goTo(action.to)"
          >
            {{ action.label }}
          </UButton>
        </div>

        <p class="sm-footnote">Legacy tab: {{ activeTab }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import { SNACKMACHINE_TABS, type SnackMachineTab } from '../../stores/snackmachine'
import UButton from '../../skills/atoms/UButton.vue'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

interface LauncherAction {
  label: string
  to: string
  primary?: boolean
}

interface LauncherGuide {
  title: string
  description: string
  actions: LauncherAction[]
}

const shell = useShellStore()
const route = useRoute()
const router = useRouter()

const VALID_TABS = new Set<SnackMachineTab>(SNACKMACHINE_TABS.map(tab => tab.id))
const routeTab = String(route.query.tab || 'snacks')
const activeTab = ref<SnackMachineTab>(VALID_TABS.has(routeTab as SnackMachineTab) ? (routeTab as SnackMachineTab) : 'snacks')

const TAB_GUIDES: Record<SnackMachineTab, LauncherGuide> = {
  snacks: {
    title: 'Runtime Snacks Moved to Server',
    description: 'Snack queue visibility and system snack inventory now live on the Server surface.',
    actions: [
      { label: 'Open Server Snacks', to: '/server?tab=snacks', primary: true },
      { label: 'Open Server Dashboard', to: '/server?tab=dashboard' },
    ],
  },
  workflows: {
    title: 'Workflows Belong to Workflow Surface',
    description: 'Workflow creation, execution, and mission context are now canonical in Workflow.',
    actions: [
      { label: 'Open Workflow', to: '/workflow', primary: true },
      { label: 'Open Workflow Publish', to: '/workflow?tab=publish' },
    ],
  },
  mcp: {
    title: 'MCP Operations Belong to Developer',
    description: 'MCP server health and capability management are dev-lane responsibilities.',
    actions: [
      { label: 'Open Developer MCP', to: '/developer?tab=mcp-servers', primary: true },
      { label: 'Open Developer Tools', to: '/developer?tab=tools' },
    ],
  },
  vault: {
    title: 'Vault Sync Belongs to Workflow',
    description: 'Vault ingestion and mission-task-binder mapping are managed in Workflow.',
    actions: [
      { label: 'Open Workflow Binder', to: '/workflow?tab=binder', primary: true },
      { label: 'Open Workflow Publish', to: '/workflow?tab=publish' },
    ],
  },
  variables: {
    title: 'Variables and Settings Belong to System',
    description: 'User and global settings are now managed under System settings tabs.',
    actions: [
      { label: 'Open System Variables', to: '/system?tab=variables', primary: true },
      { label: 'Open System Global Settings', to: '/system?tab=global-settings' },
      { label: 'Open System User Settings', to: '/system?tab=user-settings' },
    ],
  },
  scheduler: {
    title: 'Runtime Scheduling Visibility Belongs to Server',
    description: 'Use Server for live runtime health; use Workflow for task publish and execution.',
    actions: [
      { label: 'Open Server Dashboard', to: '/server?tab=dashboard', primary: true },
      { label: 'Open Workflow Publish', to: '/workflow?tab=publish' },
    ],
  },
}

const activeGuide = computed(() => TAB_GUIDES[activeTab.value])

function goTo(target: string) {
  router.push(target)
}

watch(activeTab, (tab) => {
  const current = String(route.query.tab || '')
  if (current === tab) return
  router.replace({
    path: '/snackmachine',
    query: { ...route.query, tab },
  })
})
</script>

<style scoped>
.sm-consolidation-banner {
  border-style: solid;
  border-width: var(--usx-border-width-thick);
  border-color: var(--usx-color-info);
  margin-bottom: var(--usx-spacing-md);
}

.sm-heading {
  margin: 0 0 var(--usx-spacing-sm);
}

.sm-launcher-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.sm-title {
  margin: 0;
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.sm-muted-copy {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.sm-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.sm-footnote {
  margin: 0;
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}
</style>
