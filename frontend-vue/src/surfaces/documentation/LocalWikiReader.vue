<template>
  <div class="local-wiki-reader" :class="{ 'local-wiki-reader--zen': zenMode, [`font-${fontFamily}`]: true }">
    <!-- Top Reader Header / Toolbar -->
    <header class="wiki-toolbar">
      <div class="wiki-toolbar__left">
        <button
          type="button"
          class="wiki-btn wiki-btn--icon"
          :title="zenMode ? 'Exit Zen Mode' : 'Enter Zen Focus Mode'"
          @click="zenMode = !zenMode"
        >
          <UIcon :name="zenMode ? 'fullscreen_exit' : 'fit_screen'" />
          <span class="wiki-btn__text">{{ zenMode ? 'Exit Zen' : 'Zen Focus' }}</span>
        </button>

        <div class="wiki-font-toggle">
          <button
            type="button"
            class="wiki-btn wiki-btn--toggle"
            :class="{ 'wiki-btn--active': fontFamily === 'serif' }"
            @click="fontFamily = 'serif'"
            title="Serif Reader (Charter / Georgia)"
          >
            Serif
          </button>
          <button
            type="button"
            class="wiki-btn wiki-btn--toggle"
            :class="{ 'wiki-btn--active': fontFamily === 'sans' }"
            @click="fontFamily = 'sans'"
            title="Clean Sans (Inter / System)"
          >
            Sans
          </button>
        </div>
      </div>

      <div class="wiki-toolbar__center">
        <div v-if="activeTitle" class="wiki-meta">
          <span class="wiki-meta__title">{{ activeTitle }}</span>
          <span v-if="estimatedMinutes" class="wiki-meta__reading-time">
            <UIcon name="schedule" size="xs" /> {{ estimatedMinutes }} min read ({{ wordCount }} words)
          </span>
        </div>
      </div>

      <div class="wiki-toolbar__right">
        <button
          type="button"
          class="wiki-search-trigger"
          title="Search Local Wikipedia (⌘K)"
          @click="openSearchModal"
        >
          <UIcon name="search" size="xs" />
          <span class="wiki-search-trigger__text">Search Wikipedia…</span>
          <kbd class="wiki-kbd">⌘K</kbd>
        </button>

        <button
          type="button"
          class="wiki-btn wiki-btn--icon"
          title="Knowledge Federation (Layers & Submissions)"
          @click="openFederationOverviewModal"
        >
          <UIcon name="hub" />
          <span class="wiki-btn__text">Federation</span>
        </button>

        <button
          type="button"
          class="wiki-btn wiki-btn--icon"
          title="Refresh Vaults Tree"
          :disabled="loadingTree"
          @click="loadTree"
        >
          <UIcon :name="loadingTree ? 'sync' : 'refresh'" />
        </button>
      </div>
    </header>

    <div class="wiki-body">
      <!-- Left Sidebar: Multi-Vault Explorer -->
      <aside v-show="!zenMode" class="wiki-sidebar">
        <div class="wiki-sidebar__header">
          <span class="wiki-sidebar__title">Local Vaults & Manuals</span>
          <span class="wiki-badge wiki-badge--offline">Offline Wikipedia</span>
        </div>

        <div class="wiki-tree-filter">
          <UIcon name="filter_list" size="xs" />
          <input
            v-model="filterQuery"
            type="text"
            placeholder="Filter tree..."
            class="wiki-tree-filter-input"
          />
          <button
            v-if="filterQuery"
            type="button"
            class="wiki-search-clear"
            @click="filterQuery = ''"
          >
            <UIcon name="close" size="xs" />
          </button>
        </div>

        <div v-if="loadingTree" class="wiki-loading">
          <UIcon name="sync" /> Loading multi-vault tree…
        </div>

        <div v-else-if="filteredVaults.length === 0" class="wiki-empty-tree">
          No articles match "{{ filterQuery }}".
        </div>

        <div v-else class="wiki-tree">
          <div v-for="vault in filteredVaults" :key="vault.id" class="wiki-vault-group">
            <div
              class="wiki-vault-header"
              @click="toggleGroup(vault.id)"
            >
              <UIcon :name="isGroupOpen(vault.id) ? 'expand_more' : 'chevron_right'" size="xs" />
              <span class="wiki-vault-name">{{ vault.name }}</span>
              <span class="wiki-vault-badge">{{ vault.badge }}</span>
            </div>

            <div v-if="isGroupOpen(vault.id)" class="wiki-vault-items">
              <template v-for="item in vault.items" :key="item.path">
                <WikiTreeItem
                  :item="item"
                  :active-source="activeSource"
                  :active-path="activePath"
                  @select="selectDocument"
                />
              </template>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Article Reader -->
      <main class="wiki-content">
        <div v-if="loadingContent" class="wiki-loading-content">
          <UIcon name="sync" /> Loading document…
        </div>

        <div v-else-if="!activePath" class="wiki-placeholder">
          <div class="wiki-placeholder__icon">
            <UIcon name="auto_stories" />
          </div>
          <h2>Welcome to the Sovereign Local Wikipedia</h2>
          <p>
            An offline-first, serene reading experience combining all local vaults
            (<code>~/Vault</code>, <code>~/Shared</code>, <code>~/Public</code>, and manuals).
          </p>
          <p class="wiki-placeholder__note">
            External links are safely rendered as static citation chips with zero outbound web tracking.
          </p>
          <div class="wiki-placeholder__actions">
            <button
              v-if="firstArticle"
              type="button"
              class="wiki-btn wiki-btn--primary"
              @click="selectDocument(firstArticle.source, firstArticle.path, firstArticle.title)"
            >
              <UIcon name="menu_book" /> Open {{ firstArticle.title }}
            </button>
          </div>
        </div>

        <article v-else class="wiki-article">
          <!-- Article Breadcrumb & Provenance Banner -->
          <div class="wiki-article__header">
            <div class="wiki-breadcrumb">
              <span class="wiki-breadcrumb__source">{{ sourceLabel(activeSource) }}</span>
              <span class="wiki-breadcrumb__sep">/</span>
              <span class="wiki-breadcrumb__path">{{ activePath }}</span>
            </div>
            <div class="wiki-article__tags">
              <span
                v-if="activeOverlay && activeOverlay.effective_layer !== null"
                class="wiki-chip"
                :class="layerChipClass(activeOverlay.effective_layer, activeOverlay.is_overlaid)"
                :title="activeOverlay.is_overlaid ? 'Overlaid with local edits' : 'Pristine base'"
              >
                <UIcon :name="layerIcon(activeOverlay.effective_layer)" size="xs" />
                {{ layerBadgeLabel(activeOverlay.effective_layer, activeOverlay.is_overlaid) }}
              </span>
              <span class="wiki-chip wiki-chip--offline">
                <UIcon name="cloud_off" size="xs" /> 100% Offline
              </span>
            </div>
          </div>

          <!-- Knowledge Federation Action Strip -->
          <div v-if="activeOverlay && activeOverlay.effective_layer !== null" class="wiki-federation-toolbar">
            <div class="wiki-fed-actions">
              <!-- Compare vs Canon (if diff available) -->
              <button
                v-if="activeOverlay.canon_exists && activeOverlay.has_diff"
                type="button"
                class="wiki-btn wiki-btn--xs wiki-btn--diff"
                title="View unified diff against canonical Layer 0"
                @click="openDiffModal"
              >
                <UIcon name="difference" size="xs" />
                <span>Compare vs Canon</span>
                <span class="wiki-fed-diff-stats">
                  +{{ activeOverlay.diff_stats?.additions || 0 }} -{{ activeOverlay.diff_stats?.deletions || 0 }}
                </span>
              </button>

              <!-- Toggle Canon baseline view -->
              <button
                v-if="activeOverlay.is_overlaid && activeOverlay.canon_exists"
                type="button"
                class="wiki-btn wiki-btn--xs"
                :class="{ 'wiki-btn--active': showingCanonOnly }"
                title="Toggle between personal overlay and canonical baseline"
                @click="toggleCanonOnly"
              >
                <UIcon :name="showingCanonOnly ? 'visibility_off' : 'visibility'" size="xs" />
                <span>{{ showingCanonOnly ? 'Showing Canon Baseline' : 'Show Canon Baseline' }}</span>
              </button>

              <!-- Revert to Canon (Layer 2) -->
              <button
                v-if="activeOverlay.effective_layer === 2 && activeOverlay.canon_exists"
                type="button"
                class="wiki-btn wiki-btn--xs wiki-btn--revert"
                :disabled="revertingOverlay"
                title="Revert personal overlay and restore pristine canonical baseline"
                @click="confirmRevertToCanon"
              >
                <UIcon name="undo" size="xs" />
                <span>{{ revertingOverlay ? 'Reverting...' : 'Revert to Canon' }}</span>
              </button>

              <!-- Customize in Vault (Layer 0 or 1) -->
              <button
                v-if="activeOverlay.effective_layer !== 2"
                type="button"
                class="wiki-btn wiki-btn--xs wiki-btn--fork"
                title="Fork into ~/Vault/knowledge for personal sovereign customization"
                :disabled="customizingOverlay"
                @click="customizeInVault"
              >
                <UIcon name="edit_note" size="xs" />
                <span>{{ customizingOverlay ? 'Forking...' : 'Customize in Vault' }}</span>
              </button>

              <!-- Export Submission Package (Layer 2) -->
              <button
                v-if="activeOverlay.effective_layer === 2"
                type="button"
                class="wiki-btn wiki-btn--xs wiki-btn--export"
                title="Bundle personal changes into cryptographic submission package"
                @click="openSubmissionModal"
              >
                <UIcon name="send" size="xs" />
                <span>Export Submission</span>
              </button>
            </div>

            <div class="wiki-fed-status-link">
              <button
                type="button"
                class="wiki-btn wiki-btn--xs wiki-btn--ghost"
                title="Open Federation Layer Overview"
                @click="openFederationOverviewModal"
              >
                <UIcon name="info" size="xs" />
                <span>Layer Info</span>
              </button>
            </div>
          </div>

          <!-- Auto-generated Table of Contents -->
          <div v-if="headings.length > 2" class="wiki-toc">
            <div class="wiki-toc__title">
              <UIcon name="list" size="xs" /> Table of Contents
            </div>
            <ul class="wiki-toc__list">
              <li
                v-for="h in headings"
                :key="h.id"
                class="wiki-toc__item"
                :class="`wiki-toc__item--l${h.level}`"
              >
                <a :href="`#${h.id}`" @click.prevent="scrollToHeading(h.id)">{{ h.text }}</a>
              </li>
            </ul>
          </div>

          <!-- Rendered HTML Document Body -->
          <div
            ref="wikiProseRef"
            class="wiki-prose prose-measure"
            v-html="renderedHtml"
            @click="handleProseClick"
          />
        </article>
      </main>
    </div>

    <!-- Offline Search Modal (Cmd+K) -->
    <div v-if="showSearchModal" class="wiki-modal-backdrop" @click.self="closeSearchModal">
      <div class="wiki-search-modal" role="dialog" aria-label="Search Local Wikipedia">
        <header class="wiki-search-modal__header">
          <UIcon name="search" class="wiki-search-modal__icon" />
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="Search all local vaults, manuals, and datasets..."
            class="wiki-search-modal__input"
            @keydown.down.prevent="navigateResults(1)"
            @keydown.up.prevent="navigateResults(-1)"
            @keydown.enter.prevent="selectCurrentResult"
            @keydown.esc="closeSearchModal"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="wiki-search-clear"
            @click="searchQuery = ''; searchResults = []"
          >
            <UIcon name="close" size="xs" />
          </button>
          <kbd class="wiki-kbd">ESC</kbd>
        </header>

        <!-- Zone filter pills -->
        <div class="wiki-search-modal__filters">
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'all' }"
            @click="setSearchZone('all')"
          >
            All Zones
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'personal' }"
            @click="setSearchZone('personal')"
          >
            Personal (~/Vault)
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'public' }"
            @click="setSearchZone('public')"
          >
            Public Canon (~/Public)
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'manuals' }"
            @click="setSearchZone('manuals')"
          >
            Curriculum & Manuals
          </button>
          <button
            type="button"
            class="wiki-filter-pill"
            :class="{ 'wiki-filter-pill--active': searchZone === 'shared' }"
            @click="setSearchZone('shared')"
          >
            Shared (~/Shared)
          </button>
        </div>

        <!-- Results list -->
        <div class="wiki-search-modal__results">
          <div v-if="searching" class="wiki-search-loading">
            <UIcon name="sync" /> Searching local FTS index...
          </div>
          <div v-else-if="searchQuery && searchResults.length === 0" class="wiki-search-empty">
            <UIcon name="search_off" :size="32" />
            <p>No matches found for "<strong>{{ searchQuery }}</strong>"</p>
            <span class="subtext">Search covers ~/Vault, ~/Shared, ~/Public, offline datasets, and manuals.</span>
          </div>
          <div v-else-if="!searchQuery" class="wiki-search-hint">
            <p>Type to search offline articles, canonical datasets (world parameters, coordinates), USX design tokens, and manuals.</p>
            <div class="wiki-search-quick-tags">
              <span class="subtext">Try searching:</span>
              <button type="button" class="quick-tag" @click="runQuickSearch('world parameters')">world parameters</button>
              <button type="button" class="quick-tag" @click="runQuickSearch('BBC BASIC')">BBC BASIC</button>
              <button type="button" class="quick-tag" @click="runQuickSearch('USX tokens')">USX tokens</button>
              <button type="button" class="quick-tag" @click="runQuickSearch('hardware revival')">hardware revival</button>
            </div>
          </div>
          <ul v-else class="wiki-results-list">
            <li
              v-for="(item, idx) in searchResults"
              :key="item.id || item.path"
              class="wiki-result-item"
              :class="{ 'wiki-result-item--selected': selectedResultIndex === idx }"
              @mouseenter="selectedResultIndex = idx"
              @click="chooseSearchResult(item)"
            >
              <div class="wiki-result-item__top">
                <span class="wiki-result-item__title" v-html="highlightSearchTerm(item.title, searchQuery)" />
                <span class="wiki-result-item__badge">{{ item.badge }}</span>
              </div>
              <p class="wiki-result-item__snippet" v-html="item.snippet" />
              <div class="wiki-result-item__meta">
                <span class="wiki-result-item__path">{{ item.rel_path }}</span>
                <span v-if="item.modified_at" class="wiki-result-item__date">
                  {{ new Date(item.modified_at).toLocaleDateString() }}
                </span>
              </div>
            </li>
          </ul>
        </div>

        <!-- Modal Footer -->
        <footer class="wiki-search-modal__footer">
          <div class="footer-left">
            <UIcon name="cloud_off" size="xs" />
            <span>100% Offline · SQLite FTS5 · Zero Telemetry</span>
          </div>
          <div class="footer-right">
            <span><kbd class="wiki-kbd-mini">↑</kbd><kbd class="wiki-kbd-mini">↓</kbd> Navigate</span>
            <span><kbd class="wiki-kbd-mini">↵</kbd> Open</span>
            <span><kbd class="wiki-kbd-mini">ESC</kbd> Close</span>
          </div>
        </footer>
      </div>
    </div>

    <!-- 1. Unified Diff vs Canon Modal -->
    <div v-if="showDiffModal && activeOverlay" class="wiki-modal-backdrop" @click.self="showDiffModal = false">
      <div class="wiki-fed-modal" role="dialog" aria-label="Compare vs Canon Diff">
        <header class="wiki-fed-modal__header">
          <div class="wiki-fed-modal__title-row">
            <UIcon name="difference" class="wiki-fed-modal__icon" />
            <h3 class="wiki-fed-modal__title">Diff vs Canon Baseline</h3>
            <span class="wiki-fed-diff-stats">
              +{{ activeOverlay.diff_stats?.additions || 0 }} -{{ activeOverlay.diff_stats?.deletions || 0 }}
            </span>
          </div>
          <button type="button" class="wiki-search-clear" @click="showDiffModal = false">
            <UIcon name="close" size="xs" />
          </button>
        </header>

        <div class="wiki-fed-modal__body">
          <div class="wiki-fed-diff-meta">
            <div><strong>Document:</strong> <code>{{ activeOverlay.rel_path }}</code></div>
            <div><strong>Baseline:</strong> Layer 0 Canon (<code>~/Public/global-knowledge</code>)</div>
            <div><strong>Active Layer:</strong> Layer {{ activeOverlay.effective_layer }} ({{ activeOverlay.effective_layer_name }})</div>
          </div>
          <div class="wiki-fed-diff-viewer">
            <div v-for="(line, idx) in formattedDiffLines" :key="idx" :class="['wiki-diff-line', line.type]">
              <span class="wiki-diff-line-num">{{ line.num }}</span>
              <span class="wiki-diff-line-content">{{ line.content }}</span>
            </div>
          </div>
        </div>

        <footer class="wiki-fed-modal__footer">
          <button type="button" class="wiki-btn wiki-btn--secondary" @click="showDiffModal = false">
            Close
          </button>
        </footer>
      </div>
    </div>

    <!-- 2. Export Contribution Submission Modal -->
    <div v-if="showSubmissionModal && activeOverlay" class="wiki-modal-backdrop" @click.self="showSubmissionModal = false">
      <div class="wiki-fed-modal" role="dialog" aria-label="Export Contribution Package">
        <header class="wiki-fed-modal__header">
          <div class="wiki-fed-modal__title-row">
            <UIcon name="send" class="wiki-fed-modal__icon" />
            <h3 class="wiki-fed-modal__title">Export Contribution Submission Bundle</h3>
          </div>
          <button type="button" class="wiki-search-clear" @click="showSubmissionModal = false">
            <UIcon name="close" size="xs" />
          </button>
        </header>

        <div class="wiki-fed-modal__body">
          <!-- Submission success -->
          <div v-if="submissionSuccess" class="wiki-submission-success">
            <div class="wiki-success-title">
              <UIcon name="check_circle" /> Submission Bundle Generated
            </div>
            <p>Cryptographic package saved plainly to disk (AGENTS.md compliant):</p>
            <code>{{ submissionSuccess.package_path }}</code>
            <div class="wiki-checksum-row">
              <span>SHA-256 Checksum:</span>
              <code>{{ submissionSuccess.diff_checksum }}</code>
            </div>
            <div class="wiki-submission-actions">
              <button type="button" class="wiki-btn wiki-btn--primary" @click="showSubmissionModal = false">
                Done
              </button>
            </div>
          </div>

          <div v-else class="wiki-submission-form">
            <p class="wiki-fed-modal__desc">
              Package your sovereign personal modifications into a signed bundle for community sharing or Wizard canon review.
            </p>

            <div class="wiki-form-group">
              <label>Target Article</label>
              <input type="text" :value="activeOverlay.rel_path" readonly class="wiki-input wiki-input--readonly" />
            </div>

            <div class="wiki-form-group">
              <label>Author / Pseudonym</label>
              <input v-model="submissionAuthor" type="text" placeholder="e.g. sovereign-explorer" class="wiki-input" />
            </div>

            <div class="wiki-form-group">
              <label>Contribution Notes / Research Justification</label>
              <textarea v-model="submissionNotes" rows="3" placeholder="Describe field-tested updates or citations..." class="wiki-textarea" />
            </div>

            <!-- Preflight checklist -->
            <div class="wiki-preflight-panel">
              <div class="wiki-preflight-title">
                <UIcon name="verified_user" size="xs" />
                <span>Automated AI Preflight Linter</span>
                <span v-if="preflightResult" :class="['wiki-status-tag', preflightResult.passed ? 'tag--pass' : 'tag--fail']">
                  {{ preflightResult.passed ? 'PASSED' : 'ACTION REQUIRED' }}
                </span>
              </div>

              <div v-if="!preflightResult" class="wiki-preflight-loading">
                <UIcon name="sync" /> Running privacy & standards checks...
              </div>

              <div v-else class="wiki-preflight-checks">
                <div class="wiki-check-item" :class="{ 'check--ok': preflightResult.checks?.privacy_clean, 'check--fail': !preflightResult.checks?.privacy_clean }">
                  <UIcon :name="preflightResult.checks?.privacy_clean ? 'check' : 'error'" size="xs" />
                  <span>Privacy Leak Scanner: Zero local home paths (/Users/...)</span>
                </div>
                <div class="wiki-check-item" :class="{ 'check--ok': preflightResult.checks?.credentials_clean, 'check--fail': !preflightResult.checks?.credentials_clean }">
                  <UIcon :name="preflightResult.checks?.credentials_clean ? 'check' : 'error'" size="xs" />
                  <span>Credential Scanner: Zero API keys or tokens</span>
                </div>
                <div class="wiki-check-item" :class="{ 'check--ok': preflightResult.checks?.prose_compliant, 'check--warn': !preflightResult.checks?.prose_compliant }">
                  <UIcon :name="preflightResult.checks?.prose_compliant ? 'check' : 'warning'" size="xs" />
                  <span>Prose Standards: Sentence-case typography</span>
                </div>
                <div class="wiki-check-item" :class="{ 'check--ok': preflightResult.checks?.assets_offline, 'check--warn': !preflightResult.checks?.assets_offline }">
                  <UIcon :name="preflightResult.checks?.assets_offline ? 'check' : 'warning'" size="xs" />
                  <span>Offline First: Relative & local asset paths</span>
                </div>

                <div v-if="preflightResult.errors && preflightResult.errors.length > 0" class="wiki-preflight-errors">
                  <div v-for="(err, i) in preflightResult.errors" :key="i" class="preflight-err-msg">
                    ✗ {{ err }}
                  </div>
                </div>
              </div>
            </div>

            <footer class="wiki-fed-modal__footer">
              <button type="button" class="wiki-btn wiki-btn--secondary" @click="showSubmissionModal = false">
                Cancel
              </button>
              <button
                type="button"
                class="wiki-btn wiki-btn--primary"
                :disabled="packagingSubmission || (preflightResult && !preflightResult.passed)"
                @click="submitPackage"
              >
                <UIcon :name="packagingSubmission ? 'sync' : 'send'" />
                <span>{{ packagingSubmission ? 'Packaging...' : 'Create Submission Bundle' }}</span>
              </button>
            </footer>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. Knowledge Federation Overview Modal -->
    <div v-if="showFederationModal" class="wiki-modal-backdrop" @click.self="showFederationModal = false">
      <div class="wiki-fed-modal wiki-fed-modal--wide" role="dialog" aria-label="Knowledge Federation Overview">
        <header class="wiki-fed-modal__header">
          <div class="wiki-fed-modal__title-row">
            <UIcon name="hub" class="wiki-fed-modal__icon" />
            <h3 class="wiki-fed-modal__title">Sovereign Knowledge Federation Architecture</h3>
          </div>
          <button type="button" class="wiki-search-clear" @click="showFederationModal = false">
            <UIcon name="close" size="xs" />
          </button>
        </header>

        <div class="wiki-fed-modal__body">
          <div class="wiki-fed-tier-grid">
            <div class="wiki-fed-tier-card tier--personal">
              <div class="tier-card__header">
                <span class="tier-badge">Layer 2</span>
                <h4>Sovereign Personal</h4>
              </div>
              <p class="tier-path"><code>~/Vault/knowledge/</code></p>
              <div class="tier-stat">
                <span class="stat-number">{{ fedSummary?.layers?.layer_2_personal?.articles_count || 0 }}</span>
                <span class="stat-label">articles</span>
              </div>
              <p class="tier-desc">User private notes, custom clips, sovereign overrides. Full precedence.</p>
            </div>

            <div class="wiki-fed-tier-card tier--community">
              <div class="tier-card__header">
                <span class="tier-badge">Layer 1</span>
                <h4>Community & Shared</h4>
              </div>
              <p class="tier-path"><code>~/Shared/knowledge/</code></p>
              <div class="tier-stat">
                <span class="stat-number">{{ fedSummary?.layers?.layer_1_shared?.articles_count || 0 }}</span>
                <span class="stat-label">articles</span>
              </div>
              <p class="tier-desc">Household vaults, shared team guides, peer datasets. Filter overlay.</p>
            </div>

            <div class="wiki-fed-tier-card tier--canon">
              <div class="tier-card__header">
                <span class="tier-badge">Layer 0</span>
                <h4>Base Canon</h4>
              </div>
              <p class="tier-path"><code>~/Public/global-knowledge/</code></p>
              <div class="tier-stat">
                <span class="stat-number">{{ fedSummary?.layers?.layer_0_canon?.articles_count || 0 }}</span>
                <span class="stat-label">articles</span>
              </div>
              <p class="tier-desc">Universal standards (USX, GridCore, Prose). Immutable baseline, curated by Wizard.</p>
            </div>
          </div>

          <!-- Active Overlays Section -->
          <div class="wiki-fed-section">
            <h4 class="wiki-fed-section-title">
              Active Overlays ({{ fedOverlays.length }})
            </h4>
            <div v-if="fedOverlays.length === 0" class="wiki-fed-empty">
              No active personal or shared overlays. All articles currently resolve to pristine Layer 0 canon.
            </div>
            <div v-else class="wiki-fed-table-wrapper">
              <table class="wiki-fed-table">
                <thead>
                  <tr>
                    <th>Article</th>
                    <th>Layer</th>
                    <th>Status</th>
                    <th>Diff</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in fedOverlays" :key="item.rel_path">
                    <td><code>{{ item.rel_path }}</code></td>
                    <td>
                      <span class="wiki-chip" :class="layerChipClass(item.layer, item.is_overlaid)">
                        {{ layerBadgeLabel(item.layer, item.is_overlaid) }}
                      </span>
                    </td>
                    <td>
                      <span v-if="item.canon_exists" class="wiki-tag--overlaid">Overlays Canon</span>
                      <span v-else class="wiki-tag--new">New Article</span>
                    </td>
                    <td>
                      <span v-if="item.has_diff" class="wiki-fed-diff-stats">
                        +{{ item.diff_stats?.additions || 0 }} -{{ item.diff_stats?.deletions || 0 }}
                      </span>
                      <span v-else class="wiki-muted-text">Identical</span>
                    </td>
                    <td>
                      <button
                        type="button"
                        class="wiki-btn wiki-btn--xs wiki-btn--ghost"
                        @click="selectDocument(item.layer === 2 ? 'vault' : 'shared', item.path, item.rel_path); showFederationModal = false"
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Submissions Section -->
          <div class="wiki-fed-section">
            <h4 class="wiki-fed-section-title">
              Exported Contribution Bundles ({{ fedSubmissions.length }})
            </h4>
            <div v-if="fedSubmissions.length === 0" class="wiki-fed-empty">
              No contribution bundles exported yet. Bundles are saved in <code>~/Vault/dispatches/submissions/</code>.
            </div>
            <div v-else class="wiki-fed-table-wrapper">
              <table class="wiki-fed-table">
                <thead>
                  <tr>
                    <th>Submission ID</th>
                    <th>Target</th>
                    <th>Author</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="sub in fedSubmissions" :key="sub.submission_id">
                    <td><code>{{ sub.submission_id }}</code></td>
                    <td><code>{{ sub.manifest?.rel_path }}</code></td>
                    <td>{{ sub.manifest?.author }}</td>
                    <td>{{ new Date(sub.manifest?.created_at).toLocaleString() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <footer class="wiki-fed-modal__footer">
          <button type="button" class="wiki-btn wiki-btn--secondary" @click="showFederationModal = false">
            Close
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import UIcon from "../../skills/atoms/UIcon.vue";
import { renderProseFast, sanitize } from "../../utils/markdownRenderer";
import { hydrateDiagrams } from "../../utils/diagramHydrator";

interface TreeItem {
  name: string;
  title?: string;
  path: string;
  source: string;
  is_dir: boolean;
  size?: number;
  children?: TreeItem[];
}

interface VaultGroup {
  id: string;
  name: string;
  badge: string;
  source: string;
  exists: boolean;
  items: TreeItem[];
  count: number;
}

interface HeadingItem {
  id: string;
  text: string;
  level: number;
}

const loadingTree = ref(true);
const loadingContent = ref(false);
const vaults = ref<VaultGroup[]>([]);
const openGroups = ref<Set<string>>(new Set(["personal", "manuals", "public", "shared"]));
const openFolders = ref<Set<string>>(new Set());

const activeSource = ref<string>("");
const activePath = ref<string>("");
const activeTitle = ref<string>("");
const rawMarkdown = ref<string>("");

const filterQuery = ref<string>("");
const zenMode = ref<boolean>(false);
const fontFamily = ref<"serif" | "sans">("serif");

// ── Recursive Tree Item Subcomponent ──────────────────────────────────
const WikiTreeItem = {
  name: "WikiTreeItem",
  props: {
    item: { type: Object as () => TreeItem, required: true },
    activeSource: { type: String, default: "" },
    activePath: { type: String, default: "" },
  },
  emits: ["select"],
  setup(props: { item: TreeItem; activeSource: string; activePath: string }, { emit }: any) {
    const isFolder = computed(() => props.item.is_dir);
    const isOpen = computed(() => openFolders.value.has(props.item.path));
    const isActive = computed(
      () =>
        !props.item.is_dir &&
        props.activeSource === props.item.source &&
        props.activePath === props.item.path
    );

    function toggle() {
      if (isFolder.value) {
        if (openFolders.value.has(props.item.path)) {
          openFolders.value.delete(props.item.path);
        } else {
          openFolders.value.add(props.item.path);
        }
      } else {
        emit("select", props.item.source, props.item.path, props.item.title || props.item.name);
      }
    }

    return () => {
      if (isFolder.value) {
        return h("div", { class: "wiki-tree-folder" }, [
          h(
            "div",
            {
              class: ["wiki-tree-row", "wiki-tree-row--folder"],
              onClick: toggle,
            },
            [
              h(UIcon, {
                name: isOpen.value ? "folder_open" : "folder",
                size: "xs",
              }),
              h("span", { class: "wiki-tree-label" }, props.item.name),
            ]
          ),
          isOpen.value && props.item.children
            ? h(
                "div",
                { class: "wiki-tree-children" },
                props.item.children.map((child) =>
                  h(WikiTreeItem, {
                    item: child,
                    activeSource: props.activeSource,
                    activePath: props.activePath,
                    onSelect: (src: string, p: string, t: string) => emit("select", src, p, t),
                  })
                )
              )
            : null,
        ]);
      }

      return h(
        "div",
        {
          class: [
            "wiki-tree-row",
            "wiki-tree-row--file",
            isActive.value ? "wiki-tree-row--active" : "",
          ],
          onClick: toggle,
        },
        [
          h(UIcon, { name: "description", size: "xs" }),
          h("span", { class: "wiki-tree-label" }, props.item.title || props.item.name),
        ]
      );
    };
  },
};

// ── Word count and Reading Time ──────────────────────────────────────
const wordCount = computed(() => {
  if (!rawMarkdown.value) return 0;
  return rawMarkdown.value.trim().split(/\s+/).filter(Boolean).length;
});

const estimatedMinutes = computed(() => {
  if (wordCount.value === 0) return 0;
  return Math.ceil(wordCount.value / 200);
});

// ── Find First Article for quick start ────────────────────────────────
const firstArticle = computed(() => {
  for (const v of vaults.value) {
    const found = findFirstFile(v.items);
    if (found) return found;
  }
  return null;
});

function findFirstFile(items: TreeItem[]): TreeItem | null {
  for (const item of items) {
    if (!item.is_dir) return item;
    if (item.children) {
      const sub = findFirstFile(item.children);
      if (sub) return sub;
    }
  }
  return null;
}

// ── Tree Filter ───────────────────────────────────────────────────────
function filterItems(items: TreeItem[], query: string): TreeItem[] {
  const result: TreeItem[] = [];
  const q = query.toLowerCase();

  for (const item of items) {
    if (item.is_dir && item.children) {
      const filteredChildren = filterItems(item.children, query);
      if (filteredChildren.length > 0 || item.name.toLowerCase().includes(q)) {
        result.push({
          ...item,
          children: filteredChildren.length > 0 ? filteredChildren : item.children,
        });
      }
    } else if (
      item.name.toLowerCase().includes(q) ||
      (item.title && item.title.toLowerCase().includes(q))
    ) {
      result.push(item);
    }
  }
  return result;
}

const filteredVaults = computed(() => {
  if (!filterQuery.value.trim()) return vaults.value;
  const q = filterQuery.value.trim();
  return vaults.value
    .map((v) => ({
      ...v,
      items: filterItems(v.items, q),
    }))
    .filter((v) => v.items.length > 0);
});

// ── Group Toggles ─────────────────────────────────────────────────────
function isGroupOpen(groupId: string): boolean {
  return openGroups.value.has(groupId);
}

function toggleGroup(groupId: string) {
  if (openGroups.value.has(groupId)) {
    openGroups.value.delete(groupId);
  } else {
    openGroups.value.add(groupId);
  }
}

function sourceLabel(src: string): string {
  switch (src) {
    case "vault":
      return "Personal Vault (~/Vault)";
    case "shared":
      return "Shared Vault (~/Shared)";
    case "public":
      return "Public Knowledge (~/Public)";
    case "manual":
      return "uCode Beginner Curriculum";
    case "sonic":
      return "Sonic Hardware Rebirth";
    default:
      return src;
  }
}

// ── Headings & TOC Extraction ─────────────────────────────────────────
const headings = computed<HeadingItem[]>(() => {
  if (!rawMarkdown.value) return [];
  const list: HeadingItem[] = [];
  const lines = rawMarkdown.value.split("\n");

  for (const line of lines) {
    const match = line.match(/^(#{1,3})\s+(.+)$/);
    if (match) {
      const level = match[1].length;
      const text = match[2].trim().replace(/[#*_`]/g, "");
      const id = text
        .toLowerCase()
        .replace(/[^\w\s-]/g, "")
        .replace(/\s+/g, "-");
      list.push({ id, text, level });
    }
  }
  return list;
});

function scrollToHeading(id: string) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

// ── Markdown Transformation & External Link Neutralization ────────────
const wikiProseRef = ref<HTMLElement | null>(null);

const renderedHtml = computed(() => {
  if (!rawMarkdown.value) return "";

  let processed = rawMarkdown.value;

  // 1. Transform internal [[WikiLink]] syntax to clickable local links
  processed = processed.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, target, alias) => {
    const label = alias || target;
    return `[${label}](#wiki:${encodeURIComponent(target)})`;
  });

  // 2. Parse Markdown via unified renderer (supports callouts, diagrams, charts, math)
  const rawHtml = renderProseFast(processed);

  // 3. Post-process HTML to:
  //    a) Add IDs to headings for TOC navigation
  //    b) Convert external URLs into offline citation chips
  const doc = new DOMParser().parseFromString(rawHtml, "text/html");

  // Headings
  doc.querySelectorAll("h1, h2, h3").forEach((h) => {
    const text = h.textContent?.trim() || "";
    const id = text
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-");
    h.setAttribute("id", id);
  });

  // Neutralize External Links & Style Internal Wiki Links
  doc.querySelectorAll("a").forEach((a) => {
    const href = a.getAttribute("href") || "";

    if (href.startsWith("#wiki:")) {
      a.classList.add("wiki-internal-link");
      a.setAttribute("data-wiki-target", decodeURIComponent(href.slice(6)));
    } else if (href.startsWith("http://") || href.startsWith("https://")) {
      // Create static offline citation chip
      try {
        const parsedUrl = new URL(href);
        const domain = parsedUrl.hostname.replace(/^www\./, "");
        const span = document.createElement("span");
        span.className = "offline-citation-chip";
        span.title = `External Citation: ${href}`;
        span.innerHTML = `<span class="chip-icon">🔗</span><span class="chip-domain">${domain}</span><span class="chip-tag">offline citation</span>`;
        a.replaceWith(span);
      } catch {
        const span = document.createElement("span");
        span.className = "offline-citation-chip";
        span.textContent = `[Citation: ${href}]`;
        a.replaceWith(span);
      }
    }
  });

  return sanitize(doc.body.innerHTML);
});

// Hydrate diagrams and charts whenever rendered wiki content changes
watch(renderedHtml, async () => {
  await nextTick();
  if (wikiProseRef.value) {
    await hydrateDiagrams(wikiProseRef.value);
  }
}, { immediate: true });

// ── Internal Link Click Interception ──────────────────────────────────
function handleProseClick(event: MouseEvent) {
  const target = (event.target as HTMLElement).closest("a");
  if (!target) return;

  const wikiTarget = target.getAttribute("data-wiki-target");
  if (wikiTarget) {
    event.preventDefault();
    findAndOpenWikiTarget(wikiTarget);
  }
}

function findAndOpenWikiTarget(name: string) {
  const cleanName = name.toLowerCase().trim();
  for (const vault of vaults.value) {
    const item = searchTreeForName(vault.items, cleanName);
    if (item) {
      selectDocument(item.source, item.path, item.title || item.name);
      return;
    }
  }
}

function searchTreeForName(items: TreeItem[], name: string): TreeItem | null {
  for (const item of items) {
    if (!item.is_dir) {
      if (
        item.name.toLowerCase().includes(name) ||
        (item.title && item.title.toLowerCase().includes(name))
      ) {
        return item;
      }
    }
    if (item.children) {
      const found = searchTreeForName(item.children, name);
      if (found) return found;
    }
  }
  return null;
}

// ── API Actions ───────────────────────────────────────────────────────
async function loadTree() {
  loadingTree.value = true;
  try {
    const resp = await fetch("/api/docs/wiki/tree");
    if (resp.ok) {
      const data = await resp.json();
      vaults.value = data.vaults || [];
      // Auto-open first article if none selected
      if (!activePath.value && firstArticle.value) {
        selectDocument(
          firstArticle.value.source,
          firstArticle.value.path,
          firstArticle.value.title || firstArticle.value.name
        );
      }
    }
  } catch (err) {
    console.error("Failed to load multi-vault tree:", err);
  } finally {
    loadingTree.value = false;
  }
}

interface ActiveOverlayInfo {
  is_overlaid: boolean;
  effective_layer: number | null;
  effective_layer_name: string | null;
  canon_exists: boolean;
  has_diff: boolean;
  diff_from_canon: string;
  diff_stats: { additions: number; deletions: number };
  rel_path: string;
}

const activeOverlay = ref<ActiveOverlayInfo | null>(null);
const showingCanonOnly = ref(false);
const revertingOverlay = ref(false);
const customizingOverlay = ref(false);

const showDiffModal = ref(false);
const showSubmissionModal = ref(false);
const showFederationModal = ref(false);

const fedSummary = ref<any>(null);
const fedOverlays = ref<any[]>([]);
const fedSubmissions = ref<any[]>([]);
const loadingFed = ref(false);

const submissionAuthor = ref("sovereign-user");
const submissionNotes = ref("");
const submissionType = ref("canonical_patch");
const preflightResult = ref<any>(null);
const packagingSubmission = ref(false);
const submissionSuccess = ref<any>(null);

const formattedDiffLines = computed(() => {
  if (!activeOverlay.value || !activeOverlay.value.diff_from_canon) {
    return [];
  }
  const lines = activeOverlay.value.diff_from_canon.split("\n");
  return lines.map((line, idx) => {
    let type = "diff-ctx";
    if (line.startsWith("+") && !line.startsWith("+++")) type = "diff-add";
    else if (line.startsWith("-") && !line.startsWith("---")) type = "diff-del";
    else if (line.startsWith("@@")) type = "diff-hdr";
    return {
      num: idx + 1,
      type,
      content: line,
    };
  });
});

function layerChipClass(layer: number | null, isOverlaid: boolean) {
  if (isOverlaid) return "wiki-chip--overlaid";
  if (layer === 0) return "wiki-chip--canon";
  if (layer === 1) return "wiki-chip--community";
  if (layer === 2) return "wiki-chip--personal";
  return "";
}

function layerIcon(layer: number | null) {
  if (layer === 0) return "verified";
  if (layer === 1) return "groups";
  if (layer === 2) return "person";
  return "description";
}

function layerBadgeLabel(layer: number | null, isOverlaid: boolean) {
  if (isOverlaid && layer === 2) return "Personal Overlay";
  if (isOverlaid && layer === 1) return "Community Overlay";
  if (layer === 0) return "Base Canon";
  if (layer === 1) return "Community";
  if (layer === 2) return "Personal";
  return "Document";
}

async function selectDocument(
  source: string,
  path: string,
  title?: string,
  forceCanon: boolean = false
) {
  activeSource.value = source;
  activePath.value = path;
  activeTitle.value = title || path.split("/").pop() || "Untitled";
  loadingContent.value = true;
  showingCanonOnly.value = forceCanon;

  try {
    const url = `/api/docs/content?source=${encodeURIComponent(source)}&path=${encodeURIComponent(path)}${forceCanon ? "&canonical=true" : ""}`;
    const resp = await fetch(url);
    if (resp.ok) {
      const data = await resp.json();
      rawMarkdown.value = data.content || "";
      activeOverlay.value = data.overlay || null;
    } else {
      rawMarkdown.value = `# Unable to load document\n\nPath: \`${path}\``;
      activeOverlay.value = null;
    }
  } catch (err) {
    rawMarkdown.value = `# Network Error\n\nCould not fetch document \`${path}\`.`;
    activeOverlay.value = null;
  } finally {
    loadingContent.value = false;
  }
}

async function toggleCanonOnly() {
  const nextState = !showingCanonOnly.value;
  await selectDocument(activeSource.value, activePath.value, activeTitle.value, nextState);
}

function openDiffModal() {
  showDiffModal.value = true;
}

async function customizeInVault() {
  if (!activeOverlay.value) return;
  customizingOverlay.value = true;
  try {
    const resp = await fetch("/api/knowledge/federation/overlay", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: activeOverlay.value.rel_path,
        content: rawMarkdown.value,
        layer: 2,
      }),
    });
    if (resp.ok) {
      const data = await resp.json();
      activeOverlay.value = data.overlay || activeOverlay.value;
      activeSource.value = "vault";
    }
  } catch (err) {
    console.error("Customize error:", err);
  } finally {
    customizingOverlay.value = false;
  }
}

async function confirmRevertToCanon() {
  if (!activeOverlay.value) return;
  if (!confirm(`Revert personal changes for "${activeTitle.value}" and restore pristine canonical baseline?`)) {
    return;
  }
  revertingOverlay.value = true;
  try {
    const resp = await fetch("/api/knowledge/federation/revert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: activeOverlay.value.rel_path,
        layer: 2,
      }),
    });
    if (resp.ok) {
      const data = await resp.json();
      activeOverlay.value = data.resolved || null;
      await selectDocument(activeSource.value, activePath.value, activeTitle.value, false);
    }
  } catch (err) {
    console.error("Revert error:", err);
  } finally {
    revertingOverlay.value = false;
  }
}

