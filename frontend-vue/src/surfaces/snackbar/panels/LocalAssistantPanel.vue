<template>
  <section class="local-assistant">
    <header>
      <div>
        <h2>OK Assistant</h2>
        <p>Tell me what you’d like to write, organize, research, or transform.</p>
      </div>
      <button type="button" class="usx-btn" :disabled="busy || checking" @click="load">
        <UIcon name="refresh" aria-hidden="true" /> {{ checking ? 'Checking…' : 'Refresh local models' }}
      </button>
    </header>
    <p v-if="availability" role="status">{{ availability }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-if="message" role="status">{{ message }}</p>
    <form @submit.prevent="run" :aria-busy="busy">
      <div class="assistant-options">
        <label>What are we working on?
          <select v-model="purpose" :disabled="busy">
            <option v-for="activity in activities" :key="activity.id" :value="activity.id">{{ activity.label }}</option>
          </select>
        </label>
        <label>How should I choose a local model?
          <select v-model="modelOverride" :disabled="busy || checking || !online || !chatModels.length">
            <option value="">Automatically match the task</option>
            <option v-for="item in rankedModels" :key="item.name" :value="item.name">{{ modelStrength(item) }} · {{ item.name }}</option>
          </select>
        </label>
      </div>
      <p v-if="model">
        {{ model }} will review the material you provide, draft, and review its answer.
      </p>
      <RouterLink class="usx-btn assistant-skill" :to="{ path: '/workflow', query: { tab: 'skills', skill: activitySkill.id } }">
        <UIcon name="extension" aria-hidden="true" />{{ activitySkill.label }}
      </RouterLink>
      <label>What would you like me to do?
        <input v-model="goal" maxlength="1000" placeholder="What would you like to make or review?" required />
      </label>
      <label>Notes and sources (optional)
        <textarea v-model="material" maxlength="12000" rows="3" placeholder="Paste excerpts or notes for the assistant to use." />
      </label>
      <button type="submit" class="usx-btn usx-btn--primary" :disabled="!canRun">
        <UIcon name="auto_awesome" aria-hidden="true" /> {{ busy ? 'Working…' : 'Create draft' }}
      </button>
    </form>
    <section v-if="result"><h3>Draft</h3><pre>{{ result.content }}</pre><button class="usx-btn" @click="download"><UIcon name="download" />Save Markdown copy</button><details><summary>Roundtable notes</summary><article v-for="output in result.outputs" :key="output.role"><h4>{{ output.name }}</h4><pre>{{ output.content }}</pre></article></details><p>Save accepted work in your Vault or Shared layer. Global Knowledge remains unchanged.</p></section>
    <details>
      <summary>Local model library · {{ models.length }}</summary>
      <article v-for="item in models" :key="item.name" class="model-entry">
        <strong>{{ item.name }}</strong>
        <span>{{ modelDescription(item) }}</span>
        <small v-if="item.modified_at">Last changed locally {{ new Date(item.modified_at).toLocaleDateString() }}</small>
        <button v-if="officialModelReference(item.name)" type="button" class="usx-btn"
          :disabled="busy || !online" @click="pull(item.name)">Check for an update</button>
      </article>
    </details>
    <details><summary>Install an offline model</summary><p>Reviewed application packs will specify their model needs. For now, choose an explicit tagged model from the official library. Downloading does not make it a reviewed uDOS pack.</p><a href="https://ollama.com/library" target="_blank" rel="noopener noreferrer">Browse the official library</a><label for="model-reference">Official model reference</label><input id="model-reference" v-model="downloadModel" placeholder="model:tag" /><button class="usx-btn" :disabled="busy||!online||!downloadModel.trim()" @click="pull(downloadModel)">Download selected model</button><p>Check its licence, download size and device requirements first. Existing models are not deleted. Keep this view open for progress; disconnecting does not guarantee Ollama cancels its download.</p></details>
  </section>
</template>
<script setup lang="ts">
import {computed,onMounted,ref,watch} from 'vue';
import { useRoute } from 'vue-router';
import {UCORE_BASE} from '../../../api/base';
import { useChatStore } from '../../../stores/chat';
import UIcon from '../../../skills/atoms/UIcon.vue';
interface LocalModel {
  name: string;
  size: number;
  local_chat: boolean;
  coding_focused: boolean;
  modified_at?: string;
  details?: { family?: string; parameter_size?: string; quantization_level?: string };
}
const activities = [
  { id: "project", label: "Organize a project", skill: { id: "workflow_audit", label: "Workflow Audit" } },
  { id: "creative", label: "Tell a story", skill: { id: "attach_context", label: "Attach Context" } },
  { id: "knowledge", label: "Organize my notes", skill: { id: "vault_discovery", label: "Vault Discovery" } },
  { id: "research", label: "Research a topic", skill: { id: "ask_vault", label: "Ask Vault" } },
  { id: "processing", label: "Transform text or Markdown", skill: { id: "attach_context", label: "Attach Context" } },
  { id: "ucode", label: "Write uCode", skill: { id: "workflow_audit", label: "Workflow Audit" } },
];
const models=ref<LocalModel[]>([]),online=ref(false),busy=ref(false),error=ref(''),message=ref(''),purpose=ref('project'),goal=ref(''),material=ref(''),downloadModel=ref(''),result=ref<any>(null);
const route = useRoute();
watch(() => [route.query.purpose, route.query.goal], ([requestedPurpose, requestedGoal]) => {
  if (typeof requestedPurpose === "string" && activities.some(item => item.id === requestedPurpose)) {
    purpose.value = requestedPurpose;
    if (typeof requestedGoal === "string") goal.value = requestedGoal.slice(0, 1000);
  }
}, { immediate: true });
const chatStore = useChatStore();
const modelOverride = computed({
  get: () => chatStore.okAssistantModel,
  set: value => { chatStore.okAssistantModel = value; },
});
const checking = ref(false);
const availability = ref("");
const chatModels=computed(()=>models.value.filter(item=>item.local_chat));
const activitySkill = computed(() => (activities.find(activity => activity.id === purpose.value) ?? activities[0]).skill);
const rankedModels = computed(() => {
  const coding = purpose.value === "ucode";
  return [...chatModels.value].sort((a, b) => Number(b.coding_focused === coding) - Number(a.coding_focused === coding));
});
const model = computed(() =>
  chatModels.value.some(item => item.name === modelOverride.value)
    ? modelOverride.value : rankedModels.value[0]?.name || "",
);

function modelStrength(item: LocalModel) {
  return item.coding_focused ? "Code and structured text" : "Writing, research, and organization";
}

function modelDescription(item: LocalModel) {
  return [
    item.local_chat ? (item.coding_focused ? "Coding chat" : "General chat") : "Outside local chat",
    item.details?.family,
    item.details?.parameter_size,
    item.details?.quantization_level,
    Number.isFinite(item.size) ? `${(item.size / 1e9).toFixed(2)} GB` : "",
  ].filter(Boolean).join(" · ");
}

function officialModelReference(name: string) {
  return /^[a-z0-9][a-z0-9._-]{0,79}:[a-z0-9][a-z0-9._-]{0,79}$/.test(name) && !name.includes("cloud");
}

const canRun = computed(() => !busy.value && !checking.value && online.value && Boolean(model.value && goal.value.trim()));

async function load() {
  checking.value = true;
  availability.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/assistant/library`, { signal: AbortSignal.timeout(8000) });
    const data = await response.json().catch(() => null);
    online.value = response.ok && data?.online === true;
    models.value = online.value && Array.isArray(data.models) ? data.models : [];
    if (!online.value) {
      availability.value = response.status === 401
        ? "Choose a local profile to use OK Assistant."
        : response.status === 503 && data?.online === false
          ? "Ollama is unavailable. Open Server to check the service."
          : "OK Assistant could not reach the uCore assistant service.";
      return;
    }
    if (!chatModels.value.length) availability.value = "Install a chat model to create drafts.";
  } catch {
    online.value = false;
    availability.value = "OK Assistant could not reach uCore. Check the backend and try again.";
  } finally {
    checking.value = false;
  }
}

async function run() {
  if (!canRun.value) return;
  busy.value = true;
  error.value = "";
  message.value = "Ollama is preparing your draft…";
  try {
    const response = await fetch(`${UCORE_BASE}/api/assistant/roundtable`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goal.value.trim(), material: material.value, model: modelOverride.value === model.value ? modelOverride.value : "", purpose: purpose.value }),
    });
    if (!response.ok) throw new Error((await response.text()).slice(0, 240));
    result.value = await response.json();
    message.value = "Draft ready to review.";
  } catch (exc) {
    message.value = "";
    error.value = exc instanceof Error ? exc.message : "Draft unavailable.";
  } finally {
    busy.value = false;
  }
}
async function pull(reference: string){const name=reference.trim();if(!officialModelReference(name)){error.value="Enter a tagged model from the Ollama library.";return;}if(!window.confirm(`Get the latest available files for ${name} from the official Ollama library? This uses internet data and local disk space. Review its licence and requirements first.`))return;busy.value=true;error.value='';message.value='Starting download…';try{const response=await fetch(`${UCORE_BASE}/api/assistant/models/pull`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:name,confirm:true})});if(!response.ok||!response.body)throw Error((await response.text()).slice(0,240));const reader=response.body.getReader(),decoder=new TextDecoder();let pending='',success=false;while(true){const {done,value}=await reader.read();pending+=decoder.decode(value,{stream:!done});const lines=pending.split('\n');pending=lines.pop()||'';for(const line of lines){if(!line.trim())continue;const event=JSON.parse(line);if(event.error)throw Error(event.error);message.value=event.status+(event.total?` · ${Math.round(100*(event.completed||0)/event.total)}%`:'');if(event.status==='success')success=true;}if(done)break;}if(!success)throw Error('Download ended without a verified success response. Check installed models before retrying.');await load();message.value='Model downloaded. Choose it above to try a local draft.';}catch(e){error.value=e instanceof Error?e.message:'Download failed';}finally{busy.value=false;}}
function download(){const url=URL.createObjectURL(new Blob([result.value.content],{type:'text/markdown'}));const link=document.createElement('a');link.href=url;link.download=purpose.value==='ucode'?'ucode-draft.md':'roundtable-draft.md';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
onMounted(load);
</script>
<style scoped>
.local-assistant{display:grid;gap:16px;text-align:left;max-width:64rem;margin:auto}.local-assistant header{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.local-assistant header>div{flex:1}.local-assistant h2,.local-assistant h3,.local-assistant h4,.local-assistant p{margin:0 0 8px}.local-assistant p{font-size:var(--usx-font-size-sm);color:var(--usx-color-on-surface-muted)}form{display:grid;gap:8px}label{margin:0}input,select,textarea{box-sizing:border-box;width:100%;font:inherit;padding:8px;border:1px solid var(--usx-color-border);border-radius:var(--usx-radius-sm);background:var(--usx-color-surface);color:inherit;box-shadow:none}input,select{height:36px}.usx-btn{display:inline-flex;align-items:center;gap:6px;width:fit-content;min-height:32px;padding:4px 10px;margin:0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;line-height:1.6}article{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;padding:8px 0;border-bottom:1px solid var(--usx-color-border)}details{padding:12px 0;border-top:1px solid var(--usx-color-border)}summary{cursor:pointer;margin-bottom:8px}[role=alert]{color:var(--usx-color-danger)}
header h2 { font-size: var(--usx-font-size-xl); }
.local-assistant header > div { min-width: 12rem; }
.assistant-options { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr)); gap: 8px; }
.model-entry { display: grid; justify-content: start; overflow-wrap: anywhere; }
.local-assistant form label { display: grid; gap: 4px; min-width: 0; font-size: var(--usx-font-size-sm); }
.local-assistant form :is(input, select, textarea) { margin: 0; min-width: 0; }
.local-assistant form textarea { resize: vertical; }
@media (max-width: 420px) {
  .assistant-options { grid-template-columns: minmax(0, 1fr); }
}
</style>
