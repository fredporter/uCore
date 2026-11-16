<template>
  <section class="routines" aria-label="Routines">
    <header>
      <div>
        <h2>Routines</h2>
        <p v-if="scheduler">Maintenance scheduler {{ scheduler }}</p>
      </div>
      <button class="usx-btn" type="button" :disabled="loading" @click="load">
        <UIcon name="refresh" aria-hidden="true" /> Refresh
      </button>
    </header>
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-else-if="loading && !jobs.length" role="status">Loading routines…</p>
    <p v-else-if="!jobs.length">No maintenance routines configured.</p>
    <ul v-else class="routine-list">
      <li v-for="job in jobs" :key="job.skill_id">
        <strong>{{ job.skill_id.replaceAll('_', ' ') }}</strong>
        <span>{{ job.time }} daily · {{ job.last_result?.state.replaceAll('_', ' ') || 'Awaiting first run' }}</span>
        <small v-if="job.last_result?.timestamp">Last attempt {{ formatTime(job.last_result.timestamp) }}</small>
        <small v-if="job.last_result?.next_retry">Next retry {{ formatTime(job.last_result.next_retry) }}</small>
        <small v-if="job.last_result?.state === 'needs_approval'">A local administrator can approve this run.</small>
        <small v-else-if="job.last_result?.error" class="routine-error">{{ job.last_result.error }}</small>
        <button v-if="['needs_approval', 'failed'].includes(job.last_result?.state || '')"
          type="button" class="usx-btn routine-run" :disabled="!!runningJob"
          @click="runRoutine(job)">
          <UIcon name="play_arrow" aria-hidden="true" />
          {{ runningJob === job.skill_id ? 'Running…' : job.last_result?.state === 'needs_approval' ? 'Approve & run once' : 'Retry once' }}
        </button>
      </li>
    </ul>
    <p v-if="runNotice" :role="runFailed ? 'alert' : 'status'">{{ runNotice }}</p>
    <section class="intake-check" aria-label="Binder intake check">
      <h3>Binder intake check</h3>
      <form @submit.prevent="checkBinder">
        <label>Binder
          <select v-model="binderId" :disabled="checking" @change="report = null; checkError = ''">
            <option value="" disabled>Choose a Binder</option>
            <option v-for="binder in wf.binders" :key="binder.id" :value="binder.id">
              {{ binder.title || binder.id }}
            </option>
          </select>
        </label>
        <button class="usx-btn" type="submit" :disabled="checking || !binderId">
          <UIcon name="fact_check" aria-hidden="true" /> Check provenance
        </button>
      </form>
      <p v-if="checkError" role="alert">{{ checkError }}</p>
      <p v-if="report" role="status">
        {{ report.filter(row => row.status === 'complete').length }} complete ·
        {{ report.filter(row => row.status === 'invalid').length }} need attention ·
        {{ report.filter(row => row.status === 'untracked').length }} without intake metadata
      </p>
      <ul v-if="report?.length" class="routine-list">
        <li v-for="row in report" :key="row.filename">
          <strong>{{ row.filename }}</strong>
          <small>{{ labels[row.status] }}</small>
          <small v-for="issue in row.issues" :key="issue" class="routine-error">{{ issue }}</small>
        </li>
      </ul>
      <RouterLink v-if="report" :to="{ path: '/workflow', query: { tab: 'binder', binder: binderId } }">Open checked Binder</RouterLink>
    </section>
    <nav aria-label="Related workflow">
      <RouterLink class="usx-btn" to="/snackbar?tab=feeds"><UIcon name="rss_feed" aria-hidden="true" /> Review feeds</RouterLink>
      <RouterLink class="usx-btn" to="/workflow?tab=binder"><UIcon name="book" aria-hidden="true" /> Binders</RouterLink>
      <RouterLink class="usx-btn" to="/workflow?tab=queue"><UIcon name="pending_actions" aria-hidden="true" /> Workflow Queue</RouterLink>
    </nav>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { UCORE_BASE } from "../../../api/base";
import { useWorkflowStore } from "../../../stores/workflow";
import UIcon from "../../../skills/atoms/UIcon.vue";

interface Routine {
  skill_id: string;
  time: string;
  last_result?: { state: string; timestamp?: string; next_retry?: string; error?: string } | null;
}

const jobs = ref<Routine[]>([]);
const scheduler = ref("");
const loading = ref(false);
const error = ref("");

