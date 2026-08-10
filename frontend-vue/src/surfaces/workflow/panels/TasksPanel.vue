<template>
  <div
    class="wf-panel"
    :class="{ 'wf-panel--editor-open': showCodeEditor && activeCodeTask }"
  >
    <!-- ── Task list / kanban (always visible, shrinks when editor slides in) ── -->
    <div class="wf-panel__main">
      <!-- Compact toolbar row -->
      <div class="wf-toolbar">
        <div class="wf-toolbar__toggles">
          <button
            class="wf-toolbar__btn"
            :class="{ 'wf-toolbar__btn--active': viewMode === 'list' }"
            title="List view"
            @click="viewMode = 'list'"
          >
            <UIcon name="table_rows" />
          </button>
          <button
            class="wf-toolbar__btn"
            :class="{ 'wf-toolbar__btn--active': viewMode === 'kanban' }"
            title="Kanban view"
            @click="viewMode = 'kanban'"
          >
            <UIcon name="view_kanban" />
          </button>
        </div>
        <span class="wf-toolbar__count">{{ wf.activeTasks.length }} open</span>
        <span
          v-if="wf.flowLogTasks.length"
          class="wf-toolbar__count wf-toolbar__count--done"
        >
          {{ wf.flowLogTasks.length }} done
        </span>
      </div>

      <div v-if="wf.loading" class="wf-loading">
        <UIcon name="sync" /> Loading tasks...
      </div>

      <div v-if="dragError" class="wf-error">
        <UIcon name="error" /> {{ dragError }}
      </div>

      <div v-if="viewMode === 'list'" class="task-list">
        <div
          v-for="task in orderedTasks"
          :key="task.id"
          class="task-list__row"
          :class="{
            'task-list__row--selected': wf.selectedTask?.id === task.id,
          }"
          @click="openTaskEditor(task)"
        >
          <div class="task-list__main">
            <div class="task-list__task-title">{{ task.title }}</div>
            <div class="task-list__pills">
              <span class="task-pill" :class="`task-pill--${task.status}`">{{
                formatStatus(task.status)
              }}</span>
              <span
                class="task-pill"
                :class="`task-pill--priority-${task.priority}`"
              >
                {{ task.priority }}
              </span>
              <span class="task-pill task-pill--board">{{
                task.board || "general"
              }}</span>
              <span
                v-for="tag in task.tags"
                :key="tag"
                class="task-pill task-pill--tag"
              >
                {{ tag }}
              </span>
            </div>
          </div>
          <button
            class="task-list__editor-btn"
            title="Open in Editor tab (split view)"
            @click.stop="openInEditorTab(task)"
          >
            <UIcon name="view_sidebar" />
          </button>
        </div>
      </div>

      <div v-else class="kanban-board">
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
            <span class="kanban-column-header__label">
              <UIcon :name="columnIcon(status)" />
              {{ formatStatus(status as string) }}
            </span>
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
              @click="openTaskEditor(task)"
            >
              <div class="kanban-card-top">
                <div class="kanban-card-title">{{ task.title }}</div>
                <UBadge :type="priorityBadgeType(task.priority)">{{
                  task.priority
                }}</UBadge>
              </div>
              <div class="kanban-card-pills">
                <span class="task-pill" :class="`task-pill--${task.status}`">
                  {{ formatStatus(task.status) }}
                </span>
                <span class="task-pill task-pill--board">{{ task.board }}</span>
                <span
                  v-for="tag in task.tags"
                  :key="tag"
                  class="task-pill task-pill--tag"
                >
                  {{ tag }}
                </span>
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
            @click="openTaskEditor(task)"
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

    <!-- ── Slide-in code editor panel (from right) ── -->
    <Transition name="wf-slide">
      <div v-if="showCodeEditor && activeCodeTask" class="wf-code-editor-slide">
        <div class="wf-code-editor__toolbar">
          <button class="wf-editor-back-btn" @click="closeCodeEditor">
            <UIcon name="arrow_back" />
          </button>
          <span class="wf-code-editor__title">{{ activeCodeTask.title }}</span>
          <button
            class="wf-editor-open-tab-btn"
            title="Open in Editor tab (side-by-side)"
            @click="openInEditorTab(activeCodeTask)"
          >
            <UIcon name="view_sidebar" />
          </button>
        </div>
        <div class="wf-code-editor__body">
          <EditorPanel
            :content="activeCodeTask.description || ''"
            :title="activeCodeTask.title"
            :read-only="false"
            edit-mode="code"
            :hide-header="true"
            :single-pane="true"
            @update:content="onCodeEditorUpdate"
            @open-split="openInEditorTab(activeCodeTask!)"
            @close="closeCodeEditor"
          />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import { EditorPanel } from "../../../skills";
