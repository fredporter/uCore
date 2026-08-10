<template>
  <div class="ch-panel">
    <div class="usx-flex-between usx-mb-lg">
      <div>
        <h3 class="surface__panel-title">Combined History</h3>
        <p class="ch-muted">
          Chat history, action log, spool, feed, tasks — one unified view.
        </p>
      </div>
      <UButton variant="secondary" size="sm" icon="refresh" @click="refreshAll"
        >Refresh All</UButton
      >
    </div>

    <!-- Chat History -->
    <CollapsibleSection
      title="Chat History"
      :count="chatConversations.length"
      icon="chat"
      :default-open="true"
    >
      <div v-if="chatConversations.length === 0" class="ch-muted ch-empty">
        No chat conversations saved.
      </div>
      <div v-else class="ch-list">
        <div v-for="conv in chatConversations" :key="conv.id" class="ch-item">
          <div class="ch-item-head">
            <UIcon name="chat" />
            <span class="ch-item-title">{{ conv.title || "Untitled" }}</span>
            <UBadge type="info" size="sm"
              >{{ conv.messages?.length || 0 }} msg</UBadge
            >
            <span class="ch-muted ch-timestamp">{{
              formatDate(conv.updatedAt || conv.createdAt)
            }}</span>
          </div>
        </div>
      </div>
    </CollapsibleSection>

    <!-- Action History -->
    <CollapsibleSection
      title="Action History"
      :count="actionCount"
      icon="history"
    >
      <div class="usx-flex-between ch-action-bar">
        <span class="ch-muted">{{ actions.length }} actions</span>
        <UButton
          variant="secondary"
          size="sm"
          @click="takeSnapshot"
          :disabled="snapshotLoading"
        >
          {{ snapshotLoading ? "Taking..." : "Take Snapshot" }}
        </UButton>
      </div>
      <div v-if="actions.length === 0" class="ch-muted ch-empty">
        No actions recorded.
      </div>
      <div v-else class="ch-list">
        <div
          v-for="action in actions.slice(0, 20)"
          :key="action.id"
          class="ch-item"
        >
          <div class="ch-item-head">
            <UIcon :name="actionTypeIcon(action.action_type)" />
            <span class="ch-item-title">{{
              action.description || action.action_type
            }}</span>
            <UBadge
              :type="action.status === 'completed' ? 'success' : 'warning'"
              size="sm"
            >
              {{ action.status }}
            </UBadge>
            <span class="ch-muted ch-timestamp">{{
              formatDate(action.created_at || action.timestamp)
            }}</span>
          </div>
        </div>
      </div>
    </CollapsibleSection>

    <!-- Spool Logs -->
    <CollapsibleSection title="Spool Logs" :count="spoolTotal" icon="article">
      <div v-if="spoolEntries.length === 0" class="ch-muted ch-empty">
        No spool log entries.
      </div>
      <div v-else class="ch-list">
        <div
          v-for="entry in spoolEntries.slice(0, 20)"
          :key="entry.timestamp + entry.module"
          class="ch-item"
        >
          <div class="ch-item-head">
            <UBadge :type="spoolLevelBadge(entry.level)" size="sm">{{
              entry.level
            }}</UBadge>
            <span class="ch-item-title">{{ entry.module }}</span>
            <span class="ch-muted ch-message-trunc">{{ entry.message }}</span>
            <span class="ch-muted ch-timestamp">{{ entry.timestamp }}</span>
          </div>
        </div>
      </div>
    </CollapsibleSection>

    <!-- Task Backlog -->
    <CollapsibleSection
      title="Task Backlog"
      :count="taskTotal"
      icon="assignment"
    >
      <div v-if="taskTotal === 0" class="ch-muted ch-empty">
        No tasks in backlog.
      </div>
      <div v-else class="ch-list">
        <div v-for="task in tasks.slice(0, 20)" :key="task.id" class="ch-item">
          <div class="ch-item-head">
            <UIcon name="assignment" />
            <span class="ch-item-title">{{ task.title }}</span>
            <UBadge :type="taskStatusBadge(task.status)" size="sm">{{
              task.status
            }}</UBadge>
            <span class="ch-muted ch-timestamp">{{
              task.board || "no board"
            }}</span>
          </div>
        </div>
      </div>
    </CollapsibleSection>

    <!-- Feed / Activity -->
    <CollapsibleSection
      title="Feed Activity"
      :count="feedCount"
      icon="rss_feed"
    >
      <div v-if="feedItems.length === 0" class="ch-muted ch-empty">
        No feed activity.
      </div>
      <div v-else class="ch-list">
        <div
          v-for="item in feedItems.slice(0, 10)"
          :key="item.id"
          class="ch-item"
        >
          <div class="ch-item-head">
            <UIcon name="rss_feed" />
            <span class="ch-item-title">{{
              item.title || item.type || "Activity"
            }}</span>
            <span class="ch-muted ch-message-trunc">{{
              item.description || item.summary
            }}</span>
            <span class="ch-muted ch-timestamp">{{ item.timestamp }}</span>
          </div>
        </div>
      </div>
    </CollapsibleSection>

    <!-- Service Logs -->
    <CollapsibleSection
      title="Service Logs"
      :count="serviceLogs.length"
      icon="terminal"
    >
      <div v-if="serviceLogs.length === 0" class="ch-muted ch-empty">
        No service logs.
      </div>
      <div v-else class="ch-list">
        <div
          v-for="(log, i) in serviceLogs.slice(0, 30)"
          :key="i"
          class="ch-item"
        >
          <div class="ch-item-head">
            <span class="ch-level" :class="'ch-level--' + log.level">{{
              log.level
            }}</span>
            <span class="ch-item-title">{{ log.service }}</span>
            <span class="ch-muted ch-message-trunc">{{ log.message }}</span>
            <span class="ch-muted ch-timestamp">{{ log.timestamp }}</span>
          </div>
        </div>
      </div>
    </CollapsibleSection>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import CollapsibleSection from "../../../skills/molecules/CollapsibleSection.vue";
