<template>
  <div class="alerts-recipe-container">
    <div class="alerts-header-meta">
      <span class="alerts-tag">USX Recipe: {{ recipe.recipe }}</span>
      <span class="alerts-tag">Patterns: Curtain + Toasts + Inline Banners + Dialog</span>
    </div>

    <!-- 1. Slide-down Notification Curtain (Top Announcement Bar) -->
    <Transition name="curtain-slide">
      <div
        v-if="curtainOpen && recipe.curtain"
        class="usx-curtain-banner"
        :class="`usx-curtain-banner--${recipe.curtain.severity}`"
        role="region"
        aria-label="Announcement curtain"
      >
        <div class="curtain-content">
          <UIcon :name="severityIcon(recipe.curtain.severity)" class="curtain-icon" />
          <div class="curtain-text">
            <strong class="curtain-title">{{ recipe.curtain.title }}</strong>
            <span class="curtain-msg">{{ recipe.curtain.message }}</span>
          </div>
          <button
            v-if="recipe.curtain.actionLabel"
            class="curtain-action-btn"
            @click="triggerToast('info', 'Curtain action triggered')"
          >
            {{ recipe.curtain.actionLabel }}
          </button>
        </div>
        <button
          v-if="recipe.curtain.dismissible"
          class="curtain-close-btn"
          aria-label="Dismiss announcement curtain"
          @click="curtainOpen = false"
        >
          <UIcon name="close" />
        </button>
      </div>
    </Transition>

    <div class="curtain-toggle-row">
      <button class="test-pill-btn" @click="curtainOpen = !curtainOpen">
        <UIcon :name="curtainOpen ? 'visibility_off' : 'visibility'" />
        {{ curtainOpen ? 'Hide Curtain Banner' : 'Show Curtain Banner' }}
      </button>
    </div>

    <!-- 2. Inline Surface Alert Banners -->
    <div class="alerts-section">
      <h3 class="section-title">Surface Inline Alert Banners</h3>
      <p class="section-desc">
        Contextual alert boxes embedded within surfaces for feedback and state notices.
      </p>

      <div class="inline-alerts-stack">
        <div
          v-for="alert in recipe.inlineAlerts"
          :key="alert.id"
          class="usx-inline-alert"
          :class="`usx-inline-alert--${alert.severity}`"
        >
          <div class="inline-alert-icon">
            <UIcon :name="severityIcon(alert.severity)" />
          </div>
          <div class="inline-alert-body">
            <h4 class="inline-alert-title">{{ alert.title }}</h4>
            <p class="inline-alert-message">{{ alert.message }}</p>
          </div>
          <span class="inline-alert-badge">{{ alert.severity.toUpperCase() }}</span>
        </div>
      </div>
    </div>

    <!-- 3. Interactive Floating Toast Notification Triggers -->
    <div class="alerts-section">
      <h3 class="section-title">Floating Toast Notifications</h3>
      <p class="section-desc">
        Transient bottom-right toasts for background events, progress, and async tasks. Click below to spawn live toasts:
      </p>

      <div class="interactive-triggers-grid">
        <button
          class="trigger-btn trigger-btn--success"
          @click="triggerToast('success', 'Operation completed: Git proposal committed to main branch')"
        >
          <UIcon name="check_circle" />
          Trigger Success Toast
        </button>
        <button
          class="trigger-btn trigger-btn--info"
          @click="triggerToast('info', 'Local Ollama model loaded: qwen2.5-coder:7b ready')"
        >
          <UIcon name="info" />
          Trigger Info Toast
        </button>
        <button
          class="trigger-btn trigger-btn--warning"
          @click="triggerToast('warning', 'Budget threshold alert: $0.08 / $0.10 task cap reserved')"
        >
          <UIcon name="warning" />
          Trigger Warning Toast
        </button>
        <button
          class="trigger-btn trigger-btn--error"
          @click="triggerToast('error', 'Execution error: Network policy offline denied socket connection')"
        >
          <UIcon name="error" />
          Trigger Error Toast
        </button>
      </div>
    </div>

    <!-- 4. Modal Alert Dialog Trigger -->
    <div class="alerts-section">
      <h3 class="section-title">Blocking & Confirmation Modal Dialogs</h3>
      <p class="section-desc">
        Modal overlay alerts for destructive operations, critical checkpoints, and authorization gates.
      </p>

      <div class="dialog-trigger-card">
        <div class="dialog-preview-info">
          <strong>{{ recipe.dialog.title }}</strong>
          <p>{{ recipe.dialog.message }}</p>
        </div>
        <button class="trigger-btn trigger-btn--primary" @click="triggerModalDialog">
          <UIcon name="open_in_new" />
          Launch Live Modal Dialog
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { AlertsRecipe } from '../recipes'
import UIcon from '../../skills/atoms/UIcon.vue'
import { useToast, type ToastType } from '../../composables/useToast'
import { useOverlay, type AlertType } from '../../composables/useOverlay'

