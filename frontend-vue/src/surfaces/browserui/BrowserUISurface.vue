<template>
  <div class="surface">
    <div class="surface__content browserui-shell">
      <SurfaceTabNav
        :tabs="TABS"
        :model-value="activeTab"
        orientation="horizontal"
        @update:model-value="switchTab"
      />

      <div v-if="activeTab === 'cards'" class="browserui-body">
        <section class="browserui-canvas">
          <div class="browserui-toolbar" :class="`browserui-toolbar--group-${groupBy}`">
            <div class="surface__panel browserui-panel">
              <div class="browserui-panel__header">
                <h3 class="surface__panel-title">Browser</h3>
                <div class="browserui-panel__badges">
                  <UBadge type="info" size="sm">Cards Explorer</UBadge>
                  <UBadge type="success" size="sm">Vault-backed</UBadge>
                </div>
              </div>
              <p class="surface__panel-description">
                Search, group, and enrich cards with mission-control style controls.
              </p>
              <div class="browserui-actions-row">
                <button class="uxs-btn" @click="resetControls">
                  <UIcon name="refresh" /> Reset
                </button>
                <button
                  v-if="hasActiveFilters"
                  class="uxs-btn"
                  @click="resetControls"
                >
                  <UIcon name="filter_alt_off" /> Clear filters
                </button>
                <button
                  v-if="batchSelected.length"
                  class="uxs-btn uxs-btn--primary"
                  @click="batchResearch"
                >
                  <UIcon name="science" /> Research {{ batchSelected.length }}
                </button>
              </div>
            </div>

            <div class="browserui-stats">
              <div class="browserui-stat">
                <span class="browserui-stat__value">{{ filteredSortedCards.length }}</span>
                <span class="browserui-stat__label">Visible Cards</span>
              </div>
              <div class="browserui-stat">
                <span class="browserui-stat__value browserui-stat__value--info">{{ displayedGroups.length }}</span>
                <span class="browserui-stat__label">Columns</span>
              </div>
              <div class="browserui-stat">
                <span class="browserui-stat__value browserui-stat__value--warning">{{ selectedTags.length }}</span>
                <span class="browserui-stat__label">Topic Filters</span>
              </div>
              <div class="browserui-stat">
                <span class="browserui-stat__value browserui-stat__value--success">{{ batchSelected.length }}</span>
                <span class="browserui-stat__label">Selected</span>
              </div>
            </div>

            <div class="browserui-section">
              <h4 class="browserui-section__title">Search Controls</h4>
              <div class="browserui-toolbar__row browserui-toolbar__row--primary">
                <div class="browserui-search">
                  <UInput v-model="searchQuery" placeholder="Search titles, tags, topics..." icon="search" />
                </div>

                <div class="browserui-toolbar__controls">
                  <div class="browserui-combo">
                    <span class="browserui-combo__prefix">Sort</span>
                    <select v-model="sortKey" class="browserui-select browserui-select--combo">
                      <option value="relevance">Relevance</option>
                      <option value="score">Score</option>
                      <option value="title">Title</option>
                    </select>
                  </div>

                  <div class="browserui-combo">
                    <span class="browserui-combo__prefix">Group</span>
                    <select v-model="groupBy" class="browserui-select browserui-select--combo">
                      <option value="stack">Stack</option>
                      <option value="topic">Topic</option>
                      <option value="score">Score</option>
                      <option value="custom">Custom Group</option>
                    </select>
                  </div>

                  <div class="browserui-combo">
                    <span class="browserui-combo__prefix">Layout</span>
                    <select v-model="density" class="browserui-select browserui-select--combo">
                      <option value="stacked">Stacked</option>
                      <option value="comfortable">Comfortable</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div class="browserui-section">
              <h4 class="browserui-section__title">Topics and Grouping</h4>
              <div class="browserui-toolbar__row browserui-toolbar__row--secondary">
                <div class="browserui-pillrail" aria-label="topic tags">
                  <button
                    v-for="tag in allTags"
                    :key="tag"
                    class="browserui-pill"
                    :class="{ 'browserui-pill--active': selectedTags.includes(tag) }"
                    @click="toggleTagFilter(tag)"
                  >
                    {{ tag }}
                  </button>
                </div>

                <div class="browserui-resultsbar">
                  <span class="browserui-resultsbar__text">
                    {{ filteredSortedCards.length }} cards in {{ displayedGroups.length }} columns
                  </span>
                </div>

                <div class="browserui-batch-tools">
                  <div class="browserui-quickadd">
                    <div class="browserui-mini-input-wrap">
                      <UInput v-model="newTag" placeholder="Tag topic" icon="sell" />
                    </div>
                    <button
                      class="uxs-btn uxs-btn--icon"
                      title="Add topic tag"
                      aria-label="Add topic tag"
                      @click="addTagToSelection"
                    >
                      <UIcon name="add" />
                    </button>
                  </div>

                  <div class="browserui-quickadd">
                    <div class="browserui-mini-input-wrap">
                      <UInput v-model="newGroup" placeholder="Group topic" icon="folder" />
                    </div>
                    <button
                      class="uxs-btn uxs-btn--icon"
                      title="Add topic group"
                      aria-label="Add topic group"
                      @click="addGroupToSelection"
                    >
                      <UIcon name="add" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="displayedGroups.length === 0" class="browserui-empty">
            <UIcon name="filter_alt_off" />
            <h3>{{ stacks.length ? "No cards match the current filters" : "No research cards yet" }}</h3>
            <p>{{ stacks.length ? "Try clearing filters or adjusting search/group settings." : "Save research to your vault or add a bookmark to begin." }}</p>
            <button class="uxs-btn" @click="resetControls">
              <UIcon name="refresh" /> Reset filters
            </button>
          </div>

          <div v-else class="browserui-kanban">
            <article v-for="column in displayedGroups" :key="column.id" class="browserui-column">
              <header class="browserui-column__header">
                <div class="browserui-column__title">
                  <UIcon :name="column.icon" />
                  <h3>{{ column.title }}</h3>
                </div>
                <span class="browserui-column__count">{{ column.items.length }}</span>
              </header>

              <div
                class="browserui-column__cards"
                :class="{
                  'browserui-column__cards--stacked': density === 'stacked',
                  'browserui-column__cards--comfortable': density === 'comfortable',
                }"
              >
                <article
                  v-for="card in column.items"
                  :key="`${column.id}-${card.id}`"
                  class="browserui-card"
                  :class="{
                    'browserui-card--active': selectedCard?.id === card.id,
                    'browserui-card--selected': batchSelected.includes(card.id),
                  }"
                  @click="selectCard(card)"
                >
                  <div class="browserui-card__top">
                    <input
                      type="checkbox"
                      class="browserui-card__check"
                      :checked="batchSelected.includes(card.id)"
                      @click.stop
                      @change="toggleBatch(card.id, $event)"
                    />
                    <span
                      v-if="card.score !== undefined"
                      class="browserui-card__score"
                      :class="scoreColor(card.score)"
                    >
                      {{ card.score }}
                    </span>
                    <span class="browserui-card__title">{{ card.title }}</span>
                  </div>

                  <p class="browserui-card__desc">{{ card.description }}</p>

                  <div class="browserui-card__tags">
                    <span v-for="tag in card.tags" :key="`${card.id}-${tag}`" class="browserui-card__tag">
                      {{ tag }}
                    </span>
                    <span
                      v-for="group in card.groups || []"
                      :key="`${card.id}-group-${group}`"
                      class="browserui-card__tag browserui-card__tag--group"
                    >
                      @{{ group }}
                    </span>
                  </div>

                  <div class="browserui-card__actions">
                    <button class="uxs-btn uxs-btn--sm" @click.stop="handleResearchCard(card)">
                      Research
                    </button>
                    <button class="uxs-btn uxs-btn--sm" @click.stop="enhanceCard(card)">
                      Enhance
                    </button>
                  </div>
                </article>
              </div>
            </article>
          </div>
        </section>

        <aside v-if="selectedCard" class="browserui-editor">
          <PreviewTab
            v-if="editorMode === 'preview'"
            :content="editorContent"
            :meta="editorMeta"
            @edit="editorMode = 'edit'"
            @chatui="sendToChatUI"
          />
          <EditTab
            v-else
            :content="editorContent"
            :title="selectedCard?.title"
            :tags="selectedCard?.tags"
            :binder="selectedCard?.binder"
            @preview="editorMode = 'preview'"
            @save="saveToBinder"
          />
          <button class="browserui-editor-close" @click="closeEditor">
            <UIcon name="close" />
          </button>
        </aside>
      </div>

      <ResearchDashboard
        v-if="activeTab === 'dashboard'"
        :jobs="researchJobs"
        :gaps="researchGaps"
        @approve="approveJob"
        @startResearch="startResearchJob"
        @fillGap="fillResearchGap"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue"
