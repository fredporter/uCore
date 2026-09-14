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
        <!-- Stage 3: Requirements & Plan -->
        <section v-if="currentStage === 'plan'" class="stage-content stage-plan">
          <div class="plan-header">
            <div>
              <h3>Requirements & Bounded Execution Plan</h3>
              <p class="section-subtext">uFlow strictly enforces requirements mapping and execution budgeting.</p>
            </div>
            <div class="plan-actions">
              <button
                v-if="activeBinder.metadata.state === 'draft_brief' || activeBinder.metadata.state === 'planned'"
                class="wf-zen-secondary"
                type="button"
                :disabled="authorisingRun"
                @click="authoriseRun"
              >
                <UIcon name="lock" />
                {{ authorisingRun ? 'Authorising...' : 'Authorise Run' }}
              </button>
              <button
                v-if="activeBinder.metadata.state === 'running' || activeBinder.metadata.state === 'blocked'"
                class="wf-zen-secondary"
                type="button"
                :disabled="runningAssembly"
                @click="resumeRun"
              >
                <UIcon name="replay" />
                Resume from Checkpoint
              </button>
              <button class="wf-zen-primary" type="button" :disabled="runningAssembly" @click="runAssembly">
                <UIcon name="play_arrow" />
                {{ runningAssembly ? 'Assembling Draft...' : 'Run Bounded Assembly' }}
              </button>
            </div>
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

        <!-- Stage 4: Decisions & Rationale Log -->
        <section v-if="currentStage === 'decisions'" class="stage-content stage-decisions">
          <div class="decisions-header">
            <div>
              <h3>Architectural Decisions & Rationale Log</h3>
              <p class="section-subtext">Record accepted choices, rejected proposals, and superseded alternatives.</p>
            </div>
            <button class="wf-zen-primary" type="button" @click="showAddDecisionModal = true">
              <UIcon name="add" /> Record Decision
            </button>
          </div>

          <div v-if="!activeBinder.decisions || activeBinder.decisions.length === 0" class="empty-hint">
            No decisions recorded yet. Document key technical choices to maintain project traceability.
          </div>
          <div v-else class="decisions-grid">
            <div
              v-for="dec in activeBinder.decisions"
              :key="dec.id"
              class="decision-card"
            >
              <div class="decision-card__header">
                <span class="decision-id">{{ dec.id }}</span>
                <span class="decision-status" :class="`decision-status--${dec.status}`">{{ dec.status }}</span>
              </div>
              <h4>{{ dec.title }}</h4>
              <p v-if="dec.rationale" class="decision-rationale">{{ dec.rationale }}</p>
              <span class="decision-time">{{ new Date(dec.timestamp).toLocaleDateString() }}</span>
            </div>
          </div>
        </section>

        <!-- Stage 5: Zen Lite Editor & Anti-Drift Audit -->
        <section v-if="currentStage === 'draft'" class="stage-content stage-draft">
          <!-- Zen Lite Toolbar -->
          <div class="zen-toolbar">
            <div class="zen-typography-toggles">
              <button
                type="button"
                class="zen-pill"
                :class="{ 'zen-pill--active': editorFont === 'serif' }"
                @click="editorFont = 'serif'"
              >Serif</button>
              <button
                type="button"
                class="zen-pill"
                :class="{ 'zen-pill--active': editorFont === 'sans' }"
                @click="editorFont = 'sans'"
              >Sans</button>
              <button
                type="button"
                class="zen-pill"
                :class="{ 'zen-pill--active': editorFont === 'mono' }"
                @click="editorFont = 'mono'"
              >Mono</button>
            </div>

            <div class="zen-stats">
              <span>{{ wordCount }} words</span> ·
              <span>~{{ readingTimeMinutes }} min read</span>
            </div>

            <div v-if="activeBinder.sources?.length" class="zen-citation-chips">
              <span class="citation-hint">Insert citation:</span>
              <button
                v-for="s in activeBinder.sources"
                :key="s.citation_tag"
                type="button"
                class="citation-chip-btn"
                :title="`Insert ${s.citation_tag} (${s.file_name})`"
                @click="insertCitation(s.citation_tag)"
              >
                {{ s.citation_tag }}
              </button>
            </div>

            <div class="draft-actions">
              <button
                class="wf-zen-secondary audit-btn"
                type="button"
                :disabled="auditing"
                @click="runAudit"
              >
                <UIcon name="policy" /> {{ auditing ? 'Auditing...' : 'Audit Anti-Drift' }}
              </button>
              <button class="wf-zen-secondary" type="button" @click="reloadBinder">
                <UIcon name="refresh" /> Reload
              </button>
              <button class="wf-zen-primary" type="button" :disabled="savingDraft" @click="saveDraft">
                <UIcon name="save" /> {{ savingDraft ? 'Saving...' : 'Save Draft' }}
              </button>
            </div>
          </div>

          <!-- Anti-Drift Audit Result Banner -->
          <div v-if="auditReport" class="audit-banner" :class="auditReport.passed ? 'audit-banner--passed' : 'audit-banner--warn'">
            <UIcon :name="auditReport.passed ? 'check_circle' : 'warning'" />
            <div>
              <strong>Audit: {{ auditReport.coverage_percentage }}% Requirement Coverage</strong>
              <span v-if="auditReport.passed"> — All {{ auditReport.requirements_total }} requirements verified with provenance linkage.</span>
              <span v-else> — Missing requirements: {{ auditReport.missing_requirements?.join(', ') }}</span>
            </div>
          </div>

          <!-- Concurrency conflict banner -->
          <div v-if="conflictDetected" class="conflict-alert">
            <UIcon name="warning" />
            <div>
              <strong>Concurrency Conflict Detected!</strong>
              <p>The draft on disk was modified elsewhere. Your changes were not overwritten. Click 'Reload' to fetch latest disk revision.</p>
            </div>
          </div>

          <div class="draft-editor-container" :class="`draft-editor--${editorFont}`">
            <textarea
              v-model="editableDraft"
              class="draft-textarea"
              :class="`draft-textarea--${editorFont}`"
              placeholder="Draft contents..."
              rows="18"
            />
          </div>

          <div class="evidence-ledger">
            <h3>Evidence & Claim Citations Chain ({{ activeBinder.evidence?.length || 0 }})</h3>
            <div v-if="!activeBinder.evidence || activeBinder.evidence.length === 0" class="empty-hint">
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

        <!-- Stage 6: Editions & Universal Export Bridges -->
        <section v-if="currentStage === 'publish'" class="stage-content stage-publish">
          <!-- Universal Export Bridges Card -->
          <div class="universal-exports-card">
            <div class="universal-exports-card__header">
              <UIcon name="share" />
              <div>
                <h4>Universal Export Bridges</h4>
                <p>Export project artifacts for Obsidian everyday authoring or Gemini Notebooks (NotebookLM) synthesis.</p>
              </div>
            </div>
            <div class="export-actions">
              <button class="wf-zen-secondary" type="button" @click="exportGemini">
                <UIcon name="download" /> Export for Gemini Notebooks (NotebookLM)
              </button>
              <button class="wf-zen-secondary" type="button" @click="exportObsidian">
                <UIcon name="folder_open" /> Generate Obsidian Vault Index
              </button>
            </div>
          </div>

          <!-- Sovereign Dispatch & Interactive Invitation Studio Card -->
          <div class="dispatch-studio-card">
            <div class="dispatch-studio-card__header">
              <div class="dispatch-studio-title">
                <UIcon name="send" />
                <div>
                  <h4>Sovereign Dispatch &amp; Interactive Invitation Studio</h4>
                  <p>Publish an ephemeral, tracked-free interactive story or greeting card dispatch directly from this binder's content.</p>
                </div>
              </div>
              <div class="dispatch-header-actions">
                <a href="/api/dispatch/feed.xml" target="_blank" class="wf-zen-subtle action-btn" title="Open Syndicated RSS 2.0 Feed with GIF enclosures">
                  <UIcon name="rss_feed" /> Syndicated RSS
                </a>
                <button class="wf-zen-secondary" type="button" @click="showDispatchCreator = !showDispatchCreator">
                  <UIcon :name="showDispatchCreator ? 'expand_less' : 'add'" />
                  {{ showDispatchCreator ? 'Close Studio' : 'New Dispatch' }}
                </button>
              </div>
            </div>

            <!-- Dispatch Creation Form Panel -->
            <div v-if="showDispatchCreator" class="dispatch-form">
              <div class="dispatch-form__grid">
                <div class="dispatch-form__col">
                  <label>Dispatch Title
                    <input v-model="dispatchForm.title" type="text" placeholder="e.g. Project Odyssey: Invitation to Collaborate" />
                  </label>
                  <label>Lead / Subtitle
                    <input v-model="dispatchForm.lead_text" type="text" placeholder="A calm, sovereign interactive dispatch..." />
                  </label>
                  <div class="form-row">
                    <label>Initial Viewport Mode
                      <select v-model="dispatchForm.mode_default">
                        <option value="card">[Card] Focused Step-by-Step Flow</option>
                        <option value="deck">[Deck] 10-Foot Lean-back Slide Deck</option>
                        <option value="prose">[Prose] 70ch Continuous Document</option>
                      </select>
                    </label>
                    <label>Expiration
                      <select v-model="dispatchForm.expires_in_hours">
                        <option :value="1">1 Hour</option>
                        <option :value="24">24 Hours (1 Day)</option>
                        <option :value="72">72 Hours (3 Days)</option>
                        <option :value="168">7 Days</option>
                        <option :value="0">Permanent (No expiry)</option>
                      </select>
                    </label>
                  </div>
                  <label class="checkbox-label">
                    <input v-model="dispatchForm.burn_after_read" type="checkbox" />
                    <span>Burn after read (dissolve into ether on first view or RSVP submission)</span>
                  </label>
                </div>

                <!-- Hero Animated BOB / Element Picker -->
                <div class="dispatch-form__col">
                  <div class="bob-header-row">
                    <label>Hero Animated BOB / Element</label>
                    <button class="wf-zen-subtle motif-toggle-btn" type="button" @click="showMotifGenerator = !showMotifGenerator">
                      <UIcon name="palette" /> {{ showMotifGenerator ? 'Hide Vector Generator' : 'Generate Vector Motif' }}
                    </button>
                  </div>

                  <!-- Vector Motif Generator Drawer -->
                  <div v-if="showMotifGenerator" class="motif-generator-box">
                    <span class="motif-box-title">Dot Lattice Vector Generator</span>
                    <div class="form-row">
                      <label>Motif
                        <select v-model="selectedMotif">
                          <option value="zen_envelope">Zen Sovereign Envelope</option>
                          <option value="teletext_pulse">Teletext Diamond Pulse</option>
                          <option value="cosmic_orbiter">Cosmic Celestial Orbiter</option>
                          <option value="signal_beacon">Sovereign Signal Beacon</option>
                        </select>
                      </label>
                      <label>Palette
                        <select v-model="selectedMotifPalette">
                          <option value="teletext_ceefax">Teletext Ceefax (8 Colors)</option>
                          <option value="terminal_green">Terminal Green</option>
                        </select>
                      </label>
                    </div>
                    <button class="wf-zen-primary motif-gen-btn" type="button" :disabled="generatingBob" @click="generateVectorBob">
                      <UIcon name="auto_awesome" /> {{ generatingBob ? 'Quantizing...' : 'Generate &amp; Set as Hero' }}
                    </button>
                  </div>

                  <div class="bob-picker">
                    <div
                      class="bob-option"
                      :class="{ 'bob-option--selected': !dispatchForm.hero_gif_name }"
                      @click="dispatchForm.hero_gif_name = ''"
                    >
                      <div class="bob-placeholder">None</div>
                      <span class="bob-label">No Hero</span>
                    </div>
                    <div
                      v-for="bob in catalogBobs"
                      :key="bob.id"
                      class="bob-option"
                      :class="{ 'bob-option--selected': dispatchForm.hero_gif_name === bob.asset_path }"
                      @click="dispatchForm.hero_gif_name = bob.asset_path"
                    >
                      <img :src="bob.preview_url || ('/api/dispatch/catalog/asset/' + bob.asset_path)" :alt="bob.name" class="bob-thumb" />
                      <span class="bob-label">{{ bob.name }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Dispatch Markdown Content Preview / Edit -->
              <div class="dispatch-content-field">
                <div class="field-header">
                  <label>Dispatch Story Markdown (defaults to active binder draft)</label>
                  <button class="wf-zen-subtle" type="button" @click="dispatchForm.story_markdown = editableDraft">
                    <UIcon name="refresh" /> Reset from Current Draft
                  </button>
                </div>
                <textarea
                  v-model="dispatchForm.story_markdown"
                  rows="6"
                  class="dispatch-textarea"
                  placeholder="Enter story markdown with --- card breaks and ? [ ] RSVP choice blocks..."
                />
              </div>

              <div class="dispatch-actions">
                <button
                  class="wf-zen-primary"
                  type="button"
                  :disabled="creatingDispatch || !dispatchForm.title.trim()"
                  @click="createBinderDispatch"
                >
                  <UIcon name="send" />
                  {{ creatingDispatch ? 'Creating Dispatch...' : 'Generate Sovereign Dispatch Token' }}
                </button>
              </div>
            </div>

            <!-- Existing Dispatches for this Binder -->
            <div class="binder-dispatches-list">
              <div class="dispatches-header">
                <h5>Active Sovereign Dispatches for this Binder ({{ binderDispatches.length }})</h5>
                <button class="wf-zen-subtle" type="button" @click="loadBinderDispatches">
                  <UIcon name="refresh" /> Refresh
                </button>
              </div>

              <div v-if="binderDispatches.length === 0" class="empty-hint">
                No interactive dispatches published for this binder yet. Click "New Dispatch" above to generate a shareable token.
              </div>

              <div v-for="disp in binderDispatches" :key="disp.id" class="dispatch-item-card">
                <div class="dispatch-item-main">
                  <div class="dispatch-item-info">
                    <div class="dispatch-item-title-row">
                      <strong>{{ disp.title }}</strong>
                      <span class="dispatch-mode-tag">Mode: {{ disp.mode_default }}</span>
                      <span v-if="disp.burn_after_read" class="dispatch-burn-tag">🔥 Burn After Read</span>
                      <span v-if="disp.is_expired" class="dispatch-expired-tag">Expired</span>
                    </div>
                    <div class="dispatch-item-meta">
                      <span>Token: <code>{{ disp.token }}</code></span>
                      <span>Created: {{ new Date(disp.created_at).toLocaleDateString() }}</span>
                      <span v-if="disp.expires_at">Expires: {{ new Date(disp.expires_at).toLocaleDateString() }}</span>
                      <span>Views: {{ disp.views_count || 0 }}</span>
                    </div>
                  </div>

                  <div class="dispatch-item-actions">
                    <a :href="'/p/' + disp.token" target="_blank" class="wf-zen-secondary action-btn" title="Open Guest Interactive Story">
                      <UIcon name="open_in_new" /> Open Story (/p/{{ disp.token }})
                    </a>
                    <a :href="'/api/dispatch/preview-email/' + disp.id" target="_blank" class="wf-zen-secondary action-btn" title="View Prose HTML Email">
                      <UIcon name="mail" /> Preview Email
                    </a>
                    <button
                      class="wf-zen-secondary action-btn"
                      type="button"
                      :disabled="exportingOfflineId === disp.id"
                      @click="exportOffline(disp.id)"
                      title="Export Standalone Offline HTML and signed .capsule"
                    >
                      <UIcon name="download" />
                      {{ exportingOfflineId === disp.id ? 'Exporting...' : 'Export Offline' }}
                    </button>
                    <button
                      class="wf-zen-secondary action-btn"
                      type="button"
                      @click="toggleResponsesLedger(disp.id)"
                    >
                      <UIcon name="ballot" />
                      RSVPs ({{ (disp.responses && disp.responses.length) || (responsesByDispatch[disp.id] && responsesByDispatch[disp.id].length) || 0 }})
                    </button>
                  </div>
                </div>

                <!-- Responses Ledger Drawer -->
                <div v-if="activeResponseDispatchId === disp.id" class="responses-ledger">
                  <div class="ledger-header-row">
                    <h6>RSVP &amp; Response Ledger ({{ responsesByDispatch[disp.id]?.length || 0 }} submissions)</h6>
                    <div class="ledger-header-actions">
                      <label class="sync-reminders-checkbox" title="Automatically push converted task to Apple Reminders under this Binder's list">
                        <input type="checkbox" v-model="syncToRemindersOnTaskCreation" />
                        <span>Apple Reminders Sync</span>
                      </label>
                      <label class="wf-zen-subtle ingest-file-btn" title="Ingest offline response JSON file into Activity Pod">
                        <UIcon name="file_upload" /> Ingest Offline File
                        <input type="file" accept=".json" @change="handleUploadResponseFile($event, disp.id)" style="display:none;" />
                      </label>
                    </div>
                  </div>
                  <div v-if="!responsesByDispatch[disp.id] || responsesByDispatch[disp.id].length === 0" class="empty-hint">
                    No responses or RSVP submissions received yet.
                  </div>
                  <table v-else class="responses-table">
                    <thead>
                      <tr>
                        <th>Respondent / Attendee</th>
                        <th>Status</th>
                        <th>Email / Note</th>
                        <th>Form Responses</th>
                        <th>Timestamp</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(resp, rIdx) in responsesByDispatch[disp.id]" :key="rIdx">
                        <td><strong>{{ resp.name || resp.attendee_name || 'Anonymous' }}</strong></td>
                        <td>
                          <span class="status-pill" :class="'status-' + (resp.status || 'received')">
                            {{ resp.status || 'Received' }}
                          </span>
                        </td>
                        <td>{{ resp.email || resp.notes || '-' }}</td>
                        <td>
                          <div v-if="resp.answers" class="answers-summary">
                            <span v-for="(val, q) in resp.answers" :key="q" class="answer-item">
                              <code>{{ q }}</code>: {{ val }}
                            </span>
                          </div>
                          <span v-else>-</span>
                        </td>
                        <td class="time-col">{{ new Date(resp.timestamp || resp.created_at || Date.now()).toLocaleTimeString() }}</td>
                        <td class="action-col">
                          <span v-if="resp.task_id" class="task-badge" :title="'Linked Sovereign Task: ' + resp.task_id">
                            <UIcon name="task_alt" /> Linked
                          </span>
                          <button
                            v-else
                            class="wf-zen-subtle create-task-btn"
                            :disabled="creatingTaskIndex === `${disp.id}-${rIdx}`"
                            @click="convertRsvpToTask(disp.id, rIdx)"
                            title="Convert RSVP into sovereign .tasker task &amp; optionally sync to Apple Reminders"
                          >
                            <UIcon name="add_task" />
                            {{ creatingTaskIndex === `${disp.id}-${rIdx}` ? 'Converting...' : 'Create Task' }}
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

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
            <div v-if="!activeBinder.editions || activeBinder.editions.length === 0" class="empty-hint">
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

      <!-- Add Decision Modal -->
      <div v-if="showAddDecisionModal" class="modal-backdrop" @click.self="showAddDecisionModal = false">
        <div class="modal-card">
          <header class="modal-header">
            <h3>Record Architectural Decision</h3>
            <button type="button" @click="showAddDecisionModal = false"><UIcon name="close" /></button>
          </header>
          <div class="modal-body">
            <label>Decision Title
              <input v-model="newDecision.title" type="text" placeholder="e.g. Use local mDNS over centralized DNS" />
            </label>
            <label>Status
              <select v-model="newDecision.status" class="binder-select">
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
                <option value="superseded">Superseded</option>
              </select>
            </label>
            <label>Rationale / Architecture Context
              <textarea v-model="newDecision.rationale" rows="3" placeholder="Why this option was chosen or rejected..." />
            </label>
          </div>
          <footer class="modal-footer">
            <button class="wf-zen-secondary" type="button" @click="showAddDecisionModal = false">Cancel</button>
            <button class="wf-zen-primary" type="button" :disabled="!newDecision.title.trim()" @click="addDecision">
              Save Decision
            </button>
          </footer>
        </div>
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
  { id: "decisions", label: "Decisions Log" },
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
const authorisingRun = ref(false);
const auditing = ref(false);
const auditReport = ref<any>(null);
const editorFont = ref<"serif" | "sans" | "mono">("serif");

const errorMessage = ref("");
const successMessage = ref("");
const conflictDetected = ref(false);

const editableDraft = ref("");
const loadedBaseHash = ref("");
const reviewerNotes = ref("");
const publicationReceipt = ref<any>(null);

const showDispatchCreator = ref(false);
const creatingDispatch = ref(false);
const catalogBobs = ref<any[]>([]);
const binderDispatches = ref<any[]>([]);
const responsesByDispatch = ref<Record<string, any[]>>({});
const activeResponseDispatchId = ref<string | null>(null);
const showMotifGenerator = ref(false);
const selectedMotif = ref("zen_envelope");
const selectedMotifPalette = ref("teletext_ceefax");
const generatingBob = ref(false);
const exportingOfflineId = ref<string | null>(null);
const syncToRemindersOnTaskCreation = ref(true);
const creatingTaskIndex = ref<string | null>(null);
const dispatchForm = ref({
  title: "",
  lead_text: "",
  story_markdown: "",
  hero_gif_name: "",
  mode_default: "card",
  expires_in_hours: 24,
  burn_after_read: false,
});

const showCreateModal = ref(false);
const newBinder = ref({
  id: "",
  title: "",
  outcome: "",
  audience: "General",
});

const showAddDecisionModal = ref(false);
const newDecision = ref({
  title: "",
  status: "accepted",
  rationale: "",
});

const fileInputRef = ref<HTMLInputElement | null>(null);

const wordCount = computed(() => {
  if (!editableDraft.value) return 0;
  const words = editableDraft.value.trim().split(/\s+/);
  return words[0] === "" ? 0 : words.length;
});

const readingTimeMinutes = computed(() => {
  return Math.ceil(wordCount.value / 200) || 1;
});

function getStageBadge(stageId: string): string {
  if (!activeBinder.value) return "";
  if (stageId === "sources") return String(activeBinder.value.sources?.length || 0);
  if (stageId === "plan") return String(activeBinder.value.requirements?.length || 0);
  if (stageId === "decisions") return String(activeBinder.value.decisions?.length || 0);
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
    if (!dispatchForm.value.story_markdown) {
      dispatchForm.value.story_markdown = editableDraft.value;
    }
    loadedBaseHash.value = data.binder.draft_sha256 || "";
    await loadBinderDispatches();
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

async function authoriseRun() {
  if (!selectedBinderId.value) return;
  authorisingRun.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/authorise`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        network_allowed: false,
        run_budget: { max_iterations: 10, max_token_budget: 100000 },
      }),
    });
    if (!res.ok) throw new Error(`Authorisation failed (${res.status})`);
    successMessage.value = "Run authorized with budget receipts (max 10 iterations).";
    await loadActiveBinder();
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    authorisingRun.value = false;
  }
}

async function resumeRun() {
  if (!selectedBinderId.value) return;
  runningAssembly.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/resume`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`Resume failed (${res.status})`);
    const data = await res.json();
    activeBinder.value = data.binder;
    editableDraft.value = data.binder.draft || "";
    loadedBaseHash.value = data.binder.draft_sha256 || "";
    successMessage.value = "Resumed and reconciled from last durable checkpoint.";
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    runningAssembly.value = false;
  }
}

