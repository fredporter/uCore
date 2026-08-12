<template>
  <div class="chat-panel">
    <!-- ── Header (compact, centered lane toggle) ──────────────── -->
    <div class="chat-panel__header">
      <!-- Left: dev toggle -->
      <div class="chat-panel__header-side">
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
      </div>

      <!-- Center: Vault / Code lane toggle -->
      <div class="chat-panel__lane-toggle-wrap">
        <span
          class="chat-panel__lane-label"
          :class="{ 'chat-panel__lane-label--active': activeLane === 'chat' }"
        >Vault</span>
        <button
          class="chat-panel__lane-toggle"
          :class="{ 'chat-panel__lane-toggle--dev': activeLane === 'dev' }"
          :aria-checked="activeLane === 'dev' ? 'true' : 'false'"
          aria-label="Toggle Vault/Code lane"
          role="switch"
          :disabled="!devAvailable"
          :title="devAvailable ? 'Toggle between Vault and Code lanes' : 'Code lane unavailable in this context'"
          @click="toggleLane"
        >
          <span class="chat-panel__lane-toggle-track">
            <span class="chat-panel__lane-toggle-thumb" />
          </span>
        </button>
        <span
          class="chat-panel__lane-label"
          :class="{ 'chat-panel__lane-label--active': activeLane === 'dev' }"
        >Code</span>
      </div>

      <!-- Right: empty (close moved to overlay top-right) -->
      <div class="chat-panel__header-side chat-panel__header-side--right" />
    </div>

    <!-- ── Body ──────────────────────────────────────────────── -->
    <div class="chat-panel__body">
      <div v-if="activeMessages.length === 0" class="chat-panel__empty" />

      <div v-else ref="messagesEl" class="chat-panel__messages">
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
            <button class="chat-panel__msg-action" title="Append to current document" @click="appendToDoc(msg.content)">
              <UIcon name="note_add" />
            </button>
            <button class="chat-panel__msg-action" title="New note" @click="newNote(msg.content)">
              <UIcon name="post_add" />
            </button>
            <button class="chat-panel__msg-action" title="Copy to clipboard" @click="copyText(msg.content)">
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

    <!-- ── Composer (Nuxt-style): textarea + model + send ─────── -->
    <div class="chat-panel__composer">
      <div class="chat-panel__composer-row">
        <textarea
          ref="inputEl"
          v-model="inputText"
          class="chat-panel__input"
          :placeholder="
            activeLane === 'dev'
              ? 'Dev command or question… (/ for shortcuts)'
              : 'Type your message here…'
          "
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.shift.enter.prevent="inputText += '\n'"
          @input="autoResize"
        />
        <div class="chat-panel__composer-actions">
          <button
            v-if="activeLane === 'chat'"
            class="chat-panel__model-btn"
            @click="modelPickerOpen = !modelPickerOpen"
            :title="currentModelLabel"
          >
            <UIcon name="smart_toy" />
            <span class="chat-panel__model-label">{{ currentModelLabel }}</span>
            <UIcon name="expand_more" class="chat-panel__model-chevron" />
          </button>
          <button
            class="chat-panel__send"
            :class="{ 'chat-panel__send--dev': activeLane === 'dev' }"
            :disabled="!inputText.trim() || loading"
            title="Send (Enter)"
            @click="sendMessage"
          >
            <UIcon name="send" />
          </button>
        </div>
      </div>

      <!-- Model picker dropdown -->
      <div v-if="modelPickerOpen" class="chat-panel__model-dropdown">
        <button
          v-for="model in availableModels"
          :key="model.id"
          class="chat-panel__model-option"
          :class="{ 'chat-panel__model-option--active': model.id === selectedModelId }"
          @click="selectModel(model.id)"
        >
          <span class="chat-panel__model-provider">{{ model.provider }}</span>
          <span class="chat-panel__model-name">{{ model.name }}</span>
          <UIcon v-if="model.id === selectedModelId" name="check" />
        </button>
      </div>
    </div>

    <!-- ── Footer: context + mode tabs ────────────────────────── -->
    <div class="chat-panel__footer-row">
      <span
        v-if="contextLabel && contextLabel.trim().toLowerCase() !== 'code'"
        class="chat-panel__context"
      >
        <UIcon name="location_on" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { useShellStore } from "../../stores/shell";
import { getEditorSurface } from "../../composables/useEditorSurface";
import { useWorkspaceStore } from "../../stores/workspace";
import { useToast } from "../../composables/useToast";
import { useChatStore } from "../../stores/chat";
import { renderMarkdown } from "../../composables/useMarkdown";
import UIcon from "../atoms/UIcon.vue";

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
const chatStore = useChatStore();
const editorSurface = getEditorSurface();
const ws = useWorkspaceStore();
const { toast } = useToast();

