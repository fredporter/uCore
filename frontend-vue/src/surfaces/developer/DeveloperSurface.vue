<template>
  <div class="dev-surface" :class="{ 'surface--tab-nav-vertical': shell.tabOrientation === 'vertical' }">
    <SurfaceTabNav v-model="activeTab" :tabs="DEV_TABS" :orientation="shell.tabOrientation" @toggle-orientation="shell.toggleTabOrientation()" />
    <div class="surface__body" :class="{ 'surface__body--has-sidebar': showSidebar }">
      <aside v-if="showSidebar" class="dev-sidebar">
        <div class="dev-sidebar__header">
          <span>{{ sidebarRepo ? sidebarRepo : "Select repo" }}</span>
          <button class="dev-sidebar__close" @click="closeSidebar()">&times;</button>
        </div>
        <div class="dev-sidebar__body">
          <div v-if="loadingRepos" class="dev-loading"><UIcon name="sync" /> Loading...</div>
          <template v-else-if="!sidebarRepo">
            <div v-for="repo in repos" :key="repo.name" class="dev-file-row" @click="openSidebarRepo(repo.name)">
              <UIcon name="folder" class="dev-file-icon" />
              <span class="dev-file-name">{{ repo.name }}</span>
              <code class="dev-file-path">{{ repo.branch }}</code>
            </div>
          </template>
          <template v-else>
            <div class="dev-search">
              <UIcon name="search" />
              <input v-model="fileFilter" aria-label="Filter repository files" placeholder="Filter files…" @keydown.enter="searchRepository" />
              <button :disabled="!fileFilter.trim()" title="Search file contents" @click="searchRepository"><UIcon name="manage_search" /></button>
            </div>
            <div v-if="searching" class="dev-loading"><UIcon name="sync" /> Searching…</div>
            <div v-else-if="searchResults.length" class="dev-search-results">
              <button v-for="match in searchResults" :key="`${match.path}:${match.line}`" @click="selectFile(match.path)">
                <strong>{{ match.path }}:{{ match.line }}</strong><span>{{ match.preview }}</span>
              </button>
              <button class="dev-search-results__clear" @click="searchResults=[]">Clear content results</button>
            </div>
            <div v-if="loadingFiles" class="dev-loading"><UIcon name="sync" /> Loading...</div>
            <div v-for="node in visibleTree" :key="node.path" class="dev-file-row" :style="{ paddingLeft: (8 + node.depth * 16) + 'px' }" @click="node.isDir ? toggleDir(node.path) : selectFile(node.path)" :class="{ 'dev-file-row--active': !node.isDir && activePath === node.path }">
              <UIcon :name="node.isDir ? (expandedDirs.has(node.path) ? 'folder_open' : 'folder') : 'description'" class="dev-file-icon" />
              <span class="dev-file-name">{{ node.name }}</span>
            </div>
          </template>
        </div>
      </aside>
      <div class="surface__content">
        <div v-if="activeTab==='code'" class="dev-repo-grid">
          <div class="dev-lane-bar">
            <button :class="{active:devLane==='core'}" @click="devLane='core'">Code</button>
            <button :class="{active:devLane==='extension'}" @click="devLane='extension'">Extensions</button>
            <button :class="{active:devLane==='project'}" @click="devLane='project'">Projects</button>
          </div>
          <div v-if="loadingRepos" class="dev-loading"><UIcon name="sync" /> Loading...</div>
          <div v-else class="dev-repo-grid__cards">
            <div v-for="repo in filteredRepos" :key="repo.name" class="dev-repo-card" @click="openRepoFromCard(repo)">
              <div class="dev-repo-card__header"><UIcon name="folder" /><span>{{ repo.name }}</span><UBadge :type="repo.status === 'clean' ? 'success' : 'warning'" size="sm">{{ repo.status }}</UBadge></div>
              <div class="dev-repo-card__body"><span>{{ repo.branch }}</span><span v-if="repo.changes">{{ repo.changes }} changes</span><span class="dev-kind-badge">{{ repo.kind }}</span></div>
              <div class="dev-repo-card__footer"><code>{{ repo.path }}</code></div>
            </div>
          </div>
        </div>
        <template v-else>
          <div class="dev-workbench-bar">
            <span><UIcon name="folder" /> {{ activeRepo }}</span>
            <span v-if="activePath"><UIcon name="description" /> {{ activePath }}</span>
            <button title="Go to file (Ctrl/Cmd+P)" @click="paletteOpen=true"><UIcon name="search" /> Go to file <kbd>⌘P</kbd></button>
            <button title="Create file" @click="openFileDialog('create')"><UIcon name="note_add" /></button>
            <button :disabled="!activePath" title="Rename or move file" @click="openFileDialog('move')"><UIcon name="drive_file_move" /></button>
            <button :disabled="!activePath" title="Delete file" @click="openFileDialog('delete')"><UIcon name="delete" /></button>
            <button :disabled="!activePath" title="Run diagnostics" @click="loadDiagnostics"><UIcon name="problem" /> {{ diagnosticsLabel }}</button>
            <button :class="{active:reviewOpen}" @click="reviewOpen=!reviewOpen"><UIcon name="difference" /> Review</button>
          </div>
          <div class="dev-workbench-main">
          <div class="dev-workbench-content">
        <div v-if="diagnosticsSupported !== null" class="dev-diagnostics" role="status">
          <span v-if="diagnosticsSupported === false">No diagnostics adapter for this file type.</span>
          <span v-else-if="!diagnostics.length"><UIcon name="check_circle" /> No syntax diagnostics.</span>
          <button v-for="item in diagnostics" v-else :key="`${item.line}:${item.column}:${item.message}`" @click="activeTab='editor'">
            <UBadge type="error" size="sm">{{ item.line }}:{{ item.column }}</UBadge>{{ item.message }}
          </button>
        </div>
        <div v-if="activeTab==='repository'">
          <div v-if="githubStatus" class="dev-github-bar">
            <UIcon name="cloud" />
            <a v-if="githubStatus.repository?.url" :href="githubStatus.repository.url" target="_blank" rel="noopener">{{ githubStatus.repository.nameWithOwner }}</a>
            <span v-else>GitHub unavailable</span>
            <UBadge v-if="latestRun" :type="latestRun.conclusion === 'success' ? 'success' : latestRun.status === 'in_progress' ? 'info' : 'warning'" size="sm">
              {{ latestRun.workflowName }}: {{ latestRun.conclusion || latestRun.status }}
            </UBadge>
            <a v-if="githubStatus.pull_request" :href="githubStatus.pull_request.url" target="_blank" rel="noopener">PR #{{ githubStatus.pull_request.number }}</a>
          </div>
          <div v-if="!activePath" class="dev-empty">Select a file from the sidebar.</div>
          <div v-else-if="loadingFile" class="dev-loading"><UIcon name="sync" /> Loading...</div>
          <ProseCodeReader v-else :file-name="activePath.split('/').pop() || ''" :content="fileContent" />
        </div>
        <div v-else-if="activeTab==='editor'">
          <div v-if="!activePath" class="dev-empty">Select a file to edit.</div>
          <div v-else-if="loadingFile" class="dev-loading"><UIcon name="sync" /> Loading...</div>
          <UCodeEditor ref="editor" v-else :file-content="fileContent" :file-name="activePath.split('/').pop() || ''" :file-path="activePath" :file-repo="activeRepo" :diff-original="diffBaseline" :diff-status="diffStatus" :has-repository-diff="hasRepositoryDiff" :save-revision="saveRevision" @update:file-content="fileContent = $event" @select-file="selectFile($event, false)" @save="saveFile" />
        </div>
        <DeveloperOperationsPanel v-else-if="activeTab==='operations'" :repository="activeRepo" :file="activePath" />
          </div>
          <DeveloperReviewPanel v-if="reviewOpen" :repository="activeRepo" :revision="reviewRevision" @select="selectFile" />
          </div>
        </template>
      </div>
    </div>
    <DeveloperCommandPalette :open="paletteOpen" :files="fileTree.map(item => item.name)" @close="paletteOpen=false" @select="selectFile" />
    <DeveloperFileDialog :open="fileDialogOpen" :mode="fileDialogMode" :repository="activeRepo" :path="activePath" :revision="fileRevision" @close="fileDialogOpen=false" @complete="onFileOperation" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, onBeforeUnmount, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useShellStore } from "../../stores/shell";
