<template>
  <div>
    <div class="usx-flex-between usx-mb-md">
      <div>
        <h3 class="surface__panel-title">Skills</h3>
        <p class="server-muted-text-sm">
          {{ filteredExecutables.length }} skill{{
            filteredExecutables.length !== 1 ? "s" : ""
          }}
          &middot; on-demand &middot;
          <span v-if="filter !== ''"
            >filtered from {{ srv.executables.length }} total</span
          >
        </p>
      </div>
      <div class="usx-hstack usx-gap-sm">
        <input
          v-model="filter"
          type="search"
          placeholder="Filter skills..."
          class="usx-input skills-search-input"
        />
        <UButton
          variant="secondary"
          size="sm"
          icon="refresh"
          @click="srv.fetchExecutables"
        >
          Refresh
        </UButton>
      </div>
    </div>

    <div v-if="filteredExecutables.length === 0" class="server-muted-text">
      {{
        skills.length === 0
          ? "No skills discovered."
          : "No skills match your filter."
      }}
    </div>
    <div v-else class="server-table-wrap">
      <table class="server-table">
        <thead>
          <tr>
            <th>Executable</th>
            <th>Kind</th>
            <th>Category</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="exe in filteredExecutables" :key="exe.id">
            <td>
              <span class="server-service-name-cell">
                <UIcon :name="exeIcon(exe)" />
                <span>{{ exe.name }}</span>
              </span>
            </td>
            <td>
              <UBadge
                :type="exe.kind === 'snack' ? 'warning' : 'success'"
                size="sm"
              >
                {{ exe.kind }}
              </UBadge>
            </td>
            <td>
              <UBadge type="info" size="sm">{{ exe.category }}</UBadge>
            </td>
            <td class="server-muted-text-sm">{{ exe.description }}</td>
            <td>
              <div class="usx-hstack usx-gap-xs">
                <UButton
                  variant="secondary"
                  size="sm"
                  :disabled="runLoading === exe.id"
                  @click="runExe(exe)"
                >
                  {{ runLoading === exe.id ? "Running..." : "Run" }}
                </UButton>
                <UButton
                  v-if="exe.kind === 'skill'"
                  variant="ghost"
                  size="sm"
                  @click="toggleSource(exe.id)"
                >
                  {{ sourceOpen === exe.id ? "Hide" : "Source" }}
                </UButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Source view -->
    <div
      v-if="sourceOpen && sourceContent"
      class="skills-source-panel usx-mt-md"
    >
      <div class="usx-flex-between usx-mb-sm">
        <h4 class="surface__panel-title">Source: {{ sourceOpen }}</h4>
        <UButton variant="ghost" size="sm" @click="closeSource">Close</UButton>
      </div>
      <pre class="skills-source-code">{{ sourceContent }}</pre>
    </div>

    <!-- Run result -->
    <div v-if="runResult !== null" class="skills-result-panel usx-mt-md">
      <div class="usx-flex-between usx-mb-sm">
        <h4 class="surface__panel-title">Result: {{ runSkillId }}</h4>
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
const filter = ref("");
const sourceOpen = ref<string | null>(null);
const sourceContent = ref("");
const runLoading = ref<string | null>(null);
const runResult = ref<unknown>(null);
const runSkillId = ref("");
const runError = ref<string | null>(null);

// Skills = executables of kind "skill" — on-demand, may be composed into
// automations. (Snacks live under the Snacks tab for the scheduler.)
const skills = computed(() =>
  srv.executables.filter((s) => s.kind === "skill"),
);

const CATEGORY_ICONS: Record<string, string> = {
  orchestration: "account_tree",
  devtools: "code",
  maintenance: "build",
  knowledge: "psychology",
  clipboard: "content_paste",
  tasker: "assignment",
  vault: "inventory_2",
  spool: "archive",
  system: "settings",
  snacks: "restaurant_menu",
  general: "extension",
};

function exeIcon(exe: { kind: string; category: string }): string {
  if (exe.kind === "snack") return "restaurant_menu";
  return CATEGORY_ICONS[exe.category] || "extension";
}

const filteredExecutables = computed(() => {
  const q = filter.value.toLowerCase().trim();
  if (!q) return skills.value;
  return skills.value.filter(
    (s) =>
      s.name.toLowerCase().includes(q) ||
      s.id.toLowerCase().includes(q) ||
      s.category.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q) ||
      s.kind.toLowerCase().includes(q),
  );
});

const formattedResult = computed(() => {
  if (runResult.value === null) return "";
  try {
    return JSON.stringify(runResult.value, null, 2);
  } catch {
    return String(runResult.value);
  }
});

async function toggleSource(skillId: string) {
  if (sourceOpen.value === skillId) {
    sourceOpen.value = null;
    sourceContent.value = "";
    return;
  }
  sourceOpen.value = skillId;
  sourceContent.value = "Loading...";
  try {
    const res = await fetch(`/api/skills/${skillId}/source`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    sourceContent.value =
      typeof data?.source === "string"
        ? data.source
        : JSON.stringify(data, null, 2);
  } catch (e: any) {
    sourceContent.value = `Error: ${e.message}`;
  }
}

function closeSource() {
  sourceOpen.value = null;
  sourceContent.value = "";
}

async function runExe(exe: {
  id: string;
  kind: string;
  requires_confirmation: boolean;
  name: string;
}) {
  runLoading.value = exe.id;
  runError.value = null;
  runSkillId.value = exe.name;
  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (exe.requires_confirmation) {
      headers["x-ucore-confirm"] = "true";
    }
    const res = await fetch(`/api/executables/${exe.id}/run`, {
      method: "POST",
      headers,
      body: JSON.stringify({}),
    });
    const data = await res.json();
    runResult.value = data;
  } catch (e: any) {
    runError.value = e.message || "Failed to run executable";
    runResult.value = null;
  } finally {
    runLoading.value = null;
  }
}

onMounted(() => {
  if (srv.executables.length === 0) {
    srv.fetchExecutables();
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
.skills-search-input {
  width: 220px;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
}
.skills-source-panel,
.skills-result-panel {
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
}
.skills-source-code,
.skills-result-code {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  color: var(--usx-color-on-surface);
  max-height: 400px;
  overflow-y: auto;
}
.skills-error {
  color: var(--usx-color-danger);
  font-size: var(--usx-font-size-sm);
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}
</style>
