import { onBeforeUnmount, onMounted, type Ref } from "vue";

export function useSwipe(target: Ref<HTMLElement | null>, options: { left?: () => void; right?: () => void; threshold?: number }) {
  let startX = 0;
  let startY = 0;
  const threshold = options.threshold ?? 64;
  const start = (event: TouchEvent) => { startX = event.touches[0]?.clientX ?? 0; startY = event.touches[0]?.clientY ?? 0; };
  const end = (event: TouchEvent) => {
    const touch = event.changedTouches[0];
    if (!touch) return;
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;
    if (Math.abs(dx) < threshold || Math.abs(dx) < Math.abs(dy) * 1.25) return;
    if (dx > 0) options.right?.(); else options.left?.();
  };
  onMounted(() => { target.value?.addEventListener("touchstart", start, { passive: true }); target.value?.addEventListener("touchend", end, { passive: true }); });
  onBeforeUnmount(() => { target.value?.removeEventListener("touchstart", start); target.value?.removeEventListener("touchend", end); });
}
