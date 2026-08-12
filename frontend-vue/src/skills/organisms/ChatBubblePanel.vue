<template>
  <div class="chat-panel">
    <!-- ── Header ─────────────────────────────────────────────── -->
    <div class="chat-panel__header">
      <!-- Lane toggle: Vault / Code -->
      <div class="chat-panel__lane-toggle-wrap">
        <span
          class="chat-panel__lane-label"
          :class="{ 'chat-panel__lane-label--active': activeLane === 'chat' }"
        >
          Vault
        </span>
        <button
          class="chat-panel__lane-toggle"
          :class="{ 'chat-panel__lane-toggle--dev': activeLane === 'dev' }"
          :aria-checked="activeLane === 'dev' ? 'true' : 'false'"
          aria-label="Toggle Vault/Code lane"
          role="switch"
          :disabled="!devAvailable"
          :title="
            devAvailable
              ? 'Toggle between Vault and Code lanes'
              : 'Code lane unavailable in this context'
          "
          @click="toggleLane"
        >
          <span class="chat-panel__lane-toggle-track">
            <span class="chat-panel__lane-toggle-thumb" />
          </span>
        </button>
        <span
          class="chat-panel__lane-label"
          :class="{ 'chat-panel__lane-label--active': activeLane === 'dev' }"
        >
          Code
        </span>
      </div>

      <!-- Dev mode toggle (only shown when uDev detected) -->
      <button
        v-if="devAvailable"
        class="chat-panel__dev-toggle"
        :class="{ 'chat-panel__dev-toggle--on': devModeOn }"
        :title="
          devModeOn
            ? 'Dev Mode ON — click to disable'
            : 'Dev Mode OFF — click to enable'
        "
        @click="emit('toggle-dev-mode')"
      >
        <span class="chat-panel__dev-dot" />
        Dev
      </button>
      <button
        class="chat-panel__close-btn"
        title="Close (Esc)"
        @click="closeChat"
      >
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <!-- ── Body: welcome or messages ──────────────────────────── -->
    <div class="chat-panel__body">
      <!-- Welcome (hidden once chat engaged) -->
      <div v-if="activeMessages.length === 0" class="chat-panel__welcome">
        <span class="chat-panel__welcome-icon">
          <span class="material-symbols-outlined">{{ activeLane === "dev" ? "terminal" : "auto_awesome" }}</span>
        </span>
        <h2 class="chat-panel__welcome-title">
          {{ activeLane === "dev" ? "Code Assistant" : "Hi, friend" }}
        </h2>
        <p class="chat-panel__welcome-hint">
          {{ activeLane === "dev" ? "Ask about code, run skills, manage repos." : "What would you like to explore today?" }}
        </p>

        <div class="chat-panel__prompts">
          <button
            v-for="card in activePromptCards"
            :key="card.label"
            class="chat-panel__prompt-card"
            @click="onPromptCard(card)"
          >
            {{ card.label }}
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div v-else ref="messagesEl" class="chat-panel__messages">
      <!-- Message list -->
      <article
        v-for="(msg, i) in activeMessages"
        :key="`${activeLane}-${i}`"
        class="chat-panel__msg"
        :class="`chat-panel__msg--${msg.role}`"
      >
        <div class="chat-panel__msg-text">
          <span class="material-symbols-outlined chat-panel__msg-icon">
            {{
              msg.role === "user"
                ? "person"
                : activeLane === "dev"
                  ? "terminal"
                  : "auto_awesome"
            }}
          </span>
          <p class="chat-panel__msg-content">{{ msg.content }}</p>
        </div>
        <!-- Output routing (assistant messages only) -->
        <div v-if="msg.role === 'assistant'" class="chat-panel__msg-actions">
          <button
            class="chat-panel__msg-action"
            title="Append to current document"
            @click="appendToDoc(msg.content)"
          >
            <span class="material-symbols-outlined">note_add</span>
          </button>
          <button
            class="chat-panel__msg-action"
            title="New note"
            @click="newNote(msg.content)"
          >
            <span class="material-symbols-outlined">post_add</span>
          </button>
          <button
            class="chat-panel__msg-action"
            title="Copy to clipboard"
            @click="copyText(msg.content)"
          >
            <span class="material-symbols-outlined">content_copy</span>
          </button>
        </div>
      </article>

      <!-- Loading dots -->
      <div v-if="loading" class="chat-panel__loading">
        <span class="chat-panel__dot" />
        <span class="chat-panel__dot" />
        <span class="chat-panel__dot" />
      </div>
    </div>
    </div>

    <!-- ── Footer row: context + mode tabs ────────────────────── -->
    <div class="chat-panel__footer-row">
      <span
        v-if="contextLabel && contextLabel.trim().toLowerCase() !== 'code'"
        class="chat-panel__context"
      >
        <span class="material-symbols-outlined">location_on</span>
        <span class="chat-panel__context-text">{{ contextLabel }}</span>
      </span>

      <div v-if="activeLane === 'chat'" class="chat-panel__mode-toggle" role="tablist" aria-label="Assistant mode">
        <button
          v-for="mode in CHAT_MODES"
          :key="mode.id"
          class="chat-panel__mode-btn"
          :class="{ 'chat-panel__mode-btn--active': activeChatMode === mode.id }"
          role="tab"
          :aria-selected="activeChatMode === mode.id ? 'true' : 'false'"
          @click="activeChatMode = mode.id"
        >
          {{ mode.label }}
        </button>
      </div>
    </div>

    <!-- ── Input ──────────────────────────────────────────────── -->
    <div class="chat-panel__input-row">
      <input
        ref="inputEl"
        v-model="inputText"
        class="chat-panel__input"
        :placeholder="
          activeLane === 'dev'
            ? 'Dev command or question… (/ for shortcuts)'
            : 'Message…'
        "
        @keydown.enter.exact.prevent="sendMessage"
        @keydown.shift.enter.prevent="inputText += '\n'"
        @input="onInputChange"
      />
      <button
        class="chat-panel__send"
        :class="{ 'chat-panel__send--dev': activeLane === 'dev' }"
        :disabled="!inputText.trim() || loading"
        title="Send (Enter)"
        @click="sendMessage"
      >
        <span class="material-symbols-outlined">send</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { useShellStore } from "../../stores/shell";
