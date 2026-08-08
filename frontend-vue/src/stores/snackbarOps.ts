/**
 * @module stores/snackbarOps
 * @description Snackbar (server operations) state — services, logs, budget, models, agents.
 * Wired to /api/server/* backend endpoints.
 */
import { defineStore } from "pinia";
import { ref } from "vue";

export type SnackbarOpsTab =
  | "dashboard"
  | "services"
  | "snacks"
  | "logs"
  | "plugins";

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
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "services", label: "Services", icon: "dns" },
  { id: "snacks", label: "Snacks", icon: "restaurant_menu" },
  { id: "logs", label: "Logs", icon: "article" },
  { id: "plugins", label: "Plugins", icon: "extension" },
];

export const useSnackbarOpsStore = defineStore("snackbar-ops", () => {
  const activeTab = ref<SnackbarOpsTab>("dashboard");
  const services = ref<ServiceStatus[]>([]);
  const snacks = ref<RuntimeSnack[]>([]);
  const systemSnacks = ref<RuntimeSystemSnack[]>([]);
  const logs = ref<LogEntry[]>([]);
  const modelUsage = ref<ModelUsage[]>([]);
  const agents = ref<AgentInfo[]>([]);
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

  async function fetchAll(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      await Promise.all([
        fetchHealth(),
        fetchSnacks(),
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
    snacks,
    systemSnacks,
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
    fetchLogs,
    fetchSnacks,
    fetchModels,
    fetchAgents,
    fetchBudget,
    fetchAll,
  };
});