import { useRouter } from "vue-router"
import UInput from "../../skills/atoms/UInput.vue"
import UIcon from "../../skills/atoms/UIcon.vue"
import UBadge from "../../skills/atoms/UBadge.vue"
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue"
import PreviewTab from "./panels/PreviewTab.vue"
import EditTab from "./panels/EditTab.vue"
import ResearchDashboard from "./panels/ResearchDashboard.vue"
import { useChatStore } from "../../stores/chat"
import { useWorkflowStore } from "../../stores/workflow"
import { addBinder, fetchScrape, listResearchJobs, startResearch } from "./ApiBridge"

interface StackItem {
  id: string
  title: string
  url?: string
  description: string
  tags: string[]
  score?: number
  binder?: string
  groups?: string[]
}

interface Stack {
  id: string
  title: string
  icon: string
  items: StackItem[]
}

interface DisplayCard extends StackItem {
  stackId: string
  stackTitle: string
  stackIcon: string
}

interface DisplayGroup {
  id: string
  title: string
  icon: string
  items: DisplayCard[]
}

interface KnowledgeDocument {
  id: string
  title: string
  rel_path?: string
  workspace_id?: string
  source?: string
  permissions?: string
}

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || "http://localhost:8484"
const SESSION_KEY = "browserui-session-v3"

const router = useRouter()
const wf = useWorkflowStore()
const chat = useChatStore()