import { getEditorSurface } from "../../composables/useEditorSurface";
import { useWorkspaceStore } from "../../stores/workspace";
import { useToast } from "../../composables/useToast";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const props = withDefaults(
  defineProps<{
    chatMessages?: Message[];
    devMessages?: Message[];
    loading?: boolean;
    devAvailable?: boolean;
    devModeOn?: boolean;
    contextLabel?: string;
    currentTask?: string;
  }>(),
  {
    chatMessages: () => [],
    devMessages: () => [],
    loading: false,
    devAvailable: false,
    devModeOn: false,
    contextLabel: "",
    currentTask: "",
  },
);

const emit = defineEmits<{
  "send-chat": [message: string, mode: "chat" | "plan" | "act" | "workflow"];
  "send-dev": [message: string];
  "toggle-dev-mode": [];
  close: [];
}>();

const shell = useShellStore();
const editorSurface = getEditorSurface();
const ws = useWorkspaceStore();
const { toast } = useToast();

const activeLane = ref<"chat" | "dev">("chat");
const activeChatMode = ref<"chat" | "plan" | "act" | "workflow">("chat");
const inputText = ref("");
const messagesEl = ref<HTMLDivElement | null>(null);
const inputEl = ref<HTMLInputElement | null>(null);

const CHAT_MODES = [
  { id: "chat", label: "Chat" },
  { id: "plan", label: "Research" },
  { id: "act", label: "Act" },
  { id: "workflow", label: "Workflow" },
] as const;

