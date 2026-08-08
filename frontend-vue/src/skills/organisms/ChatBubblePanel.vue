<template>
  <div class="chat-bubble-panel">
    <!-- Panel header: title, close button -->
    <div class="chat-bubble-panel__header">
      <div class="chat-bubble-panel__title">
        <UIcon name="chat" />
        <span>Developer Assistant</span>
      </div>
      <button
        class="chat-bubble-panel__close"
        title="Close (Esc)"
        @click="closeChat"
      >
        <UIcon name="close" />
      </button>
    </div>

    <!-- Chat messages area -->
    <div class="chat-bubble-panel__messages" ref="messagesEl">
      <div v-if="messages.length === 0" class="chat-bubble-panel__empty">
        <UIcon name="chat" />
        <h3>Start a conversation</h3>
        <p>Ask for help with code, research, or tasks</p>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-bubble-panel__message"
        :class="`chat-bubble-panel__message--${msg.role}`"
      >
        <div class="chat-bubble-panel__message-avatar">
          <UIcon :name="msg.role === 'user' ? 'person' : 'auto_awesome'" />
        </div>
        <div class="chat-bubble-panel__message-body">
          {{ msg.content }}
        </div>
      </div>

      <div v-if="loading" class="chat-bubble-panel__loading">
        <span class="chat-bubble-panel__loading-dot" />
        <span class="chat-bubble-panel__loading-dot" />
        <span class="chat-bubble-panel__loading-dot" />
      </div>
    </div>

    <!-- Input area -->
    <div class="chat-bubble-panel__input-area">
      <input
        v-model="inputText"
        type="text"
        class="chat-bubble-panel__input"
        placeholder="Type a message... (Shift+Enter for new line)"
        @keydown.enter="sendMessage"
        @keydown.shift.enter.prevent="addNewLine"
      />
      <button
        class="chat-bubble-panel__send"
        :disabled="!inputText.trim() || loading"
        title="Send (Enter)"
        @click="sendMessage"
      >
        <UIcon name="send" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ChatBubblePanel
 * @description Modal content for floating chat bubble
 * @category skills/organisms
 *
 * Features:
 * - Chat message history display
 * - User and AI message rendering
 * - Input field with send button
 * - Loading state with animated dots
 * - Auto-scroll to latest message
 * - Keyboard: Enter to send, Shift+Enter for new line
 *
 * Props:
 * - messages: Array of {role, content} objects
 * - loading: Whether awaiting AI response
 *
 * Emits:
 * - send: When user submits message
 * - close: When close button clicked
 */
import { ref, watch, nextTick } from "vue";
import { useShellStore } from "../../stores/shell";
import UIcon from "../atoms/UIcon.vue";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  messages?: Message[];
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  messages: () => [],
  loading: false,
});

const emit = defineEmits<{
  send: [message: string];
  close: [];
}>();

const shell = useShellStore();
const messagesEl = ref<HTMLDivElement | null>(null);
const inputText = ref("");

// Auto-scroll to latest message
watch(
  () => props.messages,
  async () => {
    await nextTick();
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
  },
  { deep: true },
);

function sendMessage() {
  const text = inputText.value.trim();
  if (!text || props.loading) return;

  emit("send", text);
  inputText.value = "";
}

function addNewLine() {
  inputText.value += "\n";
}

function closeChat() {
  emit("close");
  shell.setChatMode("closed");
}
</script>

<style scoped>
.chat-bubble-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--usx-chat-panel-bg);
  border: var(--usx-chat-panel-border);
  border-radius: var(--usx-chat-panel-radius);
  overflow: hidden;
}

/* ─── Header ──────────────────────────────────────────────────── */

.chat-bubble-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: var(--usx-chat-panel-border);
  background-color: var(--usx-color-surface-variant);
}

.chat-bubble-panel__title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-base);
}

.chat-bubble-panel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-md);
  color: var(--usx-color-on-surface-muted);
  transition: all 150ms ease;
}

