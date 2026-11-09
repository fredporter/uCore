<template>
  <div
    class="surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <aside v-if="connectionSetupNeeded" class="dashboard-setup"><span>Set up your local profile and workspace.</span><button class="usx-btn" @click="router.push('/setup')">Set up workspace</button></aside>
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
import { useSettingsStore } from "../../stores/settings";
import { useShellStore } from "../../stores/shell";
import { useExtensionStore } from "../../stores/extensions";
import { ucoreApi } from "../../api/client";
import SurfaceCard from "../../skills/molecules/SurfaceCard.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";

const router = useRouter();
const shell = useShellStore();
const extStore = useExtensionStore();

// Hub navigation tabs — core + running surfaces
const HUB_TABS = [
  { id: "dashboard", label: "Dashboard", icon: "home" },
  { id: "workflow", label: "Workflow", icon: "schedule" },
  { id: "server", label: "Server", icon: "dns" },
  { id: "snackbar", label: "Snackbar", icon: "storefront" },
  { id: "system", label: "System", icon: "settings" },
];

const activeHubTab = ref("dashboard");

const visibleHubTabs = computed(() => HUB_TABS);

watch(activeHubTab, (tabId) => {
  if (!tabId || tabId === "dashboard") return;
  const routes: Record<string, string> = {
    workflow: "/workflow?tab=mission-control",
    snackbar: "/snackbar",
    server: "/server",
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
  workflow: {
    title: "Workflow",
    description: "Tasks, missions and files",
    icon: "flag",
    route: "/workflow?tab=mission-control",
    color: "var(--usx-color-primary)",
  },
  ucode: {
    title: "uCode",
    description: "Coding and graphics",
    icon: "grid",
    route: "/ucode",
    color: "var(--usx-color-success)",
  },
  server: { title: "Server", description: "Local infrastructure and storage", icon: "dns", route: "/server", color: "var(--usx-color-info)" },
  snackbar: {
    title: "Snackbar",
    description: "Services and automation",
    icon: "dns",
    route: "/snackbar",
    color: "var(--usx-color-warning)",
  },
  system: {
    title: "System",
    description: "Settings and tools",
    icon: "settings",
    route: "/system",
    color: "var(--usx-color-on-surface-muted)",
  },
  documentation: {
    title: "Knowledge",
    description: "Guides",
    icon: "menu_book",
    route: "/documentation",
    color: "var(--usx-color-accent)",
  },
  browserui: {
    title: "Research",
    description: "Research and bookmarks",
    icon: "language",
    route: "/workflow?tab=research",
    color: "var(--usx-color-info)",
  },
  groovebox: {
    title: "Groovebox",
    description: "Make music",
    icon: "music_note",
    route: "/groovebox",
    color: "var(--usx-color-warning)",
  },
  sonic: {
    title: "Sonic",
    description: "Prepare bootable USB drives",
    icon: "usb",
    route: "/sonic",
    color: "var(--usx-color-success)",
  },
  developer: {
    title: "Engineering",
    description: "Developer tools",
    icon: "terminal",
    route: "/documentation?tab=developer",
    color: "var(--usx-color-primary)",
  },
  markdown: {
    title: "Editor",
    description: "Write and edit files",
    icon: "diamond",
    route: "/workflow?tab=editor",
    color: "var(--usx-color-primary)",
  },
  dreamscape: {
    title: "Daily rhythm",
    description: "Daily planning and reflection",
    icon: "psychology",
    route: "/workflow?tab=mission-control",
    color: "var(--usx-color-accent)",
  },
  google: {
    title: "Google Studio",
    description: "Google tools",
    icon: "cloud",
    route: "/google",
    color: "var(--usx-color-info)",
  },
  banana: {
    title: "Banana Studio",
    description: "Create images and graphics",
    icon: "image",
    route: "/banana",
    color: "var(--usx-color-warning)",
  },
  recipes: {
    title: "Surfaces & Recipes",
    description: "Interface examples",
    icon: "widgets",
    route: "/recipes",
    color: "var(--usx-color-primary)",
  },
  homenest: {
    title: "HomeNest",
    description: "Media and games",
    icon: "tv",
    route: "/homenest",
    color: "var(--usx-color-info)",
  },
  bitchat: {
    title: "BitChat",
    description: "Nearby messaging",
    icon: "forum",
    route: "/bitchat",
    color: "var(--usx-color-success)",
  },
};

const displaySettings = useSettingsStore();
const advancedSurfaceIds = new Set(["developer", "snackbar", "recipes", "google", "banana", "bitchat"]);
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
    // Chat is a global widget, not a dedicated navigable surface.
    if (surface.manifest.id === "intelligence") continue;
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
  for (const id of ["documentation", "workflow", "system", "browserui"]) {
    if (!seen.has(id) && SURFACE_CARD_DATA[id]) cards.push({ id, ...SURFACE_CARD_DATA[id] });
  }
  // Built-in first-class surfaces: guard against catalogue duplicates
  if (!seen.has("developer")) {
    cards.push({ id: "developer", ...SURFACE_CARD_DATA.developer });
  }

  if (!seen.has("google")) {
    cards.push({ id: "google", ...SURFACE_CARD_DATA.google });
  }
  if (!seen.has("banana")) {
    cards.push({ id: "banana", ...SURFACE_CARD_DATA.banana });
  }
  if (!seen.has("recipes")) {
    cards.push({ id: "recipes", ...SURFACE_CARD_DATA.recipes });
  }
  if (!seen.has("sonic")) {
    cards.push({ id: "sonic", ...SURFACE_CARD_DATA.sonic });
  }
  if (!seen.has("homenest")) {
    cards.push({ id: "homenest", ...SURFACE_CARD_DATA.homenest });
  }
  if (!seen.has("bitchat")) {
    cards.push({ id: "bitchat", ...SURFACE_CARD_DATA.bitchat });
  }
  // Always show Markdown Editor card
  cards.push({ id: "markdown", ...SURFACE_CARD_DATA.markdown });

  if (!seen.has("ucode")) cards.push({ id: "ucode", ...SURFACE_CARD_DATA.ucode });
  return cards.filter(card => displaySettings.advancedView || !advancedSurfaceIds.has(card.id));
});

