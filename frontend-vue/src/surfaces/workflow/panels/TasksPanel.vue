<template>
  <div class="wf-panel">
    <!-- ── Task list / kanban (always visible, shrinks when editor slides in) ── -->
    <div class="wf-panel__main wf-zen-surface">
      <header class="wf-unified-header">
        <div class="wf-unified-header__left">
          <p class="wf-standard-header__kicker">User Workflow</p>
          <div class="wf-unified-header__title-row">
            <h2 class="wf-unified-header__title">Tasks</h2>
            <div class="wf-unified-header__badges">
              <UBadge type="info" size="sm">{{ wf.activeTasks.length }} open</UBadge>
              <UBadge v-if="wf.inProgressCount > 0" type="warning" size="sm">{{ wf.inProgressCount }} in progress</UBadge>
              <UBadge v-if="pendingApprovals.length > 0" type="warning" size="sm">{{ pendingApprovals.length }} approvals</UBadge>
              <UBadge v-if="inboundItems.length > 0" type="info" size="sm">{{ inboundItems.length }} inbound</UBadge>
            </div>
          </div>
        </div>

        <div class="wf-unified-header__right" role="toolbar" aria-label="Task views and actions">
          <!-- View switcher segmented group -->
          <div class="wf-segmented-group">
            <button
              type="button"
              class="usx-btn wf-segmented-btn"
              :class="{ 'wf-segmented-btn--active': viewMode === 'kanban' }"
              title="Kanban view"
              @click="viewMode = 'kanban'"
            >
              <UIcon name="view_kanban" />
              <span>Kanban</span>
            </button>
            <button
              type="button"
              class="usx-btn wf-segmented-btn"
              :class="{ 'wf-segmented-btn--active': viewMode === 'list' }"
              title="Task rows"
              @click="viewMode = 'list'"
            >
              <UIcon name="table_rows" />
              <span>Rows</span>
            </button>
            <button
              type="button"
              class="usx-btn wf-segmented-btn"
              :class="{ 'wf-segmented-btn--active': viewMode === 'triage' }"
              title="Inbound Communications Triage"
              @click="loadInboundTriage(); viewMode = 'triage'"
            >
              <UIcon name="mark_email_unread" />
              <span>Inbox Triage</span>
            </button>
          </div>

          <!-- Actions -->
          <div class="wf-header-actions">
            <button
              class="usx-btn usx-btn--secondary"
              :disabled="syncingReminders"
              title="Sync enabled task connections"
              @click="triggerRemindersSync"
            >
              <UIcon :name="syncingReminders ? 'sync' : 'alarm'" :class="{ 'wf-spin': syncingReminders }" />
              <span class="wf-toolbar__btn-label">{{ syncingReminders ? "Syncing..." : "Sync connections" }}</span>
            </button>
            <button class="usx-btn usx-btn--primary" type="button" @click="newTask">
              <UIcon name="add" /> <span>New Task</span>
            </button>
          </div>
        </div>
      </header>

      <div v-if="syncFeedback" class="wf-feedback-banner font-mono">
        <UIcon name="info" /> {{ syncFeedback }}
      </div>

      <div v-if="wf.loading" class="wf-loading">
        <UIcon name="sync" /> Loading tasks...
      </div>

      <div v-if="wf.taskError" class="wf-error" role="alert">{{ wf.taskError }} <button class="usx-btn" @click="wf.fetchTasks()">Retry</button></div>
      <div v-if="dragError" class="wf-error">
        <UIcon name="error" /> {{ dragError }}
      </div>

      <div class="task-scope" role="toolbar" aria-label="Task filters">

        <label><span>Binder</span><span class="task-scope__select"><select :value="wf.activeBinderId" @change="wf.showList('', ($event.target as HTMLSelectElement).value)" aria-label="Task binder"><option value="">All binders</option><option v-for="binder in wf.binderChoices" :key="binder.id" :value="binder.id">{{ binder.title || binder.id }}</option></select><UIcon name="expand_more" /></span></label>
        <label><span>Show</span><span class="task-scope__select"><select v-model="completionFilter" aria-label="Task completion"><option value="active">Open</option><option value="done">Done</option><option value="all">All</option></select><UIcon name="expand_more" /></span></label>
        <button class="usx-btn" @click="newList"><UIcon name="add" /> New Binder</button>
        <button class="usx-btn" @click="addGroup"><UIcon name="create_new_folder" /> New group</button>
        <span>{{ visibleTasks.length }} tasks · {{ wf.scopedTasks.filter(task => task.status === 'completed').length }} done</span>
      </div>
      <div v-if="wf.binderChoices.length" class="task-destinations" aria-label="Move or copy to a Binder"><span>Move to Binder:</span><button v-for="binder in wf.binderChoices" :key="binder.id" class="usx-btn" @click="wf.showList('',binder.id)" @dragover.prevent @drop.prevent="dropInto($event, { binder: binder.id })">{{ binder.title || binder.id }}</button><small>Hold Option/Alt while dropping to copy.</small></div>

      <div v-if="viewMode === 'list'" class="task-list">
        <section v-for="group in taskGroups" :key="group.name" class="task-group" @dragover.prevent @drop.prevent="dropInto($event, { group: group.name === 'Ungrouped' ? '' : group.name })">
          <h3>{{ group.name }} <small>{{ group.tasks.length }}</small></h3>
          <p v-if="!group.tasks.length">Drop tasks here to group them.</p>
          <div v-for="task in group.tasks" :key="task.id" class="task-list__row" :class="{ 'task-list__row--selected': wf.selectedTask?.id === task.id }"
            draggable="true" @dragstart="wf.startTaskDrag($event, task)">
            <input type="checkbox" :checked="task.status === 'completed'" :aria-label="`Complete ${task.title}`" @change="changeTask(task, { status: task.status === 'completed' ? 'todo' : 'completed' })" />
            <button class="task-list__main usx-btn" @click="openTaskEditor(task)"><span class="task-list__copy"><strong>{{ task.title }}</strong><small>{{ wf.binders.find(binder => binder.id === task.binder)?.title || task.binder || "No Binder" }} · {{ formatStatus(task.status) }}</small></span></button>
            <select :value="task.status" :aria-label="`Status for ${task.title}`" @change="changeTask(task, { status: ($event.target as HTMLSelectElement).value })"><option v-if="!statuses.includes(task.status)" :value="task.status">{{ formatStatus(task.status) }}</option><option v-for="status in statuses" :key="status" :value="status">{{ formatStatus(status) }}</option></select>
            <select :value="task.binder || ''" :aria-label="`Binder for ${task.title}`" @change="changeTask(task, { binder: ($event.target as HTMLSelectElement).value })"><option value="">No binder</option><option v-for="binder in wf.binderChoices" :key="binder.id" :value="binder.id">{{ binder.title || binder.id }}</option></select>
            <button class="usx-btn" :aria-label="`Group ${task.title}`" @click="groupTask(task)"><UIcon name="workspaces" /></button>
            <button class="usx-btn" :aria-label="`Move ${task.title}`" @click="moveTask(task)"><UIcon name="drive_file_move" /></button>
            <button class="usx-btn" :aria-label="`Copy ${task.title}`" @click="copyTask(task)"><UIcon name="content_copy" /></button>
          </div>
        </section>
        <p v-if="!visibleTasks.length && !extraGroups.length">No tasks match this view.</p>
      </div>

      <div v-else-if="viewMode === 'kanban'" class="kanban-board">
        <div
          v-for="status in statuses"
          :key="status"
          class="kanban-column"
          @dragover.prevent
          @drop.prevent="dropInto($event, { status })"
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
              visibleByStatus[status]?.length || 0
            }}</UBadge>
          </div>
          <div class="kanban-cards">
            <div
              v-if="(visibleByStatus[status] || []).length === 0"
              class="kanban-empty"
            >
              No tasks
            </div>
            <div
              v-for="task in visibleByStatus[status] || []"
              :key="task.id"
              class="kanban-card"
              :class="{
                'kanban-card--selected': wf.selectedTask?.id === task.id,
              }"
              draggable="true"
              @dragstart="wf.startTaskDrag($event, task)"
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
                <span v-if="task.binder" class="task-pill task-pill--board">{{ wf.binders.find(binder => binder.id === task.binder)?.title || task.binder }}</span>
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

      <!-- ── Inbound Communications Triage View ── -->
      <div v-else-if="viewMode === 'triage'" class="wf-triage-view">
        <!-- Autonomous Approvals Section -->
        <section v-if="pendingApprovals.length > 0" class="wf-triage-section surface__panel">
          <div class="wf-triage-section__header">
            <div class="wf-triage-section__title">
              <UIcon name="gavel" />
              <h3>Needs approval</h3>
            </div>
            <UBadge type="warning" size="sm">{{ pendingApprovals.length }} Pending</UBadge>
          </div>
          <div class="wf-triage-list">
            <div v-for="task in pendingApprovals" :key="task.id" class="wf-triage-card wf-triage-card--approval">
              <div class="wf-triage-card__main">
                <div class="wf-triage-card__header">
                  <span class="wf-triage-card__badge wf-triage-card__badge--autonomous">Needs approval</span>
                  <span class="wf-triage-card__title">{{ task.title }}</span>
                </div>
                <p class="wf-triage-card__desc">{{ task.description || task.summary || 'Review this action before it runs.' }}</p>
                <div v-if="task.action_type" class="wf-triage-card__meta font-mono">
                  <span>Action: {{ task.action_type }}</span>
                </div>
              </div>
              <div class="wf-triage-card__actions">
                <button
                  type="button"
                  class="usx-btn usx-btn--sm usx-btn--primary"
                  @click="handleApproveTask(task)"
                >
                  <UIcon name="check" /> Approve
                </button>
                <button
                  type="button"
                  class="usx-btn usx-btn--sm usx-btn--secondary"
                  @click="handleRejectTask(task)"
                >
                  <UIcon name="close" /> Reject
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Inbound Communications Feed -->
        <section class="wf-triage-section surface__panel">
          <div class="wf-triage-section__header">
            <div class="wf-triage-section__title">
              <UIcon name="inbox" />
              <h3>Host Inbound Feed (Apple Mail & Messages)</h3>
            </div>
            <div class="wf-triage-section__actions">
              <button
                type="button"
                class="usx-btn usx-btn--sm"
                :disabled="loadingInbound"
                @click="loadInboundTriage"
              >
                <UIcon :name="loadingInbound ? 'sync' : 'refresh'" :class="{ 'wf-spin': loadingInbound }" />
                <span>Fetch Latest</span>
              </button>
            </div>
          </div>

          <div v-if="loadingInbound" class="wf-loading">
            <UIcon name="sync" class="wf-spin" /> Querying Apple Mail & Messages via JXA...
          </div>

          <div v-else-if="inboundItems.length === 0" class="wf-triage-empty">
            <UIcon name="mark_email_read" :size="40" />
            <p>All host communications are triaged. Zero pending messages.</p>
            <button type="button" class="usx-btn usx-btn--sm usx-btn--secondary" @click="loadInboundTriage">
              Check for New Messages
            </button>
          </div>

          <div v-else class="wf-triage-list">
            <div
              v-for="item in inboundItems"
              :key="item.id"
              class="wf-triage-card"
              :class="`wf-triage-card--${item.source}`"
            >
              <div class="wf-triage-card__main">
                <div class="wf-triage-card__header">
                  <span
                    class="wf-triage-card__badge"
                    :class="item.source === 'mail' ? 'wf-triage-card__badge--mail' : 'wf-triage-card__badge--imessage'"
                  >
                    <UIcon :name="item.source === 'mail' ? 'mail' : 'chat'" />
                    {{ item.source === 'mail' ? 'Apple Mail' : 'iMessage' }}
                  </span>
                  <span class="wf-triage-card__sender">{{ item.sender }}</span>
                  <span class="wf-triage-card__time font-mono">{{ item.timestamp }}</span>
                </div>
                <h4 v-if="item.subject" class="wf-triage-card__subject">{{ item.subject }}</h4>
                <p class="wf-triage-card__preview">{{ item.preview }}</p>
              </div>
              <div class="wf-triage-card__actions">
                <button
                  type="button"
                  class="usx-btn usx-btn--sm usx-btn--primary"
                  title="Extract action and add as Workflow Task"
                  @click="convertInboundToTask(item)"
                >
                  <UIcon name="add_task" /> Convert to Task
                </button>
                <template v-if="item.source === 'mail'">
                  <button
                    type="button"
                    class="usx-btn usx-btn--sm usx-btn--secondary"
                    title="Flag email in Apple Mail"
                    @click="flagMail(item)"
                  >
                    <UIcon name="flag" />
                  </button>
                  <button
                    type="button"
                    class="usx-btn usx-btn--sm usx-btn--secondary"
                    title="Archive email in Apple Mail"
                    @click="archiveMail(item)"
                  >
                    <UIcon name="archive" />
                  </button>
                </template>
              </div>
            </div>
          </div>
        </section>
      </div>


    </div>

    <!-- ── Slide-in code editor panel (from right) ── -->

  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import { useWorkflowStore, type WorkflowTask } from "../../../stores/workflow";
