<template>
  <div class="local-wiki-reader" :class="{ 'local-wiki-reader--zen': zenMode, [`font-${fontFamily}`]: true }">
    <!-- Top Reader Header / Toolbar -->
    <header class="wiki-toolbar">
      <div class="wiki-toolbar__left">
        <button
          type="button"
          class="wiki-btn wiki-btn--icon"
          :title="zenMode ? 'Exit Zen Mode' : 'Enter Zen Focus Mode'"
          @click="zenMode = !zenMode"
        >
          <UIcon :name="zenMode ? 'fullscreen_exit' : 'fit_screen'" />
          <span class="wiki-btn__text">{{ zenMode ? 'Exit Zen' : 'Zen Focus' }}</span>
        </button>

        <div class="wiki-font-toggle">
          <button
            type="button"
            class="wiki-btn wiki-btn--toggle"
            :class="{ 'wiki-btn--active': fontFamily === 'serif' }"
            @click="fontFamily = 'serif'"
            title="Serif Reader (Charter / Georgia)"
          >
            Serif
          </button>
          <button
            type="button"
            class="wiki-btn wiki-btn--toggle"
            :class="{ 'wiki-btn--active': fontFamily === 'sans' }"
            @click="fontFamily = 'sans'"
            title="Clean Sans (Inter / System)"
          >
            Sans
          </button>
        </div>
      </div>

      <div class="wiki-toolbar__center">
        <div v-if="activeTitle" class="wiki-meta">
          <span class="wiki-meta__title">{{ activeTitle }}</span>
          <span v-if="estimatedMinutes" class="wiki-meta__reading-time">
            <UIcon name="schedule" size="xs" /> {{ estimatedMinutes }} min read ({{ wordCount }} words)
          </span>
        </div>
      </div>

      <div class="wiki-toolbar__right">
        <button
          type="button"
          class="wiki-search-trigger"
          title="Search Local Wikipedia (⌘K)"
          @click="openSearchModal"
        >
          <UIcon name="search" size="xs" />
          <span class="wiki-search-trigger__text">Search Wikipedia…</span>
          <kbd class="wiki-kbd">⌘K</kbd>
        </button>

        <button
          type="button"
          class="wiki-btn wiki-btn--icon"
          title="Refresh Vaults Tree"
          :disabled="loadingTree"
          @click="loadTree"
        >
          <UIcon :name="loadingTree ? 'sync' : 'refresh'" />
        </button>
      </div>
    </header>

    <div class="wiki-body">
      <!-- Left Sidebar: Multi-Vault Explorer -->
      <aside v-show="!zenMode" class="wiki-sidebar">
        <div class="wiki-sidebar__header">
          <span class="wiki-sidebar__title">Local Vaults & Manuals</span>
          <span class="wiki-badge wiki-badge--offline">Offline Wikipedia</span>
        </div>

        <div class="wiki-tree-filter">
          <UIcon name="filter_list" size="xs" />
          <input
            v-model="filterQuery"
            type="text"
            placeholder="Filter tree..."
            class="wiki-tree-filter-input"
          />
          <button
            v-if="filterQuery"
            type="button"
            class="wiki-search-clear"
            @click="filterQuery = ''"
          >
            <UIcon name="close" size="xs" />
          </button>
        </div>

        <div v-if="loadingTree" class="wiki-loading">
          <UIcon name="sync" /> Loading multi-vault tree…
        </div>

        <div v-else-if="filteredVaults.length === 0" class="wiki-empty-tree">
          No articles match "{{ filterQuery }}".
        </div>

        <div v-else class="wiki-tree">
          <div v-for="vault in filteredVaults" :key="vault.id" class="wiki-vault-group">
            <div
              class="wiki-vault-header"
              @click="toggleGroup(vault.id)"
            >
              <UIcon :name="isGroupOpen(vault.id) ? 'expand_more' : 'chevron_right'" size="xs" />
              <span class="wiki-vault-name">{{ vault.name }}</span>
              <span class="wiki-vault-badge">{{ vault.badge }}</span>
            </div>

            <div v-if="isGroupOpen(vault.id)" class="wiki-vault-items">
              <template v-for="item in vault.items" :key="item.path">
                <WikiTreeItem
                  :item="item"
                  :active-source="activeSource"
                  :active-path="activePath"
                  @select="selectDocument"
                />
              </template>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Article Reader -->
      <main class="wiki-content">
        <div v-if="loadingContent" class="wiki-loading-content">
          <UIcon name="sync" /> Loading document…
        </div>

        <div v-else-if="!activePath" class="wiki-placeholder">
          <div class="wiki-placeholder__icon">
            <UIcon name="auto_stories" />
          </div>
          <h2>Welcome to the Sovereign Local Wikipedia</h2>
          <p>
            An offline-first, serene reading experience combining all local vaults
            (<code>~/Vault</code>, <code>~/Shared</code>, <code>~/Public</code>, and manuals).
          </p>
          <p class="wiki-placeholder__note">
            External links are safely rendered as static citation chips with zero outbound web tracking.
          </p>
          <div class="wiki-placeholder__actions">
            <button
              v-if="firstArticle"
              type="button"
              class="wiki-btn wiki-btn--primary"
              @click="selectDocument(firstArticle.source, firstArticle.path, firstArticle.title)"
            >
              <UIcon name="menu_book" /> Open {{ firstArticle.title }}
            </button>
          </div>
        </div>

        <article v-else class="wiki-article">
          <!-- Article Breadcrumb & Provenance Banner -->
          <div class="wiki-article__header">
            <div class="wiki-breadcrumb">
              <span class="wiki-breadcrumb__source">{{ sourceLabel(activeSource) }}</span>
              <span class="wiki-breadcrumb__sep">/</span>
              <span class="wiki-breadcrumb__path">{{ activePath }}</span>
            </div>
            <div class="wiki-article__tags">
              <span class="wiki-chip wiki-chip--offline">
                <UIcon name="cloud_off" size="xs" /> 100% Offline
              </span>
            </div>
          </div>

          <!-- Auto-generated Table of Contents -->
          <div v-if="headings.length > 2" class="wiki-toc">
            <div class="wiki-toc__title">
              <UIcon name="list" size="xs" /> Table of Contents
            </div>
            <ul class="wiki-toc__list">
              <li
                v-for="h in headings"
                :key="h.id"
                class="wiki-toc__item"
                :class="`wiki-toc__item--l${h.level}`"
              >
                <a :href="`#${h.id}`" @click.prevent="scrollToHeading(h.id)">{{ h.text }}</a>
              </li>
            </ul>
          </div>

          <!-- Rendered HTML Document Body -->
          <div
            class="wiki-prose prose-measure"
            v-html="renderedHtml"
            @click="handleProseClick"
          />
        </article>
      </main>
    </div>

    <!-- Offline Search Modal (Cmd+K) -->
    <div v-if="showSearchModal" class="wiki-modal-backdrop" @click.self="closeSearchModal">
      <div class="wiki-search-modal" role="dialog" aria-label="Search Local Wikipedia">
        <header class="wiki-search-modal__header">
          <UIcon name="search" class="wiki-search-modal__icon" />
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="Search all local vaults, manuals, and datasets..."
            class="wiki-search-modal__input"
            @keydown.down.prevent="navigateResults(1)"
            @keydown.up.prevent="navigateResults(-1)"
            @keydown.enter.prevent="selectCurrentResult"
            @keydown.esc="closeSearchModal"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="wiki-search-clear"
            @click="searchQuery = ''; searchResults = []"
          >
            <UIcon name="close" size="xs" />
          </button>
          <kbd class="wiki-kbd">ESC</kbd>
        </header>

        <!-- Zone filter pills -->
        <div class="wiki-search-modal__filters">
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'all' }"
            @click="setSearchZone('all')"
          >
            All Zones
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'personal' }"
            @click="setSearchZone('personal')"
          >
            Personal (~/Vault)
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'public' }"
            @click="setSearchZone('public')"
          >
            Public Canon (~/Public)
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'manuals' }"
            @click="setSearchZone('manuals')"
          >
            Curriculum & Manuals
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'shared' }"
            @click="setSearchZone('shared')"
          >
            Shared (~/Shared)
          </button>
        </div>

        <!-- Results list -->
        <div class="wiki-search-modal__results">
          <div v-if="searching" class="wiki-search-loading">
            <UIcon name="sync" /> Searching local FTS index...
          </div>
          <div v-else-if="searchQuery && searchResults.length === 0" class="wiki-search-empty">
            <UIcon name="search_off" :size="32" />
            <p>No matches found for "<strong>{{ searchQuery }}</strong>"</p>
            <span class="subtext">Search covers ~/Vault, ~/Shared, ~/Public, offline datasets, and manuals.</span>
          </div>
          <div v-else-if="!searchQuery" class="wiki-search-hint">
            <p>Type to search offline articles, canonical datasets (world parameters, coordinates), USX design tokens, and manuals.</p>
            <div class="wiki-search-quick-tags">
              <span class="subtext">Try searching:</span>
              <button type="button" class="quick-tag" @click="runQuickSearch('world parameters')">world parameters</button>
              <button type="button" class="quick-tag" @click="runQuickSearch('BBC BASIC')">BBC BASIC</button>
              <button type="button" class="quick-tag" @click="runQuickSearch('USX tokens')">USX tokens</button>
              <button type="button" class="quick-tag" @click="runQuickSearch('hardware revival')">hardware revival</button>
            </div>
          </div>
          <ul v-else class="wiki-results-list">
            <li
              v-for="(item, idx) in searchResults"
              :key="item.id || item.path"
              class="wiki-result-item"
              :class="{ 'wiki-result-item--selected': selectedResultIndex === idx }"
              @mouseenter="selectedResultIndex = idx"
              @click="chooseSearchResult(item)"
            >
              <div class="wiki-result-item__top">
                <span class="wiki-result-item__title" v-html="highlightSearchTerm(item.title, searchQuery)" />
                <span class="wiki-result-item__badge">{{ item.badge }}</span>
              </div>
              <p class="wiki-result-item__snippet" v-html="item.snippet" />
              <div class="wiki-result-item__meta">
                <span class="wiki-result-item__path">{{ item.rel_path }}</span>
                <span v-if="item.modified_at" class="wiki-result-item__date">
                  {{ new Date(item.modified_at).toLocaleDateString() }}
                </span>
              </div>
            </li>
          </ul>
        </div>

        <!-- Modal Footer -->
        <footer class="wiki-search-modal__footer">
          <div class="footer-left">
            <UIcon name="cloud_off" size="xs" />
            <span>100% Offline · SQLite FTS5 · Zero Telemetry</span>
          </div>
          <div class="footer-right">
            <span><kbd class="wiki-kbd-mini">↑</kbd><kbd class="wiki-kbd-mini">↓</kbd> Navigate</span>
            <span><kbd class="wiki-kbd-mini">↵</kbd> Open</span>
            <span><kbd class="wiki-kbd-mini">ESC</kbd> Close</span>
          </div>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";
