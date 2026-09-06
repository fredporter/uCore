<template>
  <section class="actions" aria-labelledby="actions-title">
    <header><h3 id="actions-title">Checks</h3><button title="Refresh actions" @click="refresh"><UIcon name="refresh" /></button></header>
    <div class="actions__buttons">
      <button v-for="action in actions" :key="action.id" :disabled="running" @click="run(action.id)"><UIcon name="play_arrow" />{{ action.label }}</button>
      <span v-if="!actions.length">No approved repository scripts.</span>
    </div>
    <article v-if="latest" class="actions__run">
      <div><strong>{{ latest.action }}</strong><UBadge :type="statusType(latest.status)" size="sm">{{ latest.status }}</UBadge><span>{{ latest.durationSeconds ?? 0 }}s</span></div>
      <button v-if="['queued','running'].includes(latest.status)" @click="cancel(latest.id)">Stop</button>
      <pre v-if="latest.output">{{ latest.output }}</pre>
      <p v-if="latest.error">{{ latest.error }}</p>
      <small>Audit: developer-actions.jsonl</small>
    </article>
    <nav aria-label="Related authorities">
      <RouterLink to="/workflow?tab=tasks"><UIcon name="task_alt" /> uFlow tasks</RouterLink>
      <RouterLink to="/snackbar?tab=automation"><UIcon name="automation" /> Server Automations &amp; Skills</RouterLink>
    </nav>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import UBadge from "../../skills/atoms/UBadge.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
interface Action { id: string; label: string }
interface Run { id: string; action: string; status: string; durationSeconds?: number; output: string; error?: string }
const props = defineProps<{ repository: string }>();
const actions = ref<Action[]>([]); const runs = ref<Run[]>([]); let timer: ReturnType<typeof setInterval> | undefined;
const latest = computed(() => runs.value[0]); const running = computed(() => runs.value.some((item) => ["queued","running"].includes(item.status)));
async function refresh() {
  if (!props.repository) return;
  const [actionResponse, runsResponse] = await Promise.all([
    fetch(`/api/developer/repos/${encodeURIComponent(props.repository)}/actions`),
    fetch(`/api/developer/command-runs?repository=${encodeURIComponent(props.repository)}`),
  ]);
  if (actionResponse.ok) actions.value = (await actionResponse.json()).actions || [];
  if (runsResponse.ok) runs.value = (await runsResponse.json()).runs || [];
}
async function run(action: string) { await fetch(`/api/developer/repos/${encodeURIComponent(props.repository)}/actions/run`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({action,timeout:300}) }); await refresh(); }
async function cancel(id: string) { await fetch(`/api/developer/command-runs/${id}/cancel`, {method:"POST"}); await refresh(); }
function statusType(status:string): "success"|"warning"|"info"|"error" { if(status==="passed")return "success"; if(["failed","timed_out","cancelled"].includes(status))return "error"; return "info"; }
watch(() => props.repository, refresh); onMounted(() => { refresh(); timer=setInterval(() => {if(running.value)refresh();},1000);}); onBeforeUnmount(() => {if(timer)clearInterval(timer);});
</script>

<style scoped>
.actions { border-top: var(--usx-border-width) solid var(--usx-color-border); }.actions header,.actions__run>div { display:flex;align-items:center;justify-content:space-between;gap:var(--usx-spacing-xs);padding:var(--usx-spacing-sm); }.actions h3{margin:0;font-size:var(--usx-font-size-sm)}.actions header button{border:0;background:transparent;color:var(--usx-color-on-surface-muted)}.actions__buttons{display:flex;flex-wrap:wrap;gap:var(--usx-spacing-xs);padding:0 var(--usx-spacing-sm) var(--usx-spacing-sm)}.actions__buttons button,.actions__run>button{display:inline-flex;align-items:center;gap:var(--usx-spacing-xs);padding:var(--usx-spacing-xs);border:var(--usx-border-width) solid var(--usx-color-border);background:var(--usx-color-surface);color:var(--usx-color-on-surface);border-radius:var(--usx-radius-sm)}.actions__run{padding:var(--usx-spacing-xs);}.actions__run pre{max-height:14rem;overflow:auto;white-space:pre-wrap;font-size:var(--usx-font-size-xs);background:var(--usx-color-background);padding:var(--usx-spacing-xs)}.actions__run p{color:var(--usx-color-danger)}.actions nav{display:flex;flex-direction:column;gap:var(--usx-spacing-xs);padding:var(--usx-spacing-sm);border-top:var(--usx-border-width) solid var(--usx-color-border)}.actions nav a{display:flex;align-items:center;gap:var(--usx-spacing-xs);color:var(--usx-color-primary);font-size:var(--usx-font-size-xs)}
</style>