import { ucoreApi } from "../../../api/client";
import {
  approveTaskAction,
  syncAppleRemindersInbound,
  syncAppleRemindersOutbound,
  syncTaskReminders,
} from "../../browserui/ApiBridge";

const wf = useWorkflowStore();
const viewMode = ref<"list" | "kanban" | "triage">("list");
const statuses = ["todo", "in-progress", "review", "blocked", "completed"];
const dragError = ref<string | null>(null);

// ── Reminders & Autonomy state ────────────────────────────────────
const syncingReminders = ref(false);
const syncingSingleRem = ref(false);
const executingAction = ref(false);
const syncFeedback = ref<string | null>(null);

// ── Communications & Inbound Triage state ─────────────────────────
const inboundItems = ref<
  Array<{
    id: string;
    source: "mail" | "imessage";
    sender: string;
    subject?: string;
    preview: string;
    timestamp: string;
    raw?: any;
  }>
>([]);
const loadingInbound = ref(false);

const pendingApprovals = computed(() =>
  (wf.tasks || []).filter(
    (t) =>
      ["pending", "pending_approval"].includes(t.approval_status || "") ||
      (t.workflowType === "autonomous" && t.status === "in-progress"),
  ),
);

async function loadInboundTriage() {
  loadingInbound.value = true;
  try {
    const items: Array<{
      id: string;
      source: "mail" | "imessage";
      sender: string;
      subject?: string;
      preview: string;
      timestamp: string;
      raw?: any;
    }> = [];

    // 1. Fetch Apple Mail intake
    try {
      const mailRes: any = await ucoreApi.host.mailIntake({
        limit: 15,
        unread_only: false,
      });
      if (mailRes?.ok && Array.isArray(mailRes.items)) {
        for (const m of mailRes.items) {
          items.push({
            id: m.id || m.message_id || `mail-${Math.random()}`,
            source: "mail",
            sender: m.sender || m.from || "Apple Mail",
            subject: m.subject || "(No Subject)",
            preview: m.snippet || m.body || "",
            timestamp:
              m.date_received || m.timestamp || new Date().toLocaleTimeString(),
            raw: m,
          });
        }
      }
    } catch {
      // Ignored if host Apple Mail is unavailable
    }

    // 2. Fetch Apple Messages intake
    try {
      const msgRes: any = await ucoreApi.host.imessageIntake({ limit: 15 });
      if (msgRes?.ok && Array.isArray(msgRes.items)) {
        for (const msg of msgRes.items) {
          items.push({
            id: msg.id || `msg-${Math.random()}`,
            source: "imessage",
            sender: msg.sender || msg.handle || "iMessage Contact",
            preview: msg.text || msg.body || "",
            timestamp: msg.timestamp || new Date().toLocaleTimeString(),
            raw: msg,
          });
        }
      }
    } catch {
      // Ignored if host iMessage is unavailable
    }

    inboundItems.value = items;
  } finally {
    loadingInbound.value = false;
  }
}

