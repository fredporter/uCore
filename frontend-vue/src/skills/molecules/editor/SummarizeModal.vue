<template>
  <Teleport to="body">
    <div class="summarize-overlay" @click.self="emit('close')">
      <div class="summarize-modal">
        <div class="summarize-modal__header">
          <UIcon name="summarize" />
          <span>Summarize</span>
          <button class="summarize-modal__close" @click="emit('close')">
            <UIcon name="close" />
          </button>
        </div>

        <div class="summarize-modal__body">
          <!-- Style selector -->
          <div class="summarize-modal__style-row">
            <label>Style</label>
            <div class="summarize-modal__style-btns">
              <button
                v-for="s in styles"
                :key="s.value"
                class="summarize-modal__style-btn"
                :class="{
                  'summarize-modal__style-btn--active': style === s.value,
                }"
                @click="style = s.value"
              >
                {{ s.label }}
              </button>
            </div>
          </div>

          <!-- Input text (pre-filled from content, editable) -->
          <textarea
            v-model="inputText"
            class="summarize-modal__textarea"
            placeholder="Paste or type text to summarize…"
            rows="6"
          />

          <!-- Result -->
          <div v-if="result" class="summarize-modal__result">
            <div class="summarize-modal__result-label">
              <UIcon name="auto_awesome" />
              Summary
              <span v-if="fallback" class="summarize-modal__fallback-tag"
                >fallback</span
              >
            </div>
            <div class="summarize-modal__result-text">{{ result }}</div>
          </div>

          <div v-if="error" class="summarize-modal__error">{{ error }}</div>
        </div>

        <div class="summarize-modal__footer">
          <button
            class="summarize-modal__btn"
            :disabled="loading || !inputText.trim()"
            @click="runSummarize"
          >
            <UIcon :name="loading ? 'sync' : 'auto_awesome'" />
            {{ loading ? "Summarizing…" : "Summarize" }}
          </button>
          <button
            v-if="result"
            class="summarize-modal__btn summarize-modal__btn--primary"
            @click="emit('insert', result)"
          >
            <UIcon name="add_comment" /> Insert into Document
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import UIcon from "../../atoms/UIcon.vue";
import { parseDocument } from "../../../utils/frontmatterParser";
import { SNACKBAR_BASE } from "../../../api/base";

const props = defineProps<{ content: string }>();
const emit = defineEmits<{ insert: [summary: string]; close: [] }>();

// Pre-fill with body text (strip frontmatter)
const { body } = parseDocument(props.content);
const inputText = ref(body.slice(0, 2000));
const style = ref<"bullets" | "paragraph">("bullets");
const result = ref("");
const fallback = ref(false);
const error = ref("");
const loading = ref(false);

const styles = [
  { value: "bullets", label: "Bullet points" },
  { value: "paragraph", label: "Paragraph" },
] as const;

async function runSummarize() {
  if (!inputText.value.trim()) return;
  loading.value = true;
  error.value = "";
  result.value = "";
  fallback.value = false;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/editor/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: inputText.value, style: style.value }),
      signal: AbortSignal.timeout(20000),
    });
    const data = await res.json();
    if (data.summary) {
      result.value = data.summary;
      fallback.value = data.fallback === true;
    } else {
      error.value = data.error ?? "No summary returned";
    }
  } catch {
    error.value = "Backend unavailable. Try again later.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.summarize-overlay {
  position: fixed;
  inset: 0;
  z-index: 2100;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-lg);
}

.summarize-modal {
  background-color: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.25);
  width: 100%;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.summarize-modal__header {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-bottom: 1px solid var(--usx-color-border);
  background-color: var(--usx-color-surface-variant);
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface);
}

.summarize-modal__close {
  margin-left: auto;
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

.summarize-modal__body {
  padding: var(--usx-spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.summarize-modal__style-row {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
}

.summarize-modal__style-row label {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
  flex-shrink: 0;
}

.summarize-modal__style-btns {
  display: flex;
  gap: var(--usx-spacing-xs);
}

.summarize-modal__style-btn {
  padding: 3px var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-full);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
  cursor: pointer;
  transition: all 120ms ease;
}

.summarize-modal__style-btn--active {
  background-color: color-mix(
    in srgb,
    var(--usx-color-primary) 15%,
    transparent
  );
  border-color: var(--usx-color-primary);
  color: var(--usx-color-primary);
}

.summarize-modal__textarea {
  width: 100%;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background-color: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  resize: vertical;
  line-height: 1.5;
  min-height: 120px;
}

.summarize-modal__result {
  padding: var(--usx-spacing-md);
  background-color: color-mix(
    in srgb,
    var(--usx-color-success) 8%,
    transparent
  );
  border: 1px solid
    color-mix(in srgb, var(--usx-color-success) 25%, transparent);
  border-radius: var(--usx-radius-md);
}

.summarize-modal__result-label {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-success);
  margin-bottom: var(--usx-spacing-xs);
}

.summarize-modal__fallback-tag {
  font-weight: var(--usx-font-weight-regular);
  opacity: 0.7;
  font-style: italic;
}

.summarize-modal__result-text {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface);
  line-height: 1.6;
  white-space: pre-wrap;
}

.summarize-modal__error {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-danger);
}

.summarize-modal__footer {
  display: flex;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md) var(--usx-spacing-lg);
  border-top: 1px solid var(--usx-color-border);
}

.summarize-modal__btn {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-sm) var(--usx-spacing-lg);
  border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  background: transparent;
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  font-family: var(--usx-font-family-sans);
  cursor: pointer;
  transition: all 150ms ease;
}

.summarize-modal__btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.summarize-modal__btn--primary {
  background-color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  color: white;
  flex: 1;
}

.summarize-modal__btn--primary:hover {
  background-color: var(--usx-color-primary-hover);
}
</style>
