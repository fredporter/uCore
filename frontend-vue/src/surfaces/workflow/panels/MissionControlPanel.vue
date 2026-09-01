<template>
  <div class="wf-panel wf-panel--zen wf-zen-surface">
    <header class="wf-zen-header">
      <div>
        <p class="wf-zen-kicker">User Workflow</p>
        <h2>What needs your attention?</h2>
        <p>{{ wf.inProgressCount }} in progress · {{ wf.activeTasks.length }} open</p>
      </div>
      <button class="wf-zen-primary" type="button" @click="openTasks">
        <UIcon name="add" /> New or open task
      </button>
    </header>

    <div v-if="wf.loading" class="wf-loading"><UIcon name="sync" /> Loading workflow…</div>
    <div
      v-else-if="wf.error && !wf.tasks.length && !wf.missions.length"
      class="wf-error"
    >
      <UIcon name="error" /> {{ wf.error }}
      <button type="button" @click="wf.fetchAll()">Retry</button>
    </div>

    <section v-if="currentTasks.length" class="wf-zen-section">
      <div class="wf-zen-section__heading">
        <h3>Now</h3><span>{{ currentTasks.length }}</span>
      </div>
      <div class="task-list wf-now-list">
        <button
          v-for="task in currentTasks"
          :key="task.id"
          class="task-list__row"
          type="button"
          @click="openTask(task)"
        >
          <span class="task-list__main">
            <span class="task-list__state" :class="`task-list__state--${task.status}`" />
            <span class="task-list__copy">
              <strong class="task-list__task-title">{{ task.title }}</strong>
              <small class="task-list__meta">{{ task.board || task.binder || "Workflow" }} · {{ task.status }}</small>
            </span>
          </span>
          <span class="task-list__editor-btn" :title="task.status === 'todo' ? 'Start task' : 'Continue task'"><UIcon name="view_sidebar" /></span>
        </button>
      </div>
    </section>

    <section class="wf-zen-section">
      <div class="wf-zen-section__heading">
        <h3>Missions</h3><span>{{ wf.missions.length }}</span>
      </div>
      <div class="wf-mission-cards">
        <button v-for="mission in wf.missions" :key="mission.id" class="wf-mission-row" type="button" @click="openMission(mission.taskIds)">
          <UIcon name="flag" />
          <span class="wf-mission-row__copy"><strong>{{ mission.title }}</strong><small>{{ mission.taskIds.length }} tasks · {{ mission.status }}</small></span>
          <UIcon name="arrow_forward" />
        </button>
      </div>
      <p v-if="!wf.missions.length && !wf.loading" class="wf-zen-empty">No missions yet. Add a task to begin.</p>
    </section>

    <div class="wf-dashboard-actions">
    <details class="wf-zen-details wf-prompt-card">
      <summary>Compile files into a Binder</summary>
      <div
        class="wf-launchpad-drop"
        :class="{ 'wf-launchpad-drop--active': isDragging }"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
      >
        <UIcon name="publish" />
        <span>Drop Markdown, YAML, JSON or code here</span>
        <div v-if="launchpadFiles.length" class="wf-launchpad-files">
          <div v-for="(file, idx) in launchpadFiles" :key="idx" class="wf-launchpad-file">
            <span>{{ file.name }}</span>
            <button type="button" title="Remove" @click="removeFile(idx)"><UIcon name="close" /></button>
          </div>
          <button class="wf-zen-primary" type="button" @click="compileBinder">Compile Binder</button>
        </div>
      </div>
    </details>

    <details class="wf-zen-details wf-prompt-card">
      <summary>Workflow settings and history</summary>
      <div class="wf-actions-row">
        <UButton size="sm" variant="secondary" icon="archive" :disabled="!!busyAction" @click="archiveState">Archive</UButton>
        <UButton size="sm" variant="secondary" icon="add" :disabled="!!busyAction" @click="seedState">Seed tasks</UButton>
        <UButton size="sm" variant="secondary" icon="refresh" :disabled="!!busyAction" @click="resetState">Reset + seed</UButton>
      </div>
      <p v-if="lastActionMessage" class="wf-action-message">{{ lastActionMessage }}</p>
      <div v-if="wf.workflowRuns.length" class="wf-zen-history">
        <span v-for="run in wf.workflowRuns.slice(0, 5)" :key="run.run_id">
          {{ run.workflow_name || run.workflow_id }} · {{ run.status }} · {{ formatTime(run.started_at) }}
        </span>
      </div>
    </details>
    </div>
  </div>
