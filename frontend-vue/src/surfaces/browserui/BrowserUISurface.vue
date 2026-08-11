<template>
  <div class="surface">
    <div class="surface__content browserui-shell">
      <div class="browserui-tabs">
        <button v-for="tab in TABS" :key="tab.id"
          class="browserui-tab"
          :class="{ 'browserui-tab--active': activeTab === tab.id }"
          @click="switchTab(tab.id)">
          <UIcon :name="tab.icon" />{{ tab.label }}
        </button>
      </div>
            <div v-if="activeTab === 'cards'" class="browserui-body">
        <div class="browserui-toolbar">
          <div class="browserui-search">
            <UInput v-model="searchQuery" placeholder="Search topics..." icon="search" />
          </div>
          <div class="browserui-pills">
            <button v-for="tag in allTags" :key="tag" class="browserui-pill"
              :class="{ 'browserui-pill--active': activeTag === tag }"
              @click="activeTag = activeTag === tag ? '' : tag">{{ tag }}</button>
          </div>
          <div class="browserui-actions">
            <button class="uxs-btn uxs-btn--primary" @click="activeTag = ''; batchSelected = []">
              <UIcon name="refresh" /> Reset
            </button>
            <button v-if="batchSelected.length" class="uxs-btn uxs-btn--primary"
              @click="batchResearch">Research {{ batchSelected.length }}</button>
          </div>
        </div>
        <div class="browserui-kanban">
          <div v-for="stack in filteredStacks" :key="stack.id" class="browserui-column">
            <div class="browserui-column__header">
              <UIcon :name="stack.icon" /><h3>{{ stack.title }}</h3>
              <span class="browserui-column__count">{{ stack.items.length }}</span>
            </div>
            <div class="browserui-column__cards">
              <div v-for="card in stack.items" :key="card.id"
                class="browserui-card"
                :class="{ 'browserui-card--active': selectedCard?.id === card.id, 'browserui-card--selected': batchSelected.includes(card.id) }"
                @click.self="selectCard(card)">
                <div class="browserui-card__top">
                  <input type="checkbox" :checked="batchSelected.includes(card.id)"
                    @change="toggleBatch(card.id, $event)" class="browserui-card__check" />
                  <span class="browserui-card__score" v-if="card.score !== undefined"
                    :class="scoreColor(card.score)">{{ card.score }}</span>
                  <span class="browserui-card__title">{{ card.title }}</span>
                </div>
                <div class="browserui-card__desc">{{ card.description }}</div>
                <div class="browserui-card__tags">
                  <span v-for="t in card.tags" :key="t" class="browserui-card__tag">{{ t }}</span>
                </div>
                <div class="browserui-card__actions">
                  <button class="uxs-btn uxs-btn--sm" @click.stop="handleResearchCard(card)">Research</button>
                  <button class="uxs-btn uxs-btn--sm" @click.stop="enhanceCard(card)">Enhance</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="selectedCard" class="browserui-editor">
          <PreviewTab v-if="editorMode === 'preview'" :content="editorContent" :meta="editorMeta"
            @edit="editorMode = 'edit'" @chatui="sendToChatUI" />
          <EditTab v-else :content="editorContent" :title="selectedCard?.title"
            :tags="selectedCard?.tags" :binder="selectedCard?.binder"
            @preview="editorMode = 'preview'" @save="saveToBinder" />
          <button class="browserui-editor-close" @click="selectedCard = null; editorMode = 'preview'">
            <UIcon name="close" /></button>
        </div>
      </div>
      <ResearchDashboard v-if="activeTab === 'dashboard'"
        :jobs="researchJobs" :gaps="researchGaps"
        @approve="approveJob" @startResearch="startResearchJob"
        @fillGap="fillResearchGap"
      />
    </div>
  </div>
</template>


<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import UInput from "../../skills/atoms/UInput.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import UButton from "../../skills/atoms/UButton.vue";
import CardStack from "./panels/CardStack.vue"
import PreviewTab from "./panels/PreviewTab.vue"
import EditTab from "./panels/EditTab.vue"
import ResearchDashboard from "./panels/ResearchDashboard.vue"
import { useChatStore } from "../../stores/chat"

