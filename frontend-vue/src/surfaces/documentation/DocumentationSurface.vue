<template>
  <div
    class="documentation-surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="visibleTabs"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="documentation-content-inner" :class="{ 'documentation-content-inner--reader': activeTab === 'wiki' }">
      <!-- 1. Local Wikipedia Tab (Default Serene View) -->
      <div v-if="activeTab === 'wiki'" class="doc-wiki-wrapper">
        <LocalWikiReader />
      </div>

      <!-- 2. Learning Curriculum Tab -->
      <div v-else-if="activeTab === 'learning'" class="doc-learning-wrapper">
        <LearningPanel :active-path="viewingDoc?.path" @open="onLearningOpen" @catalog="readingQueue = $event" />
      </div>

      <!-- 3. Developer & Engineering Tooling Tab -->
      <div v-else-if="activeTab === 'developer'" class="documentation-content">
        <!-- Diagnostic & Health strip inside Developer tab -->
        <div class="doc-health-strip">
          <div class="doc-health-item">
            <span class="doc-health-label">Sites API</span>
            <UBadge :type="statusType(apiStatus.sites)">
              {{ statusText(apiStatus.sites) }}
            </UBadge>
          </div>
          <div class="doc-health-item">
            <span class="doc-health-label">Knowledge API</span>
            <UBadge :type="statusType(apiStatus.knowledge)">
              {{ statusText(apiStatus.knowledge) }}
            </UBadge>
          </div>
          <div class="doc-health-item">
            <span class="doc-health-label">Courses API</span>
            <UBadge :type="statusType(apiStatus.courses)">
              {{ statusText(apiStatus.courses) }}
            </UBadge>
          </div>
          <div class="doc-health-item">
            <span class="doc-health-label">Export API</span>
            <UBadge :type="statusType(apiStatus.export)">
              {{ statusText(apiStatus.export) }}
            </UBadge>
          </div>
        </div>

        <div class="doc-export-summary" v-if="lastExportAt">
          <UIcon name="schedule" />
          <span>Last export: {{ lastExportAt }}</span>
        </div>

        <!-- Developer & Engineering Tooling Content -->
        <div class="doc-section doc-developer-section">
          <div class="doc-hero-banner">
            <UIcon name="terminal" class="doc-hero-icon" />
            <div class="doc-hero-text">
              <h3 style="margin: 0 0 0.5rem 0;">Developer tools</h3>
              <p style="margin: 0; color: var(--usx-color-on-surface-muted);">
                Use Codex or your desktop development tools to extend uCore.
              </p>
            </div>
          </div>

          <div class="doc-tool-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--usx-spacing-md); margin-top: var(--usx-spacing-md);">
            <div class="doc-tool-card" style="padding: var(--usx-spacing-md); background: var(--usx-color-surface-variant); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md);">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <UIcon name="computer" />
                <h4 style="margin: 0;">Antigravity IDE & Codex</h4>
              </div>
              <p style="font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: 0.75rem;">External desktop IDE with pair programming, architectural planning, multi-repository intelligence, and visual artifacts.</p>
              <div><code style="font-size: var(--usx-font-size-xs);">AGENTS.md contract compliant</code></div>
            </div>

            <div class="doc-tool-card" style="padding: var(--usx-spacing-md); background: var(--usx-color-surface-variant); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md);">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <UIcon name="code" />
                <h4 style="margin: 0;">Antigravity CLI (agy)</h4>
              </div>
              <p style="font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: 0.75rem;">CLI execution environment for autonomous tasks, cron schedules, background workers, and subagent orchestration.</p>
              <div><code style="font-size: var(--usx-font-size-xs);">agy run / agy agent</code></div>
            </div>

            <div class="doc-tool-card" style="padding: var(--usx-spacing-md); background: var(--usx-color-surface-variant); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md);">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <UIcon name="hub" />
                <h4 style="margin: 0;">Model Context Protocol (MCP)</h4>
              </div>
              <p style="font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: 0.75rem;">Standardized integration protocols connecting external IDEs and agents directly to uCore APIs, vaults, and repositories.</p>
              <div><code style="font-size: var(--usx-font-size-xs);">mcp-server-git / mcp-filesystem</code></div>
            </div>

            <div class="doc-tool-card" style="padding: var(--usx-spacing-md); background: var(--usx-color-surface-variant); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md);">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <UIcon name="article" />
                <h4 style="margin: 0;">Obsidian Baseline Authoring</h4>
              </div>
              <p style="font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted); margin-bottom: 0.75rem;">Obsidian is the primary user authoring standard for notes, binders, and canvases. Filesystem authority with zero database lock-in.</p>
              <div><code style="font-size: var(--usx-font-size-xs);">~/Vault · ~/Shared · ~/Public</code></div>
            </div>
          </div>

          <div class="doc-section doc-section--spaced" style="margin-top: var(--usx-spacing-lg);">
            <h4 class="doc-section-title">Workspace storage</h4>
            <div style="padding: var(--usx-spacing-md); background: var(--usx-color-surface-variant); border-left: 4px solid var(--usx-color-primary); border-radius: var(--usx-radius-sm);">
              <ul style="margin: 0; padding-left: 1.25rem; font-size: var(--usx-font-size-sm);">
                <li><strong>Repository Source:</strong> All repos belong under <code>~/Code/&lt;repo&gt;</code>.</li>
                <li><strong>Mutable State:</strong> Owned by <code>UDOS_HOME</code> (default <code>~/Code/.udos</code>). Never write state directly to <code>$HOME</code>.</li>
                <li><strong>User Documents:</strong> Pure UTF-8 markdown in <code>~/Vault</code>, <code>~/Shared</code>, and <code>~/Public</code>.</li>
                <li><strong>Validation:</strong> Run <code>python3 scripts/check_home_path_policy.py</code> before committing path changes.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <transition name="doc-sidepanel">
      <aside v-if="viewingDoc" ref="readerPane" class="doc-sidepanel" :class="{ 'doc-sidepanel--fullscreen': readerFullscreen }" role="region" aria-label="Reading view">
        <div class="doc-sidepanel__bar">
          <button class="usx-btn" aria-label="Return to library" @click="closeReader"><UIcon name="library_books" /></button>
          <span class="doc-sidepanel__title">{{ viewingDoc.title }}</span>
          <button ref="fullscreenButton" class="usx-btn" :aria-label="readerFullscreen ? 'Exit full screen' : 'Full screen'" :aria-pressed="readerFullscreen" @click="readerFullscreen = !readerFullscreen"><UIcon :name="readerFullscreen ? 'fullscreen_exit' : 'fullscreen'" /></button>
          <button
            class="usx-btn doc-sidepanel__close"
            title="Close"
            @click="closeReader"
          >
            <UIcon name="close" />
          </button>
        </div>
        <nav class="reading-location" aria-label="Reading location">
          <span>{{ viewingDoc.source }} / {{ viewingDoc.path }}</span>
          <div>
            <button class="usx-btn" aria-label="Previous document" :disabled="readingPosition <= 0 || docLoading" @click="navigateReading(-1)"><UIcon name="chevron_left" /></button>
            <span v-if="readingPosition >= 0">{{ readingPosition + 1 }} of {{ readingQueue.length }}</span>
            <button class="usx-btn" aria-label="Next document" :disabled="readingPosition < 0 || readingPosition >= readingQueue.length - 1 || docLoading" @click="navigateReading(1)"><UIcon name="chevron_right" /></button>
            <button v-if="parentPath" class="usx-btn" @click="openDoc(viewingDoc.source, parentPath, 'Contents')">Up one folder</button>
          </div>
        </nav>
        <div ref="readerBody" class="doc-sidepanel__body">
          <div v-if="docLoading" class="doc-loading">
            <UIcon name="sync" /> Loading...
          </div>
          <div v-else-if="viewingDoc.listing" class="doc-sidepanel__listing">
            <div
              v-for="item in viewingDoc.listing"
              :key="item.path"
              class="doc-sidepanel__row"
              role="button"
              tabindex="0"
              @click="openDoc(viewingDoc.source, item.path, item.name)"
              @keydown.enter="openDoc(viewingDoc.source, item.path, item.name)"
            >
              <UIcon :name="item.is_dir ? 'folder' : 'description'" />
              <span class="doc-sidepanel__row-name">{{ item.name }}</span>
            </div>
            <div v-if="viewingDoc.listing.length === 0" class="doc-empty">
              Empty folder.
            </div>
          </div>
          <DocumentArticle v-else :content="viewingDoc.content" @navigate="openRelativeDocument" />
        </div>
      </aside>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useSettingsStore } from "../../stores/settings";
