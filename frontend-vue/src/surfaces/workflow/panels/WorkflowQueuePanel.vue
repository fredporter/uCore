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
      <h3>Scheduled runs</h3>
      <p v-if="!wf.schedules.length">No reviewed schedules.</p>
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
onMounted(() => {
  if (!wf.schedules.length) void wf.fetchSchedules();
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
