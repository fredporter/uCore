<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <div>
        <h3 class="surface__panel-title">MCP Servers &amp; Tools</h3>
        <p class="server-muted-text-sm">
          {{ mcpServers.length }} server{{
            mcpServers.length !== 1 ? "s" : ""
          }}, {{ visibleTools.length }} tool{{
            visibleTools.length !== 1 ? "s" : ""
          }}
        </p>
      </div>
      <UButton variant="secondary" size="sm" icon="refresh" @click="refresh">
        Refresh
      </UButton>
    </div>

    <!-- Servers status -->
    <h4 class="surface__panel-title server-subheading">Servers</h4>
    <div v-if="mcpServers.length === 0" class="server-muted-text">
      No MCP servers probed.
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
        <thead>
          <tr>
            <th>Server</th>
            <th>Status</th>
            <th>Port</th>
            <th>Tools</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="svr in mcpServers" :key="svr.name">
            <td>
              <span class="server-service-name-cell">
                <UIcon name="dns" />
                <span>{{ svr.name }}</span>
              </span>
            </td>
            <td>
              <UBadge
                :type="
                  svr.status === 'online'
                    ? 'success'
                    : svr.status === 'offline'
                      ? 'error'
                      : 'warning'
                "
                size="sm"
              >
                {{ svr.status }}
              </UBadge>
            </td>
            <td class="server-muted-text-sm">{{ svr.port || "N/A" }}</td>
            <td class="server-muted-text-sm">{{ svr.tools }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Tools list -->
    <div class="usx-mt-xl">
      <div class="usx-flex-between usx-mb-sm">
        <h4 class="surface__panel-title server-subheading">Tools</h4>
        <input
          v-model="toolFilter"
          type="search"
          placeholder="Filter tools..."
          class="usx-input skills-search-input"
        />
      </div>
      <div v-if="visibleTools.length === 0" class="server-muted-text">
        {{
          mcpTools.length === 0
            ? "No MCP tools discovered."
            : "No tools match your filter."
        }}
      </div>
      <div v-else class="server-table-wrap">
        <table class="server-table">
          <thead>
            <tr>
              <th>Tool</th>
              <th>Server</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tool in visibleTools" :key="tool.name">
              <td>
                <span class="server-service-name-cell">
                  <UIcon
                    :name="
                      tool.name.startsWith('ucore_skill_')
                        ? 'extension'
                        : tool.name.startsWith('ucore_clipboard')
                          ? 'content_paste'
                          : tool.name.startsWith('ucore_gridsmith')
                            ? 'grid_view'
                            : tool.name.startsWith('ucore_toon')
                              ? 'palette'
                              : 'build'
                    "
                  />
                  <span>{{ tool.name }}</span>
                </span>
              </td>
              <td>
                <UBadge type="info" size="sm">{{ tool.server }}</UBadge>
              </td>
              <td class="server-muted-text-sm">{{ tool.description }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";

const srv = useSnackbarOpsStore();
const toolFilter = ref("");

const visibleTools = computed(() => {
  const q = toolFilter.value.toLowerCase().trim();
  if (!q) return srv.mcpTools;
  return srv.mcpTools.filter(
    (t) =>
      t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.server.toLowerCase().includes(q),
  );
});

const mcpServers = computed(() => srv.mcpServers);
const mcpTools = computed(() => srv.mcpTools);

function refresh() {
  srv.fetchMCP();
}

onMounted(() => {
  if (srv.mcpTools.length === 0 && srv.mcpServers.length === 0) {
    srv.fetchMCP();
  }
});
</script>

<style scoped>
.server-muted-text,
.server-muted-text-sm {
  color: var(--usx-color-on-surface-muted);
}
.server-muted-text {
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-md);
}
.server-muted-text-sm {
  font-size: var(--usx-font-size-xs);
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
  border-bottom: 1px solid var(--usx-color-border);
  white-space: nowrap;
}
.server-table td {
  padding: var(--usx-spacing-sm);
  border-bottom: 1px solid var(--usx-color-border);
  vertical-align: middle;
}
.server-service-name-cell {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-weight: var(--usx-font-weight-medium);
}
.server-subheading {
  font-size: var(--usx-font-size-base);
  margin-bottom: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
}
.skills-search-input {
  width: 220px;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
}
</style>