import DocumentArticle from "../../skills/molecules/DocumentArticle.vue";
import { containReaderKeys } from "../../utils/readingDocument";
import { useShellStore } from "../../stores/shell";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import LearningPanel from "./panels/LearningPanel.vue";
import LocalWikiReader from "./LocalWikiReader.vue";

const shell = useShellStore();
const settings = useSettingsStore();
const route = useRoute();
const router = useRouter();

const TABS = [
  { id: "wiki", label: "Knowledge", icon: "auto_stories" },
  { id: "learning", label: "uCode", icon: "school" },
  { id: "developer", label: "Advanced", icon: "terminal" },
];
const visibleTabs = computed(() => TABS.filter(tab => tab.id !== "developer" || settings.advancedView));
const VALID_DOC_TABS = new Set(TABS.map((tab) => tab.id));
const routeTab = String(route.query.tab || "");

function normalizeDocTab(tab: string): string {
  if (tab === "guide" || tab === "knowledge") return "wiki";
  if (tab === "advanced") tab = "developer";
  if (tab === "ucode") tab = "learning";
  if (tab === "developer" && !settings.advancedView) return "wiki";
  if (VALID_DOC_TABS.has(tab)) return tab;
  return "wiki";
}

const activeTab = ref(normalizeDocTab(routeTab));