const activeTab = ref<"cards" | "dashboard">("cards")
const searchQuery = ref("")
const selectedCard = ref<DisplayCard | null>(null)
const editorMode = ref<"preview" | "edit">("preview")
const editorContent = ref("")
const editorMeta = ref<{ source?: string; score?: number; tags?: string[]; title?: string }>({})

const sortKey = ref<"relevance" | "score" | "title">("relevance")
const groupBy = ref<"stack" | "topic" | "score" | "custom">("stack")
const density = ref<"stacked" | "comfortable">("stacked")
const selectedTags = ref<string[]>([])

const newTag = ref("")
const newGroup = ref("")
const customTopics = ref<string[]>([])
const customGroups = ref<string[]>([])

const stacks = ref<Stack[]>([])
const researchJobs = ref<any[]>([])
const researchGaps = ref<any[]>([])
const researchContent = ref<Record<string, string>>({})
const batchSelected = ref<string[]>([])
const sessionCardMeta = ref<Record<string, { tags: string[]; groups: string[] }>>({})

const TABS = [
  { id: "cards", label: "Cards", icon: "dashboard" },
  { id: "dashboard", label: "Research", icon: "science" },
]

function normalizeTag(value: string): string {
  const cleaned = value.trim().toLowerCase().replace(/\s+/g, "-")
  if (!cleaned) return ""
  return cleaned.startsWith("#") ? cleaned : `#${cleaned}`
}

function normalizeGroup(value: string): string {
  return value.trim().replace(/\s+/g, " ")
}

function scoreColor(score: number | undefined): string {
  if (score === undefined) return ""
  if (score >= 4) return "browserui-score--high"
  if (score >= 2) return "browserui-score--mid"
  return "browserui-score--low"
}

function flattenCards(): DisplayCard[] {
  return stacks.value.flatMap((stack) =>
    stack.items.map((item) => ({
      ...item,
      groups: item.groups || [],
      stackId: stack.id,
      stackTitle: stack.title,
      stackIcon: stack.icon,
    })),
  )
}

const allTags = computed(() => {
  const tags = new Set<string>(customTopics.value)
  for (const card of flattenCards()) {
    for (const tag of card.tags) tags.add(tag)
  }
  return [...tags].sort((a, b) => a.localeCompare(b))
})

function pruneSelectedTags() {
  if (selectedTags.value.length === 0) return
  const available = new Set(allTags.value)
  selectedTags.value = selectedTags.value.filter((tag) => available.has(tag))
}

function relevanceScore(card: DisplayCard, q: string): number {
  if (!q) return card.score ?? 0
  let score = 0
  const query = q.toLowerCase()
  if (card.title.toLowerCase().includes(query)) score += 5
  if (card.description.toLowerCase().includes(query)) score += 3
  if (card.tags.some((tag) => tag.toLowerCase().includes(query))) score += 2
  return score + (card.score ?? 0)
}

const filteredSortedCards = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  const activeTagFilters = selectedTags.value

  const filtered = flattenCards().filter((card) => {
    const matchesTag = activeTagFilters.length === 0 || activeTagFilters.some((tag) => card.tags.includes(tag))
    const matchesQuery =
      !q ||
      card.title.toLowerCase().includes(q) ||
      card.description.toLowerCase().includes(q) ||
      card.tags.some((tag) => tag.toLowerCase().includes(q)) ||
      (card.groups || []).some((group) => group.toLowerCase().includes(q))
    return matchesTag && matchesQuery
  })

  filtered.sort((a, b) => {
    if (sortKey.value === "score") return (b.score ?? 0) - (a.score ?? 0)
    if (sortKey.value === "title") return a.title.localeCompare(b.title)
    return relevanceScore(b, q) - relevanceScore(a, q)
  })

  return filtered
})

const displayedGroups = computed<DisplayGroup[]>(() => {
  const cards = filteredSortedCards.value
  const map = new Map<string, DisplayGroup>()

  const addToGroup = (id: string, title: string, icon: string, card: DisplayCard) => {
    const existing = map.get(id)
    if (existing) {
      existing.items.push(card)
      return
    }
    map.set(id, { id, title, icon, items: [card] })
  }

  for (const card of cards) {
    if (groupBy.value === "stack") {
      addToGroup(card.stackId, card.stackTitle, card.stackIcon, card)
      continue
    }

    if (groupBy.value === "topic") {
      const tags = card.tags.length ? card.tags : ["#untagged"]
      for (const tag of tags) addToGroup(`topic-${tag}`, tag, "sell", card)
      continue
    }

    if (groupBy.value === "score") {
      if ((card.score ?? -1) >= 4) addToGroup("score-high", "High Score", "trending_up", card)
      else if ((card.score ?? -1) >= 2) addToGroup("score-mid", "Mid Score", "equalizer", card)
      else if ((card.score ?? -1) >= 0) addToGroup("score-low", "Low Score", "south", card)
      else addToGroup("score-unrated", "Unrated", "help", card)
      continue
    }

    const groups = card.groups && card.groups.length ? card.groups : ["Ungrouped"]
    for (const group of groups) addToGroup(`group-${group}`, group, "folder", card)
  }

  return [...map.values()].sort((a, b) => b.items.length - a.items.length || a.title.localeCompare(b.title))
})

