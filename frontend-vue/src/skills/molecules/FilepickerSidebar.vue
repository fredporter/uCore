<template>
  <div class="filepicker-sidebar">
    <SidebarModeSwitch />
    <div id="workflow-editor-sidebar-context" />
    <WorkflowNavigator v-if="shell.sidebarMode !== 'vault'" :mission-mode="shell.sidebarMode === 'mission'" />
    <template v-else>
      <div class="filepicker-sidebar__actions filepicker-sidebar__toolbar" role="toolbar" aria-label="Vault actions">
        <button
          class="usx-btn filepicker-sidebar__action-btn"
          title="New file"
          @click="handleNewFile"
        >
          <UIcon name="note_add" />
        </button>
        <button
          class="usx-btn filepicker-sidebar__action-btn"
          title="New binder"
          @click="handleNewBinder"
        >
          <UIcon name="create_new_folder" />
        </button>
        <button
          class="usx-btn filepicker-sidebar__action-btn"
          title="Add Workspace"
          @click="pickerOpen = true"
        >
          <UIcon name="add_box" />
        </button>
        <button type="button" class="usx-btn filepicker-sidebar__action-btn" title="Refresh document index"
          aria-label="Refresh document index" :disabled="loading" @click="buildIndex">
          <UIcon name="refresh" aria-hidden="true" />
        </button>
        <RouterLink class="usx-btn filepicker-sidebar__action-btn" to="/workflow?tab=skills&skill=vault_discovery"
          title="Vault Skills" aria-label="Vault Skills">
          <UIcon name="extension" aria-hidden="true" />
        </RouterLink>
      </div>
    <form v-if="moveSelection" class="filepicker-sidebar__move" @submit.prevent="moveAcrossVaults">
      <strong :title="moveSelection.name">{{ moveSelection.name }}</strong>
      <label>Folder in {{ moveSelection.source === 'user' ? 'Shared Vaults' : 'User Vault' }}
        <input v-model="moveParent" placeholder="Vault root" :disabled="moving" />
      </label>
      <div class="filepicker-sidebar__move-actions">
        <button type="submit" class="usx-btn" :disabled="moving">Move</button>
        <button type="button" class="usx-btn" :disabled="moving" @click="moveSelection = null">Cancel</button>
      </div>
    </form>
    <div class="filepicker-sidebar__content">
      <section v-if="relatedFiles.length" class="filepicker-sidebar__workspace">
        <div class="filepicker-sidebar__header">
          <button type="button" class="usx-btn filepicker-sidebar__heading"
            :aria-expanded="relatedExpanded" :aria-controls="`${vaultContentId}-related`"
            @click="relatedExpanded = !relatedExpanded">
            <UIcon :name="relatedExpanded ? 'expand_more' : 'chevron_right'" aria-hidden="true" />
            Related
          </button>
        </div>
        <div v-show="relatedExpanded" :id="`${vaultContentId}-related`" class="filepicker-sidebar__workspace-body">
          <button v-for="{ file } in relatedFiles" :key="file.path" type="button"
            class="usx-btn filepicker-sidebar__related-link" :title="fileTitle(file)"
            @click="handleFileSelect(file)">
            <UIcon name="description" aria-hidden="true" />
            <span>{{ fileTitle(file) }}</span>
          </button>
        </div>
      </section>
      <div class="filepicker-sidebar__header">
        <button type="button" class="usx-btn filepicker-sidebar__heading"
          :aria-expanded="vaultExpanded" :aria-controls="vaultContentId"
          @click="vaultExpanded = !vaultExpanded">
          <UIcon :name="vaultExpanded ? 'expand_more' : 'chevron_right'" aria-hidden="true" />
          User Vault
        </button>
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

    <template v-else>
      <div v-show="vaultExpanded" :id="vaultContentId" class="filepicker-sidebar__vault-tree">
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
          @click="openUserFolder(row)"
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
              currentIndexedFile?.path === row.file.path,
          }"
          @click="handleFileSelect(row.file)"
          @dblclick="handleDoubleClick(row.file)"
        >
          <UIcon
            :name="getFileIcon(row.file.extension, row.file.filename)"
            class="filepicker-sidebar__item-icon"
          />

          <span class="filepicker-sidebar__item-name" :title="fileTitle(row.file)">{{
            fileTitle(row.file)
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
        <button v-if="canMove(row)" type="button" class="usx-btn filepicker-sidebar__move-btn"
          title="Move to another vault" aria-label="Move to another vault" @click="selectMove(row, 'user')">
          <UIcon name="drive_file_move" aria-hidden="true" />
        </button>
      </div>

      <div v-if="userRows.length === 0" class="filepicker-sidebar__empty">
        <UIcon name="mdi:file-document-outline" />
        <span>No files in the User Vault</span>
        <UButton size="sm" variant="ghost" @click="handleNewFile">
          Create a new file
        </UButton>
      </div>

      </div>

      <!-- Vault layers and registered workspaces -->
      <section
        v-for="ws in addedSections"
        :key="ws.source"
        class="filepicker-sidebar__workspace"
      >
        <div class="filepicker-sidebar__header">
          <button type="button" class="usx-btn filepicker-sidebar__heading"
            :aria-expanded="expandedSections.has(ws.source)"
            :aria-controls="`${vaultContentId}-${ws.source}`"
            @click="toggleSection(ws.source)">
            <UIcon :name="expandedSections.has(ws.source) ? 'expand_more' : 'chevron_right'" aria-hidden="true" />
            {{ ws.label }}
          </button>
          <div v-if="!ws.builtIn" class="filepicker-sidebar__actions">
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
              title="Remove workspace"
              @click="handleRemoveWorkspace(ws.source)"
            >
              <UIcon name="close" />
            </button>
          </div>
        </div>
        <div v-show="expandedSections.has(ws.source)" :id="`${vaultContentId}-${ws.source}`"
          class="filepicker-sidebar__workspace-body">
          <p v-if="!ws.count" class="filepicker-sidebar__empty">No indexed Markdown files</p>
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
                  currentIndexedFile?.path === row.file.path,
              }"
              @click="handleFileSelect(row.file)"
              @dblclick="handleDoubleClick(row.file)"
            >
              <UIcon
                :name="getFileIcon(row.file.extension, row.file.filename)"
                class="filepicker-sidebar__item-icon"
              />

              <span class="filepicker-sidebar__item-name" :title="fileTitle(row.file)">{{
                fileTitle(row.file)
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
            <button v-if="ws.source === 'shared' && canMove(row)" type="button" class="usx-btn filepicker-sidebar__move-btn"
              title="Move to another vault" aria-label="Move to another vault" @click="selectMove(row, 'shared')">
              <UIcon name="drive_file_move" aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>
    </template>

    </div>
    </template>
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
import { useRoute, useRouter } from "vue-router";
import { ref, computed, onMounted, watch, useId } from "vue";
import { useShellStore } from "../../stores/shell";
import SidebarModeSwitch from "./SidebarModeSwitch.vue";
import WorkflowNavigator from "./WorkflowNavigator.vue";
import UIcon from "../atoms/UIcon.vue";
import UButton from "../atoms/UButton.vue";
import USpinner from "../atoms/USpinner.vue";
import WorkspacePickerModal from "./WorkspacePickerModal.vue";
import { UCORE_BASE } from "../../api/base";
import { ucoreApi } from "../../api/client";
import { getEditorSurface } from "../../composables/useEditorSurface";
import { useWorkflowStore } from "../../stores/workflow";
import type { FileEntry } from "../../types/filepicker";


interface Props {
  open?: boolean;
  compact?: boolean;
  reader?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  open: true,
  compact: false,
  reader: false,
});

const emit = defineEmits<{
  fileSelect: [file: FileEntry, openEditor?: boolean];
  newFile: [binderId: string];
}>();
const wf = useWorkflowStore();
const editorSurface = getEditorSurface();
const shell = useShellStore();
const router = useRouter();
const route = useRoute();

// ─── Refs ───────────────────────────────────────────────────────────
const files = ref<FileEntry[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const indexStatus = ref<"ok" | "not-built" | "unknown">("unknown");
const mirrorMessage = ref("");
const vaultExpanded = ref(false);
const relatedExpanded = ref(false);
const expandedSections = ref<Set<string>>(new Set());
watch(() => props.reader, reading => {
  if (reading) expandedSections.value.add("global-knowledge");
}, { immediate: true });

function toggleSection(source: string) {
  const sections = new Set(expandedSections.value);
  if (sections.has(source)) sections.delete(source);
  else sections.add(source);
  expandedSections.value = sections;
}
const vaultContentId = useId();
const pickerOpen = ref(false);
const addedWorkspaces = ref<AddedWorkspace[]>([]);
const MARKDOWN_OPEN_MODE_KEY = "ucore.filepicker.markdown-open-mode";
const markdownOpenMode = ref<"auto" | "prose" | "code">("auto");
const selectedFile = ref<FileEntry | null>(null);
watch(() => [wf.selectedTask?.id, wf.binderDocument?.path], ([task, document]) => { if (task || document) selectedFile.value = null; });
const expandedFolders = ref<Set<string>>(new Set());
const collapsedActiveTopics = ref(new Set<string>());

interface FolderTreeRow {
  id: string;
  type: "folder";
  path: string;
  name: string;
  depth: number;
  fileCount: number;
  diskPath: string;
}

interface FileTreeRow {
  id: string;
  type: "file";
  depth: number;
  file: FileEntry;
}

type TreeRow = FolderTreeRow | FileTreeRow;

const moveSelection = ref<{ source: "user" | "shared"; path: string; name: string } | null>(null);
const moveParent = ref("");
const moving = ref(false);

function canMove(row: TreeRow) {
  return row.type === "folder" || !row.file.is_readonly;
}

function selectMove(row: TreeRow, source: "user" | "shared") {
  moveParent.value = "";
  mirrorMessage.value = "";
  moveSelection.value = row.type === "folder"
    ? { source, path: row.diskPath, name: row.name }
    : { source, path: row.file.path, name: row.file.filename };
}

async function moveAcrossVaults() {
  const entry = moveSelection.value;
  if (!entry || moving.value) return;
  moving.value = true;
  mirrorMessage.value = "";
  try {
    const response = await fetch(`${UCORE_BASE}/api/editor/files`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: entry.source,
        path: entry.path,
        parent: moveParent.value,
        destination_source: entry.source === "user" ? "shared" : "user",
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not move entry");
    moveSelection.value = null;
    selectedFile.value = null;
    const index = await ucoreApi.library.build();
    if (!index.ok) throw new Error("Entry moved. Rebuild the index to refresh the sidebar.");
    await fetchFiles();
    mirrorMessage.value = "Entry moved.";
  } catch (error) {
    mirrorMessage.value = error instanceof Error ? error.message : "Could not move entry";
  } finally {
    moving.value = false;
  }
}


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
    const targets = [...new Set(["user", "shared", "public", ...addedWorkspaces.value.map((w) => w.source)])];
    const results: FileEntry[] = [];
    const pageSize = 500;
    const bySource = await Promise.all(targets.map(async (source) => {
      const entries: FileEntry[] = [];
      const seen = new Set<string>();
      for (let offset = 0; ; offset += pageSize) {
        const res = await ucoreApi.library.search("*", source, pageSize, offset);
        if (!res.ok) throw new Error("Could not load the library index.");
        const page = ((res.data as { results?: FileEntry[] })?.results || []);
        const fresh = page.filter((entry) => !seen.has(entry.path));
        fresh.forEach((entry) => seen.add(entry.path));
        entries.push(...fresh);
        if (page.length < pageSize || !fresh.length) return entries;
      }
    }));
    results.push(...bySource.flat());
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
  emit("newFile", wf.activeBinderId || "");
}

/** Open the same canonical binder creation form used by Workflow. */
async function handleNewBinder() {
  wf.requestBinderCreation();
  await router.push({ path: "/workflow", query: { tab: "binder", ...(wf.activeBinderId ? { binder: wf.activeBinderId } : {}) } });
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

/** Unregister an added workspace from the sidebar. */
async function handleRemoveWorkspace(source: string) {
  mirrorMessage.value = "";
  try {
    const res = await ucoreApi.library.removeWorkspace(source);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    mirrorMessage.value = "Workspace removed.";
    await fetchWorkspaces();
    await fetchFiles();
  } catch (e: any) {
    mirrorMessage.value = `Remove failed: ${e?.message || e}`;
  }
}

function handleFileSelect(file: FileEntry) {
  selectedFile.value = file;
  if (!props.reader || !file.relative_path) wf.setEditorMode(resolveModeForFile(file));
  emit("fileSelect", { ...file });
}

function openInMode(file: FileEntry, mode: "prose" | "code") {
  wf.setEditorMode(mode);
  emit("fileSelect", { ...file }, true);
}

function handleDoubleClick(file: FileEntry) {
  // Could open in editor or navigate
  selectedFile.value = file;
  emit("fileSelect", file);
}

async function openUserFolder(row: FolderTreeRow) {
  if (props.reader) {
    toggleFolder("user", row.path);
    return;
  }
  const match = row.path.match(/^(?:binders\/)?([^/]+)$/i);
  const binder = match && wf.binders.find(item => item.id === match[1]);
  if (!binder) {
    toggleFolder("user", row.path);
    return;
  }
  try {
    const response = await fetch(`${UCORE_BASE}/api/binder/${encodeURIComponent(binder.id)}`, { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error("Could not open the Binder");
    const { binder: detail } = await response.json();
    const documents: { filename: string; path: string }[] = detail.documents || [];
    const document = documents.find(item => /^index\.md$/i.test(item.filename)) || documents[0];
    if (document) {
      if (!isFolderExpanded("user", row.path)) toggleFolder("user", row.path);
      await wf.openVaultDocument(document.path, document.filename, binder.id);
      await router.push({ path: "/workflow", query: { tab: "editor", binder: binder.id, file: document.path } });
    } else {
      wf.showBinder(binder.id);
      await router.push({ path: "/workflow", query: { tab: "binder", binder: binder.id } });
    }
  } catch (error) {
    mirrorMessage.value = error instanceof Error ? error.message : "Could not open the Binder";
  }
}

function folderKey(source: string, path: string): string {
  return `${source}:${path}`;
}

function isFolderExpanded(source: string, path: string): boolean {
  if (source === "global-knowledge" && currentIndexedFile.value &&
      isGlobalKnowledge(currentIndexedFile.value) &&
      topicKey(topicOf(currentIndexedFile.value) || "Unclassified") === path) {
    return !collapsedActiveTopics.value.has(path);
  }
  return expandedFolders.value.has(folderKey(source, path));
}

function toggleFolder(source: string, path: string) {
  if (source === "global-knowledge") {
    if (isFolderExpanded(source, path)) collapsedActiveTopics.value.add(path);
    else collapsedActiveTopics.value.delete(path);
  }
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
  if (!wf.binders.length) void wf.fetchBinders().catch(() => {});
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
  builtIn: boolean;
  rows: TreeRow[];
}

/** Segments to hide in the file tree (dot / @ / underscore folders). */
function isHiddenSegment(segment: string): boolean {
  return (
    segment.startsWith(".") ||
    segment.startsWith("@") ||
    segment.startsWith("_") ||
    segment === "Originals" ||
    segment === "Drop Box"
  );
}

/** Markdown files only, skipping hidden (. / @) paths — hides empty folders. */
function isVisibleFile(f: FileEntry): boolean {
  if (String(f.extension || "").toLowerCase() !== "md") return false;
  return !String(f.path || "")
    .split("/")
    .some(isHiddenSegment);
}

/** Strip the .md extension for display. */
function fileTitle(file: FileEntry): string {
  return file.title || file.filename.replace(/\.md$/i, "");
}

function topicOf(file: FileEntry) {
  if (file.knowledge?.topic) return file.knowledge.topic;
  if (!isGlobalKnowledge(file)) return "";
  const path = file.path.split("/global-knowledge/").at(-1)?.split("/") || [];
  return path.length > 1 ? path[0] : "";
}

function topicKey(topic: string) {
  return topic.trim().toLowerCase().replace(/[\s_]+/g, "-");
}

const currentIndexedFile = computed(() => {
  if (props.reader) {
    return files.value.find(file => file.reader_source === route.query.source && file.relative_path === route.query.article);
  }
  const path = editorSurface.currentFile.value?.path || wf.selectedFile?.path || selectedFile.value?.path;
  return files.value.find(file => file.path === path);
});

watch(currentIndexedFile, (file) => {
  if (!file) return;
  const section = publicSection(file);
  if (section === "user") vaultExpanded.value = true;
  else expandedSections.value.add(section);
});

const relatedFiles = computed(() => {
  const current = currentIndexedFile.value;
  if (!current) return [];
  const visible = files.value.filter(isVisibleFile);
  const referenceKey = (value: string) => value.split("#")[0].replace(/\.md$/i, "").trim().toLowerCase();
  const titles = new Map<string, Set<string>>();
  for (const file of visible) {
    for (const alias of [file.filename, fileTitle(file)]) {
      const key = referenceKey(alias);
      if (!titles.has(key)) titles.set(key, new Set());
      titles.get(key)!.add(file.path);
    }
  }
  const refersTo = (source: FileEntry, target: FileEntry) => source.knowledge?.references?.some((reference) => {
    if (reference === target.knowledge?.uid) return true;
    const paths = titles.get(referenceKey(reference));
    return paths?.size === 1 && paths.has(target.path);
  });
  const topic = topicKey(topicOf(current));
  return visible.filter((file) => file.path !== current.path)
    .map((file) => {
      const explicit = refersTo(current, file) || refersTo(file, current);
      const sameTopic = topic && topicKey(topicOf(file)) === topic;
      return { file, rank: explicit ? 2 : sameTopic ? 1 : 0 };
    })
    .filter(({ rank }) => rank > 0)
    .sort((a, b) => b.rank - a.rank || fileTitle(a.file).localeCompare(fileTitle(b.file)))
    .slice(0, 12);
});

function buildTopicRows(entries: FileEntry[]): TreeRow[] {
  const topics = new Map<string, { name: string; entries: FileEntry[] }>();
  for (const file of entries) {
    const name = topicOf(file) || "Unclassified";
    const key = topicKey(name);
    if (!topics.has(key)) topics.set(key, { name: name.replace(/[-_]/g, " "), entries: [] });
    topics.get(key)!.entries.push(file);
  }
  const rows: TreeRow[] = [];
  for (const [key, { name, entries: documents }] of [...topics].sort(([a], [b]) => a.localeCompare(b))) {
    rows.push({ id: `topic:${key}`, type: "folder", path: key, name, depth: 0,
      diskPath: "", fileCount: documents.length });
    if (isFolderExpanded("global-knowledge", key)) {
      for (const file of [...documents].sort((a, b) => fileTitle(a).localeCompare(fileTitle(b)))) {
        rows.push({ id: `file:${file.path}`, type: "file", depth: 1, file });
      }
    }
  }
  return rows;
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
        diskPath: root ? `${root}/${folder.path}` : folder.path,
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

const defaultSections = [
  { source: "shared", label: "Shared Vaults" },
  { source: "global-knowledge", label: "Global Knowledge" },
  { source: "udos-documentation", label: "uDOS Documentation" },
];

function publicSection(file: FileEntry) {
  if (file.source !== "public") return file.source;
  const path = file.path.toLowerCase();
  if (path.includes("/udos-docs/docs/")) return "udos-documentation";
  return path.split("/").includes("global-knowledge") ? "global-knowledge" : "public";
}

function isGlobalKnowledge(file: FileEntry) {
  return publicSection(file) === "global-knowledge";
}

const addedSections = computed<AddedSection[]>(() => {
  const registered = addedWorkspaces.value.filter(
    (workspace) => !defaultSections.some((section) => section.source === workspace.source),
  );
  const sections = [
    ...defaultSections.map((section) => ({ ...section, builtIn: true })),
    ...registered.map((workspace) => ({ source: workspace.source, label: workspace.source === "public" ? "Public Vaults" : workspace.name, builtIn: false })),
  ];
  return sections.map((section) => {
    const entries = files.value.filter((file) => {
      if (!isVisibleFile(file)) return false;
      return publicSection(file) === section.source;
    });
    return {
      ...section,
      count: entries.length,
      rows: section.source === "global-knowledge" ? buildTopicRows(entries) : buildTreeRows(entries, section.source),
    };
  });
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
      if (parts.length > 1 && !(source === "user" && parts[0].toLowerCase() === "memory")) {
        firstLevel.add(`${source}:${parts[0]}`);
      }
    }
  }
  expandedFolders.value = firstLevel;
}

// ─── Icon mapping ───────────────────────────────────────────────────
function getFileIcon(ext: string, filename?: string): string {
  if (
    ext === "ipynb" ||
    (filename && (filename.endsWith(".notebook.md") || filename.toLowerCase().includes("notebook")))
  ) {
    return "auto_stories";
  }
  const iconMap: Record<string, string> = {

    md: "description",
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
  box-sizing: border-box;
  min-height: 37px;
  padding: 4px 8px;
  border-bottom: 1px solid var(--usx-color-border);
  flex: 0 0 auto;
}

.filepicker-sidebar__content {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
  min-height: 0;
  overflow: hidden auto;
}

.filepicker-sidebar .filepicker-sidebar__heading {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  background: transparent;
  border-color: transparent;
  min-height: 28px;
  margin: 0;
  padding: 0;
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
}

.filepicker-sidebar form.filepicker-sidebar__move {
  display: grid;
  gap: 4px;
  margin: 0;
  padding: 6px 8px;
  border-bottom: 1px solid var(--usx-color-border);
  font-size: var(--usx-font-size-sm);
}
.filepicker-sidebar__move strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.filepicker-sidebar .filepicker-sidebar__move label {
  display: grid;
  gap: 3px;
  margin: 0;
}
.filepicker-sidebar .filepicker-sidebar__move input {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 30px;
  margin: 0;
  padding: 3px 8px;
  font-size: inherit;
}
.filepicker-sidebar__move-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}
.filepicker-sidebar .filepicker-sidebar__move .usx-btn {
  width: auto;
  min-height: 30px;
  margin: 0;
  padding: 3px 8px;
  font-size: inherit;
}
.filepicker-sidebar .filepicker-sidebar__move button[type="button"] {
  background: transparent;
  color: var(--usx-color-on-surface);
}
.filepicker-sidebar .filepicker-sidebar__move-btn.usx-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 28px;
  width: 28px;
  min-width: 0;
  height: 28px;
  min-height: 0;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
}
.filepicker-sidebar .filepicker-sidebar__move-btn.usx-btn:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
}
.filepicker-sidebar__toolbar {
  justify-content: flex-end;
  padding: 2px 8px;
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}
.filepicker-sidebar__toolbar .usx-btn { margin: 0; }
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

.filepicker-sidebar__content::-webkit-scrollbar {
  width: 4px;
}

.filepicker-sidebar__content::-webkit-scrollbar-thumb {
  background-color: var(--usx-color-border);
  border-radius: 2px;
}

/* ─── Added workspaces — each its own row like Vault ─────────────── */
/* padding: 0 overrides the global `.usx-section, section` rule. */
.filepicker-sidebar__vault-tree,
.filepicker-sidebar__workspace {
  flex-shrink: 0;
}

.filepicker-sidebar__workspace {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 0;
  border: 0;
  padding: 0;
}

.filepicker-sidebar__workspace-body {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.filepicker-sidebar__tree-row {
  display: flex;
  align-items: center;
  min-width: 0;
  padding-inline: calc(8px + var(--depth) * 16px) 4px;
}

.filepicker-sidebar__tree-row > :is(.filepicker-sidebar__folder, .filepicker-sidebar__item) {
  flex: 1 1 0;
  min-width: 0;
  width: auto;
}

.filepicker-sidebar__item-open:focus-visible,
.filepicker-sidebar__item:focus-within .filepicker-sidebar__item-open {
  opacity: 1;
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
.filepicker-sidebar .filepicker-sidebar__related-link.usx-btn {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--usx-spacing-xs);
  width: 100%;
  min-width: 0;
  min-height: 30px;
  margin: 0;
  padding: 2px 8px;
  border: 0;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  text-align: start;
}
.filepicker-sidebar .filepicker-sidebar__related-link.usx-btn:hover {
  background: var(--usx-color-border);
}
.filepicker-sidebar__related-link :deep(.u-icon) {
  flex-shrink: 0;
  color: var(--usx-color-on-surface-muted);
}
.filepicker-sidebar__related-link span:last-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