interface PromptCard {
  label: string;
  icon: string;
  hint: string;
  prompt: string;
  mode?: "chat" | "plan" | "act" | "workflow";
}

const CHAT_PROMPTS: PromptCard[] = [
  {
    label: "Research a topic",
    icon: "travel_explore",
    hint: "Deep-dive with sources",
    prompt: "Research and summarize ",
    mode: "plan",
  },
  {
    label: "Draft content",
    icon: "edit_note",
    hint: "Write prose or docs",
    prompt: "Write a draft about ",
    mode: "chat",
  },
  {
    label: "Explain a concept",
    icon: "lightbulb",
    hint: "Simple breakdown",
    prompt: "Explain ",
    mode: "chat",
  },
  {
    label: "Plan a workflow",
    icon: "account_tree",
    hint: "Step-by-step pipeline",
    prompt: "Plan a workflow for ",
    mode: "workflow",
  },
  {
    label: "Summarize a doc",
    icon: "summarize",
    hint: "Condense to key points",
    prompt: "Summarize the following: ",
    mode: "act",
  },
  {
    label: "Quick brainstorm",
    icon: "psychology",
    hint: "Generate ideas fast",
    prompt: "Brainstorm ideas for ",
    mode: "chat",
  },
];

const DEV_PROMPTS: PromptCard[] = [
  {
    label: "Audit ecosystem",
    icon: "analytics",
    hint: "Check health & services",
    prompt: "Run ecosystem audit and show me a summary",
  },
  {
    label: "Explain this file",
    icon: "description",
    hint: "Current open file",
    prompt: "Explain the current file I have open",
  },
  {
    label: "Suggest next task",
    icon: "assignment",
    hint: "Smart task picking",
    prompt: "Based on my current context, what should I work on next?",
  },
  {
    label: "Check build",
    icon: "build",
    hint: "Lint and type errors",
    prompt: "Check if there are any build errors in the current project",
  },
  {
    label: "Refactor code",
    icon: "auto_fix",
    hint: "Clean up current file",
    prompt: "Refactor the current file for readability",
  },
  {
    label: "Run a skill",
    icon: "extension",
    hint: "Trigger a named skill",
    prompt: "Run the skill: ",
  },
];

const activePromptCards = computed<PromptCard[]>(() =>
  activeLane.value === "dev" ? DEV_PROMPTS : CHAT_PROMPTS,
);

const activeMessages = computed(() =>
  activeLane.value === "dev" ? props.devMessages : props.chatMessages,
);

function onPromptCard(card: PromptCard) {
  if (card.mode) activeChatMode.value = card.mode;
  inputText.value = card.prompt;
  nextTick(() => inputEl.value?.focus());
}

// Auto-scroll on new messages
watch(
  activeMessages,
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
  if (activeLane.value === "dev") {
    emit("send-dev", text);
  } else {
    emit("send-chat", text, activeChatMode.value);
  }
  inputText.value = "";
}

function onInputChange() {
  // Slash command hint — future feature placeholder
}

function toggleLane() {
  activeLane.value = activeLane.value === "chat" ? "dev" : "chat";
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
  background-color: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  overflow: hidden;
}

/* ─── Header ──────────────────────────────────────────────────── */
.chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm);
  background-color: var(--usx-color-surface-variant);
  flex-shrink: 0;
  gap: var(--usx-spacing-xs);
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
  border-radius: var(--usx-radius-full);
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

.chat-panel__lane-toggle-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  white-space: nowrap;
  flex-shrink: 0;
}

.chat-panel__lane-label {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-none);
  white-space: nowrap;
}

.chat-panel__lane-label--active {
  color: var(--usx-color-on-surface);
  font-weight: var(--usx-font-weight-medium);
}

.chat-panel__lane-static {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface);
}

.chat-panel__lane-toggle {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  min-height: 0;
}