.chat-bubble-panel__close:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

/* ─── Messages area ───────────────────────────────────────────── */

.chat-bubble-panel__messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.chat-bubble-panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}

.chat-bubble-panel__empty h3 {
  margin-top: var(--usx-spacing-md);
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface);
}

.chat-bubble-panel__empty p {
  font-size: var(--usx-font-size-sm);
  margin-top: var(--usx-spacing-xs);
}

/* ─── Messages ────────────────────────────────────────────────── */

.chat-bubble-panel__message {
  display: flex;
  gap: var(--usx-spacing-md);
  animation: slideIn 200ms ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-bubble-panel__message--user {
  flex-direction: row-reverse;
}

.chat-bubble-panel__message-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--usx-radius-full);
  font-size: var(--usx-font-size-sm);
  flex-shrink: 0;
}

.chat-bubble-panel__message--user .chat-bubble-panel__message-avatar {
  background-color: var(--usx-color-primary);
  color: white;
}

.chat-bubble-panel__message--assistant .chat-bubble-panel__message-avatar {
  background-color: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

.chat-bubble-panel__message-body {
  max-width: 80%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  line-height: 1.5;
  word-wrap: break-word;
}

.chat-bubble-panel__message--user .chat-bubble-panel__message-body {
  background-color: var(--usx-color-primary);
  color: white;
}

.chat-bubble-panel__message--assistant .chat-bubble-panel__message-body {
  background-color: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

/* ─── Loading ─────────────────────────────────────────────────── */

.chat-bubble-panel__loading {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
}

.chat-bubble-panel__loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--usx-color-on-surface-muted);
  animation: bounce 1.4s infinite;
}

.chat-bubble-panel__loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.chat-bubble-panel__loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    opacity: 0.5;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-8px);
  }
}

/* ─── Input area ──────────────────────────────────────────────── */

.chat-bubble-panel__input-area {
  display: flex;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-top: var(--usx-chat-panel-border);
  background-color: var(--usx-color-surface);
}

.chat-bubble-panel__input {
  flex: 1;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-chat-panel-border);
  border-radius: var(--usx-radius-md);
  background-color: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-sans);
  font-size: var(--usx-font-size-sm);
  resize: none;
  max-height: 80px;
}

.chat-bubble-panel__input:focus {
  outline: none;
  border-color: var(--usx-color-primary);
  box-shadow: 0 0 0 2px rgba(var(--usx-color-primary), 0.1);
}

.chat-bubble-panel__input::placeholder {
  color: var(--usx-color-on-surface-muted);
}

.chat-bubble-panel__send {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: none;
  background-color: var(--usx-color-primary);
  color: white;
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  font-size: var(--usx-font-size-base);
  transition: all 150ms ease;
}

.chat-bubble-panel__send:hover:not(:disabled) {
  background-color: var(--usx-color-primary-hover);
  transform: scale(1.05);
}

.chat-bubble-panel__send:disabled {
  background-color: var(--usx-color-on-surface-muted);
  cursor: not-allowed;
  opacity: 0.5;
}

/* ─── Scrollbar styling ───────────────────────────────────────── */

.chat-bubble-panel__messages::-webkit-scrollbar {
  width: 6px;
}

.chat-bubble-panel__messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-bubble-panel__messages::-webkit-scrollbar-thumb {
  background-color: var(--usx-color-border);
  border-radius: 3px;
}

.chat-bubble-panel__messages::-webkit-scrollbar-thumb:hover {
  background-color: var(--usx-color-on-surface-muted);
}

/* ─── Reduced motion ──────────────────────────────────────────── */

@media (prefers-reduced-motion: reduce) {
  .chat-bubble-panel__message {
    animation: none;
  }

  .chat-bubble-panel__loading-dot {
    animation: none;
    opacity: 1;
  }

  .chat-bubble-panel__send:hover:not(:disabled) {
    transform: none;
  }
}
</style>