<!-- legacy dashboard retained temporarily as an unreachable migration reference -->
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import { useWorkflowStore } from "../../../stores/workflow";

const wf = useWorkflowStore();
const router = useRouter();
const busyAction = ref("");
const lastActionMessage = ref("");

const currentTasks = computed(() =>
  [...wf.activeTasks]
    .sort((a, b) => {
      const rank: Record<string, number> = { "in-progress": 0, review: 1, blocked: 2, todo: 3 };
      return (rank[a.status] ?? 9) - (rank[b.status] ?? 9);
    })
    .slice(0, 7),
);

function openTasks() {
  wf.setTab("tasks");
}

function openTask(task: (typeof wf.tasks)[number]) {
  wf.selectTask(task, true);
  wf.setTab("editor");
}

function openMission(taskIds: string[]) {
  const next = taskIds
    .map((id) => wf.tasks.find((task) => task.id === id))
    .find((task) => task && task.status !== "completed");
  if (next) openTask(next);
  else openTasks();
}

// ── Launchpad (moved from Binder tab) ─────────────────────────────
interface LaunchpadFile {
  name: string;
  size: number;
  type: string;
  raw: File;
}

const isDragging = ref(false);
const launchpadFiles = ref<LaunchpadFile[]>([]);

function onDragOver() {
  isDragging.value = true;
}

function onDragLeave() {
  isDragging.value = false;
}

function onDrop(e: DragEvent) {
  isDragging.value = false;
  if (!e.dataTransfer?.files) return;
  for (let i = 0; i < e.dataTransfer.files.length; i++) {
    const f = e.dataTransfer.files[i];
    launchpadFiles.value = [
      ...launchpadFiles.value,
      { name: f.name, size: f.size, type: f.type || "", raw: f },
    ];
  }
}

function removeFile(idx: number) {
  launchpadFiles.value.splice(idx, 1);
}

async function compileBinder(): Promise<void> {
  if (launchpadFiles.value.length === 0) return;
  wf.loading = true;
  try {
    for (const f of launchpadFiles.value) {
      const text = await f.raw.text();
      console.log("[Launchpad] file:", f.name, text.slice(0, 80));
    }
    lastActionMessage.value = `Compiled ${launchpadFiles.value.length} files`;
    launchpadFiles.value = [];
  } catch (e: any) {
    lastActionMessage.value = `Binder compile failed: ${e.message || e}`;
  } finally {
    wf.loading = false;
  }
}

function formatTime(iso: string): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

async function archiveState() {
  busyAction.value = "archive";
  lastActionMessage.value = "";
  try {
    const payload: any = await wf.archiveUserWorkflow("manual-user-archive");
    const dir = payload?.archive?.archive_dir || "archive created";
    lastActionMessage.value = `Archive complete: ${dir}`;
  } catch (e: any) {
    lastActionMessage.value = `Archive failed: ${e.message || e}`;
  } finally {
    busyAction.value = "";
  }
}

async function resetState() {
  const ok = window.confirm(
    "Archive current user workflow and reset to fresh seed data?",
  );
  if (!ok) return;

  busyAction.value = "reset";
  lastActionMessage.value = "";
  try {
    const payload: any = await wf.resetUserWorkflow("user-reset-seed");
    const count = payload?.seed?.tasks?.created_count || 0;
    lastActionMessage.value = `Reset complete. Seeded ${count} tasks.`;
  } catch (e: any) {
    lastActionMessage.value = `Reset failed: ${e.message || e}`;
  } finally {
    busyAction.value = "";
  }
}

async function seedState() {
  busyAction.value = "seed";
  lastActionMessage.value = "";
  try {
    const payload: any = await wf.seedUserWorkflow("user-seed-only");
    const count = payload?.seed?.tasks?.created_count || 0;
    lastActionMessage.value = `Seed complete. Added or refreshed ${count} tasks.`;
  } catch (e: any) {
    lastActionMessage.value = `Seed failed: ${e.message || e}`;
  } finally {
    busyAction.value = "";
  }
}

onMounted(() => {
  wf.fetchAll();
});
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
  height: 100%;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--usx-color-primary) 3%, transparent) 0%,
    transparent 20%
  );
}