if (routeTab === "publish") {
  router.replace({ path: "/workflow", query: { tab: "publish" } });
}

watch(activeTab, (tab) => {
  if (routeTab !== "publish" && route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } });
  }
}, { immediate: true });

watch(
  () => route.query.tab,
  (tab) => {
    const normalized = normalizeDocTab(String(tab || "wiki"));
    if (String(tab || "") === "publish") {
      router.replace({ path: "/workflow", query: { tab: "publish" } });
      return;
    }
    activeTab.value = normalized;
  },
);

interface ReadingReference { title?: string; name: string; source?: string; path: string }
const readingQueue = ref<ReadingReference[]>([]);
const readerFullscreen = ref(false);
const readerPane = ref<HTMLElement | null>(null);
const fullscreenButton = ref<HTMLElement | null>(null);
const readerBody = ref<HTMLElement | null>(null);
let readerOpener: HTMLElement | null = null;
const readingPosition = computed(() => readingQueue.value.findIndex(item => item.path === viewingDoc.value?.path && (item.source || "learning") === viewingDoc.value?.source));
const parentPath = computed(() => viewingDoc.value?.path.includes("/") ? viewingDoc.value.path.slice(0, viewingDoc.value.path.lastIndexOf("/")) : "");
function closeReader() { ++readerRequest; docLoading.value = false; viewingDoc.value = null; readerFullscreen.value = false; void nextTick(() => readerOpener?.focus()); }
function navigateReading(offset: number) { const item = readingQueue.value[readingPosition.value + offset]; if (item) void openDoc(item.source || "learning", item.path, item.title || item.name); }
function readerKeydown(event: KeyboardEvent) { containReaderKeys(event, readerPane.value, readerFullscreen.value, () => { readerFullscreen.value = false; fullscreenButton.value?.focus(); }); }
watch(readerFullscreen, async () => { await nextTick(); fullscreenButton.value?.focus(); });
onMounted(() => document.addEventListener("keydown", readerKeydown));
onBeforeUnmount(() => document.removeEventListener("keydown", readerKeydown));
function openRelativeDocument(href: string) {
  if (!viewingDoc.value) return;
  const base = viewingDoc.value.path.split("/").slice(0, -1);
  for (const part of href.split('#')[0].split('/')) { if (part === '..') base.pop(); else if (part && part !== '.') base.push(decodeURIComponent(part)); }
  void openDoc(viewingDoc.value.source, base.join('/'), base.at(-1) || 'Document');
}
watch(() => settings.advancedView, enabled => { if (!enabled && activeTab.value === "developer") activeTab.value = "wiki"; });

interface DocSite {
  id: string;
  name: string;
  path: string;
  description?: string;
  built: boolean;
}
interface Section {
  id: string;
  name: string;
  path: string;
}
interface RepoDocItem {
  name: string;
  path: string;
  size: number;
}
interface RepoDocGroup {
  repo: string;
  root: string;
  docs: RepoDocItem[];
  count: number;
}

