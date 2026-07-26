<template>
  <div class="developer-panel">
    <div class="developer-panel-header">
      <h3 class="developer-panel-title">Skills</h3>
      <UBadge type="success">{{ loading ? '...' : skills.length + ' installed' }}</UBadge>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="skills-loading">
      <UIcon name="sync" spin :size="18" />
      <span>Loading skills...</span>
    </div>

    <!-- Offline -->
    <div v-else-if="offline" class="skills-offline">
      <UIcon name="cloud_off" :size="18" />
      <span>Skills backend unreachable. Start the uCore server.</span>
    </div>

    <!-- Skill list -->
    <div v-else class="developer-card-list">
      <div
        v-for="skill in skills"
        :key="skill.id"
        class="developer-card"
      >
        <div class="developer-card-row">
          <div class="developer-card-info">
            <UIcon :name="skill.icon" />
            <div class="developer-card-text">
              <span class="developer-card-title">{{ skill.name }}</span>
              <span class="developer-card-desc">{{ skill.description }}</span>
              <span v-if="skill.category" class="developer-card-category">{{ skill.category }}</span>
            </div>
            <UBadge
              :type="runState(skill.id).status === 'success' ? 'success' : runState(skill.id).status === 'error' ? 'error' : skill.active ? 'success' : 'info'"
              size="sm"
            >
              {{ runState(skill.id).status === 'loading' ? 'running...' : runState(skill.id).status === 'success' ? 'done' : runState(skill.id).status === 'error' ? 'failed' : skill.active ? 'active' : 'available' }}
            </UBadge>
          </div>
          <div class="developer-card-actions">
            <button
              class="skill-run-btn"
              :disabled="runState(skill.id).status === 'loading'"
              @click="runSkill(skill)"
            >
              <UIcon
                :name="runState(skill.id).status === 'loading' ? 'sync' : 'play_arrow'"
                :spin="runState(skill.id).status === 'loading'"
                :size="14"
              />
              {{ runState(skill.id).status === 'loading' ? 'Running' : 'Run' }}
            </button>
          </div>
        </div>

        <!-- Confirmation prompt -->
        <div
          v-if="runState(skill.id).awaitingConfirm"
          class="skill-confirm-bar"
        >
          <UIcon name="warning" :size="14" />
          <span>This skill requires confirmation. Proceed?</span>
          <button class="skill-confirm-yes" @click.stop="confirmRun(skill)">Yes, Run</button>
          <button class="skill-confirm-no" @click.stop="cancelConfirm(skill.id)">Cancel</button>
        </div>

        <!-- Result -->
        <div
          v-if="runState(skill.id).status === 'success'"
          class="skill-result skill-result--success"
        >
          <div class="skill-result-header">
            <UIcon name="check_circle" :size="14" />
            <span>Success</span>
            <button class="skill-result-dismiss" @click.stop="clearResult(skill.id)">Dismiss</button>
          </div>
          <!-- Health summary (ecosystem-audit, skill-audit, etc.) -->
          <div v-if="runState(skill.id).resultHealth" class="skill-health-summary">
            <div class="skill-health-row" v-if="runState(skill.id).resultHealth!.working !== undefined">
              <span>Working</span> <strong>{{ runState(skill.id).resultHealth!.working }}</strong>
            </div>
            <div class="skill-health-row" v-if="runState(skill.id).resultHealth!.untested">
              <span>Untested</span> <strong>{{ runState(skill.id).resultHealth!.untested }}</strong>
            </div>
            <div class="skill-health-row" v-if="runState(skill.id).resultHealth!.broken">
              <span>Broken</span> <strong>{{ runState(skill.id).resultHealth!.broken }}</strong>
            </div>
            <div class="skill-health-row" v-if="runState(skill.id).resultHealth!.orphaned">
              <span>Orphaned</span> <strong>{{ runState(skill.id).resultHealth!.orphaned }}</strong>
            </div>
            <div class="skill-health-row" v-if="runState(skill.id).resultHealth!.health_pct !== undefined">
              <span>Health</span> <strong>{{ runState(skill.id).resultHealth!.health_pct }}%</strong>
            </div>
            <div class="skill-health-row" v-if="runState(skill.id).resultHealth!.total_items">
              <span>Total Items</span> <strong>{{ runState(skill.id).resultHealth!.total_items }}</strong>
            </div>
          </div>
          <!-- Summary stats (ecosystem-audit report) -->
          <div v-if="runState(skill.id).resultSummary" class="skill-health-summary">
            <div class="skill-health-row" v-for="(entry) in resultSummaryEntries(skill.id)" :key="entry[0]">
              <span>{{ formatKey(entry[0]) }}</span> <strong>{{ entry[1] }}</strong>
            </div>
          </div>
          <pre class="skill-output">{{ runState(skill.id).resultJson }}</pre>
        </div>

        <!-- Error -->
        <div
          v-if="runState(skill.id).status === 'error'"
          class="skill-result skill-result--error"
        >
          <div class="skill-result-header">
            <UIcon name="error" :size="14" />
            <span>Error</span>
            <button class="skill-result-dismiss" @click.stop="clearResult(skill.id)">Dismiss</button>
          </div>
          <div class="skill-error-msg">{{ runState(skill.id).errorMessage }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SkillsPanel
 * @description Simple skills runner — list skills, click Run, see result.
 *   Destructive skills require explicit confirmation.
 *   Result is shown as formatted JSON with optional health/summary extraction.
 * @category surfaces/developer
 */
import { ref, reactive, onMounted } from 'vue'
import UIcon from '../../../skills/atoms/UIcon.vue'
import UBadge from '../../../skills/atoms/UBadge.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

interface Skill {
  id: string
  name: string
  icon: string
  active: boolean
  version: string
  runs: number
  description: string
  category?: string
  category_priority?: number
  requires_confirmation?: boolean
}

interface RunState {
  status: 'idle' | 'loading' | 'success' | 'error'
  resultJson: string
  resultHealth: Record<string, number> | null
  resultSummary: Record<string, number> | null
  errorMessage: string
  awaitingConfirm: boolean
}

const skills = ref<Skill[]>([])
const loading = ref(true)
const offline = ref(false)

const runStates = reactive<Record<string, RunState>>({})

function getRunState(skillId: string): RunState {
  if (!runStates[skillId]) {
    runStates[skillId] = {
      status: 'idle',
      resultJson: '',
      resultHealth: null,
      resultSummary: null,
      errorMessage: '',
      awaitingConfirm: false,
    }
  }
  return runStates[skillId]
}

function runState(skillId: string): RunState {
  return getRunState(skillId)
}

/** Type-safe accessor for resultSummary entries. */
function resultSummaryEntries(skillId: string) {
  const summary = runStates[skillId]?.resultSummary
  if (!summary) return []
  return Object.entries(summary) as [string, unknown][]
}

const iconMap: Record<string, string> = {
  'vault-sync': 'sync',
  'tasker': 'task',
  'git-maintenance': 'build',
  'usx-standard': 'palette',
  'daily-backup': 'backup',
  'brain-sync': 'psychology',
  'dev-destroy-rebuild': 'restart_alt',
  'docs-roundup': 'description',
  'tasker-ingest': 'input',
  'ask-vault': 'search',
  'file-edit-enhancer': 'edit',
  'autostart_health_check': 'monitor_heart',
  'ecosystem-audit': 'analytics',
}

const DESTRUCTIVE_CATEGORIES = new Set(['mutating', 'destructive', 'write', 'admin'])

function isDestructive(skill: Skill): boolean {
  if (skill.requires_confirmation) return true
  if (!skill.category) return false
  return DESTRUCTIVE_CATEGORIES.has(skill.category.toLowerCase())
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function fetchSkills() {
  loading.value = true
  offline.value = false
  try {
    const res = await fetch(`${API_BASE}/api/skills`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    const list = data.skills || data || []
    skills.value = list.map((s: any) => ({
      id: s.skill_id || s.id || s.name?.toLowerCase() || 'unknown',
      name: s.name || s.skill_id || 'Unknown Skill',
      icon: iconMap[s.skill_id] || iconMap[s.id] || 'extension',
      active: s.active !== false,
      version: s.version || '1.0',
      runs: s.runs || s.run_count || 0,
      description: s.description || s.skill_id || '',
      category: s.category || undefined,
      category_priority: s.category_priority,
      requires_confirmation: s.requires_confirmation === true,
    }))
  } catch {
    offline.value = true
    skills.value = []
  } finally {
    loading.value = false
  }
}

async function runSkill(skill: Skill) {
  const state = getRunState(skill.id)

  // Destructive skills require confirmation first
  if (isDestructive(skill) && !state.awaitingConfirm) {
    state.awaitingConfirm = true
    return
  }

  state.status = 'loading'
  state.resultJson = ''
  state.resultHealth = null
  state.resultSummary = null
  state.errorMessage = ''
  state.awaitingConfirm = false

  try {
    const body: Record<string, unknown> = {}
    if (isDestructive(skill)) {
      body.confirm = true
    }

    const res = await fetch(`${API_BASE}/api/skills/${encodeURIComponent(skill.id)}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120_000),
    })

    const data = await res.json()

    if (!res.ok || data.error) {
      state.status = 'error'
      state.errorMessage = data.error || data.errors?.join(', ') || `HTTP ${res.status}`
      return
    }

    state.status = 'success'

    // Extract health stats if present (ecosystem-audit, skill-audit)
    if (data.health && typeof data.health === 'object') {
      state.resultHealth = data.health
    }
    // Extract summary if present (ecosystem-audit report)
    if (data.summary && typeof data.summary === 'object' && !Array.isArray(data.summary)) {
      state.resultSummary = data.summary
    }

    // Format full result as pretty JSON for display
    state.resultJson = JSON.stringify(data, null, 2)
  } catch (e: any) {
    state.status = 'error'
    if (e.name === 'TimeoutError' || e.name === 'AbortError') {
      state.errorMessage = 'Request timed out. The skill may still be running server-side.'
    } else {
      state.errorMessage = e.message || 'Unknown error'
    }
  }
}

function confirmRun(skill: Skill) {
  const state = getRunState(skill.id)
  state.awaitingConfirm = false
  runSkill(skill)
}

function cancelConfirm(skillId: string) {
  const state = getRunState(skillId)
  state.awaitingConfirm = false
}

function clearResult(skillId: string) {
  const state = getRunState(skillId)
  state.status = 'idle'
  state.resultJson = ''
  state.resultHealth = null
  state.resultSummary = null
  state.errorMessage = ''
}

onMounted(() => {
  fetchSkills()
})
</script>

<style scoped>
.developer-panel {
  max-width: calc(var(--usx-spacing-2xl) * 28);
}

.developer-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--usx-spacing-md);
}

.developer-panel-title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
}

.skills-loading,
.skills-offline {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-lg);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
}

/* ─── Card List ────────────────────────────────────── */
.developer-card-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.developer-card {
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
}

.developer-card-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
}

.developer-card-info {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  flex: 1;
  min-width: 0;
}

.developer-card-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.developer-card-title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.developer-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.developer-card-category {
  display: inline-block;
  padding: 0 var(--usx-spacing-xs);
  background: color-mix(in srgb, var(--usx-color-info) 10%, transparent);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-xs);
  width: fit-content;
}

.developer-card-actions {
  flex-shrink: 0;
}

/* ─── Run Button ───────────────────────────────────── */
.skill-run-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border: none;
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  cursor: pointer;
  white-space: nowrap;
}

.skill-run-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.skill-run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ─── Confirmation Bar ─────────────────────────────── */
.skill-confirm-bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  background: color-mix(in srgb, var(--usx-color-warning) 8%, transparent);
  border: var(--usx-border-width) solid var(--usx-color-warning);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
}

.skill-confirm-bar span {
  flex: 1;
}

.skill-confirm-yes,
.skill-confirm-no {
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border: none;
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  cursor: pointer;
}

.skill-confirm-yes {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
}

.skill-confirm-no {
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

/* ─── Result Display ───────────────────────────────── */
.skill-result {
  margin-top: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  overflow: hidden;
}

.skill-result--success {
  border-color: var(--usx-color-success);
}

.skill-result--error {
  border-color: var(--usx-color-danger);
}

.skill-result-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-background);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-medium);
}

.skill-result-dismiss {
  margin-left: auto;
  padding: var(--usx-spacing-1) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
}

/* ─── Health Summary ───────────────────────────────── */
.skill-health-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm);
  background: var(--usx-color-surface);
}

.skill-health-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-background);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
}

.skill-health-row strong {
  color: var(--usx-color-primary);
}

/* ─── JSON Output ──────────────────────────────────── */
.skill-output {
  margin: 0;
  padding: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono, 'SF Mono', 'Menlo', monospace);
  line-height: 1.4;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
}

/* ─── Error Message ────────────────────────────────── */
.skill-error-msg {
  padding: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 4%, transparent);
}
</style>