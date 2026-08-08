<template>
  <div class="chat-panel">
    <!-- ── Header ─────────────────────────────────────────────── -->
    <div class="chat-panel__header">
      <!-- Lane tabs: Chat / Dev (Dev hidden unless devMode available) -->
      <div class="chat-panel__lanes">
        <button
          class="chat-panel__lane-btn"
          :class="{ 'chat-panel__lane-btn--active': activeLane === 'chat' }"
          @click="activeLane = 'chat'"
        >
          <span class="material-symbols-outlined">chat</span>
          Chat
        </button>
        <button
          v-if="devAvailable"
          class="chat-panel__lane-btn chat-panel__lane-btn--dev"
          :class="{ 'chat-panel__lane-btn--active': activeLane === 'dev' }"
          @click="activeLane = 'dev'"
        >
          <span class="material-symbols-outlined">code</span>
          Dev
        </button>
      </div>

      <div class="chat-panel__header-right">
        <!-- Dev mode toggle (only shown when uDev detected) -->
        <button
          v-if="devAvailable"
          class="chat-panel__dev-toggle"
          :class="{ 'chat-panel__dev-toggle--on': devModeOn }"
          :title="devModeOn ? 'Dev Mode ON — click to disable' : 'Dev Mode OFF — click to enable'"
          @click="emit('toggle-dev-mode')"
        >
          <span class="chat-panel__dev-dot" />
          Dev
        </button>
        <button class="chat-panel__close-btn" title="Close (Esc)" @click="closeChat">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
    </div>

    <!-- ── Context strip ──────────────────────────────────────── -->
    <div v-if="contextLabel" class="chat-panel__context">
      <span class="material-symbols-outlined">location_on</span>
      <span class="chat-panel__context-text">{{ contextLabel }}</span>
      <button
        v-if="activeLane === 'dev' && currentTask"
        class="chat-panel__context-badge"
        title="Task context active"
      >
        <span class="material-symbols-outlined">assignment</span>
        {{ currentTask }}
      </button>
    </div>

    <!-- ── Messages ───────────────────────────────────────────── -->
    <div ref="messagesEl" class="chat-panel__messages">
      <!-- Empty state -->
      <div v-if="activeMessages.length === 0" class="chat-panel__empty">
        <span class="material-symbols-outlined chat-panel__empty-icon">
          {{ activeLane === 'dev' ? 'terminal' : 'auto_awesome' }}
        </span>
        <p class="chat-panel__empty-title">
          {{ activeLane === 'dev' ? 'Developer Assistant' : 'Start a conversation' }}
        </p>
        <p class="chat-panel__empty-hint">
          {{ activeLane === 'dev'
            ? 'Ask about code, run skills, manage repos. Context-aware.'
            : 'Ask anything. Outputs can go directly into your documents.' }}
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
      <div
        v-for="(msg, i) in activeMessages"
        :key="`${activeLane}-${i}`"
        class="chat-panel__msg"
        :class="`chat-panel__msg--${msg.role}`"
      >
        <div class="chat-panel__msg-avatar">
          <span class="material-symbols-outlined">
            {{ msg.role === 'user' ? 'person' : activeLane === 'dev' ? 'terminal' : 'auto_awesome' }}
          </span>
        </div>
        <div class="chat-panel__msg-body">
          <div class="chat-panel__msg-text">{{ msg.content }}</div>
          <!-- Output routing (assistant messages only) -->
          <div v-if="msg.role === 'assistant'" class="chat-panel__msg-actions">
            <button class="chat-panel__msg-action" title="Append to current document" @click="appendToDoc(msg.content)">
              <span class="material-symbols-outlined">note_add</span>
            </button>
            <button class="chat-panel__msg-action" title="New note" @click="newNote(msg.content)">
              <span class="material-symbols-outlined">post_add</span>
            </button>
            <button class="chat-panel__msg-action" title="Copy to clipboard" @click="copyText(msg.content)">
              <span class="material-symbols-outlined">content_copy</span>
            </button>
          </div>
        </div>
      </div>

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
        :placeholder="activeLane === 'dev' ? 'Dev command or question… (/ for shortcuts)' : 'Message…'"
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

interface Message { role: "user" | "assistant"; content: string }

const props = withDefaults(defineProps<{
  chatMessages?: Message[];
  devMessages?: Message[];
  loading?: boolean;
  devAvailable?: boolean;
  devModeOn?: boolean;
  contextLabel?: string;
  currentTask?: string;
}>(), {
  chatMessages: () => [],
  devMessages: () => [],
  loading: false,
  devAvailable: false,
  devModeOn: false,
  contextLabel: "",
  currentTask: "",
});

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
  { label: "Audit ecosystem", icon: "analytics",   prompt: "Run ecosystem audit and show me a summary" },
  { label: "Explain this file", icon: "description", prompt: "Explain the current file I have open" },
  { label: "Suggest next task", icon: "assignment",  prompt: "Based on my current context, what should I work on next?" },
  { label: "Check build",       icon: "build",       prompt: "Check if there are any build errors in the current project" },
];

