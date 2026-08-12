<template>
  <div
    class="surface"
    :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }"
  >
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="INTEL_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content intel-content">

      <!-- ═══ Chat tab (default) — AssistUI experience ═══ -->
      <template v-if="activeTab === 'chat'">
        <div class="assistui-mode-toggle">
          <button v-for="mode in ASSISTUI_MODES" :key="mode.id" class="assistui-mode-btn"
            :class="{ 'assistui-mode-btn--active': chat.promptMode === mode.id }"
            @click="switchMode(mode.id); if (mode.id === 'workflow') wf.fetchAll()">
            <span>{{ mode.label }}</span>
          </button>
        </div>

        <template v-if="chat.promptMode !== 'workflow'">
          <div class="assistui-chat-body" :class="{ 'assistui-chat-body--engaged': chat.messages.length > 1 }">
            <div v-if="chat.messages.length <= 1" class="assistui-welcome">
              <span class="assistui-welcome-icon"><UIcon name="auto_awesome" /></span>
              <h1 class="assistui-welcome-title">{{ welcomeTitle }}</h1>
              <div v-if="chat.messages[0]" class="assistui-msg assistui-msg--assistant assistui-welcome-bubble">
                <div class="assistui-msg-bubble" v-html="renderMarkdown(chat.messages[0].content)" />
              </div>
              <div class="assistui-composer assistui-composer--welcome">
                <div class="assistui-composer-row">
                  <textarea ref="inputRef" v-model="chat.input" class="assistui-input" :placeholder="inputPlaceholder" rows="1" @keydown="handleInputKeydown" />
                  <div class="assistui-composer-actions">
                    <button class="assistui-model-btn" @click="modelPickerOpen = !modelPickerOpen" :title="chat.currentModelName">
                      <UIcon name="smart_toy" /><span>{{ chat.currentModelName }}</span><UIcon name="expand_more" />
                    </button>
                    <button class="assistui-submit-btn" @click="chat.sendMessage()" :disabled="!chat.input.trim()"><UIcon name="send" /></button>
                  </div>
                </div>
                <div v-if="modelPickerOpen" class="assistui-model-dropdown">
                  <button v-for="model in chat.models" :key="model.id" class="assistui-model-option"
                    :class="{ 'assistui-model-option--active': chat.selectedModel === model.id }"
                    @click="chat.setModel(model.id); modelPickerOpen = false">
                    <span class="assistui-model-provider">{{ model.provider }}</span>
                    <span class="assistui-model-name">{{ model.name }}</span>
                    <UIcon v-if="chat.selectedModel === model.id" name="check" />
                  </button>
                </div>
              </div>
              <div v-if="chat.prompts.length > 0" class="assistui-prompts">
                <button v-for="prompt in chat.prompts" :key="prompt.id" class="assistui-prompt-pill" @click="handlePromptClick(prompt)">{{ prompt.label }}</button>
              </div>
            </div>
            <div v-else ref="messagesEl" class="assistui-messages">
              <div v-for="msg in chat.messages" :key="msg.id" class="assistui-msg" :class="`assistui-msg--${msg.role}`">
                <div v-if="msg.role === 'assistant'" class="assistui-msg-avatar"><UIcon name="auto_awesome" /></div>
                <div class="assistui-msg-bubble" v-html="renderMarkdown(msg.content)" />
              </div>
              <div v-if="chat.loading" class="assistui-loading"><span class="assistui-loading-dot" /><span class="assistui-loading-dot" /><span class="assistui-loading-dot" /></div>
              <div v-if="chat.promptMode === 'plan' && chat.planSteps.length > 0" class="assistui-plan-card">
                <div class="assistui-plan-card__header"><UIcon name="checklist" /> Plan Steps</div>
                <div v-for="(step, i) in chat.planSteps" :key="i" class="assistui-plan-step" :class="{ 'assistui-plan-step--done': step.done }">
                  <UIcon :name="step.done ? 'check_box' : 'check_box_outline_blank'" /><span>{{ step.description }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="chat.messages.length > 1" class="assistui-composer assistui-composer--footer">
            <div class="assistui-composer-row">
              <textarea ref="inputRef" v-model="chat.input" class="assistui-input" :placeholder="inputPlaceholder" rows="1" @keydown="handleInputKeydown" />
              <div class="assistui-composer-actions">
                <button class="assistui-model-btn" @click="modelPickerOpen = !modelPickerOpen" :title="chat.currentModelName"><UIcon name="smart_toy" /></button>
                <button class="assistui-submit-btn" @click="chat.sendMessage()" :disabled="!chat.input.trim()"><UIcon name="send" /></button>
              </div>
            </div>
            <div v-if="modelPickerOpen" class="assistui-model-dropdown assistui-model-dropdown--up">
              <button v-for="model in chat.models" :key="model.id" class="assistui-model-option"
                :class="{ 'assistui-model-option--active': chat.selectedModel === model.id }"
                @click="chat.setModel(model.id); modelPickerOpen = false">
                <span class="assistui-model-provider">{{ model.provider }}</span>
                <span class="assistui-model-name">{{ model.name }}</span>
                <UIcon v-if="chat.selectedModel === model.id" name="check" />
              </button>
            </div>
          </div>
        </template>
        <div v-else class="assistui-workflow-panel"><p>Workflow tasks and missions shown here.</p></div>
      </template>

      <!-- ═══ Intelligence tab ═══ -->
      <template v-else-if="activeTab === 'intel'">
        <section class="surface__panel intel-header">
          <div class="intel-header__row">
            <h3 class="surface__panel-title">Intelligence</h3>
            <span class="intel-header__badge">Settings &amp; History</span>
          </div>
          <p class="surface__panel-description">System prompt, context sources, and unified history.</p>
        </section>

        <div class="intel-panel">
          <h3 class="surface__panel-title">Chat Settings</h3>
          <p class="intel-muted">System prompt, context sources, and persona configuration.</p>
          <div class="intel-form-section">
            <h4 class="intel-section-label">System Prompt</h4>
            <textarea v-model="systemPrompt" class="intel-textarea" rows="4" placeholder="You are a helpful assistant…" />
          </div>
          <div class="intel-form-section">
            <h4 class="intel-section-label">Context Sources</h4>
            <div class="intel-checkbox-row"><label><input v-model="ctx.vault" type="checkbox" /> Vault documents</label></div>
            <div class="intel-checkbox-row"><label><input v-model="ctx.tasks" type="checkbox" /> Active tasks</label></div>
            <div class="intel-checkbox-row"><label><input v-model="ctx.surface" type="checkbox" /> Current surface</label></div>
          </div>
          <button class="intel-save-btn" @click="savePrompt">Save Chat Settings</button>
        </div>
      </template>

      <!-- ═══ Models tab ═══ -->
      <SnackbarModelsPanel v-else-if="activeTab === 'models'" />

      <!-- ═══ Agents tab ═══ -->
      <SnackbarAgentsPanel v-else-if="activeTab === 'agents'" />

      <!-- ═══ Budget tab ═══ -->
      <SnackbarBudgetPanel v-else-if="activeTab === 'budget'" />

      <!-- ═══ History tab ═══ -->
      <CombinedHistoryPanel v-else-if="activeTab === 'history'" />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useShellStore } from "../../stores/shell";
