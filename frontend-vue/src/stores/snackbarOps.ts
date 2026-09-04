/**
 * @module stores/snackbarOps
 * @description Snackbar (server operations) state — services, logs, budget, models, agents.
 * Wired to /api/server/* backend endpoints.
 */
import { defineStore } from "pinia";
import { ref } from "vue";
import { useSnackbarStore } from "./snackbar";

export type SnackbarOpsTab =
  | "dashboard"
  | "services"
  | "ai"
  | "automation"
  | "extensions"
  | "logs";

export interface RuntimeSnack {
  id: string;
  type: string;
  priority: string;
  status: string;
  source: string;
  timestamp: string;
}

export interface RuntimeSystemSnack {
  id: string;
  name: string;
  kind: string;
}

export interface ServiceStatus {
  name: string;
  status: "up" | "degraded" | "down";
  port: number;
  uptime: number;
  type: "system" | "user";
  description: string;
}

export interface UnifiedServiceInfo {
  id: string;
  name: string;
  kind: "service" | "tool";
  description: string;
  status: "up" | "degraded" | "down";
  port: number;
  type: string;
  actions: string[];
  meta: Record<string, unknown>;
}

export interface LogEntry {
  timestamp: string;
  service: string;
  level: "info" | "warn" | "error";
  message: string;
}

export interface ModelUsage {
  id: string;
  name: string;
  pct: number;
  calls: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  icon: string;
  active: boolean;
  description: string;
}

export interface ExecutableInfo {
  id: string;
  name: string;
  category: string;
  description: string;
  kind: "skill" | "snack";
  icon: string;
  enabled: boolean;
  requires_confirmation: boolean;
  actions: string[];
}

export interface BudgetInfo {
  remaining: number;
  used: number;
  limit: number;
  over_limit: boolean;
}

export interface HealthInfo {
  services: ServiceStatus[];
  count: number;
  up: number;
  degraded: number;
  down: number;
  health_pct: number;
}

export const SNACKBAR_OPS_TABS: {
  id: SnackbarOpsTab;
  label: string;
  icon: string;
}[] = [
  { id: "dashboard", label: "Overview", icon: "dashboard" },
  { id: "services", label: "Services", icon: "dns" },
  { id: "ai", label: "Models", icon: "smart_toy" },
  { id: "automation", label: "Automations", icon: "automation" },
  { id: "extensions", label: "Extensions", icon: "extension" },
  { id: "logs", label: "Logs", icon: "article" },
];

