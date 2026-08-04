<template>
  <div class="system-page">
    <div class="system-page-shell">
      <div class="system-page-header">
        <UIcon :name="displayIcon" class="system-page-header-icon" />
        <h2 class="system-page-title">{{ displayTitle }}</h2>
        <UBadge type="neutral" size="sm">{{ resolvedPageCode }}</UBadge>
      </div>

      <div class="system-page-body">
        <template v-if="isClipboardPage">
          <p class="system-page-note">
            Full clipboard history. Select an item to promote it to the active
            system clipboard.
          </p>

          <div class="clipboard-toolbar">
            <button class="system-page-action" @click="loadClipboardHistory" :disabled="clipboardLoading">
              {{ clipboardLoading ? 'Refreshing…' : 'Refresh' }}
            </button>
            <button class="system-page-action" @click="captureClipboard" :disabled="clipboardLoading">
              Capture Current Clipboard
            </button>
            <button class="system-page-action" @click="clearClipboardHistory" :disabled="clipboardLoading || clipboardItems.length === 0">
              Clear History
            </button>
          </div>

          <p v-if="clipboardMessage" class="clipboard-message">{{ clipboardMessage }}</p>

          <section class="system-fallback-block clipboard-block">
            <div v-if="clipboardLoading" class="clipboard-state">Loading clipboard history…</div>
            <div v-else-if="clipboardItems.length === 0" class="clipboard-state">No clipboard history yet.</div>
            <ul v-else class="clipboard-list">
              <li v-for="item in clipboardItems" :key="item.id" class="clipboard-list-item">
                <div class="clipboard-item-main">
                  <div class="clipboard-item-header">
                    <span class="clipboard-item-source">{{ item.source || 'clipboard' }}</span>
                    <span class="clipboard-item-time">{{ item.timestamp || 'pending' }}</span>
                  </div>
                  <p class="clipboard-item-content">{{ summarizeClipboard(item.content) }}</p>
                </div>
                <div class="clipboard-item-actions">
                  <button class="system-page-action" @click="promoteClipboardItem(item.id)">Use Next Paste</button>
                  <button class="system-page-action" @click="pinClipboardItem(item)">{{ item.pinned ? 'Unpin' : 'Pin' }}</button>
                  <button class="system-page-action" @click="deleteClipboardItem(item.id)">Delete</button>
                </div>
              </li>
            </ul>
          </section>

          <div class="system-actions-row">
            <button class="system-page-action" @click="goBack">Go Back</button>
            <button class="system-page-action" @click="goHome">Home</button>
            <button class="system-page-action" @click="goTo('/server?tab=snacks')">Open SnackMachine</button>
          </div>
        </template>

        <template v-else>
          <h3 class="system-fallback-title">{{ fallbackModel.heading }}</h3>
          <p class="system-page-note">{{ fallbackModel.summary }}</p>

          <section class="system-fallback-block">
            <h4 class="system-fallback-subtitle">What You Can Do</h4>
            <ul class="system-fallback-list">
              <li v-for="step in fallbackModel.steps" :key="step">{{ step }}</li>
            </ul>
          </section>

          <section class="system-fallback-block" v-if="fallbackModel.suggestions.length">
            <h4 class="system-fallback-subtitle">Suggested Pages</h4>
            <div class="system-fallback-links">
              <button
                v-for="suggestion in fallbackModel.suggestions"
                :key="suggestion.label"
                class="system-fallback-link"
                @click="goTo(suggestion.to)"
              >
                {{ suggestion.label }}
              </button>
            </div>
          </section>

          <div class="system-actions-row">
            <button class="system-page-action" @click="goBack">Go Back</button>
            <button class="system-page-action" @click="retry">Retry</button>
            <button class="system-page-action" @click="goHome">Home</button>
            <button class="system-page-action" @click="goTo('/system?tab=pages')">Browse Fallback Pages</button>
          </div>

          <p class="system-fallback-footnote">{{ fallbackModel.footnote }}</p>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'
import { SNACKBAR_BASE } from '../../api/base'

interface PageMeta { id: string; title: string; icon: string }
interface SuggestionLink { label: string; to: string }
interface FallbackModel {
  heading: string
  summary: string
  steps: string[]
  suggestions: SuggestionLink[]
  footnote: string
}