import UIcon from "../../skills/atoms/UIcon.vue";
import UBadge from "../../skills/atoms/UBadge.vue";
import SurfaceTabNav from "../../skills/molecules/SurfaceTabNav.vue";
import UCodeEditor from "../../skills/molecules/editor/UCodeEditor.vue";
import ProseCodeReader from "../../skills/molecules/editor/ProseCodeReader.vue";
import DeveloperOperationsPanel from "./DeveloperOperationsPanel.vue";
import DeveloperCommandPalette from "./DeveloperCommandPalette.vue";
import DeveloperReviewPanel from "./DeveloperReviewPanel.vue";
import DeveloperFileDialog from "./DeveloperFileDialog.vue";

const shell = useShellStore();
const route = useRoute();
const router = useRouter();
type DeveloperTab = "code" | "repository" | "editor" | "operations";
const activeTab = ref<DeveloperTab>("code");
const DEV_TABS = [
  { id: "code", label: "Code", icon: "folder" },
  { id: "repository", label: "Repository", icon: "description" },
  { id: "editor", label: "Editor", icon: "diamond" },
  { id: "operations", label: "Operations", icon: "smart_toy" },
];

interface Repo { name: string; branch: string; status: string; path: string; changes?: number; kind?: string; }
interface FileItem { name: string; type: string; size?: number; }
interface TreeNode { name: string; path: string; isDir: boolean; depth: number; }
interface SearchMatch { path: string; line: number; column: number; preview: string }
interface Diagnostic { severity: string; line: number; column: number; message: string }
interface GithubRun { workflowName: string; status: string; conclusion: string; url: string; }
interface GithubStatus { configured: boolean; repository?: { nameWithOwner: string; url: string }; pull_request?: { number: number; url: string } | null; runs?: GithubRun[]; }