import { useWorkflowStore } from "../../stores/workflow";
import { startResearch, listResearchJobs, getResearchStatus, fetchScrape, addBinder } from "./ApiBridge"

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || "http://localhost:8484";
const searchQuery = ref("");
const loading = ref(true);
const router = useRouter();
const wf = useWorkflowStore();

interface StackItem {
  id: string;
  title: string;
  url?: string;
  description: string;
  tags: string[];
  score?: number;
  binder?: string;
}

const stacks = ref<
  Array<{ id: string; title: string; icon: string; items: StackItem[] }>
>([]);

const DEFAULT_STACKS = [
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
];

const activeCard = ref<StackItem | null>(null);
const activeTab = ref<"cards" | "dashboard">("cards")
const selectedCard = ref<StackItem | null>(null)
const editorMode = ref<"preview" | "edit">("preview")
const editorContent = ref("")
const editorMeta = ref<{ source?: string; score?: number; tags?: string[]; title?: string }>({})
const researchJobs = ref<any[]>([])
const researchGaps = ref<any[]>([])
const batchSelected = ref<string[]>([])
const activeTag = ref("")
const chat = useChatStore()

const TABS = [
  { id: "cards", label: "Cards", icon: "dashboard" },
  { id: "dashboard", label: "Research", icon: "science" },
]

const researchContent = ref<Record<string, string>>({});
const expandingId = ref<string | null>(null);

function sourceLabel(url: string): string {
  try {
    return new URL(url ?? "").hostname.replace(/^www\./, "");
  } catch {
    return url ?? "";
  }
}

function switchTab(tab: string) {
  activeTab.value = tab as "cards" | "dashboard"
}

function openResearchUrl(url: string) {
  window.open(url, "_blank", "noopener");
}

async function expandCard(item: StackItem) {
  expandingId.value = item.id;
  try {
    const scraped = await fetchScrape(item.url ?? "");
    researchContent.value = {
      ...researchContent.value,
      [item.id]: scraped?.text || scraped?.description || item.description,
    };
  } catch {
    researchContent.value = {
      ...researchContent.value,
      [item.id]: item.description,
    };
  } finally {
    expandingId.value = null;
  }
}

function summariseCard(item: StackItem) {
  const existing = researchContent.value[item.id] || item.description;
  const summary = `## Summary\n\nKey points from ${item.title}:\n\n- ${item.description}\n\n_Expand to fetch full content from the source._`;
  researchContent.value = {
    ...researchContent.value,
    [item.id]: existing + "\n\n" + summary,
  };
}

function saveToEditor(item: StackItem) {
  const scraped = researchContent.value[item.id]
    ? {
        title: item.title,
        description: researchContent.value[item.id],
        url: item.url,
        text: researchContent.value[item.id],
      }
    : null;
  const { filename, content } = {
    filename: (item.title || "untitled").toLowerCase().replace(/[^a-z0-9\s-]/g,"").trim().replace(/\s+/g,"-").slice(0,60)+".md",
    content: "---\ntitle: \""+(item.title||"")+"\"\nsource: \""+(item.url||"")+"\"\ndate: \""+new Date().toISOString().slice(0,10)+"\"\n---\n\n# "+(item.title||"")+"\n\n"+(scraped?.text || item.description)
  };
  wf.selectFile({
    id: `research-${item.id}`,
    path: `/research/${filename}`,
    filename,
    extension: "md",
    binder: "Research",
    content,
    readOnly: false,
  });
  router.push({ path: "/workflow", query: { tab: "editor" } });
}

async function fetchBookmarks() {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/knowledge?type=bookmark`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      const items = (data.items || data || []).map((b: any) => ({
        id: b.id || b.url,
        title: b.title || b.name || "Untitled",
        url: b.url || b.link || "#",
        description: b.description || b.summary || "",
        tags: (b.tags || b.keywords || []).map((t: string) =>
          t.startsWith("#") ? t : `#${t}`,
        ),
      }));
      if (items.length > 0) {
        stacks.value = [
          { id: "bookmarks", title: "Bookmarks", icon: "bookmark", items },
        ];
        return;
      }
    }
  } catch {
    /* backend offline */
  }
  stacks.value = DEFAULT_STACKS;
  loading.value = false;
}
// ── New panel methods ───────────────────────────────────

function selectCard(item: StackItem) {
  selectedCard.value = item
  editorContent.value = researchContent.value[item.id] || item.description
  editorMeta.value = { source: item.url, tags: item.tags, title: item.title }
}