const runningJob = ref("");
const runNotice = ref("");
const runFailed = ref(false);

async function runRoutine(job: Routine) {
  if (runningJob.value) return;
  const name = job.skill_id.replaceAll("_", " ");
  if (!window.confirm(`Run ${name} once with its configured settings? This may change files or local data.`)) return;
  runningJob.value = job.skill_id;
  runNotice.value = "";
  runFailed.value = false;
  try {
    const response = await fetch(`${UCORE_BASE}/api/system/maintenance/${encodeURIComponent(job.skill_id)}/run`, {
      method: "POST",
      headers: { "x-ucore-confirm": "true" },
    });
    if (response.status === 401 || response.status === 403) {
      throw new Error("Choose a local administrator profile to run this routine.");
    }
    const result = await response.json().catch(() => null);
    if (!response.ok || !result?.success) throw new Error(result?.error || "Could not run this routine.");
    runNotice.value = "Routine completed.";
  } catch (exc) {
    runFailed.value = true;
    runNotice.value = exc instanceof Error ? exc.message : "Could not run this routine.";
  } finally {
    await load();
    runningJob.value = "";
  }
}

function formatTime(value: string) {
  return new Date(value).toLocaleString();
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/system/maintenance`, {
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) throw new Error("Maintenance scheduler unavailable.");
    const result = await response.json();
    scheduler.value = result.status;
    jobs.value = result.jobs || [];
  } catch {
    scheduler.value = "";
    jobs.value = [];
    error.value = "Could not load maintenance routines.";
  } finally {
    loading.value = false;
  }
}

interface IntakeCheck {
  filename: string;
  status: "complete" | "invalid" | "untracked";
  issues: string[];
}

const wf = useWorkflowStore();
const binderId = ref("");
const checking = ref(false);
const report = ref<IntakeCheck[] | null>(null);
const checkError = ref("");
const labels = { complete: "Provenance complete", invalid: "Needs attention", untracked: "Without intake metadata" };

async function checkBinder() {
  if (!binderId.value || checking.value) return;
  checking.value = true;
  report.value = null;
  checkError.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/binder/${encodeURIComponent(binderId.value)}/intake-check`, {
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) {
      if (response.status === 401) throw new Error("Choose a local user profile to check Binder provenance.");
      if (response.status === 404) {
        const result = await response.json().catch(() => null);
        throw new Error(result?.error === "Binder not found"
          ? "This Binder could not be found."
          : "The running uCore backend does not expose Binder intake checks. Restart it from the current checkout.");
      }
      throw new Error("Could not check this Binder.");
    }
    const result = await response.json();
    if (!Array.isArray(result.documents)) throw new Error("The Binder check returned an invalid report.");
    report.value = result.documents;
  } catch (exc) {
    checkError.value = exc instanceof Error && exc.name !== "TypeError" && exc.name !== "TimeoutError"
      ? exc.message
      : "Could not reach uCore to check this Binder.";
  } finally {
    checking.value = false;
  }
}

onMounted(() => {
  void load();
  void wf.fetchBinders().then(() => {
    if (!binderId.value && wf.binders.some(binder => binder.id === wf.activeBinderId)) {
      binderId.value = wf.activeBinderId;
    }
  }).catch(() => { checkError.value = "Could not load Binders."; });
});
</script>

<style scoped>
.routines { display: grid; gap: var(--usx-spacing-md); min-width: 0; }
.routines header, .routines nav { display: flex; flex-wrap: wrap; align-items: center; gap: var(--usx-spacing-sm); }
.routines header { justify-content: space-between; }
.routines h2, .routines p { margin: 0; }
.routines .usx-btn { display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); margin: 0; }
.routine-list { list-style: none; margin: 0; padding: 0; }
.routine-list li { display: grid; gap: 3px; padding: var(--usx-spacing-sm) 0; border-bottom: 1px solid var(--usx-color-border); overflow-wrap: anywhere; }
.routine-list strong, .routine-list span { text-transform: capitalize; }
.intake-check { display: grid; gap: var(--usx-spacing-sm); min-width: 0; }
.intake-check form { display: flex; align-items: end; flex-wrap: wrap; gap: var(--usx-spacing-sm); }
.intake-check select { max-width: 100%; }
.intake-check .routine-list strong { text-transform: none; }
.routine-run { justify-self: start; }
.routine-list small { color: var(--usx-color-on-surface-muted); }
.routine-list .routine-error { color: var(--usx-color-danger); }
</style>