const repos = ref<Repo[]>([]);
const fileTree = ref<FileItem[]>([]);
const activeRepo = ref("");
const activePath = ref("");
const fileContent = ref("");
const diffBaseline = ref("");
const diffStatus = ref<"clean" | "modified" | "added" | "deleted">("clean");
const hasRepositoryDiff = ref(false);
const saveRevision = ref(0);
const loadingRepos = ref(true);
const loadingFiles = ref(false);
const loadingFile = ref(false);
const showSidebar = computed(() => shell.developerSidebarOpen && activeTab.value !== "code");
const sidebarRepo = ref("");
const devLane = ref<"core" | "extension" | "project">("extension");
const expandedDirs = ref<Set<string>>(new Set());
const githubStatus = ref<GithubStatus | null>(null);
const latestRun = computed(() => githubStatus.value?.runs?.[0] || null);
const fileFilter = ref("");
const searchResults = ref<SearchMatch[]>([]);
const searching = ref(false);
const paletteOpen = ref(false);
const reviewOpen = ref(true);
const reviewRevision = ref(0);
const editor = ref<InstanceType<typeof UCodeEditor> | null>(null);
const openPaths = ref<string[]>([]);
const fileRevision = ref("");
const diagnostics = ref<Diagnostic[]>([]);
const diagnosticsSupported = ref<boolean | null>(null);
const fileDialogOpen = ref(false);
const fileDialogMode = ref<"create" | "move" | "delete">("create");
const diagnosticsLabel = computed(() => diagnosticsSupported.value === false ? "unsupported" : diagnostics.value.length ? `${diagnostics.value.length} issue${diagnostics.value.length === 1 ? '' : 's'}` : diagnosticsSupported.value ? "clean" : "Diagnostics");
const SESSION_KEY = "ucore-developer-workbench";

function getLaneForRepo(repo: Repo): "core" | "extension" | "project" {
  const name = (repo.name || "").trim().toLowerCase();
  if (name === "fredporter") return "project";
  if (["ucore", "sonicscrewdriver", "snackmachine", "ucode", "uflow", "uknowledge", "uvector"].includes(name)) return "core";
  if (["dreamscape", "google"].some((suffix) => name.endsWith(suffix))) return "extension";
  return "extension";
}

