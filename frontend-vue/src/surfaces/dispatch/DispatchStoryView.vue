<template>
  <div class="dispatch-viewport" :class="[`dispatch-viewport--${activeMode}`, `dispatch-viewport--${aspectRatio}`]" ref="viewportEl" tabindex="0" @keydown="handleGlobalKeydown">
    <!-- Ephemeral Tombstone State -->
    <div v-if="status === 'burned' || status === 'expired'" class="dispatch-tombstone">
      <div class="dispatch-tombstone__box">
        <div class="dispatch-tombstone__icon">✦</div>
        <h2 class="dispatch-tombstone__title">Ether Dissolution</h2>
        <p class="dispatch-tombstone__desc">{{ tombstoneMessage }}</p>
        <router-link to="/" class="dispatch-tombstone__link">Return to Sovereign Home</router-link>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="dispatch-loading">
      <div class="dispatch-loading__pulse">Connecting to sovereign dispatch...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="dispatch-error">
      <div class="dispatch-error__box">
        <h3>Dispatch Unavailable</h3>
        <p>{{ error }}</p>
        <router-link to="/" class="dispatch-tombstone__link">Return Home</router-link>
      </div>
    </div>

    <!-- Active Tri-Mode Story Container -->
    <div v-else class="dispatch-canvas-frame" :class="[`aspect-${aspectRatio}`]">
      <!-- Top Control Bar: Mode Selector & Viewport Presets -->
      <header class="dispatch-bar">
        <div class="dispatch-bar__left">
          <span class="dispatch-bar__badge">uDOS DISPATCH</span>
          <span class="dispatch-bar__title">{{ manifest?.title }}</span>
        </div>

        <div class="dispatch-bar__center">
          <div class="dispatch-mode-toggle" role="tablist">
            <button
              class="dispatch-mode-btn"
              :class="{ active: activeMode === 'card' }"
              @click="activeMode = 'card'"
              title="Zen Card Mode (1)"
            >
              [Card]
            </button>
            <button
              class="dispatch-mode-btn"
              :class="{ active: activeMode === 'deck' }"
              @click="activeMode = 'deck'"
              title="10-Foot TV Deck Mode (2)"
            >
              [Deck]
            </button>
            <button
              class="dispatch-mode-btn"
              :class="{ active: activeMode === 'prose' }"
              @click="activeMode = 'prose'"
              title="Prose Reader Mode (3)"
            >
              [Prose]
            </button>
          </div>
        </div>

        <div class="dispatch-bar__right">
          <button class="dispatch-btn-sm" @click="toggleAspect" :title="`Switch Aspect (Current: ${aspectRatio})`">
            {{ aspectRatio }}
          </button>
          <button class="dispatch-btn-sm" @click="toggleFullscreen" title="Fullscreen (F)">
            {{ isFullscreen ? 'Exit ⛶' : 'Fullscreen ⛶' }}
          </button>
        </div>
      </header>

      <!-- VIEW 1: ZEN CARD MODE (Typeform-style single focused quantum) -->
      <section v-if="activeMode === 'card'" class="dispatch-stage dispatch-stage--card">
        <div class="dispatch-progress">
          <div class="dispatch-progress__bar" :style="{ width: `${cardProgressPct}%` }"></div>
        </div>

        <div class="dispatch-card-container">
          <transition name="quantum-fade" mode="out-in">
            <!-- Cover / Lead Card -->
            <div v-if="currentCardIndex === 0" :key="'lead'" class="dispatch-card dispatch-card--lead">
              <div v-if="manifest?.hero_asset" class="dispatch-card__hero">
                <img :src="manifest.hero_asset" alt="Hero Animation" class="dispatch-bob-img" />
              </div>
              <h1 class="dispatch-card__heading">{{ manifest?.title }}</h1>
              <p v-if="manifest?.lead_text" class="dispatch-card__lead">{{ manifest.lead_text }}</p>
              <div class="dispatch-card__body" v-html="renderedCards[0]"></div>
              <button class="dispatch-btn-primary dispatch-btn-primary--lg" @click="nextCard">
                Begin Dispatch &rarr;
              </button>
            </div>

            <!-- Response Confirmation Card -->
            <div v-else-if="currentCardIndex >= renderedCards.length" :key="'done'" class="dispatch-card dispatch-card--done">
              <div class="dispatch-card__hero-icon">✦</div>
              <h2 class="dispatch-card__heading">Response Dispatched</h2>
              <p class="dispatch-card__lead">Your responses have been recorded peacefully in the host vault.</p>
              <div v-if="manifest?.burn_after_read" class="dispatch-card__burn-note">
                (This one-time dispatch will dissolve upon closing this window.)
              </div>
              <button class="dispatch-btn-secondary" @click="currentCardIndex = 0">Review Cards</button>
            </div>

            <!-- Question / Content Card -->
            <div v-else :key="currentCardIndex" class="dispatch-card dispatch-card--question">
              <div class="dispatch-card__step-label">Step {{ currentCardIndex }} of {{ renderedCards.length - 1 }}</div>
              <div class="dispatch-card__body" v-html="renderedCards[currentCardIndex]"></div>

              <!-- Interactive Form Controls for current step -->
              <div class="dispatch-form-group" v-if="getCurrentQuestion()">
                <label class="dispatch-form-label">{{ getCurrentQuestion()?.label }}</label>

                <!-- Multiple Choice -->
                <div v-if="getCurrentQuestion()?.type === 'choice'" class="dispatch-options-list">
                  <button
                    v-for="(opt, idx) in getCurrentQuestion()?.options"
                    :key="idx"
                    class="dispatch-option-btn"
                    :class="{ selected: formAnswers[getCurrentQuestion()!.id] === opt }"
                    @click="selectOption(getCurrentQuestion()!.id, opt)"
                  >
                    <span class="dispatch-option-key">{{ idx + 1 }}</span>
                    <span class="dispatch-option-text">{{ opt }}</span>
                  </button>
                </div>

                <!-- Text Input -->
                <div v-else-if="getCurrentQuestion()?.type === 'text'" class="dispatch-input-row">
                  <input
                    type="text"
                    class="dispatch-input"
                    v-model="formAnswers[getCurrentQuestion()!.id]"
                    placeholder="Type your response..."
                    @keydown.enter="nextCard"
                    autofocus
                  />
                  <button class="dispatch-btn-primary" @click="nextCard">OK &check;</button>
                </div>

                <!-- Number Input -->
                <div v-else-if="getCurrentQuestion()?.type === 'number'" class="dispatch-input-row">
                  <input
                    type="number"
                    class="dispatch-input"
                    v-model="formAnswers[getCurrentQuestion()!.id]"
                    placeholder="Count"
                    @keydown.enter="nextCard"
                    autofocus
                  />
                  <button class="dispatch-btn-primary" @click="nextCard">OK &check;</button>
                </div>
              </div>

              <!-- Card Navigation Bar -->
              <div class="dispatch-card__nav">
                <button class="dispatch-btn-secondary" :disabled="currentCardIndex === 0" @click="prevCard">
                  &larr; Previous
                </button>
                <button
                  v-if="currentCardIndex === renderedCards.length - 1"
                  class="dispatch-btn-primary"
                  :disabled="submitting"
                  @click="submitAllAnswers"
                >
                  {{ submitting ? 'Submitting...' : 'Complete & Send &rarr;' }}
                </button>
                <button v-else class="dispatch-btn-primary" @click="nextCard">
                  Next &rarr;
                </button>
              </div>
            </div>
          </transition>
        </div>
      </section>

      <!-- VIEW 2: 10-FOOT DECK MODE (Marp-style presentation for TV / console) -->
      <section v-else-if="activeMode === 'deck'" class="dispatch-stage dispatch-stage--deck">
        <div class="dispatch-deck-slide">
          <transition name="deck-slide" mode="out-in">
            <div :key="currentCardIndex" class="dispatch-deck-content">
              <div v-if="manifest?.hero_asset && currentCardIndex === 0" class="dispatch-deck__hero">
                <img :src="manifest.hero_asset" alt="Hero Animation" class="dispatch-bob-img--lg" />
              </div>
              <div class="dispatch-deck-body" v-html="renderedCards[currentCardIndex] || renderedCards[0]"></div>
            </div>
          </transition>
        </div>

        <footer class="dispatch-deck-footer">
          <button class="dispatch-deck-btn" :disabled="currentCardIndex === 0" @click="prevCard">&larr; PREV</button>
          <span class="dispatch-deck-counter">{{ currentCardIndex + 1 }} / {{ renderedCards.length }}</span>
          <button class="dispatch-deck-btn" :disabled="currentCardIndex >= renderedCards.length - 1" @click="nextCard">NEXT &rarr;</button>
        </footer>
      </section>

      <!-- VIEW 3: PROSE READER MODE (Standard 70ch reading column) -->
      <section v-else-if="activeMode === 'prose'" class="dispatch-stage dispatch-stage--prose">
        <div class="dispatch-prose-container">
          <div v-if="manifest?.hero_asset" class="dispatch-prose-hero">
            <img :src="manifest.hero_asset" alt="Hero Animation" class="dispatch-bob-img" />
          </div>
          <header class="dispatch-prose-header">
            <h1 class="dispatch-prose-title">{{ manifest?.title }}</h1>
            <p v-if="manifest?.lead_text" class="dispatch-prose-lead">{{ manifest.lead_text }}</p>
          </header>

          <article class="dispatch-prose-body" v-html="fullRenderedProse"></article>

          <div class="dispatch-prose-rsvp" v-if="questions.length > 0">
            <h3 class="dispatch-prose-rsvp-title">Respond to this Dispatch</h3>
            <div v-for="q in questions" :key="q.id" class="dispatch-prose-q">
              <label class="dispatch-form-label">{{ q.label }}</label>
              <div v-if="q.type === 'choice'" class="dispatch-options-row">
                <button
                  v-for="opt in q.options"
                  :key="opt"
                  class="dispatch-option-btn dispatch-option-btn--inline"
                  :class="{ selected: formAnswers[q.id] === opt }"
                  @click="formAnswers[q.id] = opt"
                >
                  {{ opt }}
                </button>
              </div>
              <input v-else type="text" class="dispatch-input" v-model="formAnswers[q.id]" placeholder="Your answer" />
            </div>
            <button class="dispatch-btn-primary dispatch-btn-primary--lg" :disabled="submitting" @click="submitAllAnswers">
              {{ submitting ? 'Submitting...' : 'Submit Responses' }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { renderProseFast } from "../../utils/markdownRenderer";

interface QuestionDef {
  id: string;
  label: string;
  type: "choice" | "text" | "number";
  options?: string[];
}

const route = useRoute();
const viewportEl = ref<HTMLElement | null>(null);

const token = computed(() => String(route.params.token || ""));
const loading = ref(true);
const submitting = ref(false);
const error = ref("");
const status = ref<"active" | "burned" | "expired" | "not_found">("active");
const tombstoneMessage = ref("");

const manifest = ref<any>(null);
const rawMarkdown = ref("");
const activeMode = ref<"card" | "deck" | "prose">("card");
const aspectRatio = ref<"4:3" | "16:9">("16:9");
const isFullscreen = ref(false);
const currentCardIndex = ref(0);
const formAnswers = ref<Record<string, any>>({});
const questions = ref<QuestionDef[]>([]);

// Split markdown into discrete cards by "---"
const rawCards = computed(() => {
  if (!rawMarkdown.value) return [];
  return rawMarkdown.value
    .split(/\n---\n/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);
});

// Render cards HTML
const renderedCards = computed(() => {
  return rawCards.value.map((card) => renderProseFast(card));
});

// Full prose rendering for Prose mode
const fullRenderedProse = computed(() => {
  return renderProseFast(rawMarkdown.value);
});

const cardProgressPct = computed(() => {
  if (renderedCards.value.length === 0) return 0;
  return Math.min(100, Math.round(((currentCardIndex.value + 1) / renderedCards.value.length) * 100));
});

// Parse questions from markdown cards
function parseQuestions() {
  const extracted: QuestionDef[] = [];
  rawCards.value.forEach((card, idx) => {
    const lines = card.split("\n");
    for (const line of lines) {
      const trimmed = line.trim();
      // Choice question: ? [ ] Option A / Option B
      if (trimmed.startsWith("? [ ]")) {
        const parts = trimmed.replace("? [ ]", "").split("/").map((s) => s.trim());
        extracted.push({
          id: `q_${idx}`,
          label: parts[0] || "Select an option:",
          type: "choice",
          options: parts.length > 1 ? parts.slice(1) : ["Yes", "No", "Maybe"],
        });
      }
      // Text question: ? (Label): [text]
      else if (trimmed.startsWith("? (") && trimmed.includes("): [text]")) {
        const label = trimmed.substring(3, trimmed.indexOf("): [text]"));
        extracted.push({
          id: `q_${idx}`,
          label,
          type: "text",
        });
      }
      // Number question: ? (Label): [number]
      else if (trimmed.startsWith("? (") && trimmed.includes("): [number]")) {
        const label = trimmed.substring(3, trimmed.indexOf("): [number]"));
        extracted.push({
          id: `q_${idx}`,
          label,
          type: "number",
        });
      }
    }
  });
  questions.value = extracted;
}

function getCurrentQuestion(): QuestionDef | undefined {
  return questions.value.find((q) => q.id === `q_${currentCardIndex.value}`);
}

function selectOption(qid: string, val: string) {
  formAnswers.value[qid] = val;
  // Smooth auto-advance on selection
  setTimeout(() => {
    nextCard();
  }, 220);
}

function nextCard() {
  if (currentCardIndex.value < renderedCards.value.length) {
    currentCardIndex.value++;
  }
}

function prevCard() {
  if (currentCardIndex.value > 0) {
    currentCardIndex.value--;
  }
}

function toggleAspect() {
  aspectRatio.value = aspectRatio.value === "16:9" ? "4:3" : "16:9";
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    viewportEl.value?.requestFullscreen().catch(() => {});
    isFullscreen.value = true;
  } else {
    document.exitFullscreen().catch(() => {});
    isFullscreen.value = false;
  }
}

