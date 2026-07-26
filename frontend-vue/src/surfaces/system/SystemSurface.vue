<template>
  <div class="surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="SYSTEM_TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="surface__content">
      <!-- Pages Browser -->
      <div v-if="currentTab === 'pages'" class="system-panel">
        <h3 class="surface__panel-title">System Pages</h3>
        <p class="system-muted-copy">Browse S-pages and P-pages.</p>
        <div class="system-filter-group">
          <button class="system-filter-btn" :class="{ 'system-filter-btn--active': pageFilter === 'all' }" @click="pageFilter = 'all'">All</button>
          <button class="system-filter-btn" :class="{ 'system-filter-btn--active': pageFilter === 's' }" @click="pageFilter = 's'">S-Pages</button>
          <button class="system-filter-btn" :class="{ 'system-filter-btn--active': pageFilter === 'p' }" @click="pageFilter = 'p'">P-Pages</button>
        </div>
        <div class="system-pages-grid">
          <div v-for="page in filteredPages" :key="page.id" class="system-page-card" @click="navigateToPage(page.id)">
            <UIcon :name="page.icon" />
            <span class="system-page-id">{{ page.id }}</span>
            <span class="system-page-title">{{ page.title }}</span>
          </div>
        </div>
        <p v-if="filteredPages.length === 0" class="system-muted-copy">No pages found. Try a different filter.</p>
      </div>

      <!-- Services -->
      <div v-else-if="currentTab === 'services'" class="system-panel">
        <h3 class="surface__panel-title">Services</h3>
        <p class="system-muted-copy">System daemon and infrastructure health.</p>
        <div v-if="loadingServices" class="system-loading">Probing services...</div>
        <div v-else class="system-services-summary">
          <span class="system-stat system-stat--up">{{ servicesSummary.up }} up</span>
          <span class="system-stat system-stat--degraded">{{ servicesSummary.degraded }} degraded</span>
          <span class="system-stat system-stat--down">{{ servicesSummary.down }} down</span>
          <span class="system-stat system-stat--pct">{{ servicesSummary.healthPct }}% healthy</span>
        </div>
        <div class="system-services-list">
          <div v-for="svc in services" :key="svc.name" class="system-service-row">
            <span class="system-service-dot" :class="'system-service-dot--' + svc.status" />
            <span class="system-service-name">{{ svc.name }}</span>
            <span class="system-service-desc">{{ svc.description }}</span>
            <UBadge :type="svc.status === 'up' ? 'success' : svc.status === 'degraded' ? 'warning' : 'error'" size="sm">{{ svc.status }}</UBadge>
          </div>
        </div>
      </div>

      <!-- Variables -->
      <div v-else-if="currentTab === 'variables'" class="system-panel">
        <h3 class="surface__panel-title">Variables</h3>
        <p class="system-muted-copy">User and installation variables.</p>
        <div v-if="loadingVars" class="system-loading">Loading variables...</div>
        <div v-else>
          <h4 class="system-section-title">User Variables</h4>
          <div class="system-vars-list">
            <div v-for="(value, key) in userVariables" :key="key" class="system-var-row">
              <code class="system-var-key">{{ key }}</code>
              <input
                v-if="editingVar === key"
                v-model="editVarValue"
                class="system-var-input"
                @keyup.enter="saveVariable(key)"
                @keyup.escape="editingVar = null"
              />
              <span v-else class="system-var-value">{{ value }}</span>
              <UBadge type="info" size="sm">user</UBadge>
              <button v-if="editingVar !== key" class="system-edit-btn" @click="startEditVar(key, value)">✎</button>
              <button v-else class="system-save-btn" @click="saveVariable(key)">✓</button>
            </div>
          </div>
          <h4 class="system-section-title">Installation Metadata</h4>
          <div class="system-vars-list">
            <div v-for="(value, key) in installVariables" :key="key" class="system-var-row">
              <code class="system-var-key">{{ key }}</code>
              <span class="system-var-value">{{ value }}</span>
              <UBadge type="neutral" size="sm">install</UBadge>
            </div>
          </div>
        </div>
      </div>

      <!-- Secrets -->
      <div v-else-if="currentTab === 'secrets'" class="system-panel">
        <h3 class="surface__panel-title">Secrets</h3>
        <p class="system-muted-copy">Encrypted secret storage. Values are masked by default.</p>
        <div class="system-secrets-actions">
          <button class="system-action-btn" @click="showAddSecret = true">+ Add Secret</button>
          <button class="system-action-btn" @click="importSecretsFromEnv">↳ Import from Env</button>
        </div>
        <div v-if="showAddSecret" class="system-add-secret-form">
          <input v-model="newSecretKey" placeholder="SECRET_NAME" class="system-var-input" />
          <input v-model="newSecretValue" placeholder="secret value" type="password" class="system-var-input" />
          <button class="system-save-btn" @click="addSecret">Save</button>
          <button class="system-edit-btn" @click="showAddSecret = false">Cancel</button>
        </div>
        <div v-if="loadingSecrets" class="system-loading">Loading secrets...</div>
        <div v-else class="system-secrets-list">
          <div v-for="secret in secrets" :key="secret.key" class="system-secret-row">
            <span class="system-secret-key">{{ secret.key }}</span>
            <span class="system-secret-value">{{ revealingSecret === secret.key ? secret.value : '••••••••' }}</span>
            <UBadge type="info" size="sm">{{ secret.scope }}</UBadge>
            <button class="system-edit-btn" @click="toggleRevealSecret(secret.key)">👁</button>
            <button class="system-delete-btn" @click="deleteSecret(secret.key)">✕</button>
          </div>
        </div>
      </div>

      <!-- Global Settings -->
      <div v-else-if="currentTab === 'global-settings'" class="system-panel">
        <h3 class="surface__panel-title">Global Settings</h3>
        <p class="system-muted-copy">Theme, palette, and typography controls. Saved server-side.</p>
        <div class="system-settings-form">
          <div class="settings-row"><label>Theme</label><select v-model="themeSettings.theme"><option>dark</option><option>light</option><option>auto</option></select></div>
          <div class="settings-row"><label>Font Size</label><input type="range" min="12" max="24" v-model.number="themeSettings.fontSize" /><span>{{ themeSettings.fontSize }}px</span></div>
          <div class="settings-row"><label>Palette</label><select v-model="themeSettings.palette"><option>default</option><option>ocean</option><option>forest</option><option>sunset</option></select></div>
        </div>
        <button class="system-action-btn system-save-settings-btn" @click="saveGlobalSettings">Save Global Settings</button>
      </div>

      <!-- User Settings -->
      <div v-else-if="currentTab === 'user-settings'" class="system-panel">
        <h3 class="surface__panel-title">User Settings</h3>
        <p class="system-muted-copy">Your profile and preferences. Saved server-side.</p>
        <div class="system-settings-form">
          <div class="settings-row"><label>Display Name</label><input type="text" v-model="userSettings.displayName" /></div>
          <div class="settings-row"><label>Email</label><input type="email" v-model="userSettings.email" placeholder="user@example.com" /></div>
          <div class="settings-row"><label>Default Model</label><select v-model="userSettings.defaultModel"><option>Llama 3.2</option><option>GPT-4o</option><option>DeepSeek V3</option></select></div>
        </div>
        <button class="system-action-btn system-save-settings-btn" @click="saveUserSettings">Save User Settings</button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import type { TabDef } from '../../skills/molecules/SurfaceTabNav.vue'