async function runPreflight() {
  if (!activeOverlay.value) return;
  try {
    const resp = await fetch("/api/knowledge/federation/preflight", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: rawMarkdown.value,
        path: activeOverlay.value.rel_path,
      }),
    });
    if (resp.ok) {
      preflightResult.value = await resp.json();
    }
  } catch (err) {
    console.error("Preflight check error:", err);
  }
}

async function openSubmissionModal() {
  showSubmissionModal.value = true;
  submissionSuccess.value = null;
  submissionNotes.value = "";
  await runPreflight();
}

async function submitPackage() {
  if (!activeOverlay.value) return;
  packagingSubmission.value = true;
  try {
    const resp = await fetch("/api/knowledge/federation/export-submission", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: activeOverlay.value.rel_path,
        author: submissionAuthor.value,
        notes: submissionNotes.value,
        submission_type: submissionType.value,
      }),
    });
    if (resp.ok) {
      const data = await resp.json();
      submissionSuccess.value = data.package;
    } else {
      const err = await resp.json();
      alert(`Submission export failed: ${err.error || "Unknown error"}`);
    }
  } catch (err) {
    console.error("Submission export error:", err);
  } finally {
    packagingSubmission.value = false;
  }
}

async function openFederationOverviewModal() {
  showFederationModal.value = true;
  loadingFed.value = true;
  try {
    const [summaryResp, overlaysResp, subsResp] = await Promise.all([
      fetch("/api/knowledge/federation/summary"),
      fetch("/api/knowledge/federation/overlays"),
      fetch("/api/knowledge/federation/submissions"),
    ]);
    if (summaryResp.ok) fedSummary.value = await summaryResp.json();
    if (overlaysResp.ok) {
      const oData = await overlaysResp.json();
      fedOverlays.value = oData.overlays || [];
    }
    if (subsResp.ok) {
      const sData = await subsResp.json();
      fedSubmissions.value = sData.submissions || [];
    }
  } catch (err) {
    console.error("Load federation data error:", err);
  } finally {
    loadingFed.value = false;
  }
}

