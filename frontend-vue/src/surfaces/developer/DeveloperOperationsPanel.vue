<template>
  <section class="ops" aria-labelledby="developer-operations-title">
    <header class="ops__header">
      <div>
        <h2 id="developer-operations-title">Dev Mode Operations</h2>
        <p>Repository-scoped ACP actions. Write-capable work requires explicit approval.</p>
      </div>
      <UBadge :type="capabilities?.available ? 'success' : 'warning'" size="sm">
        {{ capabilities?.available ? "NanoCoder ready" : "NanoCoder unavailable" }}
      </UBadge>
    </header>

    <div class="ops__composer">
      <label for="developer-action">Action</label>
      <select id="developer-action" v-model="selectedAction">
        <option v-for="action in actions" :key="action.id" :value="action.id">
          {{ action.label }}{{ action.write ? " · approval required" : "" }}
        </option>
      </select>
      <label for="developer-prompt">Request</label>
      <textarea id="developer-prompt" v-model="prompt" rows="4" :placeholder="promptPlaceholder" />
      <div class="ops__context">
        <span><UIcon name="folder" /> {{ repository }}</span>
        <span v-if="file"><UIcon name="description" /> {{ file }}</span>
      </div>
      <p v-if="error" class="ops__error" role="alert">{{ error }}</p>
      <UButton :disabled="submitting || !prompt.trim() || !selectedAction" @click="submitOperation">
        <UIcon :name="selectedSpec?.write ? 'approval' : 'play_arrow'" />
        {{ selectedSpec?.write ? "Request approval" : "Run action" }}
      </UButton>
    </div>

    <div class="ops__history">
      <h3>Session activity</h3>
      <p v-if="!operations.length" class="ops__empty">No operations for this repository yet.</p>
      <article v-for="operation in operations" :key="operation.id" class="operation">
        <header>
          <strong>{{ operation.label }}</strong>
          <UBadge :type="statusType(operation.status)" size="sm">{{ operation.status.replaceAll('_', ' ') }}</UBadge>
        </header>
        <p>{{ operation.prompt }}</p>
        <div v-if="operation.status === 'awaiting_approval'" class="operation__controls">
          <UButton @click="decide(operation.id, 'approve')">Approve once</UButton>
          <UButton variant="ghost" @click="decide(operation.id, 'deny')">Deny</UButton>
        </div>
        <UButton v-else-if="['queued', 'running'].includes(operation.status)" variant="ghost" @click="cancel(operation.id)">
          Stop
        </UButton>
        <p v-if="operation.error" class="ops__error">{{ operation.error }}</p>
        <details v-if="operation.events.length">
          <summary>{{ operation.events.length }} event{{ operation.events.length === 1 ? '' : 's' }}</summary>
          <ol>
            <li v-for="(event, index) in operation.events" :key="index">
              {{ eventLabel(event) }}
            </li>
          </ol>
        </details>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import UButton from "../../skills/atoms/UButton.vue";
import UIcon from "../../skills/atoms/UIcon.vue";

interface ActionSpec { id: string; label: string; icon: string; write: boolean }
interface Capabilities { available: boolean; devMode: string; actions: ActionSpec[] }
interface OperationEvent { type?: string; status?: string; decision?: string; method?: string; update?: Record<string, unknown> }
interface Operation { id: string; label: string; prompt: string; status: string; events: OperationEvent[]; error?: string }

const props = defineProps<{ repository: string; file?: string }>();
const capabilities = ref<Capabilities | null>(null);
const operations = ref<Operation[]>([]);
const selectedAction = ref("");
const prompt = ref("");
const error = ref("");
const submitting = ref(false);
let pollTimer: ReturnType<typeof setInterval> | undefined;

const actions = computed(() => capabilities.value?.actions || []);
const selectedSpec = computed(() => actions.value.find((item) => item.id === selectedAction.value));
const promptPlaceholder = computed(() => selectedSpec.value?.id === "diagnose-failure" ? "Paste the bounded failure or diagnostic context…" : "Describe the outcome you want from this repository…");

async function loadCapabilities() {
  const response = await fetch("/api/developer/operations/capabilities");
  if (!response.ok) throw new Error("Developer operations are unavailable");
  capabilities.value = await response.json();
  selectedAction.value ||= capabilities.value?.actions[0]?.id || "";
}

async function loadOperations() {
  const response = await fetch(`/api/developer/operations?repository=${encodeURIComponent(props.repository)}`);
  if (response.ok) operations.value = (await response.json()).operations || [];
}

async function submitOperation() {
  submitting.value = true; error.value = "";
  try {
    const response = await fetch("/api/developer/operations", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: selectedAction.value, repository: props.repository, prompt: prompt.value,
        context: props.file ? { file: props.file } : {},
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Operation could not be created");
    prompt.value = "";
    await loadOperations();
  } catch (cause) { error.value = cause instanceof Error ? cause.message : "Operation failed"; }
  finally { submitting.value = false; }
}

async function decide(id: string, decision: "approve" | "deny") {
  await fetch(`/api/developer/operations/${id}/decision`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision }) });
  await loadOperations();
}

async function cancel(id: string) {
  await fetch(`/api/developer/operations/${id}/cancel`, { method: "POST" });
  await loadOperations();
}

function statusType(status: string): "success" | "warning" | "info" | "error" {
  if (status === "completed") return "success";
  if (["failed", "denied", "cancelled"].includes(status)) return "error";
  if (status === "awaiting_approval") return "warning";
  return "info";
}

function eventLabel(event: OperationEvent): string {
  if (event.type === "approval") return `Approval ${event.decision}`;
  if (event.type === "lifecycle") return `Status: ${event.status}`;
  const updateType = typeof event.update?.sessionUpdate === "string" ? event.update.sessionUpdate : "update";
  return `ACP ${updateType}`;
}

async function refresh() { try { await Promise.all([loadCapabilities(), loadOperations()]); } catch (cause) { error.value = cause instanceof Error ? cause.message : "Operations unavailable"; } }
watch(() => props.repository, refresh);
onMounted(() => { refresh(); pollTimer = setInterval(() => { if (operations.value.some((item) => ["queued", "running"].includes(item.status))) loadOperations(); }, 1500); });
onBeforeUnmount(() => { if (pollTimer) clearInterval(pollTimer); });
</script>

<style scoped>
.ops { display: grid; grid-template-columns: minmax(16rem, 24rem) minmax(18rem, 1fr); gap: var(--usx-spacing-md); }
.ops__header { grid-column: 1 / -1; display: flex; justify-content: space-between; gap: var(--usx-spacing-md); align-items: start; }
.ops__header h2, .ops__history h3 { margin: 0; }
.ops__header p, .operation p { color: var(--usx-color-on-surface-muted); }
.ops__composer, .operation { border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); background: var(--usx-color-surface); padding: var(--usx-spacing-md); }
.ops__composer { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); align-self: start; }
.ops__composer select, .ops__composer textarea { width: 100%; padding: var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); }
.ops__context, .operation header, .operation__controls { display: flex; align-items: center; gap: var(--usx-spacing-sm); flex-wrap: wrap; }
.ops__context { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.ops__history { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); min-width: 0; }
.operation header { justify-content: space-between; }
.operation details { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.ops__error { color: var(--usx-color-error, #d33) !important; }
.ops__empty { color: var(--usx-color-on-surface-muted); }
@media (max-width: 760px) { .ops { grid-template-columns: 1fr; } }
</style>
