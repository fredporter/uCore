<template>
  <aside class="review" aria-labelledby="review-title">
    <header><h3 id="review-title">Working tree</h3><button title="Refresh review" @click="load"><UIcon name="refresh" /></button></header>
    <p v-if="loading">Loading review…</p>
    <p v-else-if="!items.length" class="review__clean"><UIcon name="check_circle" /> Working tree clean</p>
    <ul v-else>
      <li v-for="item in items" :key="`${item.staged}-${item.file}`">
        <button class="review__file" @click="$emit('select', item.file)">
          <UBadge :type="item.staged ? 'success' : 'warning'" size="sm">{{ item.staged ? 'staged' : item.status }}</UBadge>
          <span>{{ item.file }}</span>
        </button>
        <button class="review__stage" :title="item.staged ? 'Unstage file' : 'Stage file'" @click="toggleStage(item)">
          <UIcon :name="item.staged ? 'remove' : 'add'" />
        </button>
      </li>
    </ul>
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
const props = defineProps<{ repository: string; revision?: number }>();
const emit = defineEmits<{ select: [path: string] }>();
const staged = ref<Omit<StatusItem, "staged">[]>([]);
const unstaged = ref<Omit<StatusItem, "staged">[]>([]);
const loading = ref(false);
const commitMessage = ref(""); const commitOutput = ref(""); const commitFailed = ref(false); const committing = ref(false);
const items = computed(() => [
  ...staged.value.map((item) => ({ ...item, staged: true })),
  ...unstaged.value.filter((item) => !staged.value.some((stagedItem) => stagedItem.file === item.file)).map((item) => ({ ...item, staged: false })),
]);
async function load() {
  if (!props.repository) return;
  loading.value = true;
  try {
    const response = await fetch(`/api/developer/repos/${encodeURIComponent(props.repository)}/status`);
    if (response.ok) { const data = await response.json(); staged.value = data.staged || []; unstaged.value = data.unstaged || []; }
  } finally { loading.value = false; }
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
.review li { display: flex; align-items: center; gap: var(--usx-spacing-xs); }
.review__file { min-width: 0; flex: 1; display: flex; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-xs); background: transparent; border: 0; color: var(--usx-color-on-surface); text-align: left; }
.review__file span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.review__clean, .review > p { display: flex; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); color: var(--usx-color-on-surface-muted); }
.review__commit { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); border-top: var(--usx-border-width) solid var(--usx-color-border); }
.review__commit textarea { resize: vertical; padding: var(--usx-spacing-xs); background: var(--usx-color-background); color: var(--usx-color-on-surface); border: var(--usx-border-width) solid var(--usx-color-border); }
.review__commit > button { padding: var(--usx-spacing-xs); border: var(--usx-border-width) solid var(--usx-color-primary); border-radius: var(--usx-radius-sm); background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.review__commit > button:disabled { opacity: .5; }.review__commit p { white-space: pre-wrap; overflow-wrap: anywhere; font-size: var(--usx-font-size-xs); }.review__error { color: var(--usx-color-danger); }
@media (max-width: 900px) { .review { width: 14rem; flex-basis: 14rem; } }
@media (max-width: 700px) { .review { display: none; } }
</style>