const filteredRepos = computed(() => {
  return repos.value.filter((repo) => getLaneForRepo(repo) === devLane.value);
});

const visibleTree = computed(() => {
  const result: TreeNode[] = [];
  if (!sidebarRepo.value || !fileTree.value.length) return result;
  const filter = fileFilter.value.trim().toLowerCase();
  if (filter) {
    return fileTree.value.filter((item) => item.name.toLowerCase().includes(filter)).slice(0, 100).map((item) => ({ name: item.name.split("/").pop() || item.name, path: item.name, isDir: false, depth: 0 }));
  }
  const allPaths = new Set(fileTree.value.map(f => f.name));
  const dirMap = new Map<string, string[]>();
  for (const p of allPaths) {
    const slash = p.lastIndexOf("/");
    const dir = slash === -1 ? "" : p.substring(0, slash);
    const name = slash === -1 ? p : p.substring(slash + 1);
    if (!dirMap.has(dir)) dirMap.set(dir, []);
    dirMap.get(dir)!.push(name);
  }
  const expanded = expandedDirs.value;
  function walk(dir: string, depth: number) {
    const children = dirMap.get(dir) || [];
    const subdirs: string[] = [];
    const files: string[] = [];
    for (const c of children) {
      const full = dir ? dir + "/" + c : c;
      (allPaths.has(full + "/") || [...allPaths].some(p => p.startsWith(full + "/")) ? subdirs : files).push(c);
    }
    for (const d of [...subdirs].sort()) {
      const full = dir ? dir + "/" + d : d;
      result.push({ name: d, path: full, isDir: true, depth });
      if (expanded.has(full)) walk(full, depth + 1);
    }
    for (const f of [...files].sort()) {
      const full = dir ? dir + "/" + f : f;
      result.push({ name: f, path: full, isDir: false, depth });
    }
  }
  walk("", 0);
  return result;
});

async function fetchRepos() {
  loadingRepos.value = true;
  try { const res = await fetch("/api/developer/repos", { signal: AbortSignal.timeout(8000) }); if (res.ok) { const d = await res.json(); repos.value = d.repos || []; } } catch { repos.value = []; }
  loadingRepos.value = false;
}

async function openRepoFromCard(repo: Repo) {
  shell.setDeveloperSidebarOpen(true);
  await openSidebarRepo(repo.name);
  activeTab.value = "repository";
}

function closeSidebar() {
  shell.setDeveloperSidebarOpen(false);
  activeRepo.value = "";
  activePath.value = "";
  sidebarRepo.value = "";
}

function toggleDir(path: string) {
  const s = new Set(expandedDirs.value);
  if (s.has(path)) s.delete(path); else s.add(path);
  expandedDirs.value = s;
}

async function openSidebarRepo(name: string) {
  sidebarRepo.value = name; activeRepo.value = name; activePath.value = ""; expandedDirs.value = new Set();
  loadingFiles.value = true;
  githubStatus.value = null;
  fileFilter.value = ""; searchResults.value = [];
  try {
    const res = await fetch("/api/developer/repos/" + encodeURIComponent(name) + "/github", { signal: AbortSignal.timeout(12000) });
    if (res.ok) githubStatus.value = await res.json();
  } catch {}
  try { const res = await fetch("/api/developer/repos/" + encodeURIComponent(name) + "/files", { signal: AbortSignal.timeout(8000) }); if (res.ok) { const d = await res.json(); fileTree.value = d.files || []; } } catch { fileTree.value = []; }
  loadingFiles.value = false;
  // Auto-select default file
  const names = fileTree.value.map(f => f.name);
  const prefs = ["README.md", "readme.md", "docs/README.md"];
  const def = prefs.find(p => names.includes(p)) || names[0];
  if (def) {
    await selectFile(def);
  }
}

