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
import { onMounted } from "vue";
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";

const srv = useSnackbarOpsStore();

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
</style>
