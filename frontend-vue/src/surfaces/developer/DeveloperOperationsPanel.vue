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
      <label for="developer-task-reference">uFlow task reference <span class="ops__optional">optional</span></label>
      <input id="developer-task-reference" v-model="taskReference" placeholder="Task ID or stable reference" />
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
        <p v-if="operation.context?.taskReference" class="operation__task"><UIcon name="task_alt" /> {{ operation.context.taskReference }}</p>
        <div v-if="operation.status === 'awaiting_approval'" class="operation__controls">
          <UButton @click="decide(operation.id, 'approve')">Approve once</UButton>
          <UButton variant="ghost" @click="decide(operation.id, 'deny')">Deny</UButton>
        </div>
        <UButton v-else-if="['queued', 'running'].includes(operation.status)" variant="ghost" @click="cancel(operation.id)">
          Stop
        </UButton>
        <p v-if="operation.error" class="ops__error">{{ operation.error }}</p>
        <section v-if="operation.proposal?.files.length" class="operation__proposal" aria-label="Proposed changes">
          <h4>Proposed changes</h4>
          <p>Generated in an isolated workspace. Apply each reviewed file explicitly.</p>
          <details v-for="fileProposal in operation.proposal.files" :key="fileProposal.fingerprint">
            <summary>{{ fileProposal.path }}{{ fileProposal.applied ? " · applied" : "" }}</summary>
            <pre>{{ fileProposal.patch }}</pre>
            <UButton
              :disabled="fileProposal.applied || operation.status !== 'completed'"
              @click="applyProposal(operation.id, fileProposal)"
            >
              {{ fileProposal.applied ? "Applied" : "Apply proposed file" }}
            </UButton>
          </details>
        </section>
        <details v-if="operation.events.length">
          <summary>{{ operation.events.length }} event{{ operation.events.length === 1 ? '' : 's' }}</summary>
          <ol class="operation__events">
            <li v-for="(event, index) in operation.events" :key="index" :class="`operation__event operation__event--${eventCard(event).kind}`">
              <UIcon :name="eventCard(event).icon" />
              <span><strong>{{ eventCard(event).title }}</strong><small v-if="eventCard(event).detail">{{ eventCard(event).detail }}</small></span>
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
interface ProposalFile { path: string; patch: string; fingerprint: string; applied: boolean }
interface Operation { id: string; label: string; prompt: string; status: string; context?: Record<string, string>; events: OperationEvent[]; error?: string; proposal?: { fingerprint: string; files: ProposalFile[] } }

const props = defineProps<{ repository: string; file?: string }>();
const capabilities = ref<Capabilities | null>(null);
const operations = ref<Operation[]>([]);
const selectedAction = ref("");
const prompt = ref("");
const taskReference = ref("");
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
        context: {
          ...(props.file ? { file: props.file } : {}),
          ...(taskReference.value.trim() ? { taskReference: taskReference.value.trim() } : {}),
        },
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

async function applyProposal(id: string, fileProposal: ProposalFile) {
  error.value = "";
  try {
    const response = await fetch(`/api/developer/operations/${id}/proposal/apply`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: fileProposal.path, fingerprint: fileProposal.fingerprint }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Proposal could not be applied");
    await loadOperations();
  } catch (cause) { error.value = cause instanceof Error ? cause.message : "Proposal could not be applied"; }
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

function eventCard(event: OperationEvent) {
  if (event.type === "approval") return { kind: "approval", icon: "approval", title: eventLabel(event), detail: "" };
  if (event.type === "lifecycle") return { kind: "lifecycle", icon: event.status === "completed" ? "check_circle" : "sync", title: eventLabel(event), detail: "" };
  const updateType = typeof event.update?.sessionUpdate === "string" ? event.update.sessionUpdate : "update";
  const normalized = updateType.toLowerCase();
  const kind = normalized.includes("plan") ? "plan" : normalized.includes("tool") ? "tool" : normalized.includes("diff") || normalized.includes("patch") ? "diff" : "message";
  const icon = { plan: "checklist", tool: "build", diff: "difference", message: "notes" }[kind];
  const detailSource = event.update?.content ?? event.update?.message ?? event.update?.title ?? event.update?.path ?? "";
  const detail = typeof detailSource === "string" ? detailSource.slice(0, 500) : "";
  return { kind, icon, title: `ACP ${updateType.replaceAll("_", " ")}`, detail };
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
.ops__composer select, .ops__composer textarea, .ops__composer input { width: 100%; padding: var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); }
.ops__optional { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }
.ops__context, .operation header, .operation__controls { display: flex; align-items: center; gap: var(--usx-spacing-sm); flex-wrap: wrap; }
.ops__context { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.ops__history { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); min-width: 0; }
.operation header { justify-content: space-between; }
.operation details { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.operation__task { display: flex; align-items: center; gap: var(--usx-spacing-xs); font-size: var(--usx-font-size-xs); }
.operation__events { display: grid; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-xs); list-style: none; }.operation__event { display: flex; align-items: flex-start; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-xs); border-left: 3px solid var(--usx-color-border); background: var(--usx-color-surface-variant); }.operation__event span { display: grid; min-width: 0; }.operation__event small { margin-top: .15rem; white-space: pre-wrap; overflow-wrap: anywhere; }.operation__event--plan { border-color: var(--usx-color-info); }.operation__event--tool { border-color: var(--usx-color-warning); }.operation__event--diff { border-color: var(--usx-color-success); }
.operation__proposal { margin-top: var(--usx-spacing-sm); border-top: var(--usx-border-width) solid var(--usx-color-border); }.operation__proposal h4 { margin-bottom: 0; }.operation__proposal pre { max-height: 18rem; overflow: auto; padding: var(--usx-spacing-sm); background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); white-space: pre; }
.ops__error { color: var(--usx-color-error, #d33) !important; }
.ops__empty { color: var(--usx-color-on-surface-muted); }
@media (max-width: 760px) { .ops { grid-template-columns: 1fr; } }
</style>
