import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { registerSW } from "virtual:pwa-register";

interface InstallPromptEvent extends Event { prompt(): Promise<void>; userChoice: Promise<{ outcome: "accepted" | "dismissed" }> }
const INSTALL_DISMISSED = "ucore-pwa-install-dismissed";

export function usePwa() {
  const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);
  const installEvent = ref<InstallPromptEvent | null>(null);
  const dwellComplete = ref(false);
  const installing = ref(false);
  const installMessage = ref("");
  let dwellTimer: ReturnType<typeof setTimeout> | undefined;
  const updateOnline = () => { online.value = navigator.onLine; };
  const captureInstall = (event: Event) => { event.preventDefault(); installEvent.value = event as InstallPromptEvent; };
  const canInstall = computed(() => dwellComplete.value && Boolean(installEvent.value) && localStorage.getItem(INSTALL_DISMISSED) !== "true");

  async function install() {
    const event = installEvent.value;
    if (!event) {
      installMessage.value = "Installation is not available in this browser. Use its app or site menu to install uCore.";
      return false;
    }
    installing.value = true;
    installMessage.value = "";
    try {
      await event.prompt();
      const choice = await Promise.race([
        event.userChoice,
        new Promise<{ outcome: "dismissed" }>((resolve) =>
          setTimeout(() => resolve({ outcome: "dismissed" }), 5000),
        ),
      ]);
      const accepted = choice.outcome === "accepted";
      installEvent.value = null;
      installMessage.value = accepted
        ? "uCore was installed."
        : "The install prompt was dismissed or could not open. Use the browser app menu to install uCore.";
      return accepted;
    } catch {
      installEvent.value = null;
      installMessage.value = "This browser could not open its install prompt. Use the browser app or site menu to install uCore.";
      return false;
    } finally {
      installing.value = false;
    }
  }
  function dismissInstall() {
    localStorage.setItem(INSTALL_DISMISSED, "true");
    installEvent.value = null;
    installMessage.value = "";
  }

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
  return { online, canInstall, installing, installMessage, install, dismissInstall };
}
