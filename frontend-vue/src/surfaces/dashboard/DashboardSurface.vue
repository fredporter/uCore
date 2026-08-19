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

        <!-- Active Extensions section -->
        <template v-if="activeExtensions.length > 0">
          <h2 class="dashboard-surface__section-title">Active Extensions</h2>
          <div
            class="dashboard-surface__grid-inner dashboard-surface__grid-inner--extensions"
          >
            <SurfaceCard
              v-for="ext in activeExtensions"
              :key="ext.id"
              :surface="ext"
              @click="navigate(ext.route)"
            />
          </div>
        </template>
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
import { ref, computed, watch, onMounted } from "vue";
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
  { id: "intelligence", label: "Intelligence", icon: "lightbulb" },
  { id: "snackbar", label: "Snackbar", icon: "storefront" },
  { id: "system", label: "System", icon: "settings" },
];

const activeHubTab = ref("dashboard");

const visibleHubTabs = computed(() => HUB_TABS);

watch(activeHubTab, (tabId) => {
  if (!tabId || tabId === "dashboard") return;
  const routes: Record<string, string> = {
    workflow: "/workflow?tab=mission-control",
    intelligence: "/intelligence",
    snackbar: "/snackbar",
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
    icon: "lightbulb",
    route: "/intelligence",
    color: "var(--usx-color-accent)",
  },
  workflow: {
    title: "Workflow",
    description: "Missions, Tasks & Binder",
    icon: "flag",
    route: "/workflow?tab=mission-control",
    color: "var(--usx-color-primary)",
  },
  ucode: {
    title: "uCode",
    description: "GridCore — Grid, Teletext & Terminal",
    icon: "grid",
    route: "/ucode",
    color: "var(--usx-color-success)",
  },
  snackbar: {
    title: "Snackbar Server",
    description: "Server Ops, Services, Snacks & Logs",
    icon: "storefront",
    route: "/snackbar",
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
    description: "Repositories, Code Review & Editing",
    icon: "code",
    route: "/developer",
    color: "var(--usx-color-danger)",
  },
  markdown: {
    title: "Editor",
    description: "WYSIWYG Prose and Code Editor",
    icon: "diamond",
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
  const seen = new Set<string>();
  for (const surface of extStore.visibleSurfaces) {
    const card = SURFACE_CARD_DATA[surface.manifest.id];
    if (card) {
      cards.push({
        id: surface.manifest.id,
        ...card,
        status: surface.status === "running" ? "running" : undefined,
      });
      seen.add(surface.manifest.id);
    }
  }
  // Developer is a built-in uCore surface. Guard against catalogue duplicates.
  if (!seen.has("developer")) {
    cards.push({ id: "developer", ...SURFACE_CARD_DATA.developer });
  }
  // Always show Markdown Editor card
  cards.push({ id: "markdown", ...SURFACE_CARD_DATA.markdown });

  return cards;
});

// Active extensions to show as cards below the main surfaces
const activeExtensions = computed(() => {
  // Filter out surface/core kinds — only show actual plugins that are enabled/running
  return extStore.all
    .filter(
      (e) =>
        e.manifest.kind === "plugin" &&
        (e.status === "running" || e.status === "installed"),
    )
    .map((e) => ({
      id: e.manifest.id,
      title: e.manifest.name,
      description: e.manifest.description || "Installed extension",
      icon: e.manifest.icon || "extension",
      route: `/snackbar?tab=extensions#${e.manifest.id}`,
      color: "var(--usx-color-primary)",
      status: e.status as "running" | "stopped" | "error",
    }));
});

onMounted(() => {
  void extStore.fetchCatalogue();
});

function navigate(route: string) {
  if (route.startsWith("http")) {
    window.open(route, "_blank");
    return;
  }

  // Normalize workflow navigation so UIHub cards always open the intended tab.
  if (route.startsWith("/workflow")) {
    const url = new URL(route, window.location.origin);
    const tab = (url.searchParams.get("tab") || "mission-control").trim();
    router.push({ path: "/workflow", query: { tab } });
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

.dashboard-surface__grid-inner--extensions {
  --dashboard-column-min: calc(var(--usx-touch-min) * 10);
  opacity: 0.85;
}

.dashboard-surface__section-title {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  margin: var(--usx-spacing-xl) 0 var(--usx-spacing-md);
  padding-bottom: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}
</style>
