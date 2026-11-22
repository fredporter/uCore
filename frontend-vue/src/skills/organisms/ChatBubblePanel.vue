<template>
  <div class="chat-panel">
    <!-- ── Header (lane toggle moved to overlay top-right) ────── -->
    <div class="chat-panel__header">
      <div class="chat-panel__header-spacer" />
      <button
        v-if="activeLane === 'chat' && (localAssistant ? chatMessages.some(msg => msg.role === 'user') && !loading : chatStore.hasMessages)"
        type="button"
        class="usx-btn chat-panel__header-action"
        :title="localAssistant ? 'Clear conversation' : 'Clear chat history'"
        :aria-label="localAssistant ? 'Clear conversation' : 'Clear chat history'"
        @click="localAssistant ? emit('clear-local') : chatStore.clearHistory()"
      >
        <UIcon name="delete_sweep" />
      </button>
    </div>

    <!-- ── Body ──────────────────────────────────────────────── -->
    <div ref="messagesEl" class="chat-panel__body">
      <div v-if="localAssistant && !activeMessages.length" class="chat-panel__start">
        <p>Ask a question, draft something, or plan your next step with your local assistant.</p>
        <div class="chat-panel__prompts">
          <button
            v-for="prompt in starterPrompts"
            :key="prompt.icon"
            type="button"
            class="usx-btn chat-panel__prompt"
            @click="useStarterPrompt(prompt.text)"
          >
            <UIcon :name="prompt.icon" aria-hidden="true" />
            {{ prompt.label }}
          </button>
        </div>
      </div>

      <div v-else class="chat-panel__messages">
        <article
          v-for="(msg, i) in activeMessages"
          :key="`${activeLane}-${i}`"
          class="chat-panel__msg"
          :class="`chat-panel__msg--${msg.role}`"
        >
          <div class="chat-panel__msg-row">
            <div class="chat-panel__msg-body" v-html="renderMsgContent(msg.content)" />
          </div>
          <div v-if="msg.role === 'assistant'" class="chat-panel__msg-actions">
            <button v-if="activeLane === 'chat'" class="usx-btn chat-panel__msg-action" title="Append to current document" @click="appendToDoc(msg.content)">
              <UIcon name="note_add" />
            </button>
            <button v-if="activeLane === 'chat'" class="usx-btn chat-panel__msg-action" title="New note" @click="newNote(msg.content)">
              <UIcon name="post_add" />
            </button>
            <button class="usx-btn chat-panel__msg-action" title="Copy to clipboard" @click="copyText(msg.content)">
              <UIcon name="content_copy" />
            </button>
          </div>
        </article>

        <div v-if="loading" class="chat-panel__loading">
          <span class="chat-panel__dot" />
          <span class="chat-panel__dot" />
          <span class="chat-panel__dot" />
        </div>
      </div>
    </div>

    <!-- ── Composer: input + send row, model switcher below ───── -->
    <div class="chat-panel__composer">
      <div class="chat-panel__composer-row">
        <textarea
          ref="inputEl"
          v-model="inputText"
          class="chat-panel__input"
          :placeholder="inputPlaceholder"
          :aria-label="localAssistant ? 'OK Assistant' : 'Message'"
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.shift.enter.prevent="inputText += '\n'"
        />
        <button
          class="usx-btn chat-panel__send"
          :disabled="!inputText.trim() || loading"
          aria-label="Send message"
          title="Send (Enter)"
          @click="sendMessage"
        >
          <UIcon name="send" />
        </button>
      </div>

      <div class="chat-panel__composer-actions">
        <RouterLink class="usx-btn chat-panel__settings" :to="localAssistant ? '/workflow?tab=ai' : '/system?tab=preferences'" @click="shell.setChatMode('closed')"><UIcon name="settings" />{{ localAssistant ? "Local models" : "Settings" }}</RouterLink>
        <label v-if="localAssistant" class="chat-panel__specialist-select">
          <UIcon name="psychology" />
          <select
            v-model="selectedSpecialist"
            aria-label="Assistant specialist"
          >
            <option value="">General Assistant</option>
            <option value="format-smith">Format Smith (Markdown)</option>
          </select>
          <UIcon name="expand_more" class="chat-panel__presentation-chevron" />
        </label>
        <label v-if="localAssistant && cloudModels.length && !selectedSpecialist" class="chat-panel__specialist-select">
          <UIcon name="cloud" />
          <select :value="cloudModel" :disabled="loading" aria-label="Assistant model"
            @change="emit('update:cloudModel', ($event.target as HTMLSelectElement).value)">
            <option value="">Local Assistant</option>
            <option v-for="model in cloudModels" :key="model.id" :value="model.id">
              {{ model.name || model.id }} ({{ model.provider }})
            </option>
          </select>
        </label>
        <label class="chat-panel__presentation">
          <UIcon name="view_sidebar" />
          <select
            :value="shell.chatPresentation"
            aria-label="Chat presentation"
            @change="setPresentation"
          >
            <option value="overlay">Overlay</option>
            <option value="toast">Toast</option>
            <option value="sidebar">Sidebar</option>
            <option value="floating">Floating</option>
          </select>
          <UIcon name="expand_more" class="chat-panel__presentation-chevron" />
        </label>
      </div>

    </div>

    <!-- ── Footer: context + mode tabs ────────────────────────── -->
    <div class="chat-panel__footer-row">
      <span
        v-if="displayContext && displayContext.trim().toLowerCase() !== 'code'"
        class="chat-panel__context"
      >
        <UIcon name="location_on" />
        <span class="chat-panel__context-text">{{ displayContext }}</span>
      </span>

      <div v-if="localAssistant" class="chat-panel__mode-toggle" role="tablist" aria-label="Assistant specialist">
        <button
          type="button"
          class="usx-btn chat-panel__mode-btn"
          :class="{ 'chat-panel__mode-btn--active': !selectedSpecialist }"
          role="tab"
          :aria-selected="!selectedSpecialist ? 'true' : 'false'"
          @click="selectedSpecialist = ''"
        >
          General
        </button>
        <button
          type="button"
          class="usx-btn chat-panel__mode-btn"
          :class="{ 'chat-panel__mode-btn--active': selectedSpecialist === 'format-smith' }"
          role="tab"
          :aria-selected="selectedSpecialist === 'format-smith' ? 'true' : 'false'"
          @click="selectedSpecialist = 'format-smith'"
        >
          Format Smith
        </button>
      </div>

      <div v-else class="chat-panel__mode-toggle" role="tablist" aria-label="Assistant mode">
        <button
          v-for="mode in CHAT_MODES"
          :key="mode.id"
          class="usx-btn chat-panel__mode-btn"
          :class="{ 'chat-panel__mode-btn--active': activeChatMode === mode.id }"
          role="tab"
          :aria-selected="activeChatMode === mode.id ? 'true' : 'false'"
          @click="setMode(mode.id)"
        >
          {{ mode.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { RouterLink } from "vue-router";
import { useShellStore } from "../../stores/shell";
import type { ChatPresentation } from "../../stores/shell";
import { getEditorSurface } from "../../composables/useEditorSurface";
import { useWorkspaceStore } from "../../stores/workspace";
import { useToast } from "../../composables/useToast";
import { useChatStore, type ModelOption } from "../../stores/chat";
import { renderMarkdown } from "../../composables/useMarkdown";
import UIcon from "../atoms/UIcon.vue";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const props = withDefaults(
  defineProps<{
    chatMessages?: Message[];
    localAssistant?: boolean;
    cloudModel?: string;
    cloudModels?: ModelOption[];
    devMessages?: Message[];
    loading?: boolean;
    devAvailable?: boolean;
    devModeOn?: boolean;
    contextLabel?: string;
    currentTask?: string;
    activeLane?: "chat" | "dev";
  }>(),
  {
    chatMessages: () => [],
    cloudModel: "",
    cloudModels: () => [],
    devMessages: () => [],
    loading: false,
    devAvailable: false,
    devModeOn: false,
    contextLabel: "",
    currentTask: "",
    activeLane: "chat",
  },
);

const emit = defineEmits<{
  "clear-local": [];
  "update:cloudModel": [model: string];
  "send-chat": [message: string, mode?: "chat" | "plan" | "act" | "workflow", specialist?: string];
  "send-dev": [message: string, mode: "ask" | "plan" | "act"];
  "toggle-dev-mode": [];
  "update:activeLane": [lane: "chat" | "dev"];
  close: [];
}>();

const shell = useShellStore();

function setPresentation(event: Event) {
  shell.setChatPresentation((event.target as HTMLSelectElement).value as ChatPresentation);
}
const chatStore = useChatStore();
const editorSurface = getEditorSurface();
const displayContext = computed(() => {
  if (!props.localAssistant) return props.contextLabel;
  const path = editorSurface.currentFile.value?.path || "";
  if (/(?:^|\/)global-knowledge\//i.test(path)) return "Global Knowledge";
  if (/(?:^|\/)Shared\//.test(path)) return "Shared Vaults";
  if (/(?:^|\/)Public\//.test(path)) return "Public Sites";
  return "User Vault";
});
const ws = useWorkspaceStore();
const { toast } = useToast();

const activeLane = ref<'chat'>('chat');
const activeChatMode = computed({
  get: () => chatStore.promptMode === 'workflow' ? 'plan' : chatStore.promptMode,
  set: (mode: "chat" | "plan" | "act" | "workflow") => chatStore.setPromptMode(mode),
});
const messagesEl = ref<HTMLDivElement | null>(null);
const inputEl = ref<HTMLTextAreaElement | null>(null);
const modelPickerOpen = ref(false);
const selectedModelId = ref(chatStore.selectedModel);

const inputText = computed({
  get: () => chatStore.input,
  set: (v: string) => { chatStore.input = v; },
});

const selectedSpecialist = ref<"" | "format-smith">("");

// ─── Dynamic composer placeholder (matches Intelligence surface) ──
const inputPlaceholder = computed(() => {
  if (props.localAssistant) {
    return selectedSpecialist.value === "format-smith"
      ? "Paste notes to format as Markdown…"
      : "OK Assistant…";
  }
  switch (activeChatMode.value) {
    case "plan": return "What should we research?";
    case "act": return "What should we do?";
    default: return "What would you like to do today?";
  }
});

function setMode(id: "chat" | "plan" | "act" | "workflow") {
  activeChatMode.value = id;

}

// ─── Model selector ──────────────────────────────────────────
const availableModels = computed(() => chatStore.models);
const currentModelLabel = computed(() => {
  const m = chatStore.models.find((mod) => mod.id === selectedModelId.value);
  return m?.name ?? "Model";
});

function selectModel(id: string) {
  selectedModelId.value = id;
  chatStore.setModel(id);
  modelPickerOpen.value = false;
}

const starterPrompts = computed(() => {
  if (selectedSpecialist.value === "format-smith") {
    return [
      { icon: "format_align_left", label: "Format notes", text: "# Notes 2026-11-21\n* attendee: Alice and Bob\n* budget: $1,250 (estimated?)" },
      { icon: "checklist", label: "Format action items", text: "Action items:\n- Alice: review roadmap\n- Bob: estimate budget (~$500?)" },
    ];
  }
  return [
    { icon: "search", label: "Research a topic", text: "Help me outline a research plan for " },
    { icon: "edit_note", label: "Draft a note", text: "Help me draft a Markdown note about " },
    { icon: "checklist", label: "Plan next steps", text: "Help me break this goal into next steps: " },
  ];
});

function useStarterPrompt(prompt: string) {
  if (!inputText.value.trim()) inputText.value = prompt;
  inputEl.value?.focus();
}

watch(inputText, () => {
  const input = inputEl.value;
  if (!input) return;
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}, { flush: "post" });

// ─── Simple message content render ────────────────────────────
function renderMsgContent(content: string): string {
  return renderMarkdown(content);
}

const CHAT_MODES = [
  { id: "chat", label: "Ask" },
  { id: "plan", label: "Plan" },
  { id: "act", label: "Act" },
] as const;

const activeMessages = computed(() => props.chatMessages);

// Auto-scroll on new messages
watch(
  [activeMessages, () => props.loading],
  async () => {
    await nextTick();
    if (messagesEl.value)
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
  },
  { deep: true },
);

function sendMessage() {
  const text = inputText.value.trim();
  if (!text || props.loading) return;
  inputText.value = "";
  emit("send-chat", text, activeChatMode.value, selectedSpecialist.value);
}

function closeChat() {
  emit("close");
  shell.setChatMode("closed");
}

// ─── Output routing ──────────────────────────────────────────
function appendToDoc(content: string) {
  const current = editorSurface.currentFile.value;
  if (current) {
    editorSurface.updateContent(`${current.content}\n\n${content}`);
    toast("Appended to document", "success", { duration: 2000 });
  } else {
    toast("No document open — use 'New note' instead", "info");
  }
}

function newNote(content: string) {
  const today = new Date().toISOString().slice(0, 10);
  const filename = `Chat Note ${today}.md`;
  const md = `---\ntitle: "Chat Note"\ndate: "${today}"\ntype: note\nsource: chat\n---\n\n${content}`;
  ws.createFile("/notes", filename);
  const node = ws.tree
    .flatMap((n: import("../../stores/workspace").FileNode) => n.children ?? [])
    .find(
      (n: import("../../stores/workspace").FileNode) => n.name === filename,
    );
  if (node) ws.updateFileContent(node.id, md);
  toast(`Saved as "${filename}"`, "success");
}

async function copyText(content: string) {
  try {
    await navigator.clipboard.writeText(content);
    toast("Copied to clipboard", "success", { duration: 1500 });
  } catch {
    toast("Copy failed", "error");
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

/* ─── Header (single lane toggle icon, right-aligned) ─────────── */
.chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: transparent;
  flex-shrink: 0;
  min-height: 36px;
  position: relative;
}

.chat-panel__header-spacer {
  flex: 1;
}

.chat-panel__header-action {
  display: inline-grid;
  place-items: center;
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  min-height: var(--usx-control-size-sm);
  padding: 0;
  border: 0;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
}

.chat-panel__header-action:hover,
.chat-panel__header-action:focus-visible {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.chat-panel__lane-icon-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-font-size-base);
  line-height: var(--usx-line-height-none);
  transition:
    color var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.chat-panel__lane-icon-toggle:hover {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-on-surface);
}

.chat-panel__lane-icon-toggle--dev {
  background: color-mix(in srgb, var(--usx-color-primary) 14%, transparent);
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}

.chat-panel__mode-toggle {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
}

.chat-panel__mode-btn {
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  border-radius: var(--usx-radius-md);
  padding: 0 var(--usx-spacing-sm);
  min-height: var(--usx-control-size-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  cursor: pointer;
  white-space: nowrap;
  line-height: var(--usx-line-height-tight);
  transition:
    color var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.chat-panel__mode-btn--active {
  background: color-mix(in srgb, var(--usx-color-primary) 14%, transparent);
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}

/* ─── Footer row: context + mode tabs ────────────────────────── */
.chat-panel__footer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) 0;
  flex-shrink: 0;
  min-height: var(--usx-touch-min);
}

/* ─── Context (inline pill) ───────────────────────────────────── */
.chat-panel__context {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-sm);
  min-height: var(--usx-control-size-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.chat-panel__context .u-icon {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-info);
}

.chat-panel__context-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-panel__context-badge {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-xs);
  min-height: calc(var(--usx-touch-min) - var(--usx-spacing-sm));
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 12%,
    transparent
  );
  border: none;
  border-radius: var(--usx-radius-full);
  color: var(--usx-color-primary);
  font-size: var(--usx-font-size-xs);
  cursor: default;
  flex-shrink: 0;
}

/* ─── Body ────────────────────────────────────────────────────── */
.chat-panel__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  container-type: size;
}

.chat-panel__start,
.chat-panel__messages {
  box-sizing: border-box;
  min-height: 100%;
  padding: var(--usx-spacing-xs) 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.chat-panel__start > p,
.chat-panel__messages > :first-child {
  margin-top: auto;
}

.chat-panel__start > p {
  margin-bottom: 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  color: var(--usx-color-on-surface);
}

.chat-panel__prompts {
  display: none;
}

@container (min-height: 10rem) {
  .chat-panel__prompts {
    display: flex;
    flex-wrap: wrap;
    gap: var(--usx-spacing-xs);
    padding-bottom: var(--usx-spacing-xs);
  }
}

.chat-panel__prompt.usx-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin: 0;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
}

.chat-panel__prompt.usx-btn:hover {
  background: var(--usx-color-surface-variant);
}

/* Message bubbles — single container */
.chat-panel__msg {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  max-width: 88%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-base);
  line-height: var(--usx-line-height-normal);
  animation: msgIn var(--usx-motion-duration-base) ease;
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
}

.chat-panel__msg--user {
  align-self: flex-end;
  background-color: var(--usx-color-primary);
  color: #fff;
  border-bottom-right-radius: var(--usx-radius-sm);
}

.chat-panel__msg--assistant {
  align-self: flex-start;
  background-color: color-mix(in srgb, var(--usx-color-surface) 70%, transparent);
  backdrop-filter: blur(8px);
  color: var(--usx-color-on-surface);
  border-bottom-left-radius: var(--usx-radius-sm);
}

.chat-panel__msg-row {
  display: flex;
  width: 100%;
}

.chat-panel__msg-body {
  flex: 1;
  min-width: 0;
  width: 100%;
  word-wrap: break-word;
}

.chat-panel__msg-body :deep(h1),
.chat-panel__msg-body :deep(h2),
.chat-panel__msg-body :deep(h3) {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-bold);
  margin: 0 0 var(--usx-spacing-xs);
}

