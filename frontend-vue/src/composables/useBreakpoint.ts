import { onBeforeUnmount, onMounted, ref } from "vue";

export function useBreakpoint(query = "(max-width: 40rem)") {
  const matches = ref(false);
  let media: MediaQueryList | null = null;
  const update = () => { matches.value = media?.matches ?? false; };
  onMounted(() => {
    if (typeof window.matchMedia !== "function") return;
    media = window.matchMedia(query);
    update();
    media.addEventListener("change", update);
  });
  onBeforeUnmount(() => media?.removeEventListener("change", update));
  return matches;
}
