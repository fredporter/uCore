<template>
  <div
    class="documentation-surface"
    :class="{
      'surface--tab-nav-vertical': shell.tabOrientation === 'vertical',
    }"
  >
    <SurfaceTabNav
      v-model="activeTab"
      :tabs="TABS"
      :orientation="shell.tabOrientation"
      @toggle-orientation="shell.toggleTabOrientation()"
    />
    <div class="documentation-content-inner">
      <div class="documentation-content">
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

        <!-- Guide Tab -->
        <div v-if="activeTab === 'guide'">
          <div v-if="loading" class="doc-loading">
            <UIcon name="sync" /> Loading doc sites...
          </div>
          <div v-else-if="docSites.length > 0">
            <div class="doc-site-grid">
              <div
                v-for="site in docSites"
                :key="site.id"
                class="doc-site-hero"
                @click="viewingSite = site.id"
              >
                <div class="doc-site-hero-icon">
                  <UIcon name="menu_book" />
                </div>
                <div class="doc-site-hero-content">
                  <h4 class="doc-site-hero-title">{{ site.name }}</h4>
                  <p v-if="site.description" class="doc-site-hero-desc">
                    {{ site.description }}
                  </p>
                </div>
                <UBadge :type="site.built ? 'success' : 'warning'" size="sm">
                  {{ site.built ? "built" : "not built" }}
                </UBadge>
              </div>
            </div>
            <div v-if="viewingSite" class="doc-viewer">
              <div class="doc-viewer-bar">
                <span class="doc-viewer-label">{{ viewingSite }}</span>
                <UButton
                  size="sm"
                  variant="secondary"
                  icon="close"
                  @click="viewingSite = null"
                  >Close</UButton
                >
              </div>
              <iframe
                :src="`/api/docs/serve/${viewingSite}/`"
                :title="viewingSite"
                class="doc-frame"
              />
            </div>
          </div>
          <div v-else class="doc-empty">
            No doc sites found in ~/Public/doc-sites/.
          </div>

          <!-- Component Docs (mirror of in-repo docs/) -->
          <div class="doc-section doc-section--spaced">
            <h4 class="doc-section-title">Component Docs</h4>
            <div v-if="repoDocsLoading" class="doc-loading">
              <UIcon name="sync" /> Loading component docs...
            </div>
            <div v-else-if="repoDocs.length > 0">
              <div class="doc-section" v-for="repo in repoDocs" :key="repo.repo">
                <h4 class="doc-repo-title">
                  <UIcon name="code" />
                  {{ repo.repo }} — {{ repo.count }} docs
                </h4>
                <div class="doc-repo-list">
                  <div
                    v-for="doc in repo.docs"
                    :key="doc.path"
                    class="doc-repo-row"
                    role="button"
                    tabindex="0"
                    @click="openDoc('mirror', `${repo.repo}/${doc.path}`, doc.name)"
                    @keydown.enter="openDoc('mirror', `${repo.repo}/${doc.path}`, doc.name)"
                  >
                    <UIcon name="description" />
                    <span class="doc-repo-name">{{ doc.name }}</span>
                    <code class="doc-mono">{{ doc.path }}</code>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="doc-empty">No component docs found.</div>
          </div>
        </div>

        <!-- Knowledge Tab -->
        <div v-else-if="activeTab === 'knowledge'">
          <div v-if="knowledgeLoading" class="doc-loading">
            <UIcon name="sync" /> Loading knowledge library...
          </div>
          <div v-else-if="knowledgeSections.length > 0">
            <div class="doc-knowledge-grid">
              <div
                v-for="section in knowledgeSections"
                :key="section.id"
                class="doc-knowledge-card"
                role="button"
                tabindex="0"
                @click="openDoc('knowledge', section.id, section.name)"
                @keydown.enter="openDoc('knowledge', section.id, section.name)"
              >
                <div class="doc-knowledge-card-icon">
                  <UIcon name="book_2" />
                </div>
                <div class="doc-knowledge-card-content">
                  <h4 class="doc-knowledge-card-title">{{ section.name }}</h4>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="doc-empty">
            Knowledge library not found at ~/Public/global-knowledge/.
          </div>
        </div>

        <!-- Learning Tab -->
        <div v-else-if="activeTab === 'learning'">
          <LearningPanel @open="onLearningOpen" />
        </div>

        <!-- Publishing Tab -->
        <div v-else-if="activeTab === 'publish'">
          <div class="doc-section">
            <h4 class="doc-section-title">Export Vault</h4>
            <UButton
              size="sm"
              variant="primary"
              icon="publish"
              :disabled="exportRunning"
              @click="runExport"
            >
              {{ exportRunning ? "Exporting..." : "Export Vault to DocLang" }}
            </UButton>
            <div v-if="exportResult" class="doc-export-msg">
              <UBadge
                :type="exportResult.error ? 'error' : 'success'"
                size="sm"
              />
              <span>{{
                exportResult.error ? exportResult.error : exportResult.message
              }}</span>
            </div>
          </div>

          <div class="doc-section doc-section--spaced">
            <h4 class="doc-section-title">Publish Docs Site</h4>
            <p v-if="publishStatus?.built_at" class="doc-export-msg">
              Last built: {{ publishStatus.built_at }} ·
              {{ publishStatus.total_files }} files
            </p>
            <div class="doc-actions">
              <UButton
                size="sm"
                variant="primary"
                icon="publish"
                :disabled="publishing"
                @click="runPublish(false)"
              >
                {{ publishing ? "Building..." : "Build Docs Site" }}
              </UButton>
              <UButton
                size="sm"
                variant="secondary"
                icon="upload"
                :disabled="publishing"
                @click="runPublish(true)"
              >
                Build + Deploy
              </UButton>
            </div>
            <div v-if="publishResult" class="doc-export-msg">
              <UBadge
                :type="publishResult.status === 'error' ? 'error' : 'success'"
                size="sm"
              />
              <span>{{
                publishResult.status === "error"
                  ? publishResult.error || "Publish failed"
                  : "Published " +
                    (publishResult.build?.rendered_pages ?? 0) +
                    " pages"
              }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <transition name="doc-sidepanel">
      <aside v-if="viewingDoc" class="doc-sidepanel">
        <div class="doc-sidepanel__bar">
          <span class="doc-sidepanel__title">{{ viewingDoc.title }}</span>
          <button
            v-if="canEditDoc() && !editingDoc"
            class="doc-sidepanel__edit"
            title="Edit in Dev Mode"
            @click="startEdit"
          >
            <UIcon name="edit" />
          </button>
          <button
            class="doc-sidepanel__close"
            title="Close"
            @click="viewingDoc = null"
          >
            <UIcon name="close" />
          </button>
        </div>
        <div class="doc-sidepanel__body">
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
          <div v-else-if="editingDoc" class="doc-sidepanel__editor">
            <textarea
              v-model="draftContent"
              class="doc-sidepanel__textarea"
              spellcheck="false"
            />
            <div v-if="saveError" class="doc-sidepanel__error">
              {{ saveError }}
            </div>
            <div class="doc-sidepanel__editor-actions">
              <UButton
                size="sm"
                variant="primary"
                icon="save"
                :disabled="savingDoc"
                @click="saveDoc"
              >
                {{ savingDoc ? "Saving..." : "Save to repo" }}
              </UButton>
              <UButton
                size="sm"
                variant="secondary"
                icon="close"
                :disabled="savingDoc"
                @click="cancelEdit"
                >Cancel</UButton
              >
            </div>
          </div>
          <div
            v-else
            class="doc-sidepanel__content"
            v-html="renderDocMarkdown(viewingDoc.content)"
          />
        </div>
      </aside>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import { useDevModeStore } from "../../stores/devMode";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import UButton from "../../skills/atoms/UButton.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import LearningPanel from "./panels/LearningPanel.vue";

const shell = useShellStore();
const devMode = useDevModeStore();
const route = useRoute();
const router = useRouter();

const TABS = [
  { id: "guide", label: "Guide & Docs", icon: "menu_book" },
  { id: "knowledge", label: "Knowledge", icon: "auto_stories" },
  { id: "learning", label: "Learning", icon: "school" },
];
const VALID_DOC_TABS = new Set(TABS.map((tab) => tab.id));
const routeTab = String(route.query.tab || "");
const activeTab = ref(VALID_DOC_TABS.has(routeTab) ? routeTab : "guide");

if (routeTab === "publish") {
  router.replace({ path: "/workflow", query: { tab: "publish" } });
}

watch(activeTab, (tab) => {
  if (route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } });
  }
});

