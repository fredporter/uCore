<template>
  <aside class="review" aria-labelledby="review-title">
    <header><h3 id="review-title">Working tree</h3><button title="Refresh review" @click="load"><UIcon name="refresh" /></button></header>
    <p v-if="loading">Loading review…</p>
    <p v-else-if="!items.length" class="review__clean"><UIcon name="check_circle" /> Working tree clean</p>
    <ul v-else>
      <li v-for="item in items" :key="`${item.staged}-${item.file}`">
        <div class="review__file-row">
          <button class="review__file" @click="$emit('select', item.file)">
            <UBadge :type="item.staged ? 'success' : 'warning'" size="sm">{{ item.staged ? 'staged' : item.status }}</UBadge>
            <span>{{ item.file }}</span>
          </button>
          <button class="review__stage" :title="item.staged ? 'Unstage file' : 'Stage file'" @click="toggleStage(item)">
            <UIcon :name="item.staged ? 'remove' : 'add'" />
          </button>
        </div>
        <details v-if="!item.staged && diffFor(item)?.hunks.length" class="review__hunks">
          <summary>{{ diffFor(item)?.hunks.length }} hunk{{ diffFor(item)?.hunks.length === 1 ? '' : 's' }}</summary>
          <article v-for="hunk in diffFor(item)?.hunks" :key="hunk.index" class="review__hunk">
            <header><code>{{ hunk.header }}</code><button :disabled="stagingHunk === `${item.file}:${hunk.index}`" @click="stageHunk(item.file, hunk.index)">Stage hunk</button></header>
            <pre><code><span v-for="(line, index) in hunk.lines" :key="index" :class="lineClass(line)">{{ line }}
</span></code></pre>
          </article>
        </details>
      </li>
    </ul>
    <p v-if="reviewError" class="review__error" role="alert">{{ reviewError }}</p>
    <div class="review__commit">
      <label for="commit-message">Commit preparation</label>
      <textarea id="commit-message" v-model="commitMessage" rows="3" placeholder="Describe the staged change…" />
      <button :disabled="!staged.length || !commitMessage.trim() || committing" @click="commit">Commit {{ staged.length }} staged file{{ staged.length === 1 ? '' : 's' }}</button>
      <p v-if="commitOutput" :class="{ 'review__error': commitFailed }">{{ commitOutput }}</p>
    </div>
    <DeveloperActionsPanel :repository="repository" />
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import DeveloperActionsPanel from "./DeveloperActionsPanel.vue";