import { useSnackbarOpsStore } from "../../stores/snackbarOps";
import { useChatStore, ASSISTUI_MODES } from "../../stores/chat";
import { useWorkflowStore } from "../../stores/workflow";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import SnackbarModelsPanel from "../snackbar/panels/SnackbarModelsPanel.vue";
import SnackbarAgentsPanel from "../snackbar/panels/SnackbarAgentsPanel.vue";
import SnackbarBudgetPanel from "../snackbar/panels/SnackbarBudgetPanel.vue";
import CombinedHistoryPanel from "./panels/CombinedHistoryPanel.vue";

const INTEL_TABS = [
  { id: "chat", label: "Chat", icon: "chat" },
  { id: "intel", label: "Intelligence", icon: "chat" },
  { id: "models", label: "Models", icon: "chat" },
  { id: "agents", label: "Agents", icon: "chat" },
  { id: "budget", label: "Budget", icon: "chat" },
  { id: "history", label: "History", icon: "chat" },
];

const shell = useShellStore();
const srv = useSnackbarOpsStore();
const chat = useChatStore();
const wf = useWorkflowStore();

const activeTab = ref("chat");

watch(activeTab, (tab) => shell.setIntelTab(tab), { immediate: true });
const modelPickerOpen = ref(false);
const inputRef = ref<HTMLTextAreaElement | null>(null);