async function convertInboundToTask(item: {
  id: string;
  source: "mail" | "imessage";
  sender: string;
  subject?: string;
  preview: string;
}) {
  try {
    const text = item.subject
      ? `${item.subject}: ${item.preview}`
      : item.preview;
    const res: any = await ucoreApi.workflow.actionToTask({
      text,
      source: item.source,
      source_ref: item.id,
      priority: "medium",
      sender: item.sender,
    });
    if (res?.ok) {
      syncFeedback.value = `Created task: "${res.task?.title || item.subject || "Inbound action"}"`;
      inboundItems.value = inboundItems.value.filter((i) => i.id !== item.id);
      await wf.fetchTasks();
    }
  } catch (err: any) {
    syncFeedback.value = `Error converting to task: ${err?.message || err}`;
  }
}

async function handleApproveTask(task: WorkflowTask) {
  try {
    const res: any = await ucoreApi.workflow.approveTask(task.id);
    if (res?.ok) {
      syncFeedback.value = `Approved action for: ${task.title}`;
      await wf.fetchTasks();
    }
  } catch (err: any) {
    syncFeedback.value = `Approval error: ${err?.message || err}`;
  }
}

async function handleRejectTask(task: WorkflowTask) {
  try {
    const res: any = await ucoreApi.workflow.rejectTask(
      task.id,
      "Rejected by user in inbox triage",
    );
    if (res?.ok) {
      syncFeedback.value = `Rejected task: ${task.title}`;
      await wf.fetchTasks();
    }
  } catch (err: any) {
    syncFeedback.value = `Rejection error: ${err?.message || err}`;
  }
}