import UIcon from "../../skills/atoms/UIcon.vue";

interface TreeItem {
  name: string;
  title?: string;
  path: string;
  source: string;
  is_dir: boolean;
  size?: number;
  children?: TreeItem[];
}

interface VaultGroup {
  id: string;
  name: string;
  badge: string;
  source: string;
  exists: boolean;
  items: TreeItem[];
  count: number;
}

interface HeadingItem {
  id: string;
  text: string;
  level: number;
}

const loadingTree = ref(true);
const loadingContent = ref(false);
const vaults = ref<VaultGroup[]>([]);
const openGroups = ref<Set<string>>(new Set(["personal", "manuals", "public", "shared"]));
const openFolders = ref<Set<string>>(new Set());

const activeSource = ref<string>("");
const activePath = ref<string>("");
const activeTitle = ref<string>("");
const rawMarkdown = ref<string>("");

const filterQuery = ref<string>("");
const zenMode = ref<boolean>(false);
const fontFamily = ref<"serif" | "sans">("serif");

// ── Recursive Tree Item Subcomponent ──────────────────────────────────
const WikiTreeItem = {
  name: "WikiTreeItem",
  props: {
    item: { type: Object as () => TreeItem, required: true },
    activeSource: { type: String, default: "" },
    activePath: { type: String, default: "" },
  },
  emits: ["select"],
  setup(props: { item: TreeItem; activeSource: string; activePath: string }, { emit }: any) {
    const isFolder = computed(() => props.item.is_dir);
    const isOpen = computed(() => openFolders.value.has(props.item.path));
    const isActive = computed(
      () =>
        !props.item.is_dir &&
        props.activeSource === props.item.source &&
        props.activePath === props.item.path
    );

    function toggle() {
      if (isFolder.value) {
        if (openFolders.value.has(props.item.path)) {
          openFolders.value.delete(props.item.path);
        } else {
          openFolders.value.add(props.item.path);
        }
      } else {
        emit("select", props.item.source, props.item.path, props.item.title || props.item.name);
      }
    }

    return () => {
      if (isFolder.value) {
        return h("div", { class: "wiki-tree-folder" }, [
          h(
            "div",
            {
              class: ["wiki-tree-row", "wiki-tree-row--folder"],
              onClick: toggle,
            },
            [
              h(UIcon, {
                name: isOpen.value ? "folder_open" : "folder",
                size: "xs",
              }),
              h("span", { class: "wiki-tree-label" }, props.item.name),
            ]
          ),
          isOpen.value && props.item.children
            ? h(
                "div",
                { class: "wiki-tree-children" },
                props.item.children.map((child) =>
                  h(WikiTreeItem, {
                    item: child,
                    activeSource: props.activeSource,
                    activePath: props.activePath,
                    onSelect: (src: string, p: string, t: string) => emit("select", src, p, t),
                  })
                )
              )
            : null,
        ]);
      }

      return h(
        "div",
        {
          class: [
            "wiki-tree-row",
            "wiki-tree-row--file",
            isActive.value ? "wiki-tree-row--active" : "",
          ],
          onClick: toggle,
        },
        [
          h(UIcon, { name: "description", size: "xs" }),
          h("span", { class: "wiki-tree-label" }, props.item.title || props.item.name),
        ]
      );
    };
  },
};

