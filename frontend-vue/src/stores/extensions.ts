/**
 * @module stores/extensions
 * @description Event-driven extension presence registry.
 * Extensions announce themselves via SSE (extension_online / extension_offline).
 * Required/core surfaces always appear; optional ones only when running.
 *
 * Also provides API actions for the Snackbar extensions tab:
 * fetchCatalogue, toggleExtension, installExtension, repairExtension.
 */
import { ref, computed } from "vue";
import { defineStore } from "pinia";
import { SNACKBAR_BASE } from "@/api/base";

export type ExtensionKind = "core" | "surface" | "service" | "plugin";
export type ExtensionStatus = "unknown" | "available" | "installed" | "running";

export interface ExtensionManifest {
  id: string;
  name: string;
  kind: ExtensionKind;
  required: boolean; // core surfaces always shown
  route?: string;
  icon: string;
  description?: string;
  status_endpoint?: string;
  install_url?: string;
  activation_required: boolean;
  version?: string;
}

interface ExtensionEntry {
  manifest: ExtensionManifest;
  status: ExtensionStatus;
  lastSeen?: number; // epoch ms
}

// ─── Built-in manifest registry ─────────────────────────────────

const BUILTIN_MANIFESTS: ExtensionManifest[] = [
  // Core surfaces — always visible
  {
    id: "dashboard",
    name: "Dashboard",
    kind: "core",
    required: true,
    icon: "home",
    route: "/",
    activation_required: false,
  },
  {
    id: "workflow",
    name: "Workflow",
    kind: "core",
    required: true,
    icon: "flag",
    route: "/workflow",
    activation_required: false,
  },
  {
    id: "intelligence",
    name: "Intelligence",
    kind: "core",
    required: true,
    icon: "lightbulb",
    route: "/intelligence",
    activation_required: false,
  },
  {
    id: "system",
    name: "System",
    kind: "core",
    required: true,
    icon: "settings",
    route: "/system",
    activation_required: false,
  },
  {
    id: "snackbar",
    name: "Snackbar",
    kind: "core",
    required: true,
    icon: "storefront",
    route: "/snackbar",
    activation_required: false,
  },
  // Optional surfaces — supply on demand
  {
    id: "browserui",
    name: "Browser",
    kind: "surface",
    required: false,
    icon: "language",
    route: "/browserui",
    activation_required: false,
    description: "Web research and bookmark stacks",
  },
  {
    id: "ucode",
    name: "uCode",
    kind: "surface",
    required: false,
    icon: "grid_on",
    route: "/ucode",
    activation_required: false,
    description: "Grid engine, Teletext, terminal",
  },
  {
    id: "groovebox",
    name: "Groovebox",
    kind: "surface",
    required: false,
    icon: "music_note",
    route: "/groovebox",
    activation_required: false,
    description: "Music and audio tools",
  },
  {
    id: "sonic",
    name: "Sonic Screwdriver",
    kind: "surface",
    required: false,
    icon: "build_circle",
    route: "/sonic",
    activation_required: false,
    description: "System diagnostics and repair",
  },
  {
    id: "documentation",
    name: "Documentation",
    kind: "surface",
    required: true,
    icon: "menu_book",
    route: "/documentation",
    activation_required: false,
    description: "Built-in documentation viewer",
  },
  // Extensions that require installation + activation
  {
    id: "udev",
    name: "Developer",
    kind: "surface",
    required: false,
    icon: "code",
    route: "/developer",
    activation_required: true,
    description: "Full developer lane — requires uDev",
    install_url: "https://github.com/fredporter/uDev",
  },
  {
    id: "snack-shack",
    name: "Snack Shack",
    kind: "plugin",
    required: false,
    icon: "storefront",
    route: "/snackbar?tab=snacks",
    activation_required: false,
    description: "Browse and install AI model packages",
  },
  {
    id: "plugin-store",
    name: "Plugin Store",
    kind: "plugin",
    required: false,
    icon: "extension",
    route: "/intelligence?tab=plugins",
    activation_required: false,
    description: "Discover and install uDOS extensions",
    install_url: "#",
  },
  // External udos-* extension manifest entries
  {
    id: "udos-budget",
    name: "uDos Budget",
    kind: "plugin",
    required: false,
    icon: "savings",
    activation_required: false,
    description: "Budget policy & status plugin",
  },
  {
    id: "udos-identity",
    name: "uDos Identity",
    kind: "plugin",
    required: false,
    icon: "fingerprint",
    activation_required: false,
    description: "Identity profile & session plugin",
  },
  {
    id: "udos-google",
    name: "Google Bridge",
    kind: "plugin",
    required: false,
    icon: "cloud",
    activation_required: false,
    description: "Google OAuth, Gemini/Gems, Drive mirror",
  },
  {
    id: "udos-dreamscape",
    name: "Dreamscape",
    kind: "plugin",
    required: false,
    icon: "psychology",
    activation_required: false,
    description: "Mission scaffolding & daily briefing",
  },
  {
    id: "udos-publishing",
    name: "Publishing",
    kind: "plugin",
    required: false,
    icon: "publish",
    activation_required: false,
    description: "Cloud mirror for udo.guide/udo.place",
  },
  {
    id: "udos-vaults",
    name: "Vault Topology",
    kind: "plugin",
    required: false,
    icon: "folder_special",
    activation_required: false,
    description: "Vault topology & AppFlowy bridge",
  },
  {
    id: "udos-agents",
    name: "uDos Agents",
    kind: "plugin",
    required: false,
    icon: "smart_toy",
    activation_required: false,
    description: "Specialized agent scaffolding",
  },
  {
    id: "homenest",
    name: "HomeNest",
    kind: "plugin",
    required: false,
    icon: "home",
    activation_required: false,
    description: "Home stream server — Jellyfin + Home Assistant bridge",
  },
];

