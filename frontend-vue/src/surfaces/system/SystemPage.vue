<template>
  <div class="system-page">
    <div class="system-page-header">
      <UIcon :name="pageMeta.icon || 'dashboard'" class="system-page-header-icon" />
      <h2 class="system-page-title">{{ pageMeta.title || pageCode }}</h2>
      <UBadge type="neutral" size="sm">{{ pageCode }}</UBadge>
    </div>

    <div v-if="pageMeta" class="system-page-body">
      <p class="system-page-note">{{ pageMeta.description || 'System page content renders here.' }}</p>

      <div v-if="resolvedPageCode.startsWith('S')" class="system-s-page-content">
        <div v-if="loading" class="system-loading">Loading page data...</div>
        <div v-else>
          <p v-if="loadError" class="system-page-note">{{ loadError }}</p>

          <div v-if="summaryCards.length" class="system-summary-grid">
            <article v-for="card in summaryCards" :key="card.label" class="system-summary-card">
              <span class="system-summary-label">{{ card.label }}</span>
              <span class="system-summary-value">{{ card.value }}</span>
            </article>
          </div>

          <div v-if="detailItems.length" class="system-details-list">
            <article v-for="item in detailItems" :key="item.title" class="system-detail-row">
              <span class="system-detail-title">{{ item.title }}</span>
              <span class="system-detail-meta">{{ item.meta }}</span>
            </article>
          </div>

          <div v-if="actions.length" class="system-actions-row">
            <button
              v-for="action in actions"
              :key="action.label"
              class="system-page-action"
              @click="navigate(action.to)"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="system-page-body">
      <p class="system-page-note">Unknown page: {{ pageCode }}. Not found in S-pages registry.</p>
      <router-link to="/system?tab=pages" class="system-page-back-link">← Back to Pages Browser</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { SNACKBAR_BASE } from '../../api/base'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

const API_BASE = SNACKBAR_BASE
const route = useRoute()
const router = useRouter()

interface PageMeta { id: string; title: string; icon: string; description?: string }
interface SummaryCard { label: string; value: string }
interface DetailItem { title: string; meta: string }
interface ActionLink { label: string; to: string }

// e.g. /system/s100 -> S100
const pageCode = computed(() => {
  const raw = String(route.params.pageId || '')
  return raw.toUpperCase() || 'UNKNOWN'
})

const LEGACY_P_TO_S_ALIAS: Record<string, string> = {
  P001: 'S340',
  P002: 'S340',
  P003: 'S340',
  P004: 'S340',
  P005: 'S340',
}

const resolvedPageCode = computed(() => LEGACY_P_TO_S_ALIAS[pageCode.value] || pageCode.value)

const LOCAL_FALLBACK_PAGES: PageMeta[] = [
  { id: 'S100', title: 'Tool Builder', icon: 'build' },
  { id: 'S101', title: 'Story Builder', icon: 'auto_stories' },
  { id: 'S300', title: 'Workflow Builder', icon: 'account_tree' },
  { id: 'S340', title: 'Operations Console', icon: 'tune' },
  { id: 'S310', title: 'Clipboard Orchestration', icon: 'content_paste' },
  { id: 'S320', title: 'Knowledge Tools', icon: 'psychology' },
  { id: 'S330', title: 'Migration Dashboard', icon: 'migration' },
  { id: 'S600', title: 'Learning Hub', icon: 'school' },
]
const pageMeta = ref<PageMeta | null>(null)
const loading = ref(false)
const loadError = ref('')
const summaryCards = ref<SummaryCard[]>([])
const detailItems = ref<DetailItem[]>([])
const actions = ref<ActionLink[]>([])

function applyPageMeta(pages: PageMeta[]) {
  const found = pages.find(p => p.id.toUpperCase() === resolvedPageCode.value)
  if (!found) return false
  pageMeta.value = {
    ...found,
    description: found.description || `${found.id} - ${found.title} system page.`,
  }
  return true
}

function navigate(to: string) {
  router.push(to)
}

