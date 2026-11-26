<script setup lang="ts">
import { ref, computed } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import type { AuthoringWorkbenchRecipe, CitationSourceItem } from '../recipes'
import { citationGenerator, type CitationFormat } from '../../utils/citationGenerator'

const props = defineProps<{
  recipe: AuthoringWorkbenchRecipe
}>()

// Active Citation Format in Provenance Sidebar
const activeFormat = ref<CitationFormat>(props.recipe.activeCitationFormat || 'uKnowledge')

// Editor View Mode: 'preview' (rendered USX prose) vs 'source' (raw markdown)
const editorMode = ref<'preview' | 'source'>('preview')

// Interactive Document Content State (editable if user types in source mode)
const documentContent = ref<string>(props.recipe.document.content)

// Selected citations for combination
const selectedCitationIds = ref<string[]>(props.recipe.citations.map((c) => c.id))

// Copy / Action Feedback
const copiedMessage = ref<string | null>(null)
let copyTimer: number | null = null

function showNotification(msg: string) {
  copiedMessage.value = msg
  if (copyTimer) window.clearTimeout(copyTimer)
  copyTimer = window.setTimeout(() => {
    copiedMessage.value = null
  }, 2500)
}

function getCitationString(source: CitationSourceItem, format: CitationFormat): string {
  return citationGenerator(
    {
      url: source.url || 'local-file',
      title: source.title,
      author: source.author,
      site: source.siteName,
      published: source.publicationDate,
      accessed: source.accessDate,
    },
    format
  )
}

function copyCitation(source: CitationSourceItem) {
  const text = getCitationString(source, activeFormat.value)
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
  }
  showNotification(`Copied ${activeFormat.value} citation for "${source.title.slice(0, 30)}..."`)
}

function insertCitationToDocument(source: CitationSourceItem) {
  const citationText = getCitationString(source, activeFormat.value)
  documentContent.value += `\n\n${citationText}`
  showNotification(`Inserted ${activeFormat.value} citation into document!`)
}

function toggleCitationSelection(id: string) {
  if (selectedCitationIds.value.includes(id)) {
    selectedCitationIds.value = selectedCitationIds.value.filter((item) => item !== id)
  } else {
    selectedCitationIds.value.push(id)
  }
}

// Synthesize research from selected citations
const combinedSynthesisPreview = computed(() => {
  const chosen = props.recipe.citations.filter((c) => selectedCitationIds.value.includes(c.id))
  if (chosen.length === 0) return 'Select at least one source to generate synthesis.'

  const titles = chosen.map((c) => `* **${c.title}** (${c.author || c.siteName || 'Source'})`).join('\n')
  const citations = chosen.map((c) => getCitationString(c, activeFormat.value)).join('\n\n')

  return `### Multi-Source Synthesis Brief\n\nThis synthesis reconciles ${chosen.length} verified provenance nodes:\n\n${titles}\n\n#### Provenance Citations\n\n${citations}`
})

function insertSynthesis() {
  documentContent.value += `\n\n${combinedSynthesisPreview.value}`
  showNotification('Appended multi-source synthesis brief to document!')
}

// Icon helper for provenance types
function getProvenanceIcon(type: CitationSourceItem['provenanceType']): string {
  switch (type) {
    case 'paper':
      return 'menu_book'
    case 'local_file':
      return 'description'
    case 'git_commit':
      return 'commit'
    case 'web':
    default:
      return 'public'
  }
}
</script>