import { useWorkflowStore, type WorkflowTask } from "../../../stores/workflow";
import { toTaskMarkdownLine } from "../../../utils/taskMarkdown";

const wf = useWorkflowStore();
const viewMode = ref<"list" | "kanban">("list");
const statuses = ["todo", "in-progress", "review", "blocked"];
const dragTaskId = ref<string | null>(null);
const dragFromStatus = ref<string | null>(null);
const dragError = ref<string | null>(null);

// ── Inline code editor state ──────────────────────────────────────
const showCodeEditor = ref(false);
const activeCodeTask = ref<WorkflowTask | null>(null);

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

const COLUMN_ICONS: Record<string, string> = {
  todo: "radio_button_unchecked",
  "in-progress": "play_circle",
  review: "rate_review",
  blocked: "block",
};

function columnIcon(status: string): string {
  return COLUMN_ICONS[status] || "circle";
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

// ── Inline code editor actions ──────────────────────────────────

/** Open the selected task in the inline code editor (single panel). */
function openTaskEditor(task: WorkflowTask) {
  activeCodeTask.value = task;
  wf.selectTask(task, false); // select without opening side-column editor
  showCodeEditor.value = true;
}

/** Close the inline code editor and return to task list. */
function closeCodeEditor() {
  showCodeEditor.value = false;
  activeCodeTask.value = null;
  wf.closeEditor();
}

/** Open the task in the full Editor tab (split view, hides task list). */
function openInEditorTab(task: WorkflowTask) {
  wf.selectTask(task, true); // select and open side-column editor
  showCodeEditor.value = false;
  activeCodeTask.value = null;
  wf.setTab("editor");
}

/** Update task description from inline code editor. */
function onCodeEditorUpdate(value: string) {
  if (activeCodeTask.value) {
    activeCodeTask.value.description = value;
  }
  wf.updateEditorContent(value);
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
/* ── Panel layout ───────────────────────────────────────────── */

.wf-panel {
  display: flex;
  flex-direction: row;
  gap: 0;
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.wf-panel__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  overflow-y: auto;
}

/* ── Slide-in code editor (from right) ──────────────────────── */

.wf-panel--editor-open .wf-panel__main {
  flex: 0 0 55%;
}

.wf-code-editor-slide {
  flex: 1;
  min-width: 320px;
  max-width: 560px;
  display: flex;
  flex-direction: column;
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-background);
  overflow: hidden;
  flex-shrink: 0;
}

.wf-code-editor__toolbar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  flex-shrink: 0;
}

.wf-code-editor__title {
  flex: 1;
  min-width: 0;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-code-editor__body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ── Slide transition ───────────────────────────────────────── */

.wf-slide-enter-active,
.wf-slide-leave-active {
  transition:
    width 0.25s ease,
    opacity 0.2s ease;
}

.wf-slide-enter-from,
.wf-slide-leave-to {
  width: 0 !important;
  min-width: 0;
  opacity: 0;
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

/* ── Compact toolbar ────────────────────────────────────────── */

.wf-toolbar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) 0;
}