async function flagMail(item: { id: string }) {
  try {
    await ucoreApi.host.mailFlag(item.id, 0);
    syncFeedback.value = "Flagged message in Apple Mail";
  } catch (err: any) {
    syncFeedback.value = `Flag error: ${err?.message || err}`;
  }
}

async function archiveMail(item: { id: string }) {
  try {
    await ucoreApi.host.mailArchive(item.id);
    inboundItems.value = inboundItems.value.filter((i) => i.id !== item.id);
    syncFeedback.value = "Archived message in Apple Mail";
  } catch (err: any) {
    syncFeedback.value = `Archive error: ${err?.message || err}`;
  }
}



const completionFilter = ref("active");
const extraGroups = ref<string[]>([]);
const visibleTasks = computed(() => wf.orderedContextTasks.filter(task => completionFilter.value === "all" || (completionFilter.value === "done" ? task.status === "completed" : !["completed", "superseded", "cancelled", "archived"].includes(task.status))));
const visibleByStatus = computed(() => Object.fromEntries(statuses.map(status => [status, visibleTasks.value.filter(task => task.status === status)])));
const taskGroups = computed(() => [...new Set([...visibleTasks.value.map(task => task.group || "Ungrouped"), ...extraGroups.value])].map(name => ({ name, tasks: visibleTasks.value.filter(task => (task.group || "Ungrouped") === name) })));
async function newList() { wf.binderCreateRequested = true; wf.setTab('mission-control'); }