const showSearchModal = ref(false);
const searchQuery = ref("");
const searchZone = ref<"all" | "personal" | "public" | "manuals" | "shared">("all");
const searchResults = ref<any[]>([]);
const searching = ref(false);
const selectedResultIndex = ref(0);
const searchInputRef = ref<HTMLInputElement | null>(null);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function openSearchModal() {
  showSearchModal.value = true;
  selectedResultIndex.value = 0;
  nextTick(() => {
    searchInputRef.value?.focus();
  });
}

function closeSearchModal() {
  showSearchModal.value = false;
}

function setSearchZone(zone: "all" | "personal" | "public" | "manuals" | "shared") {
  searchZone.value = zone;
  runSearch();
}

function runQuickSearch(query: string) {
  searchQuery.value = query;
  runSearch();
}

function navigateResults(delta: number) {
  if (searchResults.value.length === 0) return;
  const newIndex = selectedResultIndex.value + delta;
  if (newIndex >= 0 && newIndex < searchResults.value.length) {
    selectedResultIndex.value = newIndex;
  }
}

function selectCurrentResult() {
  if (searchResults.value.length > 0 && selectedResultIndex.value < searchResults.value.length) {
    chooseSearchResult(searchResults.value[selectedResultIndex.value]);
  }
}

function chooseSearchResult(item: any) {
  closeSearchModal();
  selectDocument(item.source, item.rel_path, item.title);
}

