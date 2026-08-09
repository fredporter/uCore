<template>
  <Teleport to="body">
    <div v-if="visible" class="scraper-overlay" @click.self="emit('cancel')">
      <div class="scraper-modal" role="dialog" aria-modal="true">
        <!-- Header -->
        <div class="scraper-modal__header">
          <div class="scraper-modal__title">
            <UIcon name="language" />
            <span>Open in Markdown Editor</span>
          </div>
          <button class="scraper-modal__close" @click="emit('cancel')">
            <UIcon name="close" />
          </button>
        </div>

        <!-- Card preview -->
        <div class="scraper-modal__preview">
          <div class="scraper-modal__site">
            <UIcon name="public" />
            <span>{{ siteLabel }}</span>
          </div>
          <div class="scraper-modal__card-title">{{ card.title }}</div>
          <div v-if="card.description" class="scraper-modal__card-desc">
            {{ card.description }}
          </div>
          <div v-if="card.tags?.length" class="scraper-modal__tags">
            <span
              v-for="tag in card.tags"
              :key="tag"
              class="scraper-modal__tag"
            >
              {{ tag }}
            </span>
          </div>
          <a
            :href="card.url"
            target="_blank"
            rel="noopener"
            class="scraper-modal__url"
          >
            <UIcon name="open_in_new" />
            {{ card.url }}
          </a>
        </div>

        <!-- Loading state -->
        <div v-if="loading" class="scraper-modal__loading">
          <UIcon name="sync" />
          <span>Creating research document…</span>
        </div>

        <!-- Actions -->
        <div v-else class="scraper-modal__actions">
          <button
            class="scraper-modal__btn scraper-modal__btn--primary"
            @click="openInMarkdown"
          >
            <UIcon name="edit_note" />
            Open in Markdown Editor
          </button>
          <button class="scraper-modal__btn" @click="emit('cancel')">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import UIcon from "../../atoms/UIcon.vue";
import { useWorkspaceStore } from "../../../stores/workspace";
import { buildResearchDocument, fetchScrape } from "../../../utils/webScraper";

interface CardData {
  title: string;
  description: string;
  url: string;
  tags?: string[];
}

const props = defineProps<{ card: CardData; visible: boolean }>();
const emit = defineEmits<{ cancel: []; opened: [] }>();

const router = useRouter();
const ws = useWorkspaceStore();
const loading = ref(false);

const siteLabel = computed(() => {
  try {
    return new URL(props.card.url).hostname.replace(/^www\./, "");
  } catch {
    return props.card.url;
  }
});

async function openInMarkdown() {
  loading.value = true;
  try {
    // Try backend scraper; fall back to card metadata gracefully
    const scraped = await fetchScrape(props.card.url);
    const { filename, content } = buildResearchDocument(props.card, scraped);

    // Create file in workspace and auto-select it (opens in editor)
    ws.createFile("/research", filename);
    // Patch content into the newly created node
    const node = ws.tree
      .flatMap(
        (n: import("../../../stores/workspace").FileNode) => n.children ?? [],
      )
      .find(
        (n: import("../../../stores/workspace").FileNode) =>
          n.name === filename,
      );
    if (node) ws.updateFileContent(node.id, content);

    emit("opened");
    // Navigate to workflow editor tab
    await router.push({ path: "/workflow", query: { tab: "editor" } });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.scraper-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-lg);
}

.scraper-modal {
  background-color: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.25);
  width: 100%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ─── Header ──────────────────────────────────────────────────── */

.scraper-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface-variant);
}

.scraper-modal__title {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.scraper-modal__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--usx-radius-sm);
  color: var(--usx-color-on-surface-muted);
}

.scraper-modal__close:hover {
  background-color: var(--usx-color-border);
  color: var(--usx-color-on-surface);
}

/* ─── Preview ─────────────────────────────────────────────────── */

.scraper-modal__preview {
  padding: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
}

.scraper-modal__site {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
}

.scraper-modal__card-title {
  font-size: var(--usx-font-size-lg);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
  line-height: 1.3;
}

.scraper-modal__card-desc {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  line-height: 1.5;
}

.scraper-modal__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}

.scraper-modal__tag {
  padding: 2px var(--usx-spacing-sm);
  border-radius: var(--usx-radius-full);
  background-color: color-mix(in srgb, var(--usx-color-info) 12%, transparent);
  color: var(--usx-color-info);
  font-size: var(--usx-font-size-xs);
}

.scraper-modal__url {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-primary);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scraper-modal__url:hover {
  text-decoration: underline;
}

/* ─── Loading ─────────────────────────────────────────────────── */

.scraper-modal__loading {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  border-top: 1px solid var(--usx-color-border);
}

/* ─── Actions ─────────────────────────────────────────────────── */

.scraper-modal__actions {
  display: flex;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-top: 1px solid var(--usx-color-border);
}

.scraper-modal__btn {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background-color: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 150ms ease;
}

.scraper-modal__btn:hover {
  background-color: var(--usx-color-border);
}

.scraper-modal__btn--primary {
  background-color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  color: white;
  flex: 1;
}

.scraper-modal__btn--primary:hover {
  background-color: var(--usx-color-primary-hover);
}
</style>