const props = defineProps<{
  recipe: AlertsRecipe
}>()

const curtainOpen = ref(props.recipe.curtain?.visible ?? true)
const { toast } = useToast()
const overlay = useOverlay()

function severityIcon(severity: string): string {
  switch (severity) {
    case 'success':
      return 'check_circle'
    case 'critical':
    case 'error':
      return 'error'
    case 'warning':
      return 'warning'
    default:
      return 'info'
  }
}

function triggerToast(type: ToastType, message: string) {
  toast(message, type)
}

function triggerModalDialog() {
  const dlg = props.recipe.dialog
  overlay.showAlert({
    type: (dlg.type === 'critical' ? 'critical' : dlg.type) as AlertType,
    title: dlg.title,
    message: dlg.message,
    actions: [
      {
        label: dlg.confirmLabel,
        variant: 'primary',
        onClick: () => {
          toast('Proposal authorization confirmed', 'success')
        },
      },
      {
        label: dlg.cancelLabel || 'Cancel',
        variant: 'secondary',
        onClick: () => {
          toast('Authorization cancelled', 'info')
        },
      },
    ],
  })
}
</script>

<style scoped>
.alerts-recipe-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
}

.alerts-header-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.alerts-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--usx-color-surface-variant, rgba(255, 255, 255, 0.08));
  border-radius: 4px;
  color: var(--usx-color-on-surface-muted, #999);
  font-family: var(--usx-font-family-mono, monospace);
}