async function selectFile(path: string, track = true) {
  activePath.value = path; loadingFile.value = true;
  const repo = activeRepo.value;
  try {
    const res = await fetch("/api/developer/repos/" + encodeURIComponent(repo) + "/file-preview?path=" + encodeURIComponent(path), { signal: AbortSignal.timeout(10000) });
    if (res.ok) {
      const d = await res.json();
      if (activeRepo.value === repo && activePath.value === path) {
        fileContent.value = d.content || "";
        fileRevision.value = d.revision || "";
        diagnostics.value = []; diagnosticsSupported.value = null;
        if (track && !openPaths.value.includes(path)) openPaths.value.push(path);
        await refreshFileDiff(repo, path, fileContent.value);
      }
    }
  } catch {}
  loadingFile.value = false;
}

function openFileDialog(mode: "create" | "move" | "delete") { fileDialogMode.value = mode; fileDialogOpen.value = true; }

async function onFileOperation(path: string, deleted: boolean) {
  await openSidebarRepo(activeRepo.value);
  reviewRevision.value++;
  if (deleted) { openPaths.value = openPaths.value.filter((item) => item !== path); return; }
  await selectFile(path);
  activeTab.value = "editor";
}

async function loadDiagnostics() {
  if (!activeRepo.value || !activePath.value) return;
  const response = await fetch(`/api/developer/repos/${encodeURIComponent(activeRepo.value)}/diagnostics?path=${encodeURIComponent(activePath.value)}`);
  if (response.ok) { const data = await response.json(); diagnosticsSupported.value = data.supported; diagnostics.value = data.diagnostics || []; }
}

async function searchRepository() {
  if (!activeRepo.value || !fileFilter.value.trim()) return;
  searching.value = true;
  try {
    const response = await fetch(`/api/developer/repos/${encodeURIComponent(activeRepo.value)}/search?q=${encodeURIComponent(fileFilter.value)}&limit=50`);
    searchResults.value = response.ok ? (await response.json()).matches || [] : [];
  } finally { searching.value = false; }
}

async function refreshFileDiff(repo: string, path: string, fallback: string): Promise<void> {
  try {
    const res = await fetch("/api/developer/repos/" + encodeURIComponent(repo) + "/diff?path=" + encodeURIComponent(path), { signal: AbortSignal.timeout(10000) });
    if (!res.ok) throw new Error("Diff unavailable");
    const data = await res.json();
    if (activeRepo.value === repo && activePath.value === path) {
      diffBaseline.value = typeof data.baseline === "string" ? data.baseline : fallback;
      diffStatus.value = ["clean", "modified", "added", "deleted"].includes(data.status) ? data.status : "modified";
      hasRepositoryDiff.value = data.hasDiff === true;
    }
  } catch {
    if (activeRepo.value === repo && activePath.value === path) {
      diffBaseline.value = fallback;
      diffStatus.value = "clean";
      hasRepositoryDiff.value = false;
    }
  }
}

async function saveFile() {
  if (!activeRepo.value || !activePath.value) return;
  try {
    const repo = activeRepo.value;
    const path = activePath.value;
    const res = await fetch("/api/developer/repos/" + encodeURIComponent(repo) + "/file-preview?path=" + encodeURIComponent(path), { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: fileContent.value, revision: fileRevision.value }), signal: AbortSignal.timeout(15000) });
    if (res.ok) {
      const saved = await res.json(); fileRevision.value = saved.revision || fileRevision.value;
      await refreshFileDiff(repo, path, fileContent.value);
      saveRevision.value++;
      reviewRevision.value++;
    } else if (res.status === 409) {
      const conflict = await res.json(); window.alert(conflict.error || "File changed outside the editor. Reload before saving.");
    }
  } catch {}
}

watch(activeTab, (tab) => {
  if (route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } });
  }
  shell.setDeveloperSurfaceTab(tab);
  if (tab === "code") {
    closeSidebar();
  } else if (tab === "repository" || tab === "editor" || tab === "operations") {
    if (!shell.developerSidebarOpen || !sidebarRepo.value || !activePath.value) {
      activeTab.value = "code";
      closeSidebar();
      return;
    }
    shell.setDeveloperSidebarOpen(true);
  }
});