const hasActiveFilters = computed(() => {
  return (
    searchQuery.value.trim().length > 0 ||
    selectedTags.value.length > 0 ||
    sortKey.value !== "relevance" ||
    groupBy.value !== "stack"
  )
})

function toggleBatch(id: string, event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  if (checked) {
    batchSelected.value = [...new Set([...batchSelected.value, id])]
  } else {
    batchSelected.value = batchSelected.value.filter((existing) => existing !== id)
  }
}

function mutateSelectedCards(mutator: (item: StackItem) => StackItem) {
  if (batchSelected.value.length === 0) return
  const selected = new Set(batchSelected.value)
  stacks.value = stacks.value.map((stack) => ({
    ...stack,
    items: stack.items.map((item) => (selected.has(item.id) ? mutator(item) : item)),
  }))
}

function toggleTagFilter(tag: string) {
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter((t) => t !== tag)
    return
  }
  selectedTags.value = [...selectedTags.value, tag]
}

function addTagToSelection() {
  const tag = normalizeTag(newTag.value)
  if (!tag) return

  if (!customTopics.value.includes(tag)) {
    customTopics.value = [...customTopics.value, tag]
  }

  mutateSelectedCards((item) => {
    const tags = item.tags.includes(tag) ? item.tags : [...item.tags, tag]
    return { ...item, tags }
  })

  newTag.value = ""
}

function addGroupToSelection() {
  const group = normalizeGroup(newGroup.value)
  if (!group) return

  if (!customGroups.value.includes(group)) {
    customGroups.value = [...customGroups.value, group]
  }

  mutateSelectedCards((item) => {
    const groups = item.groups || []
    const nextGroups = groups.includes(group) ? groups : [...groups, group]
    return { ...item, groups: nextGroups }
  })

  newGroup.value = ""
}

function selectCard(card: DisplayCard) {
  selectedCard.value = card
  editorContent.value = researchContent.value[card.id] || card.description
  editorMeta.value = { source: card.url, score: card.score, tags: card.tags, title: card.title }
}

function closeEditor() {
  selectedCard.value = null
  editorMode.value = "preview"
}

function resetControls() {
  searchQuery.value = ""
  selectedTags.value = []
  sortKey.value = "relevance"
  groupBy.value = "stack"
  batchSelected.value = []
}

function switchTab(tab: string) {
  if (tab === "cards" || tab === "dashboard") {
    activeTab.value = tab
  }
}

function applySessionMeta() {
  if (!Object.keys(sessionCardMeta.value).length) return
  stacks.value = stacks.value.map((stack) => ({
    ...stack,
    items: stack.items.map((item) => {
      const saved = sessionCardMeta.value[item.id]
      if (!saved) return { ...item, groups: item.groups || [] }
      return {
        ...item,
        tags: saved.tags.length ? saved.tags : item.tags,
        groups: saved.groups,
      }
    }),
  }))
}

async function fetchKnowledgeStacks(): Promise<Stack[]> {
  try {
    const res = await fetch(`${API_BASE}/api/knowledge/documents`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) return []
    const data = await res.json()
    const documents: KnowledgeDocument[] = Array.isArray(data?.documents) ? data.documents : []
    const byWorkspace = new Map<string, StackItem[]>()
    for (const document of documents) {
      const workspace = document.workspace_id || document.source || "knowledge"
      const items = byWorkspace.get(workspace) || []
      items.push({
        id: document.id,
        title: document.title || document.rel_path || "Untitled note",
        description: document.rel_path || "Markdown knowledge note",
        tags: ["#knowledge", normalizeTag(workspace), normalizeTag(document.permissions || "read")],
        groups: [workspace],
      })
      byWorkspace.set(workspace, items)
    }
    return [...byWorkspace.entries()].map(([workspace, items]) => ({
      id: `knowledge-${workspace}`,
      title: workspace === "main" ? "Main Vault" : workspace,
      icon: workspace === "public" ? "public" : "folder_managed",
      items,
    }))
  } catch {
    return []
  }
}

async function fetchBookmarks() {
  const knowledgeStacks = await fetchKnowledgeStacks()

  try {
    const res = await fetch(`${API_BASE}/api/knowledge?type=bookmark`, {
      signal: AbortSignal.timeout(5000),
    })
    if (res.ok) {
      const data = await res.json()
      const raw = data.items || data || []
      const items: StackItem[] = raw.map((bookmark: any) => ({
        id: bookmark.id || bookmark.url,
        title: bookmark.title || bookmark.name || "Untitled",
        url: bookmark.url || bookmark.link || "",
        description: bookmark.description || bookmark.summary || "",
        tags: (bookmark.tags || bookmark.keywords || []).map((tag: string) => normalizeTag(tag)).filter(Boolean),
        groups: [],
      }))
      if (items.length) {
        stacks.value = [{ id: "bookmarks", title: "Bookmarks", icon: "bookmark", items }, ...knowledgeStacks]
        applySessionMeta()
        pruneSelectedTags()
        return
      }
    }
  } catch {
    // backend offline
  }

  stacks.value = knowledgeStacks
  applySessionMeta()
  pruneSelectedTags()
}

