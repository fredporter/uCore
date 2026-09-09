<template>
  <div class="story-recipe-container" tabindex="0" @keydown="handleKeydown">
    <!-- Progress Header -->
    <div class="story-progress-bar">
      <div
        class="story-progress-fill"
        :style="{ width: `${((currentStep + 1) / totalSteps) * 100}%` }"
      ></div>
    </div>

    <div class="story-header-meta">
      <span class="story-tag">USX Recipe: {{ recipe.recipe }}</span>
      <span class="story-step-badge">Step {{ currentStep + 1 }} of {{ totalSteps }}</span>
    </div>

    <!-- Active Question Stage -->
    <div class="story-stage">
      <Transition name="story-slide" mode="out-in">
        <div :key="currentQuestion.id" class="story-card">
          <div class="story-question-num">
            <span>{{ currentStep + 1 }}</span>
            <UIcon name="arrow_forward" class="num-arrow" />
          </div>

          <h2 class="story-headline">{{ currentQuestion.headline }}</h2>
          <p v-if="currentQuestion.subtext" class="story-subtext">
            {{ currentQuestion.subtext }}
          </p>

          <!-- Single / Multi Choice Options -->
          <div
            v-if="currentQuestion.type === 'single-choice' || currentQuestion.type === 'multi-choice'"
            class="story-options-grid"
          >
            <button
              v-for="opt in currentQuestion.options"
              :key="opt.id"
              class="story-option-btn"
              :class="{ 'story-option-btn--selected': answers[currentQuestion.id] === opt.id }"
              @click="selectOption(opt.id)"
            >
              <span v-if="opt.shortcut" class="story-shortcut-key">{{ opt.shortcut }}</span>
              <div class="story-option-content">
                <span class="story-option-label">{{ opt.label }}</span>
                <span v-if="opt.description" class="story-option-desc">{{ opt.description }}</span>
              </div>
              <UIcon
                v-if="answers[currentQuestion.id] === opt.id"
                name="check"
                class="story-check-icon"
              />
            </button>
          </div>

          <!-- Freeform Text Input -->
          <div v-else-if="currentQuestion.type === 'text'" class="story-text-container">
            <textarea
              v-model="answers[currentQuestion.id]"
              class="story-textarea"
              :placeholder="currentQuestion.placeholder || 'Type your answer here...'"
              rows="3"
              autofocus
            ></textarea>
            <div class="story-input-hint">
              <kbd class="kbd-key">Shift</kbd> + <kbd class="kbd-key">Enter</kbd> for newline
            </div>
          </div>

          <!-- Controls Bar -->
          <div class="story-controls">
            <button
              v-if="currentStep > 0"
              class="story-nav-btn story-nav-btn--secondary"
              @click="prevStep"
            >
              <UIcon name="arrow_back" />
              Back
            </button>

            <button
              class="story-nav-btn story-nav-btn--primary"
              :disabled="currentQuestion.required && !answers[currentQuestion.id]"
              @click="nextStep"
            >
              {{ isLastStep ? (recipe.submitLabel || 'Submit') : 'OK' }}
              <UIcon v-if="!isLastStep" name="check" />
              <span class="story-btn-hint">Press ↵</span>
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { StoryRecipe } from '../recipes'
import UIcon from '../../skills/atoms/UIcon.vue'

const props = defineProps<{
  recipe: StoryRecipe
}>()

const currentStep = ref(0)
const answers = ref<Record<string, string>>({})

const totalSteps = computed(() => props.recipe.questions.length)
const currentQuestion = computed(() => props.recipe.questions[currentStep.value])
const isLastStep = computed(() => currentStep.value === totalSteps.value - 1)

function selectOption(optId: string) {
  answers.value[currentQuestion.value.id] = optId
}

function nextStep() {
  if (currentQuestion.value.required && !answers.value[currentQuestion.value.id]) return
  if (isLastStep.value) {
    alert(`Story Form Completed!\nAnswers:\n${JSON.stringify(answers.value, null, 2)}`)
  } else {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) currentStep.value--
}

function handleKeydown(e: KeyboardEvent) {
  // Enter key advances
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    nextStep()
    return
  }
  // Number or letter shortcut match
  if (currentQuestion.value.options) {
    const matched = currentQuestion.value.options.find(
      (o) => o.shortcut?.toLowerCase() === e.key.toLowerCase(),
    )
    if (matched) {
      e.preventDefault()
      selectOption(matched.id)
    }
  }
}
</script>