export const SYSTEM_TABS: TabDef[] = [
  { id: 'pages', label: 'Pages', icon: 'dashboard' },
  { id: 'services', label: 'Services', icon: 'dns' },
  { id: 'variables', label: 'Variables', icon: 'tune' },
  { id: 'secrets', label: 'Secrets', icon: 'key' },
  { id: 'global-settings', label: 'Global', icon: 'settings' },
  { id: 'user-settings', label: 'User', icon: 'person' },
]
</script>

<script setup lang="ts">
import { computed, ref, reactive, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useShellStore } from '../../stores/shell'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'
import SurfaceTabNav from '../../skills/molecules/SurfaceTabNav.vue'

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'
const route = useRoute()
const router = useRouter()
const shell = useShellStore()

const activeTab = ref((route.query.tab as string) || 'pages')
const currentTab = computed(() => activeTab.value)

// ── Pages ────────────────────────────────────────────────────────
const pageFilter = ref<'all' | 's' | 'p'>('all')
const allPages = ref<Array<{id: string; title: string; icon: string; type: string}>>([])
const filteredPages = computed(() => {
  if (pageFilter.value === 'all') return allPages.value
  return allPages.value.filter(p => p.type === pageFilter.value)
})

function navigateToPage(pageId: string) {
  router.push(`/system/${pageId.toLowerCase()}`)
}

