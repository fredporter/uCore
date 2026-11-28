<template>
  <section class="workflow-queue">
    <header>
      <h2>Queue</h2>
      <button class="usx-btn" :disabled="refreshing" @click="refresh">
        <UIcon name="refresh" aria-hidden="true" />Refresh queue
      </button>
    </header>
    <nav aria-label="Related Snackbar workflows">
      <RouterLink class="usx-btn" :to="{ path: '/workflow', query: { tab: 'feeds', binder: wf.activeBinderId || undefined, mission: wf.activeMissionId || undefined } }">Feeds</RouterLink>
      <RouterLink class="usx-btn" to="/snackbar?tab=automation">Routines</RouterLink>
      <RouterLink class="usx-btn" to="/snackbar?tab=snacks">Snacks</RouterLink>
      <RouterLink class="usx-btn" to="/workflow?tab=skills">Skills</RouterLink>
    </nav>
    <section v-if="wf.activeMissionId" class="queue-section" aria-label="Mission task queue">
      <h3>{{ wf.missions.find(mission => mission.id === wf.activeMissionId)?.title }}</h3>
      <p v-if="!queuedTasks.length">No queued tasks for this mission.</p>
      <button v-for="task in queuedTasks" :key="task.id" class="usx-btn queue-run" @click="wf.openTask(task)">
        <UIcon name="play_circle" aria-hidden="true" />
        <span class="queue-run__copy">
          <strong>{{ task.title }}</strong>
          <small>{{ task.status.replaceAll('-', ' ') }}</small>
        </span>
        <UIcon name="arrow_forward" aria-hidden="true" />
      </button>
    </section>
    <p v-if="error" role="alert">{{ error }}</p>
    <section class="queue-section" aria-label="Workflow runs">
      <h3>Workflow runs</h3>
      <p v-if="!wf.workflowRuns.length">No workflow runs yet.</p>
      <article v-for="run in wf.workflowRuns" :key="run.run_id" class="queue-run">
        <UIcon name="pending_actions" aria-hidden="true" />
        <div class="queue-run__copy">
          <strong>{{ run.workflow_name || run.workflow_id }}</strong>
          <small>
            {{ run.status }}
            <template v-if="run.started_at">
              · <time :datetime="run.started_at">{{ new Date(run.started_at).toLocaleString() }}</time>
            </template>
          </small>
        </div>
        <div v-if="run.status === 'running'" class="queue-run__actions">
          <button
            class="usx-btn"
            :disabled="busyRunId === run.run_id"
            :aria-label="`Cancel run ${run.workflow_name || run.workflow_id}`"
            @click="act(run.run_id, 'cancel')"
          >
            <UIcon name="stop_circle" aria-hidden="true" />Cancel
          </button>
        </div>
        <div v-else-if="resumable(run.status)" class="queue-run__actions">
          <button
            class="usx-btn"
            :disabled="busyRunId === run.run_id"
            :aria-label="`Resume run ${run.workflow_name || run.workflow_id}`"
            @click="act(run.run_id, 'resume')"
          >
            <UIcon name="play_circle" aria-hidden="true" />Resume
          </button>
        </div>
      </article>
    </section>
    <section class="queue-section" aria-label="Scheduled runs">
      <div class="queue-section__head">
        <h3>Scheduled runs</h3>
        <button class="usx-btn" type="button" @click="startCreate">
          <UIcon name="add" aria-hidden="true" />New schedule
        </button>
      </div>
      <p v-if="scheduleError" role="alert">{{ scheduleError }}</p>

      <form v-if="draft" class="schedule-form" @submit.prevent="saveDraft">
        <label>
          <span>Schedule id</span>
          <input v-model.trim="draft.schedule_id" :disabled="!!editingId" maxlength="64" required />
        </label>
        <label>
          <span>Workflow</span>
          <select v-model="draft.workflow_id" required>
            <option value="" disabled>Choose a workflow</option>
            <option v-for="workflow in wf.workflowDefinitions" :key="workflow.id" :value="workflow.id">
              {{ workflow.name || workflow.id }}
            </option>
          </select>
        </label>
        <label>
          <span>Kind</span>
          <select v-model="draft.kind">
            <option value="calendar">Calendar time</option>
            <option value="delay">Delay</option>
          </select>
        </label>
        <label v-if="draft.kind === 'calendar'">
          <span>Local time</span>
          <input v-model="draft.local_time" type="time" required />
        </label>
        <label v-else>
          <span>Delay (seconds)</span>
          <input v-model.number="draft.delay_seconds" type="number" min="0" step="30" />
        </label>
        <label>
          <span>Timezone</span>
          <input v-model.trim="draft.timezone" list="schedule-zones" required />
          <datalist id="schedule-zones">
            <option v-for="zone in zones" :key="zone" :value="zone" />
          </datalist>
        </label>
        <label class="schedule-form__check">
          <input v-model="draft.enabled" type="checkbox" />
          <span>Enabled</span>
        </label>
        <div class="schedule-form__actions">
          <button class="usx-btn usx-btn--primary" :disabled="saving">
            <UIcon name="check" aria-hidden="true" />{{ editingId ? 'Save changes' : 'Create schedule' }}
          </button>
          <button class="usx-btn" type="button" :disabled="saving" @click="cancelDraft">Cancel</button>
        </div>
      </form>

      <p v-if="!wf.schedules.length && !draft">No reviewed schedules.</p>
      <article v-for="schedule in wf.schedules" :key="schedule.schedule_id" class="queue-run">
        <UIcon name="schedule" aria-hidden="true" />
        <div class="queue-run__copy">
          <strong>{{ schedule.schedule_id }}</strong>
          <small>
            {{ schedule.local_time }} {{ schedule.timezone }} ·
            {{ schedule.enabled ? 'enabled' : 'disabled' }} · revision {{ schedule.revision }}
          </small>
          <small v-if="!schedule.occurrences.length">No occurrences planned yet.</small>
          <small v-for="occurrence in schedule.occurrences" :key="occurrence.occurrence_id">
            {{ occurrence.status }} ·
            <time :datetime="occurrence.due_at">{{ new Date(occurrence.due_at).toLocaleString() }}</time>
            <template v-if="occurrence.run_id"> · {{ occurrence.run_id }}</template>
            <template v-if="occurrence.reason"> · {{ occurrence.reason }}</template>
          </small>
        </div>
        <div class="queue-run__actions">
          <button class="usx-btn" :disabled="saving" @click="startEdit(schedule)">
            <UIcon name="edit" aria-hidden="true" />Edit
          </button>
          <button class="usx-btn" :disabled="saving" @click="toggleEnabled(schedule)">
            <UIcon :name="schedule.enabled ? 'pause' : 'play_arrow'" aria-hidden="true" />
            {{ schedule.enabled ? 'Disable' : 'Enable' }}
          </button>
          <button
            v-if="confirmDelete !== schedule.schedule_id"
            class="usx-btn"
            :disabled="saving"
            @click="confirmDelete = schedule.schedule_id"
          >
            <UIcon name="delete" aria-hidden="true" />Delete
          </button>
          <button v-else class="usx-btn usx-btn--danger" :disabled="saving" @click="removeSchedule(schedule)">
            <UIcon name="warning" aria-hidden="true" />Confirm delete
          </button>
        </div>
      </article>
    </section>
    <BrowserUISurface ref="researchQueue" embedded queue-only :binder-id="wf.activeBinderId || undefined" :key="wf.activeBinderId" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useWorkflowStore } from '../../../stores/workflow';