async function handleResearchCard(card: DisplayCard | StackItem) {
  try {
    const tags = card.tags?.length ? card.tags : ["#research"]
    const response = await startResearch(card.url ?? "", tags[0].replace("#", ""), tags, "full")
    researchJobs.value.unshift({
      id: response.job_id || "0",
      url: card.url ?? "",
      binder: "research",
      state: "pending",
      progress: 0,
    })
  } catch {
    // backend offline
  }
}

async function enhanceCard(card: DisplayCard | StackItem) {
  try {
    const scraped = await fetchScrape(card.url ?? "")
    if (!scraped) return
    const nextText = scraped.text || scraped.description || card.description
    researchContent.value = { ...researchContent.value, [card.id]: nextText }
    if (selectedCard.value?.id === card.id) {
      editorContent.value = nextText
      editorMeta.value = {
        source: card.url,
        score: card.score,
        tags: card.tags,
        title: scraped.title || card.title,
      }
    }
  } catch {
    // backend offline
  }
}

async function batchResearch() {
  const selected = new Set(batchSelected.value)
  const cards = flattenCards().filter((card) => selected.has(card.id))
  for (const card of cards) {
    await handleResearchCard(card)
  }
  batchSelected.value = []
}

function sendToChatUI() {
  chat.sendMessage(
    `Research this topic and provide a structured plan:\n\nTitle: ${editorMeta.value.title || ""}\nSource: ${editorMeta.value.source || ""}\n\nContent:\n${editorContent.value.slice(0, 2000)}`,
  )
}

async function saveToBinder(payload: { title: string; content: string; tags: string[] }) {
  try {
    await addBinder(payload.title, payload.content.slice(0, 500), payload.tags)
  } catch {
    // backend offline
  }

  const filename = `${payload.title || "research-note"}.md`.toLowerCase().replace(/\s+/g, "-")
  const content = `---\ntitle: "${payload.title || ""}"\ndate: "${new Date().toISOString().slice(0, 10)}"\n---\n\n${payload.content}`

  wf.selectFile({
    id: `research-${Date.now()}`,
    path: `/research/${filename}`,
    filename,
    extension: "md",
    binder: "Research",
    content,
    readOnly: false,
  })

  router.push({ path: "/workflow", query: { tab: "editor" } })
}

async function hydrateResearchJobs() {
  try {
    const jobs = await listResearchJobs()
    if (jobs.length) researchJobs.value = jobs
  } catch {
    // backend offline
  }
}

async function detectKnowledgeGaps() {
  try {
    const res = await fetch(`${API_BASE}/api/research/vault-scan`, {
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) return
    const data = await res.json()
    researchGaps.value = data.gaps || []
  } catch {
    // backend offline
  }
}

function approveJob(job: any) {
  if (job?.url) {
    const card: StackItem = {
      id: `job-${job.id || Date.now()}`,
      title: job.url,
      url: job.url,
      description: "Approved research job",
      tags: (job.tags || ["#research"]).map((tag: string) => normalizeTag(tag)),
      groups: [],
    }
    handleResearchCard(card)
  }
}

function startResearchJob(payload: { url: string; binder?: string; tags?: string[]; mode?: string }) {
  const card: StackItem = {
    id: `dash-${Date.now()}`,
    title: payload.url,
    url: payload.url,
    description: "Research from dashboard",
    tags: (payload.tags || ["#research"]).map((tag) => normalizeTag(tag)),
    groups: payload.binder ? [payload.binder] : [],
  }
  return handleResearchCard(card)
}

function fillResearchGap(gap: any) {
  activeTab.value = "cards"
  const query = gap?.query || gap?.topic || gap?.title || ""
  searchQuery.value = String(query)
}

function saveSession() {
  const cardMeta: Record<string, { tags: string[]; groups: string[] }> = {}
  for (const stack of stacks.value) {
    for (const item of stack.items) {
      cardMeta[item.id] = {
        tags: item.tags,
        groups: item.groups || [],
      }
    }
  }

  localStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      searchQuery: searchQuery.value,
      selectedTags: selectedTags.value,
      sortKey: sortKey.value,
      groupBy: groupBy.value,
      density: density.value,
      customTopics: customTopics.value,
      customGroups: customGroups.value,
      researchJobs: researchJobs.value.slice(0, 50),
      cardMeta,
    }),
  )
}

function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return
    const data = JSON.parse(raw)

    searchQuery.value = data.searchQuery || ""
    selectedTags.value = data.selectedTags || []
    sortKey.value = data.sortKey || "relevance"
    groupBy.value = data.groupBy || "stack"
    density.value = data.density || "stacked"
    customTopics.value = data.customTopics || []
    customGroups.value = data.customGroups || []
    researchJobs.value = data.researchJobs || []
    sessionCardMeta.value = data.cardMeta || {}
  } catch {
    // ignore malformed session data
  }
}

watch(
  [searchQuery, selectedTags, sortKey, groupBy, density, customTopics, customGroups, researchJobs, stacks],
  () => saveSession(),
  { deep: true },
)

onMounted(async () => {
  loadSession()
  await fetchBookmarks()
  await Promise.all([hydrateResearchJobs(), detectKnowledgeGaps()])
})
</script>

