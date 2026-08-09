<template>
  <div class="floating-chat" :class="{ 'floating-chat--open': isOpen }">
    <Transition name="chat-panel">
      <div v-if="isOpen" class="floating-chat__panel">
        <div class="floating-chat__header">
          <span class="floating-chat__title">AI Assistant</span>
          <div class="floating-chat__header-actions">
            <UButton
              variant="ghost"
              size="sm"
              @click="isOpen = false"
              title="Minimize"
            >
              <UIcon name="remove" />
            </UButton>
            <UButton
              variant="ghost"
              size="sm"
              @click="isOpen = false"
              title="Close"
            >
              <UIcon name="close" />
            </UButton>
          </div>
        </div>
        <div class="floating-chat__body">
          <div class="floating-chat__messages">
            <div
              v-for="msg in chat.messages"
              :key="msg.id"
              class="floating-chat__message"
              :class="`floating-chat__message--${msg.role}`"
            >
              <div
                class="floating-chat__message-body"
                v-html="renderMarkdown(msg.content)"
              />
            </div>
            <div v-if="chat.loading" class="floating-chat__loading">
              <span /><span /><span />
            </div>
          </div>
          <div class="floating-chat__input">
            <textarea
              v-model="chat.input"
              placeholder="Ask me anything..."
              rows="1"
              @keydown="handleKeyDown"
            />
            <UButton
              variant="primary"
              size="sm"
              :disabled="!chat.input.trim() || chat.loading"
              @click="chat.sendMessage()"
            >
              <UIcon name="send" />
            </UButton>
          </div>
        </div>
      </div>
    </Transition>

    <button
      class="floating-chat__bubble"
      @click="isOpen = !isOpen"
      :title="isOpen ? 'Close chat' : 'Open chat'"
    >
      <UIcon :name="isOpen ? 'close' : 'chat'" />
    </button>
  </div>
</template>

<script setup lang="ts">
/**
 * @component FloatingChat
 * @description Intercom-style floating chat bubble for embedding on other surfaces.
 * Ported from FloatingChatWrapper (React).
 * @category surfaces
 * @usage <FloatingChat @close="handleClose" />
 */
import { ref } from "vue";
import UButton from "../../skills/atoms/UButton.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import { useChatStore } from "../../stores/chat";
import { renderMarkdown } from "../../composables/useMarkdown";

const chat = useChatStore();
const isOpen = ref(false);

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chat.sendMessage();
  }
}
</script>

<style scoped>
.floating-chat {
  position: fixed;
  bottom: var(--usx-spacing-lg);
  right: var(--usx-spacing-lg);
  z-index: 500;
}

.floating-chat__panel {
  width: min(90vw, 420px);
  height: min(85vh, 600px);
  background: var(--usx-color-background);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 8px 32px
    color-mix(in srgb, var(--usx-color-on-surface) 15%, transparent);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: var(--usx-spacing-sm);
}

.floating-chat__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-md);
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-base);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.floating-chat__header-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.floating-chat__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.floating-chat__messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.floating-chat__message--user .floating-chat__message-body {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-radius: var(--usx-radius-lg) var(--usx-radius-md) var(--usx-radius-sm)
    var(--usx-radius-lg);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  font-size: var(--usx-font-size-base);
  margin-left: auto;
  max-width: 80%;
}

.floating-chat__message--assistant .floating-chat__message-body {
  font-size: var(--usx-font-size-base);
  line-height: var(--usx-line-height-relaxed);
  padding: var(--usx-spacing-xs) 0;
}

.floating-chat__loading {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) 0;
}

.floating-chat__loading span {
  width: var(--usx-spacing-sm);
  height: var(--usx-spacing-sm);
  border-radius: 50%;
  background: var(--usx-color-on-surface-muted);
  animation: bounce var(--usx-motion-duration-pulse) infinite ease-in-out both;
}

.floating-chat__loading span:nth-child(1) {
  animation-delay: calc(var(--usx-motion-delay-lg) * -1);
}
.floating-chat__loading span:nth-child(2) {
  animation-delay: calc(var(--usx-motion-delay-sm) * -1);
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.floating-chat__input {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
}

.floating-chat__input textarea {
  flex: 1;
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-base);
  font-family: var(--usx-font-family-sans);
  resize: none;
  outline: none;
}

.floating-chat__input textarea:focus {
  border-color: var(--usx-color-primary);
}

.floating-chat__bubble {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: 50%;
  border: none;
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  cursor: pointer;
  font-size: var(--usx-font-size-xl);
  transition:
    transform var(--usx-transition-fast),
    background var(--usx-transition-fast);
  margin-left: auto;
  box-shadow: 0 4px 12px
    color-mix(in srgb, var(--usx-color-primary) 40%, transparent);
}

.floating-chat__bubble:hover {
  transform: scale(1.08);
  background: var(--usx-color-primary-hover);
}

/* Panel transition */
.chat-panel-enter-active,
.chat-panel-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.chat-panel-enter-from,
.chat-panel-leave-to {
  opacity: 0;
  transform: translateY(var(--usx-spacing-lg)) scale(0.95);
}
</style>