.wf-panel--zen {
  width: min(100%, 60rem);
  margin: 0 auto;
  padding: clamp(var(--usx-spacing-md), 3vw, var(--usx-spacing-xl));
  background: none;
}

.wf-zen-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--usx-spacing-lg);
  padding-block: var(--usx-spacing-sm) var(--usx-spacing-lg);
}

.wf-zen-header h2,
.wf-zen-header p { margin: 0; }
.wf-zen-header h2 { font-size: clamp(1.65rem, 5vw, 2.5rem); }
.wf-zen-header p { color: var(--usx-color-on-surface-muted); }
.wf-zen-kicker { font-size: var(--usx-font-size-sm); text-transform: uppercase; letter-spacing: .08em; }

.wf-zen-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  min-height: 2.5rem;
  padding: 0 var(--usx-spacing-lg);
  border: var(--usx-border-width) solid var(--usx-color-primary);
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  color: var(--usx-color-primary);
  cursor: pointer;
  white-space: nowrap;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
}

.wf-zen-primary:hover {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

.wf-zen-section { border-top: 1px solid var(--usx-color-border); }
.wf-zen-section__heading { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-md) var(--usx-spacing-xs) var(--usx-spacing-xs); }
.wf-zen-section__heading h3 { margin: 0; font-size: var(--usx-font-size-base); }
.wf-zen-section__heading span { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }

.wf-task-row,
.wf-mission-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  width: 100%;
  min-height: 3.25rem;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 0;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface);
  text-align: left;
  cursor: pointer;
}
.wf-task-row:hover, .wf-mission-row:hover { background: var(--usx-color-surface-hover); }
.wf-task-row { border-radius: 0; }
.wf-task-row:not(:last-child) { border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.wf-mission-row { border-radius: 0; }
.wf-mission-row:not(:last-child) { border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.wf-mission-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr)); gap: var(--usx-spacing-sm); padding-top: var(--usx-spacing-sm); }
.wf-mission-cards .wf-mission-row { min-height: 7rem; padding: var(--usx-spacing-md); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); }
.wf-dashboard-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--usx-spacing-sm); }
.wf-dashboard-actions .wf-prompt-card { min-height: 3.5rem; padding: var(--usx-spacing-md); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); }
.wf-task-row__state { width: .7rem; height: .7rem; border: 2px solid var(--usx-color-border); border-radius: 50%; flex: 0 0 auto; }
.wf-task-row__state--in-progress { border-color: var(--usx-color-primary); background: var(--usx-color-primary); }
.wf-task-row__state--review { border-color: var(--usx-color-warning); }
.wf-task-row__state--blocked { border-color: var(--usx-color-danger); }
.wf-task-row__content, .wf-mission-row__copy { display: flex; flex: 1; min-width: 0; flex-direction: column; }
.wf-mission-row > :deep(.u-icon) { width: var(--usx-icon-size-md); height: var(--usx-icon-size-md); flex: 0 0 var(--usx-icon-size-md); font-size: var(--usx-icon-size-md); }
.wf-task-row small, .wf-mission-row small { color: var(--usx-color-on-surface-muted); }
.wf-task-row__action { display: inline-flex !important; flex: 0 0 auto !important; flex-direction: row !important; align-items: center; gap: 4px; color: var(--usx-color-primary); }
.wf-zen-empty { padding: var(--usx-spacing-lg); color: var(--usx-color-on-surface-muted); }

.wf-zen-details { border-top: 1px solid var(--usx-color-border); padding: var(--usx-spacing-md) var(--usx-spacing-xs); }
.wf-zen-details summary { cursor: pointer; color: var(--usx-color-on-surface-muted); }
.wf-zen-history { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); margin-top: var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }

@media (max-width: 600px) {
  .wf-zen-header { align-items: stretch; flex-direction: column; }
  .wf-task-row__action { font-size: 0; }
  .wf-dashboard-actions { grid-template-columns: 1fr; }
}

.wf-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  flex-wrap: wrap;
}

.wf-panel-badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.wf-actions-row {
  display: flex;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--usx-spacing-sm);
}

.wf-action-message {
  margin-top: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
}

.wf-button-warning :deep(.u-button) {
  background: var(--usx-color-warning);
  color: var(--usx-color-on-warning);
}