function addGroup() { const name = window.prompt("Group name"); if (name?.trim()) extraGroups.value.push(name.trim()); }
async function newTask() {
  if (!wf.activeBinderId) { wf.binderCreateRequested = true; wf.setTab('mission-control'); return; }
  const title = window.prompt("Task title");
  if (!title?.trim()) return;
  try { await wf.createTask(title.trim()); }
  catch (error) { dragError.value = error instanceof Error ? error.message : "Could not create task"; }
}
async function changeTask(task: WorkflowTask, patch: { status?: string; board?: string; group?: string; binder?: string }) {
  dragError.value = null;
  try { await wf.patchTask(task.id, patch); }
  catch (error) { dragError.value = error instanceof Error ? error.message : "Could not update task"; }
}
async function groupTask(task: WorkflowTask) {
  const group = window.prompt("Group name (leave empty to ungroup)", task.group || "");
  if (group !== null) await changeTask(task, { group: group.trim() });
}
async function moveTask(task: WorkflowTask) {
  const board = window.prompt("Move to Binder ID", task.binder || "");
  if (board?.trim()) await changeTask(task, { binder: board.trim() });
}
async function copyTask(task: WorkflowTask) {
  const board = window.prompt("Copy to Binder ID", task.binder || "");
  if (!board?.trim()) return;
  try { await wf.duplicateTask(task.id, { binder: board.trim() }); }
  catch (error) { dragError.value = error instanceof Error ? error.message : "Could not copy task"; }
}
async function dropInto(event: DragEvent, destination: { board?: string; binder?: string; group?: string; status?: string }) {
  dragError.value = null;
  try { await wf.dropTask(event, { ...(wf.activeBinderId ? { binder: wf.activeBinderId } : {}), ...destination }); }
  catch (error) { dragError.value = error instanceof Error ? error.message : "Could not move task"; }
}

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

function openTaskEditor(task: WorkflowTask) { wf.openTask(task); }
function openInEditorTab(task: WorkflowTask) { wf.openTask(task); }

async function triggerRemindersSync() {
  syncingReminders.value = true;
  syncFeedback.value = null;
  try {
    const state = await fetch('/api/connections').then(response => { if (!response.ok) throw new Error('Connections unavailable'); return response.json(); });
    const connections = state.connections.filter((item: any) => item.config.enabled && item.config.collections.tasks);
    if (!connections.length) { syncFeedback.value = 'Choose Apple or Google lists in Settings → Connections.'; return; }
    const results = [];
    for (const item of connections) {
      const response = await fetch(`/api/connections/${item.id}/sync`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: '{}' });
      if (!response.ok) throw new Error('Connection sync failed');
      const result = await response.json();
      results.push(`${item.provider}: ${result.state}${result.error ? ' · ' + result.error : ''}`);
    }
    syncFeedback.value = results.join(' · ');
    await wf.fetchTasks();
  } catch (err: any) {
    syncFeedback.value = `Sync error: ${err?.message || "Unknown error"}`;
  } finally {
    syncingReminders.value = false;
    setTimeout(() => {
      syncFeedback.value = null;
    }, 5000);
  }
}

