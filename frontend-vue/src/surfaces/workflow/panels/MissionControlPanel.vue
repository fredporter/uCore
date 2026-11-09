<template>
  <section class="mission-control">
    <header><h2>Mission Control</h2><p>What would you like to do today?</p></header>
    <form @submit.prevent="create">
      <label for="mission-objective">Your objective</label>
      <div class="mission-control__entry"><input id="mission-objective" v-model="objective" maxlength="500" placeholder="What would you like to achieve?" required /><button class="usx-btn usx-btn--primary" :disabled="busy || !objective.trim()"><UIcon name="flag" />Set mission</button></div>
    </form>
    <p v-if="error" role="alert">{{ error }}</p>
    <label v-if="wf.missions.length">Current mission
      <select :value="wf.activeMissionId" @change="wf.selectMission(($event.target as HTMLSelectElement).value)"><option value="">All missions</option><option v-for="mission in wf.missions.filter(item => item.status !== 'archived')" :key="mission.id" :value="mission.id">{{ mission.title }} · {{ mission.status }}</option></select>
    </label>
    <section v-if="selectedMission" class="mission-control__focus">
      <h3>{{ selectedMission.title }}</h3>
      <p>{{ completed }} of {{ wf.missionTasks.length }} tasks done</p>
      <div class="mission-control__actions"><button class="usx-btn" @click="wf.setTab('tasks')"><UIcon name="checklist" />Tasks</button><button class="usx-btn" @click="wf.setTab('queue')"><UIcon name="queue" />Queue</button><button class="usx-btn" :disabled="busy" @click="setStatus(selectedMission.status === 'completed' ? 'active' : 'completed')">{{ selectedMission.status === 'completed' ? 'Reopen mission' : 'Complete mission' }}</button></div>
      <label>Result Binder
        <select :value="selectedMission.binder || ''" :disabled="busy" @change="linkBinder(($event.target as HTMLSelectElement).value)"><option value="">Choose when ready</option><option v-for="binder in wf.binders" :key="binder.id" :value="binder.id">{{ binder.title || binder.id }}</option></select>
      </label>
      <button class="usx-btn" @click="wf.binderCreateRequested = true"><UIcon name="create_new_folder" />New Binder for materials</button>
    </section>
    <p v-else-if="!wf.missions.length && !wf.loading">A mission gives the work a purpose. Tasks and research move it forward; a Binder collects the results.</p>
    <section v-if="nextTask"><h3>Up next</h3><button class="usx-btn mission-control__next" @click="wf.openTask(nextTask)"><UIcon name="play_circle" />{{ nextTask.title }}<UIcon name="arrow_forward" /></button></section>
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
.mission-control { display: grid; gap: var(--usx-spacing-md); padding: var(--usx-spacing-md); min-width: 0; }
h2, h3, p { margin: 0; } header, form, label, .mission-control__focus { display: grid; gap: var(--usx-spacing-sm); }
.mission-control__entry, .mission-control__actions { display: flex; align-items: center; flex-wrap: wrap; gap: var(--usx-spacing-sm); }
input, select { box-sizing: border-box; min-width: 0; width: 100%; margin: 0; font: inherit; }
.mission-control__entry input { flex: 1 1 18rem; }
.mission-control__focus { border-top: var(--usx-border-width) solid var(--usx-color-border); padding-top: var(--usx-spacing-md); }
.usx-btn { display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); margin: 0; width: fit-content; }
.mission-control__next { text-align: left; white-space: normal; }
</style>