import { useSnackbarOpsStore } from "../../../stores/snackbarOps";

const srv = useSnackbarOpsStore();

// ── Data ─────────────────────────────────────────────────────────

interface ChatConv {
  id: string;
  title: string;
  messages: unknown[];
  createdAt: string;
  updatedAt: string;
}

interface HistAction {
  id: string;
  action_type: string;
  description: string;
  status: string;
  created_at: string;
  timestamp: string;
}

interface SpoolEntry {
  timestamp: string;
  level: string;
  module: string;
  message: string;
}

interface TaskEntry {
  id: string;
  title: string;
  status: string;
  board: string;
}

interface FeedEntry {
  id: string;
  title: string;
  type: string;
  description: string;
  summary: string;
  timestamp: string;
}

const chatConversations = ref<ChatConv[]>([]);
const actions = ref<HistAction[]>([]);
const actionCount = ref(0);
const spoolEntries = ref<SpoolEntry[]>([]);
const spoolTotal = ref(0);
const tasks = ref<TaskEntry[]>([]);
const taskTotal = ref(0);
const feedItems = ref<FeedEntry[]>([]);
const feedCount = ref(0);
const snapshotLoading = ref(false);

// Service logs from snackbarOpsStore
const serviceLogs = computed(() => srv.logs || []);

// ── Helpers ──────────────────────────────────────────────────────

function formatDate(iso: string): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso.slice(0, 16);
  }
}

function actionTypeIcon(type: string): string {
  const map: Record<string, string> = {
    file_edit: "edit",
    skill_run: "extension",
    snapshot: "camera",
    restore: "restore",
    undo: "undo",
    commit: "code",
  };
  return map[type] || "history";
}

function spoolLevelBadge(
  level: string,
): "error" | "warning" | "info" | "success" {
  if (level === "ERROR") return "error";
  if (level === "WARNING") return "warning";
  if (level === "INFO") return "info";
  return "success";
}