async function handleResearchCard(card: any) {
  try {
    const r = await startResearch(card.url ?? "", card.tags[0]?.replace("#", "") || "research", card.tags, "full")
    researchJobs.value.unshift({ id: (r as any).job_id || "0", url: card.url ?? "", binder: "research", state: "pending", progress: 0 })
  } catch (e) { /* offline */ }
}


async function enhanceCard(item: StackItem) {
  try {
    const scraped = await fetchScrape(item.url ?? "")
    if (scraped) {
      researchContent.value = { ...researchContent.value, [item.id]: scraped.text || scraped.description }
      editorContent.value = scraped.text || scraped.description
      editorMeta.value = { source: item.url, tags: item.tags, title: scraped.title || item.title }
    }
  } catch (e) { /* offline */ }
}

function sendToChatUI() {
  chat.sendMessage(`Research this topic and provide a structured plan:\n\nTitle: ${editorMeta.value.title}\nSource: ${editorMeta.value.source}\n\nContent:\n${editorContent.value.substring(0, 2000)}`)
}

async function saveToBinder(save: { title: string; content: string; tags: string[] }) {
  try {
    await addBinder(save.title, save.content, save.tags)
  } catch (e) { /* offline */ }
  selectedCard.value = null
  editorMode.value = "preview"
}

async function startResearchJob(params: { url: string; binder: string; tags: string[] }) {
  try {
    const r = await startResearch(params.url, params.binder, params.tags, "full")
    researchJobs.value.unshift({ id: r.job_id, url: params.url, binder: params.binder, state: "pending", progress: 0 })
  } catch (e) { /* offline */ }
}

async function approveJob(job: any) {
  try {
    const status = await getResearchStatus(job.id)
    const idx = researchJobs.value.findIndex(j => j.id === job.id)
    if (idx >= 0) researchJobs.value[idx] = { ...researchJobs.value[idx], ...status }
  } catch (e) { /* offline */ }
}

function fillResearchGap(gap: any) {
  const url = gap.url || gap.topic
  startResearchJob({ url, binder: "research", tags: gap.tags || [] })
}

async function batchResearch() {
  const allItems = stacks.value.flatMap(s => s.items)
  const selected = allItems.filter(i => batchSelected.value.includes(i.id))
  for (const item of selected) {
    try {
      const r = await startResearch(item.url ?? "", item.tags[0]?.replace("#", "") || "research", item.tags, "summarise")
      researchJobs.value.unshift({ id: (r as any).job_id, url: item.url ?? "", binder: "research", state: "pending", progress: 0 })
    } catch { /* skip */ }
  }
  batchSelected.value = []
}

async function detectKnowledgeGaps() {
  try {
    const res = await fetch(`${API_BASE}/api/research/vault-scan`, { signal: AbortSignal.timeout(5000) })
    if (res.ok) {
      const data = await res.json()
      researchGaps.value = data.gaps || []
    }
  } catch { /* offline */ }
}

// Session persistence
function saveSession() {
  localStorage.setItem("browserui-session", JSON.stringify({
    researchJobs: researchJobs.value.slice(0, 20),
    searchQuery: searchQuery.value,
  }))
}
function loadSession() {
  try {
    const raw = localStorage.getItem("browserui-session")
    if (!raw) return
    const data = JSON.parse(raw)
    researchJobs.value = data.researchJobs || []
    searchQuery.value = data.searchQuery || ""
  } catch {
    // ignore malformed session data
  }
}

function toggleBatch(id: string, event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  if (checked) batchSelected.value = [...batchSelected.value, id]
  else batchSelected.value = batchSelected.value.filter(i => i !== id)
}

function scoreColor(s: number | undefined): string {
  if (s === undefined) return ""
  if (s >= 4) return "browserui-score--high"
  if (s >= 2) return "browserui-score--mid"
  return "browserui-score--low"
}


watch(researchJobs, () => saveSession(), { deep: true })

onMounted(() => {
  loadSession()
  fetchBookmarks()
  detectKnowledgeGaps()
})




const allTags = computed(() => {
  const tags = new Set<string>()
  for (const s of stacks.value) for (const item of s.items) for (const t of item.tags) tags.add(t)
  return [...tags].sort()
})


