<template>
  <section class="wf-feeds wf-zen-surface">
    <header class="wf-feeds__header">
      <div>
        <p class="wf-standard-header__kicker">User Workflow</p>
        <h2>Feeds</h2>
        <p>Review useful signals, then turn only what matters into work.</p>
      </div>
      <div class="wf-feeds__actions">
        <button class="usx-btn wf-standard-header__action" type="button" :disabled="loading" @click="load"><UIcon name="refresh" /> Refresh</button>
        <UButton
          size="sm"
          variant="secondary"
          :disabled="applyingRules || ruleProposalCount === 0"
          @click="applyRules"
        >
          {{ applyingRules ? 'Applying…' : `Apply ${ruleProposalCount} rule ${ruleProposalCount === 1 ? 'proposal' : 'proposals'}` }}
        </UButton>
      </div>
    </header>

    <section class="feed-monitor"><header><h3>Monitored connections</h3><button class="usx-btn" @click="router.push('/system?tab=connections')">Manage connections</button></header><p v-if="!connections.length">Choose source lists or groups in Connections. Flags and stars can then select items or trigger rules.</p><article v-for="connection in connections" :key="connection.id"><span>{{ connection.health.account || connection.provider }} · {{ connection.health.state }}</span><small v-for="(scope,kind) in connection.config.collections" :key="kind">{{ kind }}: {{ scope.lists.length }} lists · {{ scope.direction === 'both' ? 'in + out' : 'in' }} · {{ connection.config.enabled ? 'monitored' : 'paused' }}</small><button class="usx-btn" :disabled="syncing || !connection.config.enabled" @click="syncConnection(connection)">Sync</button></article></section>
    <div class="wf-feeds__sources" aria-label="Feed sources">
      <button
        v-for="source in sources"
        :key="source.id"
        class="usx-btn wf-feeds__source"
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

    <details class="feed-import">
      <summary>Import a saved RSS item</summary>
      <form @submit.prevent="importRss">
        <label>
          RSS item or pilot fixture JSON file
          <input ref="rssInput" type="file" accept=".json,application/json"
            :disabled="importing" @change="rssFile = ($event.target as HTMLInputElement).files?.[0] || null" />
        </label>
        <button type="submit" class="usx-btn" :disabled="!rssFile || importing">
          <UIcon name="upload_file" aria-hidden="true" /> {{ importing ? "Importing…" : "Import for review" }}
        </button>
      </form>
    </details>
    <p v-if="error" class="wf-feeds__notice" role="alert">{{ error }}</p>
    <p v-if="importedItem" class="feed-operation-result" role="status">
      {{ importedItem.processed
        ? `Updated feed item ${importedItem.id}, which had already been reviewed.`
        : `Imported feed item ${importedItem.id} for review.` }}
      <span v-if="importedItem.receipt">Spool receipt {{ importedItem.receipt }}</span>
    </p>
    <p v-if="route.query.binder">
      Adding tasks to {{ wf.binders.find(binder => binder.id === route.query.binder)?.title || route.query.binder }}.
      <RouterLink v-if="route.query.mission" :to="{ path: '/workflow', query: { tab: 'queue', binder: route.query.binder, mission: route.query.mission } }">Open mission queue</RouterLink>
    </p>
    <p v-if="promotedTask" class="feed-operation-result" role="status">
      {{ promotedTask.existing ? "Task already exists." : "Task created." }}
      <RouterLink v-if="loadedTask" :to="{ path: '/workflow', query: { tab: 'editor', task: loadedTask.id, binder: loadedTask.binder || undefined, mission: loadedTask.mission || undefined } }">Open task</RouterLink>
      <button v-else-if="!promoting" type="button" class="usx-btn" :disabled="refreshingTask" @click="loadPromotedTask">
        <UIcon name="refresh" aria-hidden="true" /> {{ refreshingTask ? "Loading task…" : "Retry loading task" }}
      </button>
      <span v-if="promotedTask.receipt">Spool receipt {{ promotedTask.receipt }}</span>
    </p>
    <div v-if="selectedActivity" class="feed-binder-intake">
      <strong>{{ selectedActivity.title || selectedActivity.type }}</strong>
      <label>
        Destination Binder
        <select v-model="destinationBinder" :disabled="sending">
          <option value="" disabled>Choose a Binder</option>
          <option v-for="binder in wf.binders" :key="binder.id" :value="binder.id">
            {{ binder.title || binder.id }}
          </option>
        </select>
      </label>
      <div class="feed-binder-intake__actions">
        <button type="button" class="usx-btn" :disabled="sending || !destinationBinder" @click="sendToBinder">
          <UIcon name="note_add" aria-hidden="true" /> Save Markdown
        </button>
        <button type="button" class="usx-btn" :disabled="sending" @click="selectedActivity = null">Cancel</button>
      </div>
      <p v-if="!wf.binders.length"><RouterLink to="/workflow?tab=binder">Open Binders</RouterLink> to create a destination.</p>
    </div>
    <p v-if="binderNotice" role="status">
      {{ binderNotice }}
      <RouterLink :to="{ path: '/workflow', query: { tab: 'binder', binder: savedBinder } }">Open Binder</RouterLink>
    </p>
    <div v-if="!loading && activities.length === 0" class="wf-feeds__empty">
      No feed items yet. Sync a source when you are ready.
    </div>

    <article v-if="viewedRecord" class="feed-detail"><header><h3>{{ viewedRecord.data.title }}</h3><button class="usx-btn" @click="viewedRecord=null">Close details</button></header><p v-if="viewedRecord.data.sender">{{ viewedRecord.data.sender }}</p><p v-if="viewedRecord.data.start">{{ viewedRecord.data.start.dateTime || viewedRecord.data.start.date }}</p><p>{{ viewedRecord.data.body }}</p></article>
    <div class="wf-feed-list">
      <article v-for="item in activities" :key="item.id" class="wf-feed-row">
        <button class="usx-btn wf-feed-row__main" :title="preview(item.content)" @click="openFeedRecord(item)">
          <span class="wf-feed-row__state" />
          <div class="wf-feed-row__copy">
            <h3>{{ item.title || item.type }}</h3>
            <div class="wf-feed-card__meta">{{ item.source }} · {{ formatDate(item.timestamp) }}</div>
          </div>
        </button>
        <div class="feed-row-actions">
          <button class="usx-btn" type="button" title="Send to Binder" aria-label="Send to Binder"
            :disabled="sending" @click="chooseBinder(item)"><UIcon name="book" aria-hidden="true" /></button>
          <button class="usx-btn" type="button" title="Add to tasks" aria-label="Add to tasks"
            :disabled="promoting || refreshingTask" @click="toTask(item)"><UIcon name="add_task" aria-hidden="true" /></button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { UCORE_BASE } from "../../../api/base";
