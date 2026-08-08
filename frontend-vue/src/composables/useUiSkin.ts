import { ref } from "vue";

export type UiSkinMode = "usx" | "flowbite" | "auto";
export type UiSkinResolved = "usx" | "flowbite";

const UI_SKIN_KEY = "ucore.ui-skin";

const uiSkinMode = ref<UiSkinMode>("auto");
const uiSkinResolved = ref<UiSkinResolved>("usx");

let initialized = false;
let mediaQuery: MediaQueryList | null = null;
let themeObserver: MutationObserver | null = null;

function resolveAutoSkin(): UiSkinResolved {
  const explicitTheme = document.documentElement.dataset.theme;
  if (explicitTheme === "dark") return "usx";
  if (explicitTheme === "light") return "flowbite";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "usx"
    : "flowbite";
}

function applyResolvedSkin(skin: UiSkinResolved) {
  uiSkinResolved.value = skin;
  document.documentElement.dataset.uiSkin = skin;
  document.documentElement.dataset.uiSkinMode = uiSkinMode.value;
}

function setUiSkinMode(mode: UiSkinMode) {
  uiSkinMode.value = mode;
  const resolved = mode === "auto" ? resolveAutoSkin() : mode;
  applyResolvedSkin(resolved);
  try {
    localStorage.setItem(UI_SKIN_KEY, mode);
  } catch {
    // no-op
  }
}

function cycleUiSkinMode() {
  if (uiSkinMode.value === "usx") {
    setUiSkinMode("flowbite");
    return;
  }
  if (uiSkinMode.value === "flowbite") {
    setUiSkinMode("auto");
    return;
  }
  setUiSkinMode("usx");
}

function toggleUiSkin() {
  const next: UiSkinMode =
    uiSkinResolved.value === "flowbite" ? "usx" : "flowbite";
  setUiSkinMode(next);
}

function initUiSkin() {
  if (initialized) return;
  initialized = true;

  let saved: UiSkinMode = "auto";
  try {
    const value = localStorage.getItem(UI_SKIN_KEY);
    if (value === "usx" || value === "flowbite" || value === "auto") {
      saved = value;
    }
  } catch {
    // no-op
  }

  setUiSkinMode(saved);

  mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaQuery.addEventListener("change", () => {
    if (uiSkinMode.value !== "auto") return;
    applyResolvedSkin(resolveAutoSkin());
  });

  themeObserver = new MutationObserver(() => {
    if (uiSkinMode.value !== "auto") return;
    applyResolvedSkin(resolveAutoSkin());
  });
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
}

export function useUiSkin() {
  return {
    uiSkinMode,
    uiSkinResolved,
    initUiSkin,
    setUiSkinMode,
    cycleUiSkinMode,
    toggleUiSkin,
  };
}