const filteredStacks = computed(() => {
  let result = stacks.value
  if (activeTag.value) {
    result = result.map(s => ({ ...s, items: s.items.filter(i => i.tags.includes(activeTag.value)) })).filter(s => s.items.length)
  }
  if (!searchQuery.value) return result
  const q = searchQuery.value.toLowerCase()
  return result
    .map((stack) => ({
      ...stack,
      items: stack.items.filter(
        (item) =>
          item.title.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q) ||
          item.tags.some((t) => t.toLowerCase().includes(q)),
      ),
    }))
    .filter((stack) => stack.items.length > 0);
});
</script>

<style scoped>
/* ─── Shell: standard surface__content flex container ───────── */
.browserui-shell {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

/* ─── Tab bar ────────────────────────────────────────────────── */
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
  border-bottom: 2px solid transparent;
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

/* ─── Body: vertical stack (toolbar → kanban) ───────────────── */
.browserui-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

/* ─── Toolbar: centered search + pills + actions ───────────── */
.browserui-toolbar {
  display: flex; flex-direction: column; align-items: center;
  gap: var(--usx-spacing-md); padding: var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0; background: var(--usx-color-surface);
}
.browserui-search { width: 100%; max-width: 480px; }
.browserui-pills {
  display: flex; gap: var(--usx-spacing-xs); flex-wrap: wrap;
  justify-content: center; max-width: 600px;
}
.browserui-pill {
  font-size: var(--usx-font-size-xs); padding: 4px var(--usx-spacing-md);
  border-radius: var(--usx-radius-full); border: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface); cursor: pointer;
  color: var(--usx-color-on-surface-muted); white-space: nowrap;
  transition: all var(--usx-transition-fast);
}
.browserui-pill:hover { border-color: var(--usx-color-primary); color: var(--usx-color-primary); }
.browserui-pill--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); border-color: var(--usx-color-primary); }
.browserui-actions { display: flex; gap: var(--usx-spacing-sm); }

/* ─── Kanban columns ─────────────────────────────────────────── */
.browserui-kanban {
  display: flex; gap: var(--usx-spacing-md); flex: 1; min-height: 0;
  overflow-x: auto; overflow-y: hidden; padding: var(--usx-spacing-md);
}
.browserui-column {
  flex: 0 0 300px; display: flex; flex-direction: column; min-height: 0;
  background: var(--usx-color-surface-variant); border-radius: var(--usx-radius-lg);
  overflow: hidden;
}
.browserui-column__header {
  display: flex; align-items: center; gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}
.browserui-column__header h3 { margin: 0; font-size: var(--usx-font-size-sm); font-weight: 600; flex: 1; }
.browserui-column__count {
  font-size: var(--usx-font-size-xs); background: var(--usx-color-surface);
  padding: 1px 8px; border-radius: var(--usx-radius-full); font-weight: 600;
}
.browserui-column__cards {
  flex: 1; overflow-y: auto; padding: var(--usx-spacing-sm);
  display: flex; flex-direction: column; gap: var(--usx-spacing-sm);
}

/* ─── Editor close button ───────────────────────────────────── */
.browserui-editor-close {
  position: absolute;
  top: var(--usx-spacing-sm);
  right: var(--usx-spacing-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
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

/* ─── Shared button styles used in shell ────────────────────── */
.uxs-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  padding: 4px var(--usx-spacing-sm);
  cursor: pointer;
  background: var(--usx-color-surface);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  transition: background var(--usx-transition-fast);
}

.uxs-btn:hover {
  background: var(--usx-color-surface-hover);
}

.uxs-btn--primary {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border-color: var(--usx-color-primary);
}

.uxs-btn--primary:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 85%, black);
}

/* ─── Canvas ─────────────────────────────────────────────────── */
.browserui-canvas {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: var(--usx-spacing-md);
}

.browserui-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-3xl) 0;
  color: var(--usx-color-on-surface-muted);
  text-align: center;
}

.browserui-empty-icon {
  font-size: 3em;
  margin-bottom: var(--usx-spacing-md);
  opacity: 0.4;
}

.browserui-empty p {
  margin: 0;
  font-size: var(--usx-font-size-base);
}
.browserui-empty-hint {
  font-size: var(--usx-font-size-sm) !important;
  margin-top: var(--usx-spacing-xs) !important;
}