import BrowserUISurface from '../../browserui/BrowserUISurface.vue';
import UIcon from '../../../skills/atoms/UIcon.vue';

const wf = useWorkflowStore();
const refreshing = ref(false);
const busyRunId = ref('');
const error = ref('');
const RESUMABLE = ['interrupted', 'cancelled', 'timed_out'];

function resumable(status: string) {
  return RESUMABLE.includes(status);
}

async function act(runId: string, action: 'cancel' | 'resume') {
  busyRunId.value = runId;
  error.value = '';
  try {
    const ok = action === 'cancel' ? await wf.cancelRun(runId) : await wf.resumeRun(runId);
    if (!ok) error.value = `Could not ${action} the run.`;
  } finally {
    busyRunId.value = '';
  }
}
const researchQueue = ref<InstanceType<typeof BrowserUISurface> | null>(null);

type Draft = {
  schedule_id: string;
  workflow_id: string;
  kind: "calendar" | "delay";
  local_time: string;
  delay_seconds: number;
  timezone: string;
  enabled: boolean;
};

const zones = [
  "UTC",
  "Australia/Perth",
  "Australia/Sydney",
  "Europe/London",
  "Europe/Berlin",
  "America/New_York",
  "America/Los_Angeles",
  "Asia/Tokyo",
];

const draft = ref<Draft | null>(null);
const editingId = ref("");
const saving = ref(false);
const scheduleError = ref("");
const confirmDelete = ref("");