function highlightSearchTerm(text: string, term: string): string {
  if (!text || !term.trim()) return text || "";
  const escaped = term.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return text.replace(new RegExp(`(${escaped})`, "gi"), "<mark>$1</mark>");
}

async function runSearch() {
  const q = searchQuery.value.trim();
  if (!q) {
    searchResults.value = [];
    searching.value = false;
    return;
  }

  searching.value = true;
  try {
    let url = `/api/docs/wiki/search?q=${encodeURIComponent(q)}&limit=25`;
    if (searchZone.value !== "all") {
      url += `&vault=${encodeURIComponent(searchZone.value)}`;
    }
    const resp = await fetch(url);
    if (resp.ok) {
      const data = await resp.json();
      searchResults.value = data.results || [];
      selectedResultIndex.value = 0;
    }
  } catch (err) {
    console.error("Search failed:", err);
  } finally {
    searching.value = false;
  }
}

watch(searchQuery, () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    runSearch();
  }, 150);
});

function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    if (showSearchModal.value) {
      closeSearchModal();
    } else {
      openSearchModal();
    }
  } else if (e.key === "Escape" && showSearchModal.value) {
    closeSearchModal();
  }
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  loadTree();
});

onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
});
</script>

<style scoped>
.local-wiki-reader {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--usx-color-bg, #0d1117);
  color: var(--usx-color-text, #c9d1d9);
  font-family: inherit;
}

/* ── Typography Modes ──────────────────────────────────────────────── */
.local-wiki-reader.font-serif .wiki-prose {
  font-family: "Charter", "Georgia", "Merriweather", serif;
}

.local-wiki-reader.font-sans .wiki-prose {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif;
}

/* ── Top Toolbar ───────────────────────────────────────────────────── */
.wiki-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--usx-color-surface, #161b22);
  border-bottom: 1px solid var(--usx-color-border, #30363d);
  gap: 16px;
}

.wiki-toolbar__left,
.wiki-toolbar__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wiki-toolbar__center {
  flex: 1;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wiki-meta__title {
  font-weight: 600;
  margin-right: 10px;
  color: var(--usx-color-primary, #58a6ff);
}

.wiki-meta__reading-time {
  font-size: 12px;
  color: #8b949e;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.wiki-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 12px;
  background: #21262d;
  color: #c9d1d9;
  border: 1px solid #30363d;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.wiki-btn:hover {
  background: #30363d;
}

.wiki-btn--active {
  background: #1f6feb;
  color: #ffffff;
  border-color: #388bfd;
}

.wiki-btn--primary {
  background: #238636;
  color: #ffffff;
  border-color: #2ea043;
  padding: 8px 16px;
  font-size: 14px;
}

.wiki-btn--primary:hover {
  background: #2ea043;
}

.wiki-font-toggle {
  display: inline-flex;
  border: 1px solid #30363d;
  border-radius: 4px;
  overflow: hidden;
}

.wiki-btn--toggle {
  border: none;
  border-radius: 0;
}

.wiki-search-box {
  display: inline-flex;
  align-items: center;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 4px;
  padding: 2px 8px;
  gap: 6px;
}

.wiki-search-input {
  background: transparent;
  border: none;
  color: #c9d1d9;
  font-size: 12px;
  width: 160px;
  outline: none;
}

.wiki-search-clear {
  background: transparent;
  border: none;
  color: #8b949e;
  cursor: pointer;
  display: flex;
  align-items: center;
}

/* ── Main Layout ───────────────────────────────────────────────────── */
.wiki-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.wiki-sidebar {
  width: 320px;
  background: #161b22;
  border-right: 1px solid #30363d;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.wiki-sidebar__header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #21262d;
}

.wiki-sidebar__title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #8b949e;
}

.wiki-badge--offline {
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
  border: 1px solid rgba(63, 185, 80, 0.3);
  border-radius: 10px;
}

.wiki-tree {
  padding: 8px 0;
}

.wiki-vault-group {
  margin-bottom: 6px;
}

.wiki-vault-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #e6edf3;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.02);
}

.wiki-vault-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.wiki-vault-name {
  flex: 1;
}

.wiki-vault-badge {
  font-size: 10px;
  color: #8b949e;
  background: #21262d;
  padding: 1px 6px;
  border-radius: 4px;
}

.wiki-vault-items {
  padding-left: 8px;
}

/* ── Tree Rows ─────────────────────────────────────────────────────── */
:deep(.wiki-tree-row) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 12px;
  color: #8b949e;
  cursor: pointer;
  border-radius: 4px;
  margin: 1px 4px;
  user-select: none;
}

