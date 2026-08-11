<template>
  <div class="surface">
    <div class="surface__content browserui-shell">
      <div class="browserui-tabs">
        <button
          v-for="tab in TABS"
          :key="tab.id"
          class="browserui-tab"
          :class="{ 'browserui-tab--active': activeTab === tab.id }"
          @click="switchTab(tab.id)"
        >
          <UIcon :name="tab.icon" />{{ tab.label }}
        </button>
      </div>

      <div v-if="activeTab === 'cards'" class="browserui-body">
        <section class="browserui-canvas">
          <div class="browserui-toolbar">
            <div class="browserui-toolbar__row browserui-toolbar__row--primary">
              <div class="browserui-search">
                <UInput v-model="searchQuery" placeholder="Search titles, tags, topics..." icon="search" />
              </div>

              <div class="browserui-toolbar__controls">
                <label class="browserui-select-wrap">
                  <span>Sort</span>
                  <select v-model="sortKey" class="browserui-select">
                    <option value="relevance">Relevance</option>
                    <option value="score">Score</option>
                    <option value="title">Title</option>
                  </select>
                </label>

                <label class="browserui-select-wrap">
                  <span>Group</span>
                  <select v-model="groupBy" class="browserui-select">
                    <option value="stack">Stack</option>
                    <option value="topic">Topic</option>
                    <option value="score">Score</option>
                    <option value="custom">Custom Group</option>
                  </select>
                </label>

                <label class="browserui-select-wrap">
                  <span>Layout</span>
                  <select v-model="density" class="browserui-select">
                    <option value="stacked">Stacked</option>
                    <option value="comfortable">Comfortable</option>
                  </select>
                </label>

                <button class="uxs-btn" @click="resetControls">
                  <UIcon name="refresh" /> Reset
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

              <div class="browserui-batch-tools">
                <div class="browserui-mini-input-wrap">
                  <UInput v-model="newTag" placeholder="Add topic tag" icon="sell" />
                </div>
                <button class="uxs-btn" @click="addTagToSelection">
                  <UIcon name="add" /> Tag {{ batchSelected.length || "topic" }}
                </button>

                <div class="browserui-mini-input-wrap">
                  <UInput v-model="newGroup" placeholder="Add group" icon="folder" />
                </div>
                <button class="uxs-btn" @click="addGroupToSelection">
                  <UIcon name="add" /> Group {{ batchSelected.length || "topic" }}
                </button>
              </div>
            </div>
          </div>

          <div class="browserui-kanban">
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

const DEFAULT_STACKS: Stack[] = [
  {
    id: "research",
    title: "Research",
    icon: "search",
    items: [
      {
        id: "r1",
        title: "MCP Protocol Spec",
        url: "https://modelcontextprotocol.io",
        description: "Official MCP specification",
        tags: ["#mcp", "#protocol"],
      },
      {
        id: "r2",
        title: "Vue 3 Docs",
        url: "https://vuejs.org",
        description: "Vue 3 framework documentation",
        tags: ["#vue", "#frontend"],
      },
      {
        id: "r3",
        title: "Rust Async Book",
        url: "https://rust-lang.github.io/async-book/",
        description: "Async Rust guide",
        tags: ["#rust", "#async"],
      },
    ],
  },
  {
    id: "bookmarks",
    title: "Bookmarks",
    icon: "bookmark",
    items: [
      {
        id: "b1",
        title: "GitHub Copilot Docs",
        url: "https://docs.github.com/en/copilot",
        description: "Copilot documentation",
        tags: ["#tools", "#ai"],
      },
      {
        id: "b2",
        title: "MDN Web Docs",
        url: "https://developer.mozilla.org",
        description: "Web platform reference",
        tags: ["#reference", "#web"],
      },
      {
        id: "b3",
        title: "Docker Compose Docs",
        url: "https://docs.docker.com/compose/",
        description: "Multi-container apps",
        tags: ["#docker", "#devops"],
      },
      {
        id: "b4",
        title: "Tailwind CSS Docs",
        url: "https://tailwindcss.com/docs",
        description: "Utility-first CSS",
        tags: ["#css", "#frontend"],
      },
    ],
  },
  {
    id: "learning",
    title: "Learning",
    icon: "school",
    items: [
      {
        id: "l1",
        title: "Pinia Docs",
        url: "https://pinia.vuejs.org",
        description: "Vue state management",
        tags: ["#vue", "#state"],
      },
      {
        id: "l2",
        title: "Vite Docs",
        url: "https://vitejs.dev",
        description: "Next-gen frontend tooling",
        tags: ["#build", "#frontend"],
      },
      {
        id: "l3",
        title: "CodeMirror 6",
        url: "https://codemirror.net",
        description: "Code editor component",
        tags: ["#editor", "#code"],
      },
    ],
  },
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
    const matchesTag = activeTagFilters.length === 0 || activeTagFilters.every((tag) => card.tags.includes(tag))
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
  activeTab.value = tab as "cards" | "dashboard"
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

async function fetchBookmarks() {
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
        stacks.value = [{ id: "bookmarks", title: "Bookmarks", icon: "bookmark", items }]
        applySessionMeta()
        return
      }
    }
  } catch {
    // backend offline
  }

  stacks.value = DEFAULT_STACKS.map((stack) => ({
    ...stack,
    items: stack.items.map((item) => ({ ...item, groups: item.groups || [] })),
  }))
  applySessionMeta()
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
  padding: 0;
  overflow: hidden;
}

