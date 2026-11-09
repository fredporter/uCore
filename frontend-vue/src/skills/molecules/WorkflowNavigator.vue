<template>
  <nav class="workflow-nav" aria-label="Workflow location">
    <p class="workflow-nav__location" aria-live="polite">{{ wf.locationLabel }}</p>
    <p v-if="notice" role="alert">{{ notice }}</p>
    <details open>
      <summary>Task lists</summary>
      <button class="usx-btn" :aria-current="!wf.activeList && !wf.activeBinderId ? 'page' : undefined" @click="wf.showList()">All tasks</button>
      <button v-for="list in wf.taskLists" :key="list" class="usx-btn" :aria-current="wf.activeList === list ? 'page' : undefined"
        @click="wf.showList(list)" @dragover.prevent @drop.prevent="drop($event, { board: list })">
        <UIcon name="list" /> {{ list }} <small>{{ wf.tasks.filter(task => task.board === list && task.status !== 'completed').length }}</small>
      </button>
      <button class="usx-btn" @click="newList"><UIcon name="add" /> New list</button>
    </details>
    <details open>
      <summary>Binders</summary>
      <button v-for="binder in wf.binderChoices" :key="binder.id" class="usx-btn" :aria-current="wf.activeBinderId === binder.id ? 'page' : undefined"
        @click="binder.hasContent ? wf.showBinder(binder.id) : wf.showList('', binder.id)" @dragover.prevent @drop.prevent="drop($event, { binder: binder.id })">
        <UIcon name="book" /> {{ binder.title || binder.id }}
      </button>
      <p v-if="!wf.binderChoices.length">No binders yet.</p>
    </details>
    <section v-if="wf.activeBinderId || wf.activeList || wf.selectedTask" aria-label="Current work">
      <div class="workflow-nav__heading"><strong>In this location</strong><button class="usx-btn" @click="wf.showList(wf.activeList, wf.activeBinderId)">View tasks</button></div>
      <div v-if="wf.binders.some(binder => binder.id === wf.activeBinderId)" class="workflow-nav__heading">
        <button class="usx-btn" :aria-current="wf.binderDocument?.path.endsWith('/brief') ? 'page' : undefined" @click="openDocument('brief')">Brief</button>
        <button class="usx-btn" :aria-current="wf.binderDocument?.path.endsWith('/draft') ? 'page' : undefined" @click="openDocument('draft')">Draft</button>
      </div>
      <button v-for="task in wf.relatedTasks" :key="task.id" class="usx-btn" :aria-current="wf.selectedTask?.id === task.id ? 'page' : undefined"
        draggable="true" @dragstart="wf.startTaskDrag($event, task)" @click="wf.openTask(task)">
        <UIcon :name="task.status === 'completed' ? 'check_circle' : 'radio_button_unchecked'" /> {{ task.title }}
      </button>
      <p v-if="!wf.scopedTasks.length">No tasks here yet.</p>
    </section>
  </nav>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useWorkflowStore } from "../../stores/workflow";
import { UCORE_BASE } from "../../api/base";
import UIcon from "../atoms/UIcon.vue";
const wf = useWorkflowStore();
const notice = ref("");
onMounted(() => {
  if (!wf.binders.length) void wf.fetchBinders().catch(error => { notice.value = error.message; });
});
async function drop(event: DragEvent, destination: { board?: string; binder?: string }) {
  notice.value = "";
  try { await wf.dropTask(event, destination); }
  catch (error) { notice.value = error instanceof Error ? error.message : "Could not move task"; }
}
async function newList() {
  const name = window.prompt("List name");
  if (!name?.trim()) return;
  try { await wf.createList(name.trim()); }
  catch (error) { notice.value = error instanceof Error ? error.message : "Could not create list"; }
}
async function openDocument(part: "brief" | "draft") {
  notice.value = "";
  try {
    const id = wf.activeBinderId;
    const response = await fetch(`${UCORE_BASE}/api/binder/${encodeURIComponent(id)}`, { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error("Could not open binder content");
    const { binder } = await response.json();
    wf.openBinderDocument(id, `${binder.metadata.title || id} · ${part}`, binder[part] || "", binder.draft_sha256 || "", part === "brief");
  } catch (error) { notice.value = error instanceof Error ? error.message : "Could not open document"; }
}
</script>
<style scoped>
.workflow-nav { display: grid; gap: var(--usx-spacing-md); padding: var(--usx-spacing-sm); border-bottom: 1px solid var(--usx-color-border); }
.workflow-nav__location { overflow-wrap: anywhere; color: var(--usx-color-on-surface-muted); margin: 0; }
.workflow-nav details, .workflow-nav section { display: grid; gap: var(--usx-spacing-xs); }
.workflow-nav summary { cursor: pointer; margin-bottom: var(--usx-spacing-xs); }
.workflow-nav .usx-btn { display: flex; align-items: center; gap: var(--usx-spacing-xs); text-align: left; width: 100%; white-space: normal; }
.workflow-nav [aria-current="page"] { background: var(--usx-color-surface-hover); color: var(--usx-color-primary); }
.workflow-nav__heading { display: flex; align-items: center; gap: var(--usx-spacing-xs); }
.workflow-nav small { margin-left: auto; }
</style>
