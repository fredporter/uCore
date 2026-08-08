<template>
  <Teleport to="body">
    <Transition name="stories-fade">
      <div
        v-if="overlay.storiesConfig.value"
        class="stories-overlay"
        role="dialog"
        aria-modal="true"
        @keydown.escape="overlay.dismiss()"
        @keydown.right="nextSlide"
        @keydown.left="prevSlide"
      >
        <!-- Progress bar -->
        <div class="stories-progress">
          <div
            class="stories-progress__fill"
            :style="{ width: `${progressPct}%` }"
          />
        </div>

        <!-- Header -->
        <div class="stories-header">
          <span class="stories-header__title">{{ cfg.title }}</span>
          <div class="stories-header__meta">
            {{ currentIndex + 1 }} / {{ cfg.slides.length }}
          </div>
          <button
            class="stories-header__close"
            aria-label="Close"
            @click="overlay.dismiss()"
          >
            <UIcon name="close" />
          </button>
        </div>

        <!-- Slide content -->
        <div class="stories-stage">
          <Transition :name="`slide-${direction}`" mode="out-in">
            <div
              :key="currentIndex"
              class="stories-slide"
              :class="`stories-slide--${currentSlide.layout ?? 'default'}`"
              v-html="currentSlide.content"
            />
          </Transition>
        </div>

        <!-- Navigation -->
        <div class="stories-nav">
          <button
            class="stories-nav__btn"
            :disabled="currentIndex === 0"
            @click="prevSlide"
          >
            <UIcon name="chevron_left" /> Previous
          </button>
          <div class="stories-nav__dots">
            <button
              v-for="(_, i) in cfg.slides"
              :key="i"
              class="stories-nav__dot"
              :class="{ 'stories-nav__dot--active': i === currentIndex }"
              :aria-label="`Go to slide ${i + 1}`"
              @click="goTo(i)"
            />
          </div>
          <button
            class="stories-nav__btn stories-nav__btn--primary"
            @click="onNext"
          >
            {{ isLast ? "Finish" : "Next" }}
            <UIcon v-if="!isLast" name="chevron_right" />
            <UIcon v-else name="check" />
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import UIcon from "../atoms/UIcon.vue";
import { useOverlay } from "../../composables/useOverlay";

const overlay = useOverlay();
const currentIndex = ref(0);
const direction = ref<"forward" | "back">("forward");

const cfg = computed(() => overlay.storiesConfig.value!);
const currentSlide = computed(() => cfg.value.slides[currentIndex.value]);
const isLast = computed(
  () => currentIndex.value === cfg.value.slides.length - 1,
);
const progressPct = computed(
  () => ((currentIndex.value + 1) / cfg.value.slides.length) * 100,
);

function nextSlide() {
  if (currentIndex.value < cfg.value.slides.length - 1) {
    direction.value = "forward";
    currentIndex.value++;
  }
}

function prevSlide() {
  if (currentIndex.value > 0) {
    direction.value = "back";
    currentIndex.value--;
  }
}

function goTo(index: number) {
  direction.value = index > currentIndex.value ? "forward" : "back";
  currentIndex.value = index;
}

function onNext() {
  if (isLast.value) {
    overlay.dismiss();
  } else {
    nextSlide();
  }
}
</script>

<style scoped>
.stories-overlay {
  position: fixed;
  inset: 0;
  z-index: 1400;
  display: flex;
  flex-direction: column;
  background-color: var(--usx-color-background);
  outline: none;
}

/* ─── Progress bar ────────────────────────────────────────────── */

.stories-progress {
  height: 3px;
  background-color: var(--usx-color-border);
  flex-shrink: 0;
}

.stories-progress__fill {
  height: 100%;
  background-color: var(--usx-color-primary);
  transition: width 300ms ease;
}

/* ─── Header ──────────────────────────────────────────────────── */

.stories-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: 1px solid var(--usx-color-border);
  flex-shrink: 0;
}

.stories-header__title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  flex: 1;
}

.stories-header__meta {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.stories-header__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
}

.stories-header__close:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

/* ─── Slide stage ─────────────────────────────────────────────── */

.stories-stage {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.stories-slide {
  position: absolute;
  inset: 0;
  padding: var(--usx-spacing-2xl) var(--usx-spacing-xl);
  overflow-y: auto;
  font-size: var(--usx-font-size-base);
  line-height: 1.7;
  color: var(--usx-color-on-surface);
}

.stories-slide--lead {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: var(--usx-font-size-xl);
}

.stories-slide--center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

/* ─── Navigation ──────────────────────────────────────────────── */

.stories-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-top: 1px solid var(--usx-color-border);
  flex-shrink: 0;
}

.stories-nav__btn {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 150ms ease;
}

.stories-nav__btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.stories-nav__btn--primary {
  background-color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  color: white;
}

.stories-nav__btn--primary:hover {
  background-color: var(--usx-color-primary-hover);
}

.stories-nav__dots {
  display: flex;
  gap: var(--usx-spacing-xs);
  align-items: center;
}

.stories-nav__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  background-color: var(--usx-color-border);
  cursor: pointer;
  transition: all 150ms ease;
  padding: 0;
}

.stories-nav__dot--active {
  background-color: var(--usx-color-primary);
  transform: scale(1.3);
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

.slide-forward-enter-from {
  transform: translateX(100%);
  opacity: 0;
}
.slide-forward-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}
.slide-back-enter-from {
  transform: translateX(-100%);
  opacity: 0;
}
.slide-back-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* ─── Overlay entrance ────────────────────────────────────────── */

.stories-fade-enter-active,
.stories-fade-leave-active {
  transition: opacity 200ms ease;
}
.stories-fade-enter-from,
.stories-fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .stories-progress__fill,
  .slide-forward-enter-active,
  .slide-forward-leave-active,
  .slide-back-enter-active,
  .slide-back-leave-active,
  .stories-fade-enter-active,
  .stories-fade-leave-active {
    transition: none;
  }
}
</style>