async function safeGet(path: string) {
  try {
    const res = await fetch(`${API_BASE}${path}`, { signal: AbortSignal.timeout(4000) })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

function setContent(cards: SummaryCard[], items: DetailItem[], links: ActionLink[]) {
  summaryCards.value = cards
  detailItems.value = items
  actions.value = links
}

async function loadS100ToolBuilder() {
  const [skills, tools, mcp] = await Promise.all([
    safeGet('/api/skills'),
    safeGet('/api/tools'),
    safeGet('/api/mcp/tools'),
  ])
  const skillCount = Number(skills?.count || 0)
  const toolCount = Number(tools?.count || 0)
  const mcpCount = Number(mcp?.count || 0)
  const topSkills = (skills?.skills || []).slice(0, 5).map((s: any) => s.name || s.id)
  setContent(
    [
      { label: 'Skills', value: String(skillCount) },
      { label: 'System Tools', value: String(toolCount) },
      { label: 'MCP Tools', value: String(mcpCount) },
    ],
    topSkills.length
      ? topSkills.map((name: string) => ({ title: name, meta: 'Available skill' }))
      : [{ title: 'No skills discovered', meta: 'Check skills registry health' }],
    [
      { label: 'Open Developer Skills', to: '/developer?tab=skills' },
      { label: 'Open MCP Servers', to: '/developer?tab=mcp' },
    ],
  )
}

async function loadS101StoryBuilder() {
  const [prompts, docs, workspaces] = await Promise.all([
    safeGet('/api/chat/prompts'),
    safeGet('/api/knowledge/documents'),
    safeGet('/api/knowledge/workspaces'),
  ])
  const promptCount = Array.isArray(prompts) ? prompts.length : Number(prompts?.count || 0)
  const docCount = Number(docs?.count || 0)
  const workspaceCount = Number(workspaces?.count || 0)
  const recentDocs = (docs?.documents || []).slice(0, 5).map((d: any) => d.name || d.title || d.object_id)
  setContent(
    [
      { label: 'Prompt Templates', value: String(promptCount) },
      { label: 'Knowledge Docs', value: String(docCount) },
      { label: 'Workspaces', value: String(workspaceCount) },
    ],
    recentDocs.length
      ? recentDocs.map((name: string) => ({ title: name, meta: 'Recent document' }))
      : [{ title: 'No documents listed', meta: 'Connect AppFlowy or sync sources' }],
    [
      { label: 'Open Assistant', to: '/assistui' },
      { label: 'Open Documentation', to: '/documentation' },
    ],
  )
}

async function loadS300WorkflowBuilder() {
  const [workflows, runs] = await Promise.all([
    safeGet('/api/workflows'),
    safeGet('/api/workflows/runs?limit=8'),
  ])
  const wfList = workflows?.workflows || []
  const runList = runs?.runs || []
  const completed = runList.filter((r: any) => r.status === 'completed').length
  const failed = runList.filter((r: any) => r.status === 'failed').length
  setContent(
    [
      { label: 'Workflows', value: String(wfList.length || workflows?.count || 0) },
      { label: 'Recent Runs', value: String(runList.length || runs?.count || 0) },
      { label: 'Completed', value: String(completed) },
      { label: 'Failed', value: String(failed) },
    ],
    runList.length
      ? runList.slice(0, 6).map((run: any) => ({
          title: run.workflow_name || run.workflow_id || run.id || 'Workflow run',
          meta: `status=${run.status || 'unknown'}`,
        }))
      : [{ title: 'No workflow runs yet', meta: 'Run a workflow to populate history' }],
    [
      { label: 'Open Workflow Surface', to: '/workflow' },
      { label: 'Open SnackMachine Workflows', to: '/snackmachine?tab=workflows' },
    ],
  )
}

async function loadS310Clipboard() {
  const clipboard = await safeGet('/api/snacks/clipboard?limit=12')
  const items = clipboard?.items || []
  const pinned = items.filter((item: any) => Boolean(item.pinned)).length
  setContent(
    [
      { label: 'Clipboard Items', value: String(clipboard?.count || items.length || 0) },
      { label: 'Pinned', value: String(pinned) },
    ],
    items.length
      ? items.slice(0, 8).map((item: any) => ({
          title: item.content ? String(item.content).slice(0, 48) : item.id || 'Clipboard item',
          meta: `${item.source || 'clipboard'}${item.pinned ? ' | pinned' : ''}`,
        }))
      : [{ title: 'Clipboard is empty', meta: 'Capture or save clipboard entries' }],
    [
      { label: 'Open SnackMachine', to: '/snackmachine' },
      { label: 'Open System Surface', to: '/system?tab=services' },
    ],
  )
}

async function loadS320Knowledge() {
  const [workspaces, docs] = await Promise.all([
    safeGet('/api/knowledge/workspaces'),
    safeGet('/api/knowledge/documents'),
  ])
  const wsList = workspaces?.workspaces || []
  const docList = docs?.documents || []
  setContent(
    [
      { label: 'Workspaces', value: String(workspaces?.count || wsList.length || 0) },
      { label: 'Documents', value: String(docs?.count || docList.length || 0) },
    ],
    wsList.length
      ? wsList.slice(0, 6).map((ws: any) => ({ title: ws.name || ws.id || 'Workspace', meta: ws.id || 'id unavailable' }))
      : [{ title: 'No workspaces found', meta: 'Configure AppFlowy connection' }],
    [
      { label: 'Open Documentation', to: '/documentation' },
      { label: 'Open Developer MCP', to: '/developer?tab=mcp' },
    ],
  )
}

async function loadS330Migration() {
  const [coverage, imports] = await Promise.all([
    safeGet('/api/knowledge/index/coverage'),
    safeGet('/api/knowledge/import/status'),
  ])
  const coverageRows = coverage?.coverage || []
  const jobs = imports?.jobs || []
  const coveragePct = coverage?.coverage_pct ?? 0
  setContent(
    [
      { label: 'Coverage', value: `${coveragePct}%` },
      { label: 'Indexed Docs', value: String(coverage?.total_docs || 0) },
      { label: 'Import Jobs', value: String(jobs.length) },
    ],
    coverageRows.length
      ? coverageRows.slice(0, 6).map((row: any) => ({
          title: row.source || 'source',
          meta: `${row.indexed || 0}/${row.expected || 0} indexed (${row.coverage_percent || 0}%)`,
        }))
      : [{ title: 'No coverage rows', meta: 'Run index or import operations' }],
    [
      { label: 'Open Workflow', to: '/workflow' },
      { label: 'Open Server', to: '/server?tab=services' },
    ],
  )
}

async function loadS340Operations() {
  const [services, variables, secrets, settings] = await Promise.all([
    safeGet('/api/system/services'),
    safeGet('/api/variables'),
    safeGet('/api/secrets'),
    safeGet('/api/system/settings'),
  ])
  const svcList = services?.services || []
  const up = svcList.filter((svc: any) => svc.status === 'up').length
  const degraded = svcList.filter((svc: any) => svc.status === 'degraded').length
  const down = svcList.filter((svc: any) => svc.status === 'down').length
  setContent(
    [
      { label: 'Services Up', value: String(up) },
      { label: 'Degraded', value: String(degraded) },
      { label: 'Down', value: String(down) },
      { label: 'Variables', value: String(Object.keys(variables?.user || {}).length) },
      { label: 'Secrets', value: String(secrets?.count || 0) },
      { label: 'Theme', value: String(settings?.settings?.global?.theme || 'unknown') },
    ],
    svcList.length
      ? svcList.slice(0, 8).map((svc: any) => ({
          title: svc.name || 'service',
          meta: `${svc.status || 'unknown'} | port ${svc.port || 0}`,
        }))
      : [{ title: 'No services listed', meta: 'Check service registry and health paths' }],
    [
      { label: 'Open System Services', to: '/system?tab=services' },
      { label: 'Open Server Surface', to: '/server?tab=dashboard' },
    ],
  )
}

async function loadS600Learning() {
  const [skills, workflows, docs] = await Promise.all([
    safeGet('/api/skills'),
    safeGet('/api/workflows'),
    safeGet('/api/knowledge/documents'),
  ])
  const skillCount = Number(skills?.count || 0)
  const workflowCount = Number(workflows?.count || 0)
  const docCount = Number(docs?.count || 0)
  setContent(
    [
      { label: 'Skills Catalog', value: String(skillCount) },
      { label: 'Workflow Templates', value: String(workflowCount) },
      { label: 'Knowledge Docs', value: String(docCount) },
    ],
    [
      { title: 'Start here: System -> Services', meta: 'Validate runtime health before editing flows' },
      { title: 'Then: Workflow Surface', meta: 'Run and inspect mission workflows' },
      { title: 'Then: Developer -> MCP', meta: 'Audit available tools and capability groups' },
    ],
    [
      { label: 'Open Workflow', to: '/workflow' },
      { label: 'Open Developer', to: '/developer' },
    ],
  )
}

async function loadPageContent() {
  summaryCards.value = []
  detailItems.value = []
  actions.value = []
  loadError.value = ''
  loading.value = true

  try {
    if (resolvedPageCode.value === 'S100') {
      await loadS100ToolBuilder()
    } else if (resolvedPageCode.value === 'S101') {
      await loadS101StoryBuilder()
    } else if (resolvedPageCode.value === 'S300') {
      await loadS300WorkflowBuilder()
    } else if (resolvedPageCode.value === 'S310') {
      await loadS310Clipboard()
    } else if (resolvedPageCode.value === 'S320') {
      await loadS320Knowledge()
    } else if (resolvedPageCode.value === 'S330') {
      await loadS330Migration()
    } else if (resolvedPageCode.value === 'S340') {
      await loadS340Operations()
    } else if (resolvedPageCode.value === 'S600') {
      await loadS600Learning()
    } else {
      setContent([], [{ title: 'No page model registered', meta: `Code ${resolvedPageCode.value}` }], [])
    }
  } catch {
    loadError.value = 'Failed to load system page data from backend endpoints.'
  } finally {
    loading.value = false
  }
}

async function fetchPageMeta() {
  try {
    const res = await fetch(`${API_BASE}/api/system/pages`, { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      const pages: PageMeta[] = data.pages || []
      if (applyPageMeta(pages)) return
    }
  } catch {}

  applyPageMeta(LOCAL_FALLBACK_PAGES)
}

onMounted(async () => {
  await fetchPageMeta()
  await loadPageContent()
})

watch(resolvedPageCode, async () => {
  await fetchPageMeta()
  await loadPageContent()
})
</script>

<style scoped>
.system-page { padding: var(--usx-spacing-xl); max-width: 900px; }
.system-page-header { display: flex; align-items: center; gap: var(--usx-spacing-md); margin-bottom: var(--usx-spacing-lg); }
.system-page-header-icon { font-size: var(--usx-font-size-2xl); }
.system-page-title { margin: 0; font-size: var(--usx-font-size-xl); font-weight: var(--usx-font-weight-semibold); }
.system-page-note { color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-base); }
.system-page-body { margin-top: var(--usx-spacing-md); }
.system-loading { padding: var(--usx-spacing-md); color: var(--usx-color-on-surface-muted); }
.system-summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-md); }
.system-summary-card { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-sm); border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-md); background: var(--usx-color-surface); }
.system-summary-label { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.system-summary-value { font-size: var(--usx-font-size-lg); font-weight: var(--usx-font-weight-semibold); color: var(--usx-color-on-surface); }
.system-details-list { display: flex; flex-direction: column; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-md); }
.system-detail-row { display: flex; align-items: center; justify-content: space-between; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); background: var(--usx-color-background); border: 1px solid var(--usx-color-border); }
.system-detail-title { font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface); overflow-wrap: anywhere; }
.system-detail-meta { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.system-actions-row { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-sm); }
.system-page-action { padding: var(--usx-spacing-xs) var(--usx-spacing-md); border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); cursor: pointer; font-size: var(--usx-font-size-sm); }
.system-page-action:hover { border-color: var(--usx-color-primary); color: var(--usx-color-primary); }
.system-page-back-link { display: inline-block; margin-top: var(--usx-spacing-md); color: var(--usx-color-primary); font-size: var(--usx-font-size-sm); text-decoration: none; }
.system-page-back-link:hover { text-decoration: underline; }
</style>