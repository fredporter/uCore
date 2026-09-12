<template>
  <div class="wf-panel notebook-binder-panel">
    <div class="wf-panel__main wf-zen-surface">
      <!-- Standard Header -->
      <header class="wf-standard-header">
        <div>
          <p class="wf-standard-header__kicker">uFlow Anti-Drift Pipeline</p>
          <h2>Notebook Binders</h2>
          <p v-if="activeBinder">
            {{ activeBinder.metadata.title }} ·
            <span class="binder-status-badge" :class="`binder-status-badge--${activeBinder.metadata.state}`">
              {{ activeBinder.metadata.state }}
            </span>
          </p>
          <p v-else>Select or create a project binder to begin notebook production</p>
        </div>
        <div class="header-actions">
          <select
            v-if="binders.length"
            v-model="selectedBinderId"
            class="binder-select"
            @change="loadActiveBinder"
          >
            <option v-for="b in binders" :key="b.id || b.name" :value="b.id || b.name">
              {{ b.title || b.name }} ({{ b.state || 'active' }})
            </option>
          </select>
          <button class="wf-zen-primary" type="button" @click="showCreateModal = true">
            <UIcon name="add" /> New Binder
          </button>
        </div>
      </header>

      <!-- Loading / Error states -->
      <div v-if="loading" class="wf-loading">
        <UIcon name="sync" /> Loading binder data...
      </div>
      <div v-if="errorMessage" class="wf-error">
        <UIcon name="error" /> {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="wf-success">
        <UIcon name="check_circle" /> {{ successMessage }}
      </div>

      <!-- Binder Active Workspace -->
      <div v-if="activeBinder && !loading" class="binder-workspace">
        <!-- Stage Navigation Bar -->
        <nav class="stages-nav">
          <button
            v-for="(stage, idx) in STAGES"
            :key="stage.id"
            class="stage-tab"
            :class="{ 'stage-tab--active': currentStage === stage.id }"
            type="button"
            @click="currentStage = stage.id"
          >
            <span class="stage-step">{{ idx + 1 }}</span>
            <span class="stage-label">{{ stage.label }}</span>
            <span
              v-if="getStageBadge(stage.id)"
              class="stage-badge"
            >
              {{ getStageBadge(stage.id) }}
            </span>
          </button>
        </nav>

        <!-- Stage 1: Brief & Guardrails -->
        <section v-if="currentStage === 'brief'" class="stage-content stage-brief">
          <div class="brief-card">
            <h3>Project Brief & Outcome Contract</h3>
            <div class="markdown-preview" v-html="renderMarkdown(activeBinder.brief)" />
          </div>
        </section>

        <!-- Stage 2: Sources & Cryptographic Intake -->
        <section v-if="currentStage === 'sources'" class="stage-content stage-sources">
          <div class="sources-upload-box" @dragover.prevent @drop.prevent="onDropFiles">
            <UIcon name="cloud_upload" :size="32" />
            <p><strong>Drop document files here</strong> or choose files for cryptographic intake</p>
            <span class="subtext">Originals byte-preserved in ~/Vault/Originals/ with SHA-256 integrity</span>
            <input
              ref="fileInputRef"
              type="file"
              class="file-input-hidden"
              multiple
              @change="onFileSelected"
            />
            <button class="wf-zen-secondary" type="button" @click="triggerFileInput">
              Browse Files
            </button>
          </div>

          <div class="sources-ledger">
            <h3>Attached Sources Ledger ({{ activeBinder.sources.length }})</h3>
            <div v-if="activeBinder.sources.length === 0" class="empty-hint">
              No source documents attached yet. Ingest documents to provide factual citation backing.
            </div>
            <div
              v-for="src in activeBinder.sources"
              :key="src.citation_tag"
              class="source-row"
            >
              <span class="source-tag">{{ src.citation_tag }}</span>
              <div class="source-info">
                <strong>{{ src.file_name }}</strong>
                <span class="source-hash">SHA256: {{ src.source_sha256 }}</span>
                <span class="source-path">{{ src.markdown_path }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Stage 3: Requirements & Plan -->
        <section v-if="currentStage === 'plan'" class="stage-content stage-plan">
          <div class="plan-header">
            <h3>Requirements & Bounded Execution Plan</h3>
            <button class="wf-zen-primary" type="button" :disabled="runningAssembly" @click="runAssembly">
              <UIcon name="play_arrow" />
              {{ runningAssembly ? 'Assembling Draft...' : 'Run Bounded Assembly' }}
            </button>
          </div>

          <div class="requirements-grid">
            <div
              v-for="req in activeBinder.requirements"
              :key="req.id"
              class="req-card"
              :class="`req-card--${req.status}`"
            >
              <div class="req-card__header">
                <span class="req-id">{{ req.id }}</span>
                <span class="req-status">{{ req.status }}</span>
              </div>
              <h4>{{ req.title }}</h4>
              <p>{{ req.description }}</p>
            </div>
          </div>

          <div class="tasks-table-card">
            <h4>uFlow Task Pipeline</h4>
            <div v-for="t in activeBinder.plan" :key="t.task_id" class="task-row">
              <span class="task-id">{{ t.task_id }}</span>
              <span class="task-title">{{ t.title }}</span>
              <span class="task-req">{{ t.req_id }}</span>
              <span class="task-status" :class="`task-status--${t.status}`">{{ t.status }}</span>
            </div>
          </div>
        </section>

        <!-- Stage 4: Draft & Evidence Citations (Anti-Drift) -->
        <section v-if="currentStage === 'draft'" class="stage-content stage-draft">
          <div class="draft-toolbar">
            <div class="draft-hashes">
              <span>Base Hash: <code>{{ activeBinder.draft_sha256 ? activeBinder.draft_sha256.slice(0, 12) : 'none' }}...</code></span>
            </div>
            <div class="draft-actions">
              <button class="wf-zen-secondary" type="button" @click="reloadBinder">
                <UIcon name="refresh" /> Discard / Reload
              </button>
              <button class="wf-zen-primary" type="button" :disabled="savingDraft" @click="saveDraft">
                <UIcon name="save" /> {{ savingDraft ? 'Saving...' : 'Save Draft' }}
              </button>
            </div>
          </div>

          <!-- Concurrency conflict banner -->
          <div v-if="conflictDetected" class="conflict-alert">
            <UIcon name="warning" />
            <div>
              <strong>Concurrency Conflict Detected!</strong>
              <p>The draft on disk was modified elsewhere. Your changes were not overwritten. Click 'Discard / Reload' to fetch latest disk revision.</p>
            </div>
          </div>

          <div class="draft-editor-container">
            <textarea
              v-model="editableDraft"
              class="draft-textarea"
              placeholder="Draft contents..."
              rows="16"
            />
          </div>

          <div class="evidence-ledger">
            <h3>Evidence & Claim Citations Chain ({{ activeBinder.evidence.length }})</h3>
            <div v-if="activeBinder.evidence.length === 0" class="empty-hint">
              No evidence citations recorded. Run assembly or insert citation references.
            </div>
            <table v-else class="evidence-table">
              <thead>
                <tr>
                  <th>Requirement</th>
                  <th>Section</th>
                  <th>Citation</th>
                  <th>Source Hash</th>
                  <th>Verified</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="ev in activeBinder.evidence" :key="ev.req_id">
                  <td><code>{{ ev.req_id }}</code></td>
                  <td>{{ ev.section }}</td>
                  <td><span class="source-tag">{{ ev.citation }}</span></td>
                  <td><code>{{ ev.source_hash ? ev.source_hash.slice(0, 12) : '' }}...</code></td>
                  <td>{{ ev.verified_at ? new Date(ev.verified_at).toLocaleTimeString() : 'Verified' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Stage 5: Editions & Sovereign Publishing -->
        <section v-if="currentStage === 'publish'" class="stage-content stage-publish">
          <div class="acceptance-box">
            <h3>Accept Working Draft into Immutable Edition</h3>
            <p>Freezes current draft, requirements coverage, and evidence into a permanent snapshot.</p>
            <div class="accept-form">
              <input
                v-model="reviewerNotes"
                type="text"
                class="notes-input"
                placeholder="Reviewer notes / approval rationale..."
              />
              <button class="wf-zen-primary" type="button" :disabled="acceptingEdition" @click="acceptEdition">
                <UIcon name="verified" /> {{ acceptingEdition ? 'Accepting...' : 'Accept Edition' }}
              </button>
            </div>
          </div>

          <div class="editions-list">
            <h3>Accepted Editions & Sovereign Publication Receipts</h3>
            <div v-if="activeBinder.editions.length === 0" class="empty-hint">
              No accepted editions yet. Once the draft is reviewed, accept it to freeze edition 1.
            </div>
            <div
              v-for="ed in activeBinder.editions"
              :key="ed.edition"
              class="edition-card"
            >
              <div class="edition-card__header">
                <div class="edition-title">
                  <span class="edition-badge">Edition {{ ed.edition }}</span>
                  <strong>{{ ed.file_name }}</strong>
                </div>
                <button
                  class="wf-zen-primary"
                  type="button"
                  :disabled="publishingEdition === ed.edition"
                  @click="publishEdition(ed.edition)"
                >
                  <UIcon name="public" />
                  {{ publishingEdition === ed.edition ? 'Publishing...' : 'Publish Static Site' }}
                </button>
              </div>
              <p class="edition-notes">"{{ ed.reviewer_notes }}"</p>
              <div class="edition-meta">
                <span>SHA-256: <code>{{ ed.sha256 }}</code></span>
                <span>Sources: {{ ed.sources_count }}</span>
                <span>Created: {{ new Date(ed.created_at).toLocaleString() }}</span>
              </div>
            </div>
          </div>

          <div v-if="publicationReceipt" class="publication-receipt-card">
            <header>
              <UIcon name="check_circle" />
              <strong>Sovereign Publication Receipt</strong>
            </header>
            <div class="receipt-details">
              <div><strong>Target:</strong> {{ publicationReceipt.target }}</div>
              <div><strong>Published At:</strong> {{ publicationReceipt.published_at }}</div>
              <div><strong>Static Output:</strong> <code>{{ publicationReceipt.output_path }}</code></div>
              <div>
                <strong>Local URL:</strong>
                <a :href="publicationReceipt.output_url" target="_blank" rel="noopener">
                  {{ publicationReceipt.output_url }}
                </a>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Create Binder Modal -->
      <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
        <div class="modal-card">
          <header class="modal-header">
            <h3>Create Durable Project Binder</h3>
            <button type="button" @click="showCreateModal = false"><UIcon name="close" /></button>
          </header>
          <div class="modal-body">
            <label>Binder ID (folder name)
              <input v-model="newBinder.id" type="text" placeholder="project-spec" />
            </label>
            <label>Title
              <input v-model="newBinder.title" type="text" placeholder="Project Specification" />
            </label>
            <label>Outcome Goal
              <textarea v-model="newBinder.outcome" rows="3" placeholder="Concrete outcome to achieve..." />
            </label>
            <label>Audience
              <input v-model="newBinder.audience" type="text" placeholder="Engineers, Stakeholders" />
            </label>
          </div>
          <footer class="modal-footer">
            <button class="wf-zen-secondary" type="button" @click="showCreateModal = false">Cancel</button>
            <button class="wf-zen-primary" type="button" :disabled="creating" @click="createBinder">
              {{ creating ? 'Creating...' : 'Create Binder' }}
            </button>
          </footer>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import UIcon from "@/skills/atoms/UIcon.vue";

const STAGES = [
  { id: "brief", label: "Brief & Guardrails" },
  { id: "sources", label: "Sources & Intake" },
  { id: "plan", label: "Requirements & Plan" },
  { id: "draft", label: "Draft & Anti-Drift" },
  { id: "publish", label: "Editions & Publish" },
];

const binders = ref<any[]>([]);
const selectedBinderId = ref<string>("");
const activeBinder = ref<any>(null);
const currentStage = ref<string>("brief");

const loading = ref(false);
const savingDraft = ref(false);
const runningAssembly = ref(false);
const acceptingEdition = ref(false);
const publishingEdition = ref<number | null>(null);
const creating = ref(false);

const errorMessage = ref("");
const successMessage = ref("");
const conflictDetected = ref(false);

const editableDraft = ref("");
const loadedBaseHash = ref("");
const reviewerNotes = ref("");
const publicationReceipt = ref<any>(null);

const showCreateModal = ref(false);
const newBinder = ref({
  id: "",
  title: "",
  outcome: "",
  audience: "General",
});

const fileInputRef = ref<HTMLInputElement | null>(null);

function getStageBadge(stageId: string): string {
  if (!activeBinder.value) return "";
  if (stageId === "sources") return String(activeBinder.value.sources?.length || 0);
  if (stageId === "plan") return String(activeBinder.value.requirements?.length || 0);
  if (stageId === "publish") return String(activeBinder.value.editions?.length || 0);
  return "";
}

function renderMarkdown(md: string): string {
  if (!md) return "";
  // Safe simple formatting for display
  return md
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^\> (.*$)/gim, "<blockquote>$1</blockquote>")
    .replace(/\*\*(.*)\*\*/gim, "<strong>$1</strong>")
    .replace(/\*(.*)\*/gim, "<em>$1</em>")
    .replace(/`([^`]+)`/gim, "<code>$1</code>")
    .replace(/\n\n/gim, "<br><br>");
}

async function fetchBinders() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const res = await fetch("/api/binder/list");
    if (!res.ok) throw new Error(`Failed listing binders (${res.status})`);
    const data = await res.json();
    binders.value = data.binders || [];
    if (binders.value.length > 0 && !selectedBinderId.value) {
      selectedBinderId.value = binders.value[0].id || binders.value[0].name;
      await loadActiveBinder();
    }
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function loadActiveBinder() {
  if (!selectedBinderId.value) return;
  loading.value = true;
  errorMessage.value = "";
  conflictDetected.value = false;
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}`);
    if (!res.ok) throw new Error(`Failed loading binder (${res.status})`);
    const data = await res.json();
    activeBinder.value = data.binder;
    editableDraft.value = data.binder.draft || "";
    loadedBaseHash.value = data.binder.draft_sha256 || "";
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function reloadBinder() {
  await loadActiveBinder();
  successMessage.value = "Draft reloaded from disk revision.";
  setTimeout(() => { successMessage.value = ""; }, 3000);
}

function triggerFileInput() {
  fileInputRef.value?.click();
}

async function onFileSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  if (!target.files?.length) return;
  await uploadFiles(Array.from(target.files));
  target.value = "";
}

async function onDropFiles(event: DragEvent) {
  if (!event.dataTransfer?.files?.length) return;
  await uploadFiles(Array.from(event.dataTransfer.files));
}

async function uploadFiles(files: File[]) {
  if (!selectedBinderId.value) return;
  errorMessage.value = "";
  successMessage.value = "";
  loading.value = true;
  try {
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file, file.name);
      formData.append("author", "User");
      const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/intake`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || `Intake failed for ${file.name}`);
      }
    }
    successMessage.value = `Successfully ingested ${files.length} document(s) with SHA-256 provenance.`;
    await loadActiveBinder();
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function runAssembly() {
  if (!selectedBinderId.value) return;
  runningAssembly.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/run`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`Assembly failed (${res.status})`);
    const data = await res.json();
    activeBinder.value = data.binder;
    editableDraft.value = data.binder.draft;
    loadedBaseHash.value = data.binder.draft_sha256;
    currentStage.value = "draft";
    successMessage.value = "Draft successfully assembled with anti-drift citations!";
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    runningAssembly.value = false;
  }
}