interface ClipboardItem {
  id: string
  content: string
  source: string
  timestamp?: string
  pinned?: boolean
}

const route = useRoute()
const router = useRouter()

const LOCAL_FALLBACK_PAGES: PageMeta[] = [
  { id: 'S100', title: 'Page Not Found', icon: 'search_off' },
  { id: 'S101', title: 'Server Offline', icon: 'cloud_off' },
  { id: 'S300', title: 'Internal Server Error', icon: 'error' },
  { id: 'S310', title: 'Clipboard Full History', icon: 'content_paste' },
  { id: 'S320', title: 'Access Restricted', icon: 'lock' },
  { id: 'S330', title: 'Configuration Missing', icon: 'settings' },
  { id: 'S340', title: 'Dependency Unavailable', icon: 'link_off' },
  { id: 'S600', title: 'Help and Recovery', icon: 'help' },
]

const LEGACY_P_TO_S_ALIAS: Record<string, string> = {
  P001: 'S101',
  P002: 'S330',
  P003: 'S340',
  P004: 'S320',
  P005: 'S300',
}

const pageCode = computed(() => {
  const raw = String(route.params.pageId || '')
  return raw.toUpperCase() || 'S100'
})

const resolvedPageCode = computed(() => LEGACY_P_TO_S_ALIAS[pageCode.value] || pageCode.value)

const pageMeta = computed<PageMeta>(() => {
  const found = LOCAL_FALLBACK_PAGES.find(p => p.id === resolvedPageCode.value)
  if (found) return found
  return {
    id: resolvedPageCode.value,
    title: 'Unknown Fallback Page',
    icon: 'help',
  }
})

const displayTitle = computed(() => pageMeta.value.title)
const displayIcon = computed(() => pageMeta.value.icon)
const isClipboardPage = computed(() => resolvedPageCode.value === 'S310')

const clipboardItems = ref<ClipboardItem[]>([])
const clipboardLoading = ref(false)
const clipboardMessage = ref('')

function summarizeClipboard(content: string) {
  const compact = String(content || '').replace(/\s+/g, ' ').trim()
  if (!compact) return '(empty clipboard item)'
  return compact.length > 120 ? `${compact.slice(0, 120)}...` : compact
}

async function loadClipboardHistory() {
  clipboardLoading.value = true
  clipboardMessage.value = ''
  try {
    const response = await fetch(`${SNACKBAR_BASE}/api/snacks/clipboard?limit=100`)
    if (!response.ok) {
      clipboardMessage.value = `Failed to load clipboard history (${response.status}).`
      clipboardItems.value = []
      return
    }
    const payload = await response.json()
    clipboardItems.value = (payload.items || []) as ClipboardItem[]
  } catch {
    clipboardMessage.value = 'Clipboard history is currently unavailable.'
    clipboardItems.value = []
  } finally {
    clipboardLoading.value = false
  }
}

async function promoteClipboardItem(itemId: string) {
  clipboardMessage.value = ''
  try {
    const response = await fetch(`${SNACKBAR_BASE}/api/snacks/clipboard/${itemId}/paste`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    if (!response.ok) {
      clipboardMessage.value = `Failed to set clipboard item (${response.status}).`
      return
    }
    clipboardMessage.value = 'Clipboard item set for next paste.'
    await loadClipboardHistory()
  } catch {
    clipboardMessage.value = 'Failed to set clipboard item.'
  }
}

async function pinClipboardItem(item: ClipboardItem) {
  clipboardMessage.value = ''
  const desiredPinned = !Boolean(item.pinned)
  try {
    const response = await fetch(`${SNACKBAR_BASE}/api/snacks/clipboard/${item.id}/pin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pinned: desiredPinned }),
    })
    if (!response.ok) {
      clipboardMessage.value = `Failed to update pin state (${response.status}).`
      return
    }
    await loadClipboardHistory()
  } catch {
    clipboardMessage.value = 'Failed to update pin state.'
  }
}

async function deleteClipboardItem(itemId: string) {
  clipboardMessage.value = ''
  try {
    const response = await fetch(`${SNACKBAR_BASE}/api/snacks/clipboard/${itemId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      clipboardMessage.value = `Failed to delete clipboard item (${response.status}).`
      return
    }
    await loadClipboardHistory()
  } catch {
    clipboardMessage.value = 'Failed to delete clipboard item.'
  }
}

async function captureClipboard() {
  clipboardMessage.value = ''
  try {
    const response = await fetch(`${SNACKBAR_BASE}/api/snacks/clipboard/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: 'system-s310' }),
    })
    if (!response.ok) {
      clipboardMessage.value = `Failed to capture clipboard (${response.status}).`
      return
    }
    clipboardMessage.value = 'Captured current clipboard item.'
    await loadClipboardHistory()
  } catch {
    clipboardMessage.value = 'Failed to capture current clipboard.'
  }
}

async function clearClipboardHistory() {
  clipboardMessage.value = ''
  try {
    const response = await fetch(`${SNACKBAR_BASE}/api/snacks/clipboard/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ include_pinned: false }),
    })
    if (!response.ok) {
      clipboardMessage.value = `Failed to clear clipboard history (${response.status}).`
      return
    }
    clipboardMessage.value = 'Clipboard history cleared.'
    await loadClipboardHistory()
  } catch {
    clipboardMessage.value = 'Failed to clear clipboard history.'
  }
}