/* ─── 1. Curtain Banner ─────────────────────────────────────────── */
.usx-curtain-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.25rem;
  border-radius: var(--usx-radius-md, 8px);
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.15));
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.usx-curtain-banner--info {
  background: color-mix(in srgb, var(--usx-color-info, #0288d1) 15%, #1e1e1e);
  border-left: 4px solid var(--usx-color-info, #0288d1);
}
.usx-curtain-banner--warning {
  background: color-mix(in srgb, var(--usx-color-warning, #f57c00) 15%, #1e1e1e);
  border-left: 4px solid var(--usx-color-warning, #f57c00);
}
.usx-curtain-banner--critical {
  background: color-mix(in srgb, var(--usx-color-danger, #d32f2f) 15%, #1e1e1e);
  border-left: 4px solid var(--usx-color-danger, #d32f2f);
}
.usx-curtain-banner--success {
  background: color-mix(in srgb, var(--usx-color-success, #388e3c) 15%, #1e1e1e);
  border-left: 4px solid var(--usx-color-success, #388e3c);
}

.curtain-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.curtain-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.curtain-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.curtain-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #fff);
}

.curtain-msg {
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-muted, #ccc);
}

.curtain-action-btn {
  margin-left: auto;
  padding: 0.35rem 0.85rem;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 150ms ease;
  white-space: nowrap;
}

.curtain-action-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.curtain-close-btn {
  background: transparent;
  border: none;
  color: var(--usx-color-on-surface-muted, #888);
  cursor: pointer;
  padding: 0.25rem;
  margin-left: 0.75rem;
  display: flex;
  align-items: center;
}

.curtain-close-btn:hover {
  color: #fff;
}

.curtain-toggle-row {
  display: flex;
  justify-content: flex-end;
}

.test-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: transparent;
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.2));
  color: var(--usx-color-on-surface-muted, #aaa);
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  cursor: pointer;
}

.test-pill-btn:hover {
  color: #fff;
  border-color: var(--usx-color-primary, #646cff);
}

/* ─── 2. Sections ─────────────────────────────────────────────────── */
.alerts-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #fff);
  margin: 0;
}

.section-desc {
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-muted, #999);
  margin: 0;
}

.inline-alerts-stack {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.usx-inline-alert {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  padding: 0.85rem 1.25rem;
  border-radius: var(--usx-radius-md, 8px);
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.12));
  background: var(--usx-color-surface, #1e1e1e);
}

.usx-inline-alert--info {
  border-left: 4px solid var(--usx-color-info, #0288d1);
}
.usx-inline-alert--success {
  border-left: 4px solid var(--usx-color-success, #388e3c);
}
.usx-inline-alert--warning {
  border-left: 4px solid var(--usx-color-warning, #f57c00);
}
.usx-inline-alert--critical {
  border-left: 4px solid var(--usx-color-danger, #d32f2f);
}

.inline-alert-icon {
  font-size: 1.25rem;
  margin-top: 0.1rem;
}

.usx-inline-alert--info .inline-alert-icon {
  color: var(--usx-color-info, #0288d1);
}
.usx-inline-alert--success .inline-alert-icon {
  color: var(--usx-color-success, #388e3c);
}
.usx-inline-alert--warning .inline-alert-icon {
  color: var(--usx-color-warning, #f57c00);
}
.usx-inline-alert--critical .inline-alert-icon {
  color: var(--usx-color-danger, #d32f2f);
}

.inline-alert-body {
  flex: 1;
}

.inline-alert-title {
  margin: 0 0 0.2rem 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #fff);
}

.inline-alert-message {
  margin: 0;
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-muted, #ccc);
  line-height: 1.4;
}

.inline-alert-badge {
  font-size: 0.65rem;
  font-family: var(--usx-font-family-mono, monospace);
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--usx-color-on-surface-muted, #aaa);
}

/* ─── 3. Triggers Grid ───────────────────────────────────────────── */
.interactive-triggers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.trigger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: var(--usx-radius-md, 8px);
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.15));
  background: var(--usx-color-surface, #1e1e1e);
  color: var(--usx-color-on-surface, #fff);
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 180ms ease;
}

.trigger-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.trigger-btn--success:hover {
  border-color: var(--usx-color-success, #388e3c);
  color: var(--usx-color-success, #388e3c);
}
.trigger-btn--info:hover {
  border-color: var(--usx-color-info, #0288d1);
  color: var(--usx-color-info, #0288d1);
}
.trigger-btn--warning:hover {
  border-color: var(--usx-color-warning, #f57c00);
  color: var(--usx-color-warning, #f57c00);
}
.trigger-btn--error:hover {
  border-color: var(--usx-color-danger, #d32f2f);
  color: var(--usx-color-danger, #d32f2f);
}
.trigger-btn--primary {
  background: var(--usx-color-primary, #646cff);
  border-color: var(--usx-color-primary, #646cff);
  color: #fff;
}
.trigger-btn--primary:hover {
  background: var(--usx-color-primary-hover, #535bf2);
}

/* ─── 4. Dialog Card ─────────────────────────────────────────────── */
.dialog-trigger-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 1rem 1.25rem;
  border-radius: var(--usx-radius-md, 8px);
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.15));
  background: var(--usx-color-surface, #1e1e1e);
}

.dialog-preview-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.dialog-preview-info strong {
  font-size: 0.95rem;
  color: var(--usx-color-on-surface, #fff);
}

.dialog-preview-info p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--usx-color-on-surface-muted, #aaa);
}

/* ─── Transitions ─────────────────────────────────────────────────── */
.curtain-slide-enter-active,
.curtain-slide-leave-active {
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.curtain-slide-enter-from,
.curtain-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
