<template>
  <section class="workflow-queue">
    <header><h2>Queue</h2><p>Background work and recent results across your workspace.</p><button class="usx-btn" :disabled="refreshing" @click="refresh"><UIcon name="refresh" />Refresh workflow runs</button></header>
    <section v-if="wf.activeMissionId" aria-label="Mission task queue"><h3>{{ wf.missions.find(mission => mission.id === wf.activeMissionId)?.title }}</h3><p>Tasks for this objective. Background runs below retain their existing job identities.</p><p v-if="!wf.missionTasks.length">No tasks for this mission yet.</p><button v-for="task in wf.missionTasks.filter(item => !['completed', 'archived', 'cancelled', 'superseded'].includes(item.status))" :key="task.id" class="usx-btn queue-run" @click="wf.openTask(task)">{{ task.title }} · {{ task.status }}</button></section>
    <p v-if="error" role="alert">{{ error }}</p>
    <section aria-label="Workflow runs"><h3>Workflow runs</h3><p v-if="!wf.workflowRuns.length">No workflow runs yet.</p><article v-for="run in wf.workflowRuns" :key="run.run_id" class="queue-run"><strong>{{ run.workflow_name || run.workflow_id }}</strong><span>{{ run.status }}</span><time>{{ run.started_at ? new Date(run.started_at).toLocaleString() : '' }}</time></article></section>
    <BrowserUISurface embedded queue-only />
  </section>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { useWorkflowStore } from '../../../stores/workflow';
import BrowserUISurface from '../../browserui/BrowserUISurface.vue';
import UIcon from '../../../skills/atoms/UIcon.vue';
const wf = useWorkflowStore();
const refreshing = ref(false), error = ref('');
async function refresh() { refreshing.value=true; error.value=''; try { await wf.fetchWorkflowRuns(); } catch { error.value='Could not refresh workflow runs.'; } finally { refreshing.value=false; } }
</script>
<style scoped>
.workflow-queue { display: grid; gap: var(--usx-spacing-md); min-width: 0; }
.workflow-queue header, .workflow-queue section { padding: var(--usx-spacing-md); margin: 0; }
h2, h3, p { margin: 0 0 var(--usx-spacing-sm); }
.queue-run { display: flex; align-items: center; flex-wrap: wrap; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm) 0; border-bottom: 1px solid var(--usx-color-border); }
.queue-run strong { flex: 1; }
</style>