<style scoped>
.browserui-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: 0;
  overflow: hidden;

  --browserui-toolbar-text-size: var(--usx-font-size-sm);
  --browserui-toolbar-label-size: var(--usx-font-size-xs);
  --browserui-toolbar-prefix-size: var(--browserui-toolbar-text-size);
  --browserui-toolbar-control-height: var(--usx-control-size-sm);
  --browserui-toolbar-prefix-width: calc(var(--usx-touch-target-comfortable) * 1.45);
  --browserui-toolbar-combo-width: calc(var(--usx-touch-target-comfortable) * 3.15);
  --browserui-toolbar-pill-height: calc(var(--usx-control-size-sm) - var(--usx-spacing-xs));
  --browserui-toolbar-row-gap: var(--usx-spacing-sm);
  --browserui-toolbar-inline-gap: var(--usx-spacing-sm);
  --browserui-toolbar-panel-padding: var(--usx-spacing-sm);
  --browserui-toolbar-search-max-width: calc(var(--usx-touch-target-comfortable) * 7);
}

.browserui-body {
  display: flex;
  position: relative;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.browserui-canvas {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md) var(--usx-spacing-md);
}

.browserui-toolbar {
  display: grid;
  gap: var(--usx-spacing-md);
  position: relative;
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin-bottom: var(--usx-spacing-sm);
}

.browserui-toolbar__row {
  display: grid;
  align-items: stretch;
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.browserui-toolbar__row--primary {
  grid-template-columns: minmax(0, auto) minmax(0, 1fr);
}

.browserui-toolbar__row--secondary {
  grid-template-columns: minmax(0, 1fr) auto auto;
}

.browserui-toolbar__row--secondary {
  margin-top: 0;
}

.browserui-panel {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--usx-color-primary) 3%, transparent) 0%,
    transparent 20%
  );
}

.browserui-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-md);
  flex-wrap: wrap;
}

.browserui-panel__badges {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.browserui-actions-row {
  display: flex;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--usx-spacing-sm);
}

.browserui-stats {
  --browserui-stat-column-min: calc(var(--usx-touch-min) * 3.75);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, var(--browserui-stat-column-min)), 1fr));
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.browserui-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-lg);
  min-width: 12ch;
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.browserui-stat__value {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
  line-height: var(--usx-line-height-tight);
  color: var(--usx-color-on-surface);
}

.browserui-stat__label {
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
}

.browserui-stat__value--success {
  color: var(--usx-color-success);
}

.browserui-stat__value--info {
  color: var(--usx-color-primary);
}

.browserui-stat__value--warning {
  color: var(--usx-color-warning);
}

.browserui-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 var(--usx-border-width-thick) 0
    color-mix(in srgb, var(--usx-color-border) 35%, transparent);
}

.browserui-section__title {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: none;
  letter-spacing: normal;
  padding-bottom: var(--usx-spacing-xs);
  border-bottom: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-border) 70%, transparent);
}

.browserui-search {
  width: min(100%, var(--browserui-toolbar-search-max-width));
  min-width: 0;
}

.browserui-toolbar__controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--browserui-toolbar-inline-gap);
  justify-content: flex-start;
  min-width: 0;
}

.browserui-field {
  display: grid;
  grid-auto-flow: column;
  align-items: center;
  gap: var(--browserui-toolbar-inline-gap);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--browserui-toolbar-text-size);
  font-family: var(--usx-font-family-sans);
  font-weight: var(--usx-font-weight-medium);
  white-space: nowrap;
}

.browserui-field__label {
  font-size: var(--browserui-toolbar-label-size);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-tight);
}

.browserui-combo {
  display: inline-flex;
  align-items: stretch;
  flex: 0 0 var(--browserui-toolbar-combo-width);
  width: var(--browserui-toolbar-combo-width);
  height: var(--browserui-toolbar-control-height);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: color-mix(in srgb, var(--usx-color-surface) 92%, var(--usx-color-surface-variant));
  overflow: hidden;
}

.browserui-combo__prefix {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  flex: 0 0 var(--browserui-toolbar-prefix-width);
  min-width: var(--browserui-toolbar-prefix-width);
  max-width: var(--browserui-toolbar-prefix-width);
  width: var(--browserui-toolbar-prefix-width);
  height: 100%;
  padding: 0 var(--usx-spacing-sm);
  font-size: var(--browserui-toolbar-prefix-size);
  font-family: var(--usx-font-family-sans);
  font-weight: var(--usx-font-weight-medium);
  line-height: var(--usx-line-height-tight);
  color: var(--usx-color-on-surface-muted);
  background: color-mix(in srgb, var(--usx-color-surface-variant) 72%, var(--usx-color-surface));
  border-right: var(--usx-border-width) solid var(--usx-color-border);
  white-space: nowrap;
}

.browserui-select {
  appearance: none;
  -webkit-appearance: none;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background:
    linear-gradient(45deg, transparent 50%, var(--usx-color-on-surface-muted) 50%) calc(100% - var(--usx-spacing-sm)) calc(50% - 1px) / 6px 6px no-repeat,
    linear-gradient(135deg, var(--usx-color-on-surface-muted) 50%, transparent 50%) calc(100% - var(--usx-spacing-xs)) calc(50% - 1px) / 6px 6px no-repeat,
    color-mix(in srgb, var(--usx-color-surface) 92%, var(--usx-color-surface-variant));
  color: var(--usx-color-on-surface);
  min-height: var(--browserui-toolbar-control-height);
  min-width: calc(var(--usx-touch-target-comfortable) * 1.6);
  padding: 0 var(--usx-spacing-xl) 0 var(--usx-spacing-sm);
  font-size: var(--browserui-toolbar-text-size);
  font-family: var(--usx-font-family-sans);
  font-weight: var(--usx-font-weight-medium);
  line-height: var(--usx-line-height-tight);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--usx-color-surface) 85%, transparent);
}

