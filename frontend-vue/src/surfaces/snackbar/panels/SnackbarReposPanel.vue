<template>
  <div class="wf-panel">
    <div class="wf-toolbar">
      <span class="wf-toolbar__count">
        <UIcon name="folder" />
        {{ activeRepo || "Repositories" }}
      </span>
      <span v-if="repos.length" class="wf-toolbar__count">
        {{ repos.length }} repos
      </span>
      <button v-if="activeRepo" class="wf-toolbar__btn" @click="activeRepo = ''; fileTree = []">
        <UIcon name="arrow_back" /> Back
      </button>
    </div>
    <div v-if="apiError" class="wf-error"><UIcon name="error" /> {{ apiError }}</div>
    <div v-if="!activeRepo" class="doc-site-grid">
      <div v-if="loadingRepos" class="wf-loading"><UIcon name="sync" /> Loading repos...</div>
      <div v-for="repo in repos" :key="repo.name" class="doc-site-hero" @click="openRepo(repo.name)">
        <div class="doc-site-hero-icon"><UIcon :name="repo.dirty ? 'sync' : 'folder'" /></div>
        <div class="doc-site-hero-content">
          <h4 class="doc-site-hero-title">{{ repo.name }}</h4>
          <code class="doc-mono">{{ repo.branch }}</code>
        </div>
        <UBadge :type="repo.dirty ? 'warning' : 'success'" size="sm">{{ repo.dirty ? 'dirty' : 'clean' }}</UBadge>
      </div>
      <div v-if="!loadingRepos && repos.length === 0" class="wf-empty">No repositories found under ~/Code/.</div>
    </div>
    <div v-else>
      <div v-if="loadingFiles" class="wf-loading"><UIcon name="sync" /> Loading files...</div>
      <div v-else class="doc-publish-list">
        <div v-for="file in fileTree" :key="file.path" class="doc-publish-row" @click="openFile(file.path)">
          <UIcon :name="file.type === 'dir' ? 'folder_open' : 'description'" />
          <span class="doc-publish-name">{{ file.name }}</span>
          <code class="doc-mono">{{ file.path }}</code>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UBadge from "../../../skills/atoms/UBadge.vue";

interface RepoItem { name: string; branch: string; dirty: boolean; path: string; }
interface FileItem { name: string; path: string; type: "file" | "dir"; size?: number; }

const repos = ref<RepoItem[]>([]);
const fileTree = ref<FileItem[]>([]);
const activeRepo = ref("");
const loadingRepos = ref(true);
const loadingFiles = ref(false);
const apiError = ref("");

async function fetchRepos() {
  loadingRepos.value = true;
  apiError.value = "";
  try {
    const res = await fetch("/api/developer/repos", { signal: AbortSignal.timeout(8000) });
    if (res.ok) { const data = await res.json(); repos.value = data.repos || []; }
    else { apiError.value = "Repo API returned " + res.status; }
  } catch (e: any) { apiError.value = e.message || "Repo API unavailable"; }
  loadingRepos.value = false;
}

async function openRepo(name: string) {
  activeRepo.value = name;
  loadingFiles.value = true;
  apiError.value = "";
  try {
    const url = "/api/developer/repos/" + encodeURIComponent(name) + "/files";
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    if (res.ok) { const data = await res.json(); fileTree.value = data.files || []; }
    else { apiError.value = "File API returned " + res.status; }
  } catch (e: any) { apiError.value = e.message || "File API unavailable"; }
  loadingFiles.value = false;
}

function openFile(path: string) {
  window.dispatchEvent(new CustomEvent("snackbar-repo-file-open", {
    detail: { repo: activeRepo.value, path, openEditor: true },
  }));
}

onMounted(fetchRepos);
</script>

<style scoped>
.wf-panel { display: flex; flex-direction: column; gap: var(--usx-spacing-md); }
.wf-toolbar { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm) var(--usx-spacing-md); background: var(--usx-color-surface-variant); border-radius: var(--usx-radius-sm); font-size: var(--usx-font-size-sm); }
.wf-toolbar__count { display: flex; align-items: center; gap: var(--usx-spacing-xs); font-weight: var(--usx-font-weight-medium); }
.wf-toolbar__btn { display: inline-flex; align-items: center; gap: var(--usx-spacing-xs); padding: var(--usx-spacing-xs) var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-sm); background: var(--usx-color-surface); color: var(--usx-color-on-surface); cursor: pointer; font-size: var(--usx-font-size-sm); }
.wf-toolbar__btn:hover { background: var(--usx-color-surface-variant); }
.wf-loading, .wf-empty, .wf-error { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-xl); color: var(--usx-color-on-surface-muted); font-size: var(--usx-font-size-sm); justify-content: center; }
.wf-error { color: var(--usx-color-danger); }
</style>
