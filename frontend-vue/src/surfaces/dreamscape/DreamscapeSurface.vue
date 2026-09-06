<template>
  <div class="surface dreamscape-surface">
    <div class="surface__content">
      <!-- Header -->
      <section class="surface__panel dreamscape-header">
        <div class="dreamscape-header__row">
          <div class="dreamscape-title-wrap">
            <UIcon name="psychology" class="dreamscape-title-icon" />
            <div>
              <h1 class="surface__panel-title">Dreamscape</h1>
              <p class="surface__panel-description">
                Dreambeans daily reflection, Chronos circadian briefing, and mission scaffolding.
              </p>
            </div>
          </div>
          <div class="dreamscape-nav-pills">
            <button
              type="button"
              class="dreamscape-nav-pill"
              :class="{ 'dreamscape-nav-pill--active': activeTab === 'beans' }"
              @click="activeTab = 'beans'"
            >
              <UIcon name="local_cafe" /> Dreambeans
            </button>
            <button
              type="button"
              class="dreamscape-nav-pill"
              :class="{ 'dreamscape-nav-pill--active': activeTab === 'briefing' }"
              @click="activeTab = 'briefing'"
            >
              <UIcon name="wb_sunny" /> Chronos Briefing
            </button>
            <button
              type="button"
              class="dreamscape-nav-pill"
              :class="{ 'dreamscape-nav-pill--active': activeTab === 'missions' }"
              @click="activeTab = 'missions'"
            >
              <UIcon name="flag" /> Missions
            </button>
          </div>
        </div>
      </section>

      <!-- Feedback notice -->
      <div v-if="noticeMessage" class="dreamscape-notice" :class="`dreamscape-notice--${noticeType}`">
        <span>{{ noticeMessage }}</span>
        <button class="dreamscape-notice-close" @click="noticeMessage = ''">&times;</button>
      </div>

      <!-- Tab 1: Dreambeans Daily Capture -->
      <div v-if="activeTab === 'beans'" class="dreamscape-tab-body">
        <div class="dreamscape-grid">
          <!-- Capture Form -->
          <div class="dreamscape-card dreamscape-capture-card">
            <div class="dreamscape-card__header">
              <div class="dreamscape-card__title">
                <UIcon name="edit_note" />
                <h3>Today's Daily Bean</h3>
              </div>
              <span class="dreamscape-date-badge">{{ currentDateFormatted }}</span>
            </div>

            <div class="dreamscape-form">
              <!-- Energy Rating -->
              <div class="dreamscape-field">
                <label class="dreamscape-label">Energy Level: <strong>{{ beanForm.energy }} / 5</strong></label>
                <div class="dreamscape-rating-pills">
                  <button
                    v-for="lvl in 5"
                    :key="lvl"
                    type="button"
                    class="dreamscape-rating-pill"
                    :class="{ 'dreamscape-rating-pill--active': beanForm.energy === lvl }"
                    @click="beanForm.energy = lvl"
                  >
                    <UIcon :name="lvl >= 4 ? 'battery_charging_full' : lvl >= 3 ? 'battery_5_bar' : 'battery_2_bar'" />
                    <span>{{ lvl }}</span>
                  </button>
                </div>
              </div>

              <!-- Focus Rating -->
              <div class="dreamscape-field">
                <label class="dreamscape-label">Cognitive Focus: <strong>{{ beanForm.focus }} / 5</strong></label>
                <div class="dreamscape-rating-pills">
                  <button
                    v-for="lvl in 5"
                    :key="lvl"
                    type="button"
                    class="dreamscape-rating-pill"
                    :class="{ 'dreamscape-rating-pill--active': beanForm.focus === lvl }"
                    @click="beanForm.focus = lvl"
                  >
                    <UIcon :name="lvl >= 4 ? 'center_focus_strong' : 'filter_center_focus'" />
                    <span>{{ lvl }}</span>
                  </button>
                </div>
              </div>

              <!-- Daily Intent -->
              <div class="dreamscape-field">
                <label class="dreamscape-label">Primary Intent</label>
                <input
                  v-model="beanForm.intent"
                  type="text"
                  class="dreamscape-input"
                  placeholder="What is the single most important outcome for today?"
                />
              </div>

              <!-- Friction Log -->
              <div class="dreamscape-field">
                <label class="dreamscape-label">Friction &amp; Blockers</label>
                <input
                  v-model="beanForm.friction"
                  type="text"
                  class="dreamscape-input"
                  placeholder="What slowed you down, felt heavy, or created drag?"
                />
              </div>

              <!-- Reflections / Wins -->
              <div class="dreamscape-field">
                <label class="dreamscape-label">Wins &amp; Reflections</label>
                <textarea
                  v-model="beanForm.reflections"
                  rows="3"
                  class="dreamscape-textarea"
                  placeholder="Notes, victories, or unexpected discoveries..."
                ></textarea>
              </div>

              <div class="dreamscape-actions">
                <UButton
                  variant="primary"
                  icon="save"
                  :disabled="savingBean"
                  @click="handleCaptureBean"
                >
                  {{ savingBean ? "Recording…" : "Record Daily Bean" }}
                </UButton>
              </div>
            </div>
          </div>

          <!-- Bean History / Today's State -->
          <div class="dreamscape-card dreamscape-history-card">
            <div class="dreamscape-card__header">
              <div class="dreamscape-card__title">
                <UIcon name="history" />
                <h3>Recorded Bean</h3>
              </div>
            </div>

            <div v-if="!savedBean" class="dreamscape-empty-state">
              <UIcon name="local_cafe" :size="48" />
              <p>No bean recorded for today yet. Fill in your ratings on the left to capture your rhythm.</p>
            </div>

            <div v-else class="dreamscape-bean-summary">
              <div class="dreamscape-metric-row">
                <div class="dreamscape-metric">
                  <span class="dreamscape-metric__label">Energy</span>
                  <span class="dreamscape-metric__value">{{ savedBean.energy || beanForm.energy }}/5</span>
                </div>
                <div class="dreamscape-metric">
                  <span class="dreamscape-metric__label">Focus</span>
                  <span class="dreamscape-metric__value">{{ savedBean.focus || beanForm.focus }}/5</span>
                </div>
                <div class="dreamscape-metric">
                  <span class="dreamscape-metric__label">Status</span>
                  <UBadge type="success" size="sm">Recorded</UBadge>
                </div>
              </div>

              <div v-if="savedBean.intent || beanForm.intent" class="dreamscape-summary-item">
                <strong>Intent:</strong>
                <p>{{ savedBean.intent || beanForm.intent }}</p>
              </div>

              <div v-if="savedBean.friction || beanForm.friction" class="dreamscape-summary-item">
                <strong>Friction:</strong>
                <p>{{ savedBean.friction || beanForm.friction }}</p>
              </div>

              <div v-if="savedBean.reflections || beanForm.reflections" class="dreamscape-summary-item">
                <strong>Reflections:</strong>
                <p>{{ savedBean.reflections || beanForm.reflections }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 2: Chronos Briefing -->
      <div v-else-if="activeTab === 'briefing'" class="dreamscape-tab-body">
        <div class="dreamscape-card dreamscape-briefing-card">
          <div class="dreamscape-card__header">
            <div class="dreamscape-card__title">
              <UIcon name="wb_sunny" />
              <h3>Chronos Morning Briefing</h3>
            </div>
            <UButton variant="secondary" size="sm" icon="refresh" :disabled="loadingBriefing" @click="fetchBriefing">
              Refresh
            </UButton>
          </div>

          <div v-if="loadingBriefing" class="dreamscape-empty-state">
            <UIcon name="sync" class="spinning" :size="48" />
            <p>Synthesizing circadian rhythm and priority briefing…</p>
          </div>

          <div v-else-if="briefing" class="dreamscape-briefing-content">
            <div class="dreamscape-briefing-grid">
              <div class="dreamscape-briefing-col">
                <div class="dreamscape-briefing-col__head">
                  <UIcon name="today" />
                  <h4>Today's Focus</h4>
                </div>
                <ul>
                  <li v-for="(item, idx) in briefing.today || defaultTodayItems" :key="idx">
                    {{ item }}
                  </li>
                </ul>
              </div>

              <div class="dreamscape-briefing-col">
                <div class="dreamscape-briefing-col__head">
                  <UIcon name="forward" />
                  <h4>Next Horizon</h4>
                </div>
                <ul>
                  <li v-for="(item, idx) in briefing.next || defaultNextItems" :key="idx">
                    {{ item }}
                  </li>
                </ul>
              </div>

              <div class="dreamscape-briefing-col">
                <div class="dreamscape-briefing-col__head">
                  <UIcon name="visibility" />
                  <h4>Watchpoints</h4>
                </div>
                <ul>
                  <li v-for="(item, idx) in briefing.watch || defaultWatchItems" :key="idx">
                    {{ item }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 3: Missions Scaffolding -->
      <div v-else-if="activeTab === 'missions'" class="dreamscape-tab-body">
        <div class="dreamscape-card dreamscape-mission-card">
          <div class="dreamscape-card__header">
            <div class="dreamscape-card__title">
              <UIcon name="rocket_launch" />
              <h3>Launch Mission Scaffolding</h3>
            </div>
          </div>

          <div class="dreamscape-form dreamscape-form--horizontal">
            <div class="dreamscape-field">
              <label class="dreamscape-label">Domain Interest</label>
              <input
                v-model="missionInterest"
                type="text"
                class="dreamscape-input"
                placeholder="e.g. Distributed Knowledge Systems, AI Sandbox"
              />
            </div>
            <div class="dreamscape-field">
              <label class="dreamscape-label">Mission Intent</label>
              <input
                v-model="missionIntent"
                type="text"
                class="dreamscape-input"
                placeholder="e.g. Consolidate offline vault mirroring and build telemetry"
              />
            </div>
            <div class="dreamscape-actions">
              <UButton
                variant="primary"
                icon="rocket_launch"
                :disabled="launchingMission || !missionInterest.trim() || !missionIntent.trim()"
                @click="handleLaunchMission"
              >
                {{ launchingMission ? "Scaffolding…" : "Scaffold Mission" }}
              </UButton>
            </div>
          </div>

          <!-- Active Missions List -->
          <div class="dreamscape-missions-list usx-mt-lg">
            <h4>Scaffolded Missions ({{ missions.length }})</h4>
            <div v-if="missions.length === 0" class="dreamscape-empty-state">
              <UIcon name="flag" :size="36" />
              <p>No active missions yet. Define an interest and intent above to scaffold a mission.</p>
            </div>
            <div v-else class="dreamscape-missions-grid">
              <div v-for="(m, idx) in missions" :key="idx" class="dreamscape-mission-item">
                <div class="dreamscape-mission-item__header">
                  <span class="dreamscape-mission-badge">{{ m.interest }}</span>
                  <UBadge type="info" size="sm">{{ m.priority || "High" }}</UBadge>
                </div>
                <p class="dreamscape-mission-intent">{{ m.intent }}</p>
                <div class="dreamscape-mission-footer">
                  <span>Horizon: {{ m.horizon || "Sprint 4" }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import UIcon from "../../skills/atoms/UIcon.vue"
import UButton from "../../skills/atoms/UButton.vue"
import UBadge from "../../skills/atoms/UBadge.vue"
import {
  captureDreamBean,
  getDreamBean,
  getDailyBriefing,
  createMission,
  type DailyBriefingResult,
  type MissionResult,
} from "../browserui/ApiBridge"

const activeTab = ref<"beans" | "briefing" | "missions">("beans")
const noticeMessage = ref("")
const noticeType = ref<"success" | "error" | "info">("info")

const savingBean = ref(false)
const savedBean = ref<Record<string, any> | null>(null)

const beanForm = ref({
  energy: 4,
  focus: 4,
  intent: "",
  friction: "",
  reflections: "",
})

const currentDateFormatted = computed(() => {
  return new Date().toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  })
})

const loadingBriefing = ref(false)
const briefing = ref<DailyBriefingResult["briefing"] | null>(null)

const defaultTodayItems = [
  "Execute Sprint 4 UI surfaces alignment",
  "Validate Zen Ecosystem Contract boundaries",
  "Review vault mirror revisions and local notebooks",
]

const defaultNextItems = [
  "Sprint 4 packaging & tag verification",
  "Finalize Host PIM bridge integration testing",
]

const defaultWatchItems = [
  "Maintain strict Dev Mode isolation",
  "Ensure zero unhandled errors on offline API fallbacks",
]

const missionInterest = ref("")
const missionIntent = ref("")
const launchingMission = ref(false)
const missions = ref<Array<{ interest: string; intent: string; horizon?: string; priority?: string }>>([
  {
    interest: "Google AI Studio Integration",
    intent: "Unify Gemini 2.0 Code Execution and Grounded Search across uCore.",
    horizon: "Sprint 4",
    priority: "Immediate",
  },
  {
    interest: "Host-Native Zen PIM",
    intent: "Leverage macOS Apple Events for Safari, Notes, and Reminders exchange.",
    horizon: "Sprint 4",
    priority: "High",
  },
])

onMounted(() => {
  void fetchTodayBean()
  void fetchBriefing()
})

async function fetchTodayBean() {
  try {
    const res = await getDreamBean()
    if (res && res.status === "success" && res.bean) {
      savedBean.value = res.bean
      if (res.bean.energy) beanForm.value.energy = res.bean.energy
      if (res.bean.focus) beanForm.value.focus = res.bean.focus
      if (res.bean.intent) beanForm.value.intent = res.bean.intent
      if (res.bean.friction) beanForm.value.friction = res.bean.friction
      if (res.bean.reflections) beanForm.value.reflections = res.bean.reflections
    }
  } catch {
    // offline or not yet recorded
  }
}

async function handleCaptureBean() {
  savingBean.value = true
  try {
    const res = await captureDreamBean({
      energy: beanForm.value.energy,
      focus: beanForm.value.focus,
      intent: beanForm.value.intent,
      friction: beanForm.value.friction,
      reflections: beanForm.value.reflections,
    })
    savedBean.value = res.bean || { ...beanForm.value }
    noticeType.value = "success"
    noticeMessage.value = "Daily Bean recorded successfully!"
  } catch (err: any) {
    noticeType.value = "error"
    noticeMessage.value = `Failed to capture bean: ${err?.message || err}`
  } finally {
    savingBean.value = false
  }
}

async function fetchBriefing() {
  loadingBriefing.value = true
  try {
    const res = await getDailyBriefing()
    if (res && res.briefing) {
      briefing.value = res.briefing
    }
  } catch {
    // fallback to defaults
    briefing.value = {
      today: defaultTodayItems,
      next: defaultNextItems,
      watch: defaultWatchItems,
    }
  } finally {
    loadingBriefing.value = false
  }
}

async function handleLaunchMission() {
  if (!missionInterest.value.trim() || !missionIntent.value.trim()) return
  launchingMission.value = true
  try {
    const res = await createMission(missionInterest.value.trim(), missionIntent.value.trim())
    missions.value.unshift({
      interest: missionInterest.value.trim(),
      intent: missionIntent.value.trim(),
      horizon: res.mission?.horizon || "Sprint 4",
      priority: res.mission?.priority || "Normal",
    })
    missionInterest.value = ""
    missionIntent.value = ""
    noticeType.value = "success"
    noticeMessage.value = "Mission scaffolded successfully!"
  } catch (err: any) {
    noticeType.value = "error"
    noticeMessage.value = `Mission launch failed: ${err?.message || err}`
  } finally {
    launchingMission.value = false
  }
}
</script>

<style scoped>
.dreamscape-surface {
  padding: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  overflow-y: auto;
}

.dreamscape-header {
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
}

.dreamscape-header__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--usx-spacing-md);
}