function handleGlobalKeydown(e: KeyboardEvent) {
  if (e.key === "f" || e.key === "F") {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
    toggleFullscreen();
  } else if (e.key === "ArrowRight" || e.key === "j" || e.key === "J") {
    if (e.target instanceof HTMLInputElement) return;
    nextCard();
  } else if (e.key === "ArrowLeft" || e.key === "k" || e.key === "K") {
    if (e.target instanceof HTMLInputElement) return;
    prevCard();
  } else if (e.key === "1") {
    activeMode.value = "card";
  } else if (e.key === "2") {
    activeMode.value = "deck";
  } else if (e.key === "3") {
    activeMode.value = "prose";
  }
}

async function fetchDispatch() {
  loading.value = true;
  error.value = "";
  try {
    const res = await fetch(`/api/dispatch/token/${token.value}`);
    const data = await res.json();
    if (res.status === 404 || data.status === "not_found") {
      error.value = "Dispatch not found or revoked.";
      status.value = "not_found";
    } else if (data.status === "burned" || data.status === "expired") {
      status.value = data.status;
      tombstoneMessage.value = data.tombstone || "This dispatch has dissolved into the ether.";
    } else {
      status.value = "active";
      manifest.value = data.dispatch;
      rawMarkdown.value = data.story_markdown || "";
      if (manifest.value.mode_default) {
        activeMode.value = manifest.value.mode_default;
      }
      parseQuestions();
    }
  } catch (err: any) {
    error.value = err.message || "Failed to load dispatch.";
  } finally {
    loading.value = false;
  }
}

