<template>
  <div class="services-panel-shell">
    <!-- Header -->
    <div class="recipe-header">
      <div class="header-left">
        <span class="material-symbols-outlined header-icon">dns</span>
        <div>
          <h2 class="recipe-title">Unified Services &amp; Tools</h2>
          <p class="recipe-desc">
            {{ srv.unifiedServices.length }} registered ({{ kindCount("service") }} services &middot; {{ kindCount("tool") }} tools &middot; {{ kindCount("mcp") }} MCP)
          </p>
        </div>
      </div>
      <div class="header-meta">
        <button class="usx-btn usx-btn--secondary m3-button" @click="handleRefresh">
          <UIcon name="refresh" />
          <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Crash recovery banner via USX Callout Caution -->
    <div v-if="downServices.length > 0" class="usx-callout usx-callout-caution">
      <div class="usx-callout-header">
        <span class="material-symbols-outlined">bug_report</span>
        <span>{{ downServices.length }} Service{{ downServices.length > 1 ? "s" : "" }} Not Responding</span>
      </div>
      <div class="crash-banner-content">
        <span>Restart managed runtimes below or open diagnostics for recovery guidance.</span>
        <button class="usx-btn usx-btn--danger m3-button m3-button-danger" @click="$router.push('/system/s500')">
          <UIcon name="medical_services" />
          <span>Open Crash Recovery</span>
        </button>
      </div>
    </div>

    <!-- Unified Services Table in USX Container Card -->
    <div class="table-container-card">
      <div v-if="srv.unifiedServices.length === 0" class="server-empty-state">
        <span class="material-symbols-outlined empty-icon">dns</span>
        <p>No services registered or discovered.</p>
      </div>
      <div v-else class="server-table-wrap">
        <table class="usx-table">
          <thead>
            <tr>
              <th>Service</th>
              <th>Kind</th>
              <th>Description</th>
              <th>Detail</th>
              <th>Status</th>
              <th v-if="downServices.length > 0">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="svc in srv.unifiedServices" :key="svc.id">
              <td>
                <span class="server-service-name-cell">
                  <span class="service-table-icon">
                    <span class="material-symbols-outlined">{{ serviceIcon(svc) }}</span>
                  </span>
                  <span class="service-name-text">{{ svc.name }}</span>
                </span>
              </td>
              <td>
                <span class="kind-pill" :class="`kind-pill--${svc.kind}`">{{ svc.kind }}</span>
              </td>
              <td class="server-desc-cell">{{ svc.description }}</td>
              <td class="server-mono-cell">{{ serviceDetail(svc) }}</td>
              <td>
                <span
                  class="status-pill"
                  :class="`status-pill--${svc.status}`"
                >
                  {{ svc.status }}
                </span>
              </td>
              <td v-if="downServices.length > 0">
                <div v-if="svc.status !== 'up' && svc.actions.includes('restart')" class="crash-inline-actions">
                  <button
                    class="usx-btn usx-btn--ghost crash-btn"
                    title="Restart service"
                    :disabled="actionLoading === svc.name"
                    @click="doRestart(svc.name)"
                  >
                    <UIcon name="restart_alt" />
                  </button>
                </div>
                <span v-else class="server-mono-cell">{{ svc.status === 'up' ? '—' : 'Manual recovery' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <RouterLink class="usx-btn" to="/system?tab=apps">Connected apps and sync</RouterLink>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import { useSnackbarStore } from "../../../stores/snackbar";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import {
  getHostCapabilities,
  intakeAppleNotes,
  intakeAppleReminders,
  sendHostNotification,
  sendHostSay,
  type HostCapabilitiesResult,
} from "../../browserui/ApiBridge";

const srv = useSnackbarOpsStore();
const toast = useSnackbarStore();

const actionLoading = ref<string | null>(null);

const downServices = computed(() =>
  srv.unifiedServices.filter((s) => s.status !== "up"),
);

async function doRestart(name: string) {
  actionLoading.value = name;
  const ok = await srv.restartService(name);
  toast.show(
    ok ? `Service "${name}" restarted` : `Failed to restart "${name}"`,
    ok ? "success" : "error",
    4000,
    "services",
  );
  actionLoading.value = null;
  srv.fetchUnifiedServices();
}

function kindCount(kind: string): number {
  return srv.unifiedServices.filter((s) => s.kind === kind).length;
}

function serviceIcon(svc: {
  kind: string;
  type: string;
  name: string;
}): string {
  if (svc.kind === "tool") {
    const map: Record<string, string> = {
      git: "code",
      docker: "deployed_code",
      node: "javascript",
      python: "terminal",
      ollama: "smart_toy",
      gh: "code",
    };
    return map[svc.name.toLowerCase()] || "build";
  }
  if (svc.kind === "mcp") return "dns";
  return svc.type === "system" ? "settings" : "dns";
}

function kindBadge(kind: string): "success" | "info" | "warning" {
  if (kind === "tool") return "success";
  if (kind === "mcp") return "warning";
  return "info";
}

function serviceDetail(svc: {
  kind: string;
  port: number;
  meta: Record<string, any>;
}): string {
  if (svc.kind === "tool") {
    const ver = svc.meta?.version || "";
    return ver ? `v${ver}` : "";
  }
  if (svc.kind === "mcp") {
    return svc.meta?.endpoint || "";
  }
  return svc.port ? `:${svc.port}` : "";
}

onMounted(() => {
  if (srv.agents.length === 0) {
    srv.fetchAgents();
  }
  if (srv.unifiedServices.length === 0) {
    srv.fetchUnifiedServices();
  }

});

const hostCaps = ref<HostCapabilitiesResult | null>(null);

async function loadHostCapabilities() {
  try {
    hostCaps.value = await getHostCapabilities();
  } catch (err) {
    console.debug("Failed to load host capabilities", err);
  }
}

function handleRefresh() {
  srv.fetchUnifiedServices();

}

async function testNotification() {
  actionLoading.value = "notify";
  try {
    const res = await sendHostNotification(
      "uCore Zen",
      "Host native notification operational.",
      "Snackbar",
    );
    toast.show(
      res.ok ? "Desktop notification sent!" : "Notification failed",
      res.ok ? "success" : "error",
      3000,
      "services",
    );
  } catch (err: any) {
    toast.show(`Notification error: ${err?.message || err}`, "error", 3000, "services");
  } finally {
    actionLoading.value = null;
  }
}

async function testSpeech() {
  actionLoading.value = "say";
  try {
    const res = await sendHostSay("uDOS host integration nominal.");
    toast.show(
      res.ok ? "Speech synthesis triggered!" : "Speech synthesis failed",
      res.ok ? "success" : "error",
      3000,
      "services",
    );
  } catch (err: any) {
    toast.show(`Speech error: ${err?.message || err}`, "error", 3000, "services");
  } finally {
    actionLoading.value = null;
  }
}

async function testFetchReminders() {
  actionLoading.value = "reminders";
  try {
    const res = await intakeAppleReminders({ limit: 10 });
    if (res.ok) {
      toast.show(
        `Retrieved ${res.items.length} active Apple Reminders`,
        "success",
        4000,
        "services",
      );
    } else {
      toast.show(res.error || "Reminders intake failed", "warning", 4000, "services");
    }
  } catch (err: any) {
    toast.show(`Reminders intake error: ${err?.message || err}`, "error", 4000, "services");
  } finally {
    actionLoading.value = null;
  }
}

async function testFetchNotes() {
  actionLoading.value = "notes";
  try {
    const res = await intakeAppleNotes({ limit: 10 });
    if (res.ok) {
      toast.show(
        `Retrieved ${res.items.length} Apple Notes`,
        "success",
        4000,
        "services",
      );
    } else {
      toast.show(res.error || "Notes intake failed", "warning", 4000, "services");
    }
  } catch (err: any) {
    toast.show(`Notes intake error: ${err?.message || err}`, "error", 4000, "services");
  } finally {
    actionLoading.value = null;
  }
}
</script>

<style scoped>

.services-panel-shell {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
}

/* ── Recipe Header ── */
.recipe-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent));
  flex-wrap: wrap;
  gap: 0.75rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-icon {
  font-size: 28px;
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.recipe-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.recipe-desc {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.header-meta,
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* ── M3 Button Pattern ── */
.m3-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 6px;
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 15%, transparent));
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 4%, transparent));
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
  cursor: pointer;
  transition: all 0.15s ease;
}

