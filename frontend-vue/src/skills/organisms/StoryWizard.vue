<template>
  <div class="story-wizard">
    <!-- Top progress bar -->
    <div class="story-wizard__progress-bar">
      <div
        class="story-wizard__progress-fill"
        :style="{ width: `${progressPct}%` }"
      />
    </div>

    <!-- Header: title + step counter -->
    <div class="story-wizard__header">
      <div class="story-wizard__step-label">
        <span class="story-wizard__step-num">{{ currentStep + 1 }}</span>
        <span class="story-wizard__step-of">of {{ steps.length }}</span>
      </div>
      <h2 class="story-wizard__title">{{ steps[currentStep]?.title }}</h2>
      <p v-if="steps[currentStep]?.subtitle" class="story-wizard__subtitle">
        {{ steps[currentStep].subtitle }}
      </p>
    </div>

    <!-- Step dot indicators -->
    <div class="story-wizard__dots" role="tablist">
      <button
        v-for="(step, i) in steps"
        :key="i"
        class="story-wizard__dot"
        :class="{
          'story-wizard__dot--done': i < currentStep,
          'story-wizard__dot--active': i === currentStep,
        }"
        :aria-label="`Go to step ${i + 1}: ${step.title}`"
        :aria-current="i === currentStep ? 'step' : undefined"
        role="tab"
        @click="goTo(i)"
      />
    </div>

    <!-- Slide content -->
    <div class="story-wizard__stage">
      <TransitionGroup :name="`slide-${direction}`">
        <div
          :key="currentStep"
          class="story-wizard__slide"
          :class="`story-wizard__slide--${steps[currentStep]?.layout ?? 'default'}`"
        >
          <slot :name="`step-${currentStep}`">
            <div v-if="steps[currentStep]?.html" v-html="steps[currentStep].html" />
            <p v-else class="story-wizard__placeholder">Step {{ currentStep + 1 }}</p>
          </slot>
        </div>
      </TransitionGroup>
    </div>

    <!-- Navigation footer -->
    <div class="story-wizard__nav">
      <button
        class="story-wizard__nav-btn"
        :disabled="currentStep === 0"
        @click="prev"
      >
        <span class="material-symbols-outlined">chevron_left</span>
        Previous
      </button>
      <div class="story-wizard__nav-center">
        <slot name="footer-center" />
      </div>
      <button
        class="story-wizard__nav-btn story-wizard__nav-btn--primary"
        @click="next"
      >
        {{ isLast ? finishLabel : 'Next' }}
        <span class="material-symbols-outlined">
          {{ isLast ? 'check' : 'chevron_right' }}
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component StoryWizard
 * @description Step-by-step wizard for settings, onboarding, and tutorials.
 * Each step is a full-panel "slide" with navigation.
 * Use slots named `step-0`, `step-1`, etc. for step content.
 * Or provide `html` in each step definition for simple HTML content.
 */
import { computed, ref } from 'vue';

export interface WizardStep {
  title: string;
  subtitle?: string;
  layout?: 'default' | 'lead' | 'center';
  html?: string;
}

const props = withDefaults(defineProps<{
  steps: WizardStep[];
  modelValue?: number;
  finishLabel?: string;
}>(), {
  modelValue: 0,
  finishLabel: 'Done',
});

const emit = defineEmits<{
  'update:modelValue': [step: number];
  finish: [];
}>();

const direction = ref<'forward' | 'back'>('forward');

const currentStep = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
});

const isLast = computed(() => currentStep.value === props.steps.length - 1);

const progressPct = computed(
  () => ((currentStep.value + 1) / props.steps.length) * 100,
);

function next() {
  if (isLast.value) {
    emit('finish');
    return;
  }
  direction.value = 'forward';
  currentStep.value = currentStep.value + 1;
}

function prev() {
  if (currentStep.value === 0) return;
  direction.value = 'back';
  currentStep.value = currentStep.value - 1;
}