const systemPrompt = ref("You are a helpful assistant.");
const ctx = ref({ vault: true, tasks: true, surface: true });

const welcomeTitle = computed(() => {
  if (chat.promptMode === "plan") return "What should we research?";
  if (chat.promptMode === "act") return "Ready to act";
  return "Good evening";
});

const inputPlaceholder = computed(() => {
  switch (chat.promptMode) {
    case "plan": return "What should we research?";
    case "act": return "What should we do?";
    case "workflow": return "What workflow should we plan?";
    default: return "What would you like to do today?";
  }
});

const renderMarkdown = (content: string) => content
  .replace(/^# (.+)$/gm, "<h1>$1</h1>")
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/`(.+?)`/g, "<code>$1</code>")
  .replace(/\n/g, "<br>");

function handlePromptClick(prompt: any) { chat.input = prompt.label; chat.sendMessage(); }
function handleInputKeydown(e: KeyboardEvent) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); chat.sendMessage(); } }
function switchMode(mode: string) { chat.setPromptMode(mode as any); }
function savePrompt() {
  try { localStorage.setItem("ucore-chat-prompt", systemPrompt.value); } catch {}
  try { localStorage.setItem("ucore-chat-context", JSON.stringify(ctx.value)); } catch {}
}

onMounted(() => {
  srv.fetchAll();
  const saved = localStorage.getItem("ucore-chat-prompt");
  if (saved) systemPrompt.value = saved;
  try {
    const ctxSaved = localStorage.getItem("ucore-chat-context");
    if (ctxSaved) ctx.value = { ...ctx.value, ...JSON.parse(ctxSaved) };
  } catch {}
});
</script>

<style scoped>
.intel-content { display: grid; gap: var(--usx-spacing-md); padding: var(--usx-spacing-lg); }
.intel-header { background: linear-gradient(180deg, color-mix(in srgb, var(--usx-color-primary) 4%, transparent) 0%, transparent 78%); }
.intel-header__row { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-sm); flex-wrap: wrap; }
.intel-header__badge { display: inline-flex; align-items: center; min-height: calc(var(--usx-touch-min) - var(--usx-spacing-sm)); padding: 0 var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-full); font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); background: color-mix(in srgb, var(--usx-color-surface-variant) 75%, var(--usx-color-surface)); }
.intel-panel { max-width: var(--usx-prose-width); }
.intel-muted { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-lg); }
.intel-form-section { margin-bottom: var(--usx-spacing-lg); }
.intel-section-label { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-semibold); margin-bottom: var(--usx-spacing-sm); }
.intel-textarea { width: 100%; padding: var(--usx-spacing-sm) var(--usx-spacing-md); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); background-color: var(--usx-color-surface); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); font-family: var(--usx-font-family-sans); resize: vertical; line-height: var(--usx-line-height-normal); }
.intel-checkbox-row { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-1) 0; font-size: var(--usx-font-size-sm); }
.intel-save-btn { min-height: var(--usx-touch-min); padding: 0 var(--usx-spacing-xl); background-color: var(--usx-color-primary); color: var(--usx-color-on-primary); border: var(--usx-border-width) solid var(--usx-color-primary); border-radius: var(--usx-radius-md); cursor: pointer; font-size: var(--usx-font-size-sm); }

