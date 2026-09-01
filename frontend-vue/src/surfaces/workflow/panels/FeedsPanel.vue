<template>
  <section class="wf-feeds wf-zen-surface">
    <header class="wf-feeds__header">
      <div>
        <p class="wf-standard-header__kicker">User Workflow</p>
        <h2>Feeds</h2>
        <p>Review useful signals, then turn only what matters into work.</p>
      </div>
      <button class="wf-standard-header__action" type="button" :disabled="loading" @click="load"><span class="material-symbols-outlined">refresh</span> Refresh</button>
      <UButton
        size="sm"
        variant="secondary"
        :disabled="applyingRules || ruleProposalCount === 0"
        @click="applyRules"
      >
        {{ applyingRules ? 'Applying…' : `Apply ${ruleProposalCount} rule ${ruleProposalCount === 1 ? 'proposal' : 'proposals'}` }}
      </UButton>
    </header>

    <div class="wf-feeds__sources" aria-label="Feed sources">
      <button
        v-for="source in sources"
        :key="source.id"
        class="wf-feeds__source"
        :class="{ 'wf-feeds__source--active': filter === source.id }"
        @click="filter = filter === source.id ? '' : source.id; load()"
      >
        {{ source.label }}
        <span v-if="source.state === 'planned'">Planned</span>
      </button>
    </div>
    <UButton
      v-if="selectedSource?.available"
      size="sm"
      variant="secondary"
      :disabled="syncing"
      @click="syncSelected"
    >
      {{ syncing ? 'Syncing…' : `Sync ${selectedSource.label}` }}
    </UButton>

    <p v-if="error" class="wf-feeds__notice">{{ error }}</p>
    <div v-if="!loading && activities.length === 0" class="wf-feeds__empty">
      No feed items yet. Sync a source when you are ready.
    </div>

    <div class="wf-feed-list">
      <article v-for="item in activities" :key="item.id" class="wf-feed-row">
        <div class="wf-feed-row__main" :title="preview(item.content)">
          <span class="wf-feed-row__state" />
          <div class="wf-feed-row__copy">
            <h3>{{ item.title || item.type }}</h3>
            <div class="wf-feed-card__meta">{{ item.source }} · {{ formatDate(item.timestamp) }}</div>
          </div>
        </div>
        <button class="wf-canonical-action" type="button" title="Add to tasks" @click="toTask(item)"><span class="material-symbols-outlined">add_task</span></button>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { UCORE_BASE } from "../../../api/base";
import { useWorkflowStore } from "../../../stores/workflow";
import UButton from "../../../skills/atoms/UButton.vue";

interface Activity { id: number; source: string; type: string; title: string; content: string; timestamp: string }
interface Source { id: string; label: string; state: string; available: boolean }

const wf = useWorkflowStore();
const activities = ref<Activity[]>([]);
const sources = ref<Source[]>([]);
const filter = ref("");
const loading = ref(false);
const syncing = ref(false);
const applyingRules = ref(false);
const ruleProposalCount = ref(0);
const error = ref("");
const DEFAULT_SOURCES: Source[] = [
  { id: "research", label: "Research", state: "local", available: true },
  { id: "vault", label: "Vault changes", state: "local", available: true },
  { id: "workflow", label: "Workflow", state: "local", available: true },
];
const DEFAULT_ACTIVITIES: Activity[] = [
  { id: -1, source: "research", type: "signal", title: "Review saved research", content: "Revisit recently collected topics and promote only useful findings into a Binder.", timestamp: new Date().toISOString() },
  { id: -2, source: "vault", type: "change", title: "New vault notes", content: "Summarise recent notes and connect them to an active mission or task.", timestamp: new Date().toISOString() },
  { id: -3, source: "workflow", type: "review", title: "Weekly workflow review", content: "Check blocked and in-progress work before choosing the next action.", timestamp: new Date().toISOString() },
];
const selectedSource = computed(() => sources.value.find((source) => source.id === filter.value));

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const suffix = filter.value ? `&source=${encodeURIComponent(filter.value)}` : "";
    const [feedRes, sourceRes, rulesRes] = await Promise.all([
      fetch(`${UCORE_BASE}/api/feed/query?limit=50&processed=false${suffix}`),
      fetch(`${UCORE_BASE}/api/feed/sources`),
      fetch(`${UCORE_BASE}/api/feed/rules`),
    ]);
    if (!feedRes.ok) throw new Error("Feeds are unavailable.");
    activities.value = (await feedRes.json()).activities || [];
    if (sourceRes.ok) sources.value = (await sourceRes.json()).sources || [];
    ruleProposalCount.value = rulesRes.ok ? Number((await rulesRes.json()).count || 0) : 0;
  } catch (exc) {
    sources.value = [...DEFAULT_SOURCES];
    activities.value = DEFAULT_ACTIVITIES.filter((item) => !filter.value || item.source === filter.value);
    error.value = "Using local feeds";
  } finally {
    loading.value = false;
  }
}

