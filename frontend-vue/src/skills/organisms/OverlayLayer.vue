<template>
  <ToastOverlay />
  <AlertOverlay />
  <PopupOverlay />
  <StoriesOverlay />
  <!-- Floating chat bubble — bottom-right on all surfaces -->
  <ChatBubble>
    <ChatBubblePanel
      :messages="chatMessages"
      :loading="chatLoading"
      @send="sendChatMessage"
    />
  </ChatBubble>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import ToastOverlay from "../molecules/ToastOverlay.vue";
import AlertOverlay from "./AlertOverlay.vue";
import PopupOverlay from "./PopupOverlay.vue";
import StoriesOverlay from "./StoriesOverlay.vue";
import ChatBubble from "../molecules/ChatBubble.vue";
import ChatBubblePanel from "./ChatBubblePanel.vue";
import { useToast } from "../../composables/useToast";
import { useFeed } from "../../composables/useFeed";
import { useOverlay } from "../../composables/useOverlay";
import { SNACKBAR_BASE } from "../../api/base";

const { toast } = useToast();
const { events } = useFeed();
const overlay = useOverlay();

// ─── Chat state ────────────────────────────────────────────────
interface ChatMsg {
  role: "user" | "assistant";
  content: string;
}
const chatMessages = ref<ChatMsg[]>([]);
const chatLoading = ref(false);

async function sendChatMessage(text: string) {
  chatMessages.value.push({ role: "user", content: text });
  chatLoading.value = true;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        history: chatMessages.value.slice(-10),
      }),
      signal: AbortSignal.timeout(30000),
    });
    const data = await res.json();
    const reply = data.response || data.message || data.content || "…";
    chatMessages.value.push({ role: "assistant", content: reply });
  } catch {
    chatMessages.value.push({
      role: "assistant",
      content: "Backend unavailable. Try again later.",
    });
  } finally {
    chatLoading.value = false;
  }
}

// Map feed events → toast notifications
watch(
  () => events.value.at(-1),
  (event) => {
    if (!event) return;
    switch (event.type) {
      case "skill_complete":
        toast(`${event.data.skill || "Skill"} completed`, "success", {
          duration: 4000,
        });
        break;
      case "skill_error":
        toast(
          `${event.data.skill || "Skill"} failed: ${event.data.error || ""}`,
          "error",
          { duration: 6000 },
        );
        break;
      case "toast": {
        const msg = event.data.message as string;
        if (msg) toast(msg, (event.data.type as any) || "info");
        break;
      }
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