// Active extensions to show as cards below the main surfaces
const activeExtensions = computed(() => {
  // Infrastructure stays in Server/Settings. Only launch distinct, running surfaces.
  return extStore.all
    .filter(
      (e) =>
        displaySettings.advancedView &&
        e.manifest.kind === "plugin" &&
        Boolean(e.manifest.route) &&
        !visibleSurfaces.value.some(
          (card) => card.route.split(/[?#]/)[0] === e.manifest.route?.split(/[?#]/)[0],
        ) &&
        e.status === "running",
    )
    .map((e) => ({
      id: e.manifest.id,
      title: e.manifest.name,
      description: e.manifest.description || "Installed extension",
      icon: e.manifest.icon || "extension",
      route: e.manifest.route!,
      color: "var(--usx-color-primary)",
      status: e.status as "running" | "stopped" | "error",
    }));
});

const syncState = ref<{
  ok?: boolean;
  timestamp?: string | null;
  apple_sync?: {
    reminders?: { available?: boolean; bidirectional?: boolean };
    notes?: { available?: boolean; bidirectional?: boolean };
    mail?: { available?: boolean; bidirectional?: boolean };
    messages?: { available?: boolean; bidirectional?: boolean };
  } | null;
  google_drive?: {
    configured?: boolean;
    vault_path?: string;
    vault_exists?: boolean;
    cloud_storage_detected?: boolean;
  } | null;
  bitchat_mesh?: {
    active?: boolean;
    local_peer_id?: string;
    online_peers?: number;
  } | null;
}>({
  ok: true,
  timestamp: null,
  apple_sync: null,
  google_drive: null,
  bitchat_mesh: null,
});

const connectionSetupNeeded = ref(false);
onMounted(async () => {
  try {
    const response = await fetch('/api/connections');
    if (response.ok) { const data=await response.json(); connectionSetupNeeded.value=!data.setup.completed; }
  } catch { /* Existing local workspace remains usable offline. */ }
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

/* ── Sync Card ───────────────────────────── */

.dashboard-sync-card {
  margin-bottom: var(--usx-spacing-xl);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.dashboard-sync-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-md);
  padding-bottom: var(--usx-spacing-xs);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-wrap: wrap;
}

.dashboard-sync-card__title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.dashboard-sync-card__title h3 {
  margin: 0;
  font-size: var(--usx-font-size-md);
  font-weight: 600;
  color: var(--usx-color-on-surface);
}

.dashboard-sync-card__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--usx-color-on-surface-muted);
  display: inline-block;
  transition: background-color 0.2s ease;
}

.dashboard-sync-card__dot--active {
  background: var(--usx-color-success);
  box-shadow: 0 0 6px var(--usx-color-success);
}

.dashboard-sync-card__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.dashboard-sync-card__time {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.dashboard-sync-card__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--usx-spacing-md);
}

.dashboard-sync-item {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
}

.dashboard-sync-item__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-primary);
  flex-shrink: 0;
}

.dashboard-sync-item__info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.dashboard-sync-item__label {
  font-size: var(--usx-font-size-xs);
  font-weight: 600;
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-sync-item__detail {
  font-size: 0.7rem;
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-spin {
  animation: dashboard-spin 1s linear infinite;
}

@keyframes dashboard-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

.dashboard-setup { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin:12px; padding:12px; border:1px solid var(--usx-color-border); border-radius:var(--usx-radius-sm); font-size:var(--usx-font-size-sm); }
.dashboard-setup .usx-btn { min-height:32px; margin:0; padding:4px 8px; }
</style>
