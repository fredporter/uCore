<template>
  <ToastOverlay />
  <AlertOverlay />
  <PopupOverlay />
  <StoriesOverlay />
  <ChatBubble v-if="!hideChatBubble">
    <template #above>
      <div v-if="showWelcome" class="chat-above-center">
        <div class="chat-above-icon">
          <UIcon name="auto_awesome" />
        </div>
        <h2 class="chat-above-title">{{ overlayWelcomeTitle }}</h2>
      </div>
    </template>

    <ChatBubblePanel
      :chat-messages="chatMessages"
      :dev-messages="[]"
      :loading="assistChat.loading"
      :dev-available="false"
      :dev-mode-on="false"
      :context-label="contextLabel"
      :current-task="currentTaskTitle"
      :active-lane="'chat'"
      @send-chat="sendChat"
      @update:active-lane="activeLane = 'chat'"
    />

    <template #below>
      <div v-if="showWelcome" class="chat-below-prompts">
        <button
          v-for="card in chatPromptCards"
          :key="card.label"
          class="chat-below-pill"
          @click="handlePromptClick(card)"
        >
          {{ card.label }}
        </button>
      </div>
    </template>
  </ChatBubble>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";
import ToastOverlay from "../molecules/ToastOverlay.vue";
import AlertOverlay from "./AlertOverlay.vue";
import PopupOverlay from "./PopupOverlay.vue";
import StoriesOverlay from "./StoriesOverlay.vue";
import ChatBubble from "../molecules/ChatBubble.vue";
import ChatBubblePanel from "./ChatBubblePanel.vue";
import UIcon from "../atoms/UIcon.vue";
import { useToast } from "../../composables/useToast";
import { useFeed } from "../../composables/useFeed";
import { useOverlay } from "../../composables/useOverlay";
import { useExtensionStore } from "../../stores/extensions";
import { useShellStore } from "../../stores/shell";
import { useWorkflowStore } from "../../stores/workflow";
import { useChatStore } from "../../stores/chat";

const { toast } = useToast();
const { events } = useFeed();
const shell = useShellStore();
const route = useRoute();
const extStore = useExtensionStore();
const assistChat = useChatStore();

// Chat has one global entry point: the bottom bubble.
const hideChatBubble = computed(() => false);

// ─── Context strip ───────────────────────────────────────────────
const contextLabel = computed(() => {
  const path = shell.lastSurface ?? "";
  if (path.includes("/workflow")) return "Workflow";
  if (path.includes("/browserui")) return "Browser";
  if (path.includes("/snackbar")) return "Snackbar";
  if (path.includes("/system")) return "System";
  if (path.includes("/ucode")) return "uCode";
  return "Dashboard";
});

const currentTaskTitle = ref("");
const wf = useWorkflowStore();
watch(
  () => wf.selectedTask,
  (t) => {
    currentTaskTitle.value = (t as any)?.title ?? "";
  },
  { immediate: true },
);

// ─── Chat state ──────────────────────────────────────────────────
interface Msg {
  role: "user" | "assistant";
  content: string;
}

const activeLane = ref<"chat">("chat");

interface PromptCard {
  label: string;
  prompt: string;
  mode?: "chat" | "plan" | "act" | "workflow";
}

const chatPromptCards: PromptCard[] = [
  { label: "Research a topic", prompt: "Research and summarize ", mode: "plan" },
  { label: "Draft content", prompt: "Write a draft about ", mode: "chat" },
  { label: "Explain a concept", prompt: "Explain ", mode: "chat" },
  { label: "Plan a workflow", prompt: "Plan a workflow for ", mode: "workflow" },
  { label: "Summarize a doc", prompt: "Summarize the following: ", mode: "act" },
  { label: "Quick brainstorm", prompt: "Brainstorm ideas for ", mode: "chat" },
];

function handlePromptClick(card: PromptCard) {
  if (card.mode) assistChat.setPromptMode(card.mode);
  assistChat.input = card.prompt;
}

const chatMessages = computed<Msg[]>(() =>
  assistChat.messages.map((m) => ({ role: m.role, content: m.content })),
);

const showWelcome = computed(() =>
  activeLane.value === "chat" && chatMessages.value.length <= 1 && !assistChat.input.trim(),
);

const timeGreeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
});

const overlayWelcomeTitle = computed(() => {
  switch (assistChat.promptMode) {
    case "plan": return "What should we research?";
    case "act": return "Ready to act";
    case "workflow": return "What workflow should we plan?";
    default: return timeGreeting.value;
  }
});
async function sendChat(text: string, mode: "chat" | "plan" | "act" | "workflow") {
  assistChat.setPromptMode(mode);
  await assistChat.sendMessage(text);
  assistChat.saveCurrentConversation();
}

// ─── Feed event handlers ─────────────────────────────────────────
watch(
  () => events.value.at(-1),
  (event) => {
    if (!event) return;
    const overlay = useOverlay();

    switch (event.type) {
      // Skills
      case "skill_complete":
        toast(`✅ ${event.data.skill || "Skill"} completed`, "success", {
          duration: 4000,
        });
        break;
      case "skill_error":
        toast(
          `❌ ${event.data.skill || "Skill"} failed: ${event.data.error || ""}`,
          "error",
          { duration: 6000 },
        );
        break;

      // Extensions
      case "extension_online": {
        const id = event.data.id as string;
        extStore.markRunning(id, event.data.version as string | undefined);
        const name = event.data.name ?? id;
        toast(`${name} connected`, "info", { duration: 3000 });
        break;
      }
      case "extension_offline": {
        const id = event.data.id as string;
        extStore.markOffline(id);
        const name = event.data.name ?? id;
        toast(`${name} disconnected`, "warning", { duration: 4000 });
        break;
      }

      // Backend-initiated toasts
      case "toast": {
        const msg = event.data.message as string;
        if (msg) toast(msg, (event.data.type as any) || "info");
        break;
      }

      // Critical system alerts
      case "alert":
        overlay.showAlert({
          type: (event.data.level as any) || "warning",
          title: (event.data.title as string) || "System Alert",
          message: (event.data.message as string) || "",
        });
        break;
    }
  },
);
</script>