/* ─── Stack sections ─────────────────────────────────────────── */
.browserui-stack + .browserui-stack {
  margin-top: var(--usx-spacing-lg);
}

.browserui-stack-header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-bottom: var(--usx-spacing-sm);
}

.browserui-stack-icon {
  font-size: 1.25em;
  color: var(--usx-color-on-surface-muted);
}

.browserui-stack-header h3 {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0;
  flex: 1;
}

/* ─── Cards in kanban columns ──────────────────────────────── */
.browserui-card {
  padding: var(--usx-spacing-sm); border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md); cursor: pointer;
  background: var(--usx-color-surface);
  transition: border-color var(--usx-transition-fast), box-shadow var(--usx-transition-fast);
}
.browserui-card:hover { border-color: var(--usx-color-primary); box-shadow: 0 1px 4px color-mix(in srgb, var(--usx-color-primary) 15%, transparent); }
.browserui-card--active { border-color: var(--usx-color-primary); background: color-mix(in srgb, var(--usx-color-primary) 5%, transparent); }
.browserui-card--selected { border-color: var(--usx-color-success); background: color-mix(in srgb, var(--usx-color-success) 5%, transparent); }
.browserui-card__top { display: flex; align-items: center; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-xs); }
.browserui-card__check { width: 14px; height: 14px; accent-color: var(--usx-color-primary); cursor: pointer; flex-shrink: 0; }
.browserui-card__score { font-size: 10px; font-weight: 700; min-width: 22px; text-align: center; padding: 1px 4px; border-radius: var(--usx-radius-sm); }
.browserui-score--high { background: var(--usx-color-success); color: var(--usx-color-on-success); }
.browserui-score--mid { background: var(--usx-color-warning); color: var(--usx-color-on-warning); }
.browserui-score--low { background: var(--usx-color-danger); color: var(--usx-color-on-danger); }
.browserui-card__title { font-weight: 600; font-size: var(--usx-font-size-sm); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.browserui-card__desc { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-xs); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.browserui-card__tags { display: flex; gap: 2px; flex-wrap: wrap; margin-bottom: var(--usx-spacing-xs); }
.browserui-card__tag { font-size: 10px; padding: 1px 6px; border-radius: var(--usx-radius-full); background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface-muted); }
.browserui-card__actions { display: flex; gap: var(--usx-spacing-xs); }


/* ─── Right: Editor slide-in ─────────────────────────────────── */
.editor-slide-enter-active,
.editor-slide-leave-active {
  transition:
    width 0.25s ease,
    opacity 0.2s ease;
  overflow: hidden;
}

.editor-slide-enter-from,
.editor-slide-leave-to {
  width: 0 !important;
  opacity: 0;
}

.browserui-editor {
  position: absolute; top: 0; right: 0; bottom: 0;
  width: 420px; max-width: 50vw;
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  display: flex; flex-direction: column;
  box-shadow: -4px 0 16px rgba(0,0,0,0.08);
  z-index: 10; overflow-y: auto;
}
}

.browserui-doc {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.browserui-doc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}

.browserui-doc-title {
  margin: 0 0 var(--usx-spacing-xs);
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
}

.browserui-doc-source {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-primary);
  text-decoration: none;
}

.browserui-doc-source:hover {
  text-decoration: underline;
}

.browserui-doc-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.browserui-doc-close:hover {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

.browserui-doc-actions {
  display: flex;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}

.browserui-doc-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.browserui-doc-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-md);
}

.browserui-doc-frontmatter {
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-md);
  margin-bottom: var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-mono);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.browserui-doc-fm-row {
  display: flex;
  gap: var(--usx-spacing-sm);
  align-items: center;
}

.browserui-doc-fm-key {
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-semibold);
  min-width: 4ch;
}

.browserui-doc-fm-row a {
  color: var(--usx-color-on-surface-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.browserui-doc-body {
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-normal);
}

.browserui-doc-body h4 {
  margin: 0 0 var(--usx-spacing-sm);
  font-size: var(--usx-font-size-base);
}

.browserui-doc-body blockquote {
  margin: var(--usx-spacing-sm) 0;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-left: 3px solid var(--usx-color-primary);
  background: var(--usx-color-surface-variant);
  border-radius: 0 var(--usx-radius-sm) var(--usx-radius-sm) 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
}

.browserui-doc-footer {
  padding: var(--usx-spacing-md);
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}
</style>
