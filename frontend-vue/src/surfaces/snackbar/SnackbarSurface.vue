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
      <div
        v-if="activeTab === 'dashboard'"
        class="surface__panel server-tab-shell"
      >
        <SnackbarDashboardPanel />
      </div>

      <!-- Services -->
      <div
        v-else-if="activeTab === 'services'"
        class="surface__panel server-tab-shell"
      >
        <SnackbarServicesPanel />
      </div>
      <!-- Snacks -->
      <div
        v-else-if="activeTab === 'snacks'"
        class="surface__panel server-tab-shell"
      >
        <SnackbarSnacksPanel />
      </div>
      <!-- Logs -->
      <div
        v-else-if="activeTab === 'logs'"
        class="surface__panel server-tab-shell"
      >
        <SnackbarLogsPanel />
      </div>
      <!-- Models -->
      <div
        v-else-if="activeTab === 'models'"
        class="surface__panel server-tab-shell"
      >
        <SnackbarModelsPanel />
      </div>
      <!-- Agents -->
      <div
        v-else-if="activeTab === 'agents'"
        class="surface__panel server-tab-shell"
      >
        <SnackbarAgentsPanel />
      </div>
      <!-- Budget -->
      <div
        v-else-if="activeTab === 'budget'"
        class="surface__panel server-tab-shell"
      >
        <SnackbarBudgetPanel />
      </div>
      <div v-else class="surface__panel server-tab-shell">
        <SnackbarDashboardPanel />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SnackbarSurface
 * @description Snackbar operations surface — wired to /api/server/* backend.
 * Dashboard, services, logs, models, runtime agents, budget.
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
const SnackbarLogsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarLogsPanel.vue"),
);
const SnackbarModelsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarModelsPanel.vue"),
);
const SnackbarAgentsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarAgentsPanel.vue"),
);
const SnackbarBudgetPanel = defineAsyncComponent(
  () => import("./panels/SnackbarBudgetPanel.vue"),
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