import { useWorkflowStore } from "../../../stores/workflow";
import { useRoute, useRouter } from "vue-router";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UButton from "../../../skills/atoms/UButton.vue";

interface Activity { metadata?: string | Record<string,any>; id: number; source: string; type: string; title: string; content: string; timestamp: string }
interface Source { id: string; label: string; state: string; available: boolean }

const wf = useWorkflowStore();
const activities = ref<Activity[]>([]);
const sources = ref<Source[]>([]);
const connections = ref<any[]>([]);
const router = useRouter();
const route = useRoute();
const viewedRecord = ref<any>(null);
const filter = ref("");
const loading = ref(false);
const syncing = ref(false);
const applyingRules = ref(false);
const ruleProposalCount = ref(0);
const error = ref("");
const selectedActivity = ref<Activity | null>(null);
const destinationBinder = ref("");
const savedBinder = ref("");
const binderNotice = ref("");
const sending = ref(false);
const promoting = ref(false);
const promotedTask = ref<{ id: string; existing: boolean; receipt?: string } | null>(null);
const loadedTask = computed(() => wf.tasks.find(task => task.id === promotedTask.value?.id));
const refreshingTask = ref(false);
const rssInput = ref<HTMLInputElement | null>(null);
const rssFile = ref<File | null>(null);
const importing = ref(false);
const importedItem = ref<{ id: number; processed: boolean; receipt?: string } | null>(null);

