<template>
  <div class="filepicker-sidebar">
    <div class="filepicker-sidebar__header">
      <span class="filepicker-sidebar__heading">Vault</span>
      <div class="filepicker-sidebar__actions">
        <button
          class="filepicker-sidebar__action-btn"
          title="New file"
          @click="handleNewFile"
        >
          <UIcon name="note_add" />
        </button>
        <button
          class="filepicker-sidebar__action-btn"
          title="New binder"
          @click="handleNewBinder"
        >
          <UIcon name="create_new_folder" />
        </button>
        <button
          class="filepicker-sidebar__action-btn"
          title="Add Workspace"
          @click="pickerOpen = true"
        >
          <UIcon name="add_box" />
        </button>
      </div>
    </div>

    <div v-if="mirrorMessage" class="filepicker-sidebar__mirror-message">
      {{ mirrorMessage }}
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

    <div v-else class="filepicker-sidebar__scroll">
      <!-- User Vault — always shown, locked as the default -->
      <div
        v-for="row in userRows"
        :key="row.id"
        class="filepicker-sidebar__tree-row"
        :style="{ '--depth': String(row.depth) }"
      >
        <button
          v-if="row.type === 'folder'"
          class="filepicker-sidebar__folder"
          @click="toggleFolder('user', row.path)"
        >
          <UIcon
            :name="
              isFolderExpanded('user', row.path)
                ? 'expand_more'
                : 'chevron_right'
            "
            class="filepicker-sidebar__folder-chevron"
          />
          <UIcon name="folder" class="filepicker-sidebar__folder-icon" />
          <span class="filepicker-sidebar__folder-name">{{ row.name }}</span>
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
            displayName(row.file.filename)
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

      <div v-if="userRows.length === 0" class="filepicker-sidebar__empty">
        <UIcon name="mdi:file-document-outline" />
        <span>No files in the User Vault</span>
        <UButton size="sm" variant="ghost" @click="handleNewFile">
          Create a new file
        </UButton>
      </div>

      <!-- Added workspaces: each its own row like Vault, 3 icons as breaker -->
      <section
        v-for="ws in addedSections"
        :key="ws.source"
        class="filepicker-sidebar__workspace"
      >
        <div class="filepicker-sidebar__workspace-header">
          <span class="filepicker-sidebar__workspace-title">{{
            ws.label
          }}</span>
          <div class="filepicker-sidebar__actions">
            <button
              class="filepicker-sidebar__action-btn"
              title="New file"
              @click="handleWorkspaceNewFile(ws.source)"
            >
              <UIcon name="note_add" />
            </button>
            <button
              class="filepicker-sidebar__action-btn"
              title="New binder"
              @click="handleWorkspaceNewBinder(ws.source)"
            >
              <UIcon name="create_new_folder" />
            </button>
            <button
              class="filepicker-sidebar__action-btn"
              title="Add Workspace"
              @click="pickerOpen = true"
            >
              <UIcon name="add_box" />
            </button>
          </div>
        </div>
        <div class="filepicker-sidebar__workspace-body">
          <div
            v-for="row in ws.rows"
            :key="row.id"
            class="filepicker-sidebar__tree-row"
            :style="{ '--depth': String(row.depth) }"
          >
            <button
              v-if="row.type === 'folder'"
              class="filepicker-sidebar__folder"
              @click="toggleFolder(ws.source, row.path)"
            >
              <UIcon
                :name="
                  isFolderExpanded(ws.source, row.path)
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
                displayName(row.file.filename)
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
        </div>
      </section>
    </div>

    <WorkspacePickerModal
      v-if="pickerOpen"
      @close="pickerOpen = false"
      @added="onWorkspaceAdded"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * @component FilepickerSidebar
 * @description Vault-style sidebar — always locked to the local User Vault,
 * with user-added workspaces (existing vaults/folders) shown as their own rows
 * below. Shows markdown files only. New File / New Binder / Add Workspace actions.
 * @category molecules
 * @props {boolean} open - Sidebar visibility
 * @props {boolean} compact - Compact mode
 * @emits {FileEntry} fileSelect - File selected
 * @emits {string} newFile - New file requested
 * @usage <FilepickerSidebar :open="true" @file-select="handleFileSelect" />
 */
import { ref, computed, onMounted, watch } from "vue";
import UIcon from "../atoms/UIcon.vue";
import UButton from "../atoms/UButton.vue";
import USpinner from "../atoms/USpinner.vue";
import WorkspacePickerModal from "./WorkspacePickerModal.vue";
import { ucoreApi } from "../../api/client";
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
const wf = useWorkflowStore();

