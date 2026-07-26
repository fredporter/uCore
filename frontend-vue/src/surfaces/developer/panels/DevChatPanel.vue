<template>
  <div class="dev-chat-panel">
    <!-- Model picker + status bar -->
    <div class="dev-chat-topbar">
      <div class="dev-chat-controls-row">
        <!-- Model picker -->
        <div class="dev-chat-model-section">
          <button class="usx-button" @click="modelPickerOpen = !modelPickerOpen">
            <UIcon name="smart_toy" />
            <span>{{ currentModelName }}</span>
            <UIcon name="expand_more" />
          </button>
          <div v-if="modelPickerOpen" class="dev-chat-model-dropdown">
            <button
              v-for="model in models"
              :key="model.id"
              class="dev-chat-model-option"
              :class="{ 'dev-chat-model-option--active': selectedModel === model.id }"
              @click="selectedModel = model.id; modelPickerOpen = false"
            >
              <span class="dev-chat-model-provider">{{ model.provider }}</span>
              <span class="dev-chat-model-name">{{ model.name }}</span>
              <UIcon v-if="selectedModel === model.id" name="check" />
            </button>
          </div>
        </div>

        <!-- Lane indicator -->
        <div class="dev-chat-lane">
          <UIcon :name="dev.currentLane.icon" :size="14" />
          <span>{{ dev.currentLane.label }} Lane</span>
          <span class="dev-chat-lane-sep" />
          <span class="dev-chat-lane-workspace">{{ dev.currentWorkspace }}</span>
        </div>

        <!-- Status + Actions -->
        <div class="dev-chat-status-bar">
          <span
            class="dev-chat-status-dot"
            :class="{ 'dev-chat-status-dot--online': snackbarStatus === 'online' }"
          />
          <span class="dev-chat-status-text">{{ statusText }}</span>
          <span class="dev-chat-status-sep" />
          <button class="usx-button" @click="clearChat()">
            <UIcon name="delete" /> Clear
          </button>
        </div>
      </div>
    </div>

    <!-- Chat Messages -->
    <div class="dev-chat-messages" ref="messagesEl">
      <!-- Welcome / empty state -->
      <div v-if="dev.chatMessages.length === 0" class="dev-chat-empty">
        <h2>
          <UIcon name="code" /> Developer Assistant
        </h2>
        <p>Ask me about code review, repo management, skills, MCP servers, service health, or deployment.</p>

        <!-- Prompt cards -->
        <div class="dev-chat-prompt-row">
          <div
            v-for="prompt in DEV_PROMPTS"
            :key="prompt.id"
            class="dev-chat-prompt-card"
            @click="handlePromptClick(prompt)"
          >
            <span class="dev-chat-prompt-card-icon"><UIcon :name="prompt.icon" /></span>
            <span class="dev-chat-prompt-card-label">{{ prompt.label }}</span>
            <span class="dev-chat-prompt-card-context">{{ prompt.context }}</span>
          </div>
        </div>
      </div>

      <!-- Messages -->
      <div
        v-for="(msg, i) in dev.chatMessages"
        :key="i"
        class="dev-chat-message"
        :class="`dev-chat-message--${msg.role}`"
      >
        <div class="dev-chat-message-header">
          <span class="dev-chat-message-role">
            {{ msg.role === 'user' ? 'You' : 'Dev Assistant' }}
          </span>
        </div>
        <div class="dev-chat-message-body" v-html="renderMarkdown(msg.content)" />
      </div>

      <!-- Loading indicator -->
      <div v-if="dev.chatLoading" class="dev-chat-loading">
        <span class="dev-chat-loading-dot" />
        <span class="dev-chat-loading-dot" />
        <span class="dev-chat-loading-dot" />
      </div>
    </div>

    <!-- Input -->
    <div class="dev-chat-input-row">
      <textarea
        ref="inputRef"
        v-model="inputText"
        class="dev-chat-input"
        placeholder="Ask about code, repos, skills..."
        @keydown="handleInputKeydown"
      />
      <button class="dev-chat-submit-btn" @click="sendMessage()">
        <UIcon name="send" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component DevChatPanel
 * @description Developer-lane AI chat panel with streaming, model selection,
 * and lane/workspace-aware context. Tab panel within Developer Surface.
 * @category surfaces/developer
 */