function emptyDraft(): Draft {
  return {
    schedule_id: "",
    workflow_id: wf.workflowDefinitions[0]?.id ?? "",
    kind: "calendar",
    local_time: "20:00",
    delay_seconds: 300,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    enabled: true,
  };
}

function startCreate() {
  scheduleError.value = "";
  confirmDelete.value = "";
  editingId.value = "";
  draft.value = emptyDraft();
}

function startEdit(schedule: typeof wf.schedules[number]) {
  scheduleError.value = "";
  confirmDelete.value = "";
  editingId.value = schedule.schedule_id;
  draft.value = {
    schedule_id: schedule.schedule_id,
    workflow_id: schedule.workflow_id,
    kind: schedule.kind === "delay" ? "delay" : "calendar",
    local_time: schedule.local_time,
    delay_seconds: schedule.delay_seconds ?? 0,
    timezone: schedule.timezone,
    enabled: schedule.enabled,
  };
}

function cancelDraft() {
  draft.value = null;
  editingId.value = "";
}

async function saveDraft() {
  if (!draft.value) return;
  scheduleError.value = "";
  saving.value = true;
  try {
    const payload = {
      workflow_id: draft.value.workflow_id,
      kind: draft.value.kind,
      local_time: draft.value.local_time,
      delay_seconds: Number(draft.value.delay_seconds) || 0,
      timezone: draft.value.timezone,
      enabled: draft.value.enabled,
    };
    const failure = editingId.value
      ? await wf.updateSchedule(editingId.value, payload)
      : await wf.createSchedule({ ...payload, schedule_id: draft.value.schedule_id });
    if (failure) {
      scheduleError.value = failure;
      return;
    }
    cancelDraft();
  } finally {
    saving.value = false;
  }
}

async function toggleEnabled(schedule: typeof wf.schedules[number]) {
  scheduleError.value = "";
  saving.value = true;
  try {
    const failure = await wf.updateSchedule(schedule.schedule_id, { enabled: !schedule.enabled });
    if (failure) scheduleError.value = failure;
  } finally {
    saving.value = false;
  }
}

async function removeSchedule(schedule: typeof wf.schedules[number]) {
  scheduleError.value = "";
  saving.value = true;
  try {
    const failure = await wf.deleteSchedule(schedule.schedule_id);
    if (failure) {
      scheduleError.value = failure;
      return;
    }
    confirmDelete.value = "";
    if (editingId.value === schedule.schedule_id) cancelDraft();
  } finally {
    saving.value = false;
  }
}
onMounted(() => {
  if (!wf.schedules.length) void wf.fetchSchedules();
  if (!wf.workflowDefinitions.length) void wf.fetchWorkflowDefinitions();
});

const queuedTasks = computed(() => wf.missionTasks.filter(
  task => !['completed', 'archived', 'cancelled', 'superseded'].includes(task.status),
));

async function refresh() {
  refreshing.value = true;
  error.value = '';
  try {
    await Promise.all([wf.fetchWorkflowRuns(), wf.fetchSchedules(), researchQueue.value?.refreshQueue()]);
  } catch {
    error.value = 'Could not refresh the queue.';
  } finally {
    refreshing.value = false;
  }
}
</script>

<style scoped>
.workflow-queue {
  display: grid;
  align-content: start;
  gap: var(--usx-spacing-md);
  min-width: 0;
  padding: var(--usx-spacing-md);
}

.queue-section {
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--usx-spacing-sm);
}

.queue-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.schedule-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 11rem), 1fr));
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}

.schedule-form label {
  display: grid;
  gap: var(--usx-spacing-xs);
  margin: 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.schedule-form input,
.schedule-form select {
  margin: 0;
  font-size: var(--usx-font-size-sm);
}

.schedule-form__check {
  grid-auto-flow: column;
  align-items: center;
  justify-content: start;
  gap: var(--usx-spacing-xs);
}

.schedule-form__actions {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

h2, h3, p {
  margin: 0;
}

h2 {
  font-size: var(--usx-font-size-xl);
}

h3 {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

p, .queue-run__copy small {
  color: var(--usx-color-on-surface-muted);
}

.workflow-queue > header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}

.workflow-queue header .usx-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin: 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
}

.queue-run {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  margin: 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  text-align: left;
  white-space: normal;
}

.queue-run__copy {
  display: grid;
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
}

.queue-run__copy strong {
  font-weight: var(--usx-font-weight-semibold);
}

.queue-run__copy small {
  font-size: var(--usx-font-size-sm);
}

.queue-run__actions {
  display: flex;
  gap: var(--usx-spacing-sm);
  margin-inline-start: auto;
}
</style>
