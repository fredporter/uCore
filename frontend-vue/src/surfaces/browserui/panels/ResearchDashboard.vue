/**
 * @component ResearchDashboard — Research queue, progress, and gaps.
 */
<template>
  <div class="rdash">
    <section class="rdash__hero surface__panel">
      <div class="rdash__hero-top">
        <h3 class="surface__panel-title">Research Control</h3>
        <div class="rdash__hero-badges">
          <span class="rdash__hero-badge">Queue Driven</span>
          <span class="rdash__hero-badge">Vault Gap Aware</span>
        </div>
      </div>
      <p class="surface__panel-description">
        Monitor live research jobs, launch new requests, and fill knowledge gaps.
      </p>
    </section>

    <div class="rdash__stats">
      <div class="rdash__stat">
        <span class="rdash__stat-value">{{ jobCount }}</span>
        <span class="rdash__stat-label">Total Jobs</span>
      </div>
      <div class="rdash__stat">
        <span class="rdash__stat-value rdash__stat-value--info">{{ runningCount }}</span>
        <span class="rdash__stat-label">Running</span>
      </div>
      <div class="rdash__stat">
        <span class="rdash__stat-value rdash__stat-value--success">{{ completedCount }}</span>
        <span class="rdash__stat-label">Completed</span>
      </div>
      <div class="rdash__stat">
        <span class="rdash__stat-value rdash__stat-value--warning">{{ gapCount }}</span>
        <span class="rdash__stat-label">Open Gaps</span>
      </div>
    </div>

    <div class="rdash__layout">
      <section class="rdash__section rdash__section--queue">
        <div class="rdash__section-head">
          <h3>Research Queue</h3>
          <span class="rdash__badge">{{ jobCount }}</span>
        </div>

        <div v-if="props.jobs.length === 0" class="rdash__empty">No active research jobs</div>

        <div v-else class="rdash__queue-list">
        <div
          v-for="j in props.jobs"
          :key="j.id"
          class="rdash__job"
          :class="{ 'rdash__job--selected': selectedJob?.id === j.id }"
          @click="selectedJob = selectedJob?.id === j.id ? null : j"
        >
          <div class="rdash__job-top">
            <div class="rdash__job-main">
              <UIcon :name="stateIcon(j.state)" class="rdash__job-icon" />
              <span class="rdash__job-url">{{ j.url }}</span>
            </div>
            <span class="rdash__job-state" :class="`rdash__job-state--${j.state}`">{{ stateLabel(j.state) }}</span>
          </div>
          <div class="rdash__job-bar">
            <div class="rdash__job-bar-fill" :style="{ width: j.progress + '%' }"></div>
          </div>
          <div class="rdash__job-meta">
            <span>Binder: {{ j.binder }}</span>
            <span v-if="j.result?.score" class="rdash__job-score">Score: {{ j.result.score }}/5</span>
            <span v-if="j.error" class="rdash__job-error">{{ j.error }}</span>
          </div>
          <div v-if="selectedJob?.id === j.id && j.state === 'completed'" class="rdash__job-detail">
            <div v-if="j.result?.file"><strong>Saved:</strong> {{ j.result.file }}</div>
            <div v-if="j.result?.score"><strong>Quality:</strong> {{ j.result.score }}/5</div>
            <button class="uxs-btn uxs-btn--sm" @click.stop="$emit('approve', j)">Approve</button>
          </div>
        </div>
        </div>
      </section>

      <aside class="rdash__side">
        <section class="rdash__section rdash__section--request">
          <div class="rdash__section-head">
            <h3>Request Research</h3>
          </div>
          <div class="rdash__request-form">
            <label class="rdash__field">
              <span>URL</span>
              <input v-model="newUrl" placeholder="https://..." class="rdash__input rdash__input--url" />
            </label>
            <label class="rdash__field">
              <span>Binder</span>
              <input v-model="newBinder" placeholder="research" class="rdash__input rdash__input--sm" />
            </label>
            <label class="rdash__field">
              <span>Tags</span>
              <input v-model="newTags" placeholder="ai, docs, planning" class="rdash__input rdash__input--sm" />
            </label>
            <button class="uxs-btn uxs-btn--primary" @click="submitRequest" :disabled="!newUrl">Start Research</button>
          </div>
        </section>

        <section class="rdash__section">
          <div class="rdash__section-head">
            <h3>Research Gaps</h3>
            <span class="rdash__badge">{{ gapCount }}</span>
          </div>

          <div v-if="props.gaps.length === 0" class="rdash__empty">No active gaps detected</div>

          <template v-else>
            <div class="rdash__gap-actions">
              <button class="uxs-btn uxs-btn--sm" @click="props.gaps.forEach(g => $emit('fillGap', g))">Research All</button>
            </div>
          <div v-for="g in props.gaps" :key="g.topic" class="rdash__gap">
            <UIcon name="warning" class="rdash__gap-icon" />
            <span class="rdash__gap-priority" :class="`rdash__gap-priority--${g.priority || 'low'}`">{{ (g.priority || 'low') }}</span>
            <span class="rdash__gap-topic">{{ g.topic }}</span>
            <span class="rdash__gap-reason">{{ g.reason }}</span>
            <button class="uxs-btn uxs-btn--sm" @click="$emit('fillGap', g)">Research</button>
          </div>
          </template>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue"