.wf-toolbar__toggles {
  display: flex;
  gap: 2px;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  overflow: hidden;
}

.wf-toolbar__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: calc(var(--usx-touch-min) * 0.7);
  height: calc(var(--usx-touch-min) * 0.7);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  padding: 0;
  min-height: 0;
  border-radius: 0;
}

.wf-toolbar__btn:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 6%, transparent);
  color: var(--usx-color-on-surface);
}

.wf-toolbar__btn--active {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary, #fff);
}

.wf-toolbar__btn--active:hover {
  background: var(--usx-color-primary-hover, var(--usx-color-primary));
}

.wf-toolbar__count {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
}

.wf-toolbar__count--done {
  color: var(--usx-color-success);
}

.wf-flowlog-list {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
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

.task-list {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  overflow: hidden;
}

/* 2‑column task list on wide screens */
@media (min-width: 1100px) {
  .task-list {
    column-count: 2;
    column-gap: 0;
    column-rule: var(--usx-border-width) solid var(--usx-color-border);
  }

  .task-list__row {
    break-inside: avoid;
  }
}

.task-list__row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
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

.task-list__main {
  flex: 1;
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

/* ── Pills row (under task name) ────────────────────────────── */

.task-list__pills,
.kanban-card-pills {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  margin-top: var(--usx-spacing-xs);
}

.task-pill {
  display: inline-flex;
  align-items: center;
  padding: 1px var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  line-height: 1.4;
  white-space: nowrap;
  border: var(--usx-border-width) solid transparent;
}

/* Status colours */
.task-pill--todo {
  color: var(--usx-color-on-surface-muted);
  background: var(--usx-color-surface-variant);
}

.task-pill--in-progress {
  color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-primary) 25%, transparent);
}

.task-pill--review {
  color: var(--usx-color-warning);
  background: color-mix(in srgb, var(--usx-color-warning) 10%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-warning) 25%, transparent);
}

.task-pill--blocked {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-danger) 20%, transparent);
}

.task-pill--completed {
  color: var(--usx-color-success);
  background: color-mix(in srgb, var(--usx-color-success) 10%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-success) 25%, transparent);
}

/* Priority colours */
.task-pill--priority-high {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 6%, transparent);
}

.task-pill--priority-medium {
  color: var(--usx-color-warning);
  background: color-mix(in srgb, var(--usx-color-warning) 6%, transparent);
}

.task-pill--priority-low {
  color: var(--usx-color-on-surface-muted);
  background: var(--usx-color-surface-variant);
}

/* Neutral pills */
.task-pill--board {
  color: var(--usx-color-on-surface-muted);
  background: var(--usx-color-surface-variant);
}

.task-pill--tag {
  color: var(--usx-color-info);
  background: color-mix(in srgb, var(--usx-color-info) 8%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-info) 18%, transparent);
}

.kanban-board {
  --kanban-col-min: calc(var(--usx-touch-min) * 5.5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--kanban-col-min)), 1fr)
  );
  gap: var(--usx-spacing-md);
  align-items: start;
  min-width: 0;
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
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-sm);
  border-top-style: solid;
  border-top-width: calc(
    var(--usx-border-width) + var(--usx-border-width-thick)
  );
}

.kanban-column-header__label {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
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
  padding: var(--usx-spacing-sm) var(--usx-spacing-md) var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
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
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
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

@media (max-width: 1100px) {
  .task-list__row {
    padding: var(--usx-spacing-sm) var(--usx-spacing-sm);
  }
}

/* ── Editor buttons ─────────────────────────────────────────── */

.wf-editor-back-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
}

.wf-editor-back-btn:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.wf-editor-open-tab-btn,
.task-list__editor-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: calc(var(--usx-touch-min) * 0.75);
  height: calc(var(--usx-touch-min) * 0.75);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  padding: 0;
  min-height: 0;
}

.wf-editor-open-tab-btn:hover,
.task-list__editor-btn:hover {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}
</style>