:deep(.wiki-tree-row:hover) {
  background: #21262d;
  color: #c9d1d9;
}

:deep(.wiki-tree-row--active) {
  background: rgba(88, 166, 255, 0.15) !important;
  color: #58a6ff !important;
  font-weight: 500;
}

:deep(.wiki-tree-children) {
  padding-left: 12px;
  border-left: 1px dashed #30363d;
  margin-left: 10px;
}

/* ── Content / Reading Area ────────────────────────────────────────── */
.wiki-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.local-wiki-reader--zen .wiki-content {
  padding: 48px 64px;
}

.wiki-article {
  width: 100%;
  max-width: 760px;
}

.wiki-article__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid #21262d;
}

.wiki-breadcrumb {
  font-size: 12px;
  color: #8b949e;
}

.wiki-breadcrumb__sep {
  margin: 0 6px;
  color: #484f58;
}

.wiki-chip--offline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  color: #3fb950;
}

.wiki-chip--canon {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(88, 166, 255, 0.1);
  border: 1px solid rgba(88, 166, 255, 0.3);
  border-radius: 12px;
  color: #58a6ff;
}

.wiki-chip--community {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(188, 140, 255, 0.1);
  border: 1px solid rgba(188, 140, 255, 0.3);
  border-radius: 12px;
  color: #bc8cff;
}

