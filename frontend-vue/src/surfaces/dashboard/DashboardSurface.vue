<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <!-- Hub navigation: quick-launch links to key surfaces -->
    <SurfaceTabNav
      v-model="activeHubTab"
      :tabs="visibleHubTabs"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <div class="dashboard-surface">
        <h1 class="dashboard-surface__title">Dashboard</h1>
        <p class="dashboard-surface__subtitle">Select a surface to begin</p>

        <div class="dashboard-surface__grid-inner">
          <SurfaceCard
            v-for="surface in visibleSurfaces"
            :key="surface.id"
            :surface="surface"
            @click="navigate(surface.route)"
          />
        </div>

        <div v-if="!hasUdevRunning" class="dashboard-surface__dev-hint">
          <p>
            <span class="material-symbols-outlined">code_off</span>
            Developer surface hidden — start uDev to enable.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component DashboardSurface
 * @description Mission Control — surface hub dashboard with surface cards and hub navigation.
 * Ported from DashboardSurface.tsx (React).
 * Enhanced with Dev Mode filtering — dev-only surfaces hidden when Dev Mode is off.
 * @category surfaces
 * @usage Routed at '/' — default landing page.
 */
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import { useExtensionStore } from "../../stores/extensions";
import SurfaceCard from "../../skills/molecules/SurfaceCard.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";

const router = useRouter();
const shell = useShellStore();
const extStore = useExtensionStore();

// Hub navigation tabs — core + running surfaces
const HUB_TABS = [
  { id: "dashboard", label: "Dashboard", icon: "home" },
  { id: "workflow", label: "Workflow", icon: "flag" },
  { id: "intelligence", label: "Intelligence", icon: "psychology" },
  { id: "system", label: "System", icon: "settings" },
];

const activeHubTab = ref("dashboard");

const visibleHubTabs = computed(() => HUB_TABS);

watch(activeHubTab, (tabId) => {
  if (!tabId || tabId === "dashboard") return;
  const routes: Record<string, string> = {
    workflow: "/workflow?tab=mission-control",
    intelligence: "/intelligence",
    system: "/system",
  };
  const path = routes[tabId];
  if (path) router.push(path);
});

// Surface cards — driven by extension store: required OR running
const SURFACE_CARD_DATA: Record<
  string,
  {
    title: string;
    description: string;
    icon: string;
    route: string;
    color: string;
  }
> = {
  intelligence: {
    title: "Intelligence",
    description: "Chat settings, models, agents & budget",
    icon: "psychology",
    route: "/intelligence",
    color: "var(--usx-color-accent)",
  },
  workflow: {
    title: "Workflow",
    description: "Missions, Tasks & Binder",
    icon: "flag",
    route: "/workflow",
    color: "var(--usx-color-primary)",
  },
  ucode: {
    title: "uCode",
    description: "GridCore — Grid, Teletext & Terminal",
    icon: "grid",
    route: "/ucode",
    color: "var(--usx-color-success)",
  },
  server: {
    title: "Server",
    description: "Backend Operations & Services",
    icon: "server",
    route: "/server",
    color: "var(--usx-color-warning)",
  },
  system: {
    title: "System",
    description: "Admin, Pages & Tools",
    icon: "settings",
    route: "/system",
    color: "var(--usx-color-on-surface-muted)",
  },
  documentation: {
    title: "Documentation",
    description: "Learning Hub & Guides",
    icon: "menu_book",
    route: "/documentation",
    color: "var(--usx-color-accent)",
  },
  browserui: {
    title: "Browser",
    description: "Web Reader & Bookmarks",
    icon: "language",
    route: "/browserui",
    color: "var(--usx-color-info)",
  },
  groovebox: {
    title: "Groovebox",
    description: "Music Production — Pattern Composer & Vault",
    icon: "music_note",
    route: "/groovebox",
    color: "var(--usx-color-warning)",
  },
  sonic: {
    title: "Sonic",
    description: "USB Bootloader & System Toolkit",
    icon: "usb",
    route: "/sonic",
    color: "var(--usx-color-success)",
  },
  developer: {
    title: "Developer",
    description: "Dev Lane — Models, Agents, Kanban",
    icon: "code",
    route: "/developer",
    color: "var(--usx-color-danger)",
  },
  bangle: {
    title: "Bangle Editor",
    description: "Prose/Code drafting workspace with live preview",
    icon: "edit_note",
    route: "/workflow?tab=editor",
    color: "var(--usx-color-primary)",
  },
};

const visibleSurfaces = computed(() => {
  const cards: Array<{
    id: string;
    title: string;
    description: string;
    icon: string;
    route: string;
    color: string;
    status?: "running" | "stopped" | "error";
  }> = [];

  // Always show core surfaces + running optional surfaces
  for (const surface of extStore.visibleSurfaces) {
    const card = SURFACE_CARD_DATA[surface.manifest.id];
    if (card) {
      cards.push({
        id: surface.manifest.id,
        ...card,
        status: surface.status === "running" ? "running" : undefined,
      });
    }
  }
  // Always show Bangle Editor card
  cards.push({ id: "bangle", ...SURFACE_CARD_DATA.bangle });

  return cards;
});

// Dev hint: show when developer not running
const hasUdevRunning = computed(() => extStore.isRunning("udev"));

function navigate(route: string) {
  if (route.startsWith("http")) {
    window.open(route, "_blank");
    return;
  }
  router.push(route);
}
</script>

<style scoped>
.dashboard-surface {
  max-width: var(--usx-max-width);
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.dashboard-surface__title {
  font-size: var(--usx-font-size-3xl);
  font-weight: var(--usx-font-weight-bold);
  margin-bottom: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
}

.dashboard-surface__subtitle {
  color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-md);
  font-size: var(--usx-font-size-base);
}

.dashboard-surface__grid-inner {
  --dashboard-column-min: calc(var(--usx-touch-min) * 8);
  --dashboard-column-max: 3;
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--dashboard-column-min)), 1fr)
  );
  width: 100%;
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.dashboard-surface__dev-hint {
  margin-top: var(--usx-spacing-xl);
  padding: var(--usx-spacing-md);
  background: color-mix(in srgb, var(--usx-color-info) 5%, transparent);
  border: var(--usx-border-width) solid
    color-mix(in srgb, var(--usx-color-info) 15%, transparent);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.dashboard-surface__dev-hint p {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin: 0;
}

.dashboard-surface__dev-link {
  background: none;
  border: none;
  color: var(--usx-color-primary);
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
  text-decoration: underline;
  padding: 0;
}

.dashboard-surface__dev-link:hover {
  color: var(--usx-color-primary-hover);
}
</style>
