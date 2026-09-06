<template>
  <div class="surface google-surface">
    <div class="surface__content">
      <!-- Header / Nav -->
      <section class="surface__panel google-header">
        <div class="google-header__row">
          <div class="google-title-wrap">
            <UIcon name="cloud" class="google-title-icon" />
            <div>
              <h1 class="surface__panel-title">Google AI & Drive Studio</h1>
              <p class="surface__panel-description">
                Gemini 2.0 Frontier Gateway, Drive Mirror Ledger, and Python Code Execution Sandbox.
              </p>
            </div>
          </div>
          <div class="google-nav-pills">
            <button
              type="button"
              class="google-nav-pill"
              :class="{ 'google-nav-pill--active': activeTab === 'overview' }"
              @click="activeTab = 'overview'"
            >
              <UIcon name="hub" /> Overview & Grounding
            </button>
            <button
              type="button"
              class="google-nav-pill"
              :class="{ 'google-nav-pill--active': activeTab === 'drive' }"
              @click="activeTab = 'drive'"
            >
              <UIcon name="folder_sync" /> Drive Mirror Ledger
            </button>
            <button
              type="button"
              class="google-nav-pill"
              :class="{ 'google-nav-pill--active': activeTab === 'code' }"
              @click="activeTab = 'code'"
            >
              <UIcon name="terminal" /> Code Sandbox
            </button>
          </div>
        </div>
      </section>

      <!-- Feedback notice banner -->
      <div v-if="noticeMessage" class="google-notice" :class="`google-notice--${noticeType}`">
        <span>{{ noticeMessage }}</span>
        <button class="google-notice-close" @click="noticeMessage = ''">&times;</button>
      </div>

      <!-- Tab 1: Overview & Grounding -->
      <div v-if="activeTab === 'overview'" class="google-tab-body">
        <!-- Status grid -->
        <div class="google-status-grid">
          <div class="google-card">
            <div class="google-card__icon-wrap google-card__icon-wrap--cyan">
              <UIcon name="smart_toy" />
            </div>
            <div class="google-card__info">
              <div class="google-card__label">Frontier Model</div>
              <div class="google-card__val">Gemini 2.0 Flash</div>
              <div class="google-card__sub">Native Tool Execution & Web Grounding</div>
            </div>
          </div>
          <div class="google-card">
            <div class="google-card__icon-wrap google-card__icon-wrap--amber">
              <UIcon name="palette" />
            </div>
            <div class="google-card__info">
              <div class="google-card__label">Visual Synthesis</div>
              <div class="google-card__val">Imagen 3 / Banana</div>
              <div class="google-card__sub">Mono Core Styles (Teletext, Blueprint)</div>
            </div>
          </div>
          <div class="google-card">
            <div class="google-card__icon-wrap google-card__icon-wrap--green">
              <UIcon name="sync" />
            </div>
            <div class="google-card__info">
              <div class="google-card__label">Vault Mirroring</div>
              <div class="google-card__val">Offline Google Docs</div>
              <div class="google-card__sub">Bi-directional Markdown sync ledger</div>
            </div>
          </div>
        </div>

        <!-- Grounded Search Tester -->
        <div class="google-card google-grounded-card">
          <div class="google-card__header">
            <div class="google-card__title">
              <UIcon name="travel_explore" />
              <h3>Grounded Web Synthesis</h3>
            </div>
            <span class="google-badge google-badge--cyan">Gemini 2.0 + Google Search</span>
          </div>

          <div class="google-grounded-input-row">
            <input
              v-model="searchQuery"
              type="text"
              class="google-input"
              placeholder="Enter a research query for live grounded synthesis..."
              @keyup.enter="handleGroundedSearch"
            />
            <button
              type="button"
              class="google-btn google-btn--primary"
              :disabled="isSearching || !searchQuery.trim()"
              @click="handleGroundedSearch"
            >
              <UIcon :name="isSearching ? 'hourglass_top' : 'search'" />
              <span>{{ isSearching ? "Synthesizing..." : "Search" }}</span>
            </button>
          </div>

          <!-- Grounded Search Results -->
          <div v-if="searchResult" class="google-grounded-results">
            <div class="google-results-meta">
              <span class="google-model-tag">{{ searchResult.model }}</span>
              <span v-if="searchResult.live_grounded" class="google-badge google-badge--live">Live Web Grounded</span>
              <span v-else class="google-badge google-badge--mock">Local Simulation</span>
            </div>
            <div class="google-results-summary">
              {{ searchResult.summary }}
            </div>

            <!-- Citations -->
            <div v-if="searchResult.citations?.length" class="google-citations">
              <h4 class="google-citations-heading">Grounding Citations & Sources</h4>
              <div class="google-citation-list">
                <a
                  v-for="citation in searchResult.citations"
                  :key="citation.index"
                  :href="citation.uri"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="google-citation-item"
                >
                  <div class="google-citation-index">[{{ citation.index }}]</div>
                  <div class="google-citation-content">
                    <div class="google-citation-title">{{ citation.title }}</div>
                    <div class="google-citation-uri">{{ citation.uri }}</div>
                    <div v-if="citation.snippet" class="google-citation-snippet">{{ citation.snippet }}</div>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 2: Drive Mirror Ledger -->
      <div v-if="activeTab === 'drive'" class="google-tab-body">
        <div class="google-card google-drive-card">
          <div class="google-card__header">
            <div class="google-card__title">
              <UIcon name="cloud_sync" />
              <h3>Google Drive & Vault Ledger</h3>
            </div>
            <div class="google-card__actions">
              <button
                type="button"
                class="google-btn google-btn--outline"
                :disabled="isLoadingStatus"
                @click="fetchDriveStatus"
              >
                <UIcon :name="isLoadingStatus ? 'hourglass_top' : 'refresh'" />
                <span>Refresh</span>
              </button>
              <button
                type="button"
                class="google-btn google-btn--primary"
                :disabled="isSyncing"
                @click="handleDriveSync"
              >
                <UIcon :name="isSyncing ? 'hourglass_top' : 'sync'" />
                <span>{{ isSyncing ? "Scanning..." : "Sync Vault Ledger" }}</span>
              </button>
            </div>
          </div>

          <!-- Metrics summary -->
          <div class="google-drive-stats">
            <div class="google-stat-pill">
              <span class="google-stat-val">{{ driveStatus?.total_files ?? 0 }}</span>
              <span class="google-stat-lbl">Total Vault Files</span>
            </div>
            <div class="google-stat-pill google-stat-pill--green">
              <span class="google-stat-val">{{ driveStatus?.mirrored_count ?? 0 }}</span>
              <span class="google-stat-lbl">Mirrored</span>
            </div>
            <div class="google-stat-pill google-stat-pill--amber">
              <span class="google-stat-val">{{ driveStatus?.modified_count ?? 0 }}</span>
              <span class="google-stat-lbl">Modified Locally</span>
            </div>
            <div class="google-stat-pill google-stat-pill--purple">
              <span class="google-stat-val">{{ driveStatus?.unmirrored_count ?? 0 }}</span>
              <span class="google-stat-lbl">Unmirrored</span>
            </div>
          </div>

          <!-- Files Table -->
          <div class="google-ledger-table-wrap">
            <table class="google-ledger-table">
              <thead>
                <tr>
                  <th>File / Document</th>
                  <th>Sync State</th>
                  <th>Revision</th>
                  <th>Checksum</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!fileEntries.length">
                  <td colspan="4" class="google-empty-row">
                    No vault documents found. Click "Sync Vault Ledger" to scan <code>~/Vault</code>.
                  </td>
                </tr>
                <tr v-for="[path, file] in fileEntries" :key="path">
                  <td class="google-filename-cell">
                    <UIcon :name="getFileIcon(path)" class="google-file-icon" />
                    <span class="google-filename" :title="path">{{ path }}</span>
                  </td>
                  <td>
                    <span class="google-sync-badge" :class="`google-sync-badge--${file.status}`">
                      {{ file.status }}
                    </span>
                  </td>
                  <td class="google-mono-cell">r{{ file.revision }}</td>
                  <td class="google-mono-cell">{{ file.checksum ? file.checksum.slice(0, 10) + '...' : '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Tab 3: Python Code Sandbox -->
      <div v-if="activeTab === 'code'" class="google-tab-body">
        <div class="google-card google-code-card">
          <div class="google-card__header">
            <div class="google-card__title">
              <UIcon name="terminal" />
              <h3>Gemini 2.0 Code Execution Console</h3>
            </div>
            <div class="google-card__actions">
              <span class="google-badge google-badge--cyan">Sandboxed Python</span>
            </div>
          </div>

          <!-- Preset templates -->
          <div class="google-presets-bar">
            <span class="google-presets-label">Presets:</span>
            <button
              v-for="p in CODE_PRESETS"
              :key="p.name"
              type="button"
              class="google-preset-btn"
              @click="codeText = p.code"
            >
              {{ p.name }}
            </button>
          </div>

          <!-- Editor area -->
          <div class="google-code-editor-wrap">
            <textarea
              v-model="codeText"
              class="google-code-textarea"
              rows="12"
              spellcheck="false"
              placeholder="# Enter Python code for Gemini 2.0 sandboxed execution..."
            />
          </div>

          <div class="google-code-actions">
            <button
              type="button"
              class="google-btn google-btn--primary"
              :disabled="isExecuting || !codeText.trim()"
              @click="handleRunCode"
            >
              <UIcon :name="isExecuting ? 'hourglass_top' : 'play_arrow'" />
              <span>{{ isExecuting ? "Executing..." : "Run Code" }}</span>
            </button>
          </div>

          <!-- Console Terminal Output -->
          <div v-if="codeResult" class="google-terminal">
            <div class="google-terminal__header">
              <div class="google-terminal__status">
                <span class="google-terminal__dot" :class="codeResult.outcome === 'OUTCOME_OK' ? 'google-terminal__dot--ok' : 'google-terminal__dot--err'"></span>
                <span>{{ codeResult.outcome }}</span>
              </div>
              <span class="google-badge" :class="codeResult.live_execution ? 'google-badge--live' : 'google-badge--mock'">
                {{ codeResult.live_execution ? 'Live Gemini Sandbox' : 'Local Sandbox' }}
              </span>
            </div>
            <pre class="google-terminal__output">{{ codeResult.output || "(no output)" }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import UIcon from "@/skills/atoms/UIcon.vue"
import {
  searchGrounded,
  getDriveSyncStatus,
  syncGoogleDriveVault,
  executeGoogleCode,
  type GroundedSearchResult,
  type DriveVaultStatusResult,
  type CodeExecutionResult,
} from "../browserui/ApiBridge"

const activeTab = ref<"overview" | "drive" | "code">("overview")

// Notifications
const noticeMessage = ref("")
const noticeType = ref<"success" | "error" | "info">("info")

// Grounded search state
const searchQuery = ref("Latest breakthroughs in Gemini 2.0 tool execution and grounding")
const isSearching = ref(false)
const searchResult = ref<GroundedSearchResult | null>(null)

// Drive state
const isLoadingStatus = ref(false)
const isSyncing = ref(false)
const driveStatus = ref<DriveVaultStatusResult | null>(null)

// Code Execution state
const isExecuting = ref(false)
const codeResult = ref<CodeExecutionResult | null>(null)

const CODE_PRESETS = [
  {
    name: "Fibonacci Sequence",
    code: `def fib(n):\n    a, b = 0, 1\n    res = []\n    for _ in range(n):\n        res.append(a)\n        a, b = b, a + b\n    return res\n\nprint("Fibonacci sequence (12 items):", fib(12))`,
  },
  {
    name: "Prime Sieve",
    code: `def primes_up_to(limit):\n    sieve = [True] * (limit + 1)\n    for p in range(2, int(limit**0.5) + 1):\n        if sieve[p]:\n            for i in range(p * p, limit + 1, p):\n                sieve[i] = False\n    return [p for p in range(2, limit + 1) if sieve[p]]\n\nprint("Primes up to 50:", primes_up_to(50))`,
  },
  {
    name: "System Statistics",
    code: `import math\nimport statistics\n\ndata = [12.5, 14.8, 18.2, 19.1, 24.0, 25.5, 30.1]\nprint("Mean:", statistics.mean(data))\nprint("Stdev:", statistics.stdev(data))\nprint("Square roots:", [round(math.sqrt(x), 2) for x in data])`,
  },
]

const codeText = ref(CODE_PRESETS[0].code)

const fileEntries = computed(() => {
  if (!driveStatus.value?.files) return []
  return Object.entries(driveStatus.value.files)
})

onMounted(() => {
  void fetchDriveStatus()
})

async function handleGroundedSearch() {
  if (!searchQuery.value.trim() || isSearching.value) return
  isSearching.value = true
  try {
    const res = await searchGrounded(searchQuery.value.trim(), "google-studio")
    searchResult.value = res
  } catch (err: any) {
    noticeType.value = "error"
    noticeMessage.value = `Grounded search failed: ${err?.message || err}`
  } finally {
    isSearching.value = false
  }
}

async function fetchDriveStatus() {
  isLoadingStatus.value = true
  try {
    const res = await getDriveSyncStatus()
    driveStatus.value = res
  } catch {
    // offline or not yet initialized
    driveStatus.value = {
      status: "ready",
      total_files: 0,
      mirrored_count: 0,
      modified_count: 0,
      unmirrored_count: 0,
      files: {},
    }
  } finally {
    isLoadingStatus.value = false
  }
}

async function handleDriveSync() {
  isSyncing.value = true
  try {
    const res = await syncGoogleDriveVault()
    noticeType.value = "success"
    noticeMessage.value = `Vault scan complete: ${res.scanned} scanned, ${res.updated} updated.`
    await fetchDriveStatus()
  } catch (err: any) {
    noticeType.value = "error"
    noticeMessage.value = `Vault sync failed: ${err?.message || err}`
  } finally {
    isSyncing.value = false
  }
}

async function handleRunCode() {
  if (!codeText.value.trim() || isExecuting.value) return
  isExecuting.value = true
  try {
    const res = await executeGoogleCode(codeText.value)
    codeResult.value = res
  } catch (err: any) {
    noticeType.value = "error"
    noticeMessage.value = `Code execution failed: ${err?.message || err}`
  } finally {
    isExecuting.value = false
  }
}

function getFileIcon(filename: string): string {
  if (filename.endsWith(".notebook.md")) return "edit_calendar"
  if (filename.endsWith(".md")) return "description"
  if (filename.endsWith(".json")) return "data_object"
  return "insert_drive_file"
}
</script>

<style scoped>
.google-surface {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
  background: var(--usx-color-surface-bg, #0e1117);
  color: var(--usx-color-on-surface, #e6edf3);
}

.google-surface .surface__content {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Header */
.google-header {
  padding: 1.25rem 1.5rem;
  background: var(--usx-color-surface-muted, #161b22);
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 8px;
}

.google-header__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.google-title-wrap {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.google-title-icon {
  font-size: 2.25rem;
  color: var(--usx-color-info, #58a6ff);
}

.surface__panel-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.surface__panel-description {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  color: var(--usx-color-on-surface-muted, #8b949e);
}

/* Nav pills */
.google-nav-pills {
  display: flex;
  gap: 0.5rem;
}

.google-nav-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  background: transparent;
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  color: var(--usx-color-on-surface-muted, #8b949e);
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.google-nav-pill:hover {
  background: var(--usx-color-surface-elevated, #21262d);
  color: var(--usx-color-on-surface, #e6edf3);
}

.google-nav-pill--active {
  background: var(--usx-color-primary, #1f6feb);
  border-color: var(--usx-color-primary, #1f6feb);
  color: #ffffff;
}

/* Notice banner */
.google-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.google-notice--success {
  background: rgba(46, 160, 67, 0.15);
  border: 1px solid #2ea043;
  color: #3fb950;
}

.google-notice--error {
  background: rgba(248, 81, 73, 0.15);
  border: 1px solid #f85149;
  color: #f85149;
}

.google-notice--info {
  background: rgba(56, 139, 253, 0.15);
  border: 1px solid #388bfd;
  color: #58a6ff;
}

.google-notice-close {
  background: none;
  border: none;
  color: inherit;
  font-size: 1.25rem;
  cursor: pointer;
}

/* Body / Grids */
.google-tab-body {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.google-status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.google-card {
  background: var(--usx-color-surface-muted, #161b22);
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.google-status-grid .google-card {
  flex-direction: row;
  align-items: center;
  gap: 1rem;
}

.google-card__icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.google-card__icon-wrap--cyan {
  background: rgba(56, 139, 253, 0.15);
  color: #58a6ff;
}

.google-card__icon-wrap--amber {
  background: rgba(210, 153, 34, 0.15);
  color: #d29922;
}

.google-card__icon-wrap--green {
  background: rgba(46, 160, 67, 0.15);
  color: #3fb950;
}

.google-card__label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--usx-color-on-surface-muted, #8b949e);
}

.google-card__val {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--usx-color-on-surface, #e6edf3);
}

.google-card__sub {
  font-size: 0.8rem;
  color: var(--usx-color-on-surface-muted, #8b949e);
}

/* Card Header */
.google-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.google-card__title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.google-card__title h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.google-card__actions {
  display: flex;
  gap: 0.5rem;
}

/* Buttons & Badges */
.google-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.875rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}

.google-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.google-btn--primary {
  background: var(--usx-color-primary, #1f6feb);
  color: #ffffff;
}

.google-btn--primary:hover:not(:disabled) {
  background: #388bfd;
}

.google-btn--outline {
  background: transparent;
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  color: var(--usx-color-on-surface, #e6edf3);
}

.google-btn--outline:hover:not(:disabled) {
  background: var(--usx-color-surface-elevated, #21262d);
}

.google-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 4px;
}

.google-badge--cyan {
  background: rgba(56, 139, 253, 0.15);
  color: #58a6ff;
  border: 1px solid rgba(56, 139, 253, 0.3);
}

.google-badge--live {
  background: rgba(46, 160, 67, 0.15);
  color: #3fb950;
  border: 1px solid rgba(46, 160, 67, 0.3);
}

.google-badge--mock {
  background: rgba(210, 153, 34, 0.15);
  color: #d29922;
  border: 1px solid rgba(210, 153, 34, 0.3);
}

/* Grounded Inputs */
.google-grounded-input-row {
  display: flex;
  gap: 0.75rem;
}

.google-input {
  flex: 1;
  background: var(--usx-color-surface-elevated, #0d1117);
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  color: var(--usx-color-on-surface, #e6edf3);
  font-size: 0.875rem;
}

.google-input:focus {
  outline: none;
  border-color: var(--usx-color-primary, #1f6feb);
}

.google-grounded-results {
  margin-top: 0.75rem;
  padding: 1rem;
  background: var(--usx-color-surface-elevated, #0d1117);
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.google-results-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.google-model-tag {
  font-size: 0.75rem;
  font-family: monospace;
  color: var(--usx-color-on-surface-muted, #8b949e);
}

.google-results-summary {
  font-size: 0.925rem;
  line-height: 1.5;
  color: var(--usx-color-on-surface, #e6edf3);
}

.google-citations-heading {
  margin: 0.5rem 0 0.25rem;
  font-size: 0.825rem;
  color: var(--usx-color-on-surface-muted, #8b949e);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.google-citation-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.google-citation-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--usx-color-surface-muted, #161b22);
  border-radius: 4px;
  text-decoration: none;
  color: inherit;
  border: 1px solid transparent;
  transition: all 0.15s ease;
}

.google-citation-item:hover {
  border-color: var(--usx-color-primary, #1f6feb);
  background: #1c2128;
}

.google-citation-index {
  font-family: monospace;
  font-weight: bold;
  color: #58a6ff;
  font-size: 0.8rem;
}

.google-citation-title {
  font-size: 0.85rem;
  font-weight: 500;
  color: #58a6ff;
}

.google-citation-uri {
  font-size: 0.75rem;
  color: #8b949e;
  word-break: break-all;
}

.google-citation-snippet {
  font-size: 0.775rem;
  color: #c9d1d9;
  margin-top: 0.2rem;
}

/* Drive Stats */
.google-drive-stats {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.google-stat-pill {
  flex: 1;
  min-width: 140px;
  padding: 0.75rem 1rem;
  background: var(--usx-color-surface-elevated, #0d1117);
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.google-stat-val {
  font-size: 1.5rem;
  font-weight: 700;
}

.google-stat-lbl {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-muted, #8b949e);
  text-transform: uppercase;
}

.google-stat-pill--green .google-stat-val { color: #3fb950; }
.google-stat-pill--amber .google-stat-val { color: #d29922; }
.google-stat-pill--purple .google-stat-val { color: #bc8cff; }

/* Drive Ledger Table */
.google-ledger-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 6px;
}

.google-ledger-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.85rem;
}

.google-ledger-table th,
.google-ledger-table td {
  padding: 0.65rem 0.875rem;
  border-bottom: 1px solid var(--usx-color-border-subtle, #30363d);
}

.google-ledger-table th {
  background: var(--usx-color-surface-elevated, #0d1117);
  color: var(--usx-color-on-surface-muted, #8b949e);
  font-weight: 600;
}

.google-filename-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.google-file-icon {
  font-size: 1rem;
  color: var(--usx-color-primary, #1f6feb);
}

.google-filename {
  font-family: monospace;
}

.google-mono-cell {
  font-family: monospace;
  color: var(--usx-color-on-surface-muted, #8b949e);
}

.google-sync-badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  font-size: 0.725rem;
  font-weight: 600;
  text-transform: uppercase;
}

.google-sync-badge--mirrored {
  background: rgba(46, 160, 67, 0.15);
  color: #3fb950;
}

.google-sync-badge--modified_locally {
  background: rgba(210, 153, 34, 0.15);
  color: #d29922;
}

.google-sync-badge--unmirrored {
  background: rgba(188, 140, 255, 0.15);
  color: #bc8cff;
}

.google-empty-row {
  text-align: center;
  color: var(--usx-color-on-surface-muted, #8b949e);
  padding: 2rem 1rem;
}

/* Code Sandbox */
.google-presets-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.google-presets-label {
  font-size: 0.8rem;
  color: var(--usx-color-on-surface-muted, #8b949e);
}

.google-preset-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.775rem;
  background: var(--usx-color-surface-elevated, #0d1117);
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  color: var(--usx-color-on-surface, #e6edf3);
  border-radius: 4px;
  cursor: pointer;
}

.google-preset-btn:hover {
  border-color: var(--usx-color-primary, #1f6feb);
}

.google-code-editor-wrap {
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 6px;
  overflow: hidden;
}

.google-code-textarea {
  width: 100%;
  box-sizing: border-box;
  background: #0d1117;
  color: #79c0ff;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  padding: 0.75rem;
  border: none;
  resize: vertical;
}

.google-code-textarea:focus {
  outline: none;
}

.google-code-actions {
  display: flex;
  justify-content: flex-end;
}

.google-terminal {
  background: #010409;
  border: 1px solid var(--usx-color-border-subtle, #30363d);
  border-radius: 6px;
  overflow: hidden;
}

.google-terminal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.75rem;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  font-size: 0.75rem;
}

.google-terminal__status {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-family: monospace;
}

.google-terminal__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.google-terminal__dot--ok { background: #3fb950; }
.google-terminal__dot--err { background: #f85149; }

.google-terminal__output {
  margin: 0;
  padding: 0.75rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.825rem;
  color: #e6edf3;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