<template>
  <div class="authoring-recipe-wrapper">
    <!-- Notification Toast -->
    <transition name="fade">
      <div v-if="copiedMessage" class="workbench-toast">
        <UIcon name="check_circle" class="toast-icon" />
        <span>{{ copiedMessage }}</span>
      </div>
    </transition>

    <!-- Enhanced Bangle Authoring Toolbar -->
    <div class="authoring-toolbar">
      <div class="toolbar-section format-group">
        <button type="button" class="usx-btn tb-btn" title="Bold" @click="showNotification('Format: Bold applied')">
          <UIcon name="format_bold" />
        </button>
        <button type="button" class="usx-btn tb-btn" title="Italic" @click="showNotification('Format: Italic applied')">
          <UIcon name="format_italic" />
        </button>
        <button type="button" class="usx-btn tb-btn" title="Code snippet" @click="showNotification('Format: Code block inserted')">
          <UIcon name="code" />
        </button>
        <button type="button" class="usx-btn tb-btn" title="Heading 1" @click="showNotification('Heading 1 toggled')">
          <UIcon name="format_h1" />
        </button>
        <button type="button" class="usx-btn tb-btn" title="Heading 2" @click="showNotification('Heading 2 toggled')">
          <UIcon name="format_h2" />
        </button>
        <button type="button" class="usx-btn tb-btn" title="Bullet List" @click="showNotification('Bullet list toggled')">
          <UIcon name="format_list_bulleted" />
        </button>
        <button type="button" class="usx-btn tb-btn" title="Blockquote" @click="showNotification('Blockquote toggled')">
          <UIcon name="format_quote" />
        </button>
      </div>

      <div class="toolbar-divider"></div>

      <!-- Research & Citation Tools (Sprint 4C) -->
      <div class="toolbar-section research-group">
        <button
          type="button" class="usx-btn tb-btn tb-accent"
          title="Insert Citation"
          @click="showNotification('Citation provenance palette ready in sidebar')"
        >
          <UIcon name="bookmark_add" />
          <span class="tb-label">Cite</span>
        </button>
        <button
          type="button" class="usx-btn tb-btn tb-accent"
          title="Combine Research Sources"
          @click="showNotification('Research Synthesis drawer opened')"
        >
          <UIcon name="join_inner" />
          <span class="tb-label">Combine Research</span>
        </button>
      </div>

      <!-- Mode Switcher -->
      <div class="view-mode-toggle" role="group" aria-label="Document view">
        <button
          type="button" class="usx-btn mode-btn"
          aria-label="Rendered" title="Rendered"
          :aria-pressed="editorMode === 'preview'"
          @click="editorMode = 'preview'"
        >
          <UIcon name="preview" />
        </button>
        <button
          type="button" class="usx-btn mode-btn"
          aria-label="Markdown Source" title="Markdown Source"
          :aria-pressed="editorMode === 'source'"
          @click="editorMode = 'source'"
        >
          <UIcon name="edit_note" />
        </button>
      </div>
    </div>

    <!-- Frontmatter Metadata Bar -->
    <div class="authoring-frontmatter">
      <span
        v-for="(val, key) in recipe.document.frontmatter"
        :key="key"
        class="usx-frontmatter-chip"
      >
        <span>{{ key }}:</span>
        <strong>{{ val }}</strong>
      </span>
    </div>

    <!-- Two-Column Authoring Stage -->
    <div class="authoring-layout">
      <!-- Main Document Editor / Viewer -->
      <section class="document-pane">
        <!-- Rendered USX Prose View -->
        <div v-if="editorMode === 'preview'" class="prose-content usx-prose">
          <!-- Static Rendered Sample Document -->
          <h1>{{ recipe.document.title }}</h1>
          <p>
            Modern autonomous agent runtimes require deterministic execution boundaries,
            reproducible artifact trees, and strict isolation between zero-cost local inference and
            metered frontier APIs<sup class="footnote-ref">[1]</sup>.
          </p>

          <!-- uKnowledge Citation Callout -->
          <div class="usx-callout usx-callout-note citation-callout">
            <div class="usx-callout-header">
              <UIcon name="bookmark" />
              <span>Citation: Local-First Software: You own your data, in spite of the cloud</span>
            </div>
            <div class="callout-provenance-meta">
              <span><strong>Provenance:</strong> <a href="https://www.inkandswitch.com/local-first/" target="_blank" rel="noopener">Ink & Switch</a></span>
              <span class="sep">•</span>
              <span><strong>Authors:</strong> Martin Kleppmann, Adam Wiggins, Peter van Hardenberg, Mark McGranaghan</span>
              <span class="sep">•</span>
              <span><strong>Published:</strong> April 1, 2019</span>
            </div>
          </div>

          <h2>1. Storage</h2>
          <p>
            Application state lives in <code>UDOS_HOME</code>.
            Your documents stay in your vault.
          </p>

          <h3>Verification and Citation Provenance</h3>
          <p>
            Every knowledge synthesis operation tracks original provenance. Combining research
            fragments produces auditable attribution graphs without cloud leakage<sup class="footnote-ref">[2]</sup>.
          </p>

          <!-- Footnotes Section -->
          <div class="document-footnotes">
            <hr />
            <h4>Attribution & Footnotes</h4>
            <ol>
              <li id="fn1">
                <a href="https://www.inkandswitch.com/local-first/" target="_blank" rel="noopener">
                  Local-First Software: You own your data, in spite of the cloud
                </a>
                by Martin Kleppmann et al. — Ink & Switch, accessed 2026-09-09.
              </li>
              <li id="fn2">
                <a href="https://ar.al/2020/08/07/the-small-web/" target="_blank" rel="noopener">
                  The Small Web Manifesto
                </a>
                by Aral Balkan — ar.al, accessed 2026-09-09.
              </li>
            </ol>
          </div>
        </div>

        <!-- Raw Markdown Source Mode -->
        <div v-else class="source-content">
          <textarea
            v-model="documentContent"
            class="markdown-textarea"
            rows="22"
            spellcheck="false"
          ></textarea>
        </div>
      </section>

      <!-- Right Sidebar: uKnowledge Citation Provenance & Synthesis Graph -->
      <aside class="provenance-pane">
        <div class="provenance-header">
          <div class="provenance-title-row">
            <UIcon name="history_edu" class="provenance-icon" />
            <h3>uKnowledge Provenance</h3>
          </div>
          <span class="provenance-badge">{{ recipe.citations.length }} Sources</span>
        </div>

        <p class="provenance-description">
          All citations originate from local documents or verified web snapshots.
          Select citation format to format attribution strings:
        </p>

        <!-- Format Selector Tabs -->
        <div class="format-pill-selector">
          <button
            v-for="fmt in (['uKnowledge', 'Markdown', 'APA', 'MLA', 'Chicago'] as CitationFormat[])"
            :key="fmt"
            class="format-pill-btn"
            :aria-pressed="activeFormat === fmt"
            @click="activeFormat = fmt"
          >
            {{ fmt }}
          </button>
        </div>

        <!-- Citation Cards List -->
        <div class="citation-cards-list">
          <div
            v-for="item in recipe.citations"
            :key="item.id"
            class="citation-card"
            :class="{ selected: selectedCitationIds.includes(item.id) }"
          >
            <div class="card-top-row">
              <div class="type-indicator">
                <span class="material-symbols-outlined type-icon">
                  {{ getProvenanceIcon(item.provenanceType) }}
                </span>
                <span class="type-name">{{ item.provenanceType }}</span>
              </div>
              <label class="combine-checkbox" title="Select for research synthesis">
                <input
                  type="checkbox"
                  :checked="selectedCitationIds.includes(item.id)"
                  @change="toggleCitationSelection(item.id)"
                />
                <span>Combine</span>
              </label>
            </div>

            <h4 class="citation-title">{{ item.title }}</h4>
            <div class="citation-authors" v-if="item.author">
              <UIcon name="person" class="meta-icon" />
              <span>{{ item.author }}</span>
            </div>
            <div class="citation-url" v-if="item.url">
              <UIcon name="link" class="meta-icon" />
              <a :href="item.url" target="_blank" rel="noopener">{{ item.siteName || item.url }}</a>
            </div>

            <p class="citation-note" v-if="item.note">{{ item.note }}</p>

            <!-- Live Formatted Citation String -->
            <div class="formatted-output-box">
              <div class="output-label">
                <span>Output ({{ activeFormat }}):</span>
                <button type="button" class="usx-btn icon-action-btn" @click="copyCitation(item)" title="Copy to clipboard">
                  <UIcon name="content_copy" />
                </button>
              </div>
              <pre class="citation-text"><code>{{ getCitationString(item, activeFormat) }}</code></pre>
            </div>

            <!-- Card Actions -->
            <div class="citation-card-actions">
              <button type="button" class="usx-btn card-btn" @click="copyCitation(item)">
                <UIcon name="content_copy" />
                <span>Copy</span>
              </button>
              <button type="button" class="usx-btn card-btn card-btn-primary" @click="insertCitationToDocument(item)">
                <UIcon name="add_comment" />
                <span>Insert in Document</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Multi-Source Synthesis Section (Sprint 4C Combine Research) -->
        <div class="synthesis-box">
          <div class="synthesis-header">
            <UIcon name="join_inner" />
            <h4>Research Synthesis</h4>
          </div>
          <p class="synthesis-desc">
            Combine {{ selectedCitationIds.length }} selected sources into a structured synthesis brief:
          </p>
          <button
            type="button" class="usx-btn synthesis-action-btn"
            :disabled="selectedCitationIds.length === 0"
            @click="insertSynthesis"
          >
            <UIcon name="post_add" />
            <span>Append Synthesis Section</span>
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>

