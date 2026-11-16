<template>
  <section class="mission-control">
    <header class="mission-control__header">
      <h2>Mission Control Dashboard</h2>
      <p>What would you like to do today?</p>
    </header>
    <form class="mission-control__form" @submit.prevent="create">
      <input
        id="mission-objective"
        v-model="objective"
        aria-label="Mission objective"
        maxlength="500"
        placeholder="What would you like to achieve?"
        required
      />
      <button class="usx-btn usx-btn--primary" :disabled="busy || !objective.trim()">
        <UIcon name="flag" />Set mission
      </button>
    </form>
    <p v-if="error" role="alert" class="mission-control__error">{{ error }}</p>
    <label v-if="wf.missions.length" class="mission-control__selector">
      <span>Current mission</span>
      <select :value="wf.activeMissionId" @change="wf.selectMission(($event.target as HTMLSelectElement).value)">
        <option value="">All missions</option>
        <option v-for="mission in wf.missions.filter(item => item.status !== 'archived')" :key="mission.id" :value="mission.id">
          {{ mission.title }} · {{ mission.status }}
        </option>
      </select>
    </label>
    <section v-if="selectedMission" class="mission-control__focus">
      <h3>{{ selectedMission.title }}</h3>
      <p class="mission-control__progress">{{ completed }} of {{ wf.missionTasks.length }} tasks done</p>
      <div class="mission-control__actions">
        <button class="usx-btn" @click="wf.setTab('tasks')"><UIcon name="checklist" />Tasks</button>
        <button class="usx-btn" @click="wf.setTab('queue')"><UIcon name="queue" />Queue</button>
        <button class="usx-btn" :disabled="busy" @click="setStatus(selectedMission.status === 'completed' ? 'active' : 'completed')">
          {{ selectedMission.status === 'completed' ? 'Reopen mission' : 'Complete mission' }}
        </button>
      </div>
      <label class="mission-control__field">
        <span>Result Binder</span>
        <select :value="selectedMission.binder || ''" :disabled="busy" @change="linkBinder(($event.target as HTMLSelectElement).value)">
          <option value="">Choose when ready</option>
          <option v-for="binder in wf.binders" :key="binder.id" :value="binder.id">{{ binder.title || binder.id }}</option>
        </select>
      </label>
      <button class="usx-btn" @click="wf.requestBinderCreation()">
        <UIcon name="create_new_folder" />New Binder for materials
      </button>
    </section>
    <p v-else-if="!wf.missions.length && !wf.loading" class="mission-control__hint">
      A mission gives the work a purpose. Tasks and research move it forward; a Binder collects the results.
    </p>
    <section v-if="nextTask" class="mission-control__next-section">
      <h3>Up next</h3>
      <button class="usx-btn mission-control__next" @click="wf.openTask(nextTask)">
        <UIcon name="play_circle" />{{ nextTask.title }}<UIcon name="arrow_forward" />
      </button>
      <button
        type="button"
        class="usx-btn mission-control__details-toggle"
        :aria-expanded="showTaskDetails"
        aria-controls="mission-next-details"
        @click="showTaskDetails = !showTaskDetails"
      >
        <UIcon :name="showTaskDetails ? 'expand_less' : 'expand_more'" />
        {{ showTaskDetails ? 'Less details' : 'More details' }}
      </button>
      <div v-show="showTaskDetails" id="mission-next-details" class="mission-control__details">
        <p v-if="nextTask.description || nextTask.summary">{{ nextTask.description || nextTask.summary }}</p>
        <dl>
          <dt>Status</dt><dd>{{ nextTask.status.replaceAll('-', ' ') }}</dd>
          <dt>Priority</dt><dd>{{ nextTask.priority }}</dd>
          <template v-if="nextTask.due"><dt>Due</dt><dd>{{ nextTask.due }}</dd></template>
        </dl>
      </div>
    </section>
  </section>