// ── Services ─────────────────────────────────────────────────────
interface ServiceItem { name: string; status: string; description: string; port: number; type: string }
const services = ref<ServiceItem[]>([])
const loadingServices = ref(true)
const servicesSummary = computed(() => {
  const up = services.value.filter(s => s.status === 'up').length
  const degraded = services.value.filter(s => s.status === 'degraded').length
  const down = services.value.filter(s => s.status === 'down').length
  return { up, degraded, down, healthPct: Math.round((up / Math.max(services.value.length, 1)) * 100) }
})

// ── Variables ────────────────────────────────────────────────────
const loadingVars = ref(true)
const userVariables = ref<Record<string, string>>({})
const installVariables = ref<Record<string, string>>({})
const editingVar = ref<string | null>(null)
const editVarValue = ref('')

function startEditVar(key: string, value: string) {
  editingVar.value = key
  editVarValue.value = value
}

async function saveVariable(key: string) {
  try {
    const res = await fetch(`${API_BASE}/api/variables/user`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [key]: editVarValue.value }),
    })
    if (res.ok) {
      userVariables.value[key] = editVarValue.value
    }
  } catch {}
  editingVar.value = null
}

// ── Secrets ──────────────────────────────────────────────────────
interface SecretItem { key: string; scope: string; value: string }
const secrets = ref<SecretItem[]>([])
const loadingSecrets = ref(true)
const revealingSecret = ref<string | null>(null)
const showAddSecret = ref(false)
const newSecretKey = ref('')
const newSecretValue = ref('')

function toggleRevealSecret(key: string) {
  if (revealingSecret.value === key) {
    revealingSecret.value = null
  } else {
    revealingSecret.value = key
  }
}

async function addSecret() {
  const key = newSecretKey.value.trim()
  const value = newSecretValue.value.trim()
  if (!key || !value) return
  try {
    const res = await fetch(`${API_BASE}/api/secrets/${key}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value }),
    })
    if (res.ok) {
      secrets.value.push({ key, scope: 'user', value: '••••••••' })
      newSecretKey.value = ''
      newSecretValue.value = ''
      showAddSecret.value = false
    }
  } catch {}
}

async function deleteSecret(key: string) {
  try {
    const res = await fetch(`${API_BASE}/api/secrets/${key}`, { method: 'DELETE' })
    if (res.ok) {
      secrets.value = secrets.value.filter(s => s.key !== key)
    }
  } catch {}
}

async function importSecretsFromEnv() {
  try {
    await fetch(`${API_BASE}/api/secrets/import-env`, { method: 'POST' })
    await fetchSecrets()
  } catch {}
}

// ── Global Settings ──────────────────────────────────────────────
const themeSettings = reactive({ theme: 'dark', fontSize: 16, palette: 'default' })

async function saveGlobalSettings() {
  try {
    await fetch(`${API_BASE}/api/system/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scope: 'global', values: { ...themeSettings } }),
    })
  } catch {}
}

