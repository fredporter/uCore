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

        <!-- Sovereign Ecosystem Sync Status Card -->
        <div class="dashboard-sync-card surface__panel">
          <div class="dashboard-sync-card__header">
            <div class="dashboard-sync-card__title">
              <span
                class="dashboard-sync-card__dot"
                :class="{ 'dashboard-sync-card__dot--active': syncState.ok }"
              />
              <h3>Sovereign Ecosystem Sync</h3>
            </div>
            <div class="dashboard-sync-card__actions">
              <span v-if="syncState.timestamp" class="dashboard-sync-card__time font-mono">
                {{ formatSyncTime(syncState.timestamp) }}
              </span>
              <button
                type="button"
                class="usx-btn usx-btn--sm usx-btn--secondary"
                :disabled="syncing"
                @click="fetchSyncStatus"
              >
                <UIcon :name="syncing ? 'sync' : 'refresh'" :class="{ 'dashboard-spin': syncing }" />
                <span>{{ syncing ? "Checking..." : "Check Status" }}</span>
              </button>
            </div>
          </div>

          <div class="dashboard-sync-card__grid">
            <!-- Apple PIM -->
            <div class="dashboard-sync-item">
              <div class="dashboard-sync-item__icon">
                <UIcon name="phone_iphone" />
              </div>
              <div class="dashboard-sync-item__info">
                <span class="dashboard-sync-item__label">Apple Ecosystem (PIM)</span>
                <span class="dashboard-sync-item__detail">
                  Reminders · Notes · Mail · Messages (JXA)
                </span>
              </div>
              <UBadge
                :type="syncState.apple_sync?.reminders?.available ? 'success' : 'neutral'"
                size="sm"
              >
                {{ syncState.apple_sync?.reminders?.available ? "Bridged" : "Standby" }}
              </UBadge>
            </div>

            <!-- BitChat Mesh -->
            <div class="dashboard-sync-item">
              <div class="dashboard-sync-item__icon">
                <UIcon name="hub" />
              </div>
              <div class="dashboard-sync-item__info">
                <span class="dashboard-sync-item__label">BitChat Mesh Transport</span>
                <span class="dashboard-sync-item__detail font-mono">
                  {{ syncState.bitchat_mesh?.local_peer_id || "LAN Mesh" }} · {{ syncState.bitchat_mesh?.online_peers || 0 }} peers
                </span>
              </div>
              <UBadge
                :type="syncState.bitchat_mesh?.active ? 'success' : 'neutral'"
                size="sm"
              >
                {{ syncState.bitchat_mesh?.active ? "Active" : "Offline" }}
              </UBadge>
            </div>

            <!-- Google Vault -->
            <div class="dashboard-sync-item">
              <div class="dashboard-sync-item__icon">
                <UIcon name="folder_shared" />
              </div>
              <div class="dashboard-sync-item__info">
                <span class="dashboard-sync-item__label">Sovereign Vault Storage</span>
                <span class="dashboard-sync-item__detail font-mono">
                  {{ syncState.google_drive?.vault_path || "~/Vault" }}
                </span>
              </div>
              <UBadge
                :type="syncState.google_drive?.vault_exists ? 'success' : 'neutral'"
                size="sm"
              >
                {{ syncState.google_drive?.vault_exists ? "Mounted" : "Missing" }}
              </UBadge>
            </div>
          </div>
        </div>

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
  { id: "snackbar", label: "Server", icon: "dns" },
  { id: "system", label: "System", icon: "settings" },
];

const activeHubTab = ref("dashboard");

const visibleHubTabs = computed(() => HUB_TABS);

watch(activeHubTab, (tabId) => {
  if (!tabId || tabId === "dashboard") return;
  const routes: Record<string, string> = {
    workflow: "/workflow?tab=mission-control",
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
    title: "Server",
    description: "Services, AI, Automation & Logs",
    icon: "dns",
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
    title: "Engineering",
    description: "External Antigravity IDE, agy CLI & Architecture",
    icon: "terminal",
    route: "/documentation?tab=developer",
    color: "var(--usx-color-primary)",
  },
  markdown: {
    title: "Editor",
    description: "WYSIWYG Prose and Code Editor",
    icon: "diamond",
    route: "/workflow?tab=editor",
    color: "var(--usx-color-primary)",
  },
  dreamscape: {
    title: "Dreamscape",
    description: "Dreambeans, Briefing & Scaffolding",
    icon: "psychology",
    route: "/dreamscape",
    color: "var(--usx-color-accent)",
  },
  google: {
    title: "Google Studio",
    description: "AI Studio, Drive Mirror & Gemini Sandbox",
    icon: "cloud",
    route: "/google",
    color: "var(--usx-color-info)",
  },
  banana: {
    title: "Banana Studio",
    description: "Visual Generation & Teletext Canvas",
    icon: "image",
    route: "/banana",
    color: "var(--usx-color-warning)",
  },
  recipes: {
    title: "Surfaces & Recipes",
    description: "USX & GridCore Design System Showcase",
    icon: "widgets",
    route: "/recipes",
    color: "var(--usx-color-primary)",
  },
  homenest: {
    title: "HomeNest",
    description: "Media & Living-Room Steam Console",
    icon: "tv",
    route: "/homenest",
    color: "var(--usx-color-info)",
  },
  bitchat: {
    title: "BitChat",
    description: "Decentralized Local Mesh Transport & Chat",
    icon: "forum",
    route: "/bitchat",
    color: "var(--usx-color-success)",
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
  // Built-in first-class surfaces: guard against catalogue duplicates
  if (!seen.has("developer")) {
    cards.push({ id: "developer", ...SURFACE_CARD_DATA.developer });
  }
  if (!seen.has("dreamscape")) {
    cards.push({ id: "dreamscape", ...SURFACE_CARD_DATA.dreamscape });
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

  return cards;
});

// Active extensions to show as cards below the main surfaces
const activeExtensions = computed(() => {
  // Infrastructure stays in Server/Settings. Only launch distinct, running surfaces.
  return extStore.all
    .filter(
      (e) =>
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

const syncing = ref(false);

async function fetchSyncStatus() {
  syncing.value = true;
  try {
    const res = await ucoreApi.host.syncStatus();
    if (res) {
      syncState.value = res;
    }
  } catch (err) {
    console.warn("Failed to fetch host sync status:", err);
  } finally {
    syncing.value = false;
  }
}

function formatSyncTime(ts: string | null | undefined): string {
  if (!ts) return "";
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

onMounted(() => {
  void extStore.fetchCatalogue();
  void fetchSyncStatus();
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

/* ── Sovereign Ecosystem Sync Card ───────────────────────────── */

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
</style>
