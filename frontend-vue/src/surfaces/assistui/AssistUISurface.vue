<template>
  <div class="surface">
    <div class="surface__content assistui-shell">
      <!-- Mode toggle -->
      <div class="assistui-mode-toggle">
        <button
          v-for="mode in ASSISTUI_MODES"
          :key="mode.id"
          class="assistui-mode-btn"
          :class="{ 'assistui-mode-btn--active': chat.promptMode === mode.id }"
          @click="switchMode(mode.id); if (mode.id === 'workflow') wf.fetchAll()"
        >
          <UIcon :name="mode.icon" />
          <span>{{ mode.label }}</span>
        </button>
      </div>

      <!-- Chat / Plan / Act -->
      <template v-if="chat.promptMode === 'chat' || chat.promptMode === 'plan' || chat.promptMode === 'act'">
        <!-- Body: welcome or messages -->
        <div class="assistui-chat-body" :class="{ 'assistui-chat-body--engaged': chat.messages.length > 1 }">

          <!-- Welcome (no messages yet) -->
          <div v-if="chat.messages.length <= 1" class="assistui-welcome">
            <h1 class="assistui-welcome-title">
              {{ chat.promptMode === 'plan' ? 'What should we research?' : chat.promptMode === 'act' ? 'Ready to act' : 'Good evening' }}
            </h1>

            <!-- Composer in welcome position -->
            <div class="assistui-composer assistui-composer--welcome">
              <div class="assistui-composer-row">
                <textarea
                  ref="inputRef"
                  v-model="chat.input"
                  class="assistui-input"
                  placeholder="Ask anything..."
                  rows="1"
                  @keydown="handleInputKeydown"
                />
                <div class="assistui-composer-actions">
                  <button class="assistui-model-btn" @click="modelPickerOpen = !modelPickerOpen" :title="chat.currentModelName">
                    <UIcon name="smart_toy" />
                    <span>{{ chat.currentModelName }}</span>
                    <UIcon name="expand_more" />
                  </button>
                  <button class="assistui-submit-btn" @click="chat.sendMessage()" :disabled="!chat.input.trim()">
                    <UIcon name="send" />
                  </button>
                </div>
              </div>
              <div v-if="modelPickerOpen" class="assistui-model-dropdown">
                <button
                  v-for="model in chat.models"
                  :key="model.id"
                  class="assistui-model-option"
                  :class="{ 'assistui-model-option--active': chat.selectedModel === model.id }"
                  @click="chat.setModel(model.id); modelPickerOpen = false"
                >
                  <span class="assistui-model-provider">{{ model.provider }}</span>
                  <span class="assistui-model-name">{{ model.name }}</span>
                  <UIcon v-if="chat.selectedModel === model.id" name="check" />
                </button>
              </div>
            </div>

            <!-- Prompt cards -->
            <div v-if="chat.prompts.length > 0" class="assistui-prompts">
              <button
                v-for="prompt in chat.prompts"
                :key="prompt.id"
                class="assistui-prompt-pill"
                @click="handlePromptClick(prompt)"
              >
                {{ prompt.label }}
              </button>
            </div>
          </div>

          <!-- Messages (chat engaged) -->
          <div v-else ref="messagesEl" class="assistui-messages">
            <div
              v-for="msg in chat.messages"
              :key="msg.id"
              class="assistui-msg"
              :class="`assistui-msg--${msg.role}`"
            >
              <div v-if="msg.role === 'assistant'" class="assistui-msg-avatar">
                <UIcon name="auto_awesome" />
              </div>
              <div class="assistui-msg-bubble" v-html="renderMarkdown(msg.content)" />
            </div>

            <div v-if="chat.loading" class="assistui-loading">
              <span class="assistui-loading-dot" />
              <span class="assistui-loading-dot" />
              <span class="assistui-loading-dot" />
            </div>

            <!-- Plan steps -->
            <div v-if="chat.promptMode === 'plan' && chat.planSteps.length > 0" class="assistui-plan-card">
              <div class="assistui-plan-card__header"><UIcon name="checklist" /> Plan Steps</div>
              <div v-for="(step, i) in chat.planSteps" :key="i" class="assistui-plan-step" :class="{ 'assistui-plan-step--done': step.done }">
                <UIcon :name="step.done ? 'check_box' : 'check_box_outline_blank'" />
                <span>{{ step.description }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer composer (chat engaged) -->
        <div v-if="chat.messages.length > 1" class="assistui-composer assistui-composer--footer">
          <div class="assistui-composer-row">
            <textarea
              ref="inputRef"
              v-model="chat.input"
              class="assistui-input"
              placeholder="Ask anything..."
              rows="1"
              @keydown="handleInputKeydown"
            />
            <div class="assistui-composer-actions">
              <button class="assistui-model-btn" @click="modelPickerOpen = !modelPickerOpen" :title="chat.currentModelName">
                <UIcon name="smart_toy" />
              </button>
              <button class="assistui-submit-btn" @click="chat.sendMessage()" :disabled="!chat.input.trim()">
                <UIcon name="send" />
              </button>
            </div>
          </div>
          <div v-if="modelPickerOpen" class="assistui-model-dropdown assistui-model-dropdown--up">
            <button
              v-for="model in chat.models"
              :key="model.id"
              class="assistui-model-option"
              :class="{ 'assistui-model-option--active': chat.selectedModel === model.id }"
              @click="chat.setModel(model.id); modelPickerOpen = false"
            >
              <span class="assistui-model-provider">{{ model.provider }}</span>
              <span class="assistui-model-name">{{ model.name }}</span>
              <UIcon v-if="chat.selectedModel === model.id" name="check" />
            </button>
          </div>
        </div>

        <!-- Act confirmation -->
        <div v-if="chat.promptMode === 'act' && actConfirmVisible" class="assistui-act-confirm">
          <UIcon name="warning" />
          <span>Act mode will execute tools. Confirm to proceed?</span>
          <div class="assistui-act-confirm__actions">
            <button class="usx-button" @click="actConfirmVisible = false">Cancel</button>
            <button class="usx-button usx-button--primary" @click="confirmAct()">Confirm</button>
          </div>
        </div>
      </template>

      <!-- Workflow Mode -->
      <template v-else>
        <div class="assistui-workflow-panel">
          <h2 class="assistui-workflow-title"><UIcon name="account_tree" /> Workflow</h2>
          <div v-if="wf.workflowStatus" class="assistui-workflow-status">
            <div class="assistui-workflow-card">
              <h3>Tasks</h3>
              <p>{{ wf.totalTasks }} total · {{ wf.inProgressCount }} in progress · {{ wf.completedCount }} completed</p>
            </div>
            <div v-if="wf.workflowStatus.tasker" class="assistui-workflow-card">
              <h3>Boards</h3>
              <ul><li v-for="board in wf.workflowStatus.tasker.boards" :key="board.name">{{ board.name }} ({{ board.count }})</li></ul>
            </div>
          </div>
          <div v-if="wf.loading" class="assistui-loading"><span class="assistui-loading-dot" /><span class="assistui-loading-dot" /><span class="assistui-loading-dot" /></div>
          <div v-else-if="wf.missions.length > 0">
            <div v-for="mission in wf.missions" :key="mission.id" class="assistui-workflow-card">
              <strong>{{ mission.title }}</strong>
              <p>{{ mission.description }}</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component AssistUISurface
 * @description User-facing AI chat + workflow surface with streaming, model selection,
 * and task/planning integration. Uses USX surface classes from usx-standard.css.
 * @category surfaces
 */
import { ref, computed, onMounted } from "vue";
import { useWorkflowStore } from "../../stores/workflow";
import UIcon from "../../skills/atoms/UIcon.vue";
import { useChatStore, ASSISTUI_MODES } from "../../stores/chat";

const chat = useChatStore();
const wf = useWorkflowStore();

const modelPickerOpen = ref(false);
const actConfirmVisible = ref(false);
const messagesEl = ref<HTMLElement | null>(null);
const inputRef = ref<HTMLTextAreaElement | null>(null);

const statusText = computed(() => {
  switch (chat.snackbarStatus) {
    case "online":
      return "AI Online";
    case "checking":
      return "Connecting...";
    default:
      return "AI Offline";
  }
});

const formatTime = (timestamp: Date) => {
  return new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit",
  }).format(timestamp);
};