.chat-panel__msg-body :deep(p) { margin: 0 0 var(--usx-spacing-xs); }
.chat-panel__msg-body :deep(p:last-child) { margin-bottom: 0; }

.chat-panel__msg-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--usx-transition-fast);
  margin-top: var(--usx-spacing-xs);
  padding-top: var(--usx-spacing-xs);
  border-top: 1px solid color-mix(in srgb, currentColor 15%, transparent);
  width: 100%;
}

.chat-panel__msg:hover .chat-panel__msg-actions {
  opacity: 1;
}

.chat-panel__msg-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.chat-panel__msg-action:hover {
  background-color: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

/* Loading */
.chat-panel__loading {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
}

.chat-panel__dot {
  width: var(--usx-spacing-xs);
  height: var(--usx-spacing-xs);
  border-radius: var(--usx-radius-full);
  background-color: var(--usx-color-on-surface-muted);
  animation: bounce var(--usx-motion-duration-pulse) infinite;
}
.chat-panel__dot:nth-child(2) {
  animation-delay: var(--usx-motion-delay-sm);
}
.chat-panel__dot:nth-child(3) {
  animation-delay: var(--usx-motion-delay-md);
}
@keyframes bounce {
  0%,
  80%,
  100% {
    opacity: 0.4;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(calc(var(--usx-spacing-xs) * -1.5));
  }
}

/* Composer */
.chat-panel__composer {
  flex-shrink: 0;
  position: relative;
}

.chat-panel__composer-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
}

