<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="srv.activeTab"
      :tabs="SERVER_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <!-- Dashboard -->
      <ServerDashboardPanel v-if="activeTab === 'dashboard'" />

      <!-- Services -->
      <ServerServicesPanel v-else-if="activeTab === 'services'" />
      <!-- Snacks -->
      <ServerSnacksPanel v-else-if="activeTab === 'snacks'" />
      <!-- Logs -->
      <ServerLogsPanel v-else-if="activeTab === 'logs'" />
      <!-- Models -->
      <ServerModelsPanel v-else-if="activeTab === 'models'" />
      <!-- Agents -->
      <ServerAgentsPanel v-else-if="activeTab === 'agents'" />
      <!-- Budget -->
      <ServerBudgetPanel v-else-if="activeTab === 'budget'" />
      <ServerDashboardPanel v-else />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ServerSurface
 * @description Server operations surface — wired to /api/server/* backend.
 * Dashboard, services, logs, models, runtime agents, budget.
 * @category surfaces
 * @usage Routed at '/server/*'
 */
import { computed, onMounted, defineAsyncComponent, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import ServerDashboardPanel from './panels/ServerDashboardPanel.vue'
const ServerServicesPanel = defineAsyncComponent(() => import('./panels/ServerServicesPanel.vue'))
const ServerSnacksPanel = defineAsyncComponent(() => import('./panels/ServerSnacksPanel.vue'))
const ServerLogsPanel = defineAsyncComponent(() => import('./panels/ServerLogsPanel.vue'))
const ServerModelsPanel = defineAsyncComponent(() => import('./panels/ServerModelsPanel.vue'))
const ServerAgentsPanel = defineAsyncComponent(() => import('./panels/ServerAgentsPanel.vue'))
const ServerBudgetPanel = defineAsyncComponent(() => import('./panels/ServerBudgetPanel.vue'))
import { useServerStore, SERVER_TABS, type ServerTab } from '../../stores/server'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const shell = useShellStore()
const srv = useServerStore()
const route = useRoute()
const router = useRouter()

const VALID_SERVER_TABS = new Set<ServerTab>(SERVER_TABS.map(tab => tab.id))

function normalizeServerTab(tab: string | null | undefined): ServerTab {
  if (!tab) return 'dashboard'
  return VALID_SERVER_TABS.has(tab as ServerTab) ? (tab as ServerTab) : 'dashboard'
}

const activeTab = computed(() => normalizeServerTab(String(srv.activeTab || 'dashboard')))

watch(
  () => route.query.tab,
  (queryTab) => {
    const next = normalizeServerTab(String(queryTab || 'dashboard'))
    if (srv.activeTab !== next) {
      srv.setTab(next)
    }
  },
  { immediate: true }
)

watch(
  () => srv.activeTab,
  (tab) => {
    const normalized = normalizeServerTab(String(tab || 'dashboard'))
    if (tab !== normalized) {
      srv.setTab(normalized)
      return
    }

    const current = String(route.query.tab || '')
    if (current !== normalized) {
      router.replace({ query: { ...route.query, tab: normalized } })
    }
  },
  { immediate: true }
)

onMounted(() => {
  srv.fetchAll()
})
</script>

<style></style>
