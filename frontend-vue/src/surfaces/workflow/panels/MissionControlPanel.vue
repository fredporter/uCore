<template>
  <section class="mission-control">
    <header class="mission-control__header">
      <h2>Mission Control</h2>
      <p>What would you like to do today?</p>
    </header>
    <form class="mission-control__form" @submit.prevent="create">
      <label for="mission-objective">Your objective</label>
      <div class="mission-control__entry">
        <input
          id="mission-objective"
          v-model="objective"
          maxlength="500"
          placeholder="What would you like to achieve?"
          required
        />
        <button class="usx-btn usx-btn--primary" :disabled="busy || !objective.trim()">
          <UIcon name="flag" />Set mission
        </button>
      </div>
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
      <button class="usx-btn" @click="wf.binderCreateRequested = true">
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
    </section>
  </section>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue';
import { useWorkflowStore } from '../../../stores/workflow';
import UIcon from '../../../skills/atoms/UIcon.vue';
const wf = useWorkflowStore();
const objective = ref(''), busy = ref(false), error = ref('');
const selectedMission = computed(() => wf.missions.find(mission => mission.id === wf.activeMissionId));
const completed = computed(() => wf.missionTasks.filter(task => task.status === 'completed').length);
const nextTask = computed(() => [...wf.missionTasks].filter(task => ['todo', 'in-progress', 'review'].includes(task.status)).sort((a, b) => (a.status === 'in-progress' ? -1 : b.status === 'in-progress' ? 1 : a.title.localeCompare(b.title)))[0]);
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

form,
.mission-control__focus {
  display: grid;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md, 12px);
  background: var(--usx-color-surface);
}

.mission-control__entry,
.mission-control__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
}

.mission-control__entry input {
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

input:focus-visible,
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

@media (max-width: 640px) {
  .mission-control__entry {
    align-items: stretch;
    flex-direction: column;
  }
  .mission-control__entry input {
    flex: auto;
  }
  .mission-control__entry .usx-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