.wiki-chip--personal {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(210, 153, 34, 0.1);
  border: 1px solid rgba(210, 153, 34, 0.3);
  border-radius: 12px;
  color: #d29922;
}

.wiki-chip--overlaid {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(240, 136, 62, 0.1);
  border: 1px solid rgba(240, 136, 62, 0.3);
  border-radius: 12px;
  color: #f0883e;
}

/* ── Knowledge Federation Action Strip ────────────────────────────── */
.wiki-federation-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 8px 12px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  gap: 8px;
}

.wiki-fed-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.wiki-btn--xs {
  font-size: 11px;
  padding: 4px 10px;
  gap: 4px;
  height: 28px;
}

.wiki-btn--diff {
  background: rgba(88, 166, 255, 0.12);
  border-color: #388bfd;
  color: #58a6ff;
}

.wiki-btn--revert {
  background: rgba(248, 81, 73, 0.1);
  border-color: rgba(248, 81, 73, 0.4);
  color: #f85149;
}

.wiki-btn--fork {
  background: rgba(46, 160, 67, 0.12);
  border-color: #2ea043;
  color: #3fb950;
}

.wiki-btn--export {
  background: rgba(210, 153, 34, 0.12);
  border-color: #d29922;
  color: #d29922;
}

.wiki-btn--ghost {
  background: transparent;
  border-color: #30363d;
  color: #8b949e;
}

