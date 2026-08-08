<template>
  <div class="wf-panel">
    <div class="surface__panel">
      <h3 class="surface__panel-title">Tasks</h3>
      <p class="surface__panel-description">
        Tasker-compatible tasks-md workspace with Notion-style list and kanban
        cards.
      </p>
      <div class="wf-view-switch">
        <button
          class="wf-view-btn"
          :class="{ 'wf-view-btn--active': viewMode === 'list' }"
          @click="viewMode = 'list'"
        >
          <UIcon name="table_rows" />
          List
        </button>
        <button
          class="wf-view-btn"
          :class="{ 'wf-view-btn--active': viewMode === 'kanban' }"
          @click="viewMode = 'kanban'"
        >
          <UIcon name="view_kanban" />
          Kanban
        </button>
        <span class="wf-engine-chip">Bangle-aligned task cards</span>
      </div>
    </div>

    <div v-if="wf.loading" class="wf-loading">
      <UIcon name="sync" /> Loading tasks...
    </div>

    <div v-if="dragError" class="wf-error">
      <UIcon name="error" /> {{ dragError }}
    </div>

    <div v-if="viewMode === 'list'" class="task-list">
      <div class="task-list__head">
        <span>Task</span>
        <span>Status</span>
        <span>Priority</span>
        <span>Board</span>
        <span>Tags</span>
      </div>
      <div
        v-for="task in orderedTasks"
        :key="task.id"
        class="task-list__row"
        :class="{ 'task-list__row--selected': wf.selectedTask?.id === task.id }"
        @click="wf.selectTask(task)"
      >
        <div class="task-list__task-cell">
          <div class="task-list__task-title">{{ task.title }}</div>
          <div class="task-list__task-md">{{ toTaskMarkdown(task) }}</div>
        </div>
        <UBadge type="info" size="sm">{{ formatStatus(task.status) }}</UBadge>
        <UBadge :type="priorityBadgeType(task.priority)" size="sm">{{
          task.priority
        }}</UBadge>
        <span class="task-list__meta">{{ task.board || "general" }}</span>
        <span class="task-list__meta">{{
          task.tags.join(", ") || "none"
        }}</span>
      </div>
    </div>

    <div v-else class="kanban-board">
      <div v-if="selectedTask" class="surface__panel wf-task-detail">
        <div class="wf-task-detail__header">
          <div>
            <h4 class="wf-task-detail__title">{{ selectedTask.title }}</h4>
            <p class="wf-task-detail__meta">
              {{ selectedTask.workflowType || "user" }} ·
              {{ selectedTask.binder || "Sandbox" }} ·
              {{ selectedTask.workspace || "User Vault" }}
            </p>
          </div>
          <div class="wf-task-detail__badges">
            <UBadge type="info" size="sm">{{
              formatStatus(selectedTask.status)
            }}</UBadge>
            <UBadge :type="priorityBadgeType(selectedTask.priority)" size="sm">
              {{ selectedTask.priority }}
            </UBadge>
          </div>
        </div>

        <label class="wf-task-detail__field">
          <span class="wf-task-detail__label">Summary</span>
          <textarea
            :value="selectedTask.summary || selectedTask.description || ''"
            class="wf-input wf-textarea"
            rows="3"
            placeholder="Short task summary"
            @input="
              onSummaryChange(
                selectedTask.id,
                ($event.target as HTMLTextAreaElement).value,
              )
            "
          />
        </label>

        <label class="wf-task-detail__field">
          <span class="wf-task-detail__label">Notes</span>
          <textarea
            :value="selectedTask.notes || ''"
            class="wf-input wf-textarea"
            rows="4"
            placeholder="Notes linked to this task"
            @input="
              onNotesChange(
                selectedTask.id,
                ($event.target as HTMLTextAreaElement).value,
              )
            "
          />
        </label>

        <div class="wf-task-detail__steps">
          <div class="wf-task-detail__label-row">
            <span class="wf-task-detail__label">Steps</span>
            <span class="wf-task-detail__hint"
              >Click to advance, double-click to rename</span
            >
          </div>
          <div class="wf-step-rail">
            <button
              v-for="step in selectedTask.steps || []"
              :key="step.id"
              class="wf-step-chip"
              :class="`wf-step-chip--${step.status}`"
              @click.stop="wf.cycleTaskStep(selectedTask.id, step.id)"
              @dblclick.stop.prevent="
                renameStep(selectedTask.id, step.id, step.title)
              "
            >
              <UIcon
                :name="
                  step.status === 'completed'
                    ? 'check_circle'
                    : step.status === 'in-progress'
                      ? 'play_circle'
                      : step.status === 'blocked'
                        ? 'block'
                        : 'radio_button_unchecked'
                "
              />
              <span>{{ step.title }}</span>
            </button>
          </div>
        </div>

        <div class="wf-task-detail__assets">
          <span class="wf-task-detail__label">Assets</span>
          <div class="wf-asset-rail">
            <UBadge
              v-if="(selectedTask.assetPaths || []).length === 0"
              type="info"
              size="sm"
            >
              No linked assets
            </UBadge>
            <UBadge
              v-for="asset in selectedTask.assetPaths || []"
              :key="asset"
              type="info"
              size="sm"
            >
              {{ asset }}
            </UBadge>
          </div>
        </div>
      </div>
      <div
        v-for="status in statuses"
        :key="status"
        class="kanban-column"
        @dragover.prevent
        @drop="handleDrop(status)"
      >
        <div
          class="kanban-column-header"
          :class="`kanban-column-header--${status}`"
        >
          <span>{{ formatStatus(status as string) }}</span>
          <UBadge type="info" size="sm" circle>{{
            wf.tasksByStatus[status]?.length || 0
          }}</UBadge>
        </div>
        <div class="kanban-cards">
          <div
            v-if="(wf.tasksByStatus[status] || []).length === 0"
            class="kanban-empty"
          >
            No tasks
          </div>
          <div
            v-for="task in wf.tasksByStatus[status] || []"
            :key="task.id"
            class="kanban-card"
            :class="{
              'kanban-card--selected': wf.selectedTask?.id === task.id,
            }"
            draggable="true"
            @dragstart="handleDragStart(task.id, task.status)"
            @click="wf.selectTask(task)"
          >
            <div class="kanban-card-top">
              <div class="kanban-card-title">{{ task.title }}</div>
              <UBadge :type="priorityBadgeType(task.priority)">{{
                task.priority
              }}</UBadge>
            </div>
            <p class="kanban-card-desc">{{ truncate(task.description, 80) }}</p>
            <div class="kanban-card-meta">
              <span
                v-if="task.tags.length === 0"
                class="kanban-tag kanban-tag--muted"
                >No tags</span
              >
              <UBadge v-for="tag in task.tags" :key="tag" type="info" pill>{{
                tag
              }}</UBadge>
            </div>
            <div class="kanban-card-board">
              <UIcon name="view_kanban" />
              {{ task.board }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="wf.flowLogTasks.length > 0" class="surface__panel wf-flowlog">
      <h4 class="surface__panel-title">Flowlog</h4>
      <p class="surface__panel-description">
        Completed tasks move here automatically so active work stays
        uncluttered.
      </p>
      <div class="wf-flowlog-list">
        <button
          v-for="task in wf.flowLogTasks"
          :key="task.id"
          class="wf-flowlog-item"
          @click="wf.selectTask(task)"
        >
          <div class="wf-flowlog-item__title">{{ task.title }}</div>
          <div class="wf-flowlog-item__meta">
            <span>{{ task.binder || "Sandbox" }}</span>
            <span>{{
              task.completedAt
                ? new Date(task.completedAt).toLocaleString()
                : "completed"
            }}</span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import { useWorkflowStore } from "../../../stores/workflow";
import { toTaskMarkdownLine } from "../../../utils/taskMarkdown";

const wf = useWorkflowStore();
const viewMode = ref<"list" | "kanban">("list");
const statuses = ["todo", "in-progress", "review", "blocked"];
const dragTaskId = ref<string | null>(null);
const dragFromStatus = ref<string | null>(null);
const dragError = ref<string | null>(null);

const statusRank: Record<string, number> = {
  blocked: 0,
  "in-progress": 1,
  review: 2,
  todo: 3,
  completed: 4,
};

const orderedTasks = computed(() => {
  return [...wf.activeTasks].sort((a, b) => {
    const sa = statusRank[a.status] ?? 99;
    const sb = statusRank[b.status] ?? 99;
    if (sa !== sb) return sa - sb;
    return a.title.localeCompare(b.title);
  });
});

const selectedTask = computed(
  () => wf.selectedTask || orderedTasks.value[0] || wf.flowLogTasks[0] || null,
);

const STATUS_LABELS: Record<string, string> = {
  todo: "To Do",
  "in-progress": "In Progress",
  review: "Review",
  blocked: "Blocked",
  completed: "Done",
};

function formatStatus(status: string): string {
  return STATUS_LABELS[status] || status;
}

function truncate(text: string, maxLength: number): string {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + "...";
}

function priorityBadgeType(priority: string): "error" | "warning" | "info" {
  if (priority === "high") return "error";
  if (priority === "medium") return "warning";
  return "info";
}

function onSummaryChange(taskId: string, summary: string) {
  wf.updateTaskSummary(taskId, summary);
}

function onNotesChange(taskId: string, notes: string) {
  wf.updateTaskNotes(taskId, notes);
}

function renameStep(taskId: string, stepId: string, currentTitle: string) {
  const next = window.prompt("Rename step", currentTitle);
  if (next === null) return;
  const title = next.trim();
  if (!title) return;
  wf.updateTaskStep(taskId, stepId, { title });
}

function toTaskMarkdown(task: {
  status: string;
  title: string;
  tags: string[];
  board: string;
  priority: string;
}): string {
  return toTaskMarkdownLine(task);
}

function handleDragStart(taskId: string, status: string) {
  dragTaskId.value = taskId;
  dragFromStatus.value = status;
}

async function handleDrop(targetStatus: string) {
  const taskId = dragTaskId.value;
  const fromStatus = dragFromStatus.value;
  dragTaskId.value = null;
  dragFromStatus.value = null;
  dragError.value = null;

  if (!taskId || !fromStatus || fromStatus === targetStatus) {
    return;
  }

  const idx = wf.tasks.findIndex((task) => task.id === taskId);
  if (idx < 0) {
    return;
  }

  const previous = wf.tasks[idx].status;
  wf.updateTaskStatus(taskId, targetStatus);

  try {
    await wf.patchTask(taskId, { status: targetStatus });
  } catch (err: any) {
    wf.updateTaskStatus(taskId, previous);
    dragError.value = err?.message || "Failed to persist task move";
  }
}
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
}