.dreamscape-title-wrap {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
}

.dreamscape-title-icon {
  font-size: 36px;
  color: var(--usx-color-primary);
}

.dreamscape-nav-pills {
  display: inline-flex;
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  padding: 3px;
  gap: 2px;
}

.dreamscape-nav-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-radius: var(--usx-radius-full);
  border: 0;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  cursor: pointer;
  transition: all 0.15s ease;
}

.dreamscape-nav-pill:hover {
  color: var(--usx-color-on-surface);
}

.dreamscape-nav-pill--active {
  background: var(--usx-color-surface);
  color: var(--usx-color-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.dreamscape-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
}

.dreamscape-notice--success {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid #22c55e;
}

.dreamscape-notice--error {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid #ef4444;
}

.dreamscape-notice-close {
  border: 0;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
}

.dreamscape-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--usx-spacing-md);
}

@media (max-width: 800px) {
  .dreamscape-grid {
    grid-template-columns: 1fr;
  }
}

.dreamscape-card {
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
}

.dreamscape-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--usx-spacing-md);
  padding-bottom: var(--usx-spacing-xs);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.dreamscape-card__title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  color: var(--usx-color-primary);
}

.dreamscape-card__title h3 {
  margin: 0;
  font-size: var(--usx-font-size-base);
}