.authoring-recipe-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  container-type: inline-size;
}

/* Floating Notification Toast */
.workbench-toast {
  position: fixed;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-primary);
  border: 1px solid var(--usx-color-primary);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 500;
}
.toast-icon {
  font-size: 1.25rem;
  color: var(--usx-color-primary);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Frontmatter Bar */
.authoring-frontmatter {
  margin-block: var(--usx-spacing-sm);
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}
.usx-frontmatter-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  background: var(--usx-color-surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.78rem;
  color: var(--usx-color-on-surface-muted);
}
.usx-frontmatter-chip strong {
  color: var(--usx-color-primary);
}

/* Enhanced Bangle Toolbar */
.authoring-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}
.toolbar-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
}
.authoring-toolbar button {
  margin: 0;
}

.toolbar-divider {
  width: 1px;
  height: 22px;
  background: var(--usx-color-border);
  margin: 0 0.35rem;
}
.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.5rem;
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.82rem;
  transition: background 0.15s ease;
}
.tb-btn:hover {
  background: var(--usx-color-surface-hover);
}
.tb-btn .material-symbols-outlined {
  font-size: 1.15rem;
}
.tb-accent {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-primary);
  font-weight: 500;
  border: 1px solid var(--usx-color-border);
}
.tb-accent:hover {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-primary);
}
.tb-label {
  font-size: 0.78rem;
}