.wf-button-warning :deep(.u-button:hover) {
  background: color-mix(
    in srgb,
    var(--usx-color-warning) 86%,
    var(--usx-color-danger)
  );
}

.wf-next-actions {
  margin: 0;
  padding-left: var(--usx-spacing-lg);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-stats {
  --wf-column-min: calc(var(--usx-touch-min) * 3.75);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--wf-column-min)), 1fr)
  );
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.wf-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  min-width: 12ch;
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.wf-stat-value {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  line-height: var(--usx-line-height-tight);
}

.wf-stat-label {
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
}

.wf-stat-value--success {
  color: var(--usx-color-success);
}
.wf-stat-value--info {
  color: var(--usx-color-primary);
}
.wf-stat-value--warning {
  color: var(--usx-color-warning);
}

.wf-loading,
.wf-error {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
}

.wf-loading {
  color: var(--usx-color-on-surface-muted);
}

.wf-error {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
  border: var(--usx-border-width) solid
    color-mix(in srgb, var(--usx-color-danger) 20%, transparent);
}

.wf-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 var(--usx-border-width-thick) 0
    color-mix(in srgb, var(--usx-color-border) 35%, transparent);
}

.wf-section-title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: var(--usx-letter-spacing-wide);
}

.wf-board-grid {
  --wf-column-min: calc(var(--usx-touch-min) * 4.5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--wf-column-min)), 1fr)
  );
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.wf-board-card {
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  min-width: 0;
}

.wf-board-card-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
}

/* Dashboard-style mission card grid */
.wf-mission-grid {
  --wf-column-min: calc(var(--usx-touch-min) * 5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--wf-column-min)), 1fr)
  );
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.wf-mission-card {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid
    color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  min-width: 0;
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.wf-mission-card:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 4%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-primary) 20%, transparent);
  transform: translateY(calc(var(--usx-spacing-1) * -1));
}

.wf-mission-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  flex-shrink: 0;
  font-size: var(--usx-icon-size-lg);
}

.wf-mission-card:hover .wf-mission-card-icon {
  background: var(--usx-color-primary-disabled);
  color: var(--usx-color-primary);
}

.wf-mission-card-content {
  flex: 1;
  min-width: 0;
}

.wf-mission-card-title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0 0 var(--usx-spacing-xs) 0;
  color: var(--usx-color-on-surface);
}

.wf-mission-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin: 0 0 var(--usx-spacing-sm) 0;
  line-height: var(--usx-line-height-tight);
}

.wf-mission-card-badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.wf-mission-task-count {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin-left: auto;
}

.wf-run-grid {
  --wf-column-min: calc(var(--usx-touch-min) * 5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--wf-column-min)), 1fr)
  );
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.wf-run-card {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  min-width: 0;
  transition:
    border-color var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.wf-run-card:hover {
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-2) * -1));
}

.wf-run-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  flex-shrink: 0;
  font-size: var(--usx-icon-size-lg);
}

.wf-run-card-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-run-card-name {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-run-card-time {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  font-family: var(--usx-font-family-mono);
}

/* ─── Mini Binder Launchpad widget ───────────────────────────────── */
.wf-mini-binder {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}

.wf-mini-binder-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  margin-bottom: var(--usx-spacing-xs);
}

.wf-mini-binder-header :deep(.u-button) {
  margin-left: auto;
}

.wf-mini-binder-desc {
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
}

/* ── Launchpad drop-zone (Start here) ───────────────────────── */

.wf-launchpad-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xl) var(--usx-spacing-lg);
  border: calc(var(--usx-border-width) + var(--usx-border-width-thick)) dashed
    color-mix(in srgb, var(--usx-color-primary) 20%, transparent);
  border-radius: var(--usx-radius-lg);
  background: color-mix(in srgb, var(--usx-color-primary) 2%, transparent);
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast);
  cursor: pointer;
}

.wf-launchpad-drop--active,
.wf-launchpad-drop:hover {
  border-color: color-mix(in srgb, var(--usx-color-primary) 50%, transparent);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, transparent);
}

.wf-launchpad-prompt {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.wf-launchpad-hint {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.wf-launchpad-files {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  width: 100%;
  max-width: 40ch;
}

.wf-launchpad-file {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
}

.wf-launchpad-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-xs);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  margin-left: auto;
}

.wf-launchpad-remove:hover {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
}
</style>
