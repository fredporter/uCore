<template>
  <div class="workspace-filter">
    <label class="workspace-filter__label">Vault Layer</label>
    <select
      v-model="selectedWorkspace"
      class="workspace-filter__select"
      @change="onChange"
    >
      <option
        v-for="ws in vaultLayers"
        :key="ws.id"
        :value="ws.id"
        :disabled="ws.exists === false"
      >
        {{ ws.label
        }}{{ typeof ws.fileCount === "number" ? ` (${ws.fileCount})` : ""
        }}{{ ws.exists === false ? " (missing)" : "" }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
/**
 * @component WorkspaceFilter
 * @description Vault type selector filter for the filepicker.
 * Dynamically loads vault types (User, Shared, Public) from the
 * vault topology API. Shows file counts from library stats.
 * @category molecules
 * @emits {string} source-change - Selected vault type ID
 * @usage <WorkspaceFilter @source-change="onSourceChange" />
 */
import { ref, onMounted } from "vue";
import { ucoreApi } from "../../api/client";

interface VaultLayer {
  id: string;
  label: string;
  icon: string;
  description: string;
  exists?: boolean;
  fileCount?: number;
}

const selectedWorkspace = ref("");
const vaultLayers = ref<VaultLayer[]>([
  {
    id: "user",
    label: "User Vault",
    icon: "mdi:account",
    description: "~/Vault/",
  },
  {
    id: "shared",
    label: "Shared",
    icon: "mdi:account-group",
    description: "~/Shared/",
  },
  {
    id: "public",
    label: "Public",
    icon: "mdi:book-open-variant",
    description: "~/Public/",
  },
]);

const emit = defineEmits<{
  "source-change": [source: string];
}>();

function onChange() {
  emit("source-change", selectedWorkspace.value);
}

// Optionally fetch real stats to show file counts
onMounted(async () => {
  selectedWorkspace.value = "user";
  emit("source-change", selectedWorkspace.value);
  try {
    const [topologyRes, statsRes] = await Promise.all([
      ucoreApi.vault.topology(),
      ucoreApi.library.stats(),
    ]);

    const bySource = (statsRes.data as any)?.by_source as
      | Record<string, number>
      | undefined;
    const topologyLayers = ((topologyRes.data as any)?.layers || []) as Array<
      VaultLayer & { exists?: boolean }
    >;

    if (topologyRes.ok && topologyLayers.length > 0) {
      // Show all vault types from the topology API
      vaultLayers.value = topologyLayers
        .filter((layer) => ["user", "shared", "public"].includes(layer.id))
        .map((layer) => ({
          id: layer.id,
          label: layer.label,
          icon: layer.icon,
          description: layer.description,
          exists: layer.exists,
          fileCount: bySource?.[layer.id] || 0,
        }));
      return;
    }

    if (bySource) {
      vaultLayers.value = vaultLayers.value.map((layer) => ({
        ...layer,
        fileCount: bySource[layer.id] || 0,
      }));
    }
  } catch {
    // Silently fall back to static list
  }
});
</script>

<style scoped>
.workspace-filter {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.workspace-filter__label {
  margin: 0;
  font-size: var(--filepicker-filter-label-size, var(--usx-font-size-sm));
  font-weight: var(
    --filepicker-filter-label-weight,
    var(--usx-font-weight-semibold)
  );
  text-transform: var(--filepicker-filter-label-transform, none);
  color: var(--filepicker-filter-label-color, var(--usx-color-on-surface));
  letter-spacing: var(--filepicker-filter-label-spacing, 0.01em);
}

.workspace-filter__select {
  width: 100%;
  display: block;
  margin: 0;
  min-height: var(--filepicker-select-min-height, var(--usx-touch-min));
  height: var(--filepicker-select-height, var(--usx-touch-min));
  line-height: 1.2;
  padding: var(--filepicker-select-padding-y, var(--usx-spacing-sm))
    calc(
      var(--filepicker-select-padding-x, var(--usx-spacing-md)) +
        var(--usx-spacing-lg)
    )
    var(--filepicker-select-padding-y, var(--usx-spacing-sm))
    var(--filepicker-select-padding-x, var(--usx-spacing-md));
  background: var(--filepicker-select-bg, var(--usx-color-background));
  background-image:
    linear-gradient(45deg, transparent 50%, currentColor 50%),
    linear-gradient(135deg, currentColor 50%, transparent 50%);
  background-position:
    calc(100% - var(--usx-spacing-md)) calc(50% - 2px),
    calc(100% - var(--usx-spacing-sm)) calc(50% - 2px);
  background-size:
    6px 6px,
    6px 6px;
  background-repeat: no-repeat;
  border-radius: var(--filepicker-select-radius, var(--usx-radius-sm));
  font-size: var(--filepicker-select-font-size, var(--usx-font-size-sm));
  font-family: var(--usx-font-family-sans);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
  border: var(--filepicker-select-border-width, var(--usx-border-width-thick))
    solid
    var(
      --filepicker-select-border-color,
      color-mix(in srgb, var(--usx-color-primary) 15%, transparent)
    );
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  box-sizing: border-box;
}

.workspace-filter__select:focus {
  border-color: var(--usx-color-primary);
  outline: none;
}
</style>