// ── Word count and Reading Time ──────────────────────────────────────
const wordCount = computed(() => {
  if (!rawMarkdown.value) return 0;
  return rawMarkdown.value.trim().split(/\s+/).filter(Boolean).length;
});

const estimatedMinutes = computed(() => {
  if (wordCount.value === 0) return 0;
  return Math.ceil(wordCount.value / 200);
});

// ── Find First Article for quick start ────────────────────────────────
const firstArticle = computed(() => {
  for (const v of vaults.value) {
    const found = findFirstFile(v.items);
    if (found) return found;
  }
  return null;
});

function findFirstFile(items: TreeItem[]): TreeItem | null {
  for (const item of items) {
    if (!item.is_dir) return item;
    if (item.children) {
      const sub = findFirstFile(item.children);
      if (sub) return sub;
    }
  }
  return null;
}

// ── Tree Filter ───────────────────────────────────────────────────────
function filterItems(items: TreeItem[], query: string): TreeItem[] {
  const result: TreeItem[] = [];
  const q = query.toLowerCase();

  for (const item of items) {
    if (item.is_dir && item.children) {
      const filteredChildren = filterItems(item.children, query);
      if (filteredChildren.length > 0 || item.name.toLowerCase().includes(q)) {
        result.push({
          ...item,
          children: filteredChildren.length > 0 ? filteredChildren : item.children,
        });
      }
    } else if (
      item.name.toLowerCase().includes(q) ||
      (item.title && item.title.toLowerCase().includes(q))
    ) {
      result.push(item);
    }
  }
  return result;
}

