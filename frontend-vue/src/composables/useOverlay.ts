/**
 * @module composables/useOverlay
 * @description Global overlay state — alert, popup, stories. Singleton.
 */
import { ref, shallowRef } from "vue";

export type AlertType = "critical" | "warning" | "info" | "success";

export interface AlertConfig {
  type: AlertType;
  title: string;
  message: string;
  actions?: Array<{
    label: string;
    variant?: "primary" | "secondary" | "ghost";
    onClick: () => void;
  }>;
}

export interface PopupConfig {
  title: string;
  content: string; // HTML or plain text
  actions?: Array<{
    label: string;
    variant?: "primary" | "secondary" | "ghost";
    onClick: () => void;
  }>;
}

export interface StorySlide {
  title?: string;
  content: string; // markdown
  layout?: "default" | "lead" | "center";
}

export interface StoriesConfig {
  title: string;
  slides: StorySlide[] | string[] | string;
  theme?: "dark" | "light";
  onComplete?: () => void;
}

type OverlayType = "none" | "alert" | "popup" | "stories";

// Module-level singleton
const activeType = ref<OverlayType>("none");
const alertConfig = shallowRef<AlertConfig | null>(null);
const popupConfig = shallowRef<PopupConfig | null>(null);
const storiesConfig = shallowRef<StoriesConfig | null>(null);

function showAlert(config: AlertConfig) {
  alertConfig.value = config;
  activeType.value = "alert";
}

function showPopup(config: PopupConfig) {
  popupConfig.value = config;
  activeType.value = "popup";
}

function showStories(config: StoriesConfig) {
  storiesConfig.value = config;
  activeType.value = "stories";
}

function dismiss() {
  if (activeType.value === "stories") {
    storiesConfig.value?.onComplete?.();
  }
  activeType.value = "none";
  alertConfig.value = null;
  popupConfig.value = null;
  storiesConfig.value = null;
}

export function useOverlay() {
  return {
    activeType,
    alertConfig,
    popupConfig,
    storiesConfig,
    showAlert,
    showPopup,
    showStories,
    dismiss,
  };
}
