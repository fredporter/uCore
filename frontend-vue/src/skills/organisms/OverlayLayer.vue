<template>
  <!-- All overlays are Teleported to body; this component is a logic host only -->
  <ToastOverlay />
  <AlertOverlay />
  <PopupOverlay />
  <StoriesOverlay />
</template>

<script setup lang="ts">
/**
 * @component OverlayLayer
 * @description Mounts all overlay components and wires useFeed events to toasts.
 * Place once in AppShell or App.vue root.
 */
import { watch } from "vue";
import ToastOverlay from "../molecules/ToastOverlay.vue";
import AlertOverlay from "./AlertOverlay.vue";
import PopupOverlay from "./PopupOverlay.vue";
import StoriesOverlay from "./StoriesOverlay.vue";
import { useToast } from "../../composables/useToast";
import { useFeed } from "../../composables/useFeed";
import { useOverlay } from "../../composables/useOverlay";

const { toast } = useToast();
const { events } = useFeed();

// Map feed events → toast notifications
watch(
  () => events.value.at(-1),
  (event) => {
    if (!event) return;
    switch (event.type) {
      case "skill_complete": {
        const name = (event.data.skill as string) || "Skill";
        toast(`${name} completed`, "success", { duration: 4000 });
        break;
      }
      case "skill_error": {
        const name = (event.data.skill as string) || "Skill";
        const msg = (event.data.error as string) || "Unknown error";
        toast(`${name} failed: ${msg}`, "error", { duration: 6000 });
        break;
      }
      case "toast": {
        // Backend-initiated toasts via POST /api/render/event
        const msg = (event.data.message as string) || "";
        const type = (event.data.type as any) || "info";
        if (msg) toast(msg, type);
        break;
      }
      case "alert": {
        // Backend-initiated critical alerts
        const overlay = useOverlay();
        overlay.showAlert({
          type: (event.data.level as any) || "warning",
          title: (event.data.title as string) || "System Alert",
          message: (event.data.message as string) || "",
        });
        break;
      }
    }
  },
);
</script>