.m3-button:hover:not(:disabled) {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  border-color: var(--usx-color-outline, color-mix(in srgb, var(--usx-color-on-surface) 25%, transparent));
}

.m3-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.m3-button .material-symbols-outlined {
  font-size: 18px;
}

.m3-button-danger {
  background: color-mix(in srgb, var(--usx-color-danger) 15%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-danger) 35%, transparent);
  color: var(--usx-color-danger);
}

.m3-button-danger:hover:not(:disabled) {
  background: color-mix(in srgb, var(--usx-color-danger) 25%, transparent);
}

/* ── Callout Content ── */
.crash-banner-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 0.25rem;
}

/* ── Table Container Card ── */
.table-container-card {
  border-radius: 12px;
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  overflow: hidden;
}

.server-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.server-table-wrap {
  overflow-x: auto;
}

.usx-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.usx-table th {
  text-align: left;
  font-weight: 600;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 10%, transparent));
  background: var(--usx-color-surface, var(--usx-color-surface));
  white-space: nowrap;
}

.usx-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 5%, transparent));
  vertical-align: middle;
}

.usx-table tr:hover {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
}

.server-service-name-cell {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 500;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.service-table-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.service-table-icon .material-symbols-outlined {
  font-size: 16px;
}

.service-name-text {
  font-size: 0.88rem;
  font-weight: 600;
}

.server-desc-cell {
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  max-width: 320px;
}

.server-mono-cell {
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 0.78rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

/* ── Pills and Badges ── */
.kind-pill {
  font-size: 0.68rem;
  text-transform: uppercase;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  font-family: var(--usx-font-family-mono, monospace);
}

.kind-pill--service {
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  color: var(--usx-color-primary);
}

.kind-pill--tool {
  background: color-mix(in srgb, var(--usx-color-success) 12%, transparent);
  color: var(--usx-color-success);
}

.kind-pill--mcp {
  background: color-mix(in srgb, var(--usx-color-warning) 12%, transparent);
  color: var(--usx-color-warning);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  letter-spacing: 0.03em;
}

.status-pill--up {
  background: color-mix(in srgb, var(--usx-color-success) 15%, transparent);
  color: var(--usx-color-success);
}

.status-pill--degraded {
  background: color-mix(in srgb, var(--usx-color-warning) 15%, transparent);
  color: var(--usx-color-warning);
}

.status-pill--down {
  background: color-mix(in srgb, var(--usx-color-danger) 15%, transparent);
  color: var(--usx-color-danger);
}

.status-pill--neutral {
  background: color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
}

.crash-inline-actions {
  display: flex;
  gap: 0.35rem;
}

.crash-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 15%, transparent));
  border-radius: 6px;
  background: transparent;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  cursor: pointer;
  transition: all 0.15s ease;
}