const activeLane = ref<"chat" | "dev">("chat");
const activeChatMode = ref<"chat" | "plan" | "act" | "workflow">("chat");
const messagesEl = ref<HTMLDivElement | null>(null);
const inputEl = ref<HTMLTextAreaElement | null>(null);
const modelPickerOpen = ref(false);
const selectedModelId = ref(chatStore.selectedModel);

const inputText = computed({
  get: () => chatStore.input,
  set: (v: string) => { chatStore.input = v; },
});

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

// ─── Textarea auto-resize ─────────────────────────────────────
function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement;
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
}

// ─── Simple message content render ────────────────────────────
function renderMsgContent(content: string): string {
  return renderMarkdown(content);
}

const CHAT_MODES = [
  { id: "chat", label: "Chat" },
  { id: "plan", label: "Research" },
  { id: "act", label: "Act" },
  { id: "workflow", label: "Workflow" },
] as const;

const activeMessages = computed(() =>
  activeLane.value === "dev" ? props.devMessages : props.chatMessages,
);

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
  const text = chatStore.input.trim();
  if (!text || props.loading) return;
  if (activeLane.value === "dev") {
    emit("send-dev", text);
  } else {
    emit("send-chat", text, activeChatMode.value);
  }
  chatStore.input = "";
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
  background: transparent;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

/* ─── Header (compact, centered lane toggle) ──────────────────── */
.chat-panel__header {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: transparent;
  flex-shrink: 0;
  min-height: 36px;
  position: relative;
}

.chat-panel__header-side {
  display: flex;
  align-items: center;
  min-width: 48px;
}

.chat-panel__header-side--right {
  justify-content: flex-end;
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

.chat-panel__lane-toggle-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  white-space: nowrap;
  flex-shrink: 0;
  padding: 2px var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
}

.chat-panel__lane-label {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-none);
  white-space: nowrap;
  padding: 0 2px;
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
}

.chat-panel__empty {
  flex: 1;
}

/* ─── Messages ────────────────────────────────────────────────── */
.chat-panel__messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-sm) 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

/* Message bubbles — single container */
.chat-panel__msg {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  max-width: 88%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
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

/* ─── Composer (frameless, glass input) ────────────────────────── */
.chat-panel__composer {
  flex-shrink: 0;
}

.chat-panel__composer-row {
  display: flex;
  align-items: flex-end;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) 0;
}

.chat-panel__input {
  flex: 1;
  min-width: 0;
  box-sizing: border-box;
  margin: 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-border) 50%, transparent);
  border-radius: var(--usx-radius-lg);
  background: color-mix(in srgb, var(--usx-color-surface) 60%, transparent);
  backdrop-filter: blur(12px);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-base);
  font-family: var(--usx-font-family-sans);
  line-height: var(--usx-line-height-normal);
  outline: none;
  resize: none;
  min-height: calc(var(--usx-touch-min-sm) + var(--usx-spacing-xs));
  max-height: 160px;
}

.chat-panel__input:focus {
  border-color: var(--usx-color-primary);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--usx-color-primary) 20%, transparent);
}
.chat-panel__input::placeholder {
  color: var(--usx-color-on-surface-muted);
}

/* Composer actions row */
.chat-panel__composer-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
}

/* Model selector pill */
.chat-panel__model-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-sm);
  min-height: calc(var(--usx-touch-min-sm) + var(--usx-spacing-xs));
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
  max-width: 80px;
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
  box-shadow: var(--usx-shadow-lg);
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

/* Send button */
.chat-panel__send {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: calc(var(--usx-touch-min-sm) + var(--usx-spacing-xs));
  height: calc(var(--usx-touch-min-sm) + var(--usx-spacing-xs));
  min-height: 0;
  margin: 0;
  border: none;
  background: var(--usx-color-primary);
  color: #fff;
  border-radius: var(--usx-radius-lg);
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  transition:
    background var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.chat-panel__send--dev {
  background: var(--usx-color-warning);
}

.chat-panel__send:hover:not(:disabled) {
  background: var(--usx-color-primary-hover);
  transform: scale(1.04);
}

.chat-panel__send--dev:hover:not(:disabled) {
  background: color-mix(in srgb, var(--usx-color-warning) 85%, black);
}

.chat-panel__send:active:not(:disabled) {
  transform: scale(0.96);
}
.chat-panel__send:disabled {
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

@media (max-width: 640px) {
  .chat-panel__header {
    padding: var(--usx-spacing-xs);
  }

  .chat-panel__header-side {
    min-width: 32px;
  }

  .chat-panel__lane-label {
    display: none;
  }

  .chat-panel__composer-row {
    gap: var(--usx-spacing-xs);
    padding: var(--usx-spacing-xs) 0;
  }

  .chat-panel__model-btn {
    padding: 0 var(--usx-spacing-xs);
  }

  .chat-panel__model-label {
    display: none;
  }

  .chat-panel__model-chevron {
    display: none;
  }

  .chat-panel__msg {
    max-width: 94%;
  }
}
</style>