const filteredVaults = computed(() => {
  if (!filterQuery.value.trim()) return vaults.value;
  const q = filterQuery.value.trim();
  return vaults.value
    .map((v) => ({
      ...v,
      items: filterItems(v.items, q),
    }))
    .filter((v) => v.items.length > 0);
});

// ── Group Toggles ─────────────────────────────────────────────────────
function isGroupOpen(groupId: string): boolean {
  return openGroups.value.has(groupId);
}

function toggleGroup(groupId: string) {
  if (openGroups.value.has(groupId)) {
    openGroups.value.delete(groupId);
  } else {
    openGroups.value.add(groupId);
  }
}

function sourceLabel(src: string): string {
  switch (src) {
    case "vault":
      return "Personal Vault (~/Vault)";
    case "shared":
      return "Shared Vault (~/Shared)";
    case "public":
      return "Public Knowledge (~/Public)";
    case "manual":
      return "uCode Beginner Curriculum";
    case "sonic":
      return "Sonic Hardware Rebirth";
    default:
      return src;
  }
}

// ── Headings & TOC Extraction ─────────────────────────────────────────
const headings = computed<HeadingItem[]>(() => {
  if (!rawMarkdown.value) return [];
  const list: HeadingItem[] = [];
  const lines = rawMarkdown.value.split("\n");

  for (const line of lines) {
    const match = line.match(/^(#{1,3})\s+(.+)$/);
    if (match) {
      const level = match[1].length;
      const text = match[2].trim().replace(/[#*_`]/g, "");
      const id = text
        .toLowerCase()
        .replace(/[^\w\s-]/g, "")
        .replace(/\s+/g, "-");
      list.push({ id, text, level });
    }
  }
  return list;
});

function scrollToHeading(id: string) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

// ── Markdown Transformation & External Link Neutralization ────────────
const renderedHtml = computed(() => {
  if (!rawMarkdown.value) return "";

  let processed = rawMarkdown.value;

  // 1. Transform internal [[WikiLink]] syntax to clickable local links
  processed = processed.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, target, alias) => {
    const label = alias || target;
    return `[${label}](#wiki:${encodeURIComponent(target)})`;
  });

  // 2. Parse Markdown
  const rawHtml = marked.parse(processed) as string;

  // 3. Post-process HTML to:
  //    a) Add IDs to headings for TOC navigation
  //    b) Convert external URLs into offline citation chips
  const doc = new DOMParser().parseFromString(rawHtml, "text/html");

  // Headings
  doc.querySelectorAll("h1, h2, h3").forEach((h) => {
    const text = h.textContent?.trim() || "";
    const id = text
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-");
    h.setAttribute("id", id);
  });

  // Neutralize External Links & Style Internal Wiki Links
  doc.querySelectorAll("a").forEach((a) => {
    const href = a.getAttribute("href") || "";

    if (href.startsWith("#wiki:")) {
      a.classList.add("wiki-internal-link");
      a.setAttribute("data-wiki-target", decodeURIComponent(href.slice(6)));
    } else if (href.startsWith("http://") || href.startsWith("https://")) {
      // Create static offline citation chip
      try {
        const parsedUrl = new URL(href);
        const domain = parsedUrl.hostname.replace(/^www\./, "");
        const span = document.createElement("span");
        span.className = "offline-citation-chip";
        span.title = `External Citation: ${href}`;
        span.innerHTML = `<span class="chip-icon">🔗</span><span class="chip-domain">${domain}</span><span class="chip-tag">offline citation</span>`;
        a.replaceWith(span);
      } catch {
        const span = document.createElement("span");
        span.className = "offline-citation-chip";
        span.textContent = `[Citation: ${href}]`;
        a.replaceWith(span);
      }
    }
  });

  return DOMPurify.sanitize(doc.body.innerHTML, {
    ALLOWED_ATTR: ["id", "class", "data-wiki-target", "title", "href"],
  });
});

// ── Internal Link Click Interception ──────────────────────────────────
function handleProseClick(event: MouseEvent) {
  const target = (event.target as HTMLElement).closest("a");
  if (!target) return;

  const wikiTarget = target.getAttribute("data-wiki-target");
  if (wikiTarget) {
    event.preventDefault();
    findAndOpenWikiTarget(wikiTarget);
  }
}

function findAndOpenWikiTarget(name: string) {
  const cleanName = name.toLowerCase().trim();
  for (const vault of vaults.value) {
    const item = searchTreeForName(vault.items, cleanName);
    if (item) {
      selectDocument(item.source, item.path, item.title || item.name);
      return;
    }
  }
}

function searchTreeForName(items: TreeItem[], name: string): TreeItem | null {
  for (const item of items) {
    if (!item.is_dir) {
      if (
        item.name.toLowerCase().includes(name) ||
        (item.title && item.title.toLowerCase().includes(name))
      ) {
        return item;
      }
    }
    if (item.children) {
      const found = searchTreeForName(item.children, name);
      if (found) return found;
    }
  }
  return null;
}

// ── API Actions ───────────────────────────────────────────────────────
async function loadTree() {
  loadingTree.value = true;
  try {
    const resp = await fetch("/api/docs/wiki/tree");
    if (resp.ok) {
      const data = await resp.json();
      vaults.value = data.vaults || [];
      // Auto-open first article if none selected
      if (!activePath.value && firstArticle.value) {
        selectDocument(
          firstArticle.value.source,
          firstArticle.value.path,
          firstArticle.value.title || firstArticle.value.name
        );
      }
    }
  } catch (err) {
    console.error("Failed to load multi-vault tree:", err);
  } finally {
    loadingTree.value = false;
  }
}

async function selectDocument(source: string, path: string, title?: string) {
  activeSource.value = source;
  activePath.value = path;
  activeTitle.value = title || path.split("/").pop() || "Untitled";
  loadingContent.value = true;

  try {
    const resp = await fetch(
      `/api/docs/content?source=${encodeURIComponent(source)}&path=${encodeURIComponent(path)}`
    );
    if (resp.ok) {
      const data = await resp.json();
      rawMarkdown.value = data.content || "";
    } else {
      rawMarkdown.value = `# Unable to load document\n\nPath: \`${path}\``;
    }
  } catch (err) {
    rawMarkdown.value = `# Network Error\n\nCould not fetch document \`${path}\`.`;
  } finally {
    loadingContent.value = false;
  }
}

const showSearchModal = ref(false);
const searchQuery = ref("");
const searchZone = ref<"all" | "personal" | "public" | "manuals" | "shared">("all");
const searchResults = ref<any[]>([]);
const searching = ref(false);
const selectedResultIndex = ref(0);
const searchInputRef = ref<HTMLInputElement | null>(null);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function openSearchModal() {
  showSearchModal.value = true;
  selectedResultIndex.value = 0;
  nextTick(() => {
    searchInputRef.value?.focus();
  });
}

function closeSearchModal() {
  showSearchModal.value = false;
}

function setSearchZone(zone: "all" | "personal" | "public" | "manuals" | "shared") {
  searchZone.value = zone;
  runSearch();
}

function runQuickSearch(query: string) {
  searchQuery.value = query;
  runSearch();
}

function navigateResults(delta: number) {
  if (searchResults.value.length === 0) return;
  const newIndex = selectedResultIndex.value + delta;
  if (newIndex >= 0 && newIndex < searchResults.value.length) {
    selectedResultIndex.value = newIndex;
  }
}

function selectCurrentResult() {
  if (searchResults.value.length > 0 && selectedResultIndex.value < searchResults.value.length) {
    chooseSearchResult(searchResults.value[selectedResultIndex.value]);
  }
}

function chooseSearchResult(item: any) {
  closeSearchModal();
  selectDocument(item.source, item.rel_path, item.title);
}

function highlightSearchTerm(text: string, term: string): string {
  if (!text || !term.trim()) return text || "";
  const escaped = term.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return text.replace(new RegExp(`(${escaped})`, "gi"), "<mark>$1</mark>");
}

async function runSearch() {
  const q = searchQuery.value.trim();
  if (!q) {
    searchResults.value = [];
    searching.value = false;
    return;
  }

  searching.value = true;
  try {
    let url = `/api/docs/wiki/search?q=${encodeURIComponent(q)}&limit=25`;
    if (searchZone.value !== "all") {
      url += `&vault=${encodeURIComponent(searchZone.value)}`;
    }
    const resp = await fetch(url);
    if (resp.ok) {
      const data = await resp.json();
      searchResults.value = data.results || [];
      selectedResultIndex.value = 0;
    }
  } catch (err) {
    console.error("Search failed:", err);
  } finally {
    searching.value = false;
  }
}

watch(searchQuery, () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    runSearch();
  }, 150);
});

