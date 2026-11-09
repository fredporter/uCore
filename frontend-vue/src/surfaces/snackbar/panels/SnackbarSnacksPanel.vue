<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <div>
        <h3 class="surface__panel-title">Snacks</h3>
        <p class="server-muted-text-sm">
          {{ snackExecutables.length }} snack{{
            snackExecutables.length !== 1 ? "s" : ""
          }}
          available.
        </p>
      </div>
      <UButton
        variant="secondary"
        size="sm"
        icon="refresh"
        @click="srv.fetchExecutables"
      >
        Refresh
      </UButton>
    </div>

    <div v-if="snackExecutables.length === 0" class="server-muted-text">
      No routines available.
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
        <thead>
          <tr>
            <th>Snack</th>
            <th>Category</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="exe in snackExecutables" :key="exe.id">
            <td>
              <span class="server-service-name-cell">
                <UIcon name="restaurant_menu" />
                <span>{{ exe.name }}</span>
              </span>
            </td>
            <td>
              <UBadge type="warning" size="sm">{{ exe.category }}</UBadge>
            </td>
            <td class="server-muted-text-sm">{{ exe.description }}</td>
            <td>
              <UButton
                variant="secondary"
                size="sm"
                icon="schedule"
                :disabled="!!runLoading"
                @click="runExe(exe)"
              >
                {{ runLoading === exe.id ? "Triggering..." : "Trigger Now" }}
              </UButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <details class="surface__panel" @toggle="loadMaintenance">
      <summary>Scheduled work</summary>
      <p v-if="maintenanceError" role="alert">{{ maintenanceError }}</p>
      <ul>
        <li v-for="job in maintenanceJobs" :key="job.skill_id">
          <strong>{{ job.skill_id.replaceAll('_', ' ') }}</strong> · {{ job.time }} ·
          {{ job.last_result?.state || (job.last_result ? (job.last_result.success ? 'Completed' : 'Failed') : 'Scheduled') }}
          <span v-if="job.last_success"> · Last success: {{ job.last_success }}</span>
          <span v-if="job.last_result?.next_retry"> · Retry: {{ job.last_result.next_retry }}</span>
          <p v-if="job.last_result?.error">{{ job.last_result.error }}</p>
          <p v-if="job.last_result?.state === 'needs_approval'">Review and run this action in Skills above.</p>
        </li>
      </ul>
    </details>

    <!-- Run result -->
    <div v-if="runResult !== null" class="skills-result-panel usx-mt-md">
      <div class="usx-flex-between usx-mb-sm">
        <h4 class="surface__panel-title">Result: {{ runSnackId }}</h4>
        <UButton variant="ghost" size="sm" @click="runResult = null"
          >Close</UButton
        >
      </div>
      <pre class="skills-result-code">{{ formattedResult }}</pre>
    </div>

    <!-- Error -->
    <div v-if="runError" class="skills-error usx-mt-md" role="alert">
      <UIcon name="error" /> {{ runError }}
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
const runLoading = ref<string | null>(null);
const runResult = ref<unknown>(null);
const runSnackId = ref("");
const runError = ref<string | null>(null);

interface MaintenanceJobStatus {
  skill_id: string;
  time: string;
  last_success?: string;
  last_result?: { success?: boolean; state?: string; error?: string; next_retry?: string };
}
const maintenanceJobs = ref<MaintenanceJobStatus[]>([]);
const maintenanceError = ref("");
async function loadMaintenance(event: Event) {
  if (!(event.target as HTMLDetailsElement).open) return;
  maintenanceError.value = "";
  try {
    const response = await fetch("/api/system/maintenance", { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error("Scheduled work is unavailable.");
    const data = await response.json();
    maintenanceJobs.value = data.jobs || [];
  } catch (error) {
    maintenanceError.value = error instanceof Error ? error.message : "Could not load scheduled work.";
  }
}

// Snacks = executables of kind "snack" — scheduler-loaded, autonomous.
const snackExecutables = computed(() =>
  srv.executables.filter((s) => s.kind === "snack"),
);

const formattedResult = computed(() => {
  if (runResult.value === null) return "";
  try {
    return JSON.stringify(runResult.value, null, 2);
  } catch {
    return String(runResult.value);
  }
});

async function runExe(exe: {
  id: string;
  name: string;
  requires_confirmation: boolean;
}) {
  if (runLoading.value) return;
  if (exe.requires_confirmation && !window.confirm(`Run ${exe.name}? This action may change files or system state.`)) return;
  runLoading.value = exe.id;
  runError.value = null;
  runSnackId.value = exe.name;
  try {
    const res = await fetch(`/api/executables/${exe.id}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(exe.requires_confirmation ? { "x-ucore-confirm": "true" } : {}) },
      body: JSON.stringify({}),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(
        `HTTP ${res.status}${text ? `: ${text.slice(0, 160)}` : ""}`,
      );
    }
    const data = await res.json();
    if (data.success === false) throw new Error(data.error || "Action failed");
    runResult.value = data;
  } catch (e: any) {
    runError.value = e?.message || String(e);
    runResult.value = null;
  } finally {
    runLoading.value = null;
  }
}

onMounted(() => {
  if (srv.executables.length === 0) srv.fetchExecutables();
});
</script>

<style scoped>
.server-muted-text {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-md);
}
.server-muted-text-sm {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
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
.skills-result-panel {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
}
.skills-result-code {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-mono);
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
}
.skills-error {
  color: var(--usx-color-danger);
  font-size: var(--usx-font-size-sm);
}
</style>