/* ── AssistUI chat styles ────────────────────────────────────── */
.assistui-mode-toggle { display: flex; justify-content: center; gap: var(--usx-spacing-xs); padding: 0 0 var(--usx-spacing-sm); flex-shrink: 0; }
.assistui-mode-btn { display: inline-flex !important; align-items: center; padding: 2px var(--usx-spacing-md) !important; border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-medium); cursor: pointer; white-space: nowrap; height: auto !important; min-height: auto !important; max-height: 28px !important; line-height: 1.2 !important; margin-bottom: 0 !important; transition: all var(--usx-transition-fast); }
.assistui-mode-btn:hover { background-color: var(--usx-color-surface-variant); border-color: var(--usx-color-primary); }
.assistui-mode-btn--active { background-color: var(--usx-color-primary); color: var(--usx-color-on-primary); border-color: var(--usx-color-primary); }
.assistui-chat-body { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; }
.assistui-chat-body--engaged { padding: var(--usx-spacing-md); }
.assistui-welcome { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--usx-spacing-lg); padding: var(--usx-spacing-2xl) var(--usx-spacing-lg); }
.assistui-welcome-icon { color: var(--usx-color-primary); font-size: var(--usx-font-size-3xl); margin-bottom: var(--usx-spacing-xs); }
.assistui-welcome-title { font-size: var(--usx-font-size-3xl); font-weight: var(--usx-font-weight-bold); color: var(--usx-color-on-surface); margin: 0; text-align: center; }
.assistui-msg.assistui-welcome-bubble { max-width: 42ch; width: 100%; display: block; margin: 0 auto; align-self: center; }
.assistui-welcome-bubble .assistui-msg-bubble { width: 100%; box-sizing: border-box; text-align: left; font-size: var(--usx-font-size-base); }
.assistui-composer--welcome { width: 100%; max-width: var(--usx-prose-width); }
.assistui-composer--footer { padding: var(--usx-spacing-sm); border-top: var(--usx-border-width) solid var(--usx-color-border); background: var(--usx-color-surface); flex-shrink: 0; position: relative; }
.assistui-composer-row { display: flex; align-items: center; gap: 0; border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-lg); background: var(--usx-color-surface); padding: 0; transition: border-color var(--usx-transition-fast); }
.assistui-composer-row:focus-within { border-color: var(--usx-color-primary); }
.assistui-composer-actions { display: flex; align-items: center; gap: var(--usx-spacing-xs); flex-shrink: 0; padding: var(--usx-spacing-xs); }
.assistui-model-btn { display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); padding: 0 var(--usx-spacing-xs); min-height: var(--usx-control-size-md); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-full); background: var(--usx-color-surface); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-xs); cursor: pointer; white-space: nowrap; }
.assistui-model-dropdown { position: absolute; top: calc(100% + var(--usx-spacing-xs)); left: 0; background: var(--usx-color-surface); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); min-width: var(--usx-dropdown-min-width); z-index: 10; box-shadow: var(--usx-shadow-sm); display: flex; flex-direction: column; }
.assistui-model-dropdown--up { top: auto; bottom: calc(100% + var(--usx-spacing-xs)); }
.assistui-model-option { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm) var(--usx-spacing-md); background: transparent; color: var(--usx-color-on-surface); border: none; cursor: pointer; font-size: var(--usx-font-size-sm); text-align: left; }
.assistui-model-option:hover { background: var(--usx-color-surface-hover); }
.assistui-model-option--active { background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent); color: var(--usx-color-primary); }
.assistui-model-provider { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.assistui-model-name { flex: 1; }
.assistui-prompts { display: flex; flex-wrap: wrap; justify-content: center; gap: var(--usx-spacing-xs); max-width: 36rem; }
.assistui-prompt-pill { border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-full); background: var(--usx-color-surface); color: var(--usx-color-on-surface); padding: 0 var(--usx-spacing-md); min-height: var(--usx-control-size-sm); font-size: var(--usx-font-size-xs); cursor: pointer; transition: var(--usx-transition-fast); }
.assistui-prompt-pill:hover { border-color: var(--usx-color-primary); background: color-mix(in srgb, var(--usx-color-primary) 6%, var(--usx-color-surface)); }
.assistui-messages { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: var(--usx-spacing-md); }
.assistui-msg { display: flex; gap: var(--usx-spacing-sm); max-width: 86%; }
.assistui-msg--user { align-self: flex-end; flex-direction: row-reverse; }
.assistui-msg--assistant { align-self: flex-start; }
.assistui-msg-avatar { display: flex; align-items: center; justify-content: center; width: var(--usx-control-size-md); height: var(--usx-control-size-md); border-radius: var(--usx-radius-full); background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent); color: var(--usx-color-primary); flex-shrink: 0; }
.assistui-msg-bubble { padding: var(--usx-spacing-sm) var(--usx-spacing-md); border-radius: var(--usx-radius-md); font-size: var(--usx-font-size-sm); line-height: var(--usx-line-height-normal); }
.assistui-msg--user .assistui-msg-bubble { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.assistui-msg--assistant .assistui-msg-bubble { background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); }
.assistui-input { flex: 1; min-height: var(--usx-control-size-md); border: none; background: transparent; color: var(--usx-color-on-surface); font-size: var(--usx-font-size-base); font-family: var(--usx-font-family-sans); padding: var(--usx-spacing-sm) var(--usx-spacing-md); resize: none; outline: none; box-shadow: none; line-height: var(--usx-line-height-tight); }
.assistui-submit-btn { display: flex; align-items: center; justify-content: center; width: var(--usx-control-size-md); height: var(--usx-control-size-md); border: none; border-radius: var(--usx-radius-full); background: var(--usx-color-primary); color: var(--usx-color-on-primary); cursor: pointer; flex-shrink: 0; }
.assistui-submit-btn:disabled { opacity: 0.4; cursor: default; }
.assistui-loading { display: flex; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); }
.assistui-loading-dot { width: var(--usx-spacing-xs); height: var(--usx-spacing-xs); border-radius: var(--usx-radius-full); background: var(--usx-color-on-surface-muted); animation: assistui-pulse var(--usx-motion-duration-pulse) infinite; }
.assistui-loading-dot:nth-child(2) { animation-delay: var(--usx-motion-delay-sm); }
.assistui-loading-dot:nth-child(3) { animation-delay: var(--usx-motion-delay-md); }
@keyframes assistui-pulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
.assistui-plan-card { margin-top: var(--usx-spacing-md); padding: var(--usx-spacing-md); border: var(--usx-border-width) solid var(--usx-color-primary); border-radius: var(--usx-radius-md); background: var(--usx-color-surface-variant); }
.assistui-plan-card__header { display: flex; align-items: center; gap: var(--usx-spacing-sm); font-weight: var(--usx-font-weight-semibold); color: var(--usx-color-primary); margin-bottom: var(--usx-spacing-sm); }
.assistui-plan-step { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-xs) 0; font-size: var(--usx-font-size-sm); }
.assistui-plan-step--done { opacity: 0.6; text-decoration: line-through; }
.assistui-workflow-panel { padding: var(--usx-spacing-xl); }

/* Shared USX layer */
.intel-content :deep(.surface__panel) { border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); background: color-mix(in srgb, var(--usx-color-surface) 96%, var(--usx-color-background)); padding: var(--usx-spacing-md); }
.intel-content :deep(table) { width: 100%; border-collapse: collapse; border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); overflow: hidden; background: var(--usx-color-surface); }
.intel-content :deep(th) { color: var(--usx-color-on-surface-muted); background: color-mix(in srgb, var(--usx-color-surface-variant) 78%, var(--usx-color-surface)); font-weight: var(--usx-font-weight-medium); }
.intel-content :deep(th), .intel-content :deep(td) { padding: var(--usx-spacing-sm); border-bottom: var(--usx-border-width) solid var(--usx-color-border); font-size: var(--usx-font-size-sm); text-align: left; }
</style>