.browserui-select--combo {
  flex: 1 1 auto;
  height: 100%;
  min-height: 0;
  min-width: 0;
  border: none;
  border-radius: 0;
  font-size: var(--browserui-toolbar-prefix-size);
  line-height: var(--usx-line-height-tight);
  background:
    linear-gradient(45deg, transparent 50%, var(--usx-color-on-surface-muted) 50%) calc(100% - var(--usx-spacing-sm)) calc(50% - 1px) / 6px 6px no-repeat,
    linear-gradient(135deg, var(--usx-color-on-surface-muted) 50%, transparent 50%) calc(100% - var(--usx-spacing-xs)) calc(50% - 1px) / 6px 6px no-repeat,
    transparent;
}

.browserui-toolbar :deep(.u-input__field) {
  min-height: var(--browserui-toolbar-control-height);
  font-size: var(--browserui-toolbar-text-size);
}

.browserui-select:focus {
  outline: none;
  border-color: color-mix(in srgb, var(--usx-color-primary) 56%, transparent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--usx-color-primary) 22%, transparent);
}

.browserui-combo:focus-within {
  border-color: color-mix(in srgb, var(--usx-color-primary) 56%, transparent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--usx-color-primary) 22%, transparent);
}

.browserui-pillrail {
  display: flex;
  align-items: center;
  gap: var(--browserui-toolbar-inline-gap);
  overflow-x: auto;
  overflow-y: hidden;
  padding: var(--usx-spacing-xs) 0;
  min-width: 0;
}

.browserui-resultsbar {
  display: flex;
  align-items: center;
  gap: var(--browserui-toolbar-inline-gap);
  justify-content: center;
  min-height: var(--usx-touch-target-compact);
}

.browserui-resultsbar__text {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--browserui-toolbar-label-size);
  font-family: var(--usx-font-family-sans);
  white-space: nowrap;
}

.browserui-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  border-radius: var(--usx-radius-full);
  min-height: var(--browserui-toolbar-pill-height);
  padding: 0 var(--usx-spacing-sm);
  font-size: var(--browserui-toolbar-text-size);
  line-height: var(--usx-line-height-tight);
  cursor: pointer;
  white-space: nowrap;
}

.browserui-pill--active {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.browserui-batch-tools {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: center;
  gap: var(--browserui-toolbar-inline-gap);
  min-width: 0;
}

.browserui-quickadd {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--browserui-toolbar-inline-gap);
  min-width: 0;
}

.browserui-mini-input-wrap {
  min-width: 0;
  width: 100%;
}

.browserui-mini-input-wrap :deep(.u-input__field) {
  width: 100%;
}

.browserui-kanban {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 22rem), 1fr));
  gap: var(--usx-spacing-xl);
  align-items: start;
}

.browserui-empty {
  display: grid;
  justify-items: center;
  text-align: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xl);
  border: var(--usx-border-width) dashed var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-surface) 96%, var(--usx-color-background));
}

.browserui-empty :deep(.material-symbols-outlined) {
  font-size: var(--usx-font-size-xl);
  color: var(--usx-color-on-surface-muted);
}

.browserui-empty h3 {
  margin: 0;
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface);
}

.browserui-empty p {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.browserui-column {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  background: color-mix(in srgb, var(--usx-color-surface) 95%, var(--usx-color-background));
  padding: var(--usx-spacing-lg);
  min-height: var(--usx-touch-target-comfortable);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-lg);
  box-shadow: 0 1px 0 color-mix(in srgb, var(--usx-color-border) 60%, transparent);
}

.browserui-column__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--usx-spacing-sm);
  padding: 0 0 var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid color-mix(in srgb, var(--usx-color-border) 75%, transparent);
}

.browserui-column__title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.browserui-column__title :deep(.material-symbols-outlined) {
  font-size: var(--usx-font-size-lg);
  color: var(--usx-color-primary);
}

.browserui-column__title h3 {
  margin: 0;
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  line-height: var(--usx-line-height-tight);
  letter-spacing: var(--usx-letter-spacing-tight);
  white-space: normal;
  overflow-wrap: anywhere;
}

.browserui-column__count {
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  min-width: var(--usx-touch-target-compact);
  min-height: var(--usx-touch-target-compact);
  padding: 0 var(--usx-spacing-xs);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--usx-color-surface-variant) 65%, var(--usx-color-surface));
}

.browserui-column__cards {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: stretch;
  min-height: 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: var(--usx-spacing-xs);
  scroll-snap-type: x proximity;
}

.browserui-column__cards--stacked {
  gap: var(--usx-spacing-md);
}

.browserui-column__cards--comfortable {
  gap: var(--usx-spacing-lg);
}