.browserui-tabs {
  display: flex;
  gap: 0;
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
  background: var(--usx-color-surface);
}

.browserui-tab {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: transparent;
  border: none;
  border-bottom: var(--usx-border-width-thick) solid transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  transition: color var(--usx-transition-fast), border-color var(--usx-transition-fast);
}

.browserui-tab:hover {
  color: var(--usx-color-on-surface);
}

.browserui-tab--active {
  color: var(--usx-color-primary);
  border-bottom-color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-semibold);
}

.browserui-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.browserui-canvas {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: var(--usx-spacing-md);
}

.browserui-toolbar {
  position: relative;
  background: linear-gradient(
    to bottom,
    color-mix(in srgb, var(--usx-color-surface) 96%, transparent),
    color-mix(in srgb, var(--usx-color-surface) 86%, transparent)
  );
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-md);
}

.browserui-toolbar__row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.browserui-toolbar__row--secondary {
  margin-top: var(--usx-spacing-sm);
}

.browserui-search {
  flex: 1;
  min-width: 0;
}

.browserui-toolbar__controls {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  flex-wrap: wrap;
}

.browserui-select-wrap {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.browserui-select {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
}

.browserui-pillrail {
  display: flex;
  gap: var(--usx-spacing-xs);
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: var(--usx-spacing-xs);
  min-width: 0;
  flex: 1;
}

.browserui-pill {
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  border-radius: var(--usx-radius-full);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
  white-space: nowrap;
}

.browserui-pill--active {
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.browserui-batch-tools {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.browserui-mini-input-wrap {
  min-width: var(--usx-touch-target-comfortable);
  max-width: calc(var(--usx-touch-target-comfortable) * 2.5);
}

.browserui-kanban {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 26ch), 1fr));
  gap: var(--usx-spacing-md);
  align-items: start;
}

.browserui-column {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: color-mix(in srgb, var(--usx-color-surface) 95%, var(--usx-color-background));
  padding: var(--usx-spacing-sm);
  min-height: var(--usx-touch-target-comfortable);
}

.browserui-column__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--usx-spacing-sm);
}

.browserui-column__title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  min-width: 0;
}

.browserui-column__title h3 {
  margin: 0;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.browserui-column__count {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  font-family: var(--usx-font-family-mono);
}

.browserui-column__cards {
  display: flex;
  flex-direction: column;
}

.browserui-column__cards--stacked {
  gap: var(--usx-spacing-xs);
}

.browserui-column__cards--stacked .browserui-card + .browserui-card {
  margin-top: calc(var(--usx-spacing-xs) * -1);
}

.browserui-column__cards--comfortable {
  gap: var(--usx-spacing-sm);
}

.browserui-card {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface);
  padding: var(--usx-spacing-sm);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  cursor: pointer;
  transition: border-color var(--usx-transition-fast), transform var(--usx-transition-fast);
}

.browserui-card:hover {
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-xs) * -0.2));
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
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.browserui-card__check {
  accent-color: var(--usx-color-primary);
}

.browserui-card__title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  overflow-wrap: anywhere;
}

.browserui-card__desc {
  margin: 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  line-height: var(--usx-line-height-normal);
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
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
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
}

.uxs-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  cursor: pointer;
  background: var(--usx-color-surface);
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
  padding: 0 var(--usx-spacing-sm);
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
    flex-direction: column;
    align-items: stretch;
  }

  .browserui-toolbar__controls,
  .browserui-batch-tools {
    justify-content: flex-start;
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
