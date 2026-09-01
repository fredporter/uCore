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
    <div class="surface__content snackbar-server-content">
      <section class="surface__panel snackbar-server-header">
        <div class="snackbar-server-header__row">
          <h3 class="surface__panel-title">Server</h3>
          <span class="snackbar-server-header__badge">Runtime Surface</span>
        </div>
        <p class="surface__panel-description">
          Runtime health, AI configuration, automation, extensions, and logs.
        </p>
      </section>

      <!-- Dashboard -->
      <div v-if="activeTab === 'dashboard'" class="server-tab-shell">
        <SnackbarDashboardPanel />
      </div>

      <!-- Services -->
      <div v-else-if="activeTab === 'services'" class="server-tab-shell">
        <SnackbarServicesPanel />
      </div>
      <!-- AI: models, agents, and budget share one operational context -->
      <div v-else-if="activeTab === 'ai'" class="server-tab-shell server-panel-stack">
        <SnackbarModelsPanel />
        <SnackbarAgentsPanel />
        <SnackbarBudgetPanel />
      </div>
      <!-- Automation: the inputs, capabilities, and schedules of one pipeline -->
      <div v-else-if="activeTab === 'automation'" class="server-tab-shell server-panel-stack">
        <section class="surface__panel">
          <h3 class="surface__panel-title">Automations &amp; Skills Runner</h3>
          <p class="surface__panel-description">
            The master library and runtime for reusable skills, feed inputs, and scheduled automations. Workflows invoke registered items from here.
          </p>
        </section>
        <SnackbarFeedsPanel />
        <SnackbarSkillsPanel />
        <SnackbarSnacksPanel />
      </div>
      <!-- Extensions -->
      <div v-else-if="activeTab === 'extensions'" class="server-tab-shell">
        <SnackbarExtensionsPanel />
      </div>
      <!-- Logs -->
      <div v-else-if="activeTab === 'logs'" class="server-tab-shell">
        <SnackbarLogsPanel />
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
 * Dashboard, services, agents, feeds, skills, snacks, logs, extensions.
 * @category surfaces
 * @usage Routed at '/snackbar/*'
 */
import {
  computed,
  onMounted,
  onBeforeUnmount,
  defineAsyncComponent,
  watch,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import SnackbarDashboardPanel from "./panels/SnackbarDashboardPanel.vue";
const SnackbarServicesPanel = defineAsyncComponent(
  () => import("./panels/SnackbarServicesPanel.vue"),
);
const SnackbarAgentsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarAgentsPanel.vue"),
);
const SnackbarModelsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarModelsPanel.vue"),
);
const SnackbarBudgetPanel = defineAsyncComponent(
  () => import("./panels/SnackbarBudgetPanel.vue"),
);
const SnackbarFeedsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarFeedsPanel.vue"),
);
const SnackbarSkillsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarSkillsPanel.vue"),
);
const SnackbarSnacksPanel = defineAsyncComponent(
  () => import("./panels/SnackbarSnacksPanel.vue"),
);
const SnackbarExtensionsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarExtensionsPanel.vue"),
);
const SnackbarLogsPanel = defineAsyncComponent(
  () => import("./panels/SnackbarLogsPanel.vue"),
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
  const legacyTabs: Record<string, SnackbarOpsTab> = {
    agents: "ai",
    models: "ai",
    budget: "ai",
    feeds: "automation",
    skills: "automation",
    snacks: "automation",
  };
  if (legacyTabs[tab]) return legacyTabs[tab];
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
  srv.startHealthPolling(15000);
});

onBeforeUnmount(() => {
  srv.stopHealthPolling();
});
</script>

<style scoped>
.surface__content {
  padding: var(--usx-spacing-lg);
}

.snackbar-server-content {
  display: grid;
  gap: var(--usx-spacing-md);
}

.snackbar-server-header {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--usx-color-primary) 4%, transparent) 0%,
    transparent 78%
  );
}

.snackbar-server-header__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.snackbar-server-header__badge {
  display: inline-flex;
  align-items: center;
  min-height: calc(var(--usx-touch-target-compact) - var(--usx-spacing-xs));
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  background: color-mix(in srgb, var(--usx-color-surface-variant) 75%, var(--usx-color-surface));
}

.server-tab-shell {
  width: 100%;
  box-sizing: border-box;
  min-width: 0;
}

.server-panel-stack {
  display: grid;
  gap: var(--usx-spacing-md);
}

/* Shared USX standard layer across Server tabs */
.snackbar-server-content :deep(.surface__panel) {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-surface) 96%, var(--usx-color-background));
  padding: var(--usx-spacing-md);
  box-shadow: 0 1px 0 color-mix(in srgb, var(--usx-color-border) 40%, transparent);
}

.snackbar-server-content :deep(.surface__panel-title) {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.snackbar-server-content :deep(.surface__panel-description) {
  margin: var(--usx-spacing-xs) 0 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.snackbar-server-content :deep(button:not(.surface-tab-nav__link)) {
  min-height: var(--usx-touch-target-compact);
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: color-mix(in srgb, var(--usx-color-surface) 94%, var(--usx-color-surface-variant));
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
}

.snackbar-server-content :deep(input),
.snackbar-server-content :deep(select),
.snackbar-server-content :deep(textarea) {
  min-height: var(--usx-touch-target-compact);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
}

.snackbar-server-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  overflow: hidden;
  background: var(--usx-color-surface);
}

.snackbar-server-content :deep(th),
.snackbar-server-content :deep(td) {
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border-light);
  font-size: var(--usx-font-size-sm);
  text-align: left;
}

.snackbar-server-content :deep(th) {
  color: var(--usx-color-on-surface-muted);
  background: color-mix(in srgb, var(--usx-color-surface-variant) 78%, var(--usx-color-surface));
  font-weight: var(--usx-font-weight-medium);
}
</style>