<style scoped>
.story-recipe-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 100%;
  max-width: 780px;
  margin: 0 auto;
  outline: none;
}

/* Progress bar */
.story-progress-bar {
  height: 4px;
  background: var(--usx-color-surface-variant, #2a2a2a);
  border-radius: 2px;
  overflow: hidden;
  width: 100%;
}

.story-progress-fill {
  height: 100%;
  background: var(--usx-color-primary, #646cff);
  transition: width 350ms cubic-bezier(0.4, 0, 0.2, 1);
}

.story-header-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.story-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  background: var(--usx-color-surface-variant, rgba(255, 255, 255, 0.08));
  border-radius: 4px;
  color: var(--usx-color-on-surface-muted, #999);
  font-family: var(--usx-font-family-mono, monospace);
}

.story-step-badge {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--usx-color-primary, #646cff);
}

/* Stage & Card */
.story-stage {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.story-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.story-question-num {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--usx-color-primary, #646cff);
}

.num-arrow {
  font-size: 0.85rem;
}

.story-headline {
  font-size: 1.65rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--usx-color-on-surface, #fff);
  margin: 0;
}

.story-subtext {
  font-size: 1rem;
  color: var(--usx-color-on-surface-muted, #aaa);
  margin: 0 0 0.5rem 0;
  line-height: 1.5;
}

/* Choice Option Grid */
.story-options-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.story-option-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1.25rem;
  border-radius: var(--usx-radius-md, 8px);
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.15));
  background: var(--usx-color-surface, #1e1e1e);
  color: var(--usx-color-on-surface, #fff);
  cursor: pointer;
  text-align: left;
  transition: all 180ms ease;
}

.story-option-btn:hover {
  border-color: var(--usx-color-primary, #646cff);
  background: var(--usx-color-surface-hover, rgba(100, 108, 255, 0.08));
  transform: translateY(-1px);
}

.story-option-btn--selected {
  border-color: var(--usx-color-primary, #646cff);
  background: var(--usx-color-surface-variant, rgba(100, 108, 255, 0.16));
  box-shadow: 0 0 0 1px var(--usx-color-primary, #646cff);
}

.story-shortcut-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 4px;
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.2));
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: var(--usx-font-family-mono, monospace);
  background: rgba(255, 255, 255, 0.05);
  color: var(--usx-color-primary, #646cff);
}

.story-option-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.story-option-label {
  font-size: 1rem;
  font-weight: 500;
}

.story-option-desc {
  font-size: 0.8rem;
  color: var(--usx-color-on-surface-muted, #888);
}

.story-check-icon {
  color: var(--usx-color-primary, #646cff);
  font-size: 1.25rem;
}

/* Textarea input */
.story-text-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.story-textarea {
  width: 100%;
  padding: 1rem;
  background: var(--usx-color-surface, #1e1e1e);
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.2));
  border-radius: var(--usx-radius-md, 8px);
  color: var(--usx-color-on-surface, #fff);
  font-family: inherit;
  font-size: 1.05rem;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 150ms ease;
}

.story-textarea:focus {
  outline: none;
  border-color: var(--usx-color-primary, #646cff);
}

.story-input-hint {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-muted, #777);
}

.kbd-key {
  padding: 2px 6px;
  border: 1px solid var(--usx-color-border, rgba(255, 255, 255, 0.2));
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.05);
  font-size: 0.7rem;
  font-family: var(--usx-font-family-mono, monospace);
}

/* Controls Bar */
.story-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.story-nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: var(--usx-radius-md, 8px);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 180ms ease;
}

.story-nav-btn--primary {
  background: var(--usx-color-primary, #646cff);
  color: #ffffff;
}

.story-nav-btn--primary:hover:not(:disabled) {
  background: var(--usx-color-primary-hover, #535bf2);
}

.story-nav-btn--primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.story-nav-btn--secondary {
  background: transparent;
  border-color: var(--usx-color-border, rgba(255, 255, 255, 0.2));
  color: var(--usx-color-on-surface, #fff);
}

.story-nav-btn--secondary:hover {
  background: var(--usx-color-surface-hover, rgba(255, 255, 255, 0.06));
}

.story-btn-hint {
  font-size: 0.75rem;
  opacity: 0.75;
  margin-left: 0.25rem;
}

/* Transitions */
.story-slide-enter-active,
.story-slide-leave-active {
  transition: all 250ms ease;
}

.story-slide-enter-from {
  opacity: 0;
  transform: translateY(16px);
}

.story-slide-leave-to {
  opacity: 0;
  transform: translateY(-16px);
}
</style>
