<template>
  <nav class="workflow-nav" aria-label="Workflow location">
    <p class="workflow-nav__location" aria-live="polite">{{ wf.locationLabel }}</p>
    <p v-if="notice" role="alert">{{ notice }}</p>
    <div v-if="missionMode" class="workflow-nav__heading">
      <RouterLink class="usx-btn" to="/workflow?tab=mission-control">Mission dashboard</RouterLink>
    </div>
    <section v-if="missionMode" aria-label="Missions">
      <RouterLink v-for="mission in wf.missions" :key="mission.id" class="usx-btn"
        :to="{ path: '/workflow', query: { tab: 'mission-control', mission: mission.id, binder: mission.binder || undefined } }">
        <UIcon name="flag" aria-hidden="true" />{{ mission.title }}
      </RouterLink>
      <p v-if="!wf.missions.length">No missions yet.</p>
    </section>
    <div v-else class="workflow-nav__heading">
      <RouterLink v-for="view in listViews" :key="view" class="usx-btn"
        :to="{ path: '/workflow', query: { tab: view.toLowerCase(), binder: wf.activeBinderId || undefined, mission: wf.activeMissionId || undefined, list: wf.activeList || undefined } }">{{ view }}</RouterLink>
    </div>
    <details open>
      <summary>
        <UIcon name="chevron_right" class="workflow-nav__chevron" aria-hidden="true" />
        Binders
      </summary>
      <button v-if="!missionMode" class="usx-btn" @click="wf.showList()">All tasks</button>
      <button v-for="binder in wf.binderChoices" :key="binder.id" class="usx-btn" :aria-current="wf.activeBinderId === binder.id ? 'page' : undefined"
        @click="binder.hasContent ? wf.showBinder(binder.id) : wf.showList('', binder.id)" @dragover.prevent @drop.prevent="drop($event, { binder: binder.id })">
        <UIcon name="book" /> {{ binder.title || binder.id }}
      </button>
      <p v-if="!wf.binderChoices.length">No binders yet.</p>
    </details>
    <BinderActions class="workflow-nav__management" />
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
import { ref, onMounted, watch } from "vue";
import { useWorkflowStore } from "../../stores/workflow";
import { UCORE_BASE } from "../../api/base";
import UIcon from "../atoms/UIcon.vue";
import BinderActions from "./BinderActions.vue";
const props = defineProps<{ missionMode?: boolean }>();
const listViews = ["Tasks", "Feeds", "Queue"];
const wf = useWorkflowStore();
const notice = ref("");
onMounted(() => {
  if (!wf.tasks.length) void wf.fetchTasks().catch(error => { notice.value = error.message; });
  if (!wf.binders.length) void wf.fetchBinders().catch(error => { notice.value = error.message; });
});
watch(() => props.missionMode, missionMode => {
  if (missionMode && !wf.missions.length) {
    void wf.fetchMissions().catch(error => { notice.value = error.message; });
  }
}, { immediate: true });
async function drop(event: DragEvent, destination: { board?: string; binder?: string }) {
  notice.value = "";
  try { await wf.dropTask(event, destination); }
  catch (error) { notice.value = error instanceof Error ? error.message : "Could not move task"; }
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
.workflow-nav {
  width: 100%;
  min-height: 0;
  overflow-y: auto;
  font-size: var(--usx-font-size-sm);
}

.workflow-nav > p {
  margin: 0;
  padding: 4px 8px;
  overflow-wrap: anywhere;
  color: var(--usx-color-on-surface-muted);
}

.workflow-nav > :is(details, section) {
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.workflow-nav summary,
.workflow-nav__heading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  box-sizing: border-box;
  min-height: 37px;
  padding: 4px 8px;
  border-bottom: 1px solid var(--usx-color-border);
}

.workflow-nav summary {
  cursor: pointer;
  list-style: none;
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--usx-color-on-surface-muted);
}

.workflow-nav summary::-webkit-details-marker { display: none; }
.workflow-nav details[open] > summary .workflow-nav__chevron { transform: rotate(90deg); }

.workflow-nav .usx-btn,
.workflow-nav__management :deep(.usx-btn) {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--usx-spacing-xs);
  box-sizing: border-box;
  min-width: 0;
  min-height: 30px;
  margin: 0;
  padding: 3px 8px;
  border: 0;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface);
  font: inherit;
  text-align: left;
  white-space: normal;
  overflow-wrap: anywhere;
}

.workflow-nav :is(details, section) > .usx-btn { width: 100%; }
.workflow-nav__heading { flex-wrap: wrap; }
.workflow-nav__heading strong { margin-inline-end: auto; }
.workflow-nav__management { padding: 4px 8px; }
.workflow-nav__management :deep(input) { min-width: 0; max-width: 100%; box-sizing: border-box; }
.workflow-nav :is(details, section) > p {
  margin: 0;
  padding: 4px 8px;
  color: var(--usx-color-on-surface-muted);
}

.workflow-nav .usx-btn:hover,
.workflow-nav__management :deep(.usx-btn:hover) {
  background: var(--usx-color-surface-hover);
}
.workflow-nav .usx-btn[aria-current="page"] {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-primary);
}
</style>