const loading = ref(true);
const knowledgeLoading = ref(true);
const repoDocsLoading = ref(true);
const exportRunning = ref(false);
const exportResult = ref<Record<string, any> | null>(null);
const viewingSite = ref<string | null>(null);
const viewingDoc = ref<{
  title: string;
  content: string;
  source: string;
  path: string;
  listing?: { name: string; path: string; is_dir: boolean }[];
} | null>(null);
const docLoading = ref(false);
const lastExportAt = ref<string | null>(null);

const docSites = ref<DocSite[]>([]);
const knowledgeSections = ref<Section[]>([]);
const repoDocs = ref<RepoDocGroup[]>([]);

type ApiStatus = "pending" | "ok" | "error";

const apiStatus = ref<{
  sites: ApiStatus;
  knowledge: ApiStatus;
  courses: ApiStatus;
  export: ApiStatus;
}>({
  sites: "pending",
  knowledge: "pending",
  courses: "pending",
  export: "pending",
});

async function fetchDocSites() {
  loading.value = true;
  try {
    const res = await fetch(`/api/docs/sites`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      docSites.value = data.sites || [];
      apiStatus.value.sites = "ok";
    } else {
      apiStatus.value.sites = "error";
    }
  } catch {
    apiStatus.value.sites = "error";
  }
  loading.value = false;
}

async function fetchKnowledgeSections() {
  knowledgeLoading.value = true;
  try {
    const res = await fetch(`/api/docs/global-knowledge`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      knowledgeSections.value = data.sections || [];
      apiStatus.value.knowledge = "ok";
    } else {
      apiStatus.value.knowledge = "error";
    }
  } catch {
    apiStatus.value.knowledge = "error";
  }
  knowledgeLoading.value = false;
}

async function probeExportEndpoint() {
  try {
    const res = await fetch(`/api/docs/export`, {
      signal: AbortSignal.timeout(3000),
    });
    apiStatus.value.export = res.ok ? "ok" : "error";
  } catch {
    apiStatus.value.export = "error";
  }
}

async function fetchRepoDocs() {
  repoDocsLoading.value = true;
  try {
    const res = await fetch(`/api/docs/repo-docs`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      repoDocs.value = data.repos || [];
    }
  } catch {
    repoDocs.value = [];
  }
  repoDocsLoading.value = false;
}

async function probeCoursesEndpoint() {
  try {
    const res = await fetch(`/api/docs/courses`, {
      signal: AbortSignal.timeout(3000),
    });
    apiStatus.value.courses = res.ok ? "ok" : "error";
  } catch {
    apiStatus.value.courses = "error";
  }
}

let readerRequest = 0;
async function openDoc(source: string, path: string, title: string) {
  const request = ++readerRequest;
  viewingDoc.value = { title, content: "", source, path };
  docLoading.value = true;
  try {
    const res = await fetch(
      `/api/docs/content?source=${encodeURIComponent(source)}&path=${encodeURIComponent(path)}`,
      { signal: AbortSignal.timeout(8000) },
    );
    if (res.ok) {
      const data = await res.json();
      if (request !== readerRequest) return;
      if (data.listing?.some((item: any) => !item.is_dir)) readingQueue.value = data.listing.filter((item: any) => !item.is_dir).map((item: any) => ({ ...item, source }));
      viewingDoc.value = {
        title: data.title || title,
        content: data.content || "",
        source,
        path,
        listing: data.listing,
      };
    } else if (request === readerRequest) {
      viewingDoc.value = { title, content: "Unable to load document.", source, path };
    }
  } catch {
    if (request !== readerRequest) return;
    viewingDoc.value = { title, content: "Unable to load document.", source, path };
  } finally {
    if (request === readerRequest) docLoading.value = false;
    await nextTick();
    readerBody.value?.scrollTo?.({ top: 0 });
  }
}

function onLearningOpen(course: {
  name: string;
  path: string;
  source?: string;
  title?: string;
}) {
  readerOpener = document.activeElement as HTMLElement;
  void openDoc(course.source || "learning", course.path, course.title || course.name);
}

async function runExport() {
  exportRunning.value = true;
  exportResult.value = null;
  try {
    const res = await fetch(`/api/docs/export`, {
      method: "POST",
      signal: AbortSignal.timeout(60000),
    });
    const data = await res.json();
    exportResult.value = data;
    apiStatus.value.export = res.ok ? "ok" : "error";
    if (res.ok && !data.error) {
      lastExportAt.value = new Date().toLocaleString();
    }
    await fetchDocSites();
  } catch (e: any) {
    apiStatus.value.export = "error";
    exportResult.value = { error: e.message || "Export failed" };
  } finally {
    exportRunning.value = false;
  }
}