// ── User Settings ────────────────────────────────────────────────
const userSettings = reactive({ displayName: 'uDos Developer', email: '', defaultModel: 'Llama 3.2' })

async function saveUserSettings() {
  try {
    await fetch(`${API_BASE}/api/system/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scope: 'user', values: { ...userSettings } }),
    })
  } catch {}
}

// ── Data Fetching ────────────────────────────────────────────────
async function fetchPages() {
  try {
    const res = await fetch('/api/system/pages', { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const pages = data.pages || []
      allPages.value = pages.map((p: any) => ({
        id: p.id,
        title: p.title,
        icon: p.icon || 'dashboard',
        type: p.id.startsWith('S') ? 's' : 'p',
      }))
    }
  } catch {}
}

async function fetchServices() {
  loadingServices.value = true
  try {
    const res = await fetch(`${API_BASE}/api/system/services`, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      services.value = (data.services || []).map((s: any) => ({
        name: s.name,
        status: s.status,
        description: s.description || '',
        port: s.port || 0,
        type: s.type || 'system',
      }))
    }
  } catch {}
  loadingServices.value = false
}

async function fetchVariables() {
  loadingVars.value = true
  try {
    const res = await fetch(`${API_BASE}/api/variables`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      userVariables.value = data.user || {}
      installVariables.value = data.installation || {}
    }
  } catch {}
  loadingVars.value = false
}

async function fetchSecrets() {
  loadingSecrets.value = true
  try {
    const res = await fetch(`${API_BASE}/api/secrets`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const list = data.secrets || data || []
      secrets.value = Array.isArray(list)
        ? list.map((s: any) => ({ key: s.key || s.name, scope: s.scope || 'user', value: s.masked || '••••••••' }))
        : []
    }
  } catch {}
  loadingSecrets.value = false
}

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/system/settings`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const settings = data.settings || {}
      if (settings.global) {
        themeSettings.theme = settings.global.theme || 'dark'
        themeSettings.fontSize = settings.global.fontSize || 16
        themeSettings.palette = settings.global.palette || 'default'
      }
      if (settings.user) {
        userSettings.displayName = settings.user.displayName || 'uDos Developer'
        userSettings.email = settings.user.email || ''
        userSettings.defaultModel = settings.user.defaultModel || 'Llama 3.2'
      }
    }
  } catch {}
}

onMounted(() => {
  fetchPages()
  fetchServices()
  fetchVariables()
  fetchSecrets()
  loadSettings()
})

// Persist to localStorage as cache
watch(themeSettings, (v) => { try { localStorage.setItem('ucore-theme-settings', JSON.stringify(v)) } catch {} }, { deep: true })
watch(userSettings, (v) => { try { localStorage.setItem('ucore-user-settings', JSON.stringify(v)) } catch {} }, { deep: true })
</script>

<style scoped>
.surface__content { padding: var(--usx-spacing-lg); }
.surface__panel-title { margin: 0 0 var(--usx-spacing-sm); font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); }
.system-muted-copy { margin: 0 0 var(--usx-spacing-md); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.system-section-title { margin: var(--usx-spacing-md) 0 var(--usx-spacing-xs); font-size: var(--usx-font-size-base); font-weight: var(--usx-font-weight-semibold); }
.system-loading { padding: var(--usx-spacing-lg); text-align: center; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
.system-panel { }

/* Filter */
.system-filter-group { display: flex; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-md); }
.system-filter-btn { padding: var(--usx-spacing-xs) var(--usx-spacing-md); border: 1px solid var(--usx-color-border); background: var(--usx-color-surface); border-radius: var(--usx-radius-sm); color: var(--usx-color-on-surface-muted); cursor: pointer; font-size: var(--usx-font-size-sm); }
.system-filter-btn--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); border-color: var(--usx-color-primary); }