import UIcon from "../../../skills/atoms/UIcon.vue"

export interface ResearchJob { id: string; url: string; binder: string; state: string; progress: number; error?: string; result?: { file?: string; score?: number } }
export interface ResearchGap { topic: string; reason: string; priority?: string }

const props = defineProps<{ jobs: ResearchJob[]; gaps: ResearchGap[] }>()
const emit = defineEmits<{ approve: [job: ResearchJob]; startResearch: [params: { url: string; binder: string; tags: string[] }]; fillGap: [gap: ResearchGap] }>()

const newUrl = ref("")
const newBinder = ref("")
const newTags = ref("")
const selectedJob = ref<any>(null)

const jobCount = computed(() => props.jobs.length)
const completedCount = computed(() => props.jobs.filter((job) => job.state === "completed").length)
const runningCount = computed(() => props.jobs.filter((job) => ["pending", "scraping", "summarising"].includes(job.state)).length)
const gapCount = computed(() => props.gaps.length)

function stateLabel(state: string): string {
  if (state === "summarising") return "Summarising"
  if (state === "scraping") return "Scraping"
  if (state === "completed") return "Completed"
  if (state === "failed") return "Failed"
  return "Pending"
}

function stateIcon(state: string): string {
  if (state === "completed") return "task_alt"
  if (state === "failed") return "error"
  if (state === "scraping") return "travel_explore"
  if (state === "summarising") return "auto_awesome"
  return "hourglass_top"
}

function submitRequest() {
  if (!newUrl.value) return
  const tags = newTags.value.split(",").map(t => t.trim()).filter(Boolean)
  emit("startResearch", { url: newUrl.value, binder: newBinder.value || "research", tags })
  newUrl.value = ""
  newTags.value = ""
}
</script>

<style scoped>
.rdash {
  padding: var(--usx-spacing-sm);
  overflow-y: auto;
  display: grid;
  gap: var(--usx-spacing-md);
}

.rdash__hero {
  display: grid;
  gap: var(--usx-spacing-xs);
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--usx-color-primary) 5%, transparent) 0%,
    transparent 75%
  );
}

.rdash__hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.rdash__hero-badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.rdash__hero-badge {
  display: inline-flex;
  align-items: center;
  min-height: calc(var(--usx-touch-target-compact) - var(--usx-spacing-xs));
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: color-mix(in srgb, var(--usx-color-surface-variant) 75%, var(--usx-color-surface));
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.rdash__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: var(--usx-spacing-sm);
}

.rdash__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  min-height: calc(var(--usx-touch-target-comfortable) * 1.25);
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
}

.rdash__stat-value {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-semibold);
  line-height: var(--usx-line-height-tight);
}

.rdash__stat-value--info {
  color: var(--usx-color-primary);
}

.rdash__stat-value--success {
  color: var(--usx-color-success);
}

.rdash__stat-value--warning {
  color: var(--usx-color-warning);
}

.rdash__stat-label {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.rdash__layout {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr);
  gap: var(--usx-spacing-md);
  align-items: start;
}

.rdash__side {
  display: grid;
  gap: var(--usx-spacing-md);
}

.rdash__section {
  margin: 0;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-surface) 95%, var(--usx-color-background));
  padding: var(--usx-spacing-md);
}

.rdash__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-sm);
}

.rdash__section h3 {
  font-size: var(--usx-font-size-base);
  margin: 0;
}

.rdash__empty {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) dashed var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
}

.rdash__queue-list {
  display: grid;
  gap: var(--usx-spacing-sm);
}

.rdash__job {
  padding: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  margin-bottom: 0;
  cursor: pointer;
  transition: border-color var(--usx-transition-fast), box-shadow var(--usx-transition-fast);
}

.rdash__job--selected {
  border-color: var(--usx-color-primary);
  box-shadow: 0 0 0 var(--usx-border-width) color-mix(in srgb, var(--usx-color-primary) 35%, transparent);
}

