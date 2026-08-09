<template>
  <div class="surface">
    <div class="surface__content browserui-shell">
      <div class="browserui-body">
        <!-- Center: Research cards canvas -->
        <div class="browserui-canvas">
          <div class="browserui-search">
            <UInput
              v-model="searchQuery"
              placeholder="Search topics..."
              icon="search"
            />
          </div>

          <div v-if="filteredStacks.length === 0" class="browserui-empty">
            <UIcon name="search" class="browserui-empty-icon" />
            <p>No topics found</p>
            <p class="browserui-empty-hint">
              Try a different search or add bookmarks to your vault.
            </p>
          </div>
          <div
            v-for="stack in filteredStacks"
            :key="stack.id"
            class="browserui-stack"
          >
            <div class="browserui-stack-header">
              <UIcon :name="stack.icon" class="browserui-stack-icon" />
              <h3>{{ stack.title }}</h3>
              <UBadge type="info" circle>{{ stack.items.length }}</UBadge>
            </div>
            <div class="browserui-cards">
              <div
                v-for="item in stack.items"
                :key="item.id"
                class="browserui-card"
                :class="{
                  'browserui-card--active': activeCard?.id === item.id,
                }"
                @click="selectCard(item)"
              >
                <div class="browserui-card-header">
                  <div class="browserui-card-title">{{ item.title }}</div>
                  <UIcon
                    name="diamond"
                    class="browserui-card-action-icon"
                    title="Research this topic"
                  />
                </div>
                <div class="browserui-card-desc">{{ item.description }}</div>
                <div class="browserui-card-tags">
                  <span
                    v-for="tag in item.tags"
                    :key="tag"
                    class="browserui-tag"
                    >{{ tag }}</span
                  >
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Editor panel — slides in when a card is active -->
        <transition name="editor-slide">
          <div v-if="activeCard" class="browserui-editor">
            <div class="browserui-doc">
              <div class="browserui-doc-header">
                <div>
                  <h3 class="browserui-doc-title">{{ activeCard.title }}</h3>
                  <a
                    :href="activeCard.url"
                    target="_blank"
                    rel="noopener"
                    class="browserui-doc-source"
                  >
                    <UIcon name="open_in_new" />
                    {{ sourceLabel(activeCard.url) }}
                  </a>
                </div>
                <div class="browserui-doc-header-actions">
                  <button
                    class="browserui-doc-close"
                    title="Close editor"
                    @click="activeCard = null"
                  >
                    <UIcon name="close" />
                  </button>
                </div>
              </div>

              <div class="browserui-doc-actions">
                <UButton
                  variant="secondary"
                  size="sm"
                  icon="open_in_new"
                  @click="openResearchUrl(activeCard.url)"
                >
                  Research
                </UButton>
                <UButton
                  variant="secondary"
                  size="sm"
                  icon="download"
                  :disabled="expandingId === activeCard.id"
                  @click="expandCard(activeCard)"
                >
                  {{ expandingId === activeCard.id ? "Fetching..." : "Expand" }}
                </UButton>
                <UButton
                  variant="secondary"
                  size="sm"
                  icon="summarize"
                  @click="summariseCard(activeCard)"
                >
                  Summarise
                </UButton>
              </div>

              <div
                v-if="expandingId === activeCard.id"
                class="browserui-doc-loading"
              >
                <UIcon name="sync" />
                <span
                  >Fetching content from
                  {{ sourceLabel(activeCard.url) }}…</span
                >
              </div>

              <div class="browserui-doc-content">
                <div class="browserui-doc-frontmatter">
                  <div class="browserui-doc-fm-row">
                    <span class="browserui-doc-fm-key">source</span>
                    <a :href="activeCard.url" target="_blank" rel="noopener">{{
                      activeCard.url
                    }}</a>
                  </div>
                  <div class="browserui-doc-fm-row">
                    <span class="browserui-doc-fm-key">tags</span>
                    <span>{{ (activeCard.tags || []).join(", ") }}</span>
                  </div>
                  <div class="browserui-doc-fm-row">
                    <span class="browserui-doc-fm-key">status</span>
                    <UBadge type="warning" size="sm">draft</UBadge>
                  </div>
                </div>
                <div class="browserui-doc-body">
                  <h4>{{ activeCard.title }}</h4>
                  <blockquote v-if="researchContent[activeCard.id]">
                    {{ researchContent[activeCard.id] }}
                  </blockquote>
                  <p v-else>{{ activeCard.description }}</p>
                </div>
              </div>

              <div class="browserui-doc-footer">
                <UButton
                  variant="primary"
                  size="sm"
                  icon="diamond"
                  @click="saveToEditor(activeCard)"
                >
                  Open in Markdown Editor
                </UButton>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import UInput from "../../skills/atoms/UInput.vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import UButton from "../../skills/atoms/UButton.vue";