.chat-panel__lane-toggle:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-panel__lane-toggle-track {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  width: calc(var(--usx-spacing-xl) + var(--usx-spacing-lg));
  min-width: calc(var(--usx-spacing-xl) + var(--usx-spacing-lg));
  height: calc(var(--usx-spacing-lg) + var(--usx-spacing-xs));
  border-radius: var(--usx-radius-full);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: color-mix(
    in srgb,
    var(--usx-color-on-surface-muted) 16%,
    var(--usx-color-surface)
  );
  padding: 0 var(--usx-spacing-xs);
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    box-shadow var(--usx-transition-fast);
}

.chat-panel__lane-toggle-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-spacing-md);
  height: var(--usx-spacing-md);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  box-shadow: var(--usx-shadow-sm);
  transform: translateX(0);
  transition:
    transform var(--usx-transition-fast),
    background var(--usx-transition-fast),
    box-shadow var(--usx-transition-fast);
}

.chat-panel__lane-toggle--dev .chat-panel__lane-toggle-track {
  background: color-mix(in srgb, var(--usx-color-primary) 28%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-primary) 70%, transparent);
  box-shadow: 0 0 0 1px
    color-mix(in srgb, var(--usx-color-primary) 24%, transparent);
}

.chat-panel__lane-toggle--dev .chat-panel__lane-toggle-thumb {
  transform: translateX(calc(var(--usx-spacing-lg) - var(--usx-spacing-sm)));
  background: var(--usx-color-primary);
  box-shadow: var(--usx-shadow-sm);
}

.chat-panel__dev-toggle {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  min-height: var(--usx-touch-min);
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid transparent;
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-surface) 86%, var(--usx-color-surface-variant));
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  font-family: var(--usx-font-family-sans);
  color: var(--usx-color-on-surface-muted);
  transition:
    color var(--usx-transition-fast),
    background-color var(--usx-transition-fast),
    border-color var(--usx-transition-fast);
}

.chat-panel__dev-toggle--on {
  background-color: color-mix(
    in srgb,
    var(--usx-color-warning) 12%,
    transparent
  );
  border-color: var(--usx-color-warning);
  color: var(--usx-color-warning);
}

.chat-panel__dev-dot {
  width: var(--usx-spacing-xs);
  height: var(--usx-spacing-xs);
  border-radius: var(--usx-radius-full);
  background-color: var(--usx-color-border);
  flex-shrink: 0;
}

.chat-panel__dev-toggle--on .chat-panel__dev-dot {
  background-color: var(--usx-color-warning);
}

.chat-panel__close-btn {
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
}

.chat-panel__close-btn:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

/* ─── Footer row: context + mode tabs ────────────────────────── */
.chat-panel__footer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
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

.chat-panel__context .material-symbols-outlined {
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
}

/* ─── Welcome zone ─────────────────────────────────────────────── */
.chat-panel__welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xl) var(--usx-spacing-lg);
  padding-bottom: var(--usx-spacing-2xl);
}

.chat-panel__welcome-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: calc(var(--usx-touch-min) + var(--usx-spacing-lg));
  height: calc(var(--usx-touch-min) + var(--usx-spacing-lg));
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
  color: var(--usx-color-primary);
  margin-bottom: var(--usx-spacing-sm);
}

.chat-panel__welcome-icon .material-symbols-outlined {
  font-size: calc(var(--usx-font-size-2xl) + var(--usx-font-size-xs));
}

.chat-panel__welcome-title {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-on-surface);
  margin: 0;
  text-align: center;
}

.chat-panel__welcome-hint {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-normal);
  margin: 0 0 var(--usx-spacing-md);
  text-align: center;
  max-width: 28ch;
}

/* ─── Prompt cards (suggestion pills) ─────────────────────────── */
.chat-panel__prompts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  max-width: 32rem;
}

