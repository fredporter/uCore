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
      <!-- 1. Local Wikipedia Tab (Default Serene View) -->
      <div v-if="activeTab === 'wiki'" class="doc-wiki-wrapper">
        <LocalWikiReader />
      </div>

      <!-- 2. Learning Curriculum Tab -->
      <div v-else-if="activeTab === 'learning'" class="doc-learning-wrapper">
        <LearningPanel @open="onLearningOpen" />
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
              <h3 style="margin: 0 0 0.5rem 0;">External Engineering & Ecosystem Architecture</h3>
              <p style="margin: 0; color: var(--usx-color-on-surface-muted);">
                In accordance with the sovereign architecture contract (AGENTS.md), in-browser development mode is retired.
                All software engineering, testing, and agent workflows belong in external developer tooling (Antigravity IDE, agy CLI, and Codex).
                uCore acts as the sovereign user runtime host, document binder manager, and execution bridge.
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
            <h4 class="doc-section-title">Ecosystem Workspace Boundary (AGENTS.md)</h4>
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
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import UButton from "../../skills/atoms/UButton.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import LearningPanel from "./panels/LearningPanel.vue";
import LocalWikiReader from "./LocalWikiReader.vue";

const shell = useShellStore();
const route = useRoute();
const router = useRouter();

const TABS = [
  { id: "wiki", label: "Local Wikipedia", icon: "auto_stories" },
  { id: "learning", label: "Learn to Code", icon: "school" },
  { id: "developer", label: "Developer & Tooling", icon: "terminal" },
];
const VALID_DOC_TABS = new Set(TABS.map((tab) => tab.id));
const routeTab = String(route.query.tab || "");

function normalizeDocTab(tab: string): string {
  if (tab === "guide" || tab === "knowledge") return "wiki";
  if (VALID_DOC_TABS.has(tab)) return tab;
  return "wiki";
}

const activeTab = ref(normalizeDocTab(routeTab));

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
    const normalized = normalizeDocTab(String(tab || "wiki"));
    if (String(tab || "") === "publish") {
      router.replace({ path: "/workflow", query: { tab: "publish" } });
      return;
    }
    activeTab.value = normalized;
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
  return false;
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