watch(
  () => [shell.developerSidebarOpen, activeRepo.value, activePath.value],
  () => {
    if ((activeTab.value === "repository" || activeTab.value === "editor" || activeTab.value === "operations") && (!shell.developerSidebarOpen || !activeRepo.value || !activePath.value)) {
      activeTab.value = "code";
      closeSidebar();
    }
  },
);
watch(repos, (items) => {
  if (!items.length) return;
  const fallbackLane = (["core", "extension", "project"] as const).find((lane) =>
    items.some((repo) => getLaneForRepo(repo) === lane),
  );
  if (fallbackLane && !filteredRepos.value.length) {
    devLane.value = fallbackLane;
  }
});
watch([activeRepo, activePath, activeTab, openPaths, reviewOpen], () => {
  if (!activeRepo.value) return;
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({ repository: activeRepo.value, path: activePath.value, tab: activeTab.value, openPaths: openPaths.value, reviewOpen: reviewOpen.value }));
}, { deep: true });

function onGlobalKeydown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "p") { event.preventDefault(); if (activeRepo.value) paletteOpen.value = true; }
  if (event.key === "Escape") paletteOpen.value = false;
}
onMounted(() => {
  const routeTab = (route.query.tab as string) || "";
  if (["code", "repository", "editor", "operations"].includes(routeTab)) {
    activeTab.value = routeTab as DeveloperTab;
  }
  shell.setSidebarOpen(false);
  shell.setDeveloperSidebarOpen(false);
  shell.setDeveloperSurfaceTab(activeTab.value);
  window.addEventListener("keydown", onGlobalKeydown);
  fetchRepos().then(async () => {
    try {
      const saved = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
      if (!saved?.repository || !repos.value.some((repo) => repo.name === saved.repository)) return;
      shell.setDeveloperSidebarOpen(true);
      await openSidebarRepo(saved.repository);
      if (["repository", "editor", "operations"].includes(saved.tab)) activeTab.value = saved.tab;
      await nextTick();
      const paths = Array.isArray(saved.openPaths) ? saved.openPaths.filter((path: unknown) => typeof path === "string" && fileTree.value.some((item) => item.name === path)).slice(-10) : [];
      for (const path of paths) {
        const response = await fetch(`/api/developer/repos/${encodeURIComponent(saved.repository)}/file-preview?path=${encodeURIComponent(path)}`);
        if (response.ok) { const data = await response.json(); editor.value?.openFile(path.split("/").pop() || path, path, data.content || ""); }
      }
      openPaths.value = paths;
      if (saved.path && fileTree.value.some((item) => item.name === saved.path)) await selectFile(saved.path, false);
      reviewOpen.value = saved.reviewOpen !== false;
    } catch { sessionStorage.removeItem(SESSION_KEY); }
  });
});
onBeforeUnmount(() => window.removeEventListener("keydown", onGlobalKeydown));

watch(
  () => route.query.tab,
  (tab) => {
    const t = (tab as string) || "";
    if (["code", "repository", "editor", "operations"].includes(t) && activeTab.value !== t) {
      activeTab.value = t as DeveloperTab;
    }
  },
);
</script>