async function addDecision() {
  if (!selectedBinderId.value || !newDecision.value.title.trim()) return;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/decisions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newDecision.value),
    });
    if (!res.ok) throw new Error(`Recording decision failed (${res.status})`);
    showAddDecisionModal.value = false;
    newDecision.value = { title: "", status: "accepted", rationale: "" };
    successMessage.value = "Decision recorded cleanly in decisions.json ledger.";
    await loadActiveBinder();
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  }
}

function insertCitation(citationTag: string) {
  if (!citationTag) return;
  editableDraft.value += ` [${citationTag}]`;
  successMessage.value = `Citation [${citationTag}] inserted into draft.`;
  setTimeout(() => { successMessage.value = ""; }, 2500);
}

async function runAudit() {
  if (!selectedBinderId.value) return;
  auditing.value = true;
  errorMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/audit`);
    if (!res.ok) throw new Error(`Audit failed (${res.status})`);
    const data = await res.json();
    auditReport.value = data.audit;
    if (data.audit.passed) {
      successMessage.value = `Audit Passed: ${data.audit.coverage_percentage}% requirement coverage with provenance.`;
    } else {
      errorMessage.value = `Audit Warning: Missing requirements [${data.audit.missing_requirements?.join(", ")}]`;
    }
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    auditing.value = false;
  }
}

function downloadTextFile(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function exportGemini() {
  if (!selectedBinderId.value) return;
  errorMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/export/gemini`);
    if (!res.ok) throw new Error(`Gemini export failed (${res.status})`);
    const data = await res.json();
    downloadTextFile(`${selectedBinderId.value}_gemini_notebook.md`, data.package.content);
    successMessage.value = `Exported Gemini Notebook with ${data.package.sources_count} sources & footnotes.`;
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  }
}