async function saveDraft() {
  if (!selectedBinderId.value) return;
  savingDraft.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  conflictDetected.value = false;
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/draft`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: editableDraft.value,
        expected_base_hash: loadedBaseHash.value,
      }),
    });
    if (res.status === 409) {
      conflictDetected.value = true;
      const data = await res.json();
      throw new Error(data.message || "Concurrency conflict: base hash mismatch!");
    }
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || `Failed saving draft (${res.status})`);
    }
    const data = await res.json();
    loadedBaseHash.value = data.draft_sha256;
    if (activeBinder.value) {
      activeBinder.value.draft_sha256 = data.draft_sha256;
    }
    successMessage.value = "Draft saved cleanly with hash integrity verification.";
    setTimeout(() => { successMessage.value = ""; }, 3000);
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    savingDraft.value = false;
  }
}

async function acceptEdition() {
  if (!selectedBinderId.value) return;
  acceptingEdition.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/accept`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: reviewerNotes.value }),
    });
    if (!res.ok) throw new Error(`Accept edition failed (${res.status})`);
    const data = await res.json();
    successMessage.value = `Edition ${data.edition.edition} accepted and frozen into immutable storage.`;
    reviewerNotes.value = "";
    await loadActiveBinder();
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    acceptingEdition.value = false;
  }
}

