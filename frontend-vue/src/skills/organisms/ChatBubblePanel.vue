<template>
  <div class="chat-panel">
    <!-- ── Header ─────────────────────────────────────────────── -->
    <div class="chat-panel__header">
      <!-- Lane toggle: Chat / Dev -->
      <div class="chat-panel__lane-toggle-wrap">
        <span
          class="chat-panel__lane-label"
          :class="{ 'chat-panel__lane-label--active': activeLane === 'chat' }"
        >
          Chat
        </span>
        <button
          class="chat-panel__lane-toggle"
          :class="{ 'chat-panel__lane-toggle--dev': activeLane === 'dev' }"
          :aria-checked="activeLane === 'dev' ? 'true' : 'false'"
          aria-label="Toggle Chat/Dev lane"
          role="switch"
          :disabled="!devAvailable"
          :title="
            devAvailable
              ? 'Toggle between Chat and Dev lanes'
              : 'Dev lane unavailable in this context'
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
          Developer
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

    <!-- ── Context strip ──────────────────────────────────────── -->
    <div
      v-if="contextLabel && contextLabel.trim().toLowerCase() !== 'developer'"
      class="chat-panel__context"
    >
      <span class="material-symbols-outlined">location_on</span>
      <span class="chat-panel__context-text">{{ contextLabel }}</span>
      <span
        v-if="activeLane === 'dev' && currentTask"
        class="chat-panel__context-badge"
        title="Task context active"
      >
        <span class="material-symbols-outlined">assignment</span>
        {{ currentTask }}
      </span>
    </div>

    <!-- ── Messages ───────────────────────────────────────────── -->
    <div ref="messagesEl" class="chat-panel__messages">
      <!-- Empty state -->
      <div v-if="activeMessages.length === 0" class="chat-panel__empty">
        <span class="material-symbols-outlined chat-panel__empty-icon">
          {{ activeLane === "dev" ? "terminal" : "auto_awesome" }}
        </span>
        <p class="chat-panel__empty-title">
          {{
            activeLane === "dev"
              ? "Developer Assistant"
              : "Start a conversation"
          }}
        </p>
        <p class="chat-panel__empty-hint">
          {{
            activeLane === "dev"
              ? "Ask about code, run skills, manage repos. Context-aware."
              : "Ask anything. Outputs can go directly into your documents."
          }}
        </p>
        <!-- Dev lane shortcuts -->
        <div v-if="activeLane === 'dev'" class="chat-panel__shortcuts">
          <button
            v-for="sc in DEV_SHORTCUTS"
            :key="sc.label"
            class="chat-panel__shortcut"
            @click="insertShortcut(sc.prompt)"
          >
            <span class="material-symbols-outlined">{{ sc.icon }}</span>
            {{ sc.label }}
          </button>
        </div>
      </div>

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
  "send-chat": [message: string];
  "send-dev": [message: string];
  "toggle-dev-mode": [];
  close: [];
}>();

const shell = useShellStore();
const editorSurface = getEditorSurface();
const ws = useWorkspaceStore();
const { toast } = useToast();

const activeLane = ref<"chat" | "dev">("chat");
const inputText = ref("");
const messagesEl = ref<HTMLDivElement | null>(null);
const inputEl = ref<HTMLInputElement | null>(null);

const activeMessages = computed(() =>
  activeLane.value === "dev" ? props.devMessages : props.chatMessages,
);

const DEV_SHORTCUTS = [
  {
    label: "Audit ecosystem",
    icon: "analytics",
    prompt: "Run ecosystem audit and show me a summary",
  },
  {
    label: "Explain this file",
    icon: "description",
    prompt: "Explain the current file I have open",
  },
  {
    label: "Suggest next task",
    icon: "assignment",
    prompt: "Based on my current context, what should I work on next?",
  },
  {
    label: "Check build",
    icon: "build",
    prompt: "Check if there are any build errors in the current project",
  },
];

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
    emit("send-chat", text);
  }
  inputText.value = "";
}

function insertShortcut(prompt: string) {
  inputText.value = prompt;
  nextTick(() => inputEl.value?.focus());
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
  border-radius: var(--usx-radius-md);
  overflow: hidden;
}

/* ─── Header ──────────────────────────────────────────────────── */
.chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background-color: var(--usx-color-surface-variant);
  flex-shrink: 0;
  gap: var(--usx-spacing-xs);
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
  line-height: 1;
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
  width: calc(var(--usx-spacing-2xl) + var(--usx-spacing-sm));
  min-width: calc(var(--usx-spacing-2xl) + var(--usx-spacing-sm));
  height: calc(var(--usx-spacing-xl) + var(--usx-spacing-xs));
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
  width: var(--usx-spacing-lg);
  height: var(--usx-spacing-lg);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  box-shadow: 0 1px 2px
    color-mix(in srgb, var(--usx-color-background) 55%, transparent);
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
  transform: translateX(calc(var(--usx-spacing-lg) - var(--usx-spacing-xs)));
  background: var(--usx-color-primary);
  box-shadow: 0 1px 3px
    color-mix(in srgb, var(--usx-color-primary) 35%, transparent);
}