.browserui-card {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  padding: var(--usx-spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  cursor: pointer;
  flex: 0 0 min(100%, 24rem);
  width: min(100%, 24rem);
  min-height: calc(var(--usx-touch-target-comfortable) * 2.4);
  transition: border-color var(--usx-transition-fast), transform var(--usx-transition-fast), box-shadow var(--usx-transition-fast);
  scroll-snap-align: start;
}

.browserui-card:hover {
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-xs) * -0.2));
  box-shadow: 0 var(--usx-border-width-thick) var(--usx-spacing-sm)
    color-mix(in srgb, var(--usx-color-primary) 18%, transparent);
}

.browserui-card--active {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 8%, var(--usx-color-surface));
}

.browserui-card--selected {
  box-shadow: 0 0 0 var(--usx-border-width) color-mix(in srgb, var(--usx-color-primary) 45%, transparent);
}

.browserui-card__top {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-xs);
}

.browserui-card__check {
  accent-color: var(--usx-color-primary);
}

.browserui-card__title {
  flex: 1;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  line-height: var(--usx-line-height-tight);
  overflow-wrap: anywhere;
}

.browserui-card__desc {
  margin: 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-normal);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.browserui-card__score {
  border-radius: var(--usx-radius-full);
  padding: 0 var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
}

.browserui-score--high {
  background: color-mix(in srgb, var(--usx-color-success) 20%, transparent);
  color: var(--usx-color-success);
}

.browserui-score--mid {
  background: color-mix(in srgb, var(--usx-color-warning) 20%, transparent);
  color: var(--usx-color-warning);
}

.browserui-score--low {
  background: color-mix(in srgb, var(--usx-color-info) 20%, transparent);
  color: var(--usx-color-info);
}

.browserui-card__tags {
  display: flex;
  gap: var(--usx-spacing-xs) var(--usx-spacing-sm);
  flex-wrap: wrap;
  margin-top: var(--usx-spacing-xs);
}

.browserui-card__tag {
  border-radius: var(--usx-radius-full);
  padding: 0 var(--usx-spacing-xs);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  font-size: var(--usx-font-size-xs);
  line-height: var(--usx-line-height-normal);
}

.browserui-card__tag--group {
  color: var(--usx-color-info);
}

.browserui-card__actions {
  display: flex;
  gap: var(--usx-spacing-xs);
  margin-top: auto;
  padding-top: var(--usx-spacing-xs);
}

@media (max-width: 1400px) {
  .browserui-toolbar__row--primary,
  .browserui-toolbar__row--secondary {
    grid-template-columns: 1fr;
  }

  .browserui-toolbar__controls,
  .browserui-batch-tools,
  .browserui-resultsbar {
    width: 100%;
  }
}

.uxs-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  min-height: var(--usx-touch-target-compact);
  padding: 0 var(--usx-spacing-sm);
  cursor: pointer;
  background: color-mix(in srgb, var(--usx-color-surface) 94%, var(--usx-color-surface-variant));
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
}

.uxs-btn:hover {
  background: var(--usx-color-surface-variant);
}

.uxs-btn--primary {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

.uxs-btn--sm {
  min-height: calc(var(--usx-touch-target-compact) - var(--usx-spacing-xs));
  padding: 0 var(--usx-spacing-xs);
}

.uxs-btn--icon {
  width: var(--usx-touch-target-compact);
  min-width: var(--usx-touch-target-compact);
  padding: 0;
}

.browserui-editor {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(50vw, 90ch);
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 var(--usx-spacing-lg) color-mix(in srgb, var(--usx-color-on-surface) 18%, transparent);
  z-index: 10;
  overflow-y: auto;
}

@media (min-width: 1600px) {
  .browserui-kanban {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.browserui-editor-close {
  position: absolute;
  top: var(--usx-spacing-sm);
  right: var(--usx-spacing-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-target-compact);
  height: var(--usx-touch-target-compact);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  z-index: 1;
}

.browserui-editor-close:hover {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

@media (max-width: 900px) {
  .browserui-body {
    flex-direction: column;
  }

  .browserui-toolbar__row {
    grid-template-columns: 1fr;
    align-items: start;
  }

  .browserui-resultsbar {
    justify-self: start;
    width: 100%;
    justify-content: flex-start;
  }

  .browserui-toolbar__controls,
  .browserui-batch-tools {
    grid-auto-flow: row;
    grid-auto-columns: 1fr;
    justify-content: stretch;
    width: 100%;
  }

  .browserui-field {
    grid-template-columns: auto 1fr;
  }

  .browserui-combo {
    width: 100%;
  }

  .browserui-select--combo {
    min-width: 0;
    width: 100%;
  }

  .browserui-select,
  .browserui-mini-input-wrap {
    width: 100%;
    max-width: none;
  }

  .browserui-batch-tools {
    grid-template-columns: 1fr;
  }

  .browserui-column__cards {
    scroll-snap-type: none;
  }

  .browserui-card {
    flex-basis: min(100%, 20rem);
    width: min(100%, 20rem);
  }

  .browserui-editor {
    position: fixed;
    top: auto;
    left: 0;
    right: 0;
    bottom: 0;
    width: auto;
    max-height: 70vh;
    border-left: none;
    border-top: var(--usx-border-width) solid var(--usx-color-border);
  }
}
</style>