// ─── Refs ───────────────────────────────────────────────────────────
const files = ref<FileEntry[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const indexStatus = ref<"ok" | "not-built" | "unknown">("unknown");
const mirrorMessage = ref("");
const pickerOpen = ref(false);
const addedWorkspaces = ref<AddedWorkspace[]>([]);
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

// ─── Fetch files from the unified library index ────────────────────
// Fetches per source (User Vault + added workspaces) so added workspaces
// are never crowded out of the result window by other index entries.
async function fetchFiles() {
  loading.value = true;
  error.value = null;
  try {
    const targets = ["user", ...addedWorkspaces.value.map((w) => w.source)];
    const results: FileEntry[] = [];
    for (const src of targets) {
      const res = await ucoreApi.library.search("*", src, 1000);
      if (res.ok && res.data) {
        results.push(...((res.data as any).results || []));
      }
    }
    files.value = results.filter(
      (f: FileEntry) => Boolean(f.source) && targets.includes(f.source),
    );
    autoExpandFirstLevel(files.value);
  } catch (e: any) {
    error.value = e.message || "Failed to fetch files";
    files.value = [];
  } finally {
    loading.value = false;
  }
}

async function fetchWorkspaces() {
  try {
    const res = await ucoreApi.library.workspaces();
    if (res.ok && res.data) {
      addedWorkspaces.value = ((res.data as any).workspaces || [])
        .filter((w: any) => w.exists)
        .map((w: any) => ({
          name: String(w.name || ""),
          path: String(w.path || ""),
          source: String(w.source || ""),
        }));
    }
  } catch {
    addedWorkspaces.value = [];
  }
}

function onWorkspaceAdded() {
  mirrorMessage.value = "Workspace added.";
  void fetchWorkspaces().then(() => fetchFiles());
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

function handleNewFile() {
  emit("newFile", "user");
}

/** Create a new binder (workspace folder) in the User Vault root. */
async function handleNewBinder() {
  const raw = window.prompt("New binder name", "");
  const name = (raw || "").trim();
  if (!name) return;
  mirrorMessage.value = "";
  try {
    const res = await ucoreApi.userWorkflow.importMarkdown({
      content: `# ${name}\n\nBinder workspace for **${name}**.\n`,
      source_format: "markdown",
      title: `${name} README`,
      binder: name,
      vault_layer: "user",
      relative_dir: name,
      filename: "README.md",
      metadata: { imported_from: "filepicker.new-binder" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    mirrorMessage.value = `Binder \"${name}\" created.`;
    await fetchFiles();
  } catch (e: any) {
    mirrorMessage.value = `Binder create failed: ${e?.message || e}`;
  }
}

/** Create a markdown file inside an added workspace. */
async function handleWorkspaceNewFile(source: string) {
  const raw = window.prompt("New file title", "Untitled");
  const title = (raw || "").trim();
  if (!title) return;
  if (await createWorkspaceDoc(source, { title })) {
    mirrorMessage.value = "File created.";
  }
}

/** Create a binder folder inside an added workspace. */
async function handleWorkspaceNewBinder(source: string) {
  const raw = window.prompt("New binder name", "");
  const name = (raw || "").trim();
  if (!name) return;
  if (
    await createWorkspaceDoc(source, {
      title: `${name} README`,
      filename: "README.md",
      binder: name,
    })
  ) {
    mirrorMessage.value = `Binder "${name}" created.`;
  }
}

async function createWorkspaceDoc(
  source: string,
  payload: { title: string; filename?: string; binder?: string },
): Promise<boolean> {
  mirrorMessage.value = "";
  try {
    const res = await ucoreApi.library.createWorkspaceFile({
      source,
      title: payload.title,
      filename: payload.filename || "",
      binder: payload.binder || "",
      content: `# ${payload.title}\n\n`,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    await fetchFiles();
    return true;
  } catch (e: any) {
    mirrorMessage.value = `Create failed: ${e?.message || e}`;
    return false;
  }
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

function handleDoubleClick(file: FileEntry) {
  // Could open in editor or navigate
  selectedFile.value = file;
  emit("fileSelect", file);
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

onMounted(async () => {
  loadMarkdownOpenMode();
  await fetchWorkspaces();
  await checkIndex();
  if (indexStatus.value === "ok") {
    await fetchFiles();
  }
});

// ─── Workspace definitions ─────────────────────────────────────────
interface AddedWorkspace {
  name: string;
  path: string;
  source: string;
}

interface AddedSection {
  source: string;
  label: string;
  count: number;
  rows: TreeRow[];
}

/** Segments to hide in the file tree (dot-folders, @-workspaces). */
function isHiddenSegment(segment: string): boolean {
  return segment.startsWith(".") || segment.startsWith("@");
}

/** Markdown files only, skipping hidden (. / @) paths — hides empty folders. */
function isVisibleFile(f: FileEntry): boolean {
  if (String(f.extension || "").toLowerCase() !== "md") return false;
  return !String(f.path || "")
    .split("/")
    .some(isHiddenSegment);
}

/** Strip the .md extension for display. */
function displayName(filename: string): string {
  return filename.replace(/\.md$/i, "");
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

// ─── Lists ──────────────────────────────────────────────────────────
const userRows = computed<TreeRow[]>(() =>
  buildTreeRows(
    files.value.filter(
      (f) => (f.source || "user") === "user" && isVisibleFile(f),
    ),
    "user",
  ),
);

const addedSections = computed<AddedSection[]>(() =>
  addedWorkspaces.value.map((ws) => {
    const wsFiles = files.value.filter(
      (f) => f.source === ws.source && isVisibleFile(f),
    );
    return {
      source: ws.source,
      label: ws.name,
      count: wsFiles.length,
      rows: buildTreeRows(wsFiles, ws.source),
    };
  }),
);

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
  height: 100%;
  min-height: 100%;
  padding: 0;
  gap: 0;
  box-sizing: border-box;
  overflow: hidden;
  background-color: var(--usx-color-surface-variant);
}

.filepicker-sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border-bottom: 1px solid var(--usx-color-border);
  flex-shrink: 0;
}

.filepicker-sidebar__heading {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
}

.filepicker-sidebar__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  flex-shrink: 0;
}

.filepicker-sidebar__action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  min-height: 0;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: 16px;
  transition: all 120ms ease;
}

.filepicker-sidebar__action-btn:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

.filepicker-sidebar__mirror-message {
  padding: var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: color-mix(in srgb, var(--usx-color-info) 10%, transparent);
  color: var(--usx-color-on-surface);
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

.filepicker-sidebar__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: var(--usx-spacing-xs) 0;
}

.filepicker-sidebar__scroll::-webkit-scrollbar {
  width: 4px;
}

.filepicker-sidebar__scroll::-webkit-scrollbar-thumb {
  background-color: var(--usx-color-border);
  border-radius: 2px;
}

/* ─── Added workspaces — each its own row like Vault ─────────────── */
.filepicker-sidebar__workspace {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-top: var(--usx-spacing-sm);
  border-top: 1px solid var(--usx-color-border);
}

.filepicker-sidebar__workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  flex-shrink: 0;
}

.filepicker-sidebar__workspace-title {
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__workspace-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.filepicker-sidebar__tree-row {
  padding-left: calc(8px + var(--depth) * 16px);
}

.filepicker-sidebar__folder {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface);
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 3px var(--usx-spacing-sm);
  border-radius: 0;
  cursor: pointer;
  text-align: left;
  user-select: none;
  min-height: 0;
}

.filepicker-sidebar__folder:hover {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    transparent
  );
}

.filepicker-sidebar__folder-chevron {
  font-size: 16px;
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
  width: 16px;
}

.filepicker-sidebar__folder-icon {
  font-size: 14px;
  color: var(--usx-color-warning);
  flex-shrink: 0;
}

.filepicker-sidebar__folder-name {
  flex: 1;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-regular);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__folder-count {
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  opacity: 0.7;
}

.filepicker-sidebar__item {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: 3px var(--usx-spacing-sm);
  border-radius: 0;
  cursor: pointer;
  transition: background-color 100ms ease;
  user-select: none;
}

.filepicker-sidebar__item:hover {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 8%,
    transparent
  );
}

.filepicker-sidebar__item--active {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 16%,
    transparent
  );
}

.filepicker-sidebar__item--active .filepicker-sidebar__item-name {
  color: var(--usx-color-primary);
  font-weight: var(--usx-font-weight-medium);
}

.filepicker-sidebar__item--readonly {
  opacity: 0.7;
}

.filepicker-sidebar__item-icon {
  flex-shrink: 0;
  color: var(--usx-color-on-surface-muted);
  font-size: 14px;
}

.filepicker-sidebar__item--active .filepicker-sidebar__item-icon {
  color: var(--usx-color-primary);
}

.filepicker-sidebar__item-name {
  flex: 1;
  font-size: var(--usx-font-size-sm);
  font-weight: var(--usx-font-weight-regular);
  color: var(--usx-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filepicker-sidebar__item-open {
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  min-height: 0;
  border-radius: var(--usx-radius-sm);
  cursor: pointer;
  font-size: var(--usx-font-size-sm);
  opacity: 0;
  transition: all 120ms ease;
}

.filepicker-sidebar__item:hover .filepicker-sidebar__item-open {
  opacity: 1;
}

.filepicker-sidebar__item-open:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
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
  .filepicker-sidebar__actions {
    gap: var(--usx-spacing-xs);
  }
}
</style>