async function exportObsidian() {
  if (!selectedBinderId.value) return;
  errorMessage.value = "";
  try {
    const res = await fetch(`/api/binder/${encodeURIComponent(selectedBinderId.value)}/export/obsidian`);
    if (!res.ok) throw new Error(`Obsidian export failed (${res.status})`);
    const data = await res.json();
    downloadTextFile(`${selectedBinderId.value}_Index.md`, data.content);
    successMessage.value = `Generated Obsidian index with [[WikiLinks]] (${data.index_path}).`;
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  }
}

async function loadElementCatalog() {
  try {
    const res = await fetch("/api/dispatch/catalog");
    if (!res.ok) return;
    const data = await res.json();
    catalogBobs.value = data.bobs || [];
  } catch (e) {
    // Non-critical background catalog load
  }
}

async function loadBinderDispatches() {
  if (!selectedBinderId.value) {
    binderDispatches.value = [];
    return;
  }
  try {
    const res = await fetch(`/api/dispatch/by-binder/${encodeURIComponent(selectedBinderId.value)}`);
    if (!res.ok) return;
    const data = await res.json();
    binderDispatches.value = data.dispatches || [];
  } catch (e) {
    // Non-critical background load
  }
}

async function createBinderDispatch() {
  if (!dispatchForm.value.title.trim() || !selectedBinderId.value) return;
  creatingDispatch.value = true;
  errorMessage.value = "";
  try {
    const payload = {
      binder_id: selectedBinderId.value,
      title: dispatchForm.value.title.trim(),
      lead_text: dispatchForm.value.lead_text.trim(),
      story_markdown: dispatchForm.value.story_markdown || editableDraft.value,
      hero_gif_name: dispatchForm.value.hero_gif_name || null,
      mode_default: dispatchForm.value.mode_default,
      burn_after_read: dispatchForm.value.burn_after_read,
      expires_in_seconds: dispatchForm.value.expires_in_hours > 0 ? dispatchForm.value.expires_in_hours * 3600 : null,
    };
    const res = await fetch("/api/dispatch/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `Dispatch creation failed (${res.status})`);
    }
    const data = await res.json();
    successMessage.value = `Sovereign dispatch staged! Story URL: ${data.story_url}`;
    showDispatchCreator.value = false;
    dispatchForm.value = {
      title: "",
      lead_text: "",
      story_markdown: editableDraft.value,
      hero_gif_name: "",
      mode_default: "card",
      expires_in_hours: 24,
      burn_after_read: false,
    };
    await loadBinderDispatches();
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    creatingDispatch.value = false;
  }
}

