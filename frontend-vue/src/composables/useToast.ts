/**
 * @module composables/useToast
 * @description Global toast notification queue. Singleton — safe to call from anywhere.
 */
import { ref } from "vue";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  action?: { label: string; onClick: () => void };
  duration: number; // ms; 0 = persist
}

// Module-level singleton state
const toasts = ref<Toast[]>([]);
const timers = new Map<string, ReturnType<typeof setTimeout>>();

let seq = 0;

function toast(
  message: string,
  type: ToastType = "info",
  options?: { duration?: number; action?: Toast["action"] },
): string {
  const id = `toast-${Date.now()}-${++seq}`;
  const duration = options?.duration ?? 5000;

  toasts.value.push({ id, message, type, duration, action: options?.action });

  // Keep at most 4 toasts visible
  if (toasts.value.length > 4) toasts.value.shift();

  if (duration > 0) {
    timers.set(
      id,
      setTimeout(() => dismiss(id), duration),
    );
  }
  return id;
}

function dismiss(id: string) {
  const timer = timers.get(id);
  if (timer) {
    clearTimeout(timer);
    timers.delete(id);
  }
  const idx = toasts.value.findIndex((t) => t.id === id);
  if (idx !== -1) toasts.value.splice(idx, 1);
}

function dismissAll() {
  for (const id of timers.keys()) clearTimeout(timers.get(id));
  timers.clear();
  toasts.value = [];
}

export function useToast() {
  return { toasts, toast, dismiss, dismissAll };
}
