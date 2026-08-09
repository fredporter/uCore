<template>
  <div class="filepicker-sidebar">
    <div class="filepicker-sidebar__header">
      <div
        class="filepicker-sidebar__toolbar"
        role="toolbar"
        aria-label="file-actions"
      >
        <button
          class="filepicker-sidebar__icon-btn"
          :disabled="isMirroring"
          title="Sync User Vault"
          @click="syncUserVault"
        >
          <UIcon :name="isMirroring ? 'sync' : 'sync'" :spin="isMirroring" />
        </button>
        <button
          class="filepicker-sidebar__icon-btn"
          title="New file"
          @click="handleNewFile"
        >
          <UIcon name="add" />
        </button>
        <button
          class="filepicker-sidebar__icon-btn"
          title="Open Markdown Workspace"
          @click="openMarkdownWorkspace"
        >
          <UIcon name="diamond" />
        </button>
        <button
          class="filepicker-sidebar__icon-btn"
          :disabled="!selectedFile"
          title="Duplicate selected file"
          @click="duplicateSelectedFile"
        >
          <UIcon name="content_copy" />
        </button>
        <button
          class="filepicker-sidebar__icon-btn"
          title="Dashboard"
          @click="router.push('/')"
        >
          <UIcon name="home" />
        </button>
        <button
          v-if="developerServerActive"
          class="filepicker-sidebar__icon-btn"
          title="Developer"
          @click="router.push('/developer')"
        >
          <UIcon name="terminal" />
        </button>
      </div>
    </div>

    <div v-if="mirrorMessage" class="filepicker-sidebar__mirror-message">
      {{ mirrorMessage }}
    </div>

    <div class="filepicker-sidebar__search-row">
      <UInput
        v-model="searchQuery"
        placeholder="Filter files..."
        icon="search"
        class="filepicker-sidebar__search"
      />
      <label class="filepicker-sidebar__mode-inline" for="markdown-open-mode">
        <UIcon name="diamond" class="filepicker-sidebar__inline-icon" />
        <select
          id="markdown-open-mode"
          v-model="markdownOpenMode"
          class="filepicker-sidebar__mode-select"
          title="Open as"
        >
          <option value="auto">Auto</option>
          <option value="prose">Prose</option>
          <option value="code">Code</option>
        </select>
      </label>
    </div>

    <div v-if="indexStatus === 'not-built'" class="filepicker-sidebar__banner">
      <span>Index not built</span>
      <UButton size="sm" @click="buildIndex">Build Index</UButton>
    </div>

    <div v-if="loading" class="filepicker-sidebar__loading">
      <USpinner :size="20" />
      <span>Loading files...</span>
    </div>

    <div v-else-if="error" class="filepicker-sidebar__error">
      <UIcon name="mdi:alert-circle-outline" />
      <span>{{ error }}</span>
      <UButton size="sm" @click="fetchFiles">Retry</UButton>
    </div>

    <div v-else class="filepicker-sidebar__tree">
      <!-- Files-style sections: default Files (User Vault) + other Workspaces -->
      <section
        v-for="section in sections"
        :key="section.source"
        class="filepicker-sidebar__section"
        :class="{
          'filepicker-sidebar__section--open': isSectionOpen(section.source),
        }"
      >
        <button
          class="filepicker-sidebar__section-head"
          @click="toggleSection(section.source)"
        >
          <UIcon
            :name="
              isSectionOpen(section.source) ? 'expand_more' : 'chevron_right'
            "
            class="filepicker-sidebar__section-chevron"
          />
          <UIcon
            :name="section.icon"
            class="filepicker-sidebar__section-icon"
          />
          <span class="filepicker-sidebar__section-title">{{
            section.label
          }}</span>
          <span class="filepicker-sidebar__section-count">{{
            section.count
          }}</span>
        </button>

        <div
          v-if="isSectionOpen(section.source)"
          class="filepicker-sidebar__section-body"
        >
          <div
            v-for="row in rowsFor(section)"
            :key="row.id"
            class="filepicker-sidebar__tree-row"
            :style="{ '--depth': String(row.depth) }"
          >
            <button
              v-if="row.type === 'folder'"
              class="filepicker-sidebar__folder"
              @click="toggleFolder(section.source, row.path)"
            >
              <UIcon
                :name="
                  isFolderExpanded(section.source, row.path)
                    ? 'expand_more'
                    : 'chevron_right'
                "
                class="filepicker-sidebar__folder-chevron"
              />
              <UIcon name="folder" class="filepicker-sidebar__folder-icon" />
              <span class="filepicker-sidebar__folder-name">{{
                row.name
              }}</span>
              <span class="filepicker-sidebar__folder-count">{{
                row.fileCount
              }}</span>
            </button>

            <div
              v-else
              class="filepicker-sidebar__item"
              :class="{
                'filepicker-sidebar__item--readonly': row.file.is_readonly,
                'filepicker-sidebar__item--active':
                  selectedFile?.path === row.file.path,
              }"
              @click="handleFileSelect(row.file)"
              @dblclick="handleDoubleClick(row.file)"
            >
              <UIcon
                :name="getFileIcon(row.file.extension)"
                class="filepicker-sidebar__item-icon"
              />
              <span class="filepicker-sidebar__item-name">{{
                row.file.filename
              }}</span>
              <button
                class="filepicker-sidebar__item-open"
                title="Open prose"
                @click.stop="openInMode(row.file, 'prose')"
              >
                <UIcon name="notes" />
              </button>
              <button
                class="filepicker-sidebar__item-open"
                title="Open code"
                @click.stop="openInMode(row.file, 'code')"
              >
                <UIcon name="code" />
              </button>
            </div>
          </div>

          <div
            v-if="section.count === 0 && searchQuery"
            class="filepicker-sidebar__section-empty"
          >
            No files match "{{ searchQuery }}"
          </div>
        </div>
      </section>

      <div v-if="sections.length === 0" class="filepicker-sidebar__empty">
        <UIcon name="mdi:file-document-outline" />
        <span v-if="searchQuery">No files matching "{{ searchQuery }}"</span>
        <span v-else>No files found in the vault</span>
        <UButton size="sm" variant="ghost" @click="handleNewFile">
          Create a new file
        </UButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component FilepickerSidebar
 * @description Files-style vault sidebar — default User Vault Files view, with
 * other workspaces (Shared/Public vaults) shown as their own Files sections.
 * Wired to the uCore unified library index API with vault plate integration.
 * @category molecules
 * @props {boolean} open - Sidebar visibility
 * @props {boolean} compact - Compact mode
 * @emits {FileEntry} fileSelect - File selected
 * @emits {string} newFile - New file requested
 * @usage <FilepickerSidebar :open="true" @file-select="handleFileSelect" />
 */