watch(
  () => resolvedPageCode.value,
  (code) => {
    if (code === 'S310') {
      void loadClipboardHistory()
    }
  },
  { immediate: true },
)

const fallbackModel = computed<FallbackModel>(() => {
  const title = pageMeta.value.title
  const code = resolvedPageCode.value

  if (code === 'S100') {
    return {
      heading: 'Page Not Found',
      summary: `The requested page \"${title}\" is unavailable or no longer exists.`,
      steps: [
        'Use the back button to return to the previous page.',
        'Open the page browser to choose another system page.',
        'If this URL came from a bookmark, update it.',
      ],
      suggestions: [
        { label: 'System Surface', to: '/system' },
        { label: 'Developer Surface', to: '/developer' },
        { label: 'Server Surface', to: '/server' },
      ],
      footnote: 'Error 404. If this persists, verify router paths and page registry configuration.',
    }
  }

  if (code === 'S101') {
    return {
      heading: 'Server Offline',
      summary: 'The backend service is not responding right now.',
      steps: [
        'Confirm the backend process is running on port 8484.',
        'Check backend logs for startup or import errors.',
        'Retry after the service reports healthy status.',
      ],
      suggestions: [
        { label: 'System Services', to: '/system?tab=services' },
        { label: 'Server Surface', to: '/server' },
      ],
      footnote: 'Error 503. This fallback is local and available without backend data.',
    }
  }

  if (code === 'S300') {
    return {
      heading: 'Internal Server Error',
      summary: 'A request failed due to an unexpected backend error.',
      steps: [
        'Retry the request after a short pause.',
        'Check backend logs for tracebacks near the request time.',
        'If reproducible, capture the route and report it.',
      ],
      suggestions: [
        { label: 'System Services', to: '/system?tab=services' },
        { label: 'Home', to: '/' },
      ],
      footnote: 'Error 500. If repeated, investigate app logs and recent deploy changes.',
    }
  }

  if (code === 'S310') {
    return {
      heading: 'Clipboard Full History',
      summary: 'Browse and manage clipboard history from the system surfaces area.',
      steps: [
        'Refresh to load the latest captured clipboard items.',
        'Use Next Paste to promote any item into the active clipboard.',
        'Pin important snippets to protect them from cleanup operations.',
      ],
      suggestions: [
        { label: 'SnackMachine', to: '/server?tab=snacks' },
        { label: 'System Pages', to: '/system?tab=pages' },
      ],
      footnote: 'Clipboard orchestration surface.',
    }
  }

  if (code === 'S320') {
    return {
      heading: 'Access Restricted',
      summary: 'You do not have permission to access this operation.',
      steps: [
        'Check role and environment permissions.',
        'Confirm required secrets and tokens are configured.',
        'Retry after access policy changes are applied.',
      ],
      suggestions: [
        { label: 'System Secrets', to: '/system?tab=secrets' },
        { label: 'System Settings', to: '/system?tab=user-settings' },
      ],
      footnote: 'Error 403. This page provides static remediation guidance only.',
    }
  }

  if (code === 'S330') {
    return {
      heading: 'Configuration Missing',
      summary: 'Required configuration was not found or is incomplete.',
      steps: [
        'Validate files under config and user runtime config directories.',
        'Restore missing keys from example configuration files.',
        'Restart backend after configuration updates.',
      ],
      suggestions: [
        { label: 'System Settings', to: '/system?tab=global-settings' },
        { label: 'Developer Surface', to: '/developer' },
      ],
      footnote: 'Configuration fallback. This page is intentionally local-first.',
    }
  }

  if (code === 'S340') {
    return {
      heading: 'Dependency Unavailable',
      summary: 'An external dependency is unavailable or failed to respond.',
      steps: [
        'Check service health and dependency ports.',
        'Verify required processes are installed and running.',
        'Retry after the dependency recovers.',
      ],
      suggestions: [
        { label: 'System Services', to: '/system?tab=services' },
        { label: 'Server Surface', to: '/server' },
      ],
      footnote: 'Dependency fallback. No live dependency introspection is required to render this page.',
    }
  }

  if (code === 'S600') {
    return {
      heading: 'Help and Recovery',
      summary: 'Use this page when you are unsure how to recover from a failure.',
      steps: [
        'Start with System Services to confirm baseline health.',
        'Review logs and recent changes before retrying operations.',
        'Escalate with a concise error summary and reproduction path.',
      ],
      suggestions: [
        { label: 'System Surface', to: '/system' },
        { label: 'Documentation', to: '/documentation' },
      ],
      footnote: 'Recovery guidance page. Designed to stay useful even when backend endpoints fail.',
    }
  }

  return {
    heading: 'Fallback Page',
    summary: `No local fallback template is defined for \"${title}\" (${code}).`,
    steps: [
      'Return to the page browser.',
      'Use known system fallback pages.',
      'Add a local template for this page code if needed.',
    ],
    suggestions: [
      { label: 'Browse Fallback Pages', to: '/system?tab=pages' },
      { label: 'Home', to: '/' },
    ],
    footnote: 'Unknown fallback template.',
  }
})