function taskStatusBadge(
  status: string,
): "success" | "warning" | "error" | "info" {
  if (status === "done" || status === "completed") return "success";
  if (status === "in-progress" || status === "wip") return "warning";
  if (status === "blocked") return "error";
  return "info";
}

// ── Fetches ──────────────────────────────────────────────────────

async function loadChatHistory() {
  try {
    const raw = localStorage.getItem("assistui-conversations");
    if (raw) {
      chatConversations.value = JSON.parse(raw);
    }
  } catch {
    chatConversations.value = [];
  }
}

async function loadActions() {
  try {
    const res = await fetch("/api/history/actions?limit=20");
    if (!res.ok) return;
    const data = await res.json();
    actions.value = (data?.actions || []).map((a: any) => ({
      ...a,
      created_at: a.created_at || a.timestamp || "",
    }));
    actionCount.value = data?.total || actions.value.length;
  } catch {
    // endpoint may not be available
  }
}

async function loadSpool() {
  try {
    const res = await fetch("/api/spool/feed?max=20");
    if (!res.ok) return;
    const data = await res.json();
    spoolEntries.value = data?.entries || data?.events || [];
    spoolTotal.value = data?.total || spoolEntries.value.length;
  } catch {
    // endpoint may not be available
  }
}

async function loadTasks() {
  try {
    const res = await fetch("/api/developer/tasker/tasks");
    if (!res.ok) return;
    const data = await res.json();
    tasks.value = (data?.tasks || []).map((t: any) => ({
      id: t.id || t.uid || "",
      title: t.title || t.name || "Untitled",
      status: t.status || "todo",
      board: t.board || "",
    }));
    taskTotal.value = data?.total || tasks.value.length;
  } catch {
    // endpoint may not be available
  }
}

async function loadFeed() {
  try {
    const res = await fetch("/api/feed/query?limit=10");
    if (!res.ok) return;
    const data = await res.json();
    feedItems.value = data?.items || data?.activities || [];
    feedCount.value = data?.total || feedItems.value.length;
  } catch {
    // endpoint may not be available
  }
}

async function takeSnapshot() {
  snapshotLoading.value = true;
  try {
    await fetch("/api/history/snapshot", { method: "POST" });
    await loadActions();
  } catch {
    // best-effort
  } finally {
    snapshotLoading.value = false;
  }
}

function refreshAll() {
  loadChatHistory();
  loadActions();
  loadSpool();
  loadTasks();
  loadFeed();
}

onMounted(refreshAll);
</script>

<style scoped>
.ch-panel {
  max-width: 900px;
  padding: var(--usx-spacing-xl);
}

.ch-muted {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.ch-empty {
  padding: var(--usx-spacing-md);
  text-align: center;
}

.ch-list {
  display: flex;
  flex-direction: column;
}

.ch-item {
  padding: var(--usx-spacing-sm) 0;
  border-bottom: 1px solid var(--usx-color-border);
}

.ch-item:last-child {
  border-bottom: none;
}

.ch-item-head {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  flex-wrap: wrap;
}

.ch-item-title {
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
  flex: 1;
  min-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ch-message-trunc {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 2;
}

.ch-timestamp {
  white-space: nowrap;
  font-size: var(--usx-font-size-xs);
  margin-left: auto;
  flex-shrink: 0;
}

.ch-level {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-bold);
  padding: 1px var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  flex-shrink: 0;
}

.ch-level--INFO {
  color: var(--usx-color-info);
  background: color-mix(in srgb, var(--usx-color-info) 10%, transparent);
}

.ch-level--WARNING {
  color: var(--usx-color-warning);
  background: color-mix(in srgb, var(--usx-color-warning) 10%, transparent);
}

.ch-level--ERROR {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 10%, transparent);
}

.ch-action-bar {
  padding: var(--usx-spacing-sm) 0;
}
</style>