async function submitAllAnswers() {
  submitting.value = true;
  try {
    const res = await fetch(`/api/dispatch/rsvp/${token.value}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formAnswers.value),
    });
    const result = await res.json();
    if (result.status === "success") {
      currentCardIndex.value = renderedCards.value.length + 1; // Show done card
      if (result.burned) {
        manifest.value.burn_after_read = true;
      }
    } else {
      alert("Submission error: " + (result.message || "Unknown"));
    }
  } catch (err: any) {
    alert("Network error: " + err.message);
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  fetchDispatch();
  viewportEl.value?.focus();
});
</script>

<style scoped>
.dispatch-viewport {
  position: fixed;
  inset: 0;
  background-color: #0d1117;
  color: #e6edf3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  overflow: hidden;
  outline: none;
}

/* Calibrated Canvas Frame with Containment */
.dispatch-canvas-frame {
  display: flex;
  flex-direction: column;
  background-color: #161b22;
  border: 1px solid #30363d;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.aspect-16\:9 {
  width: min(100vw, 1280px);
  height: min(100vh, 720px);
  aspect-ratio: 16 / 9;
}

.aspect-4\:3 {
  width: min(100vw, 960px);
  height: min(100vh, 720px);
  aspect-ratio: 4 / 3;
}

/* Top Bar */
.dispatch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background-color: #0d1117;
  border-bottom: 1px solid #30363d;
  font-size: 13px;
  user-select: none;
}

.dispatch-bar__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dispatch-bar__badge {
  background-color: #21262d;
  color: #58a6ff;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 3px;
  letter-spacing: 0.05em;
}

.dispatch-bar__title {
  color: #8b949e;
  font-weight: 500;
}

.dispatch-mode-toggle {
  display: flex;
  gap: 2px;
  background-color: #21262d;
  padding: 2px;
  border-radius: 4px;
}

.dispatch-mode-btn {
  background: none;
  border: none;
  color: #8b949e;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 3px;
  cursor: pointer;
}

.dispatch-mode-btn.active {
  background-color: #58a6ff;
  color: #0d1117;
}

.dispatch-bar__right {
  display: flex;
  gap: 8px;
}

.dispatch-btn-sm {
  background-color: #21262d;
  border: 1px solid #30363d;
  color: #c9d1d9;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

/* Stage */
.dispatch-stage {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ZEN CARD MODE */
.dispatch-progress {
  height: 3px;
  background-color: #21262d;
  width: 100%;
}

.dispatch-progress__bar {
  height: 100%;
  background-color: #58a6ff;
  transition: width 0.3s ease;
}

.dispatch-card-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  overflow-y: auto;
}

.dispatch-card {
  max-width: 640px;
  width: 100%;
  text-align: left;
}

.dispatch-card--lead {
  text-align: center;
}

.dispatch-bob-img {
  width: 112px;
  height: 112px;
  border-radius: 6px;
  margin-bottom: 20px;
  image-rendering: pixelated;
}

.dispatch-card__heading {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #f0f6fc;
}

.dispatch-card__lead {
  font-size: 20px;
  color: #8b949e;
  margin-bottom: 24px;
  line-height: 1.5;
}

.dispatch-card__body {
  font-size: 18px;
  line-height: 1.6;
  color: #c9d1d9;
  margin-bottom: 24px;
}

.dispatch-card__step-label {
  font-size: 12px;
  color: #58a6ff;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.dispatch-options-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.dispatch-option-btn {
  display: flex;
  align-items: center;
  gap: 16px;
  background-color: #21262d;
  border: 1px solid #30363d;
  color: #e6edf3;
  padding: 14px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 17px;
  transition: all 0.15s ease;
  min-height: 52px;
}

.dispatch-option-btn:hover {
  background-color: #30363d;
  border-color: #58a6ff;
}

.dispatch-option-btn.selected {
  background-color: #1f6feb;
  border-color: #58a6ff;
  color: #ffffff;
}

.dispatch-option-key {
  font-weight: 700;
  background-color: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
}

.dispatch-input-row {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.dispatch-input {
  flex: 1;
  background-color: #0d1117;
  border: 1px solid #30363d;
  color: #e6edf3;
  font-size: 18px;
  padding: 12px 16px;
  border-radius: 6px;
  min-height: 50px;
}

.dispatch-input:focus {
  outline: none;
  border-color: #58a6ff;
}

.dispatch-btn-primary {
  background-color: #238636;
  border: none;
  color: #ffffff;
  font-weight: 600;
  font-size: 16px;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
}

.dispatch-btn-primary--lg {
  font-size: 18px;
  padding: 14px 32px;
}

.dispatch-btn-secondary {
  background-color: #21262d;
  border: 1px solid #30363d;
  color: #c9d1d9;
  font-size: 15px;
  padding: 12px 20px;
  border-radius: 6px;
  cursor: pointer;
}

.dispatch-card__nav {
  display: flex;
  justify-content: space-between;
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #21262d;
}

/* 10-FOOT DECK MODE */
.dispatch-stage--deck {
  padding: 48px;
  justify-content: space-between;
}

.dispatch-deck-slide {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dispatch-deck-content {
  text-align: center;
  max-width: 900px;
}

.dispatch-bob-img--lg {
  width: 160px;
  height: 160px;
  image-rendering: pixelated;
  margin-bottom: 24px;
}

.dispatch-deck-body :deep(h1) {
  font-size: 48px;
  font-weight: 800;
  color: #58a6ff;
  margin-bottom: 16px;
}

.dispatch-deck-body :deep(p) {
  font-size: 26px;
  line-height: 1.5;
  color: #e6edf3;
}

.dispatch-deck-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 24px;
  border-top: 1px solid #30363d;
}

.dispatch-deck-btn {
  background-color: #21262d;
  border: 1px solid #30363d;
  color: #f0f6fc;
  font-size: 20px;
  font-weight: 700;
  padding: 12px 28px;
  border-radius: 6px;
  cursor: pointer;
}

.dispatch-deck-counter {
  font-size: 20px;
  font-weight: 700;
  color: #8b949e;
}

/* PROSE READER MODE */
.dispatch-stage--prose {
  overflow-y: auto;
  padding: 40px 24px;
}

.dispatch-prose-container {
  max-width: 70ch;
  margin: 0 auto;
  font-family: Charter, "Bitstream Charter", "Sitka Text", Cambria, Georgia, serif;
}

.dispatch-prose-title {
  font-size: 34px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #f0f6fc;
}

.dispatch-prose-lead {
  font-size: 20px;
  color: #8b949e;
  line-height: 1.5;
  margin-bottom: 24px;
}

.dispatch-prose-body {
  font-size: 18px;
  line-height: 1.75;
  color: #e6edf3;
}

.dispatch-prose-rsvp {
  margin-top: 48px;
  padding: 24px;
  background-color: #21262d;
  border-radius: 8px;
  border: 1px solid #30363d;
  font-family: Inter, sans-serif;
}

/* EPHEMERAL TOMBSTONE */
.dispatch-tombstone {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
}

.dispatch-tombstone__box {
  text-align: center;
  max-width: 480px;
  padding: 48px;
  background-color: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
}

.dispatch-tombstone__icon {
  font-size: 40px;
  color: #58a6ff;
  margin-bottom: 16px;
}

.dispatch-tombstone__title {
  font-size: 24px;
  color: #f0f6fc;
  margin-bottom: 12px;
}

.dispatch-tombstone__desc {
  font-size: 16px;
  color: #8b949e;
  line-height: 1.6;
  margin-bottom: 24px;
}

.dispatch-tombstone__link {
  display: inline-block;
  color: #58a6ff;
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
}

.dispatch-tombstone__link:hover {
  text-decoration: underline;
}
</style>
