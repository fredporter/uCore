import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { registerSW } from "virtual:pwa-register";

interface InstallPromptEvent extends Event { prompt(): Promise<void>; userChoice: Promise<{ outcome: "accepted" | "dismissed" }> }
const INSTALL_DISMISSED = "ucore-pwa-install-dismissed";

export function usePwa() {
  const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
  const installEvent = ref<InstallPromptEvent | null>(null);
  const dwellComplete = ref(false);
  let dwellTimer: ReturnType<typeof setTimeout> | undefined;
  const updateOnline = () => { online.value = navigator.onLine; };
  const captureInstall = (event: Event) => { event.preventDefault(); installEvent.value = event as InstallPromptEvent; };
  const canInstall = computed(() => dwellComplete.value && Boolean(installEvent.value) && localStorage.getItem(INSTALL_DISMISSED) !== "true");

  async function install() {
    const event = installEvent.value;
    if (!event) return false;
    await event.prompt();
    const accepted = (await event.userChoice).outcome === "accepted";
    if (accepted) installEvent.value = null;
    return accepted;
  }
  function dismissInstall() { localStorage.setItem(INSTALL_DISMISSED, "true"); installEvent.value = null; }

  onMounted(() => {
    registerSW({ immediate: true });
    window.addEventListener("online", updateOnline);
    window.addEventListener("offline", updateOnline);
    window.addEventListener("beforeinstallprompt", captureInstall);
    dwellTimer = setTimeout(() => { dwellComplete.value = true; }, 30_000);
  });
  onBeforeUnmount(() => {
    clearTimeout(dwellTimer);
    window.removeEventListener("online", updateOnline);
    window.removeEventListener("offline", updateOnline);
    window.removeEventListener("beforeinstallprompt", captureInstall);
  });
  return { online, canInstall, install, dismissInstall };
}