async function importRss() {
  const file = rssFile.value;
  if (!file || importing.value) return;
  importing.value = true;
  error.value = "";
  importedItem.value = null;
  try {
    if (file.size > 2 * 1024 * 1024) throw new Error("Choose a JSON file under 2 MiB.");
    const saved = JSON.parse(await file.text());
    const item = saved?.rss_item ?? saved;
    const guid = item?.guid ?? item?.external_id;
    const summary = item?.summary ?? item?.content;
    if (typeof guid !== "string" || !guid.trim() ||
        ![item?.title, summary].some(value => typeof value === "string" && value.trim())) {
      throw new Error("The file must contain one RSS item with a GUID and a title or summary.");
    }
    const response = await fetch(`${UCORE_BASE}/api/feed/rss`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        guid, title: item.title, summary, url: item.url, topic: item.topic,
        provenance: item.provenance, waypoint_ref: item.waypoint_ref, review_only: true,
      }),
    });
    const result = await response.json().catch(() => null);
    if (!response.ok || typeof result?.activity_id !== "number") {
      throw new Error(result?.error || "Could not import the RSS item.");
    }
    importedItem.value = {
      id: result.activity_id, processed: result.processed === true, receipt: result.spool_receipt,
    };
    rssFile.value = null;
    if (rssInput.value) rssInput.value.value = "";
    filter.value = "";
    await load();
  } catch (exc) {
    error.value = exc instanceof SyntaxError ? "Choose a valid RSS item JSON file."
      : exc instanceof Error ? exc.message : "Could not import the RSS item.";
  } finally {
    importing.value = false;
  }
}

async function chooseBinder(item: Activity) {
  error.value = "";
  binderNotice.value = "";
  selectedActivity.value = item;
  destinationBinder.value = "";
  try {
    await wf.fetchBinders(true);
    if (selectedActivity.value === item && wf.binders.some(binder => binder.id === wf.activeBinderId)) {
      destinationBinder.value = wf.activeBinderId;
    }
  } catch {
    error.value = "Could not load Binders.";
  }
}

async function sendToBinder() {
  if (!selectedActivity.value || !destinationBinder.value || sending.value) return;
  sending.value = true;
  error.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/feed/send-to-binder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activity_id: selectedActivity.value.id, binder: destinationBinder.value }),
    });
    if (!response.ok) {
      const result = await response.json().catch(() => null);
      throw new Error(result?.error || "Could not save to Binder.");
    }
    const result = await response.json();
    savedBinder.value = result.binder;
    binderNotice.value = result.duplicate ? "This revision is already in the Binder." : "Markdown saved to Binder.";
    selectedActivity.value = null;
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : "Could not save to Binder.";
  } finally {
    sending.value = false;
  }
}