function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    if (showSearchModal.value) {
      closeSearchModal();
    } else {
      openSearchModal();
    }
  } else if (e.key === "Escape" && showSearchModal.value) {
    closeSearchModal();
  }
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  loadTree();
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
});
</script>

<style scoped>
.local-wiki-reader {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--usx-color-bg, #0d1117);
  color: var(--usx-color-text, #c9d1d9);
  font-family: inherit;
}

/* ── Typography Modes ──────────────────────────────────────────────── */
.local-wiki-reader.font-serif .wiki-prose {
  font-family: "Charter", "Georgia", "Merriweather", serif;
}

.local-wiki-reader.font-sans .wiki-prose {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif;
}

/* ── Top Toolbar ───────────────────────────────────────────────────── */
.wiki-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--usx-color-surface, #161b22);
  border-bottom: 1px solid var(--usx-color-border, #30363d);
  gap: 16px;
}

.wiki-toolbar__left,
.wiki-toolbar__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wiki-toolbar__center {
  flex: 1;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wiki-meta__title {
  font-weight: 600;
  margin-right: 10px;
  color: var(--usx-color-primary, #58a6ff);
}

.wiki-meta__reading-time {
  font-size: 12px;
  color: #8b949e;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.wiki-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 12px;
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.wiki-btn:hover {
  background: #30363d;
}

.wiki-btn--active {
  background: #1f6feb;
  color: #ffffff;
  border-color: #388bfd;
}

.wiki-btn--primary {
  background: #238636;
  color: #ffffff;
  border-color: #2ea043;
  padding: 8px 16px;
  font-size: 14px;
}

.wiki-btn--primary:hover {
  background: #2ea043;
}

.wiki-font-toggle {
  display: inline-flex;
  border: 1px solid #30363d;
  border-radius: 4px;
  overflow: hidden;
}

.wiki-btn--toggle {
  border: none;
  border-radius: 0;
}

.wiki-search-box {
  display: inline-flex;
  align-items: center;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 4px;
  padding: 2px 8px;
  gap: 6px;
}

.wiki-search-input {
  background: transparent;
  border: none;
  color: #c9d1d9;
  font-size: 12px;
  width: 160px;
  outline: none;
}

.wiki-search-clear {
  background: transparent;
  border: none;
  color: #8b949e;
  cursor: pointer;
  display: flex;
  align-items: center;
}

/* ── Main Layout ───────────────────────────────────────────────────── */
.wiki-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.wiki-sidebar {
  width: 320px;
  background: #161b22;
  border-right: 1px solid #30363d;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.wiki-sidebar__header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #21262d;
}

.wiki-sidebar__title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #8b949e;
}

.wiki-badge--offline {
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
  border: 1px solid rgba(63, 185, 80, 0.3);
  border-radius: 10px;
}

.wiki-tree {
  padding: 8px 0;
}

.wiki-vault-group {
  margin-bottom: 6px;
}

.wiki-vault-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #e6edf3;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.02);
}

.wiki-vault-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.wiki-vault-name {
  flex: 1;
}

.wiki-vault-badge {
  font-size: 10px;
  color: #8b949e;
  background: #21262d;
  padding: 1px 6px;
  border-radius: 4px;
}

.wiki-vault-items {
  padding-left: 8px;
}

/* ── Tree Rows ─────────────────────────────────────────────────────── */
:deep(.wiki-tree-row) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 12px;
  color: #8b949e;
  cursor: pointer;
  border-radius: 4px;
  margin: 1px 4px;
  user-select: none;
}

:deep(.wiki-tree-row:hover) {
  background: #21262d;
  color: #c9d1d9;
}

:deep(.wiki-tree-row--active) {
  background: rgba(88, 166, 255, 0.15) !important;
  color: #58a6ff !important;
  font-weight: 500;
}

:deep(.wiki-tree-children) {
  padding-left: 12px;
  border-left: 1px dashed #30363d;
  margin-left: 10px;
}

/* ── Content / Reading Area ────────────────────────────────────────── */
.wiki-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.local-wiki-reader--zen .wiki-content {
  padding: 48px 64px;
}

.wiki-article {
  width: 100%;
  max-width: 760px;
}

.wiki-article__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid #21262d;
}