async function toggleResponsesLedger(dispatchId: string) {
  if (activeResponseDispatchId.value === dispatchId) {
    activeResponseDispatchId.value = null;
    return;
  }
  activeResponseDispatchId.value = dispatchId;
  try {
    const res = await fetch(`/api/dispatch/responses/${encodeURIComponent(dispatchId)}`);
    if (!res.ok) return;
    const data = await res.json();
    responsesByDispatch.value = {
      ...responsesByDispatch.value,
      [dispatchId]: data.responses || [],
    };
  } catch (e) {
    // Non-critical
  }
}

async function generateVectorBob() {
  generatingBob.value = true;
  errorMessage.value = "";
  try {
    const res = await fetch("/api/dispatch/generate-bob", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        motif: selectedMotif.value,
        palette_id: selectedMotifPalette.value,
        steps: 4,
        delay_ms: 100,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `BOB generation failed (${res.status})`);
    }
    const data = await res.json();
    dispatchForm.value.hero_gif_name = data.asset_name;
    // Add to catalog items if not present
    if (!catalogBobs.value.some((b: any) => b.asset_path === data.asset_name)) {
      catalogBobs.value.unshift({
        id: data.asset_name,
        name: data.asset_name,
        asset_path: data.asset_name,
        preview_url: data.asset_url,
      });
    }
    successMessage.value = `Vector BOB generated on 4×4 dot lattice: ${data.asset_name} (${data.gif_size_bytes} bytes)`;
    showMotifGenerator.value = false;
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    generatingBob.value = false;
  }
}