function statusType(status: ApiStatus): "success" | "warning" | "error" {
  if (status === "ok") return "success";
  if (status === "error") return "error";
  return "warning";
}

function statusText(status: ApiStatus): string {
  if (status === "ok") return "Online";
  if (status === "error") return "Offline";
  return "Checking";
}

function loadAdvancedDocumentation() {
  fetchDocSites();
  fetchKnowledgeSections();
  probeExportEndpoint();
  probeCoursesEndpoint();
  fetchRepoDocs();
}
watch([activeTab, () => settings.advancedView], ([tab, advanced]) => { if (tab === "developer" && advanced) loadAdvancedDocumentation(); }, { immediate: true });
</script>

<style scoped>
/* ─── Surface shell (mirrors DeveloperSurface.vue) ────────────── */
.documentation-surface {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.documentation-content-inner {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--usx-spacing-xl);
  box-sizing: border-box;
}

.documentation-content {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.doc-health-strip {
  --doc-column-min: calc(var(--usx-touch-min) * 3.5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--doc-column-min)), 1fr)
  );
  gap: var(--usx-spacing-sm);
  min-width: 0;
}

.doc-health-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
}

.doc-health-label {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.doc-export-summary {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

/* ─── Loading / Empty ──────────────────────────────────────────── */
.doc-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.doc-empty {
  padding: var(--usx-spacing-xl);
  text-align: center;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

/* ─── Sections ─────────────────────────────────────────────────── */
.doc-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.doc-section-title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: var(--usx-letter-spacing-wide);
}

/* ─── Doc site hero cards ──────────────────────────────────────── */
.doc-site-grid {
  --doc-column-min: calc(var(--usx-touch-min) * 5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--doc-column-min)), 1fr)
  );
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.doc-site-hero {
  display: flex;
  align-items: flex-start;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid
    color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
  border-radius: var(--usx-radius-md);
  cursor: pointer;
  min-width: 0;
  transition:
    background var(--usx-transition-fast),
    border-color var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.doc-site-hero:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 4%, transparent);
  border-color: color-mix(in srgb, var(--usx-color-primary) 20%, transparent);
  transform: translateY(calc(var(--usx-spacing-1) * -1));
}

.doc-site-hero-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  flex-shrink: 0;
  font-size: var(--usx-icon-size-lg);
}

.doc-site-hero:hover .doc-site-hero-icon {
  background: var(--usx-color-primary-disabled);
}

.doc-site-hero-content {
  flex: 1;
  min-width: 0;
}

.doc-site-hero-title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  margin: 0 0 var(--usx-spacing-xs) 0;
  color: var(--usx-color-on-surface);
}

.doc-site-hero-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  margin: 0;
  line-height: var(--usx-line-height-tight);
}

/* ─── Knowledge cards ──────────────────────────────────────────── */
.doc-knowledge-grid {
  --doc-column-min: calc(var(--usx-touch-min) * 5);
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, var(--doc-column-min)), 1fr)
  );
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.doc-knowledge-card {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  min-width: 0;
  min-height: var(--usx-touch-min);
  cursor: pointer;
  transition:
    border-color var(--usx-transition-fast),
    transform var(--usx-transition-fast);
}

.doc-knowledge-card:hover {
  border-color: var(--usx-color-primary);
  transform: translateY(calc(var(--usx-spacing-2) * -1));
}

.doc-knowledge-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border-radius: var(--usx-radius-md);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-primary);
  flex-shrink: 0;
  font-size: var(--usx-icon-size-lg);
}

.doc-knowledge-card-content {
  flex: 1;
  min-width: 0;
}

.doc-knowledge-card-title {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  margin: 0;
  text-transform: capitalize;
}

/* ─── Viewer ────────────────────────────────────────────────────── */
.doc-viewer {
  margin-top: var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  overflow: hidden;
  flex-shrink: 0;
}

.doc-viewer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface-variant);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.doc-viewer-label {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.doc-frame {
  width: 100%;
  height: calc(var(--usx-touch-min) * 10);
  border: none;
  display: block;
}

.doc-frame--tall {
  height: calc(100vh - 18rem);
  min-height: calc(var(--usx-touch-min) * 12);
}

/* ─── Publishing ────────────────────────────────────────────────── */
.doc-mono {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 24ch;
}

.doc-export-msg {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
}

.doc-actions {
  display: flex;
  gap: var(--usx-spacing-sm);
  margin-top: var(--usx-spacing-sm);
}

/* ─── Repo Docs ────────────────────────────────────────────────── */
.doc-section--spaced {
  margin-top: var(--usx-spacing-xl);
}

.doc-repo-title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  margin: var(--usx-spacing-md) 0 var(--usx-spacing-xs);
}