interface StatusItem { file: string; status: string; staged: boolean }
interface DiffHunk { index: number; header: string; lines: string[] }
interface FileDiff { path: string; status: string; fingerprint: string; hunks: DiffHunk[] }
const props = defineProps<{ repository: string; revision?: number }>();
const emit = defineEmits<{ select: [path: string] }>();
const staged = ref<Omit<StatusItem, "staged">[]>([]);
const unstaged = ref<Omit<StatusItem, "staged">[]>([]);
const loading = ref(false);
const diffs = ref<FileDiff[]>([]); const reviewError = ref(""); const stagingHunk = ref("");
const commitMessage = ref(""); const commitOutput = ref(""); const commitFailed = ref(false); const committing = ref(false);
const items = computed(() => [
  ...staged.value.map((item) => ({ ...item, staged: true })),
  ...unstaged.value.filter((item) => !staged.value.some((stagedItem) => stagedItem.file === item.file)).map((item) => ({ ...item, staged: false })),
]);
async function load() {
  if (!props.repository) return;
  loading.value = true;
  try {
    const root = `/api/developer/repos/${encodeURIComponent(props.repository)}`;
    const [statusResponse, diffResponse] = await Promise.all([fetch(`${root}/status`), fetch(`${root}/diffs`)]);
    if (statusResponse.ok) { const data = await statusResponse.json(); staged.value = data.staged || []; unstaged.value = data.unstaged || []; }
    if (diffResponse.ok) diffs.value = (await diffResponse.json()).files || [];
  } finally { loading.value = false; }
}
function diffFor(item: StatusItem) { return diffs.value.find((diff) => diff.path === item.file); }
function lineClass(line: string) { return line.startsWith("+") ? "review__added" : line.startsWith("-") ? "review__removed" : ""; }
async function stageHunk(path: string, hunkIndex: number) {
  const diff = diffs.value.find((item) => item.path === path); if (!diff) return;
  stagingHunk.value = `${path}:${hunkIndex}`; reviewError.value = "";
  try {
    const response = await fetch(`/api/developer/repos/${encodeURIComponent(props.repository)}/stage-hunk`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path, hunkIndex, fingerprint: diff.fingerprint }) });
    const data = await response.json(); if (!response.ok) throw new Error(data.error || "Hunk could not be staged");
  } catch (cause) { reviewError.value = cause instanceof Error ? cause.message : "Hunk could not be staged"; }
  finally { stagingHunk.value = ""; await load(); }
}
async function toggleStage(item: StatusItem) {
  const action = item.staged ? "unstage" : "stage";
  await fetch(`/api/developer/repos/${encodeURIComponent(props.repository)}/${action}?path=${encodeURIComponent(item.file)}`, { method: "POST" });
  await load();
}
async function commit() {
  committing.value = true; commitOutput.value = ""; commitFailed.value = false;
  try {
    const response = await fetch(`/api/developer/repos/${encodeURIComponent(props.repository)}/commit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: commitMessage.value }) });
    const data = await response.json(); commitFailed.value = !response.ok || !data.success; commitOutput.value = data.output || data.error || (data.success ? "Commit created." : "Nothing committed.");
    if (data.success) { commitMessage.value = ""; await load(); }
  } finally { committing.value = false; }
}
watch(() => [props.repository, props.revision], load);
onMounted(load);
</script>

<style scoped>
.review { width: 17rem; flex: 0 0 17rem; border-left: var(--usx-border-width) solid var(--usx-color-border); background: var(--usx-color-surface-variant); overflow-y: auto; }
.review header { display: flex; justify-content: space-between; align-items: center; padding: var(--usx-spacing-sm); border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.review h3 { margin: 0; font-size: var(--usx-font-size-sm); }
.review header button, .review__stage { border: 0; background: transparent; color: var(--usx-color-on-surface-muted); }
.review ul { list-style: none; margin: 0; padding: var(--usx-spacing-xs); }
.review li { display: block; border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.review__file-row { display: flex; align-items: center; gap: var(--usx-spacing-xs); }
.review__file { min-width: 0; flex: 1; display: flex; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-xs); background: transparent; border: 0; color: var(--usx-color-on-surface); text-align: left; }
.review__file span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.review__clean, .review > p { display: flex; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); color: var(--usx-color-on-surface-muted); }
.review__hunks { padding: 0 var(--usx-spacing-xs) var(--usx-spacing-xs); font-size: var(--usx-font-size-xs); }
.review__hunk { margin-top: var(--usx-spacing-xs); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); overflow: hidden; }
.review__hunk header { padding: var(--usx-spacing-xs); gap: var(--usx-spacing-xs); }.review__hunk header code { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.review__hunk header button { flex: 0 0 auto; }
.review__hunk pre { margin: 0; padding: var(--usx-spacing-xs); max-height: 12rem; overflow: auto; font-size: .68rem; background: var(--usx-color-background); }.review__hunk pre span { display: block; min-height: 1em; }.review__added { color: var(--usx-color-success); }.review__removed { color: var(--usx-color-danger); }
.review__commit { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); border-top: var(--usx-border-width) solid var(--usx-color-border); }
.review__commit textarea { resize: vertical; padding: var(--usx-spacing-xs); background: var(--usx-color-background); color: var(--usx-color-on-surface); border: var(--usx-border-width) solid var(--usx-color-border); }
.review__commit > button { padding: var(--usx-spacing-xs); border: var(--usx-border-width) solid var(--usx-color-primary); border-radius: var(--usx-radius-sm); background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.review__commit > button:disabled { opacity: .5; }.review__commit p { white-space: pre-wrap; overflow-wrap: anywhere; font-size: var(--usx-font-size-xs); }.review__error { color: var(--usx-color-danger); }
@media (max-width: 900px) { .review { width: 14rem; flex-basis: 14rem; } }
@media (max-width: 700px) { .review { display: none; } }
</style>