.wf-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-error {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-danger);
  border-radius: var(--usx-radius-md);
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
  font-size: var(--usx-font-size-sm);
}

.wf-view-switch {
  margin-top: var(--usx-spacing-sm);
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.wf-task-detail {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.wf-task-detail__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  flex-wrap: wrap;
}

.wf-task-detail__title {
  margin: 0;
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
}

.wf-task-detail__meta {
  margin: var(--usx-spacing-xs) 0 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-task-detail__badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.wf-task-detail__field,
.wf-task-detail__steps,
.wf-task-detail__assets {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-task-detail__label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.wf-task-detail__label {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.wf-task-detail__hint {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.wf-textarea {
  width: 100%;
  min-height: calc(var(--usx-touch-min) * 1.2);
  resize: vertical;
}

.wf-step-rail,
.wf-asset-rail,
.wf-flowlog-list {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.wf-step-chip,
.wf-flowlog-item {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
}

.wf-step-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  cursor: pointer;
}

.wf-step-chip--completed {
  border-color: var(--usx-color-success);
  background: color-mix(in srgb, var(--usx-color-success) 10%, transparent);
}

.wf-step-chip--in-progress {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.wf-step-chip--blocked {
  border-color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
}

.wf-step-chip--todo {
  opacity: 0.85;
}

.wf-flowlog {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-flowlog-item {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm);
  text-align: left;
  cursor: pointer;
}

.wf-flowlog-item__title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.wf-flowlog-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.wf-view-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
}

.wf-view-btn--active {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.wf-engine-chip {
  display: inline-flex;
  align-items: center;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.task-list {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  overflow: hidden;
}

.task-list__head,
.task-list__row {
  display: grid;
  grid-template-columns:
    minmax(20ch, 4fr) minmax(10ch, 1.2fr) minmax(8ch, 1fr)
    minmax(10ch, 1.2fr) minmax(14ch, 2fr);
  gap: var(--usx-spacing-sm);
  align-items: center;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
}

.task-list__head {
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  background: var(--usx-color-surface-variant);
}

.task-list__row {
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  cursor: pointer;
}

.task-list__row:last-child {
  border-bottom: none;
}

.task-list__row:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 5%, transparent);
}

.task-list__row--selected {
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.task-list__task-cell {
  min-width: 0;
}

.task-list__task-title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-list__task-md {
  margin-top: var(--usx-spacing-xs);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-list__meta {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kanban-board {
  --kanban-column-min: calc(var(--usx-touch-min) * 4.5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--kanban-column-min)), 1fr)
  );
  gap: var(--usx-spacing-lg);
  align-items: start;
  min-width: 0;
}

.wf-flowlog {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
}

.kanban-column {
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  border: var(--usx-border-width) solid var(--usx-color-border);
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: calc(var(--usx-touch-min) * 5);
}

.kanban-column-header {
  padding: var(--usx-spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-base);
  border-top-style: solid;
  border-top-width: calc(
    var(--usx-border-width) + var(--usx-border-width-thick)
  );
}

.kanban-column-header--completed {
  border-top-color: var(--usx-color-success);
}
.kanban-column-header--in-progress {
  border-top-color: var(--usx-color-primary);
}
.kanban-column-header--review {
  border-top-color: var(--usx-color-warning);
}
.kanban-column-header--blocked {
  border-top-color: var(--usx-color-danger);
}
.kanban-column-header--todo {
  border-top-color: var(--usx-color-on-surface-muted);
}

.kanban-cards {
  flex: 1;
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg) var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.kanban-empty {
  padding: var(--usx-spacing-lg);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  font-style: italic;
}

.kanban-card {
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid transparent;
  cursor: pointer;
  min-width: 0;
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    box-shadow var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.kanban-card:hover {
  border-color: var(--usx-color-primary);
}

.kanban-card--selected {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, transparent);
}

.kanban-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
  margin-bottom: var(--usx-spacing-sm);
}

.kanban-card-title {
  min-width: 0;
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-base);
  line-height: var(--usx-line-height-tight);
  overflow-wrap: anywhere;
}

.kanban-card-desc {
  margin: 0 0 var(--usx-spacing-md) 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-tight);
  overflow-wrap: anywhere;
}

.kanban-card-meta {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  font-size: var(--usx-font-size-sm);
  margin-bottom: var(--usx-spacing-sm);
}

.kanban-tag {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.kanban-tag--muted {
  font-style: italic;
}

.kanban-card-board {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  min-width: 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  overflow-wrap: anywhere;
}

@media (max-width: 1100px) {
  .task-list__head,
  .task-list__row {
    grid-template-columns: minmax(16ch, 1fr);
  }

  .task-list__head span:not(:first-child) {
    display: none;
  }
}
</style>