.rdash__job-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--usx-font-size-sm);
  gap: var(--usx-spacing-xs);
}

.rdash__job-main {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  min-width: 0;
}

.rdash__job-icon {
  color: var(--usx-color-primary);
  font-size: var(--usx-font-size-base);
}

.rdash__job-url {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.rdash__job-state {
  font-size: var(--usx-font-size-xs);
  padding: 0 var(--usx-spacing-xs);
  min-height: calc(var(--usx-touch-target-compact) - var(--usx-spacing-sm));
  border-radius: var(--usx-radius-sm);
  text-transform: uppercase;
  display: inline-flex;
  align-items: center;
}

.rdash__job-state--pending { background: var(--usx-color-surface-variant); }
.rdash__job-state--scraping { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.rdash__job-state--summarising { background: var(--usx-color-warning); }
.rdash__job-state--completed { background: var(--usx-color-success); color: var(--usx-color-on-success); }
.rdash__job-state--failed { background: var(--usx-color-danger); color: var(--usx-color-on-danger); }

.rdash__job-bar { height: var(--usx-spacing-xs); background: var(--usx-color-surface-variant); border-radius: var(--usx-radius-full); margin: var(--usx-spacing-xs) 0; }
.rdash__job-bar-fill { height: 100%; background: var(--usx-color-primary); border-radius: var(--usx-radius-full); transition: width var(--usx-transition-base); }
.rdash__job-meta { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-sm); font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.rdash__job-error { color: var(--usx-color-danger); }
.rdash__job-detail { margin-top: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); background: var(--usx-color-surface-variant); border-radius: var(--usx-radius-sm); font-size: var(--usx-font-size-xs); }
.rdash__job-score { color: var(--usx-color-success); font-weight: var(--usx-font-weight-semibold); }

.rdash__request-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--usx-spacing-sm);
}

.rdash__field {
  display: grid;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.rdash__input {
  min-height: var(--usx-touch-target-compact);
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  background: var(--usx-color-surface-variant);
}

.rdash__input--sm,
.rdash__input--url {
  width: 100%;
}

.rdash__gap-actions { margin-bottom: var(--usx-spacing-sm); }
.rdash__badge { display: inline-flex; align-items: center; justify-content: center; min-width: var(--usx-touch-target-compact); height: var(--usx-touch-target-compact); padding: 0 var(--usx-spacing-xs); border-radius: var(--usx-radius-full); background: var(--usx-color-primary); color: var(--usx-color-on-primary); font-size: var(--usx-font-size-xs); font-weight: var(--usx-font-weight-semibold); }

.rdash__gap {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) minmax(0, 1.2fr) auto;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) 0;
  font-size: var(--usx-font-size-sm);
}
.rdash__gap-icon { color: var(--usx-color-warning); }
.rdash__gap-priority { font-size: var(--usx-font-size-xs); padding: 0 var(--usx-spacing-xs); min-height: calc(var(--usx-touch-target-compact) - var(--usx-spacing-sm)); border-radius: var(--usx-radius-sm); text-transform: uppercase; font-weight: var(--usx-font-weight-semibold); display: inline-flex; align-items: center; }
.rdash__gap-priority--high { background: var(--usx-color-danger); color: var(--usx-color-on-danger); }
.rdash__gap-priority--medium { background: var(--usx-color-warning); color: var(--usx-color-on-warning); }
.rdash__gap-priority--low { background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface-muted); }
.rdash__gap-topic { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rdash__gap-reason { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); min-width: 0; }

.uxs-btn { border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); min-height: var(--usx-touch-target-compact); padding: 0 var(--usx-spacing-sm); cursor: pointer; background: var(--usx-color-surface); font-size: var(--usx-font-size-xs); }
.uxs-btn:hover { background: var(--usx-color-surface-hover); }
.uxs-btn--primary { background: var(--usx-color-primary); color: var(--usx-color-on-primary); border-color: var(--usx-color-primary); }
.uxs-btn--sm { font-size: var(--usx-font-size-xs); }
.uxs-btn:disabled { opacity: 0.5; cursor: default; }

@media (max-width: 1100px) {
  .rdash__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .rdash__layout {
    grid-template-columns: 1fr;
  }

  .rdash__gap {
    grid-template-columns: auto auto minmax(0, 1fr);
  }

  .rdash__gap-reason {
    grid-column: 1 / -1;
  }
}

@media (max-width: 700px) {
  .rdash__stats {
    grid-template-columns: 1fr;
  }
}
</style>
