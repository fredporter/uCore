<template>
  <Teleport to="body">
    <div class="toast-stack" aria-live="polite" aria-atomic="false">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="`toast--${toast.type}`"
          role="status"
        >
          <div class="toast__icon">
            <UIcon :name="iconFor(toast.type)" />
          </div>
          <span class="toast__message">{{ toast.message }}</span>
          <button
            v-if="toast.action"
            class="toast__action"
            @click="
              toast.action!.onClick();
              dismiss(toast.id);
            "
          >
            {{ toast.action.label }}
          </button>
          <button
            class="toast__close"
            :aria-label="`Dismiss: ${toast.message}`"
            @click="dismiss(toast.id)"
          >
            <UIcon name="close" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import UIcon from "../atoms/UIcon.vue";
import { useToast, type ToastType } from "../../composables/useToast";

const { toasts, dismiss } = useToast();

const ICONS: Record<ToastType, string> = {
  success: "check_circle",
  error: "error",
  warning: "warning",
  info: "info",
};

function iconFor(type: ToastType): string {
  return ICONS[type] ?? "info";
}
</script>

<style scoped>
.toast-stack {
  position: fixed;
  bottom: var(--usx-spacing-xl);
  right: var(--usx-spacing-xl);
  z-index: 1100;
  display: flex;
  flex-direction: column-reverse;
  gap: var(--usx-spacing-sm);
  pointer-events: none;
  max-width: 360px;
  width: calc(100vw - var(--usx-spacing-2xl) * 2);
}

/* ─── Toast card ──────────────────────────────────────────────── */

.toast {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background-color: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-left: 4px solid var(--usx-color-info);
  border-radius: var(--usx-radius-md);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  pointer-events: all;
  font-size: var(--usx-font-size-sm);
}

.toast--success {
  border-left-color: var(--usx-color-success);
}
.toast--error {
  border-left-color: var(--usx-color-danger);
}
.toast--warning {
  border-left-color: var(--usx-color-warning);
}
.toast--info {
  border-left-color: var(--usx-color-info);
}

.toast__icon {
  flex-shrink: 0;
  font-size: 18px;
}

.toast--success .toast__icon {
  color: var(--usx-color-success);
}
.toast--error .toast__icon {
  color: var(--usx-color-danger);
}
.toast--warning .toast__icon {
  color: var(--usx-color-warning);
}
.toast--info .toast__icon {
  color: var(--usx-color-info);
}

.toast__message {
  flex: 1;
  color: var(--usx-color-on-surface);
  line-height: 1.4;
}

.toast__action {
  padding: 2px var(--usx-spacing-sm);
  border: 1px solid var(--usx-color-primary);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-primary);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}

.toast__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--usx-color-on-surface-muted);
  border-radius: var(--usx-radius-sm);
  flex-shrink: 0;
  font-size: 14px;
  padding: 0;
}

.toast__close:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

/* ─── TransitionGroup ─────────────────────────────────────────── */

.toast-enter-active {
  transition: all 200ms ease;
}
.toast-leave-active {
  transition: all 180ms ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active {
    transition: none;
  }
}

@media (max-width: 480px) {
  .toast-stack {
    bottom: var(--usx-spacing-md);
    right: var(--usx-spacing-md);
    left: var(--usx-spacing-md);
    width: auto;
  }
}
</style>
