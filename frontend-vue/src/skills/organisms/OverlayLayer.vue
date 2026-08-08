<template>
  <ToastOverlay />
  <AlertOverlay />
  <PopupOverlay />
  <StoriesOverlay />
  <ChatBubble>
    <ChatBubblePanel
      :chat-messages="chatMessages"
      :dev-messages="devMessages"
      :loading="chatLoading"
      :dev-available="extStore.isRunning('udev')"
      :dev-mode-on="devModeOn"
      :context-label="contextLabel"
      :current-task="currentTaskTitle"
      @send-chat="sendChat"
      @send-dev="sendDev"
      @toggle-dev-mode="toggleDevMode"
    />
  </ChatBubble>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import ToastOverlay from "../molecules/ToastOverlay.vue";
import AlertOverlay from "./AlertOverlay.vue";
import PopupOverlay from "./PopupOverlay.vue";
import StoriesOverlay from "./StoriesOverlay.vue";
import ChatBubble from "../molecules/ChatBubble.vue";
import ChatBubblePanel from "./ChatBubblePanel.vue";
import { useToast } from "../../composables/useToast";
import { useFeed } from "../../composables/useFeed";
import { useOverlay } from "../../composables/useOverlay";
import { useExtensionStore } from "../../stores/extensions";
import { useShellStore } from "../../stores/shell";
import { useDevModeStore } from "../../stores/devMode";
import { useWorkflowStore } from "../../stores/workflow";
import { SNACKBAR_BASE } from "../../api/base";

const { toast } = useToast();
const { events } = useFeed();
const shell = useShellStore();
const extStore = useExtensionStore();

// ─── uDev dev-server probe ──────────────────────────────────────
// Keep the Developer surface card / Dashboard "hidden" hint in sync with
// the actual dev server, even when it was started outside the SSE announce
// path (independently, or while the backend was unreachable).
let devProbeTimer: ReturnType<typeof setInterval> | null = null;

async function probeDevStatus() {
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/status`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return;
    const data = await res.json();
    if (data.active) extStore.markRunning("udev");
    else extStore.markOffline("udev");
  } catch {
    // Backend unreachable — leave current state.
  }
}

onMounted(() => {
  void probeDevStatus();
  devProbeTimer = setInterval(() => void probeDevStatus(), 15000);
});

onBeforeUnmount(() => {
  if (devProbeTimer) clearInterval(devProbeTimer);
});

// ─── Dev mode state ─────────────────────────────────────────────
const devMode = useDevModeStore();
const devModeOn = computed(
  () => devMode.mode === "on" || devMode.mode === "minimal",
);
const toggleDevMode = () => devMode.toggle();

// ─── Context strip ───────────────────────────────────────────────
const contextLabel = computed(() => {
  const path = shell.lastSurface ?? "";
  if (path.includes("/workflow")) return "Workflow";
  if (path.includes("/browserui")) return "Browser";
  if (path.includes("/intelligence")) return "Intelligence";
  if (path.includes("/snackbar")) return "Snackbar";
  if (path.includes("/system")) return "System";
  if (path.includes("/developer")) return "Developer";
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
const chatMessages = ref<Msg[]>([]);
const devMessages = ref<Msg[]>([]);
const chatLoading = ref(false);

async function sendChat(text: string) {
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
    chatMessages.value.push({
      role: "assistant",
      content: data.response || data.message || "…",
    });
  } catch {
    chatMessages.value.push({
      role: "assistant",
      content: "Backend unavailable.",
    });
    toast("Chat backend unreachable", "warning");
  } finally {
    chatLoading.value = false;
  }
}

async function sendDev(text: string) {
  devMessages.value.push({ role: "user", content: text });
  chatLoading.value = true;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        history: devMessages.value.slice(-10),
        context: { surface: contextLabel.value, task: currentTaskTitle.value },
      }),
      signal: AbortSignal.timeout(30000),
    });
    const data = await res.json();
    devMessages.value.push({
      role: "assistant",
      content: data.response || data.message || "…",
    });
  } catch {
    devMessages.value.push({
      role: "assistant",
      content: "Developer backend unavailable.",
    });
    toast("Dev chat backend unreachable", "warning");
  } finally {
    chatLoading.value = false;
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
        if (id !== "udev")
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