.wiki-fed-diff-stats {
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 10px;
  background: rgba(0, 0, 0, 0.3);
  padding: 1px 5px;
  border-radius: 4px;
  margin-left: 4px;
}

/* ── Federation Modals ────────────────────────────────────────────── */
.wiki-fed-modal {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  width: 100%;
  max-width: 680px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-height: 85vh;
}

.wiki-fed-modal--wide {
  max-width: 860px;
}

.wiki-fed-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #30363d;
  background: #0d1117;
}

.wiki-fed-modal__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wiki-fed-modal__icon {
  color: #58a6ff;
}

.wiki-fed-modal__title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #f0f6fc;
}

.wiki-fed-modal__body {
  padding: 18px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.wiki-fed-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 18px;
  border-top: 1px solid #30363d;
  background: #0d1117;
}

.wiki-fed-diff-meta {
  background: #0d1117;
  border: 1px solid #21262d;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 12px;
  color: #8b949e;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wiki-fed-diff-viewer {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  font-family: var(--usx-font-family-mono, monospace);
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  max-height: 400px;
}

.wiki-diff-line {
  display: flex;
  padding: 1px 8px;
}

.wiki-diff-line-num {
  width: 32px;
  color: #484f58;
  user-select: none;
  text-align: right;
  padding-right: 8px;
}

.wiki-diff-line-content {
  white-space: pre-wrap;
  word-break: break-all;
}

.wiki-diff-line.diff-add {
  background: rgba(46, 160, 67, 0.15);
  color: #3fb950;
}

.wiki-diff-line.diff-del {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
}

.wiki-diff-line.diff-hdr {
  background: rgba(88, 166, 255, 0.1);
  color: #58a6ff;
  font-weight: 600;
}

/* Submission form styles */
.wiki-fed-modal__desc {
  font-size: 13px;
  color: #8b949e;
  margin: 0;
}

.wiki-form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.wiki-form-group label {
  font-size: 12px;
  font-weight: 500;
  color: #c9d1d9;
}

.wiki-input, .wiki-textarea {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 8px 12px;
  color: #f0f6fc;
  font-size: 13px;
  outline: none;
}

.wiki-input--readonly {
  color: #8b949e;
  font-family: var(--usx-font-family-mono, monospace);
  background: #161b22;
}

.wiki-preflight-panel {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wiki-preflight-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #f0f6fc;
}

.wiki-status-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: 700;
}

.tag--pass {
  background: rgba(46, 160, 67, 0.2);
  color: #3fb950;
  border: 1px solid #2ea043;
}

.tag--fail {
  background: rgba(248, 81, 73, 0.2);
  color: #f85149;
  border: 1px solid #da3633;
}

.wiki-check-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.check--ok {
  color: #3fb950;
}

.check--fail {
  color: #f85149;
}

.check--warn {
  color: #d29922;
}

.wiki-preflight-errors {
  margin-top: 6px;
  padding: 8px;
  background: rgba(248, 81, 73, 0.1);
  border-radius: 4px;
  font-size: 12px;
  color: #f85149;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wiki-submission-success {
  padding: 16px;
  background: rgba(46, 160, 67, 0.1);
  border: 1px solid #2ea043;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wiki-success-title {
  font-size: 15px;
  font-weight: 600;
  color: #3fb950;
  display: flex;
  align-items: center;
  gap: 8px;
}

.wiki-checksum-row {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #8b949e;
}

/* 3-Tier Grid */
.wiki-fed-tier-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.wiki-fed-tier-card {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tier-card__header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tier-card__header h4 {
  margin: 0;
  font-size: 13px;
  color: #f0f6fc;
}

.tier-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
}

.tier--personal .tier-badge {
  background: rgba(210, 153, 34, 0.2);
  color: #d29922;
}

.tier--community .tier-badge {
  background: rgba(188, 140, 255, 0.2);
  color: #bc8cff;
}

.tier--canon .tier-badge {
  background: rgba(88, 166, 255, 0.2);
  color: #58a6ff;
}

.tier-path code {
  font-size: 11px;
  color: #8b949e;
}

.tier-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin: 4px 0;
}

.stat-number {
  font-size: 22px;
  font-weight: 700;
  color: #f0f6fc;
}

.stat-label {
  font-size: 11px;
  color: #8b949e;
}

.tier-desc {
  font-size: 11px;
  color: #8b949e;
  line-height: 1.4;
  margin: 0;
}

.wiki-fed-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wiki-fed-section-title {
  margin: 0;
  font-size: 13px;
  color: #f0f6fc;
  font-weight: 600;
}

.wiki-fed-empty {
  font-size: 12px;
  color: #8b949e;
  font-style: italic;
  padding: 8px 0;
}

.wiki-fed-table-wrapper {
  border: 1px solid #30363d;
  border-radius: 6px;
  overflow: hidden;
}