const DEFAULT_SOURCES: Source[] = [
  { id: "research", label: "Research", state: "local", available: true },
  { id: "vault", label: "Vault changes", state: "local", available: true },
  { id: "workflow", label: "Workflow", state: "local", available: true },
];
const selectedSource = computed(() => sources.value.find((source) => source.id === filter.value));

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const suffix = filter.value ? `&source=${encodeURIComponent(filter.value)}` : "";
    const [feedRes, sourceRes, rulesRes, connectionRes] = await Promise.all([
      fetch(`${UCORE_BASE}/api/feed/query?limit=50&processed=false${suffix}`),
      fetch(`${UCORE_BASE}/api/feed/sources`),
      fetch(`${UCORE_BASE}/api/feed/rules`),
      fetch(`${UCORE_BASE}/api/connections`),
    ]);
    if (!feedRes.ok) throw new Error("Feeds are unavailable.");
    if (connectionRes.ok) connections.value = (await connectionRes.json()).connections;
    activities.value = (await feedRes.json()).activities || [];
    if (sourceRes.ok) sources.value = (await sourceRes.json()).sources || [];
    if(route.query.record){const response=await fetch(`${UCORE_BASE}/api/connections/records?id=${encodeURIComponent(String(route.query.record))}`);if(response.ok)viewedRecord.value=(await response.json()).records[0] || null;}
    ruleProposalCount.value = rulesRes.ok ? Number((await rulesRes.json()).count || 0) : 0;
  } catch (exc) {
    sources.value = [...DEFAULT_SOURCES];
    activities.value = [];
    error.value = exc instanceof Error ? exc.message : "Feeds are unavailable";
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
  if (promoting.value || refreshingTask.value) return;
  promoting.value = true;
  error.value = "";
  promotedTask.value = null;
  const binder = String(route.query.binder || "");
  const mission = typeof route.query.mission === "string" ? route.query.mission : undefined;
  try {
    const response = await fetch(`${UCORE_BASE}/api/feed/promote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ activity_id: item.id, binder, mission }),
    });
    const result = await response.json().catch(() => null);
    if (!response.ok || typeof result?.task_id !== "string") throw new Error(result?.error || "Task could not be saved.");
    activities.value = activities.value.filter(candidate => candidate.id !== item.id);
    promotedTask.value = {
      id: result.task_id,
      existing: result.existing === true,
      receipt: result.spool_receipt,
    };
    await loadPromotedTask();
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : "Task could not be saved.";
  } finally {
    promoting.value = false;
  }
}
async function loadPromotedTask() {
  if (refreshingTask.value) return;
  refreshingTask.value = true;
  error.value = "";
  try {
    await wf.fetchTasks(true);
    if (!loadedTask.value) throw new Error("Task saved. The task list could not load it yet.");
  } catch {
    error.value = "Task saved. The task list could not load it yet.";
  } finally {
    refreshingTask.value = false;
  }
}
async function syncConnection(connection:any){syncing.value=true;try{const response=await fetch(`${UCORE_BASE}/api/connections/${connection.id}/sync`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const result=await response.json();if(!response.ok||result.state==='error')throw new Error(result.error||'Connection sync failed');await load();}catch(exc){error.value=exc instanceof Error?exc.message:'Sync unavailable';}finally{syncing.value=false;}}

async function openFeedRecord(item:Activity){try{const meta=typeof item.metadata==='string'?JSON.parse(item.metadata):item.metadata||{};if(meta.collection_id){const response=await fetch(`${UCORE_BASE}/api/connections/records?id=${encodeURIComponent(meta.collection_id)}`);if(!response.ok)throw Error('Record unavailable');viewedRecord.value=(await response.json()).records[0];}else viewedRecord.value={data:{title:item.title,body:item.content}};}catch(exc){error.value=exc instanceof Error?exc.message:'Record unavailable';}}
function preview(value: string) { return (value || "No preview").replace(/\s+/g, " ").slice(0, 220); }
function formatDate(value: string) { return value ? new Date(value).toLocaleString() : "Now"; }
onMounted(load);
</script>

<style scoped>
.feed-import form {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: var(--usx-spacing-sm);
}
.feed-import label {
  display: grid;
  min-width: 0;
  gap: var(--usx-spacing-xs);
}
.feed-import input {
  max-width: 100%;
}
.feed-operation-result {
  overflow-wrap: anywhere;
}
.feed-operation-result span {
  display: block;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}
.feed-row-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
  min-width: 0;
}
.feed-binder-intake {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: var(--usx-spacing-sm);
}
.feed-binder-intake > strong,
.feed-binder-intake > p {
  grid-column: 1 / -1;
  margin: 0;
  overflow-wrap: anywhere;
}
.feed-binder-intake > label {
  display: grid;
  min-width: 0;
  gap: var(--usx-spacing-xs);
  margin: 0;
}
.feed-binder-intake select,
.feed-binder-intake__actions .usx-btn {
  box-sizing: border-box;
  min-height: max(44px, var(--usx-touch-min));
  margin: 0;
}
.feed-binder-intake select {
  width: 100%;
  min-width: 0;
}
.feed-binder-intake select:focus {
  box-shadow: none;
  border-color: var(--usx-color-border);
  outline: 2px solid var(--usx-color-primary);
  outline-offset: 2px;
}
.feed-binder-intake__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--usx-spacing-xs);
}
@media (max-width: 640px) {
  .feed-binder-intake {
    grid-template-columns: minmax(0, 1fr);
  }
}
.feed-row-actions .usx-btn { margin: 0; }

.wf-feeds { max-width: var(--usx-prose-width); margin: 0 auto; padding: clamp(var(--usx-spacing-md), 4vw, var(--usx-spacing-2xl)); }
.wf-feeds__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
}
.wf-feeds__header > :first-child { flex: 1 1 17rem; min-width: 0; }
.wf-feeds__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--usx-spacing-xs);
  max-width: 100%;
}
.wf-feeds__actions > .usx-btn { max-width: 100%; margin: 0; white-space: normal; }
.wf-feeds__header h2, .wf-feed-card h3 { margin: 0; }
.wf-feeds__header p { margin: var(--usx-spacing-xs) 0 0; color: var(--usx-color-on-surface-muted); }
.wf-feeds__sources { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 8.5rem), 1fr)); gap: var(--usx-spacing-xs); margin: var(--usx-spacing-sm) 0; padding-block: var(--usx-spacing-sm); border-block: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feeds__source { display: flex; align-items: center; justify-content: center; min-width: 0; min-height: var(--usx-control-size-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-full); padding: 0 var(--usx-spacing-sm); background: transparent; color: var(--usx-color-on-surface); cursor: pointer; font-size: var(--usx-font-size-xs); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wf-feeds__source span { margin-left: var(--usx-spacing-xs); color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }
.wf-feeds__source--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.wf-feed-list { border-top: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feed-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  min-height: var(--wf-zen-row);
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}
.wf-feed-row__main.usx-btn {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  min-width: 0;
  height: auto;
  gap: var(--usx-spacing-sm);
  margin: 0;
  padding: var(--usx-spacing-xs) 0;
  border: 0;
  background: transparent;
  text-align: left;
  white-space: normal;
  box-shadow: none;
}
.wf-feed-row__state { width: .7rem; height: .7rem; flex: 0 0 auto; border: 2px solid var(--usx-color-primary); border-radius: 50%; }
.wf-feed-row__copy {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  flex: 1;
  min-width: 0;
  gap: 2px;
}
.wf-feed-row__copy h3 {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-tight);
  overflow-wrap: anywhere;
}
.wf-feed-card__meta { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-feed-card { display: flex; align-items: center; gap: var(--usx-spacing-md); min-height: 4rem; padding: var(--usx-spacing-md) 0; border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.wf-feed-card__body { min-width: 0; flex: 1; }
.wf-feed-card__meta { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); text-transform: capitalize; }
.wf-feed-card p { margin: var(--usx-spacing-xs) 0 0; color: var(--usx-color-on-surface-muted); }
.wf-feeds__notice, .wf-feeds__empty { padding: var(--usx-spacing-sm) 0; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }

.feed-monitor { display:grid; gap:8px; padding:12px 0; font-size:var(--usx-font-size-sm); }.feed-monitor header,.feed-monitor article{display:flex;align-items:center;flex-wrap:wrap;gap:8px;}.feed-monitor small{color:var(--usx-color-on-surface-muted);}.feed-monitor .usx-btn{min-height:32px;margin:0;padding:4px 8px;font-size:inherit;}

.feed-detail { display:grid;gap:8px;padding:12px;border:1px solid var(--usx-color-border); }.feed-detail header {display:flex;align-items:center;justify-content:space-between;gap:8px;}.feed-detail p{white-space:pre-wrap;overflow-wrap:anywhere;}
</style>