async function handleSyncTaskToReminders(task: WorkflowTask) {
  syncingSingleRem.value = true;
  try {
    await syncTaskReminders(task.id, {
      title: task.title,
      notes: task.description || "",
      due_date: task.due,
      list_name: task.binder || "uDos",
    });
    syncFeedback.value = `Pushed "${task.title}" to Apple Reminders`;
  } catch (err: any) {
    syncFeedback.value = `Reminders sync error: ${err?.message || "Failed"}`;
  } finally {
    syncingSingleRem.value = false;
    setTimeout(() => {
      syncFeedback.value = null;
    }, 5000);
  }
}

async function handleApproveAction(task: WorkflowTask) {
  executingAction.value = true;
  try {
    const res = await approveTaskAction(task.id, true);
    if (res.ok) {
      task.approval_status = "executed";
      syncFeedback.value = `Action executed successfully`;
    } else {
      syncFeedback.value = `Action failed: ${res.error || "Unknown error"}`;
    }
  } catch (err: any) {
    syncFeedback.value = `Action execution error: ${err?.message || "Failed"}`;
  } finally {
    executingAction.value = false;
    setTimeout(() => {
      syncFeedback.value = null;
    }, 5000);
  }
}
</script>

<style scoped>
.task-scope, .task-destinations { display: flex; flex-wrap: wrap; align-items: center; gap: var(--usx-spacing-sm); padding-block: var(--usx-spacing-sm); }
.task-scope label { display: flex; align-items: center; gap: var(--usx-spacing-xs); }
.task-group { min-height: 4rem; border-top: 1px solid var(--usx-color-border); padding: var(--usx-spacing-sm); }
.task-group h3 { font-size: var(--usx-font-size-base); }
.task-list__row { flex-wrap: wrap; }
.task-list__row > select { max-width: 10rem; }
.task-list__copy { display: flex; flex-direction: column; text-align: left; }
.task-list__row .task-list__main { justify-content: flex-start; flex: 1; }
.task-list__row small, .task-destinations small { color: var(--usx-color-on-surface-muted); }

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
  width: min(100%, 60rem);
  margin: 0 auto;
  padding: clamp(var(--usx-spacing-md), 3vw, var(--usx-spacing-xl));
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
}

.wf-toolbar__btn--active {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
}

.wf-toolbar__count {
  flex: 1;
  min-width: 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  text-align: right;
}

.wf-toolbar__count--done {
  color: var(--usx-color-success);
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
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
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
  display: grid;
  border-top: var(--usx-border-width) solid var(--usx-color-border);
}

.wf-flowlog__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-xs) var(--usx-spacing-sm);
}

.wf-flowlog__header .surface__panel-title,
.wf-flowlog__header .surface__panel-description { margin: 0; }
.wf-flowlog__header .surface__panel-description { margin-top: 2px; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }
.wf-flowlog__count { color: var(--usx-color-success); font-size: var(--usx-font-size-xs); white-space: nowrap; }

.wf-flowlog-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--usx-spacing-xs);
  width: 100%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-xs);
  border: 0;
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.wf-flowlog-item__title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.wf-flowlog-item__copy { display: grid; min-width: 0; gap: 2px; }
.wf-flowlog-item__status { display: inline-flex; align-items: center; justify-content: center; color: var(--usx-color-success); }

.wf-flowlog-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.wf-flowlog {
  padding: var(--usx-spacing-lg) 0 0;
  border: 0;
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: 0;
  background: transparent;
}

.wf-flowlog .surface__panel-title,
.wf-flowlog .surface__panel-description { margin-left: var(--usx-spacing-xs); margin-right: var(--usx-spacing-xs); }

.task-list {
  border: 0;
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: 0;
  background: transparent;
  overflow: visible;
}

.wf-flowlog-list {
  grid-template-columns: minmax(0, 1fr);
  gap: var(--usx-spacing-sm);
  border-top: 0;
}

.wf-flowlog-item {
  min-height: 4rem;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: color-mix(in srgb, var(--usx-color-surface) 72%, transparent);
}