<style scoped>
.dev-surface { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.surface__body { display: flex; flex: 1; overflow: hidden; }
.surface__body--has-sidebar { flex-direction: row !important; }
.surface__body--has-sidebar .surface__content { flex: 1; overflow-y: auto; padding: var(--usx-spacing-md); }
.dev-sidebar { width: 280px; flex-shrink: 0; border-right: var(--usx-border-width) solid var(--usx-color-border); background: var(--usx-color-surface-variant); display: flex; flex-direction: column; }
.dev-sidebar__header { display: flex; align-items: center; justify-content: space-between; padding: var(--usx-spacing-sm) var(--usx-spacing-md); border-bottom: var(--usx-border-width) solid var(--usx-color-border); font-weight: var(--usx-font-weight-semibold); }
.dev-sidebar__close { background: none; border: none; font-size: var(--usx-font-size-lg); cursor: pointer; color: var(--usx-color-on-surface-muted); }
.dev-sidebar__body { flex: 1; overflow-y: auto; padding: var(--usx-spacing-xs); }
.dev-search { display: flex; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-xs); border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.dev-search input { min-width: 0; flex: 1; padding: var(--usx-spacing-xs); background: var(--usx-color-background); color: var(--usx-color-on-surface); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); }
.dev-search button { border: 0; background: transparent; color: var(--usx-color-on-surface-muted); }
.dev-search-results { display: flex; flex-direction: column; padding: var(--usx-spacing-xs); border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.dev-search-results button { display: flex; flex-direction: column; align-items: start; padding: var(--usx-spacing-xs); border: 0; background: transparent; color: var(--usx-color-on-surface); text-align: left; }
.dev-search-results button span { max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-xs); }
.dev-search-results .dev-search-results__clear { color: var(--usx-color-primary); }
.dev-file-row { display: flex; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); cursor: pointer; font-size: var(--usx-font-size-sm); }
.dev-file-row:hover { background: var(--usx-color-surface); }
.dev-file-row--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.dev-file-icon { flex-shrink: 0; color: var(--usx-color-on-surface-muted); }
.dev-file-name { flex: 1; font-weight: var(--usx-font-weight-medium); }
.dev-file-path { font-family: var(--usx-font-family-mono); font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); max-width: 20ch; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dev-repo-grid { display: flex; flex-direction: column; gap: var(--usx-spacing-sm); }
.dev-repo-grid__cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(28ch, 1fr)); gap: var(--usx-spacing-sm); }
.dev-repo-card { border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); background: var(--usx-color-surface); cursor: pointer; overflow: hidden; }
.dev-repo-card:hover { border-color: var(--usx-color-primary); }
.dev-repo-card__header { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm) var(--usx-spacing-md); border-bottom: var(--usx-border-width) solid var(--usx-color-border); }
.dev-repo-card__body { padding: var(--usx-spacing-sm) var(--usx-spacing-md); font-size: var(--usx-font-size-sm); }
.dev-repo-card__footer { padding: var(--usx-spacing-xs) var(--usx-spacing-md); background: var(--usx-color-surface-variant); font-size: var(--usx-font-size-xs); }
.dev-repo-card__footer code { font-family: var(--usx-font-family-mono); color: var(--usx-color-on-surface-muted); }
.dev-kind-badge { display: inline-block; padding: 1px var(--usx-spacing-xs); background: var(--usx-color-surface-variant); border-radius: var(--usx-radius-sm); font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); text-transform: capitalize; }
.dev-lane-bar { display: flex; justify-content: center; gap: var(--usx-spacing-xs); margin-bottom: var(--usx-spacing-md); align-items: center; flex-wrap: wrap; }
.dev-lane-bar button { align-self: center; flex-shrink: 0; white-space: nowrap; padding: var(--usx-spacing-xs) var(--usx-spacing-md); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); cursor: pointer; font-size: var(--usx-font-size-sm); height: auto; min-height: auto; }
.dev-lane-bar button.active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); border-color: var(--usx-color-primary); }
.dev-github-bar { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm) var(--usx-spacing-md); margin-bottom: var(--usx-spacing-md); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface-variant); font-size: var(--usx-font-size-sm); }
.dev-github-bar a { color: var(--usx-color-primary); text-decoration: none; }
.dev-workbench-bar { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); border-bottom: var(--usx-border-width) solid var(--usx-color-border); background: var(--usx-color-surface-variant); overflow-x: auto; }
.dev-workbench-bar span, .dev-workbench-bar button { display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); white-space: nowrap; }
.dev-workbench-bar span { font-size: var(--usx-font-size-xs); color: var(--usx-color-on-surface-muted); }
.dev-workbench-bar button { margin-left: auto; padding: var(--usx-spacing-xs) var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); }
.dev-workbench-bar button + button { margin-left: 0; }
.dev-workbench-bar button.active { border-color: var(--usx-color-primary); color: var(--usx-color-primary); }
.dev-workbench-main { display: flex; min-height: 0; flex: 1; }
.dev-workbench-content { min-width: 0; flex: 1; overflow: auto; }
.dev-diagnostics { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); background: var(--usx-color-surface); border-bottom: var(--usx-border-width) solid var(--usx-color-border); overflow-x: auto; font-size: var(--usx-font-size-xs); }
.dev-diagnostics button { display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); white-space: nowrap; border: 0; background: transparent; color: var(--usx-color-on-surface); }
.dev-loading, .dev-empty { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-xl); color: var(--usx-color-on-surface-muted); justify-content: center; font-size: var(--usx-font-size-sm); }
</style>