.chat-panel__composer-row:focus-within {
  border-color: var(--usx-color-primary);
}

.chat-panel__composer-row .chat-panel__input {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  margin: 0;
  padding: 10px var(--usx-spacing-sm);
  border: 0;
  background: transparent;
  color: var(--usx-color-on-surface);
  font: inherit;
  line-height: var(--usx-line-height-tight);
  outline: none;
  box-shadow: none;
  resize: none;
  min-height: max(44px, var(--usx-touch-min));
  max-height: 160px;
}

.chat-panel__input::placeholder {
  color: var(--usx-color-on-surface-muted);
}

/* Composer actions row (below input) */
.chat-panel__composer-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
  margin-top: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.chat-panel__presentation {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  min-height: var(--usx-control-size-sm);
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
}

.chat-panel__presentation select {
  appearance: none;
  min-width: 5.5rem;
  margin: 0;
  padding: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: inherit;
  font: inherit;
}

/* Model selector pill */
.chat-panel__model-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-sm);
  min-height: var(--usx-control-size-sm);
  border: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-border) 50%, transparent);
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-surface) 60%, transparent);
  backdrop-filter: blur(12px);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  white-space: nowrap;
  transition:
    border-color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.chat-panel__model-btn:hover {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, var(--usx-color-surface));
}