// Auto-scroll on new messages
watch(activeMessages, async () => {
  await nextTick();
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
}, { deep: true });

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
  const node = ws.tree.flatMap((n) => n.children ?? []).find((n) => n.name === filename);
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
  border-radius: var(--usx-radius-lg);
  overflow: hidden;
}

/* ─── Header ──────────────────────────────────────────────────── */
.chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface-variant);
  flex-shrink: 0;
  gap: var(--usx-spacing-xs);
}

.chat-panel__lanes {
  display: flex;
  gap: 2px;
  background-color: var(--usx-color-background);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: 2px;
}

.chat-panel__lane-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px var(--usx-spacing-sm);
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  color: var(--usx-color-on-surface-muted);
  transition: all 120ms ease;
  white-space: nowrap;
}

.chat-panel__lane-btn--active {
  background-color: var(--usx-color-surface);
  color: var(--usx-color-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,.1);
}

.chat-panel__lane-btn--dev.chat-panel__lane-btn--active {
  color: var(--usx-color-warning);
}

.chat-panel__header-right {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.chat-panel__dev-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: transparent;
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  color: var(--usx-color-on-surface-muted);
  transition: all 150ms ease;
}

.chat-panel__dev-toggle--on {
  background-color: color-mix(in srgb, var(--usx-color-warning) 12%, transparent);
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
  border-bottom: 1px solid var(--usx-color-border);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.chat-panel__context .material-symbols-outlined { font-size: 14px; color: var(--usx-color-info); }

.chat-panel__context-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.chat-panel__context-badge {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 1px var(--usx-spacing-xs);
  background-color: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
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
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-sans);
  color: var(--usx-color-on-surface-muted);
  text-align: left;
  transition: all 120ms ease;
}

.chat-panel__shortcut:hover {
  background-color: color-mix(in srgb, var(--usx-color-warning) 8%, transparent);
  border-color: var(--usx-color-warning);
  color: var(--usx-color-warning);
}

/* Message bubbles */
.chat-panel__msg {
  display: flex;
  gap: var(--usx-spacing-sm);
  animation: msgIn 200ms ease;
}

@keyframes msgIn { from { opacity: 0; transform: translateY(6px); } }

.chat-panel__msg--user { flex-direction: row-reverse; }

.chat-panel__msg-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: var(--usx-radius-full);
  flex-shrink: 0;
  font-size: 14px;
}

.chat-panel__msg--user .chat-panel__msg-avatar { background-color: var(--usx-color-primary); color: white; }
.chat-panel__msg--assistant .chat-panel__msg-avatar { background-color: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); }

.chat-panel__msg-body { display: flex; flex-direction: column; gap: 3px; max-width: 82%; }

.chat-panel__msg-text {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  line-height: 1.5;
  word-wrap: break-word;
}

.chat-panel__msg--user .chat-panel__msg-text { background-color: var(--usx-color-primary); color: white; border-radius: var(--usx-radius-md) var(--usx-radius-sm) var(--usx-radius-md) var(--usx-radius-md); }
.chat-panel__msg--assistant .chat-panel__msg-text { background-color: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); border-radius: var(--usx-radius-sm) var(--usx-radius-md) var(--usx-radius-md) var(--usx-radius-md); }

.chat-panel__msg-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 120ms ease;
}

.chat-panel__msg:hover .chat-panel__msg-actions { opacity: 1; }

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

.chat-panel__msg-action:hover { background-color: var(--usx-color-border); color: var(--usx-color-on-surface); }

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
.chat-panel__dot:nth-child(2) { animation-delay: 0.2s; }
.chat-panel__dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,80%,100%{opacity:.4;transform:translateY(0)} 40%{opacity:1;transform:translateY(-6px)} }

/* ─── Input ───────────────────────────────────────────────────── */
.chat-panel__input-row {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm);
  border-top: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface);
  flex-shrink: 0;
}

.chat-panel__input {
  flex: 1;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background-color: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  outline: none;
}

.chat-panel__input:focus { border-color: var(--usx-color-primary); }
.chat-panel__input::placeholder { color: var(--usx-color-on-surface-muted); }

.chat-panel__send {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  background-color: var(--usx-color-primary);
  color: white;
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  transition: all 150ms ease;
  flex-shrink: 0;
}

.chat-panel__send--dev { background-color: var(--usx-color-warning); }
.chat-panel__send:hover:not(:disabled) { opacity: 0.85; transform: scale(1.05); }
.chat-panel__send:disabled { opacity: 0.4; cursor: not-allowed; }

/* Scrollbar */
.chat-panel__messages::-webkit-scrollbar { width: 4px; }
.chat-panel__messages::-webkit-scrollbar-thumb { background-color: var(--usx-color-border); border-radius: 2px; }

@media (prefers-reduced-motion: reduce) {
  .chat-panel__msg { animation: none; }
  .chat-panel__dot { animation: none; opacity: 1; }
}
</style>