async function exportOffline(dispatchId: string) {
  exportingOfflineId.value = dispatchId;
  errorMessage.value = "";
  try {
    const res = await fetch(`/api/dispatch/export-offline/${encodeURIComponent(dispatchId)}`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `Offline export failed (${res.status})`);
    }
    const data = await res.json();
    successMessage.value = `Offline bundle ready: ${data.standalone_html_path}`;
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    exportingOfflineId.value = null;
  }
}

async function handleUploadResponseFile(event: Event, dispatchId: string) {
  const target = event.target as HTMLInputElement;
  if (!target.files || target.files.length === 0) return;
  const file = target.files[0];
  try {
    const text = await file.text();
    const payload = JSON.parse(text);
    const res = await fetch("/api/dispatch/inbox/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || `Ingestion failed (${res.status})`);
    }
    successMessage.value = `Offline response from ${payload.name || 'guest'} ingested peacefully into Activity Pod & ledger!`;
    await toggleResponsesLedger(dispatchId);
  } catch (e: any) {
    errorMessage.value = `Failed to ingest response file: ${e.message || e}`;
  } finally {
    target.value = "";
  }
}

async function convertRsvpToTask(dispatchId: string, rsvpIndex: number) {
  creatingTaskIndex.value = `${dispatchId}-${rsvpIndex}`;
  errorMessage.value = "";
  try {
    const res = await fetch(`/api/dispatch/${encodeURIComponent(dispatchId)}/rsvp/${rsvpIndex}/task`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        binder: activeBinder.value?.name || "Sandbox",
        sync_apple_reminders: syncToRemindersOnTaskCreation.value,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Failed to convert RSVP to task");
    }
    const data = await res.json();
    if (responsesByDispatch.value[dispatchId] && responsesByDispatch.value[dispatchId][rsvpIndex]) {
      responsesByDispatch.value[dispatchId][rsvpIndex].task_id = data.task_id;
    }
    successMessage.value = `Created sovereign task: ${data.task_id}${data.reminders_sync?.ok ? ' & synced to Apple Reminders' : ''}`;
  } catch (e: any) {
    errorMessage.value = e.message || String(e);
  } finally {
    creatingTaskIndex.value = null;
  }
}