import { ref, computed, onMounted, watch } from "vue";
import UInput from "../atoms/UInput.vue";
import UIcon from "../atoms/UIcon.vue";
import UButton from "../atoms/UButton.vue";
import USpinner from "../atoms/USpinner.vue";
import { ucoreApi } from "../../api/client";
import { SNACKBAR_BASE } from "../../api/base";
import { useRouter } from "vue-router";
import { useWorkflowStore } from "../../stores/workflow";
import type { FileEntry } from "../../types/filepicker";

interface Props {
  open?: boolean;
  compact?: boolean;
}

withDefaults(defineProps<Props>(), {
  open: true,
  compact: false,
});

const emit = defineEmits<{
  fileSelect: [file: FileEntry];
  newFile: [binderId: string];
}>();
const router = useRouter();
const wf = useWorkflowStore();

// ─── Refs ───────────────────────────────────────────────────────────
const searchQuery = ref("");
const files = ref<FileEntry[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const indexStatus = ref<"ok" | "not-built" | "unknown">("unknown");
const isMirroring = ref(false);
const mirrorMessage = ref("");
const developerServerActive = ref(false);
const MARKDOWN_OPEN_MODE_KEY = "ucore.filepicker.markdown-open-mode";
const markdownOpenMode = ref<"auto" | "prose" | "code">("auto");
const selectedFile = ref<FileEntry | null>(null);
const expandedFolders = ref<Set<string>>(new Set());

interface FolderTreeRow {
  id: string;
  type: "folder";
  path: string;
  name: string;
  depth: number;
  fileCount: number;
}

interface FileTreeRow {
  id: string;
  type: "file";
  depth: number;
  file: FileEntry;
}

type TreeRow = FolderTreeRow | FileTreeRow;

function loadMarkdownOpenMode() {
  try {
    const saved = localStorage.getItem(MARKDOWN_OPEN_MODE_KEY);
    if (saved === "auto" || saved === "prose" || saved === "code") {
      markdownOpenMode.value = saved;
    }
  } catch {
    // no-op
  }
}

function persistMarkdownOpenMode() {
  try {
    localStorage.setItem(MARKDOWN_OPEN_MODE_KEY, markdownOpenMode.value);
  } catch {
    // no-op
  }
}

watch(markdownOpenMode, () => {
  persistMarkdownOpenMode();
});

function resolveModeForFile(file: FileEntry): "prose" | "code" {
  if (markdownOpenMode.value === "prose" || markdownOpenMode.value === "code") {
    return markdownOpenMode.value;
  }
  const ext = String(file.extension || "").toLowerCase();
  return ext === "md" || ext === "txt" ? "prose" : "code";
}

async function refreshDeveloperServerStatus() {
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/developer/status`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) {
      developerServerActive.value = false;
      return;
    }
    const data = await res.json();
    developerServerActive.value = Boolean(data?.active);
  } catch {
    developerServerActive.value = false;
  }
}

// ─── Fetch files from the unified library index ────────────────────
// Fetches the full index (all vault sources) so the sidebar can show the
// default User Vault Files view plus other workspaces as separate sections.
async function fetchFiles() {
  loading.value = true;
  error.value = null;
  try {
    const query = searchQuery.value.trim() || "*";
    const res = await ucoreApi.library.search(query, undefined, 1000);
    if (res.ok && res.data) {
      const results = (res.data as any).results || [];
      // Only vault sources belong in the sidebar — ignore stale index
      // entries written by other indexers (e.g. code sources).
      files.value = results.filter(
        (f: FileEntry) => Boolean(f.source) && VAULT_SOURCES.has(f.source),
      );
      autoExpandFirstLevel(files.value);
    }
  } catch (e: any) {
    error.value = e.message || "Failed to fetch files";
    files.value = [];
  } finally {
    loading.value = false;
  }
}

// ─── Build index ────────────────────────────────────────────────────
async function buildIndex() {
  loading.value = true;
  try {
    const res = await ucoreApi.library.build();
    if (res.ok) {
      indexStatus.value = "ok";
      await fetchFiles();
    }
  } catch (e: any) {
    error.value = e.message || "Failed to build index";
  } finally {
    loading.value = false;
  }
}

// ─── Check index status on mount ────────────────────────────────────
async function checkIndex() {
  try {
    const res = await ucoreApi.library.stats();
    if (res.ok) {
      const total = (res.data as any)?.total_entries || 0;
      indexStatus.value = total > 0 ? "ok" : "not-built";
    }
  } catch {
    indexStatus.value = "unknown";
  }
}

// ─── Debounced search ───────────────────────────────────────────────
let searchTimer: ReturnType<typeof setTimeout> | null = null;
watch(searchQuery, () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => fetchFiles(), 300);
});

function handleNewFile() {
  emit("newFile", "user");
}

function handleFileSelect(file: FileEntry) {
  selectedFile.value = file;
  wf.setEditorMode(resolveModeForFile(file));
  emit("fileSelect", { ...file });
}

function openInMode(file: FileEntry, mode: "prose" | "code") {
  wf.setEditorMode(mode);
  emit("fileSelect", { ...file });
}

function openMarkdownWorkspace() {
  if (markdownOpenMode.value === "prose" || markdownOpenMode.value === "code") {
    wf.setEditorMode(markdownOpenMode.value);
  }
  router.push({ path: "/workflow", query: { tab: "editor" } });
}

function handleDoubleClick(file: FileEntry) {
  // Could open in editor or navigate
  selectedFile.value = file;
  emit("fileSelect", file);
}

async function duplicateSelectedFile() {
  if (!selectedFile.value) {
    mirrorMessage.value = "Select a file to duplicate.";
    return;
  }

  const source = selectedFile.value;
  const ext = String(source.extension || "md").toLowerCase();
  if (ext !== "md" && ext !== "txt") {
    mirrorMessage.value = "Duplicate currently supports markdown/text files.";
    return;
  }

  const base = source.filename.replace(/\.[^.]+$/, "");
  const title = window.prompt("Duplicate file title", `${base} Copy`);
  if (title === null) return;
  const cleanTitle = title.trim() || `${base} Copy`;
  const safeStem =
    cleanTitle
      .replace(/[^a-zA-Z0-9._ -]+/g, "-")
      .replace(/\s+/g, " ")
      .trim() || `${base}-copy`;

  let content = source.preview || "";
  try {
    const fileRes = await ucoreApi.library.file(source.path);
    if (fileRes.ok && (fileRes.data as any)?.content !== undefined) {
      content = String((fileRes.data as any).content || "");
    }
  } catch {
    // keep preview fallback
  }

  try {
    const res = await ucoreApi.userWorkflow.importMarkdown({
      content,
      source_format: "markdown",
      title: cleanTitle,
      binder: source.source || "user",
      vault_layer: source.source || "user",
      relative_dir: ".",
      filename: `${safeStem}.${ext}`,
      metadata: {
        imported_from: "filepicker.duplicate",
      },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    mirrorMessage.value = "File duplicated.";
    await fetchFiles();
  } catch (e: any) {
    mirrorMessage.value = `Duplicate failed: ${e?.message || e}`;
  }
}

function folderKey(source: string, path: string): string {
  return `${source}:${path}`;
}

function isFolderExpanded(source: string, path: string): boolean {
  return expandedFolders.value.has(folderKey(source, path));
}

function toggleFolder(source: string, path: string) {
  const key = folderKey(source, path);
  const next = new Set(expandedFolders.value);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  expandedFolders.value = next;
}

async function syncUserVault() {
  isMirroring.value = true;
  mirrorMessage.value = "";
  try {
    const res = await ucoreApi.vault.sync("User Vault");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    mirrorMessage.value = "User Vault synchronized to local index.";
  } catch (e: any) {
    mirrorMessage.value = `Sync failed: ${e?.message || e}`;
  } finally {
    isMirroring.value = false;
  }
}

onMounted(async () => {
  loadMarkdownOpenMode();
  await refreshDeveloperServerStatus();
  await checkIndex();
  if (indexStatus.value === "ok") {
    await fetchFiles();
  }
});

// ─── Files-style sections ───────────────────────────────────────────
const VAULT_SOURCES = new Set(["user", "shared", "public"]);

const WORKSPACE_META: Record<string, { label: string; icon: string }> = {
  user: { label: "Files", icon: "account_tree" },
  shared: { label: "Shared Vaults", icon: "folder_shared" },
  public: { label: "Public Vaults", icon: "public" },
};

const SECTION_ORDER = ["user", "shared", "public"];

const collapsedSections = ref<Set<string>>(new Set(["shared", "public"]));

function isSectionOpen(source: string): boolean {
  return !collapsedSections.value.has(source);
}

function toggleSection(source: string) {
  const next = new Set(collapsedSections.value);
  if (next.has(source)) {
    next.delete(source);
  } else {
    next.add(source);
  }
  collapsedSections.value = next;
}

interface VaultSection {
  source: string;
  label: string;
  icon: string;
  count: number;
  files: FileEntry[];
}

/** Longest common directory prefix across a set of absolute paths. */
function commonRoot(paths: string[]): string {
  if (paths.length === 0) return "";
  let prefix = paths[0];
  for (const p of paths) {
    let i = 0;
    while (i < prefix.length && i < p.length && prefix[i] === p[i]) i += 1;
    prefix = prefix.slice(0, i);
  }
  const idx = prefix.lastIndexOf("/");
  return idx > 0 ? prefix.slice(0, idx) : prefix;
}

/** Path relative to the vault root (e.g. "Notes/foo.md" or "foo.md"). */
function relPath(file: FileEntry, root: string): string {
  if (!root) return file.path;
  const p = file.path.startsWith(root)
    ? file.path.slice(root.length)
    : file.path;
  return p.replace(/^\/+/, "");
}

function buildTreeRows(secFiles: FileEntry[], source: string): TreeRow[] {
  const root = commonRoot(secFiles.map((f) => f.path));
  const folders = new Map<
    string,
    {
      path: string;
      name: string;
      parent: string;
      depth: number;
      fileCount: number;
    }
  >();
  const childFolders = new Map<string, Set<string>>();
  const childFiles = new Map<string, FileEntry[]>();

  const addFolderChild = (parent: string, child: string) => {
    if (!childFolders.has(parent)) {
      childFolders.set(parent, new Set());
    }
    childFolders.get(parent)!.add(child);
  };

  const addFileChild = (parent: string, file: FileEntry) => {
    if (!childFiles.has(parent)) {
      childFiles.set(parent, []);
    }
    childFiles.get(parent)!.push(file);
  };

  for (const file of secFiles) {
    const rel = relPath(file, root);
    const parts = rel.split("/").filter(Boolean);
    const filename = parts[parts.length - 1] || file.filename || file.path;
    const folderParts = parts.length > 1 ? parts.slice(0, -1) : [];
    let parent = "";
    for (let i = 0; i < folderParts.length; i += 1) {
      const segment = folderParts[i];
      const path = parent ? `${parent}/${segment}` : segment;
      if (!folders.has(path)) {
        folders.set(path, {
          path,
          name: segment,
          parent,
          depth: i,
          fileCount: 0,
        });
      }
      folders.get(path)!.fileCount += 1;
      addFolderChild(parent, path);
      parent = path;
    }

    addFileChild(parent, { ...file, filename });
  }

  const rows: TreeRow[] = [];

  const walk = (parent: string, depth: number) => {
    const folderIds = Array.from(childFolders.get(parent) || []).sort((a, b) =>
      a.localeCompare(b),
    );

    for (const folderId of folderIds) {
      const folder = folders.get(folderId);
      if (!folder) continue;
      rows.push({
        id: `folder:${source}:${folder.path}`,
        type: "folder",
        path: folder.path,
        name: folder.name,
        depth,
        fileCount: folder.fileCount,
      });
      if (isFolderExpanded(source, folder.path)) {
        walk(folder.path, depth + 1);
      }
    }

    const filesAtLevel = (childFiles.get(parent) || []).sort((a, b) =>
      a.filename.localeCompare(b.filename),
    );

    for (const file of filesAtLevel) {
      rows.push({
        id: `file:${file.path}`,
        type: "file",
        depth,
        file,
      });
    }
  };

  walk("", 0);
  return rows;
}

function rowsFor(section: VaultSection): TreeRow[] {
  return buildTreeRows(section.files, section.source);
}

const sections = computed<VaultSection[]>(() => {
  const bySource = new Map<string, FileEntry[]>();
  for (const f of files.value) {
    const key = f.source || "user";
    const list = bySource.get(key);
    if (list) {
      list.push(f);
    } else {
      bySource.set(key, [f]);
    }
  }

  const ordered: VaultSection[] = [];
  const seen = new Set<string>();

  for (const key of SECTION_ORDER) {
    const list = bySource.get(key) || [];
    if (list.length === 0) continue;
    seen.add(key);
    const meta = WORKSPACE_META[key] || { label: key, icon: "folder" };
    ordered.push({
      source: key,
      label: meta.label,
      icon: meta.icon,
      count: list.length,
      files: list,
    });
  }

  for (const [key, list] of bySource) {
    if (seen.has(key)) continue;
    if (!VAULT_SOURCES.has(key)) continue;
    const meta = WORKSPACE_META[key] || { label: key, icon: "folder" };
    ordered.push({
      source: key,
      label: meta.label,
      icon: meta.icon,
      count: list.length,
      files: list,
    });
  }

  return ordered;
});

/** Expand the first-level folders of each section once after a fetch. */
function autoExpandFirstLevel(results: FileEntry[]) {
  if (expandedFolders.value.size > 0 || results.length === 0) {
    return;
  }
  const bySource = new Map<string, FileEntry[]>();
  for (const f of results) {
    const key = f.source || "user";
    const list = bySource.get(key);
    if (list) list.push(f);
    else bySource.set(key, [f]);
  }
  const firstLevel = new Set<string>();
  for (const [source, list] of bySource) {
    const root = commonRoot(list.map((f) => f.path));
    for (const f of list) {
      const parts = relPath(f, root).split("/").filter(Boolean);
      if (parts.length > 1) {
        firstLevel.add(`${source}:${parts[0]}`);
      }
    }
  }
  expandedFolders.value = firstLevel;
}

// ─── Icon mapping ───────────────────────────────────────────────────
function getFileIcon(ext: string): string {
  const iconMap: Record<string, string> = {
    md: "mdi:language-markdown",
    ts: "mdi:language-typescript",
    tsx: "mdi:language-typescript",
    vue: "mdi:vuejs",
    json: "mdi:code-json",
    yaml: "mdi:file-code",
    yml: "mdi:file-code",
    py: "mdi:language-python",
    js: "mdi:language-javascript",
    jsx: "mdi:language-javascript",
    css: "mdi:language-css3",
    html: "mdi:language-html5",
    txt: "mdi:text",
    csv: "mdi:file-delimited",
    toml: "mdi:file-cog",
    env: "mdi:key-variant",
    sh: "mdi:console",
    svg: "mdi:svg",
    png: "mdi:file-image",
    jpg: "mdi:file-image",
    jpeg: "mdi:file-image",
    gif: "mdi:file-image",
    pdf: "mdi:file-pdf",
    doc: "mdi:file-word",
    docx: "mdi:file-word",
    xls: "mdi:file-excel",
    xlsx: "mdi:file-excel",
  };
  return iconMap[ext] || "mdi:file-document-outline";
}
</script>

<style scoped>
.filepicker-sidebar {
  --filepicker-toolbar-icon-size: clamp(
    var(--usx-font-size-xl),
    calc(var(--usx-font-size-lg) + 0.45vw),
    var(--usx-font-size-2xl)
  );
  --filepicker-inline-icon-size: clamp(
    var(--usx-font-size-base),
    calc(var(--usx-font-size-sm) + 0.3vw),
    var(--usx-font-size-lg)
  );
  --filepicker-tree-icon-size: clamp(
    var(--usx-font-size-base),
    calc(var(--usx-font-size-sm) + 0.25vw),
    var(--usx-font-size-lg)
  );
  --filepicker-aux-icon-size: clamp(
    var(--usx-font-size-sm),
    calc(var(--usx-font-size-sm) + 0.2vw),
    var(--usx-font-size-base)
  );
  --filepicker-ui-font-size: clamp(
    var(--usx-font-size-sm),
    calc(var(--usx-font-size-sm) + 0.18vw),
    var(--usx-font-size-base)
  );
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: var(--usx-spacing-sm);
  gap: var(--usx-spacing-xs);
  box-sizing: border-box;
  overflow-y: auto;
  background: transparent;
}

.filepicker-sidebar__header {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
}

.filepicker-sidebar__toolbar {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
  justify-content: flex-start;
  width: 100%;
}

.filepicker-sidebar__icon-btn {
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  border-radius: var(--usx-radius-sm);
  width: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  min-height: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  font-size: var(--usx-font-size-base);
}

.filepicker-sidebar__inline-icon {
  font-size: var(--filepicker-inline-icon-size);
}

.filepicker-sidebar__icon-btn:hover {
  color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 10%, transparent);
}

.filepicker-sidebar__icon-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.filepicker-sidebar__search-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.filepicker-sidebar__search {
  flex: 1;
  min-width: 0;
}

.filepicker-sidebar__mirror-message {
  padding: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: color-mix(in srgb, var(--usx-color-info) 10%, transparent);
  color: var(--usx-color-on-surface);
  font-size: var(--filepicker-ui-font-size);
}

.filepicker-sidebar__mode-inline {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
  color: var(--usx-color-on-surface-muted);
}

.filepicker-sidebar__mode-inline .filepicker-sidebar__inline-icon {
  font-size: var(--usx-font-size-sm);
}

.filepicker-sidebar__mode-select {
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  min-height: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  padding: 0 var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
}

.filepicker-sidebar :deep(.u-input) {
  min-height: var(--usx-control-size-sm);
  height: var(--usx-control-size-sm);
  padding: 0 var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
}

.filepicker-sidebar :deep(.u-input__icon) {
  font-size: var(--usx-font-size-base);
}

.filepicker-sidebar :deep(.u-input__field) {
  font-size: var(--filepicker-ui-font-size);
}

.filepicker-sidebar__banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  background: color-mix(in srgb, var(--usx-color-warning) 10%, transparent);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-warning);
  flex-shrink: 0;
}

.filepicker-sidebar__tree {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
}

.filepicker-sidebar__tree-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--usx-color-surface);
}

/* ─── Files-style sections ───────────────────────────────────────── */
.filepicker-sidebar__section {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.filepicker-sidebar__section-head {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  width: 100%;
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-semibold);
  min-height: var(--usx-control-size-sm);
  text-align: left;
}

.filepicker-sidebar__section-head:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 7%, transparent);
}

.filepicker-sidebar__section-chevron,
.filepicker-sidebar__section-icon {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-base);
  flex-shrink: 0;
}

.filepicker-sidebar__section-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__section-count {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  min-width: calc(var(--usx-control-size-sm) * 0.8);
  min-height: calc(var(--usx-control-size-sm) * 0.6);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 var(--usx-spacing-xs);
}

.filepicker-sidebar__section-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.filepicker-sidebar__section-empty {
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.filepicker-sidebar__tree-row {
  padding-left: calc(var(--depth) * var(--usx-spacing-sm));
}

.filepicker-sidebar__folder {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface);
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  text-align: left;
  min-height: var(--usx-control-size-sm);
}

.filepicker-sidebar__folder:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 7%, transparent);
}

.filepicker-sidebar__folder-chevron,
.filepicker-sidebar__folder-icon {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--filepicker-tree-icon-size);
}

.filepicker-sidebar__folder-name {
  flex: 1;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__folder-count {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  min-width: calc(var(--usx-control-size-sm) * 0.8);
  min-height: calc(var(--usx-control-size-sm) * 0.6);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 var(--usx-spacing-xs);
}

.filepicker-sidebar__item {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  transition: background var(--usx-transition-fast);
  min-height: var(--usx-control-size-sm);
}

.filepicker-sidebar__item:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 8%, transparent);
}

.filepicker-sidebar__item--active {
  background: color-mix(in srgb, var(--usx-color-primary) 13%, transparent);
}

.filepicker-sidebar__item--readonly {
  opacity: 0.7;
}

.filepicker-sidebar__item-icon {
  flex-shrink: 0;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--filepicker-tree-icon-size);
}

.filepicker-sidebar__item-name {
  flex: 1;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-regular);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__item-open {
  border: var(--usx-border-width) solid transparent;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: calc(var(--usx-control-size-sm) - var(--usx-spacing-xs));
  height: calc(var(--usx-control-size-sm) - var(--usx-spacing-xs));
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
}

.filepicker-sidebar__item-open:hover {
  background: color-mix(in srgb, var(--usx-color-primary) 12%, transparent);
  color: var(--usx-color-primary);
  border-color: color-mix(in srgb, var(--usx-color-primary) 35%, transparent);
}

.filepicker-sidebar__loading,
.filepicker-sidebar__error,
.filepicker-sidebar__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-lg);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--filepicker-ui-font-size);
  text-align: center;
}

.filepicker-sidebar__error {
  color: var(--usx-color-danger);
}

@media (max-width: 880px) {
  .filepicker-sidebar {
    padding: var(--usx-spacing-xs);
  }

  .filepicker-sidebar__toolbar {
    gap: var(--usx-spacing-xs);
    flex-wrap: nowrap;
    justify-content: flex-start;
  }

  .filepicker-sidebar__icon-btn {
    width: var(--usx-touch-min-sm);
    height: var(--usx-touch-min-sm);
  }
}
</style>