.wiki-breadcrumb {
  font-size: 12px;
  color: #8b949e;
}

.wiki-breadcrumb__sep {
  margin: 0 6px;
  color: #484f58;
}

.wiki-chip--offline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  color: #3fb950;
}

/* ── Table of Contents ─────────────────────────────────────────────── */
.wiki-toc {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 32px;
}

.wiki-toc__title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: #8b949e;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.wiki-toc__list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.wiki-toc__item {
  font-size: 13px;
  margin: 4px 0;
}

.wiki-toc__item--l1 {
  font-weight: 600;
}

.wiki-toc__item--l2 {
  padding-left: 14px;
}

.wiki-toc__item--l3 {
  padding-left: 28px;
  font-size: 12px;
  color: #8b949e;
}

.wiki-toc__item a {
  color: #58a6ff;
  text-decoration: none;
}

.wiki-toc__item a:hover {
  text-decoration: underline;
}

/* ── Prose Typography & 70ch Optimal Measure ───────────────────────── */
.prose-measure {
  max-width: 72ch;
  line-height: 1.75;
  font-size: 16px;
}

:deep(.wiki-prose h1) {
  font-size: 2rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #30363d;
  padding-bottom: 0.3em;
  color: #f0f6fc;
}

:deep(.wiki-prose h2) {
  font-size: 1.5rem;
  margin-top: 1.8rem;
  margin-bottom: 0.8rem;
  border-bottom: 1px solid #21262d;
  padding-bottom: 0.3em;
  color: #f0f6fc;
}