/* Mode Switcher */
.view-mode-toggle[role="group"] {
  display: inline-flex;
  flex: 0 0 auto;
  width: max-content;
  margin: 0;
  padding: 0;
  border: 0;
  box-shadow: none;
  gap: var(--usx-spacing-xs);
}
.usx-btn.mode-btn {
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  width: var(--usx-touch-min-sm);
  min-height: var(--usx-touch-min-sm);
  margin: 0;
  padding: 0;
  font-size: var(--usx-font-size-sm);
  border: var(--usx-border-width) solid transparent;
  border-radius: var(--usx-radius-sm);
  background: transparent;
  color: var(--usx-color-on-surface-muted);
}
.usx-btn.mode-btn[aria-pressed="true"] {
  color: var(--usx-color-primary);
}
.usx-btn.mode-btn:focus {
  box-shadow: none;
}
.usx-btn.mode-btn:focus-visible {
  outline: var(--usx-border-width-thick) solid var(--usx-color-primary);
  outline-offset: var(--usx-spacing-2);
}
.mode-btn .material-symbols-outlined {
  font-size: 1rem;
}

/* Workbench Two-Column Layout */
.authoring-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--usx-spacing-md);
  align-items: start;
}

@container (min-width: 960px) {
  .authoring-layout {
    grid-template-columns: minmax(0, 1fr) 340px;
  }
}

/* Document Pane */
.document-pane {
  min-width: 0;
  margin: 0;
  padding: 0;
}
.prose-content {
  width: 100%;
}
.source-content {
  width: 100%;
}
.markdown-textarea {
  width: 100%;
  min-height: 440px;
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.88rem;
  line-height: 1.6;
  border: 1px solid var(--usx-color-border);
  border-radius: 6px;
  padding: 1rem;
  resize: vertical;
}