.chat-panel__dev-toggle {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px var(--usx-spacing-sm);
  border: none;
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  color: var(--usx-color-on-surface-muted);
  transition: all 150ms ease;
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
  width: 6px;
  height: 6px;
  border-radius: 50%;
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
  width: 24px;
  height: 24px;
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

/* ─── Context strip ───────────────────────────────────────────── */
.chat-panel__context {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 4px var(--usx-spacing-md);
  background-color: color-mix(in srgb, var(--usx-color-info) 6%, transparent);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.chat-panel__context .material-symbols-outlined {
  font-size: 14px;
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
  gap: 2px;
  padding: 1px var(--usx-spacing-xs);
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 12%,
    transparent
  );
  border: none;
  border-radius: var(--usx-radius-full);
  color: var(--usx-color-primary);
  font-size: 10px;
  cursor: default;
  flex-shrink: 0;
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

.chat-panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-lg);
}

.chat-panel__empty-icon {
  font-size: 36px;
  color: var(--usx-color-on-surface-muted);
  opacity: 0.4;
}

.chat-panel__empty-title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  margin: 0;
}

.chat-panel__empty-hint {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  line-height: 1.4;
  margin: 0;
}

/* Dev shortcuts grid */
.chat-panel__shortcuts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--usx-spacing-xs);
  margin-top: var(--usx-spacing-sm);
  width: 100%;
}

.chat-panel__shortcut {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: none;
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  color: var(--usx-color-on-surface-muted);
  text-align: left;
  transition: all 120ms ease;
}

.chat-panel__shortcut:hover {
  background-color: color-mix(
    in srgb,
    var(--usx-color-warning) 8%,
    transparent
  );
  color: var(--usx-color-warning);
}

/* Message bubbles */
.chat-panel__msg {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--usx-spacing-sm);
  animation: msgIn 200ms ease;
}

@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(6px);
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
  line-height: 1.5;
  word-wrap: break-word;
}

.chat-panel__msg-icon {
  font-size: 14px;
  opacity: 0.75;
  margin-top: 1px;
}

.chat-panel__msg-content {
  display: block;
  margin: 0;
}

.chat-panel__msg--user .chat-panel__msg-text {
  background-color: var(--usx-color-primary);
  color: white;
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
  gap: 2px;
  opacity: 0;
  transition: opacity 120ms ease;
}

.chat-panel__msg:hover .chat-panel__msg-actions {
  opacity: 1;
}

.chat-panel__msg-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: 13px;
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
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--usx-color-on-surface-muted);
  animation: bounce 1.4s infinite;
}
.chat-panel__dot:nth-child(2) {
  animation-delay: 0.2s;
}
.chat-panel__dot:nth-child(3) {
  animation-delay: 0.4s;
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
    transform: translateY(-6px);
  }
}

/* ─── Input ───────────────────────────────────────────────────── */
.chat-panel__input-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-xs) 0 var(--usx-spacing-sm);
  min-height: calc(var(--usx-spacing-xl) + var(--usx-spacing-sm));
  background-color: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid transparent;
  border-radius: var(--usx-radius-md);
  flex-shrink: 0;
  transition:
    border-color var(--usx-transition-fast),
    background-color var(--usx-transition-fast),
    box-shadow var(--usx-transition-fast);
}

.chat-panel__input-row:focus-within {
  border-color: color-mix(in srgb, var(--usx-color-primary) 48%, transparent);
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 6%,
    var(--usx-color-surface-variant)
  );
  box-shadow: 0 0 0 1px
    color-mix(in srgb, var(--usx-color-primary) 24%, transparent);
}

.chat-panel__input {
  flex: 1;
  height: calc(var(--usx-spacing-xl) + var(--usx-spacing-xs));
  padding: 0;
  border: none;
  border-radius: 0;
  background-color: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  line-height: 1.35;
  outline: none;
}

.chat-panel__input:focus {
  box-shadow: none;
}
.chat-panel__input::placeholder {
  color: var(--usx-color-on-surface-muted);
}

.chat-panel__send {
  display: grid;
  place-items: center;
  width: calc(var(--usx-spacing-lg) + var(--usx-spacing-lg));
  height: calc(var(--usx-spacing-lg) + var(--usx-spacing-lg));
  border: none;
  background: transparent;
  color: var(--usx-color-primary);
  border-radius: var(--usx-radius-full);
  padding: 0;
  cursor: pointer;
  transition:
    color var(--usx-transition-fast),
    background-color var(--usx-transition-fast),
    transform var(--usx-transition-fast);
  flex-shrink: 0;
}

.chat-panel__send--dev {
  color: var(--usx-color-warning);
}

.chat-panel__send .material-symbols-outlined {
  font-size: var(--usx-font-size-lg);
  line-height: 1;
}
.chat-panel__send:hover:not(:disabled) {
  background-color: color-mix(in srgb, currentColor 12%, transparent);
  transform: translateY(-1px);
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
  width: 4px;
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
