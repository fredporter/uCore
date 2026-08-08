/**
 * @module stores/extensions
 * @description Event-driven extension presence registry.
 * Extensions announce themselves via SSE (extension_online / extension_offline).
 * Required/core surfaces always appear; optional ones only when running.
 */
import { ref, computed } from "vue";
import { defineStore } from "pinia";

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
    required: false,
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
];

// ─── Store ───────────────────────────────────────────────────────

export const useExtensionStore = defineStore("extensions", () => {
  const entries = ref<Map<string, ExtensionEntry>>(new Map());

  // Initialise all known manifests as "unknown"
  for (const manifest of BUILTIN_MANIFESTS) {
    entries.value.set(manifest.id, {
      manifest,
      status: manifest.required ? "running" : "unknown",
    });
  }

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

  return {
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
  };
});