function goTo(target: string) {
  router.push(target)
}

function goBack() {
  if (window.history.length > 1) {
    window.history.back()
    return
  }
  router.push('/system?tab=pages')
}

function retry() {
  window.location.reload()
}

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.system-page {
  padding: var(--usx-spacing-xl);
  display: flex;
  justify-content: center;
}
.system-page-shell {
  width: 100%;
  max-width: 900px;
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: var(--usx-color-surface);
  padding: var(--usx-spacing-xl);
}
.system-page-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-lg);
  text-align: center;
}
.system-page-header-icon { font-size: var(--usx-font-size-2xl); }
.system-page-title { margin: 0; font-size: var(--usx-font-size-xl); font-weight: var(--usx-font-weight-semibold); }
.system-page-note { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-base); margin: 0; text-align: center; }
.system-page-body {
  margin-top: var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  align-items: center;
}
.system-fallback-title { margin: 0; font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); color: var(--usx-color-on-surface); text-align: center; }
.system-fallback-block { border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-md); background: var(--usx-color-surface); padding: var(--usx-spacing-md); }
.system-fallback-subtitle { margin: 0 0 var(--usx-spacing-sm); font-size: var(--usx-font-size-sm); font-weight: var(--usx-font-weight-semibold); color: var(--usx-color-on-surface); text-align: center; }
.system-fallback-block { width: 100%; max-width: 720px; }
.system-fallback-list { margin: 0; padding-left: var(--usx-spacing-lg); display: flex; flex-direction: column; gap: var(--usx-spacing-xs); color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); }
.system-fallback-links { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-sm); justify-content: center; }
.system-fallback-link { border: 1px solid var(--usx-color-border); background: var(--usx-color-background); color: var(--usx-color-on-surface); border-radius: var(--usx-radius-sm); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); cursor: pointer; font-size: var(--usx-font-size-sm); }
.system-fallback-link:hover { border-color: var(--usx-color-primary); color: var(--usx-color-primary); }
.system-actions-row { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-sm); justify-content: center; }
.system-page-action { padding: var(--usx-spacing-xs) var(--usx-spacing-md); border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); cursor: pointer; font-size: var(--usx-font-size-sm); }
.system-page-action:hover { border-color: var(--usx-color-primary); color: var(--usx-color-primary); }
.system-fallback-footnote { margin: 0; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); text-align: center; }
</style>