import { ref, computed, onMounted } from 'vue'
import { useDeveloperStore } from '../../../stores/developer'
import UIcon from '../../../skills/atoms/UIcon.vue'
import { SNACKBAR_API } from '../../../api/base'

const dev = useDeveloperStore()

// Model state
const models = ref([
  { id: 'llama3.2', provider: 'ollama', name: 'Llama 3.2' },
  { id: 'mistral', provider: 'ollama', name: 'Mistral' },
  { id: 'gpt-4o', provider: 'openrouter', name: 'GPT-4o' },
])
const selectedModel = ref('llama3.2')
const modelPickerOpen = ref(false)

// Input
const inputText = ref('')
const messagesEl = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

// Status
const snackbarStatus = ref<'checking' | 'online' | 'offline'>('checking')

const currentModelName = computed(() =>
  models.value.find(m => m.id === selectedModel.value)?.name || selectedModel.value
)

const statusText = computed(() => {
  switch (snackbarStatus.value) {
    case 'online': return 'AI Online'
    case 'checking': return 'Connecting...'
    default: return 'AI Offline'
  }
})

const renderMarkdown = (content: string) => {
  return content
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function sendMessage() {
  const message = inputText.value.trim()
  if (!message || dev.chatLoading) return
  inputText.value = ''
  dev.sendChatMessage(message)
}

function handleInputKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function handlePromptClick(prompt: { label: string }) {
  inputText.value = prompt.label
  sendMessage()
}

function clearChat() {
  dev.chatMessages = []
}

onMounted(() => {
  fetch(`${SNACKBAR_API}/api/health`)
    .then(res => {
      snackbarStatus.value = res.ok ? 'online' : 'offline'
    })
    .catch(() => {
      snackbarStatus.value = 'offline'
    })
})

const DEV_PROMPTS = [
  { id: 'review', icon: 'visibility', label: 'Code review', context: '/review recent changes' },
  { id: 'status', icon: 'info', label: 'Repo status', context: '/status current repo' },
  { id: 'skills', icon: 'extension', label: 'List skills', context: '/skills available' },
  { id: 'deploy', icon: 'rocket_launch', label: 'Deploy service', context: '/deploy latest' },
  { id: 'health', icon: 'monitor_heart', label: 'System health', context: '/health check' },
  { id: 'diagnose', icon: 'bug_report', label: 'Diagnose issue', context: '/diagnose problem' },
]
</script>

<style scoped>
.dev-chat-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--usx-spacing-2xl) * 4);
  min-height: calc(var(--usx-touch-min) * 8);
  max-height: none;
  overflow: hidden;
}

/* ─── Topbar ──────────────────────────────────── */
.dev-chat-topbar {
  flex-shrink: 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.dev-chat-controls-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  width: 100%;
}

.dev-chat-model-section {
  position: relative;
  flex-shrink: 0;
}

.dev-chat-model-section .usx-button {
  border: none;
  background: transparent;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.dev-chat-model-section .usx-button:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.dev-chat-model-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: var(--usx-spacing-xs);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  min-width: calc(var(--usx-touch-min) * 5);
  z-index: 10;
  box-shadow: var(--usx-shadow-sm);
}

.dev-chat-model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: transparent;
  color: var(--usx-color-on-surface);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  text-align: left;
  border: none;
}

.dev-chat-model-option:hover {
  background: var(--usx-color-surface-hover);
}

.dev-chat-model-option--active {
  background: var(--usx-color-surface-active);
  color: var(--usx-color-primary);
}