async function syncSelected() {
  if (!selectedSource.value?.available) return;
  syncing.value = true;
  error.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/feed/sources/${encodeURIComponent(selectedSource.value.id)}/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit: 50 }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Source sync failed.");
    await load();
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : "Source sync failed.";
  } finally {
    syncing.value = false;
  }
}

async function applyRules() {
  applyingRules.value = true;
  error.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/feed/rules/apply`, { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Rules could not be applied.");
    ruleProposalCount.value = 0;
    await Promise.all([load(), wf.fetchTasks()]);
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : "Rules could not be applied.";
  } finally {
    applyingRules.value = false;
  }
}

async function toTask(item: Activity) {
  const response = await fetch(`${UCORE_BASE}/api/feed/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ activity_id: item.id, priority: "medium", binder: "Sandbox" }),
  });
  if (!response.ok) {
    wf.tasks.push({
      id: `feed-${Math.abs(item.id)}-${Date.now()}`,
      title: item.title,
      description: item.content,
      status: "todo",
      priority: "medium",
      board: "inbox",
      tags: ["feed", item.source],
    });
    activities.value = activities.value.filter((candidate) => candidate.id !== item.id);
    error.value = "Added to local Tasks";
    return;
  }
  await wf.fetchTasks();
  activities.value = activities.value.filter((candidate) => candidate.id !== item.id);
}

function preview(value: string) { return (value || "No preview").replace(/\s+/g, " ").slice(0, 220); }
function formatDate(value: string) { return value ? new Date(value).toLocaleString() : "Now"; }
onMounted(load);
</script>

<style scoped>
.wf-feeds { max-width: var(--usx-prose-width); margin: 0 auto; padding: clamp(var(--usx-spacing-md), 4vw, var(--usx-spacing-2xl)); }
.wf-feeds__header { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: var(--usx-spacing-sm); align-items: start; }
.wf-feeds__header h2, .wf-feed-card h3 { margin: 0; }
.wf-feeds__header p { margin: var(--usx-spacing-xs) 0 0; color: var(--usx-color-on-surface-muted); }
.wf-feeds__sources { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 8.5rem), 1fr)); gap: var(--usx-spacing-xs); margin: var(--usx-spacing-sm) 0; padding-block: var(--usx-spacing-sm); border-block: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feeds__source { display: flex; align-items: center; justify-content: center; min-width: 0; min-height: var(--usx-control-size-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-full); padding: 0 var(--usx-spacing-sm); background: transparent; color: var(--usx-color-on-surface); cursor: pointer; font-size: var(--usx-font-size-xs); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wf-feeds__source span { margin-left: var(--usx-spacing-xs); color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }
.wf-feeds__source--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.wf-feed-list { border-top: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feed-row { display: flex; align-items: center; box-sizing: border-box; width: 100%; height: var(--wf-zen-row); min-height: var(--wf-zen-row); gap: var(--usx-spacing-sm); margin: 0; padding: var(--usx-spacing-xs) var(--usx-spacing-sm); border: 0; border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feed-row__main { display: flex; align-items: center; flex: 1; min-width: 0; gap: var(--usx-spacing-sm); }
.wf-feed-row__state { width: .7rem; height: .7rem; flex: 0 0 auto; border: 2px solid var(--usx-color-primary); border-radius: 50%; }
.wf-feed-row__copy { display: grid; min-width: 0; gap: 2px; }
.wf-feed-row__copy h3, .wf-feed-card__meta { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-feed-card { display: flex; align-items: center; gap: var(--usx-spacing-md); min-height: 4rem; padding: var(--usx-spacing-md) 0; border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feed-card__body { min-width: 0; flex: 1; }
.wf-feed-card__meta { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); text-transform: capitalize; }
.wf-feed-card p { margin: var(--usx-spacing-xs) 0 0; color: var(--usx-color-on-surface-muted); }
.wf-feeds__notice, .wf-feeds__empty { padding: var(--usx-spacing-sm) 0; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
@media (max-width: 640px) { .wf-feeds__header { grid-template-columns: 1fr auto; } .wf-feeds__header > :last-child { grid-column: 1 / -1; } }
</style>