import { useWorkflowStore } from "../../stores/workflow";
import { buildResearchDocument, fetchScrape } from "../../utils/webScraper";

const API_BASE = import.meta.env.VITE_SNACKBAR_URL || "http://localhost:8484";
const searchQuery = ref("");
const loading = ref(true);
const router = useRouter();
const wf = useWorkflowStore();

interface StackItem {
  id: string;
  title: string;
  url: string;
  description: string;
  tags: string[];
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
const researchContent = ref<Record<string, string>>({});
const expandingId = ref<string | null>(null);

function selectCard(item: StackItem) {
  activeCard.value = item;
}

function sourceLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function openResearchUrl(url: string) {
  window.open(url, "_blank", "noopener");
}

async function expandCard(item: StackItem) {
  expandingId.value = item.id;
  try {
    const scraped = await fetchScrape(item.url);
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
  const { filename, content } = buildResearchDocument(item, scraped);
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

onMounted(() => {
  fetchBookmarks();
});

const filteredStacks = computed(() => {
  if (!searchQuery.value) return stacks.value;
  const q = searchQuery.value.toLowerCase();
  return stacks.value
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

/* ─── Body: two-panel layout ─────────────────────────────────── */
.browserui-body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ─── Search bar ─────────────────────────────────────────────── */
.browserui-search {
  padding: 0 0 var(--usx-spacing-md);
  flex-shrink: 0;
}

.browserui-search :deep(.u-input) {
  max-width: 40ch;
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

/* ─── Cards ──────────────────────────────────────────────────── */
.browserui-cards {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  min-width: 0;
}

.browserui-card {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  color: inherit;
  min-width: 0;
  cursor: pointer;
  text-align: left;
  transition:
    border-color var(--usx-transition-fast),
    background var(--usx-transition-fast);
}

.browserui-card:hover {
  border-color: var(--usx-color-primary);
}

.browserui-card--active {
  border-color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 6%, transparent);
}

.browserui-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
}

.browserui-card-action-icon {
  flex-shrink: 0;
  font-size: 16px;
  color: var(--usx-color-on-surface-muted);
  opacity: 0;
  transition: opacity 150ms ease;
}

.browserui-card:hover .browserui-card-action-icon {
  opacity: 1;
  color: var(--usx-color-primary);
}

.browserui-card-title {
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  overflow-wrap: anywhere;
}

.browserui-card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  line-height: var(--usx-line-height-normal);
  overflow-wrap: anywhere;
}

.browserui-card-tags {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  padding-top: var(--usx-spacing-xs);
}

.browserui-tag {
  display: inline-flex;
  align-items: center;
  font-size: var(--usx-font-size-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: var(--usx-color-surface-variant);
  border-radius: var(--usx-radius-full);
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-medium);
  line-height: var(--usx-line-height-none);
  white-space: nowrap;
}

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
  width: 420px;
  min-width: 320px;
  max-width: 50vw;
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-surface);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
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
