<template>
  <section class="wf-feeds">
    <header class="wf-feeds__header">
      <div>
        <h2>Feeds</h2>
        <p>Review useful signals, then turn only what matters into work.</p>
      </div>
      <UButton size="sm" variant="secondary" icon="refresh" :disabled="loading" @click="load">
        Refresh
      </UButton>
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

    <article v-for="item in activities" :key="item.id" class="wf-feed-card">
      <div class="wf-feed-card__body">
        <div class="wf-feed-card__meta">{{ item.source }} · {{ formatDate(item.timestamp) }}</div>
        <h3>{{ item.title || item.type }}</h3>
        <p>{{ preview(item.content) }}</p>
      </div>
      <UButton size="sm" variant="secondary" @click="toTask(item)">Add to tasks</UButton>
    </article>
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
    error.value = exc instanceof Error ? exc.message : "Feeds are unavailable.";
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
    error.value = "Could not add this item to Tasks.";
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
.wf-feeds { max-width: 60rem; margin: 0 auto; padding: var(--usx-spacing-lg); }
.wf-feeds__header { display: flex; justify-content: space-between; gap: var(--usx-spacing-md); align-items: start; }
.wf-feeds__header h2, .wf-feed-card h3 { margin: 0; }
.wf-feeds__header p { margin: var(--usx-spacing-xs) 0 0; color: var(--usx-color-on-surface-muted); }
.wf-feeds__sources { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-xs); margin: var(--usx-spacing-lg) 0; }
.wf-feeds__source { border: 0; border-radius: var(--usx-radius-full); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); cursor: pointer; }
.wf-feeds__source span { margin-left: var(--usx-spacing-xs); color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }
.wf-feeds__source--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.wf-feed-card { display: flex; align-items: center; gap: var(--usx-spacing-md); padding: var(--usx-spacing-md) 0; border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feed-card__body { min-width: 0; flex: 1; }
.wf-feed-card__meta { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); text-transform: capitalize; }
.wf-feed-card p { margin: var(--usx-spacing-xs) 0 0; color: var(--usx-color-on-surface-muted); }
.wf-feeds__notice, .wf-feeds__empty { padding: var(--usx-spacing-lg) 0; color: var(--usx-color-on-surface-muted); }
</style>
