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
      :chat-messages="okMessages"
      :dev-messages="[]"
      :loading="okLoading"
      :local-assistant="true"
      @clear-local="okMessages = []"
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
import { UCORE_BASE } from "../../api/base";
import { useIdentityStore } from "../../stores/identity";
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
  const path = route.path;
  if (path.includes("/workflow")) return "Workflow";
  if (path.includes("/browserui")) return "Research";
  if (path.includes("/snackbar")) return "Snackbar";
  if (path.includes("/system")) return "Settings";
  if (path.includes("/documentation")) return "Knowledge";
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
}

const chatPromptCards: PromptCard[] = [
  { label: "Explore a topic", prompt: "Explain what you know about " },
  { label: "Draft content", prompt: "Write a draft about " },
  { label: "Explain a concept", prompt: "Explain " },
  { label: "Plan a workflow", prompt: "Plan a workflow for " },
  { label: "Summarize text", prompt: "Summarize the following: " },
  { label: "Quick brainstorm", prompt: "Brainstorm ideas for " },
];

function handlePromptClick(card: PromptCard) {
  assistChat.input = card.prompt;
}

const okMessages = ref<Msg[]>([]);
const okLoading = ref(false);
const identity = useIdentityStore();
let requestId = 0;
watch(() => identity.activeProfileId, () => {
  requestId++;
  okMessages.value = [];
  okLoading.value = false;
});
const showWelcome = computed(() => !okMessages.value.length && !assistChat.input.trim());
const overlayWelcomeTitle = "OK Assistant";

async function sendChat(text: string, _mode?: string, specialist?: string) {
  if (okLoading.value) return;
  if (text.length > 12000) {
    toast("Keep your message under 12,000 characters.", "error");
    return;
  }
  const id = ++requestId;
  const messages: Msg[] = [{ role: "user", content: text }];
  let length = text.length;
  for (const message of okMessages.value.slice(-7).reverse()) {
    length += message.content.length;
    if (length > 12000) break;
    messages.unshift(message);
  }
  okMessages.value.push({ role: "user", content: text });
  okLoading.value = true;
  try {
    const payload: { messages: Msg[]; specialist?: string } = { messages };
    if (specialist) payload.specialist = specialist;
    const response = await fetch(`${UCORE_BASE}/api/assistant/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(100000),
    });
    if (!response.ok) {
      if (response.status === 401) throw new Error("Choose a local profile to use OK Assistant.");
      if (response.status === 404) throw new Error("Restart uCore to load OK Assistant chat.");
      if (response.status === 504) throw new Error("Format Smith timed out. Check the local Ollama service.");
      throw new Error((await response.text()).slice(0, 240) || "OK Assistant is unavailable.");
    }
    const data = await response.json();
    if (id === requestId) okMessages.value.push({ role: "assistant", content: data.content });
  } catch (error) {
    if (id === requestId) {
      okMessages.value.pop();
      assistChat.input = text;
      toast(error instanceof TypeError ? "Could not reach uCore." : error instanceof Error ? error.message : "OK Assistant is unavailable.", "error");
    }
  } finally {
    if (id === requestId) okLoading.value = false;
  }
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
