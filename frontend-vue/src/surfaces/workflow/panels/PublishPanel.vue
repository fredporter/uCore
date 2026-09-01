<template>
  <div class="wf-panel">
    <div class="wf-panel__main wf-zen-surface">
      <div v-if="!embedded" class="wf-toolbar">
        <div><h2>Publish</h2><p>Review the active document, then send it to a destination.</p></div>
      </div>

      <div v-if="wf.loading" class="wf-loading">
        <UIcon name="sync" /> Loading workflows...
      </div>

      <div class="wf-section">
        <div class="wf-publish-steps">
          <section>
            <span class="wf-field-label">Destination</span>
            <div class="wf-choice-row">
              <button :class="{ active: destination === 'jekyll' }" type="button" @click="destination = 'jekyll'">Local site</button>
              <button :class="{ active: destination === 'library' }" type="button" @click="destination = 'library'">Markdown library</button>
              <button type="button" disabled title="Connect a cloud publishing provider">Cloud publish · soon</button>
            </div>
          </section>
        </div>
        <div class="wf-publish-layout">
          <!-- Left: form fields -->
          <div class="wf-publish-form">
            <label class="wf-field">
              <span class="wf-field-label">Title</span>
              <input v-model="jekyllTitle" class="wf-input" type="text" placeholder="Untitled" />
            </label>
            <details class="wf-publish-advanced">
              <summary>Destination options</summary>
            <div class="wf-form-grid">
              <label class="wf-field">
                <span class="wf-field-label">Slug</span>
                <input
                  v-model="jekyllSlug"
                  class="wf-input"
                  type="text"
                  placeholder="my-new-post"
                />
              </label>
              <label class="wf-field">
                <span class="wf-field-label">Collection</span>
                <select v-model="jekyllCollection" class="wf-input">
                  <option value="posts">posts (_posts)</option>
                  <option value="pages">pages</option>
                  <option value="notes">notes (_notes)</option>
                </select>
              </label>
              <label class="wf-field">
                <span class="wf-field-label">Publish mode</span>
                <select v-model="jekyllMode" class="wf-input">
                  <option value="local">local</option>
                  <option value="cloud">cloud</option>
                </select>
              </label>
              <label class="wf-field">
                <span class="wf-field-label">Target repo</span>
                <input
                  v-model="jekyllTargetRepo"
                  class="wf-input"
                  type="text"
                  placeholder="owner/repo"
                />
              </label>
              <label class="wf-field">
                <span class="wf-field-label">Branch</span>
                <input
                  v-model="jekyllTargetBranch"
                  class="wf-input"
                  type="text"
                  placeholder="main"
                />
              </label>
              <label class="wf-field">
                <span class="wf-field-label">Commit message</span>
                <input
                  v-model="jekyllCommitMessage"
                  class="wf-input"
                  type="text"
                  placeholder="publish: my-new-post"
                />
              </label>
            </div>
            </details>

            <label v-if="false" class="wf-checkbox-row">
              <input
                v-model="jekyllExecuteGit"
                type="checkbox"
                :disabled="jekyllMode !== 'cloud'"
              />
              <span>Execute git publish (cloud only)</span>
            </label>
            <label v-if="false" class="wf-checkbox-row">
              <input
                v-model="jekyllEditMode"
                type="checkbox"
                true-value="code"
                false-value="prose"
              />
              <span>Code editing mode</span>
            </label>

            <div class="wf-workflow-footer">
              <span v-if="jekyllMessage" class="wf-muted">{{
                jekyllMessage
              }}</span>
              <UButton
                size="sm"
                variant="primary"
                icon="publish"
                :disabled="jekyllBusy"
                @click="publishJekyll"
              >
                {{ jekyllBusy ? "Preparing..." : "Prepare draft" }}
              </UButton>
            </div>

            <div v-if="jekyllOutput.path" class="wf-output">
              <p class="wf-monospace">Saved: {{ jekyllOutput.path }}</p>
              <div class="wf-output-grid">
                <div>
                  <p class="wf-output-title">Local preview</p>
                  <pre class="wf-code-block">{{
                    (jekyllOutput.next_steps?.local_preview || []).join("\n")
                  }}</pre>
                </div>
                <div>
                  <p class="wf-output-title">Cloud publish</p>
                  <pre class="wf-code-block">{{
                    (jekyllOutput.next_steps?.cloud_publish || []).join("\n")
                  }}</pre>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import UButton from "../../../skills/atoms/UButton.vue";
import { useWorkflowStore } from "../../../stores/workflow";
import { ucoreApi } from "../../../api/client";

const wf = useWorkflowStore();
const props = withDefaults(defineProps<{ sourceTitle?: string; sourceContent?: string; embedded?: boolean }>(), {
  sourceTitle: "",
  sourceContent: "",
  embedded: false,
});
const destination = ref<"jekyll" | "library">("jekyll");

const jekyllTitle = ref("");
const jekyllSlug = ref("");
const jekyllCollection = ref("posts");
const jekyllMode = ref<"local" | "cloud">("local");
const jekyllTargetRepo = ref("");
const jekyllTargetBranch = ref("main");
const jekyllExecuteGit = ref(false);
const jekyllCommitMessage = ref("");
const jekyllContent = ref("");
const jekyllEditMode = ref<"prose" | "code">("prose");
const jekyllBusy = ref(false);
const jekyllMessage = ref("");
const jekyllOutput = ref<any>({});