</template>
<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useWorkflowStore } from '../../../stores/workflow';
import UIcon from '../../../skills/atoms/UIcon.vue';
const wf = useWorkflowStore();
const objective = ref(''), busy = ref(false), error = ref('');
const selectedMission = computed(() => wf.missions.find(mission => mission.id === wf.activeMissionId));
const completed = computed(() => wf.missionTasks.filter(task => task.status === 'completed').length);
const nextTask = computed(() => [...wf.missionTasks].filter(task => ['todo', 'in-progress', 'review'].includes(task.status)).sort((a, b) => (a.status === 'in-progress' ? -1 : b.status === 'in-progress' ? 1 : a.title.localeCompare(b.title)))[0]);
const showTaskDetails = ref(false);
watch(() => nextTask.value?.id, () => { showTaskDetails.value = false; });
async function perform(action: () => Promise<void>) { if (busy.value) return; busy.value = true; error.value = ''; try { await action(); } catch (failure) { error.value = failure instanceof Error ? failure.message : 'Could not save mission'; } finally { busy.value = false; } }
async function create() { await perform(async () => { await wf.createMission(objective.value.trim()); objective.value = ''; }); }
async function setStatus(status: string) { if (selectedMission.value) await perform(() => wf.updateMission(selectedMission.value!.id, { status })); }
async function linkBinder(binder: string) { if (selectedMission.value) await perform(async () => { await wf.updateMission(selectedMission.value!.id, { binder }); wf.activeBinderId = binder; }); }
</script>
<style scoped>
.mission-control {
  display: grid;
  align-content: start;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  min-width: 0;
}

h2 {
  margin: 0;
  font-size: var(--usx-font-size-xl);
  line-height: var(--usx-line-height-tight, 1.25);
  color: var(--usx-color-on-surface);
}

h3 {
  margin: 0;
  font-size: var(--usx-font-size-base);
  line-height: 1.4;
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

p {
  margin: 0;
  font-size: var(--usx-font-size-base);
  line-height: var(--usx-line-height-normal, 1.5);
}

header p {
  color: var(--usx-color-on-surface-muted);
}

label {
  display: grid;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
}

.mission-control__focus {
  display: grid;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md, 12px);
  background: var(--usx-color-surface);
}

.mission-control__form,
.mission-control__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.mission-control__form input {
  flex: 1 1 18rem;
}

input,
select {
  box-sizing: border-box;
  min-width: 0;
  width: 100%;
  margin: 0;
  font: inherit;
  padding: 10px 12px;
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
}

#mission-objective:focus {
  border-color: transparent;
  box-shadow: none;
  outline: 2px solid var(--usx-color-primary);
  outline-offset: -2px;
}

select:focus-visible {
  outline: 2px solid var(--usx-color-primary);
  outline-offset: 2px;
}

.usx-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin: 0;
  width: fit-content;
  font-size: var(--usx-font-size-base);
}

.mission-control__error {
  color: var(--usx-color-danger);
  font-size: var(--usx-font-size-sm);
}

.mission-control__progress {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.mission-control__hint {
  color: var(--usx-color-on-surface-muted);
}

.mission-control__next-section {
  display: grid;
  gap: var(--usx-spacing-sm);
}

.mission-control__next {
  text-align: left;
  white-space: normal;
  width: 100%;
  justify-content: space-between;
}

.mission-control__form .usx-btn,
.mission-control__next,
.mission-control__details-toggle {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
}

.mission-control__details {
  padding: var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  overflow-wrap: anywhere;
}

.mission-control__details p {
  white-space: pre-wrap;
}

.mission-control__details dl {
  display: grid;
  grid-template-columns: max-content minmax(0, 1fr);
  gap: var(--usx-spacing-xs) var(--usx-spacing-md);
  margin: 0;
  font-size: var(--usx-font-size-sm);
}

.mission-control__details p + dl {
  margin-top: var(--usx-spacing-sm);
}

.mission-control__details dd {
  margin: 0;
}

@media (max-width: 640px) {
  .mission-control__form {
    align-items: stretch;
    flex-direction: column;
  }
  .mission-control__form input {
    flex: auto;
  }
  .mission-control__form .usx-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