// ─── Store ───────────────────────────────────────────────────────

export const useExtensionStore = defineStore("extensions", () => {
  const localEnabled = ref<Record<string, boolean>>({});
  const entries = ref<Map<string, ExtensionEntry>>(new Map());

  // Initialise all known manifests as "unknown"
  for (const manifest of BUILTIN_MANIFESTS) {
    entries.value.set(manifest.id, {
      manifest,
      status: manifest.required ? "running" : "unknown",
    });
  }

  function applyLocalEnabledOverrides() {
    for (const [id, enabled] of Object.entries(localEnabled.value || {})) {
      const entry = entries.value.get(id);
      if (!entry || entry.manifest.required) continue;
      entry.status = enabled ? "running" : "installed";
    }
  }

  applyLocalEnabledOverrides();

  // ─── Computed ───────────────────────────────────────────────

  const all = computed(() => [...entries.value.values()]);

  const running = computed(() =>
    all.value.filter((e) => e.status === "running"),
  );

  /** Surfaces to show in Dashboard + nav: required OR running */
  const visibleSurfaces = computed(() =>
    all.value
      .filter(
        (e) => e.manifest.kind === "surface" || e.manifest.kind === "core",
      )
      .filter((e) => e.manifest.required || e.status === "running"),
  );

  /** All known extensions for the plugin catalogue */
  const catalogue = computed(() =>
    all.value.filter((e) => !e.manifest.required),
  );

  const isRunning = (id: string) => entries.value.get(id)?.status === "running";

  const getStatus = (id: string): ExtensionStatus =>
    entries.value.get(id)?.status ?? "unknown";

  // ─── Mutations ───────────────────────────────────────────────

  function markRunning(id: string, version?: string) {
    const entry = entries.value.get(id);
    if (entry) {
      entry.status = "running";
      entry.lastSeen = Date.now();
      if (version) entry.manifest.version = version;
    } else {
      // Unknown extension announcing itself — register dynamically
      entries.value.set(id, {
        manifest: {
          id,
          name: id,
          kind: "plugin",
          required: false,
          icon: "extension",
          activation_required: false,
        },
        status: "running",
        lastSeen: Date.now(),
      });
    }
  }

  function markOffline(id: string) {
    const entry = entries.value.get(id);
    if (entry && !entry.manifest.required) {
      entry.status = "installed"; // was running, now stopped
    }
  }

  function markInstalled(id: string) {
    const entry = entries.value.get(id);
    if (entry) entry.status = "installed";
  }

  /** Prune entries not seen in last 60s (stale running) */
  function pruneStale() {
    const cutoff = Date.now() - 60_000;
    for (const [id, entry] of entries.value) {
      if (
        entry.status === "running" &&
        entry.lastSeen &&
        entry.lastSeen < cutoff &&
        !entry.manifest.required
      ) {
        entry.status = "installed";
      }
    }
  }

  // ─── API-driven catalogue & actions (Snackbar Extensions tab) ──

  /** Runtime catalogue enriched with backend probe data */
  const runtimeCatalogue = ref<any[]>([]);
  /** Loading states per action */
  const loading = ref<Record<string, string>>({}); // id -> action
  const actionMessage = ref<string>("");

  async function fetchCatalogue() {
    try {
      const res = await fetch(`${SNACKBAR_BASE}/api/extensions/catalogue`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) return;
      const data = await res.json();
      runtimeCatalogue.value = data.extensions ?? [];

      // Sync status back into known entries
      for (const ext of runtimeCatalogue.value) {
        if (typeof ext?.id === "string") {
          localEnabled.value = {
            ...localEnabled.value,
            [ext.id]: Boolean(ext.enabled),
          };
        }

        const existing = entries.value.get(ext.id);
        if (existing) {
          if (ext.status === "running" || ext.enabled) {
            existing.status = "running";
          } else if (ext.is_installed) {
            existing.status = "installed";
          } else {
            existing.status = "available";
          }
          if (ext.version) existing.manifest.version = ext.version;
        }
      }

      applyLocalEnabledOverrides();
    } catch {
      // Backend unreachable — stick with built-in status
      applyLocalEnabledOverrides();
    }
  }

  async function toggleExtension(id: string, enabled: boolean) {
    loading.value = { ...loading.value, [id]: "toggling" };

    localEnabled.value = {
      ...localEnabled.value,
      [id]: enabled,
    };

    // Optimistic update — set local status immediately
    const existing = entries.value.get(id);
    if (existing) {
      existing.status = enabled ? "running" : "installed";
    }

    try {
      const res = await fetch(`${SNACKBAR_BASE}/api/extensions/${id}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled }),
        signal: AbortSignal.timeout(5000),
      });
      const data = await res.json();
      actionMessage.value = data.message ?? "";
    } catch {
      // Backend unreachable — optimistic state is already set
      actionMessage.value = "";
    } finally {
      loading.value = { ...loading.value, [id]: "" };
    }
  }

  async function installExtension(id: string) {
    loading.value = { ...loading.value, [id]: "installing" };
    try {
      const res = await fetch(`${SNACKBAR_BASE}/api/extensions/${id}/install`, {
        method: "POST",
        signal: AbortSignal.timeout(120_000), // 2min timeout for clone+install
      });
      const data = await res.json();
      actionMessage.value = data.message ?? "";
      if (data.success) {
        const existing = entries.value.get(id);
        if (existing) {
          existing.status = "running";
        }
      }
    } catch (e: any) {
      actionMessage.value = `Install failed: ${e.message}`;
    } finally {
      loading.value = { ...loading.value, [id]: "" };
      // Refresh catalogue after install
      await fetchCatalogue();
    }
  }

  async function repairExtension(id: string) {
    loading.value = { ...loading.value, [id]: "repairing" };
    try {
      const res = await fetch(`${SNACKBAR_BASE}/api/extensions/${id}/repair`, {
        method: "POST",
        signal: AbortSignal.timeout(120_000),
      });
      const data = await res.json();
      actionMessage.value = data.message ?? "";
      if (data.success) {
        const existing = entries.value.get(id);
        if (existing) {
          existing.status = "running";
        }
      }
    } catch (e: any) {
      actionMessage.value = `Repair failed: ${e.message}`;
    } finally {
      loading.value = { ...loading.value, [id]: "" };
      await fetchCatalogue();
    }
  }

  return {
    localEnabled,
    entries,
    all,
    running,
    visibleSurfaces,
    catalogue,
    isRunning,
    getStatus,
    markRunning,
    markOffline,
    markInstalled,
    pruneStale,
    // API-driven
    runtimeCatalogue,
    loading,
    actionMessage,
    fetchCatalogue,
    toggleExtension,
    installExtension,
    repairExtension,
  };
}, {
  persist: {
    key: "ucore.extensions",
    paths: ["localEnabled"],
  },
});