.chat-panel__model-label {
  max-width: 9rem;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-panel__model-chevron {
  font-size: var(--usx-font-size-sm);
  opacity: 0.6;
}

/* Model dropdown */
.chat-panel__model-dropdown {
  position: absolute;
  bottom: 100%;
  right: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-xs);
  min-width: 200px;
  max-height: 240px;
  overflow-y: auto;
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  box-shadow: none;
  z-index: 10;
  padding: var(--usx-spacing-xs);
}

.chat-panel__model-option {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  width: 100%;
  padding: var(--usx-spacing-sm);
  border: none;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  text-align: left;
}

.chat-panel__model-option:hover {
  background: var(--usx-color-surface-variant);
}

.chat-panel__model-option--active {
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.chat-panel__model-provider {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.chat-panel__model-name {
  flex: 1;
  font-weight: var(--usx-font-weight-medium);
}

.chat-panel__send.usx-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: max(44px, var(--usx-touch-min));
  height: max(44px, var(--usx-touch-min));
  min-height: 0;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

.chat-panel__send.usx-btn:hover:not(:disabled) {
  background: var(--usx-color-primary-hover);
}

.chat-panel__send.usx-btn:disabled {
  opacity: 1;
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  cursor: not-allowed;
}

/* Scrollbar */
.chat-panel__body::-webkit-scrollbar {
  width: var(--usx-spacing-xs);
}
.chat-panel__body::-webkit-scrollbar-thumb {
  background-color: var(--usx-color-border);
  border-radius: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .chat-panel__msg {
    animation: none;
  }
  .chat-panel__dot {
    animation: none;
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .chat-panel {
    min-height: 0;
  }

  .chat-panel__header {
    min-height: 0;
    padding: 0;
  }

  .chat-panel__msg {
    max-width: 94%;
  }

  .chat-panel__presentation { display: none; }
}

@media (min-width: 641px) and (max-width: 768px) {
  .chat-panel__presentation { display: none; }
}
</style>

<style scoped>
.chat-panel__dev-context { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px; font-size: 12px; }
.chat-panel__dev-context select { max-width: 220px; }

.chat-panel__composer-actions, .chat-panel__footer-row { display: flex; align-items: center; gap: 8px; box-sizing: border-box; min-height: 40px; padding: 4px 0; margin: 0; font-family: var(--usx-font-family-sans); font-size: var(--usx-font-size-sm); line-height: 1; }
.chat-panel__composer-actions { flex-wrap: nowrap; }
.chat-panel__settings.usx-btn, .chat-panel__mode-btn.usx-btn, .chat-panel__presentation, .chat-panel__specialist-select { display: inline-flex; align-items: center; justify-content: center; gap: 4px; box-sizing: border-box; height: 32px; min-height: 32px; margin: 0; padding: 0 8px; border: 0; border-radius: var(--usx-radius-sm); background: transparent; box-shadow: none; color: var(--usx-color-on-surface-muted); font: inherit; line-height: 1; text-decoration: none; }
.chat-panel__presentation, .chat-panel__specialist-select { position: relative; padding: 0 4px; }
.chat-panel__presentation select, .chat-panel__specialist-select select { box-sizing: border-box; height: 32px; min-height: 32px; min-width: 0; width: auto; margin: 0; padding: 0 22px 0 4px; border: 0; border-radius: var(--usx-radius-sm); background: transparent; box-shadow: none; font: inherit; line-height: normal; }
.chat-panel__presentation-chevron { position: absolute; right: 4px; pointer-events: none; }
.chat-panel__composer-actions :deep(.u-icon), .chat-panel__footer-row :deep(.u-icon) { width: 18px; height: 18px; font-size: 18px; line-height: 1; }
.chat-panel__mode-toggle { gap: 2px; margin: 0; }
.chat-panel__mode-btn--active.usx-btn { background: var(--usx-color-surface-variant); color: var(--usx-color-primary); }
.chat-panel__settings:hover, .chat-panel__mode-btn:hover { background: var(--usx-color-surface-variant); }
.chat-panel__context { min-height: 32px; margin: 0; padding: 0; border: 0; background: transparent; font-size: inherit; line-height: 1; }
.chat-panel__send :deep(.u-icon), .chat-panel__header-action :deep(.u-icon), .chat-panel__msg-action :deep(.u-icon) { width: 20px; height: 20px; font-size: 20px; }
.chat-panel__header-action.usx-btn, .chat-panel__msg-action.usx-btn { width: 32px; height: 32px; min-height: 32px; margin: 0; padding: 0; border: 0; background: transparent; box-shadow: none; }
.chat-panel a:focus-visible, .chat-panel button:focus-visible, .chat-panel select:focus-visible { outline: 2px solid var(--usx-color-primary); outline-offset: 1px; }
</style>
