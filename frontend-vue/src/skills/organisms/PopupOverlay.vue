<template>
  <Teleport to="body">
    <Transition name="popup-fade">
      <div
        v-if="overlay.popupConfig.value"
        class="popup-overlay"
        @click.self="overlay.dismiss()"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`popup-title-${uid}`"
      >
        <div class="popup-modal">
          <div class="popup-modal__header">
            <h3 :id="`popup-title-${uid}`" class="popup-modal__title">
              {{ cfg.title }}
            </h3>
            <button
              class="popup-modal__close"
              aria-label="Close"
              @click="overlay.dismiss()"
            >
              <UIcon name="close" />
            </button>
          </div>

          <div class="popup-modal__body" v-html="cfg.content" />

          <div v-if="cfg.actions?.length" class="popup-modal__footer">
            <button
              v-for="action in cfg.actions"
              :key="action.label"
              class="popup-btn"
              :class="`popup-btn--${action.variant ?? 'secondary'}`"
              @click="
                action.onClick();
                overlay.dismiss();
              "
            >
              {{ action.label }}
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
import { useOverlay } from "../../composables/useOverlay";

const overlay = useOverlay();
const uid = Math.random().toString(36).slice(2, 8);

const cfg = computed(() => overlay.popupConfig.value!);
</script>

<style scoped>
.popup-overlay {
  position: fixed;
  inset: 0;
  z-index: 1300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-lg);
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
}

.popup-modal {
  display: flex;
  flex-direction: column;
  background-color: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 560px;
  max-height: 80vh;
  overflow: hidden;
}

.popup-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface-variant);
  flex-shrink: 0;
}

.popup-modal__title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  margin: 0;
}

.popup-modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
}

.popup-modal__close:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

.popup-modal__body {
  flex: 1;
  padding: var(--usx-spacing-lg);
  overflow-y: auto;
  font-size: var(--usx-font-size-sm);
  line-height: 1.6;
  color: var(--usx-color-on-surface);
}

.popup-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-top: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface-variant);
  flex-shrink: 0;
}

.popup-btn {
  padding: var(--usx-spacing-sm) var(--usx-spacing-xl);
  border-radius: var(--usx-radius-md);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 150ms ease;
  border: 1px solid transparent;
}

.popup-btn--primary {
  background-color: var(--usx-color-primary);
  color: white;
}
.popup-btn--primary:hover {
  background-color: var(--usx-color-primary-hover);
}

.popup-btn--secondary {
  background-color: transparent;
  border-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}
.popup-btn--secondary:hover {
  background-color: var(--usx-color-surface-variant);
}

.popup-btn--ghost {
  background: transparent;
  color: var(--usx-color-on-surface-muted);
}

/* ─── Transition ──────────────────────────────────────────────── */

.popup-fade-enter-active,
.popup-fade-leave-active {
  transition: all 200ms ease;
}
.popup-fade-enter-from,
.popup-fade-leave-to {
  opacity: 0;
}
.popup-fade-enter-from .popup-modal,
.popup-fade-leave-to .popup-modal {
  transform: translateY(12px);
}
</style>