async function publishEdition(edNum: number) {
  if (!selectedBinderId.value) return;
  publishingEdition.value = edNum;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edition: edNum, target: "local_static" }),
    });
    if (!res.ok) throw new Error(`Publish failed (${res.status})`);
    const data = await res.json();
    publicationReceipt.value = data.receipt;
    successMessage.value = `Edition ${edNum} successfully published to ~/Public/editions!`;
    await loadActiveBinder();
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    publishingEdition.value = null;
  }
}

async function createBinder() {
  if (!newBinder.value.id) return;
  creating.value = true;
  errorMessage.value = "";
  try {
    const res = await fetch("/api/binder/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newBinder.value),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `Creation failed (${res.status})`);
    }
    const data = await res.json();
    showCreateModal.value = false;
    newBinder.value = { id: "", title: "", outcome: "", audience: "General" };
    await fetchBinders();
    selectedBinderId.value = data.binder.metadata.id;
    await loadActiveBinder();
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    creating.value = false;
  }
}

onMounted(() => {
  void fetchBinders();
});
</script>

<style scoped>
.notebook-binder-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.binder-select {
  background: var(--surface-card, #1e293b);
  color: var(--text-primary, #f8fafc);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 6px;
  padding: 0.4rem 0.75rem;
  font-size: 0.875rem;
}

.binder-status-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.binder-status-badge--draft_brief { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }
.binder-status-badge--planned { background: rgba(56, 189, 248, 0.2); color: #38bdf8; }
.binder-status-badge--running { background: rgba(234, 179, 8, 0.2); color: #eab308; }
.binder-status-badge--ready_for_review { background: rgba(168, 85, 247, 0.2); color: #a855f7; }
.binder-status-badge--accepted { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.binder-status-badge--published { background: rgba(16, 185, 129, 0.25); color: #10b981; }

.stages-nav {
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border-subtle, #334155);
  margin-bottom: 1.5rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.stage-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted, #94a3b8);
  font-size: 0.875rem;
  cursor: pointer;
  white-space: nowrap;
}

.stage-tab:hover {
  background: rgba(255, 255, 255, 0.04);
}

.stage-tab--active {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.3);
  color: #38bdf8;
  font-weight: 600;
}

.stage-step {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  font-size: 0.75rem;
}

.stage-badge {
  background: rgba(255, 255, 255, 0.15);
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  font-size: 0.7rem;
}

.stage-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.brief-card {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1.5rem;
}

.sources-upload-box {
  border: 2px dashed var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  text-align: center;
}

.file-input-hidden { display: none; }
.subtext { font-size: 0.75rem; color: var(--text-muted, #94a3b8); }

.sources-ledger, .tasks-table-card, .evidence-ledger, .editions-list {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1.25rem;
}

.source-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid var(--border-subtle, #334155);
}

.source-tag {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-weight: 600;
  font-size: 0.75rem;
}

.source-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
}

.source-hash, .source-path {
  font-family: monospace;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.requirements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.req-card {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.req-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.req-id {
  font-family: monospace;
  font-weight: 700;
  color: #38bdf8;
  font-size: 0.85rem;
}

.req-status {
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 600;
}

.req-card--verified .req-status { color: #22c55e; }
.req-card--pending .req-status { color: #eab308; }

.task-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-subtle, #334155);
  font-size: 0.85rem;
}

.task-id { font-family: monospace; font-weight: 600; }
.task-title { flex: 1; }
.task-req { font-family: monospace; color: var(--text-muted, #94a3b8); }

.draft-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.draft-actions {
  display: flex;
  gap: 0.5rem;
}

.draft-textarea {
  width: 100%;
  background: #0f172a;
  color: #f8fafc;
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1rem;
  font-family: monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  resize: vertical;
}

.conflict-alert {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #ef4444;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.evidence-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.evidence-table th, .evidence-table td {
  padding: 0.6rem;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle, #334155);
}

.acceptance-box {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1.5rem;
}

.accept-form {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.notes-input {
  flex: 1;
  background: #0f172a;
  color: #f8fafc;
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
}

.edition-card {
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.edition-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.edition-badge {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  margin-right: 0.5rem;
}

.edition-meta {
  display: flex;
  gap: 1.5rem;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
}

.publication-receipt-card {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
  padding: 1.25rem;
  margin-top: 1rem;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal-card {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.modal-body label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  color: var(--text-muted, #94a3b8);
  gap: 0.25rem;
}

.modal-body input, .modal-body textarea {
  background: #0f172a;
  color: #f8fafc;
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 6px;
  padding: 0.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.wf-zen-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #38bdf8;
  color: #0f172a;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.wf-zen-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.wf-zen-secondary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: transparent;
  color: #f8fafc;
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 6px;
  padding: 0.5rem 0.85rem;
  cursor: pointer;
}

.wf-loading, .wf-error, .wf-success {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.wf-loading { background: rgba(56, 189, 248, 0.1); color: #38bdf8; }
.wf-error { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.wf-success { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.empty-hint { color: var(--text-muted, #94a3b8); font-size: 0.85rem; font-style: italic; padding: 1rem 0; }
</style>