/* Callout Provenance Meta */
.citation-callout {
  margin: 1.25rem 0;
}
.callout-provenance-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  color: var(--usx-color-on-surface-muted);
  margin-top: 0.35rem;
}
.callout-provenance-meta a {
  color: var(--usx-color-primary);
}
.sep {
  color: var(--usx-color-on-surface-muted);
}
.footnote-ref {
  font-size: 0.75rem;
  color: var(--usx-color-primary);
  font-weight: bold;
  cursor: pointer;
}
.document-footnotes {
  margin-top: 2rem;
  padding-top: 1rem;
  font-size: 0.85rem;
}
.document-footnotes hr {
  border: 0;
  height: 1px;
  background: var(--usx-color-border);
  margin-bottom: 1rem;
}
.document-footnotes h4 {
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}
.document-footnotes ol {
  padding-left: 1.25rem;
  color: var(--usx-color-on-surface-muted);
}
.document-footnotes li {
  margin-bottom: 0.35rem;
}

/* Right Provenance Sidebar */
.provenance-pane {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
  min-width: 0;
}
.provenance-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.provenance-title-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.provenance-icon {
  color: var(--usx-color-primary);
  font-size: 1.3rem;
}
.provenance-header h3 {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0;
  color: var(--usx-color-on-surface);
}
.provenance-badge {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface-muted);
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 9999px;
  font-weight: 500;
}
.provenance-description {
  font-size: 0.8rem;
  color: var(--usx-color-on-surface-muted);
  line-height: 1.4;
  margin: 0;
}

/* Format Pill Selector */
.format-pill-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.format-pill-btn {
  padding: 0.25rem 0.6rem;
  font-size: 0.78rem;
  border-radius: 9999px;
  border: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}
.format-pill-btn[aria-pressed="true"] {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
  font-weight: 600;
}

/* Citation Cards */
.citation-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.citation-card {
  background: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: 6px;
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  transition: border-color 0.15s ease;
}
.citation-card.selected {
  border-inline-start-color: var(--usx-color-primary);
}
.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.type-indicator {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  text-transform: uppercase;
  color: var(--usx-color-on-surface-muted);
  font-weight: 600;
}
.type-icon {
  font-size: 0.95rem;
}
.combine-checkbox {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
}
.citation-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
  color: var(--usx-color-on-surface);
}
.citation-authors,
.citation-url {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.78rem;
  color: var(--usx-color-on-surface-muted);
}
.meta-icon {
  font-size: 0.9rem;
  color: var(--usx-color-on-surface-muted);
}
.citation-url a {
  color: var(--usx-color-primary);
  text-decoration: underline;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.citation-note {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-muted);
  font-style: italic;
  margin: 0;
}

/* Formatted Output Box */
.formatted-output-box {
  margin-top: 0.25rem;
  background: var(--usx-color-surface-hover);
  border: 1px solid var(--usx-color-border);
  border-radius: 4px;
  padding: 0.45rem 0.6rem;
}
.output-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.72rem;
  color: var(--usx-color-on-surface-muted);
  margin-bottom: 0.25rem;
}
.icon-action-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--usx-color-on-surface-muted);
  padding: 0;
  display: flex;
}
.icon-action-btn .material-symbols-outlined {
  font-size: 0.9rem;
}
.citation-text,
.citation-text code {
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
}

.citation-text {
  margin: 0;
  font-size: 0.75rem;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--usx-color-on-surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

/* Card Actions */
.citation-card-actions {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.35rem;
}
.card-btn {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.3rem 0.5rem;
  font-size: 0.75rem;
  border-radius: 4px;
  border: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-on-surface);
  cursor: pointer;
}
.card-btn .material-symbols-outlined {
  font-size: 0.85rem;
}
.card-btn-primary {
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-primary);
  border-color: var(--usx-color-primary);
}

/* Synthesis Box */
.synthesis-box {
  background: var(--usx-color-surface);
  border: 1px solid var(--usx-color-border);
  border-radius: 6px;
  padding: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.synthesis-header {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--usx-color-primary);
}
.synthesis-header h4 {
  margin: 0;
  font-size: 0.88rem;
}
.synthesis-desc {
  font-size: 0.75rem;
  color: var(--usx-color-on-surface-muted);
  margin: 0;
}
.synthesis-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.45rem 0.75rem;
  border-radius: 4px;
  border: none;
  background: var(--usx-color-surface-hover);
  color: var(--usx-color-primary);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}
.synthesis-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