watch(() => [props.sourceTitle, props.sourceContent], ([title, content]) => {
  jekyllTitle.value = title || "Untitled";
  jekyllContent.value = content || "";
  jekyllSlug.value = jekyllTitle.value.toLowerCase().replace(/\.(md|markdown)$/i, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  jekyllCommitMessage.value = `publish: ${jekyllSlug.value}`;
}, { immediate: true });

watch(
  () => wf.selectedTask,
  (task) => {
    if (!task) return;
    if (!jekyllTitle.value) jekyllTitle.value = task.title || "";
    if (!jekyllContent.value) jekyllContent.value = task.description || "";
  },
  { immediate: true },
);

watch(
  () => wf.selectedFile,
  (file) => {
    if (!file) return;
    if (!jekyllTitle.value) jekyllTitle.value = file.filename || "";
    if (!jekyllContent.value) jekyllContent.value = file.content || "";
  },
  { immediate: true },
);

async function publishJekyll(): Promise<void> {
  if (!jekyllContent.value.trim()) {
    jekyllMessage.value = "Markdown draft content is required.";
    return;
  }

  jekyllBusy.value = true;
  jekyllMessage.value = "";
  jekyllOutput.value = {};

  try {
    const res = await ucoreApi.userWorkflow.publishJekyll({
      content: jekyllContent.value,
      title: jekyllTitle.value,
      slug: jekyllSlug.value,
      collection: jekyllCollection.value,
      publish_mode: jekyllMode.value,
      target_repo: jekyllTargetRepo.value,
      target_branch: jekyllTargetBranch.value,
      execute_git: jekyllExecuteGit.value && jekyllMode.value === "cloud",
      commit_message: jekyllCommitMessage.value,
      vault_layer: "public",
    });

    if (!res.ok) {
      jekyllMessage.value = `Publish prep failed (HTTP ${res.status}).`;
      return;
    }

    jekyllOutput.value = res.data || {};
    jekyllMessage.value = "Jekyll draft prepared successfully.";
  } catch (e: any) {
    jekyllMessage.value = e?.message || "Publish prep failed.";
  } finally {
    jekyllBusy.value = false;
  }
}
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: row;
  gap: 0;
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.wf-panel__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  overflow-y: auto;
  width: min(100%, 64rem);
  margin: 0 auto;
  padding: clamp(var(--usx-spacing-md), 4vw, var(--usx-spacing-2xl));
}

.wf-panel__main { width: 100%; padding: var(--usx-spacing-md); }
.wf-publish-layout, .wf-publish-form { width: 100%; max-width: none; }

.wf-publish-layout {
  display: flex;
  gap: var(--usx-spacing-md);
  min-height: 0;
}

.wf-publish-form {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  max-width: 480px;
}

.wf-publish-editor {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
  border-left: var(--usx-border-width) solid var(--usx-color-border);
  padding-left: var(--usx-spacing-md);
}

.wf-publish-editor__header {
  flex-shrink: 0;
}

/* Stack on narrow screens */
@media (max-width: 800px) {
  .wf-publish-layout {
    flex-direction: column;
  }
  .wf-publish-form {
    max-width: none;
  }
  .wf-publish-editor {
    border-left: none;
    padding-left: 0;
  }
}

.wf-loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.wf-toolbar h2, .wf-toolbar p { margin: 0; }
.wf-toolbar p { color: var(--usx-color-on-surface-muted); }
.wf-publish-steps { display: grid; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-md); }
.wf-publish-steps section { padding: var(--usx-spacing-sm); border: 0 !important; border-radius: var(--usx-radius-sm); background: color-mix(in srgb, var(--usx-color-surface) 72%, var(--usx-color-primary) 3%); }
.wf-choice-row { display: flex; flex-wrap: wrap; gap: var(--usx-spacing-xs); margin-top: var(--usx-spacing-xs); }
.wf-choice-row button { min-height: 2.25rem; padding: 0 var(--usx-spacing-md); border: 0; border-radius: var(--usx-radius-full); background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface); cursor: pointer; }
.wf-choice-row button.active { color: var(--usx-color-primary); background: color-mix(in srgb, var(--usx-color-primary) 14%, var(--usx-color-surface)); }
.wf-choice-row button:disabled { opacity: .45; cursor: default; }
.wf-publish-advanced { border-top: var(--usx-border-width) solid var(--usx-color-border); padding-top: var(--usx-spacing-sm); }
.wf-publish-advanced summary { cursor: pointer; color: var(--usx-color-on-surface-muted); margin-bottom: var(--usx-spacing-sm); }

.wf-section-title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: var(--usx-letter-spacing-wide);
}

.wf-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(18ch, 1fr));
  gap: var(--usx-spacing-sm);
}

.wf-field {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.wf-field--full {
  width: 100%;
}

.wf-field-label {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  font-weight: var(--usx-font-weight-medium);
}

.wf-input {
  width: 100%;
  border: var(--usx-border-width) solid var(--usx-color-border);
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  outline: none;
  box-shadow: none;
}

.wf-input:focus {
  border-color: var(--usx-color-primary);
}

.wf-output {
  border-top: var(--usx-border-width) solid var(--usx-color-border);
  padding-top: var(--usx-spacing-sm);
}

.wf-output-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(24ch, 1fr));
  gap: var(--usx-spacing-sm);
}

.wf-git-output {
  margin-top: var(--usx-spacing-sm);
}

.wf-checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.wf-checkbox-row input[type="checkbox"] {
  accent-color: var(--usx-color-primary);
  min-height: 0;
  width: auto;
}

.wf-output-title {
  margin: 0 0 var(--usx-spacing-xs) 0;
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.wf-code-block {
  margin: 0;
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-background);
  padding: var(--usx-spacing-sm);
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-sm);
  overflow-x: auto;
}

.wf-workflow-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.wf-muted {
  color: var(--usx-color-on-surface-muted);
}

.wf-empty-small {
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  text-align: center;
  font-style: italic;
}

.wf-monospace {
  font-family: var(--usx-font-family-mono);
}
</style>