@media (max-width: 600px) {
  .wf-flowlog-list { grid-template-columns: 1fr; }
  .wf-flowlog__header { align-items: flex-start; }
}


.task-list__row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-height: 3.25rem;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
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
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  flex: 1;
  min-width: 0;
}

.task-list__state { width: .7rem; height: .7rem; flex: 0 0 auto; border: 2px solid var(--usx-color-border); border-radius: 50%; }
.task-list__state--in-progress { border-color: var(--usx-color-primary); background: var(--usx-color-primary); }
.task-list__state--review { border-color: var(--usx-color-warning); }
.task-list__state--blocked { border-color: var(--usx-color-danger); }
.task-list__meta { margin-top: 2px; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }

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

.task-pill--priority-high,
.task-pill--priority-medium,
.task-pill--priority-low,
.task-pill--tag {
  display: none;
}

/* Neutral pills */
.task-pill--board {
  color: var(--usx-color-on-surface-muted);
  background: transparent;
  padding-inline: 0;
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
  background: transparent;
  border-radius: 0;
  border: 0;
  border-top: var(--usx-border-width) solid var(--usx-color-border);
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
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  cursor: pointer;
  min-width: 0;
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    box-shadow var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.kanban-card:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 5%, transparent);
}

.kanban-card--selected {
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.kanban-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
}

.kanban-card-title {
  min-width: 0;
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-sm);
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

.wf-toolbar__actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-2, 0.5rem);
}

.wf-toolbar__sync-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1, 0.25rem);
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  border-radius: var(--usx-radius-sm, 4px);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  cursor: pointer;
}

.wf-toolbar__sync-btn:hover:not(:disabled) {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}

.wf-feedback-banner {
  display: flex;
  align-items: center;
  gap: var(--space-2, 0.5rem);
  padding: 0.35rem 0.75rem;
  margin-bottom: var(--space-2, 0.5rem);
  font-size: 0.75rem;
  border-radius: var(--usx-radius-sm, 4px);
  background: color-mix(in srgb, #10b981 12%, transparent);
  color: #10b981;
  border: 1px solid color-mix(in srgb, #10b981 30%, transparent);
}

.wf-code-editor__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2, 0.5rem);
}

.wf-btn-action-approve {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--usx-radius-sm, 4px);
  border: 1px solid #10b981;
  background: #10b981;
  color: #ffffff;
  cursor: pointer;
}

.wf-btn-action-approve:hover:not(:disabled) {
  background: #059669;
}

.wf-action-executed-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: var(--usx-radius-sm, 4px);
  background: color-mix(in srgb, #10b981 15%, transparent);
  color: #10b981;
}

.wf-editor-sync-rem-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: calc(var(--usx-touch-min) * 0.75);
  height: calc(var(--usx-touch-min) * 0.75);
  border-radius: var(--usx-radius-sm, 4px);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  padding: 0;
}

.wf-editor-sync-rem-btn:hover:not(:disabled) {
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
}

.wf-spin {
  animation: wf-spin 1s linear infinite;
}

@keyframes wf-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── Unified Tasks Header ───────────────────── */

.wf-unified-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-wrap: wrap;
}

.wf-unified-header__left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.wf-unified-header__title-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.wf-unified-header__title {
  margin: 0;
  font-size: var(--usx-font-size-lg);
  font-weight: 600;
  color: var(--usx-color-on-surface);
}

.wf-unified-header__badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.wf-unified-header__right {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  flex-wrap: wrap;
}

.wf-segmented-group {
  display: inline-flex;
  align-items: center;
  padding: 2px;
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  gap: 2px;
}

.wf-segmented-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 0.25rem 0.6rem;
  font-size: var(--usx-font-size-xs);
  font-weight: 500;
  border: none;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.wf-segmented-btn:hover {
  color: var(--usx-color-on-surface);
  background: color-mix(in srgb, var(--usx-color-surface) 60%, transparent);
}

.wf-segmented-btn--active {
  background: var(--usx-color-surface);
  color: var(--usx-color-primary);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.wf-header-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

/* ── Inbound Communications Triage View ─────────────────────── */

.wf-triage-view {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
  padding: var(--usx-spacing-md);
  overflow-y: auto;
}

.wf-triage-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-lg);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
}

.wf-triage-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  padding-bottom: var(--usx-spacing-xs);
}

.wf-triage-section__title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.wf-triage-section__title h3 {
  margin: 0;
  font-size: var(--usx-font-size-md);
  font-weight: 600;
  color: var(--usx-color-on-surface);
}