.crash-btn:hover:not(:disabled) {
  color: var(--usx-color-danger);
  border-color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 12%, transparent);
}

.crash-btn .material-symbols-outlined {
  font-size: 16px;
}

/* ── Host-Native Integrations Section (USX Card Matrix) ── */
.host-integrations-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
  width: 100%;
}

.matrix-card {
  display: flex;
  flex-direction: column;
  padding: 1.15rem;
  border-radius: 12px;
  background: var(--usx-color-surface-container, color-mix(in srgb, var(--usx-color-on-surface) 3%, transparent));
  border: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 8%, transparent));
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

.matrix-card:hover {
  background: var(--usx-color-surface-container-high, color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent));
  border-color: var(--usx-color-outline, color-mix(in srgb, var(--usx-color-on-surface) 20%, transparent));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--usx-color-scrim) 25%, transparent);
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.icon-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--usx-color-primary, var(--usx-color-primary));
}

.icon-avatar .material-symbols-outlined {
  font-size: 20px;
}

.card-tag {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  background: color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent);
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  font-weight: 500;
}

.card-title {
  margin: 0 0 0.35rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, var(--usx-color-on-surface));
}

.card-description {
  margin: 0 0 0.85rem;
  font-size: 0.8rem;
  line-height: 1.4;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px solid var(--usx-color-outline-variant, color-mix(in srgb, var(--usx-color-on-surface) 6%, transparent));
}

.card-subtext {
  font-size: 0.72rem;
  color: var(--usx-color-on-surface-variant, var(--usx-color-on-surface-muted));
  font-family: var(--usx-font-family-mono, monospace);
}
</style>
