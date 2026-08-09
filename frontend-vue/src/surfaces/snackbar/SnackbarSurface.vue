<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      v-model="srv.activeTab"
      :tabs="SNACKBAR_OPS_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <!-- Dashboard -->
      <div v-if="activeTab === 'dashboard'" class="server-tab-shell">
        <SnackbarDashboardPanel />
      </div>

      <!-- Services -->
      <div v-else-if="activeTab === 'services'" class="server-tab-shell">
        <SnackbarServicesPanel />
      </div>
      <!-- Skills/Executables -->
      <div v-else-if="activeTab === 'skills'" class="server-tab-shell">
        <SnackbarSkillsPanel />
      </div>
      <!-- Events (feed-spool) -->
      <div v-else-if="activeTab === 'snacks'" class="server-tab-shell">
        <SnackbarSnacksPanel />
      </div>
      <!-- Logs -->
      <div v-else-if="activeTab === 'logs'" class="server-tab-shell">
        <SnackbarLogsPanel />
      </div>
      <!-- Plugins -->
      <div v-else-if="activeTab === 'plugins'" class="server-tab-shell">
        <SnackbarPluginsPanel />
      </div>
      <div v-else class="server-tab-shell">
        <SnackbarDashboardPanel />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SnackbarSurface
 * @description Snackbar operations surface — wired to /api/server/* backend.
 * Dashboard, services, snacks, logs, plugins.
 * @category surfaces
 * @usage Routed at '/snackbar/*'
 */
import { computed, onMounted, defineAsyncComponent, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import SnackbarDashboardPanel from "./panels/SnackbarDashboardPanel.vue";
const SnackbarServicesPanel = defineAsyncComponent(
  () => import("./panels/SnackbarServicesPanel.vue"),
);
const SnackbarSnacksPanel = defineAsyncComponent(
  () => import("./panels/SnackbarSnacksPanel.vue"),
);
const SnackbarSkillsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarSkillsPanel.vue"),
);
const SnackbarLogsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarLogsPanel.vue"),
);
const SnackbarPluginsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarPluginsPanel.vue"),
);
import {
  useSnackbarOpsStore,
  SNACKBAR_OPS_TABS,
  type SnackbarOpsTab,
} from "../../stores/snackbarOps";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";

const shell = useShellStore();
const srv = useSnackbarOpsStore();
const route = useRoute();
const router = useRouter();

const VALID_SNACKBAR_OPS_TABS = new Set<SnackbarOpsTab>(
  SNACKBAR_OPS_TABS.map((tab) => tab.id),
);

function normalizeSnackbarOpsTab(
  tab: string | null | undefined,
): SnackbarOpsTab {
  if (!tab) return "dashboard";
  return VALID_SNACKBAR_OPS_TABS.has(tab as SnackbarOpsTab)
    ? (tab as SnackbarOpsTab)
    : "dashboard";
}

const activeTab = computed(() =>
  normalizeSnackbarOpsTab(String(srv.activeTab || "dashboard")),
);

watch(
  () => route.query.tab,
  (queryTab) => {
    const next = normalizeSnackbarOpsTab(String(queryTab || "dashboard"));
    if (srv.activeTab !== next) {
      srv.setTab(next);
    }
  },
  { immediate: true },
);

watch(
  () => srv.activeTab,
  (tab) => {
    const normalized = normalizeSnackbarOpsTab(String(tab || "dashboard"));
    if (tab !== normalized) {
      srv.setTab(normalized);
      return;
    }

    const current = String(route.query.tab || "");
    if (current !== normalized) {
      router.replace({ query: { ...route.query, tab: normalized } });
    }
  },
  { immediate: true },
);

onMounted(() => {
  srv.fetchAll();
});
</script>

<style scoped>
.surface__content {
  padding: var(--usx-spacing-lg);
}

.server-tab-shell {
  width: 100%;
  box-sizing: border-box;
  min-width: 0;
}
</style>