.wiki-fed-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.wiki-fed-table th {
  background: #0d1117;
  padding: 8px 12px;
  text-align: left;
  color: #8b949e;
  font-weight: 500;
  border-bottom: 1px solid #30363d;
}

.wiki-fed-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #21262d;
  color: #c9d1d9;
}

.wiki-tag--overlaid {
  color: #f0883e;
  font-size: 11px;
}

.wiki-tag--new {
  color: #3fb950;
  font-size: 11px;
}

.wiki-muted-text {
  color: #6e7681;
  font-size: 11px;
}

/* ── Table of Contents ─────────────────────────────────────────────── */
.wiki-toc {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 32px;
}

.wiki-toc__title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: #8b949e;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.wiki-toc__list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.wiki-toc__item {
  font-size: 13px;
  margin: 4px 0;
}

.wiki-toc__item--l1 {
  font-weight: 600;
}

.wiki-toc__item--l2 {
  padding-left: 14px;
}

.wiki-toc__item--l3 {
  padding-left: 28px;
  font-size: 12px;
  color: #8b949e;
}

.wiki-toc__item a {
  color: #58a6ff;
  text-decoration: none;
}

.wiki-toc__item a:hover {
  text-decoration: underline;
}

/* ── Prose Typography & 70ch Optimal Measure ───────────────────────── */
.prose-measure {
  max-width: 72ch;
  line-height: 1.75;
  font-size: 16px;
}

:deep(.wiki-prose h1) {
  font-size: 2rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #30363d;
  padding-bottom: 0.3em;
  color: #f0f6fc;
}

:deep(.wiki-prose h2) {
  font-size: 1.5rem;
  margin-top: 1.8rem;
  margin-bottom: 0.8rem;
  border-bottom: 1px solid #21262d;
  padding-bottom: 0.3em;
  color: #f0f6fc;
}

:deep(.wiki-prose h3) {
  font-size: 1.25rem;
  margin-top: 1.4rem;
  margin-bottom: 0.6rem;
  color: #e6edf3;
}

:deep(.wiki-prose p) {
  margin-top: 0;
  margin-bottom: 1.2rem;
  color: #c9d1d9;
}

:deep(.wiki-prose pre) {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  font-family: "Berkeley Mono", Menlo, Consolas, monospace;
  font-size: 13px;
  margin-bottom: 1.2rem;
}

:deep(.wiki-prose code) {
  background: rgba(110, 118, 129, 0.2);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 85%;
  font-family: "Berkeley Mono", Menlo, Consolas, monospace;
}

/* ── Internal Wiki Links ───────────────────────────────────────────── */
:deep(.wiki-internal-link) {
  color: #58a6ff;
  text-decoration: none;
  border-bottom: 1px dashed #58a6ff;
  cursor: pointer;
}

:deep(.wiki-internal-link:hover) {
  color: #79c0ff;
  border-bottom-style: solid;
}

/* ── Static Offline Citation Chips (Preventing Live Web Navigation) ── */
:deep(.offline-citation-chip) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 11px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #8b949e;
  margin: 0 3px;
  vertical-align: baseline;
  user-select: all;
}

:deep(.offline-citation-chip .chip-icon) {
  font-size: 10px;
}

:deep(.offline-citation-chip .chip-domain) {
  color: #c9d1d9;
  font-weight: 500;
}

:deep(.offline-citation-chip .chip-tag) {
  font-size: 9px;
  text-transform: uppercase;
  color: #f2cc60;
  background: rgba(242, 204, 96, 0.1);
  padding: 0 4px;
  border-radius: 2px;
}

/* ── Placeholder Screen ────────────────────────────────────────────── */
.wiki-placeholder {
  text-align: center;
  padding: 64px 24px;
  max-width: 540px;
  margin: auto;
}

.wiki-placeholder__icon {
  font-size: 48px;
  color: #58a6ff;
  margin-bottom: 16px;
}

.wiki-placeholder h2 {
  font-size: 22px;
  margin-bottom: 12px;
  color: #f0f6fc;
}

.wiki-placeholder p {
  color: #8b949e;
  line-height: 1.6;
  margin-bottom: 12px;
}

.wiki-placeholder__note {
  font-size: 13px;
  color: #3fb950 !important;
}

.wiki-placeholder__actions {
  margin-top: 24px;
}

.wiki-loading-content,
.wiki-loading,
.wiki-empty-tree {
  padding: 24px;
  text-align: center;
  color: #8b949e;
  font-size: 13px;
}

/* ── Search Trigger & Sidebar Tree Filter ────────────────────────── */
.wiki-search-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--usx-color-surface-variant, #161b22);
  color: var(--usx-color-text-muted, #8b949e);
  border: 1px solid var(--usx-color-border, #30363d);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.wiki-search-trigger:hover {
  background: var(--usx-color-surface, #21262d);
  border-color: #58a6ff;
  color: var(--usx-color-text, #c9d1d9);
}

.wiki-search-trigger__text {
  font-size: 12px;
}

.wiki-kbd {
  display: inline-block;
  padding: 1px 5px;
  font-size: 10px;
  font-family: inherit;
  font-weight: 600;
  color: #8b949e;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}

.wiki-tree-filter {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 4px 8px;
  margin: 8px 12px;
}

.wiki-tree-filter-input {
  background: transparent;
  border: none;
  color: #c9d1d9;
  font-size: 12px;
  width: 100%;
  outline: none;
}

/* ── Offline Search Modal (Cmd+K) ────────────────────────────────── */
.wiki-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 80px;
  z-index: 1000;
}

.wiki-search-modal {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  width: 100%;
  max-width: 680px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.wiki-search-modal__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid #30363d;
  background: #0d1117;
}

.wiki-search-modal__icon {
  color: #58a6ff;
  font-size: 20px;
}

.wiki-search-modal__input {
  flex: 1;
  background: transparent;
  border: none;
  color: #f0f6fc;
  font-size: 16px;
  outline: none;
}

.wiki-search-modal__filters {
  display: flex;
  gap: 6px;
  padding: 8px 16px;
  background: #0d1117;
  border-bottom: 1px solid #21262d;
  overflow-x: auto;
}

.wiki-filter-pill {
  background: transparent;
  border: 1px solid transparent;
  color: #8b949e;
  border-radius: 14px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.wiki-filter-pill:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #c9d1d9;
}

.wiki-filter-pill--active {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  font-weight: 600;
}

.wiki-search-modal__results {
  max-height: 420px;
  min-height: 180px;
  overflow-y: auto;
  padding: 8px 0;
}

.wiki-search-loading,
.wiki-search-empty,
.wiki-search-hint {
  padding: 32px 24px;
  text-align: center;
  color: #8b949e;
}

.wiki-search-empty p {
  margin: 8px 0 4px;
  color: #c9d1d9;
  font-size: 14px;
}

.wiki-search-hint p {
  margin-bottom: 12px;
  font-size: 13px;
  color: #8b949e;
  line-height: 1.5;
}

.wiki-search-quick-tags {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}

.quick-tag {
  background: #21262d;
  border: 1px solid #30363d;
  color: #58a6ff;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  cursor: pointer;
}

.quick-tag:hover {
  background: rgba(56, 189, 248, 0.15);
}

.wiki-results-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.wiki-result-item {
  padding: 10px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: background 0.12s ease;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wiki-result-item:hover,
.wiki-result-item--selected {
  background: rgba(56, 189, 248, 0.1);
}

.wiki-result-item__top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.wiki-result-item__title {
  font-weight: 600;
  color: #f0f6fc;
  font-size: 14px;
}

.wiki-result-item__title :deep(mark),
.wiki-result-item__snippet :deep(mark) {
  background: rgba(56, 189, 248, 0.35);
  color: #f0f6fc;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 600;
}

.wiki-result-item__badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #21262d;
  color: #8b949e;
  border: 1px solid #30363d;
  text-transform: uppercase;
}

.wiki-result-item__snippet {
  margin: 0;
  font-size: 12px;
  color: #8b949e;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.wiki-result-item__meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #6e7681;
}

.wiki-result-item__path {
  font-family: monospace;
}

.wiki-search-modal__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 18px;
  background: #0d1117;
  border-top: 1px solid #30363d;
  font-size: 11px;
  color: #8b949e;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #3fb950;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.wiki-kbd-mini {
  display: inline-block;
  padding: 1px 4px;
  font-size: 9px;
  font-family: inherit;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 3px;
  margin-right: 4px;
}
</style>