.wf-triage-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-triage-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  transition: border-color 0.15s ease;
}

.wf-triage-card:hover {
  border-color: var(--usx-color-primary);
}

.wf-triage-card--approval {
  border-left: 3px solid var(--usx-color-warning);
}

.wf-triage-card--mail {
  border-left: 3px solid var(--usx-color-info);
}

.wf-triage-card--imessage {
  border-left: 3px solid var(--usx-color-success);
}

.wf-triage-card__main {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
  min-width: 0;
}

.wf-triage-card__header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.wf-triage-card__badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.1rem 0.4rem;
  border-radius: var(--usx-radius-sm);
}

.wf-triage-card__badge--autonomous {
  background: color-mix(in srgb, var(--usx-color-warning) 15%, transparent);
  color: var(--usx-color-warning);
}

.wf-triage-card__badge--mail {
  background: color-mix(in srgb, var(--usx-color-info) 15%, transparent);
  color: var(--usx-color-info);
}

.wf-triage-card__badge--imessage {
  background: color-mix(in srgb, var(--usx-color-success) 15%, transparent);
  color: var(--usx-color-success);
}

.wf-triage-card__sender {
  font-weight: 600;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
}

.wf-triage-card__time {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.wf-triage-card__title {
  font-weight: 600;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
}

.wf-triage-card__subject {
  margin: 0.15rem 0 0 0;
  font-size: var(--usx-font-size-sm);
  font-weight: 500;
  color: var(--usx-color-on-surface);
}

.wf-triage-card__desc,
.wf-triage-card__preview {
  margin: 0.15rem 0 0 0;
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  line-height: 1.4;
  word-break: break-word;
}

.wf-triage-card__meta {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  margin-top: 0.2rem;
}

.wf-triage-card__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
}

.wf-triage-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xl);
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}
</style>

<style scoped>
.task-scope { display: flex; align-items: center; flex-wrap: nowrap; gap: 8px; overflow-x: auto; min-height: 44px; padding: 6px 0; box-sizing: border-box; white-space: nowrap; font-family: var(--usx-font-family-sans, Inter, sans-serif); font-size: var(--usx-font-size-sm); line-height: 1; }
.task-scope > * { flex: 0 0 auto; margin: 0; }
.task-scope label { display: inline-flex; align-items: center; gap: 6px; min-height: 0; height: 32px; padding: 0; margin: 0; font: inherit; color: var(--usx-color-on-surface-muted); }
.task-scope__select { display: inline-flex; position: relative; align-items: center; height: 32px; }
.task-scope select { appearance: none; box-sizing: border-box; width: auto; max-width: 9rem; height: 32px; min-height: 32px; margin: 0; padding: 0 26px 0 8px; border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); box-shadow: none; font: inherit; line-height: normal; }
.task-scope__select :deep(.u-icon) { position: absolute; right: 5px; width: 16px; height: 16px; font-size: 16px; line-height: 1; pointer-events: none; }
.task-scope .usx-btn { display: inline-flex; align-items: center; justify-content: center; gap: 4px; box-sizing: border-box; height: 32px; min-height: 32px; margin: 0; padding: 0 8px; border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: transparent; box-shadow: none; font: inherit; line-height: 1; }
.task-scope .usx-btn :deep(.u-icon) { width: 18px; height: 18px; font-size: 18px; line-height: 1; }
.task-scope select:focus-visible, .task-scope .usx-btn:focus-visible { outline: 2px solid var(--usx-color-primary); outline-offset: -2px; }
.task-scope > span { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }

/* Compact action row: shared dimensions prevent global button defaults adding height. */
.wf-unified-header__right { flex-wrap: nowrap; gap: var(--usx-spacing-xs); max-width: 100%; min-width: 0; overflow-x: auto; padding-block: 2px; }
.wf-segmented-group, .wf-header-actions { flex: 0 0 auto; gap: 4px; }
.wf-segmented-group { padding: 0; border: 0; background: transparent; }
.wf-unified-header__right button { display: inline-flex; align-items: center; justify-content: center; gap: 4px; box-sizing: border-box; height: 36px; min-height: 36px; margin: 0; padding: 0 8px; font-size: var(--usx-font-size-sm); line-height: 1; white-space: nowrap; }
.wf-unified-header__right :deep(.u-icon) { font-size: 20px; width: 20px; height: 20px; line-height: 1; }
</style>
