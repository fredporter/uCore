<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <div>
        <h3 class="surface__panel-title">Services</h3>
        <p class="server-muted-text-sm">
          {{ srv.unifiedServices.length }} total ({{
            kindCount("service")
          }}
          services &middot; {{ kindCount("tool") }} tools &middot;
          {{ kindCount("mcp") }} MCP)
        </p>
      </div>
      <UButton
        variant="secondary"
        size="sm"
        icon="refresh"
        @click="srv.fetchUnifiedServices"
        >Refresh</UButton
      >
    </div>

    <!-- Crash recovery banner -->
    <div v-if="downServices.length > 0" class="crash-banner">
      <UIcon name="bug_report" class="crash-banner-icon" />
      <div class="crash-banner-text">
        <strong
          >{{ downServices.length }} service{{
            downServices.length > 1 ? "s" : ""
          }}
          not responding.</strong
        >
        <span>Restart, repair, or revert to a working release.</span>
      </div>
      <UButton
        variant="secondary"
        size="sm"
        icon="medical_services"
        class="crash-banner-btn"
        @click="$router.push('/system/s500')"
      >
        Open Crash Recovery
      </UButton>
    </div>

    <div v-if="srv.unifiedServices.length === 0" class="server-muted-text-sm">
      No services available.
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
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
                <UIcon :name="serviceIcon(svc)" />
                <span>{{ svc.name }}</span>
              </span>
            </td>
            <td>
              <UBadge :type="kindBadge(svc.kind)" size="sm">{{
                svc.kind
              }}</UBadge>
            </td>
            <td class="server-muted-text-sm">{{ svc.description }}</td>
            <td class="server-muted-text-sm">{{ serviceDetail(svc) }}</td>
            <td>
              <UBadge
                :type="
                  svc.status === 'up'
                    ? 'success'
                    : svc.status === 'degraded'
                      ? 'warning'
                      : 'error'
                "
                size="sm"
              >
                {{ svc.status }}
              </UBadge>
            </td>
            <td v-if="downServices.length > 0">
              <div v-if="svc.status !== 'up'" class="crash-inline-actions">
                <button
                  class="crash-btn"
                  title="Restart service"
                  :disabled="actionLoading === svc.name"
                  @click="doRestart(svc.name)"
                >
                  <UIcon name="restart_alt" />
                </button>
                <button
                  class="crash-btn"
                  title="Repair service"
                  :disabled="actionLoading === svc.name"
                  @click="doRepair(svc.name)"
                >
                  <UIcon name="build" />
                </button>
                <button
                  class="crash-btn crash-btn--danger"
                  :title="
                    destroyConfirm === svc.name
                      ? 'Confirm destroy'
                      : 'Destroy (revert to release)'
                  "
                  :disabled="actionLoading === svc.name"
                  @click="doDestroy(svc.name)"
                >
                  <UIcon
                    :name="
                      destroyConfirm === svc.name ? 'warning' : 'delete_forever'
                    "
                  />
                </button>
              </div>
              <span v-else class="server-muted-text-sm">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Agents subsection -->
    <div class="usx-mt-xl">
      <div class="usx-flex-between usx-mb-sm">
        <h4 class="surface__panel-title server-subheading">Agents</h4>
        <UButton
          variant="secondary"
          size="sm"
          icon="refresh"
          @click="srv.fetchAgents"
          >Refresh</UButton
        >
      </div>
      <div v-if="srv.agents.length === 0" class="server-muted-text-sm">
        No agents available.
      </div>
      <div v-else class="server-table-wrap">
        <table class="server-table">
          <thead>
            <tr>
              <th>Agent</th>
              <th>Description</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in srv.agents" :key="agent.id">
              <td>
                <span class="server-service-name-cell">
                  <UIcon :name="agent.icon || 'smart_toy'" />
                  <span>{{ agent.name }}</span>
                </span>
              </td>
              <td class="server-muted-text-sm">{{ agent.description }}</td>
              <td>
                <UBadge :type="agent.active ? 'success' : 'info'" size="sm">
                  {{ agent.active ? "running" : "idle" }}
                </UBadge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import { useSnackbarStore } from "../../../stores/snackbar";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";

const srv = useSnackbarOpsStore();
const toast = useSnackbarStore();

const actionLoading = ref<string | null>(null);
const destroyConfirm = ref<string | null>(null);

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

async function doRepair(name: string) {
  actionLoading.value = name;
  const ok = await srv.repairService(name);
  toast.show(
    ok ? `Service "${name}" repair initiated` : `Repair failed for "${name}"`,
    ok ? "info" : "error",
    4000,
    "services",
  );
  actionLoading.value = null;
  srv.fetchUnifiedServices();
}

function doDestroy(name: string) {
  if (destroyConfirm.value === name) {
    destroyConfirm.value = null;
    void destroyService(name);
  } else {
    destroyConfirm.value = name;
    setTimeout(() => {
      if (destroyConfirm.value === name) destroyConfirm.value = null;
    }, 5000);
  }
}

async function destroyService(name: string) {
  actionLoading.value = name;
  const ok = await srv.resetService(name);
  toast.show(
    ok
      ? `Service "${name}" reverted to working release`
      : `Destroy failed for "${name}"`,
    ok ? "warning" : "error",
    5000,
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
      vscode: "code_blocks",
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
</script>

<style scoped>
.server-muted-text-sm {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}
.server-table-wrap {
  overflow-x: auto;
}
.server-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-sm);
}
.server-table th {
  text-align: left;
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  white-space: nowrap;
}
.server-table td {
  padding: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  vertical-align: middle;
}
.server-service-name-cell {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  min-width: 0;
  overflow-wrap: anywhere;
}
.server-subheading {
  font-size: var(--usx-font-size-base);
  margin-bottom: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
}

/* ─── Crash recovery banner ──────────────────────────────────── */
.crash-banner {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid
    color-mix(in srgb, var(--usx-color-danger) 40%, transparent);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
  margin-bottom: var(--usx-spacing-md);
}

.crash-banner-icon {
  color: var(--usx-color-danger);
  font-size: var(--usx-font-size-xl);
  flex-shrink: 0;
}

.crash-banner-text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-base);
}

.crash-banner-text span {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

/* ─── Inline per-service actions ─────────────────────────────── */
.crash-inline-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.crash-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-spacing-xl);
  height: var(--usx-spacing-xl);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  transition:
    color var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.crash-btn:hover:not(:disabled) {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.crash-btn--danger:hover:not(:disabled) {
  color: var(--usx-color-danger);
  border-color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
}

.crash-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.crash-banner-btn {
  flex-shrink: 0;
}
</style>
