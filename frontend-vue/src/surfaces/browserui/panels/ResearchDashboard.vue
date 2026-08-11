/**
 * @component ResearchDashboard — Research queue, progress, and gaps.
 */
<template>
  <div class="rdash">
    <div class="rdash__section">
      <h3>Research Queue</h3>
      <div v-if="jobs.length === 0" class="rdash__empty">No active research jobs</div>
      <div v-for="j in jobs" :key="j.id" class="rdash__job">
        <div class="rdash__job-top">
          <span class="rdash__job-url">{{ j.url }}</span>
          <span class="rdash__job-state" :class="`rdash__job-state--${j.state}`">{{ j.state }}</span>
        </div>
        <div class="rdash__job-bar">
          <div class="rdash__job-bar-fill" :style="{ width: j.progress + '%' }"></div>
        </div>
        <div class="rdash__job-meta">
          <span>Binder: {{ j.binder }}</span>
          <span v-if="j.error" class="rdash__job-error">{{ j.error }}</span>
        </div>
        <div v-if="j.state === 'completed'" class="rdash__job-actions">
          <button class="uxs-btn" @click="$emit('approve', j)">Approve &amp; Commit</button>
        </div>
      </div>
    </div>

    <div class="rdash__section">
      <h3>Request Research</h3>
      <div class="rdash__request-form">
        <input v-model="newUrl" placeholder="https://..." class="rdash__input" />
        <input v-model="newBinder" placeholder="binder name" class="rdash__input rdash__input--sm" />
        <input v-model="newTags" placeholder="tags (comma)" class="rdash__input rdash__input--sm" />
        <button class="uxs-btn uxs-btn--primary" @click="submitRequest" :disabled="!newUrl">Start Research</button>
      </div>
    </div>

    <div class="rdash__section" v-if="gaps.length > 0">
      <h3>Research Gaps</h3>
      <div v-for="g in gaps" :key="g.topic" class="rdash__gap">
        <UIcon name="warning" class="rdash__gap-icon" />
        <span>{{ g.topic }}</span>
        <button class="uxs-btn uxs-btn--sm" @click="$emit('fillGap', g)">Research</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import UIcon from "../../../skills/atoms/UIcon.vue"

export interface ResearchJob { id: string; url: string; binder: string; state: string; progress: number; error?: string }
export interface ResearchGap { topic: string; reason: string }

defineProps<{ jobs: ResearchJob[]; gaps: ResearchGap[] }>()
defineEmits<{ approve: [job: ResearchJob]; startResearch: [params: { url: string; binder: string; tags: string[] }]; fillGap: [gap: ResearchGap] }>()

const newUrl = ref("")
const newBinder = ref("")
const newTags = ref("")

function submitRequest() {
  if (!newUrl.value) return
  const tags = newTags.value.split(",").map(t => t.trim()).filter(Boolean)
  emit("startResearch", { url: newUrl.value, binder: newBinder.value || "research", tags })
  newUrl.value = ""
}

const emit = defineEmits<{ approve: [job: ResearchJob]; startResearch: [params: { url: string; binder: string; tags: string[] }]; fillGap: [gap: ResearchGap] }>()
</script>

<style scoped>
.rdash { padding: var(--usx-spacing-md); overflow-y: auto; }
.rdash__section { margin-bottom: var(--usx-spacing-lg); }
.rdash__section h3 { font-size: var(--usx-font-size-base); margin-bottom: var(--usx-spacing-sm); }
.rdash__empty { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); padding: var(--usx-spacing-md); }
.rdash__job { padding: var(--usx-spacing-sm); border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); margin-bottom: var(--usx-spacing-sm); }
.rdash__job-top { display: flex; justify-content: space-between; font-size: var(--usx-font-size-sm); }
.rdash__job-url { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 70%; }
.rdash__job-state { font-size: var(--usx-font-size-xs); padding: 1px 6px; border-radius: var(--usx-radius-sm); text-transform: uppercase; }
.rdash__job-state--pending { background: var(--usx-color-surface-variant); }
.rdash__job-state--scraping { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.rdash__job-state--summarising { background: var(--usx-color-warning); }
.rdash__job-state--completed { background: var(--usx-color-success); color: var(--usx-color-on-success); }
.rdash__job-state--failed { background: var(--usx-color-danger); color: var(--usx-color-on-danger); }
.rdash__job-bar { height: 4px; background: var(--usx-color-surface-variant); border-radius: 2px; margin: var(--usx-spacing-xs) 0; }
.rdash__job-bar-fill { height: 100%; background: var(--usx-color-primary); border-radius: 2px; transition: width 0.3s; }
.rdash__job-meta { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.rdash__job-error { color: var(--usx-color-danger); }
.rdash__job-actions { margin-top: var(--usx-spacing-xs); }
.rdash__request-form { display: flex; gap: var(--usx-spacing-sm); flex-wrap: wrap; }
.rdash__input { padding: 4px var(--usx-spacing-sm); border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); font-size: var(--usx-font-size-sm); flex: 2; }
.rdash__input--sm { flex: 1; }
.rdash__gap { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-xs) 0; font-size: var(--usx-font-size-sm); }
.rdash__gap-icon { color: var(--usx-color-warning); }
.uxs-btn { border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); padding: 4px var(--usx-spacing-sm); cursor: pointer; background: var(--usx-color-surface); font-size: var(--usx-font-size-xs); }
.uxs-btn:hover { background: var(--usx-color-surface-hover); }
.uxs-btn--primary { background: var(--usx-color-primary); color: var(--usx-color-on-primary); border-color: var(--usx-color-primary); }
.uxs-btn--sm { font-size: var(--usx-font-size-xs); }
.uxs-btn:disabled { opacity: 0.5; cursor: default; }
</style>