.chat-panel__prompt-card {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  padding: 0 var(--usx-spacing-md);
  min-height: var(--usx-control-size-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  white-space: nowrap;
  transition:
    border-color var(--usx-transition-fast),
    background var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.chat-panel__prompt-card:hover {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, var(--usx-color-surface));
  transform: translateY(calc(var(--usx-border-width) * -1));
}

/* ─── Messages ────────────────────────────────────────────────── */
.chat-panel__messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

/* Message bubbles */
.chat-panel__msg {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--usx-spacing-sm);
  animation: msgIn var(--usx-motion-duration-base) ease;
}

@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(calc(var(--usx-spacing-xs) * 1.5));
  }
}

.chat-panel__msg--user {
  align-items: flex-end;
}

.chat-panel__msg-text {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-xs);
  max-width: 86%;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-normal);
  word-wrap: break-word;
}

.chat-panel__msg-icon {
  font-size: var(--usx-font-size-sm);
  opacity: 0.75;
  margin-top: var(--usx-spacing-1);
}

.chat-panel__msg-content {
  display: block;
  margin: 0;
}

.chat-panel__msg--user .chat-panel__msg-text {
  background-color: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-radius: var(--usx-radius-md) var(--usx-radius-sm) var(--usx-radius-md)
    var(--usx-radius-md);
}
.chat-panel__msg--assistant .chat-panel__msg-text {
  background-color: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  border-radius: var(--usx-radius-sm) var(--usx-radius-md) var(--usx-radius-md)
    var(--usx-radius-md);
}

.chat-panel__msg-actions {
  display: flex;
  gap: var(--usx-spacing-1);
  opacity: 0;
  transition: opacity var(--usx-transition-fast);
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

/* ─── Input ───────────────────────────────────────────────────── */
.chat-panel__input-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin: 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-sm);
  background-color: var(--usx-color-surface);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}

.chat-panel__input-row:focus-within {
  background-color: color-mix(in srgb, var(--usx-color-surface) 90%, var(--usx-color-surface-variant));
}

.chat-panel__input {
  flex: 1;
  min-width: 0;
  box-sizing: border-box;
  height: calc(var(--usx-touch-min-sm) - var(--usx-border-width-thick)) !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md) !important;
  border: var(--usx-border-width) solid transparent;
  border-radius: var(--usx-radius-md);
  background-color: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  line-height: var(--usx-line-height-tight);
  outline: none;
}

.chat-panel__input:focus {
  border-color: color-mix(in srgb, var(--usx-color-primary) 48%, transparent);
}
.chat-panel__input::placeholder {
  color: var(--usx-color-on-surface-muted);
}

.chat-panel__send {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: calc(var(--usx-touch-min-sm) - var(--usx-border-width-thick)) !important;
  height: calc(var(--usx-touch-min-sm) - var(--usx-border-width-thick)) !important;
  min-height: 0 !important;
  margin: 0 !important;
  border: var(--usx-border-width) solid transparent;
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
  color: var(--usx-color-primary);
  border-radius: var(--usx-radius-md);
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  transition:
    color var(--usx-transition-fast),
    background-color var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.chat-panel__send--dev {
  background: color-mix(in srgb, var(--usx-color-warning) 12%, transparent);
  color: var(--usx-color-warning);
}

.chat-panel__send .material-symbols-outlined {
  font-size: var(--usx-font-size-lg);
  line-height: var(--usx-line-height-none);
}
.chat-panel__send:hover:not(:disabled) {
  background-color: color-mix(in srgb, currentColor 20%, transparent);
  transform: translateY(calc(var(--usx-border-width) * -1));
}

.chat-panel__send:active:not(:disabled) {
  transform: translateY(0);
}
.chat-panel__send:disabled {
  color: var(--usx-color-on-surface-muted);
  opacity: 0.45;
  cursor: not-allowed;
}

/* Scrollbar */
.chat-panel__messages::-webkit-scrollbar {
  width: var(--usx-spacing-xs);
}
.chat-panel__messages::-webkit-scrollbar-thumb {
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
</style>