watch(
  () => route.query.tab,
  (tab) => {
    const normalized = String(tab || "guide");
    if (normalized === "publish") {
      router.replace({ path: "/workflow", query: { tab: "publish" } });
      return;
    }
    if (VALID_DOC_TABS.has(normalized)) activeTab.value = normalized;
  },
);

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
const publishStatus = ref<Record<string, any> | null>(null);
const publishing = ref(false);
const publishResult = ref<Record<string, any> | null>(null);
const viewingSite = ref<string | null>(null);
const viewingDoc = ref<{
  title: string;
  content: string;
  source: string;
  path: string;
  listing?: { name: string; path: string; is_dir: boolean }[];
} | null>(null);
const docLoading = ref(false);
const editingDoc = ref(false);
const draftContent = ref("");
const savingDoc = ref(false);
const saveError = ref<string | null>(null);
const isDevMode = computed(() => devMode.showDevContent);
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

function renderDocMarkdown(content: string): string {
  return content
    .replace(/^# (.+)$/gm, "<h2>$1</h2>")
    .replace(/^## (.+)$/gm, "<h3>$1</h3>")
    .replace(/^### (.+)$/gm, "<h4>$1</h4>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

async function openDoc(source: string, path: string, title: string) {
  viewingDoc.value = { title, content: "", source, path };
  docLoading.value = true;
  try {
    const res = await fetch(
      `/api/docs/content?source=${encodeURIComponent(source)}&path=${encodeURIComponent(path)}`,
      { signal: AbortSignal.timeout(8000) },
    );
    if (res.ok) {
      const data = await res.json();
      viewingDoc.value = {
        title: data.title || title,
        content: data.content || "",
        source,
        path,
        listing: data.listing,
      };
    } else {
      viewingDoc.value = { title, content: "Unable to load document.", source, path };
    }
  } catch {
    viewingDoc.value = { title, content: "Unable to load document.", source, path };
  } finally {
    docLoading.value = false;
  }
}

function onLearningOpen(course: {
  name: string;
  path: string;
  source?: string;
  title?: string;
}) {
  openDoc(course.source || "learning", course.path, course.title || course.name);
}

function canEditDoc(): boolean {
  return (
    isDevMode.value &&
    viewingDoc.value?.source === "mirror" &&
    !viewingDoc.value?.listing
  );
}

function startEdit() {
  if (!viewingDoc.value) return;
  draftContent.value = viewingDoc.value.content;
  saveError.value = null;
  editingDoc.value = true;
}

function cancelEdit() {
  editingDoc.value = false;
  draftContent.value = "";
  saveError.value = null;
}

async function saveDoc() {
  if (!viewingDoc.value) return;
  const [repo, ...rest] = viewingDoc.value.path.split("/");
  const docPath = rest.join("/");
  if (!repo || !docPath) {
    saveError.value = "Invalid mirror path";
    return;
  }
  savingDoc.value = true;
  saveError.value = null;
  try {
    const res = await fetch(`/api/docs/mirror/push`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo, path: docPath, content: draftContent.value }),
      signal: AbortSignal.timeout(15000),
    });
    const data = await res.json();
    if (res.ok && data.success) {
      viewingDoc.value.content = draftContent.value;
      editingDoc.value = false;
    } else {
      saveError.value = data.error || `Push failed (${res.status})`;
    }
  } catch (e: any) {
    saveError.value = e.message || "Save failed";
  } finally {
    savingDoc.value = false;
  }
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

async function fetchPublishStatus() {
  try {
    const res = await fetch(`/api/docs/publish/status`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      publishStatus.value = await res.json();
    }
  } catch {
    publishStatus.value = null;
  }
}

async function runPublish(deploy = false) {
  publishing.value = true;
  publishResult.value = null;
  try {
    const res = await fetch(`/api/docs/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ deploy }),
      signal: AbortSignal.timeout(120000),
    });
    const data = await res.json();
    publishResult.value = data;
    if (res.ok) {
      await fetchPublishStatus();
    }
  } catch (e: any) {
    publishResult.value = {
      status: "error",
      error: e.message || "Publish failed",
    };
  } finally {
    publishing.value = false;
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

onMounted(() => {
  devMode.probe();
  fetchDocSites();
  fetchKnowledgeSections();
  probeExportEndpoint();
  probeCoursesEndpoint();
  fetchRepoDocs();
  fetchPublishStatus();
});
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

.doc-sidepanel__edit {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  border: none;
  background: transparent;
  color: var(--usx-color-primary);
  cursor: pointer;
  border-radius: var(--usx-radius-full);
}

.doc-sidepanel__edit:hover {
  background: var(--usx-color-surface-variant);
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

.doc-sidepanel__editor {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  height: 100%;
}

.doc-sidepanel__textarea {
  flex: 1;
  min-height: var(--usx-touch-min);
  padding: var(--usx-spacing-md);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  line-height: var(--usx-line-height-relaxed);
  color: var(--usx-color-on-surface);
  background: var(--usx-color-surface-variant);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  resize: vertical;
}

.doc-sidepanel__error {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-danger);
}

.doc-sidepanel__editor-actions {
  display: flex;
  gap: var(--usx-spacing-sm);
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
</style>