.doc-repo-list {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  margin-top: var(--usx-spacing-xs);
}

.doc-repo-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  min-height: var(--usx-touch-min);
}

.doc-repo-row:hover {
  background: var(--usx-color-surface-variant);
}

.doc-repo-name {
  font-weight: var(--usx-font-weight-medium);
  flex: 1;
}

/* ─── Side Panel Viewer ─────────────────────────────────────────── */
.doc-sidepanel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(480px, 100vw);
  display: flex;
  flex-direction: column;
  background: var(--usx-color-surface);
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  box-shadow: var(--usx-shadow-lg);
  z-index: 1000;
}

.doc-sidepanel__bar {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.doc-sidepanel__title {
  flex: 1;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.doc-sidepanel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  border-radius: var(--usx-radius-full);
}

.doc-sidepanel__close:hover {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
}

.doc-sidepanel__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
}

.doc-sidepanel__content {
  font-size: var(--usx-font-size-base);
  line-height: var(--usx-line-height-relaxed);
  color: var(--usx-color-on-surface);
  overflow-wrap: break-word;
}

.doc-sidepanel__listing {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.doc-sidepanel__row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  cursor: pointer;
  min-height: var(--usx-touch-min);
}

.doc-sidepanel__row:hover {
  background: var(--usx-color-surface-variant);
}

.doc-sidepanel__row-name {
  flex: 1;
}

.doc-sidepanel-enter-active,
.doc-sidepanel-leave-active {
  transition: transform var(--usx-transition-slow);
}

.doc-sidepanel-enter-from,
.doc-sidepanel-leave-to {
  transform: translateX(100%);
}

.doc-wiki-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.doc-learning-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-md);
}
</style>

<style scoped>
.doc-sidepanel--fullscreen { inset: 0; width: 100%; max-width: none; border: 0; }
.doc-sidepanel__bar { flex-shrink: 0; gap: var(--usx-spacing-xs); font-family: var(--usx-font-family-sans, Inter, sans-serif); }
.doc-sidepanel__bar .usx-btn { padding: var(--usx-spacing-xs); flex-shrink: 0; }
.reading-location { padding: var(--usx-spacing-sm) var(--usx-spacing-md); border-bottom: 1px solid var(--usx-color-border); font-family: var(--usx-font-family-sans, Inter, sans-serif); font-size: var(--usx-font-size-sm); overflow-wrap: anywhere; }
.reading-location > div { display: flex; align-items: center; gap: var(--usx-spacing-xs); }
.doc-sidepanel__body { overflow-y: auto; padding: clamp(1rem, 3vw, 3rem); }
.doc-tool-card, .doc-section { text-align: left; }

.doc-sidepanel__bar { box-sizing: border-box; min-height: 48px; height: 48px; padding: 4px 12px; gap: 8px; }
.doc-sidepanel__bar button.usx-btn { display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; flex: 0 0 36px; width: 36px; height: 36px; min-height: 36px; margin: 0; padding: 0; border: 0; box-shadow: none; background: transparent; color: var(--usx-color-on-surface-muted); border-radius: var(--usx-radius-sm); }
.doc-sidepanel__bar button.usx-btn:hover { background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); }
.doc-sidepanel__bar button.usx-btn:focus-visible { outline: 2px solid var(--usx-color-primary); outline-offset: 1px; }
.doc-sidepanel__bar :deep(.u-icon) { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; font-size: 20px; line-height: 1; }
.doc-sidepanel__title { min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; line-height: 1.25; }
.reading-location { padding: 6px 12px; gap: 8px; }
.reading-location > div { display: flex; align-items: center; gap: 4px; }
.reading-location .usx-btn { display: inline-flex; align-items: center; justify-content: center; height: 32px; min-height: 32px; padding: 0 6px; margin: 0; border: 0; background: transparent; line-height: 1; }

.documentation-content-inner.documentation-content-inner--reader { padding: 0; gap: 0; overflow: hidden; }
.documentation-content-inner--reader .doc-wiki-wrapper { margin: 0; padding: 0; min-height: 0; height: 100%; }
</style>