const renderMarkdown = (content: string) => {
  return content
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
};

const resolveIcon = (icon: string) => {
  const emojiMap: Record<string, string> = {
    "⚡": "bolt",
    "📝": "edit",
    "🔍": "search",
    "💡": "lightbulb",
    "🚀": "rocket_launch",
  };
  return emojiMap[icon] || icon;
};

const handlePromptClick = (prompt: any) => {
  chat.input = prompt.label;
  chat.sendMessage();
};

const handleTaskClick = (task: any) => {
  wf.selectTask(task);
  // Dispatch custom event for any listener that wants to open editor
  window.dispatchEvent(
    new CustomEvent("assistui-task-open", { detail: { task } }),
  );
};

const handleInputKeydown = (e: KeyboardEvent) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chat.sendMessage();
  }
};

const switchMode = (mode: string) => {
  chat.setPromptMode(mode as 'chat' | 'plan' | 'act' | 'workflow');
};
const confirmAct = () => {
  actConfirmVisible.value = false;
  chat.sendMessage();
};




onMounted(() => {
  fetch("http://localhost:8484/api/health")
    .then((res) => {
      if (res.ok) {
        chat.snackbarStatus = "online";
      } else {
        chat.snackbarStatus = "offline";
      }
    })
    .catch(() => {
      chat.snackbarStatus = "offline";
    });
});
</script>

<style scoped>
/* ─── Shell ──────────────────────────────────────────────────── */
.assistui-shell {
  max-width: none;
  width: 100%;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

/* ─── Mode toggle ────────────────────────────────────────────── */
.assistui-mode-toggle {
  display: flex;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm);
  flex-shrink: 0;
}