/* Pages */
.system-pages-grid { --system-grid-column-min: calc(var(--usx-touch-min) * 4.5); display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--system-grid-column-min)), 1fr)); gap: var(--usx-spacing-sm); min-width: 0; }
.system-page-card { display: flex; flex-direction: column; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-md); background: var(--usx-color-surface); border-radius: var(--usx-radius-lg); cursor: pointer; transition: background var(--usx-transition-fast), border-color var(--usx-transition-fast), transform var(--usx-transition-fast); border: 1px solid transparent; }
.system-page-card:hover { border-color: var(--usx-color-primary); }
.system-page-id { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-semibold); color: var(--usx-color-primary); }
.system-page-title { font-size: var(--usx-font-size-sm); text-align: center; overflow-wrap: anywhere; }

/* Services */
.system-services-summary { display: flex; gap: var(--usx-spacing-md); margin-bottom: var(--usx-spacing-md); }
.system-stat { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-medium); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); }
.system-stat--up { color: var(--usx-color-success); background: rgba(76, 175, 80, 0.1); }
.system-stat--degraded { color: var(--usx-color-warning); background: rgba(255, 152, 0, 0.1); }
.system-stat--down { color: var(--usx-color-danger); background: rgba(244, 67, 54, 0.1); }
.system-stat--pct { color: var(--usx-color-on-surface-muted); background: var(--usx-color-background); }

.system-services-list { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); }
.system-service-row { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); background: var(--usx-color-background); border-radius: var(--usx-radius-md); }
.system-service-dot { width: var(--usx-spacing-sm); height: var(--usx-spacing-sm); border-radius: 50%; flex-shrink: 0; }
.system-service-dot--up { background: var(--usx-color-success); }
.system-service-dot--degraded { background: var(--usx-color-warning); }
.system-service-dot--down { background: var(--usx-color-danger); }
.system-service-name { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-medium); min-width: 10ch; }
.system-service-desc { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); flex: 1; }

/* Variables */
.system-vars-list { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-md); }
.system-var-row { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); }
.system-var-key { font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-sm); color: var(--usx-color-primary); min-width: 14ch; }
.system-var-value { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); flex: 1; }
.system-var-input { padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--usx-color-background); border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); flex: 1; }

/* Secrets */
.system-secrets-actions { display: flex; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-md); }
.system-action-btn { padding: var(--usx-spacing-xs) var(--usx-spacing-md); background: var(--usx-color-surface); border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); color: var(--usx-color-on-surface); cursor: pointer; font-size: var(--usx-font-size-sm); }
.system-action-btn:hover { background: var(--usx-color-background); }
.system-save-settings-btn { margin-top: var(--usx-spacing-md); }
.system-add-secret-form { display: flex; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-md); padding: var(--usx-spacing-sm); background: var(--usx-color-background); border-radius: var(--usx-radius-md); }
.system-secrets-list { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); }
.system-secret-row { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); }
.system-secret-key { font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-medium); min-width: 14ch; }
.system-secret-value { font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); flex: 1; }

/* Buttons */
.system-edit-btn, .system-save-btn, .system-delete-btn { padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: transparent; border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); cursor: pointer; font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); }
.system-edit-btn:hover, .system-save-btn:hover { color: var(--usx-color-primary); border-color: var(--usx-color-primary); }
.system-delete-btn:hover { color: var(--usx-color-danger); border-color: var(--usx-color-danger); }

/* Settings */
.system-settings-form { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-sm); }
.settings-row { display: flex; align-items: center; gap: var(--usx-spacing-md); padding: var(--usx-spacing-sm) 0; }
.settings-row label { min-width: 12ch; font-size: var(--usx-font-size-sm); }
.settings-row select, .settings-row input[type="text"], .settings-row input[type="email"] { padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--usx-color-background); border-radius: var(--usx-radius-sm); color: var(--usx-color-on-surface); font-size: var(--usx-font-size-sm); border: 1px solid var(--usx-color-border); }
</style>