.dreamscape-date-badge {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.dreamscape-form {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.dreamscape-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dreamscape-label {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  color: var(--usx-color-on-surface);
}

.dreamscape-rating-pills {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.dreamscape-rating-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  border: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-font-size-xs);
  transition: all 0.15s ease;
}

.dreamscape-rating-pill:hover {
  color: var(--usx-color-on-surface);
  border-color: var(--usx-color-primary);
}

.dreamscape-rating-pill--active {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

.dreamscape-input,
.dreamscape-textarea {
  width: 100%;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: inherit;
}

.dreamscape-input:focus,
.dreamscape-textarea:focus {
  outline: none;
  border-color: var(--usx-color-primary);
}

.dreamscape-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--usx-spacing-xl);
  color: var(--usx-color-on-surface-muted);
  gap: var(--usx-spacing-sm);
}

.dreamscape-metric-row {
  display: flex;
  gap: var(--usx-spacing-lg);
  margin-bottom: var(--usx-spacing-md);
  padding-bottom: var(--usx-spacing-sm);
  border-bottom: 1px dashed var(--usx-color-border);
}

.dreamscape-metric {
  display: flex;
  flex-direction: column;
}

.dreamscape-metric__label {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.dreamscape-metric__value {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-bold);
  color: var(--usx-color-primary);
}

.dreamscape-summary-item {
  margin-bottom: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
}

.dreamscape-summary-item p {
  margin: 2px 0 0;
  color: var(--usx-color-on-surface);
}

.dreamscape-briefing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--usx-spacing-md);
}

.dreamscape-briefing-col {
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-sm);
}

.dreamscape-briefing-col__head {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  color: var(--usx-color-primary);
  margin-bottom: var(--usx-spacing-xs);
}

.dreamscape-briefing-col__head h4 {
  margin: 0;
  font-size: var(--usx-font-size-sm);
}

.dreamscape-briefing-col ul {
  margin: 0;
  padding-left: var(--usx-spacing-md);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface);
  line-height: 1.6;
}

.dreamscape-missions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-sm);
}

.dreamscape-mission-item {
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
}

.dreamscape-mission-item__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.dreamscape-mission-badge {
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-primary);
}

.dreamscape-mission-intent {
  font-size: var(--usx-font-size-sm);
  margin: 4px 0;
  color: var(--usx-color-on-surface);
}

.dreamscape-mission-footer {
  font-size: 10px;
  color: var(--usx-color-on-surface-muted);
}
</style>