:deep(.wiki-prose h3) {
  font-size: 1.25rem;
  margin-top: 1.4rem;
  margin-bottom: 0.6rem;
  color: #e6edf3;
}

:deep(.wiki-prose p) {
  margin-top: 0;
  margin-bottom: 1.2rem;
  color: #c9d1d9;
}

:deep(.wiki-prose pre) {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family: "Berkeley Mono", Menlo, Consolas, monospace;
  font-size: 13px;
  margin-bottom: 1.2rem;
}

:deep(.wiki-prose code) {
  background: rgba(110, 118, 129, 0.2);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 85%;
  font-family: "Berkeley Mono", Menlo, Consolas, monospace;
}

/* ── Internal Wiki Links ───────────────────────────────────────────── */
:deep(.wiki-internal-link) {
  color: #58a6ff;
  text-decoration: none;
  border-bottom: 1px dashed #58a6ff;
  cursor: pointer;
}

:deep(.wiki-internal-link:hover) {
  color: #79c0ff;
  border-bottom-style: solid;
}

/* ── Static Offline Citation Chips (Preventing Live Web Navigation) ── */
:deep(.offline-citation-chip) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 11px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #8b949e;
  margin: 0 3px;
  vertical-align: baseline;
  user-select: all;
}

:deep(.offline-citation-chip .chip-icon) {
  font-size: 10px;
}

:deep(.offline-citation-chip .chip-domain) {
  color: #c9d1d9;
  font-weight: 500;
}

:deep(.offline-citation-chip .chip-tag) {
  font-size: 9px;
  text-transform: uppercase;
  color: #f2cc60;
  background: rgba(242, 204, 96, 0.1);
  padding: 0 4px;
  border-radius: 2px;
}

/* ── Placeholder Screen ────────────────────────────────────────────── */
.wiki-placeholder {
  text-align: center;
  padding: 64px 24px;
  max-width: 540px;
  margin: auto;
}

.wiki-placeholder__icon {
  font-size: 48px;
  color: #58a6ff;
  margin-bottom: 16px;
}

