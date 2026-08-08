<template>
  <Teleport to="body">
    <Transition name="alert-fade">
      <div
        v-if="overlay.alertConfig.value"
        class="alert-overlay"
        :class="{ 'alert-overlay--blocking': isBlocking }"
        @click.self="onBackdropClick"
        role="alertdialog"
        aria-modal="true"
        :aria-labelledby="`alert-title-${uid}`"
      >
        <div class="alert-modal" :class="`alert-modal--${cfg.type}`">
          <div class="alert-modal__icon">
            <UIcon :name="iconFor(cfg.type)" />
          </div>
          <div class="alert-modal__body">
            <h3 :id="`alert-title-${uid}`" class="alert-modal__title">
              {{ cfg.title }}
            </h3>
            <p class="alert-modal__message">{{ cfg.message }}</p>
          </div>
          <div class="alert-modal__actions">
            <button
              v-for="action in cfg.actions"
              :key="action.label"
              class="alert-btn"
              :class="`alert-btn--${action.variant ?? 'secondary'}`"
              @click="
                action.onClick();
                overlay.dismiss();
              "
            >
              {{ action.label }}
            </button>
            <button
              v-if="!cfg.actions?.length"
              class="alert-btn alert-btn--primary"
              @click="overlay.dismiss()"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";
import UIcon from "../atoms/UIcon.vue";
import { useOverlay, type AlertType } from "../../composables/useOverlay";

const overlay = useOverlay();
const uid = Math.random().toString(36).slice(2, 8);

const cfg = computed(() => overlay.alertConfig.value!);
const isBlocking = computed(() => cfg.value?.type === "critical");

const ICONS: Record<AlertType, string> = {
  critical: "error",
  warning: "warning",
  info: "info",
  success: "check_circle",
};

function iconFor(type: AlertType): string {
  return ICONS[type] ?? "info";
}

function onBackdropClick() {
  if (!isBlocking.value) overlay.dismiss();
}
</script>

<style scoped>
.alert-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-lg);
  background-color: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
}

.alert-overlay--blocking {
  background-color: rgba(0, 0, 0, 0.7);
}

/* ─── Modal card ──────────────────────────────────────────────── */

.alert-modal {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-xl);
  background-color: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.25);
  width: 100%;
  max-width: 440px;
  border-top: 4px solid var(--usx-color-info);
}

.alert-modal--critical {
  border-top-color: var(--usx-color-danger);
}
.alert-modal--warning {
  border-top-color: var(--usx-color-warning);
}
.alert-modal--success {
  border-top-color: var(--usx-color-success);
}
.alert-modal--info {
  border-top-color: var(--usx-color-info);
}

.alert-modal__icon {
  font-size: 32px;
  text-align: center;
}

.alert-modal--critical .alert-modal__icon {
  color: var(--usx-color-danger);
}
.alert-modal--warning .alert-modal__icon {
  color: var(--usx-color-warning);
}
.alert-modal--success .alert-modal__icon {
  color: var(--usx-color-success);
}
.alert-modal--info .alert-modal__icon {
  color: var(--usx-color-info);
}

.alert-modal__body {
  text-align: center;
}

.alert-modal__title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  margin: 0 0 var(--usx-spacing-xs);
}

.alert-modal__message {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  line-height: 1.5;
  margin: 0;
}

.alert-modal__actions {
  display: flex;
  justify-content: center;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

/* ─── Action buttons ──────────────────────────────────────────── */

.alert-btn {
  padding: var(--usx-spacing-sm) var(--usx-spacing-xl);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 150ms ease;
  border: 1px solid transparent;
}

.alert-btn--primary {
  background-color: var(--usx-color-primary);
  color: white;
}
.alert-btn--primary:hover {
  background-color: var(--usx-color-primary-hover);
}

.alert-btn--secondary {
  background-color: transparent;
  border-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}
.alert-btn--secondary:hover {
  background-color: var(--usx-color-surface-variant);
}

.alert-btn--ghost {
  background: transparent;
  color: var(--usx-color-on-surface-muted);
}
.alert-btn--ghost:hover {
  color: var(--usx-color-on-surface);
}

/* ─── Transition ──────────────────────────────────────────────── */

.alert-fade-enter-active,
.alert-fade-leave-active {
  transition: all 200ms ease;
}
.alert-fade-enter-from,
.alert-fade-leave-to {
  opacity: 0;
}
.alert-fade-enter-from .alert-modal,
.alert-fade-leave-to .alert-modal {
  transform: scale(0.96);
}
</style>
