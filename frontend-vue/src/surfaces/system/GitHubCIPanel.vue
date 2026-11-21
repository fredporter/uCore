<template>
  <section class="system-panel system-tab-shell ci-panel">
    <header class="ci-header">
      <h2>GitHub Actions</h2>
      <button type="button" class="usx-btn" :disabled="loading" @click="refreshStatus">
        <UIcon name="refresh" /> {{ loading ? "Refreshing…" : "Refresh status" }}
      </button>
    </header>

    <div class="ci-header">
      <label for="ci-repository">Repository</label>
      <select id="ci-repository" class="ci-repository-select" v-model="repo" @change="refreshStatus">
        <option v-for="entry in projectRepositories" :key="entry.id" :value="entry.id">
          {{ entry.label }}
        </option>
      </select>
    </div>

    <div class="ci-header">
      <label for="ci-branch-view">Branch view</label>
      <select id="ci-branch-view" class="ci-repository-select" v-model="branchView" @change="refreshStatus">
        <option value="default">Default branch</option>
        <option value="working">Working branch</option>
      </select>
    </div>

    <p v-if="loading" role="status">Checking GitHub Actions…</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <template v-if="snapshot">
      <p role="status">
        <span v-if="error">Showing saved results. </span>Last successful refresh
        <time :datetime="snapshot.refreshedAt.toISOString()">{{ snapshot.refreshedAt.toLocaleString() }}</time>
      </p>
      <p>Branch: <code>{{ snapshot.status.branch }}</code></p>
      <a v-if="actionsUrl" :href="actionsUrl" target="_blank" rel="noopener noreferrer">
        Open in GitHub Actions
      </a>
      <p v-if="snapshot.status.runs.length === 0">No runs returned for this branch.</p>
      <ul v-else>
        <li v-for="run in snapshot.status.runs" :key="run.databaseId" class="ci-run">
          <a v-if="githubUrl(run.url)" :href="githubUrl(run.url)" target="_blank" rel="noopener noreferrer">
            {{ run.workflowName }}
          </a>
          <span v-else>{{ run.workflowName }}</span>
          <span>{{ (run.conclusion || run.status).replaceAll("_", " ") }}</span>
        </li>
      </ul>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { UCORE_BASE } from "../../api/base";
import UIcon from "../../skills/atoms/UIcon.vue";

type GitHubErrorCode = "network" | "auth" | "timeout" | "cli_missing" | "branch_unavailable" | "unknown";

interface RepoStatus {
  configured: boolean;
  error_code?: GitHubErrorCode;
  branch: string;
  repository?: { url: string };
  runs_available?: boolean;
  runs: Array<{ databaseId: number; workflowName: string; status: string; conclusion: string; url: string }>;
}

const recoveryMessages: Record<GitHubErrorCode, string> = {
  network: "Could not reach GitHub. Check your internet connection or DNS, then refresh.",
  auth: "GitHub sign-in is required. Run gh auth status on the uCore host to check your session, then refresh.",
  timeout: "GitHub status took too long to load. Try refreshing again.",
  cli_missing: "GitHub CLI is unavailable on the uCore host. Install or restore gh, then refresh.",
  branch_unavailable: "This branch view is unavailable. Select the other view or check the repository branch, then refresh.",
  unknown: "GitHub workflow runs could not be loaded. Check the GitHub remote and CLI on the uCore host, then refresh.",
};

// IDs match physical workspace checkouts accepted by the developer API.
const projectRepositories = [
  { id: "uCore", label: "uCore" },
  { id: "uCode", label: "uCode" },
  { id: "uCodePlus", label: "uCode+ (uVector)" },
  { id: "SonicScrewdriver", label: "SonicScrewdriver" },
  { id: "global-knowledge", label: "Global Knowledge" },
  { id: "uCore-Publish", label: "uCore-Publish" },
  { id: "uCore-Google", label: "uCore-Google" },
  { id: "SnackMachine", label: "SnackMachine" },
  { id: "HomeNest", label: "HomeNest" },
  { id: "Groovebox", label: "Groovebox" },
];
const repo = ref("uCore");
const branchView = ref<"default" | "working">("default");
const selectionKey = computed(() => `${repo.value}:${branchView.value}`);
const snapshots = ref(new Map<string, { status: RepoStatus; refreshedAt: Date }>());
const snapshot = computed(() => snapshots.value.get(selectionKey.value));
const loading = ref(false);
const error = ref("");
let requestId = 0;
const actionsUrl = computed(() => {
  const url = githubUrl(snapshot.value?.status.repository?.url);
  return url ? url.replace(/\/$/, "") + "/actions" : "";
});

function githubUrl(value?: string) {
  if (!value) return "";
  try {
    const url = new URL(value);
    return url.origin === "https://github.com" ? url.href : "";
  } catch {
    return "";
  }
}

async function refreshStatus() {
  const id = ++requestId;
  const key = selectionKey.value;
  loading.value = true;
  error.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/developer/repos/${encodeURIComponent(repo.value)}/github?branch_view=${branchView.value}`);
    if (!response.ok) throw new Error("GitHub status unavailable");
    const data: RepoStatus = await response.json();
    if (id !== requestId) return;
    if (!data.configured || data.runs_available === false || !Array.isArray(data.runs)) {
      const saved = snapshots.value.get(key);
      if (saved && data.configured && data.branch && !["unknown", "HEAD"].includes(data.branch) &&
          data.branch !== saved.status.branch) {
        snapshots.value.delete(key);
      }
      const code = data.error_code;
      error.value = code && Object.hasOwn(recoveryMessages, code)
        ? recoveryMessages[code]
        : recoveryMessages.unknown;
    } else {
      snapshots.value.set(key, { status: data, refreshedAt: new Date() });
    }
  } catch {
    if (id === requestId) {
      error.value = "Could not load GitHub status. Check the local uCore service and try again.";
    }
  } finally {
    if (id === requestId) loading.value = false;
  }
}

onMounted(refreshStatus);
</script>

<style scoped>
.ci-panel { display: grid; gap: var(--usx-spacing-md); }
.ci-header, .ci-run {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--usx-spacing-sm);
}
.ci-header:first-child, .ci-run { justify-content: space-between; }
.ci-panel :is(h2, p, ul) { margin: 0; }
.ci-panel ul { padding: 0; list-style: none; }
.ci-panel .ci-repository-select:focus {
  outline: none;
  box-shadow: none;
  border-color: var(--usx-color-primary);
}
.ci-run {
  padding-block: var(--usx-spacing-sm);
  border-block-start: var(--usx-border-width) solid var(--usx-color-border);
}
</style>
