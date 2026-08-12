<template>
  <div class="usx-chat-bubble-container">
    <!-- Floating chat button (hidden while overlay is open) -->
    <button
      v-if="chatMode !== 'floating'"
      class="usx-chat-bubble"
      :aria-label="chatMode === 'closed' ? 'Open assistant' : 'Close assistant'"
      :title="chatMode === 'closed' ? 'Open assistant (Cmd+J)' : 'Close assistant (Esc)'"
      @click="toggleChat"
    >
      <UIcon name="chat" />
      <span v-if="unreadCount > 0" class="usx-chat-bubble-badge">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Overlay + centered stack -->
    <transition name="usx-chat-overlay">
      <div v-if="chatMode === 'floating'" class="usx-chat-overlay" @click.self="closeChat">
        <!-- Top-right actions: lane toggle + close -->
        <div class="usx-chat-overlay-actions">
          <slot name="actions" />
          <button class="usx-chat-overlay-close" @click="closeChat" title="Close (Esc)">
            <UIcon name="close" />
          </button>
        </div>
        <div class="usx-chat-overlay-stack">
          <!-- Above: welcome -->
          <div class="usx-chat-above">
            <slot name="above" />
          </div>
          <!-- Center: panel -->
          <div class="usx-chat-panel">
            <slot />
          </div>
          <!-- Below: prompts -->
          <div class="usx-chat-below">
            <slot name="below" />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
/**
 * @component ChatBubble
 * @description Floating assistant/chat bubble with unread badge and overlay
 * @category skills/molecules
 *
 * Features:
 * - Floating button (56×56px) with chat icon
 * - Unread message badge (pulsing when count > 0)
 * - Click to open/close chat panel
 * - Keyboard shortcut: Cmd+J (Mac) / Ctrl+J (Windows/Linux)
 * - Overlay dimmer for focus
 * - Responsive: bottom-right on desktop, bottom sheet on mobile
 *
 * Slot: Content rendered inside chat panel (typically ChatBubblePanel)
 */
import { computed, onMounted, onBeforeUnmount } from "vue";
import { useShellStore } from "../../stores/shell";
import UIcon from "../atoms/UIcon.vue";

interface Props {
  unreadCount?: number;
}

const props = withDefaults(defineProps<Props>(), {
  unreadCount: 0,
});

const shell = useShellStore();

const chatMode = computed(() => shell.chatMode);

function toggleChat() {
  if (shell.chatMode === "closed") {
    shell.setChatMode("floating");
  } else {
    shell.setChatMode("closed");
  }
}

function closeChat() {
  shell.setChatMode("closed");
}

function handleKeyboardShortcut(event: KeyboardEvent) {
  // Cmd+J (Mac) or Ctrl+J (Windows/Linux) to toggle chat
  const isMac = /Mac|iPhone|iPad|iPod/.test(navigator.platform);
  const modifier = isMac ? event.metaKey : event.ctrlKey;

  if (modifier && event.key === "j") {
    event.preventDefault();
    toggleChat();
  }

  // Escape to close chat
  if (event.key === "Escape" && shell.chatMode === "floating") {
    event.preventDefault();
    closeChat();
  }
}

onMounted(() => {
  window.addEventListener("keydown", handleKeyboardShortcut);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeyboardShortcut);
});
</script>

<style scoped>
.usx-chat-bubble-container {
  position: relative;
  z-index: var(--usx-zindex-chat-button);
}

/* ─── Transitions ─────────────────────────────────────────────── */

.usx-chat-overlay-enter-active,
.usx-chat-overlay-leave-active {
  transition: opacity var(--usx-chat-animation-duration)
    var(--usx-chat-animation-easing);
}

.usx-chat-overlay-enter-from,
.usx-chat-overlay-leave-to {
  opacity: 0;
}

.usx-chat-panel-enter-active,
.usx-chat-panel-leave-active {
  transition: all var(--usx-chat-animation-duration)
    var(--usx-chat-animation-easing);
}

.usx-chat-panel-enter-from {
  opacity: 0;
  transform: translateY(16px);
}

.usx-chat-panel-leave-to {
  opacity: 0;
  transform: translateY(16px);
}
</style>