function goTo(i: number) {
  direction.value = i > currentStep.value ? 'forward' : 'back';
  currentStep.value = i;
}
</script>

<style scoped>
.story-wizard {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: var(--usx-color-background);
  overflow: hidden;
}

/* ─── Progress bar ────────────────────────────────────────────── */

.story-wizard__progress-bar {
  height: 3px;
  background-color: var(--usx-color-border);
  flex-shrink: 0;
}

.story-wizard__progress-fill {
  height: 100%;
  background-color: var(--usx-color-primary);
  transition: width 300ms ease;
}

/* ─── Header ──────────────────────────────────────────────────── */

.story-wizard__header {
  padding: var(--usx-spacing-xl) var(--usx-spacing-xl) var(--usx-spacing-md);
  flex-shrink: 0;
  border-bottom: 1px solid var(--usx-color-border);
}

.story-wizard__step-label {
  display: flex;
  align-items: baseline;
  gap: var(--usx-spacing-xs);
  margin-bottom: var(--usx-spacing-xs);
}

.story-wizard__step-num {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-primary);
  line-height: 1;
}

.story-wizard__step-of {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.story-wizard__title {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  margin: 0;
}

.story-wizard__subtitle {
  margin: var(--usx-spacing-xs) 0 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  line-height: 1.5;
}

/* ─── Step dots ───────────────────────────────────────────────── */

.story-wizard__dots {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-xl);
  flex-shrink: 0;
}

.story-wizard__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  background-color: var(--usx-color-border);
  cursor: pointer;
  transition: all 200ms ease;
  padding: 0;
}

.story-wizard__dot--done {
  background-color: color-mix(in srgb, var(--usx-color-primary) 50%, transparent);
  transform: scale(0.9);
}

.story-wizard__dot--active {
  background-color: var(--usx-color-primary);
  transform: scale(1.2);
  border-radius: 4px;
  width: 20px;
}

/* ─── Stage / slide ───────────────────────────────────────────── */

.story-wizard__stage {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.story-wizard__slide {
  position: absolute;
  inset: 0;
  overflow-y: auto;
  padding: var(--usx-spacing-xl);
}

.story-wizard__slide--lead {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.story-wizard__slide--center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.story-wizard__placeholder {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

/* ─── Navigation ──────────────────────────────────────────────── */

.story-wizard__nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-md) var(--usx-spacing-xl);
  border-top: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface);
  flex-shrink: 0;
  gap: var(--usx-spacing-md);
}

.story-wizard__nav-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.story-wizard__nav-btn {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-xl);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 150ms ease;
  white-space: nowrap;
}

.story-wizard__nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.story-wizard__nav-btn:not(:disabled):hover {
  background-color: var(--usx-color-surface-variant);
}

.story-wizard__nav-btn--primary {
  background-color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  color: white;
}

.story-wizard__nav-btn--primary:not(:disabled):hover {
  background-color: var(--usx-color-primary-hover);
}

/* ─── Slide transitions ───────────────────────────────────────── */

.slide-forward-enter-active,
.slide-forward-leave-active,
.slide-back-enter-active,
.slide-back-leave-active {
  transition: all 250ms ease;
  position: absolute;
  inset: 0;
}

.slide-forward-enter-from { transform: translateX(40px); opacity: 0; }
.slide-forward-leave-to   { transform: translateX(-40px); opacity: 0; }
.slide-back-enter-from    { transform: translateX(-40px); opacity: 0; }
.slide-back-leave-to      { transform: translateX(40px); opacity: 0; }

@media (prefers-reduced-motion: reduce) {
  .slide-forward-enter-active,
  .slide-forward-leave-active,
  .slide-back-enter-active,
  .slide-back-leave-active { transition: opacity 150ms ease; }
  .slide-forward-enter-from,
  .slide-forward-leave-to,
  .slide-back-enter-from,
  .slide-back-leave-to { transform: none; }
}
</style>