.wiki-placeholder h2 {
  font-size: 22px;
  margin-bottom: 12px;
  color: #f0f6fc;
}

.wiki-placeholder p {
  color: #8b949e;
  line-height: 1.6;
  margin-bottom: 12px;
}

.wiki-placeholder__note {
  font-size: 13px;
  color: #3fb950 !important;
}

.wiki-placeholder__actions {
  margin-top: 24px;
}

.wiki-loading-content,
.wiki-loading,
.wiki-empty-tree {
  padding: 24px;
  text-align: center;
  color: #8b949e;
  font-size: 13px;
}

/* ── Search Trigger & Sidebar Tree Filter ────────────────────────── */
.wiki-search-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--usx-color-surface-variant, #161b22);
  color: var(--usx-color-text-muted, #8b949e);
  border: 1px solid var(--usx-color-border, #30363d);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.wiki-search-trigger:hover {
  background: var(--usx-color-surface, #21262d);
  border-color: #58a6ff;
  color: var(--usx-color-text, #c9d1d9);
}

.wiki-search-trigger__text {
  font-size: 12px;
}

.wiki-kbd {
  display: inline-block;
  padding: 1px 5px;
  font-size: 10px;
  font-family: inherit;
  font-weight: 600;
  color: #8b949e;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}

.wiki-tree-filter {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 4px 8px;
  margin: 8px 12px;
}

.wiki-tree-filter-input {
  background: transparent;
  border: none;
  color: #c9d1d9;
  font-size: 12px;
  width: 100%;
  outline: none;
}

/* ── Offline Search Modal (Cmd+K) ────────────────────────────────── */
.wiki-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 80px;
  z-index: 1000;
}

.wiki-search-modal {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  width: 100%;
  max-width: 680px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.wiki-search-modal__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid #30363d;
  background: #0d1117;
}

.wiki-search-modal__icon {
  color: #58a6ff;
  font-size: 20px;
}

.wiki-search-modal__input {
  flex: 1;
  background: transparent;
  border: none;
  color: #f0f6fc;
  font-size: 16px;
  outline: none;
}

.wiki-search-modal__filters {
  display: flex;
  gap: 6px;
  padding: 8px 16px;
  background: #0d1117;
  border-bottom: 1px solid #21262d;
  overflow-x: auto;
}

.wiki-filter-pill {
  background: transparent;
  border: 1px solid transparent;
  color: #8b949e;
  border-radius: 14px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.wiki-filter-pill:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #c9d1d9;
}

.wiki-filter-pill--active {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  font-weight: 600;
}

.wiki-search-modal__results {
  max-height: 420px;
  min-height: 180px;
  overflow-y: auto;
  padding: 8px 0;
}

.wiki-search-loading,
.wiki-search-empty,
.wiki-search-hint {
  padding: 32px 24px;
  text-align: center;
  color: #8b949e;
}

.wiki-search-empty p {
  margin: 8px 0 4px;
  color: #c9d1d9;
  font-size: 14px;
}

.wiki-search-hint p {
  margin-bottom: 12px;
  font-size: 13px;
  color: #8b949e;
  line-height: 1.5;
}

.wiki-search-quick-tags {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}

.quick-tag {
  background: #21262d;
  border: 1px solid #30363d;
  color: #58a6ff;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  cursor: pointer;
}

.quick-tag:hover {
  background: rgba(56, 189, 248, 0.15);
}

.wiki-results-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.wiki-result-item {
  padding: 10px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: background 0.12s ease;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wiki-result-item:hover,
.wiki-result-item--selected {
  background: rgba(56, 189, 248, 0.1);
}

.wiki-result-item__top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.wiki-result-item__title {
  font-weight: 600;
  color: #f0f6fc;
  font-size: 14px;
}

.wiki-result-item__title :deep(mark),
.wiki-result-item__snippet :deep(mark) {
  background: rgba(56, 189, 248, 0.35);
  color: #f0f6fc;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

.wiki-result-item__badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #21262d;
  color: #8b949e;
  border: 1px solid #30363d;
  text-transform: uppercase;
}

.wiki-result-item__snippet {
  margin: 0;
  font-size: 12px;
  color: #8b949e;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.wiki-result-item__meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #6e7681;
}

.wiki-result-item__path {
  font-family: monospace;
}

.wiki-search-modal__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 18px;
  background: #0d1117;
  border-top: 1px solid #30363d;
  font-size: 11px;
  color: #8b949e;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #3fb950;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.wiki-kbd-mini {
  display: inline-block;
  padding: 1px 4px;
  font-size: 9px;
  font-family: inherit;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 3px;
  margin-right: 4px;
}
</style>