export const useSnackbarOpsStore = defineStore("snackbar-ops", () => {
  const activeTab = ref<SnackbarOpsTab>("dashboard");
  const services = ref<ServiceStatus[]>([]);
  const unifiedServices = ref<UnifiedServiceInfo[]>([]);
  const snacks = ref<RuntimeSnack[]>([]);
  const systemSnacks = ref<RuntimeSystemSnack[]>([]);
  const logs = ref<LogEntry[]>([]);
  const modelUsage = ref<ModelUsage[]>([]);
  const agents = ref<AgentInfo[]>([]);
  const executables = ref<ExecutableInfo[]>([]);
  const budgetRemaining = ref<number | null>(null);
  const budgetLimit = ref<number>(50.0);
  const budgetUsed = ref<number>(0.0);
  const budgetOverLimit = ref(false);
  const healthPct = ref(0);
  const upCount = ref(0);
  const degradedCount = ref(0);
  const downCount = ref(0);
  const loading = ref(false);
  const error = ref<string | null>(null);

  function setTab(tab: SnackbarOpsTab) {
    activeTab.value = tab;
  }

  async function fetchHealth(): Promise<void> {
    try {
      const res = await fetch("/api/server/health");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: HealthInfo = await res.json();
      services.value = data.services;
      upCount.value = data.up;
      degradedCount.value = data.degraded;
      downCount.value = data.down;
      healthPct.value = data.health_pct;
    } catch (e: any) {
      console.warn("Server health fetch failed:", e.message);
    }
  }

  // ── Health polling + crash alerts ──────────────────────────────
  // Tracks last-seen status per service to fire toasts on transitions.
  const lastHealthSnapshot = ref<Record<string, string>>({});
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  /** Fetch health, diff against the previous snapshot, and toast on changes. */
  async function pollHealthWithAlerts(): Promise<void> {
    try {
      const res = await fetch("/api/server/health");
      if (!res.ok) return;
      const data: HealthInfo = await res.json();
      const next: Record<string, string> = {};
      for (const s of data.services || []) {
        next[s.name] = s.status;
      }

      const toast = useSnackbarStore();
      const previous = lastHealthSnapshot.value;

      for (const name of Object.keys(next)) {
        const prev = previous[name];
        const cur = next[name];
        if (!prev) continue; // first poll — seed only, no alert
        if (prev === cur) continue;

        if (prev === "up" && (cur === "down" || cur === "degraded")) {
          toast.show(
            `Service "${name}" ${cur === "down" ? "went down" : "is degraded"}. Open S500 to recover.`,
            cur === "down" ? "error" : "warning",
            8000,
            "health",
          );
        } else if (cur === "up") {
          toast.show(`Service "${name}" recovered`, "success", 4000, "health");
        }
      }

      lastHealthSnapshot.value = next;
      services.value = data.services;
      upCount.value = data.up;
      degradedCount.value = data.degraded;
      downCount.value = data.down;
      healthPct.value = data.health_pct;
    } catch {
      // Backend unreachable — keep last snapshot, no false alerts.
    }
  }

  /** Start periodic health polling with crash/restore toasts. */
  function startHealthPolling(intervalMs = 15000): void {
    if (pollTimer) return;
    // Seed the snapshot without alerting, then begin polling.
    void (async () => {
      try {
        const res = await fetch("/api/server/health");
        if (res.ok) {
          const data: HealthInfo = await res.json();
          const seed: Record<string, string> = {};
          for (const s of data.services || []) seed[s.name] = s.status;
          lastHealthSnapshot.value = seed;
        }
      } catch {
        /* backend down */
      }
    })();
    pollTimer = setInterval(() => void pollHealthWithAlerts(), intervalMs);
  }

  /** Stop periodic health polling. */
  function stopHealthPolling(): void {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // ── Service recovery actions ───────────────────────────────────
  async function restartService(name: string): Promise<boolean> {
    try {
      const res = await fetch(
        `/api/server/services/${encodeURIComponent(name)}/restart`,
        { method: "POST" },
      );
      return res.ok;
    } catch {
      return false;
    }
  }

  async function repairService(name: string): Promise<boolean> {
    try {
      const res = await fetch(
        `/api/server/services/${encodeURIComponent(name)}/repair`,
        { method: "POST" },
      );
      return res.ok;
    } catch {
      return false;
    }
  }

  async function resetService(name: string): Promise<boolean> {
    try {
      const res = await fetch(
        `/api/server/services/${encodeURIComponent(name)}/reset`,
        { method: "POST" },
      );
      return res.ok;
    } catch {
      return false;
    }
  }

  async function fetchServices(): Promise<void> {
    try {
      const res = await fetch("/api/server/services");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      services.value = data.services || [];
    } catch (e: any) {
      console.warn("Server services fetch failed:", e.message);
    }
  }

  async function fetchUnifiedServices(): Promise<void> {
    try {
      const res = await fetch("/api/services");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      unifiedServices.value = (data.services || []).map((s: any) => ({
        id: s.id || s.name || "",
        name: s.name || "Unknown",
        kind: s.kind || "service",
        description: s.description || "",
        status: s.status || "down",
        port: s.port || 0,
        type: s.type || "system",
        actions: s.actions || [],
        meta: s.meta || {},
      }));
    } catch (e: any) {
      console.warn("Unified services fetch failed:", e.message);
    }
  }

  async function fetchLogs(limit = 20): Promise<void> {
    try {
      const res = await fetch(`/api/server/logs?limit=${limit}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      logs.value = data.logs || [];
    } catch (e: any) {
      console.warn("Server logs fetch failed:", e.message);
    }
  }

  async function fetchSnacks(): Promise<void> {
    try {
      const [queueRes, systemRes] = await Promise.all([
        fetch("/api/snacks"),
        fetch("/api/snacks/system"),
      ]);

      if (!queueRes.ok) throw new Error(`HTTP ${queueRes.status}`);
      const queueData = await queueRes.json();
      const rawQueue = queueData?.snacks || [];
      snacks.value = Array.isArray(rawQueue)
        ? rawQueue.map((snack: any, idx: number) => ({
            id: snack.id || `snack-${idx}`,
            type: snack.type || "message",
            priority: snack.priority || "normal",
            status: snack.status || "queued",
            source: snack.source || "system",
            timestamp: snack.timestamp || "",
          }))
        : [];

      if (systemRes.ok) {
        const systemData = await systemRes.json();
        const rawSystem = systemData?.snacks || [];
        systemSnacks.value = Array.isArray(rawSystem)
          ? rawSystem.map((snack: any) => ({
              id: snack.id || "",
              name: snack.name || snack.id || "System Snack",
              kind: snack.kind || "action",
            }))
          : [];
      }
    } catch (e: any) {
      console.warn("Server snacks fetch failed:", e.message);
      snacks.value = [];
      systemSnacks.value = [];
    }
  }

  async function fetchModels(): Promise<void> {
    try {
      const res = await fetch("/api/server/models");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      modelUsage.value = data.models || [];
    } catch (e: any) {
      console.warn("Server models fetch failed:", e.message);
    }
  }

  async function fetchAgents(): Promise<void> {
    try {
      const res = await fetch("/api/server/agents");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      agents.value = data.agents || [];
    } catch (e: any) {
      console.warn("Server agents fetch failed:", e.message);
    }
  }

  async function fetchBudget(): Promise<void> {
    try {
      const res = await fetch("/api/server/budget");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: BudgetInfo = await res.json();
      budgetRemaining.value = data.remaining;
      budgetUsed.value = data.used;
      budgetLimit.value = data.limit;
      budgetOverLimit.value = data.over_limit;
    } catch (e: any) {
      console.warn("Server budget fetch failed:", e.message);
    }
  }

  async function fetchExecutables(): Promise<void> {
    try {
      const res = await fetch("/api/executables");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const raw = Array.isArray(data?.executables) ? data.executables : [];
      executables.value = raw.map((s: any) => ({
        id: s.id || "",
        name: s.name || s.id || "Unknown",
        category: s.category || "general",
        description: s.description || "",
        kind: s.kind === "snack" ? "snack" : "skill",
        icon: s.icon || "extension",
        enabled: s.enabled !== false,
        requires_confirmation: Boolean(s.requires_confirmation),
        actions: Array.isArray(s.actions) ? s.actions : [],
      }));
    } catch (e: any) {
      console.warn("Executables fetch failed:", e.message);
    }
  }

  async function fetchAll(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      await Promise.all([
        fetchHealth(),
        fetchUnifiedServices(),
        fetchSnacks(),
        fetchExecutables(),
        fetchLogs(),
        fetchModels(),
        fetchAgents(),
        fetchBudget(),
      ]);
    } catch (e: any) {
      error.value = e.message || "Failed to load server data";
    } finally {
      loading.value = false;
    }
  }

  return {
    activeTab,
    services,
    unifiedServices,
    snacks,
    systemSnacks,
    executables,
    logs,
    modelUsage,
    agents,
    budgetRemaining,
    budgetLimit,
    budgetUsed,
    budgetOverLimit,
    healthPct,
    upCount,
    degradedCount,
    downCount,
    loading,
    error,
    setTab,
    fetchHealth,
    fetchServices,
    fetchUnifiedServices,
    fetchLogs,
    fetchSnacks,
    fetchExecutables,
    fetchModels,
    fetchAgents,
    fetchBudget,
    fetchAll,
    pollHealthWithAlerts,
    startHealthPolling,
    stopHealthPolling,
    restartService,
    repairService,
    resetService,
  };
});