.dev-chat-model-provider {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.dev-chat-model-name {
  flex: 1;
  margin-left: var(--usx-spacing-sm);
}

/* ─── Lane Indicator ──────────────────────────── */
.dev-chat-lane {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.dev-chat-lane-sep {
  width: var(--usx-border-width);
  height: calc(var(--usx-spacing-md) - var(--usx-spacing-xs));
  background: var(--usx-color-border);
}

.dev-chat-lane-workspace {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
}

/* ─── Status Bar ──────────────────────────────── */
.dev-chat-status-bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  margin-left: auto;
  flex-shrink: 0;
}

.dev-chat-status-bar .usx-button {
  border: none;
  background: transparent;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.dev-chat-status-bar .usx-button:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}

.dev-chat-status-dot {
  width: var(--usx-spacing-sm);
  height: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-on-surface-muted);
}

.dev-chat-status-dot--online {
  background: var(--usx-color-success);
}

.dev-chat-status-text {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.dev-chat-status-sep {
  width: var(--usx-border-width);
  height: calc(var(--usx-spacing-lg) - var(--usx-spacing-xs));
  background: var(--usx-color-border);
}

/* ─── Messages ────────────────────────────────── */
.dev-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  min-height: 0;
}

.dev-chat-empty {
  text-align: center;
  padding: var(--usx-spacing-xl) 0;
  color: var(--usx-color-on-surface-muted);
}

.dev-chat-empty h2 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface);
  margin-bottom: var(--usx-spacing-sm);
}

.dev-chat-prompt-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, calc(var(--usx-touch-min) * 5)), 1fr));
  gap: var(--usx-spacing-md);
  margin-top: var(--usx-spacing-lg);
}

.dev-chat-prompt-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  align-items: center;
  text-align: center;
  padding: var(--usx-spacing-lg);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  cursor: pointer;
  transition: background var(--usx-transition-base), border-color var(--usx-transition-base);
  color: var(--usx-color-on-surface);
}

.dev-chat-prompt-card:hover {
  background: var(--usx-color-surface-hover);
  border-color: var(--usx-color-primary);
}

.dev-chat-prompt-card-label {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.dev-chat-prompt-card-icon {
  font-size: var(--usx-icon-size-xl);
  color: var(--usx-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
}

.dev-chat-prompt-card-context {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  font-family: var(--usx-font-family-mono);
}

/* ─── Message Bubbles ─────────────────────────── */
.dev-chat-message {
  padding: var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  max-width: 85%;
}

.dev-chat-message--user {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  margin-left: auto;
}

.dev-chat-message--assistant {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  margin-right: auto;
}

.dev-chat-message-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  margin-bottom: var(--usx-spacing-xs);
}

.dev-chat-message-role {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
}

.dev-chat-message-body {
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-relaxed);
}

.dev-chat-message-body h1,
.dev-chat-message-body h2,
.dev-chat-message-body h3 {
  margin: var(--usx-spacing-md) 0 var(--usx-spacing-sm);
}

.dev-chat-message-body code {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-sm);
  font-family: var(--usx-font-family-mono);
  color: var(--usx-color-primary);
}

/* ─── Loading ─────────────────────────────────── */
.dev-chat-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
}

.dev-chat-loading-dot {
  width: var(--usx-spacing-sm);
  height: var(--usx-spacing-sm);
  border-radius: 50%;
  background: var(--usx-color-primary);
  animation: dev-chat-pulse 1s ease-in-out infinite;
}

.dev-chat-loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dev-chat-loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dev-chat-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ─── Input Row ───────────────────────────────── */
.dev-chat-input-row {
  display: flex;
  align-items: flex-end;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}

.dev-chat-input {
  flex: 1;
  min-height: var(--usx-touch-min);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-sans);
  font-size: var(--usx-font-size-base);
  resize: vertical;
  outline: none;
}

.dev-chat-input:focus {
  border-color: var(--usx-color-primary);
}

.dev-chat-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  padding: 0;
  border: none;
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  cursor: pointer;
  font-size: var(--usx-font-size-lg);
  transition: background var(--usx-transition-fast), transform var(--usx-transition-fast);
  flex-shrink: 0;
}

.dev-chat-submit-btn:hover {
  background: var(--usx-color-primary-hover);
  transform: scale(1.05);
}

.dev-chat-submit-btn:active {
  transform: scale(0.95);
}
</style>