onMounted(() => {
  void fetchBinders();
  void loadElementCatalog();
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

/* Zen Lite Toolbar & Editor Styles */
.zen-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.zen-typography-toggles {
  display: inline-flex;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.25);
  padding: 2px;
  gap: 2px;
}

.zen-pill {
  border: none;
  background: transparent;
  color: var(--text-muted, #94a3b8);
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.zen-pill:hover {
  color: var(--text-primary, #f8fafc);
}

.zen-pill--active {
  background: #38bdf8;
  color: #0f172a;
  font-weight: 600;
}

.zen-stats {
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
}

.zen-citation-chips {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.citation-hint {
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
}

.citation-chip-btn {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 4px;
  padding: 0.15rem 0.45rem;
  font-family: monospace;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.citation-chip-btn:hover {
  background: rgba(56, 189, 248, 0.3);
}

.audit-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
}

.audit-banner--passed {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.4);
  color: #22c55e;
}

.audit-banner--warn {
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.4);
  color: #eab308;
}

.draft-editor-container {
  display: flex;
  justify-content: center;
  width: 100%;
}

.draft-textarea--serif {
  font-family: "Georgia", "Cambria", "Times New Roman", serif;
  font-size: 1.05rem;
  line-height: 1.7;
  max-width: 72ch;
}

.draft-textarea--sans {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 1rem;
  line-height: 1.6;
  max-width: 72ch;
}

.draft-textarea--mono {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  max-width: 80ch;
}

/* Decisions Log Styles */
.decisions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.decisions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.decision-card {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.decision-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.decision-id {
  font-family: monospace;
  font-weight: 700;
  color: #38bdf8;
  font-size: 0.8rem;
}

.decision-status {
  font-size: 0.7rem;
  text-transform: uppercase;
  font-weight: 600;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.decision-status--accepted {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.decision-status--rejected {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.decision-status--superseded {
  background: rgba(148, 163, 184, 0.2);
  color: #94a3b8;
}

.decision-rationale {
  font-size: 0.85rem;
  color: var(--text-secondary, #cbd5e1);
  line-height: 1.4;
}

.decision-time {
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
}

/* Universal Export Bridges Styles */
.universal-exports-card {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.universal-exports-card__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.universal-exports-card__header h4 {
  margin: 0;
  font-size: 1rem;
}

.universal-exports-card__header p {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
}

.export-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* Sovereign Dispatch Studio Styles */
.dispatch-studio-card {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.dispatch-studio-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.dispatch-studio-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.dispatch-studio-title h4 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary, #f8fafc);
}

.dispatch-studio-title p {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
}

.dispatch-form {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.dispatch-form__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 768px) {
  .dispatch-form__grid {
    grid-template-columns: 1fr;
  }
}

.dispatch-form__col {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.dispatch-form__col label {
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.dispatch-form__col input[type="text"],
.dispatch-form__col select {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 4px;
  padding: 0.5rem 0.75rem;
  color: var(--text-primary, #f8fafc);
  font-size: 0.875rem;
}

.form-row {
  display: flex;
  gap: 0.75rem;
}

.form-row > * {
  flex: 1;
}

.checkbox-label {
  display: flex !important;
  flex-direction: row !important;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--text-secondary, #cbd5e1);
  margin-top: 0.25rem;
}

.bob-picker {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 0.5rem;
  max-height: 180px;
  overflow-y: auto;
  padding: 0.5rem;
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 6px;
}

.bob-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.4rem;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.03);
  transition: all 0.15s ease;
}

.bob-option:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(56, 189, 248, 0.4);
}

.bob-option--selected {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
}

.bob-thumb {
  width: 48px;
  height: 48px;
  object-fit: contain;
  image-rendering: pixelated;
}

.bob-placeholder {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
}

.bob-label {
  font-size: 0.7rem;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 72px;
  color: var(--text-secondary, #cbd5e1);
}

.dispatch-content-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.dispatch-content-field .field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dispatch-content-field label {
  font-size: 0.8rem;
  color: var(--text-muted, #94a3b8);
}

.dispatch-textarea {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 4px;
  padding: 0.6rem;
  color: var(--text-primary, #f8fafc);
  font-family: monospace;
  font-size: 0.85rem;
  line-height: 1.4;
  resize: vertical;
}

.dispatch-actions {
  display: flex;
  justify-content: flex-end;
}

.binder-dispatches-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.dispatches-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dispatches-header h5 {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-primary, #f8fafc);
}

.dispatch-item-card {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid var(--border-subtle, #334155);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.dispatch-item-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.dispatch-item-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.dispatch-item-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.dispatch-mode-tag, .dispatch-burn-tag, .dispatch-expired-tag {
  font-size: 0.7rem;
  padding: 0.1rem 0.35rem;
  border-radius: 3px;
  text-transform: uppercase;
}

.dispatch-mode-tag {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
}

.dispatch-burn-tag {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.dispatch-expired-tag {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
}

.dispatch-item-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
}

.dispatch-item-meta code {
  color: #38bdf8;
}

.dispatch-item-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.dispatch-item-actions .action-btn {
  font-size: 0.8rem;
  padding: 0.35rem 0.65rem;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.responses-ledger {
  border-top: 1px solid var(--border-subtle, #334155);
  padding-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.responses-ledger h6 {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary, #cbd5e1);
}

.responses-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.responses-table th, .responses-table td {
  padding: 0.4rem 0.6rem;
  text-align: left;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.responses-table th {
  color: var(--text-muted, #94a3b8);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.status-pill {
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-accepted, .status-yes, .status-attending {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.status-declined, .status-no {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.status-maybe, .status-received {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}

.answers-summary {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.answer-item {
  font-size: 0.75rem;
}

.answer-item code {
  color: var(--text-muted, #94a3b8);
}

.time-col {
  color: var(--text-muted, #94a3b8);
  font-size: 0.75rem;
  white-space: nowrap;
}

.ledger-header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sync-reminders-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: var(--text-muted, #94a3b8);
  cursor: pointer;
  user-select: none;
}

.sync-reminders-checkbox input {
  cursor: pointer;
  accent-color: #38bdf8;
}

.action-col {
  white-space: nowrap;
}

.task-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.create-task-btn {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.dispatch-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bob-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.motif-toggle-btn {
  font-size: 0.75rem;
  padding: 0.15rem 0.4rem;
}

.motif-generator-box {
  background: rgba(88, 166, 255, 0.06);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}

.motif-box-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent, #58a6ff);
  display: block;
  margin-bottom: 0.5rem;
}

.motif-gen-btn {
  margin-top: 0.5rem;
  width: 100%;
}

.ledger-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.ingest-file-btn {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px dashed var(--border, #30363d);
}

.ingest-file-btn:hover {
  border-color: var(--accent, #58a6ff);
  color: var(--accent, #58a6ff);
}
</style>
