<template>
  <section class="workflow-skills wf-zen-surface">
    <h2>Skills</h2>
    <section>
      <h3>Format Markdown</h3>
      <p>Ask OK Assistant to structure a draft for review and preserve its links and metadata.</p>
      <RouterLink class="usx-btn" :to="assistant('processing', 'Format this draft as universal Markdown. Preserve links, metadata and meaning.')">
        <UIcon name="auto_awesome" aria-hidden="true" /> Open OK Assistant
      </RouterLink>
      <p>Run from uCore to preview normalized Markdown and validate intake metadata.</p>
      <pre>backend/.venv/bin/python scripts/format_universal_markdown.py draft.md</pre>
    </section>
    <section>
      <h3>Deduplicate and index</h3>
      <p>Feed intake skips identical entries and keeps changed entries as revisions. Rebuild the library index after reviewing changes.</p>
      <RouterLink class="usx-btn" :to="assistant('knowledge', 'Review these notes for duplicates and suggest which to merge.')">
        <UIcon name="auto_awesome" aria-hidden="true" /> Review duplicates
      </RouterLink>
      <button class="usx-btn" type="button" :disabled="indexing" @click="indexLibrary">Rebuild library index</button>
      <p v-if="indexMessage" :role="indexFailed ? 'alert' : 'status'">{{ indexMessage }}</p>
    </section>
    <section>
      <h3>Import a saved feed into a Binder</h3>
      <form @submit.prevent="importFeed">
        <label>Destination Binder
          <select v-model="binder" required>
            <option value="" disabled>Choose a Binder</option>
            <option v-for="item in wf.binders" :key="item.id" :value="item.id">{{ item.title || item.name || item.id }}</option>
          </select>
        </label>
        <label>Feed source <input v-model.trim="feedSource" required placeholder="Source name or URL" /></label>
        <label>RSS, Atom or JSON Feed <textarea v-model="content" rows="4" required /></label>
        <button class="usx-btn" type="submit" :disabled="importing || !binder || !feedSource || !content.trim()">Import feed</button>
        <p v-if="feedMessage" :role="feedFailed ? 'alert' : 'status'">{{ feedMessage }}</p>
      </form>
    </section>
    <section>
      <h3>Package and publish feeds</h3>
      <p>Run from uCorePub with a reviewed edition manifest.</p>
      <pre>python3 -m udos_publishing.src.edition_feed --manifest reviewed.json --edition-root edition --package output</pre>
      <p>The package includes RSS, Atom and JSON Feed files. Open the Binder to review and publish an edition.</p>
      <RouterLink class="usx-btn" :to="{ path: '/workflow', query: { tab: 'binder', binder: binder || undefined } }">Open Binders</RouterLink>
    </section>
    <section>
      <h3>Spool activity</h3>
      <button class="usx-btn" type="button" :disabled="loadingSpool" @click="readSpool">Read spool summary</button>
      <a class="usx-btn" :href="`${UCORE_BASE}/api/spool/feed`" target="_blank" rel="noopener">Open spool feed</a>
      <pre v-if="spoolSummary" :role="spoolFailed ? 'alert' : 'status'">{{ spoolSummary }}</pre>
    </section>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { UCORE_BASE } from "../../../api/base";
import { ucoreApi } from "../../../api/client";
import UIcon from "../../../skills/atoms/UIcon.vue";
import { useWorkflowStore } from "../../../stores/workflow";

const wf = useWorkflowStore();
const binder = ref(wf.activeBinderId);
const feedSource = ref("");
const content = ref("");
const importing = ref(false);
const feedMessage = ref("");
const feedFailed = ref(false);
const indexing = ref(false);
const indexMessage = ref("");
const indexFailed = ref(false);
const loadingSpool = ref(false);
const spoolSummary = ref("");
const spoolFailed = ref(false);

function assistant(purpose: string, goal: string) {
  return { path: "/workflow", query: { tab: "ai", purpose, goal } };
}

async function indexLibrary() {
  indexing.value = true;
  indexMessage.value = "";
  indexFailed.value = false;
  try {
    const response = await ucoreApi.library.build();
    if (!response.ok) throw new Error("Could not rebuild the library index.");
    indexMessage.value = "Library index rebuilt.";
  } catch {
    indexFailed.value = true;
    indexMessage.value = "Could not rebuild the library index.";
  } finally {
    indexing.value = false;
  }
}

async function importFeed() {
  if (importing.value) return;
  importing.value = true;
  feedFailed.value = false;
  feedMessage.value = "";
  try {
    const response = await ucoreApi.userWorkflow.importMarkdown({
      content: content.value, source_format: "feed", feed_source: feedSource.value,
      binder: binder.value, vault_layer: "user",
    });
    const result = response.data as { items?: { duplicate?: boolean; http_status: number }[]; error?: string };
    const accepted = (result.items || []).filter(item => item.http_status < 400);
    const duplicates = accepted.filter(item => item.duplicate).length;
    const summary = `${accepted.length - duplicates} saved, ${duplicates} already present.`;
    feedFailed.value = !response.ok;
    feedMessage.value = response.ok ? summary : `${result.error || "Feed import stopped."} ${summary}`;
  } catch {
    feedFailed.value = true;
    feedMessage.value = "Could not import the feed. You can retry with the same source.";
  } finally {
    importing.value = false;
  }
}

async function readSpool() {
  loadingSpool.value = true;
  spoolFailed.value = false;
  try {
    const response = await fetch(`${UCORE_BASE}/api/spool/summary`);
    if (!response.ok) throw new Error();
    spoolSummary.value = (await response.json()).summary || "No recent spool activity.";
  } catch {
    spoolFailed.value = true;
    spoolSummary.value = "Spool activity is unavailable.";
  } finally {
    loadingSpool.value = false;
  }
}
</script>

<style scoped>
.workflow-skills { display: grid; gap: 12px; }
.workflow-skills > section { padding: 12px; border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-md); }
.workflow-skills form, .workflow-skills label { display: grid; gap: 6px; }
.workflow-skills :is(select, input, textarea) { width: 100%; min-width: 0; }
.workflow-skills pre { white-space: pre-wrap; overflow-wrap: anywhere; }
</style>