.assistui-mode-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-md);
  min-height: var(--usx-control-size-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  cursor: pointer;
  transition: all var(--usx-transition-fast);
}

.assistui-mode-btn:hover {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-on-surface);
}

.assistui-mode-btn--active {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

/* ─── Chat body ──────────────────────────────────────────────── */
.assistui-chat-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.assistui-chat-body--engaged {
  padding: var(--usx-spacing-md);
}

/* ─── Welcome ────────────────────────────────────────────────── */
.assistui-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-lg);
  padding: var(--usx-spacing-2xl) var(--usx-spacing-lg);
}

.assistui-welcome-title {
  font-size: var(--usx-font-size-3xl);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-on-surface);
  margin: 0;
  text-align: center;
}

/* ─── Composer ───────────────────────────────────────────────── */
.assistui-composer--welcome {
  width: 100%;
  max-width: var(--usx-prose-width);
}

.assistui-composer--footer {
  padding: var(--usx-spacing-sm);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  flex-shrink: 0;
  position: relative;
}

.assistui-composer-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  padding: var(--usx-spacing-xs);
}

.assistui-composer-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
}

.assistui-model-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 0 var(--usx-spacing-xs);
  min-height: var(--usx-control-size-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
  white-space: nowrap;
}

.assistui-model-dropdown {
  position: absolute;
  top: calc(100% + var(--usx-spacing-xs));
  left: 0;
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  min-width: var(--usx-dropdown-min-width);
  z-index: 10;
  box-shadow: var(--usx-shadow-sm);
  display: flex;
  flex-direction: column;
}

.assistui-model-dropdown--up {
  top: auto;
  bottom: calc(100% + var(--usx-spacing-xs));
}

.assistui-model-option {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: transparent;
  color: var(--usx-color-on-surface);
  border: none;
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  text-align: left;
}

.assistui-model-option:hover {
  background: var(--usx-color-surface-hover);
}

.assistui-model-option--active {
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
  color: var(--usx-color-primary);
}

.assistui-model-provider {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.assistui-model-name {
  flex: 1;
}

/* ─── Prompt pills ───────────────────────────────────────────── */
.assistui-prompts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  max-width: 36rem;
}

.assistui-prompt-pill {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  padding: 0 var(--usx-spacing-md);
  min-height: var(--usx-control-size-sm);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
  transition: var(--usx-transition-fast);
}

.assistui-prompt-pill:hover {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, var(--usx-color-surface));
}

/* ─── Messages ───────────────────────────────────────────────── */
.assistui-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.assistui-msg {
  display: flex;
  gap: var(--usx-spacing-sm);
  max-width: 86%;
}

.assistui-msg--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.assistui-msg--assistant {
  align-self: flex-start;
}

.assistui-msg-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-md);
  height: var(--usx-control-size-md);
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
  color: var(--usx-color-primary);
  flex-shrink: 0;
}

.assistui-msg-bubble {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-normal);
}

.assistui-msg--user .assistui-msg-bubble {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

.assistui-msg--assistant .assistui-msg-bubble {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

/* ─── Input ──────────────────────────────────────────────────── */
.assistui-input {
  flex: 1;
  min-height: 0;
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  resize: none;
  outline: none;
  line-height: var(--usx-line-height-tight);
}

.assistui-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-control-size-md);
  height: var(--usx-control-size-md);
  border: none;
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  cursor: pointer;
  flex-shrink: 0;
}

.assistui-submit-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ─── Loading ────────────────────────────────────────────────── */
.assistui-loading {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm);
}

.assistui-loading-dot {
  width: var(--usx-spacing-xs);
  height: var(--usx-spacing-xs);
  border-radius: var(--usx-radius-full);
  background: var(--usx-color-on-surface-muted);
  animation: assistui-pulse var(--usx-motion-duration-pulse) infinite;
}

.assistui-loading-dot:nth-child(2) { animation-delay: var(--usx-motion-delay-sm); }
.assistui-loading-dot:nth-child(3) { animation-delay: var(--usx-motion-delay-md); }

@keyframes assistui-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ─── Plan card ──────────────────────────────────────────────── */
.assistui-plan-card {
  margin-top: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-primary);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
}

.assistui-plan-card__header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-primary);
  margin-bottom: var(--usx-spacing-sm);
}

.assistui-plan-step {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) 0;
  font-size: var(--usx-font-size-sm);
}

.assistui-plan-step--done {
  opacity: 0.6;
  text-decoration: line-through;
}

/* ─── Act confirm ────────────────────────────────────────────── */
.assistui-act-confirm {
  margin: var(--usx-spacing-md);
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width-thick) solid var(--usx-color-warning);
  border-radius: var(--usx-radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.assistui-act-confirm__actions {
  display: flex;
  gap: var(--usx-spacing-md);
}

/* ─── Workflow ───────────────────────────────────────────────── */
.assistui-workflow-panel {
  padding: var(--usx-spacing-lg);
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
}

.assistui-workflow-title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xl);
  margin: 0;
}

.assistui-workflow-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: var(--usx-spacing-md);
}

.assistui-workflow-card {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}
</style>
