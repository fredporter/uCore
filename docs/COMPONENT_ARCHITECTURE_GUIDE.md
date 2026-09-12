> Direction update — 12 September 2026: the [product refactor plan](UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md) and [Gemini handover](HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md) govern future work. Preserve useful features, UI and historical evidence below. Internal IDE/Dev Mode priorities and requirements to finish that program before independent product releases are superseded; current implementation descriptions are not target architecture or new release certification.

# uCore Component Architecture & Design System Guide

This guide details the frontend and backend component architecture for uCore, covering state management, the USX design system, GridCore rendering, and sovereign data boundaries.

---

## 1. Sovereign Frontend Architecture & State Management

uCore's user interface is built as a Vue 3 single-page progressive web application (PWA) with Pinia state management. Stores are strictly scoped to enforce sovereign multi-profile isolation and offline readiness.

### Core Pinia Stores

```
           ┌──────────────────────────────────────────────┐
           │             useIdentityStore                 │
           │  - user_id, codeword, install_id             │
           │  - authenticated, activeProfile, profiles    │
           └───────┬───────────────────────────────┬──────┘
                   │ activeProfileId               │ activeProfileId
                   ▼                               ▼
    ┌─────────────────────────────┐ ┌─────────────────────────────┐
    │      useSettingsStore       │ │        useChatStore         │
    │  - local & /api/user/prefs  │ │  - assistui-conversations-  │
    │  - themeMode: dark|light|auto │ │    ${profileId}             │
    │  - fontStyle, size, palette │ │  - partitioned history api  │
    └─────────────────────────────┘ └─────────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────┐ ┌─────────────────────────────┐
    │     useWorkspaceStore       │ │    useDeveloperChatStore    │
    │  - file tree, dirty files   │ │  - ACP sessions, tool-calls │
    │  - open tabs, active file   │ │  - approvals, operation log │
    └─────────────────────────────┘ └─────────────────────────────┘
```

1. **`useIdentityStore` (`src/stores/identity.ts`)**:
   - Manages machine identity, local user codeword, cryptographic installation ID, and profile switching.
   - Communicates with `/api/identity/me`, `/switch`, `/login`, and `/logout`.
   - Clears session tokens and sensitive credentials on logout; prevents data bleeding between profiles.

2. **`useSettingsStore` (`src/stores/settings.ts`)**:
   - Persists user preferences locally with fallback to `/api/user/preferences`.
   - Supports theme modes (`dark`, `light`, `auto`), font styles (`inter`, `system`, `mono`), font sizing (12-24px), and palettes (`default`, `ocean`, `forest`, `sunset`).
   - Debounces synchronization to the backend preference store with a 250ms window.
   - Profile-scoped system configurations remain managed via `SettingsManager` on `/api/system/settings`.

3. **`useChatStore` (`src/stores/chat.ts`)**:
   - Scopes conversation persistence key by active profile (`assistui-conversations-${profileId}`).
   - Communicates with `/api/chat/history?profile=${profileId}`.
   - Clear history only purges the active profile's records.

4. **`useWorkspaceStore` (`src/stores/workspace.ts`)**:
   - Manages open files, dirty state, file tree navigation, and unsaved changes confirmation.

5. **`useDeveloperChatStore` (`src/stores/developerChat.ts`)**:
   - Connects to Nanocoder ACP streaming events via server-sent events (`/api/developer/conversations/{id}/events`).
   - Handles structured tool calls, approval barriers, diff previews, and plan updates.

---

## 2. USX Design System & Recipe Hierarchy

The User Sovereign Experience (USX) design system provides a clear, high-contrast, accessible UI across all standard application surfaces.

### Design Tokens & Layout Rules
- **Themes**: Strict Light and Dark modes (`data-theme="light"` / `data-theme="dark"`).
- **Typography**: Inter (UI elements and sans text), Merriweather (long-form prose reading), JetBrains Mono (code blocks and terminal readouts).
- **Contrast**: Conforms to WCAG AA minimum 4.5:1 contrast ratios.
- **Recipe Gallery**: Visual showroom (`/recipes`) displaying vetted patterns:
  - Header cards, KPI metric displays, status tables, responsive forms.
  - Interactive authoring recipes (`AuthoringRecipeView`).
  - System status pages and alert banners.

---

## 3. GridCore Teletext & Terminal Engine

GridCore is uCore's high-performance, monospace retro-canvas layout engine used exclusively for teletext, low-bandwidth feeds, and retro terminal interfaces (`/ucode` and `/ucode?tab=teletext`).

> [!IMPORTANT]
> **Strict Lane Separation**: GridCore layout mechanics and USX design components must never be crossed over. USX governs modern standard surfaces; GridCore governs fixed-grid character-cell surfaces.

### Architecture
- **Glyph Atlas (`glyph-atlas.ts`)**: Generates and caches monospace bitmap glyphs for rapid canvas rendering.
- **Layer Map (`layer-map.ts`)**: Manages character cells, background attributes, and foreground colors across 40x24 (teletext) or 80x25 (terminal) grids.
- **Render Seed (`render-seed.ts`)**: Deterministic procedural text layout for status pages, monitors, and telemetry.
- **Teletext Catalogue (`catalogue.ts`)**: Fixed page numbers (e.g. `P100`, `P200`) mapped to operational dashboards.

---

## 4. Bangle Editor Molecule Architecture

The Bangle Editor decomposes authoring into reusable atomic and molecular Vue components under `src/skills/molecules/editor/`:

```
src/skills/molecules/editor/
├── MarkdownEditor.vue             # Core ProseMirror/Bangle wrapper
├── EnhancedBangleToolbar.vue      # Sticky/responsive formatting toolbar
├── FrontmatterEditor.vue          # Interactive YAML frontmatter pill editor
├── CitationModal.vue              # Academic/web citation modal
├── CombineResearchModal.vue       # Multi-note research aggregator modal
└── WorkspaceTreeNode.vue          # Recursive file tree navigation node
```

### Component Details
- **`MarkdownEditor.vue`**: Integrates rich ProseMirror schema, handles keyboard shortcuts (`Cmd+S`, `Cmd+J`), and synchronizes markdown text with the workspace store.
- **`EnhancedBangleToolbar.vue`**: Provides formatting buttons, headings, lists, tables, and responsive dropdowns on mobile viewports.
- **`FrontmatterEditor.vue`**: Interactively modifies metadata without raw YAML editing; leverages `parseDocument` and `serializeDocument`.
- **`CitationModal.vue`**: Formats APA, MLA, Chicago, Markdown, and uKnowledge provenance citations with real-time preview.
- **`CombineResearchModal.vue`**: Aggregates selected markdown notes into synthesized research outputs.

---

## 5. Backend Storage Boundary & APIs

All backend services run locally under Python (aiohttp) and enforce the strict storage boundary:

- **Storage Location**: All runtime mutable state belongs under `UDOS_HOME` (`settings.data_dir`, default `~/Code/.udos`).
- **Policy Invariant**: Zero writes to `$HOME` root, legacy application state directories, or unapproved paths. Checked via `python3 scripts/check_home_path_policy.py`.
- **Zero Cloud Spend**: Strictly local models (Ollama/Nanocoder) and local data stores.

### Endpoints
- **Identity API (`/api/identity/*`)**: `/me`, `/switch`, `/login`, `/logout`, `/profile`.
- **System API (`/api/system/*`)**: `/settings` (scoped reading and writing to `system_settings.json`).
- **Chat History API (`/api/chat/*`)**: `/history` (stores profile-partitioned histories under `{data_dir}/chat_history/{user}_{profile}.json`).
- **Developer Chat API (`/api/developer/*`)**: `/conversations`, `/conversations/{id}/message`, `/events`, `/operations/{id}/approve`, `/deny`.

---

## 6. Offline PWA Shell & Service Worker

The application utilizes Workbox via `vite-plugin-pwa` to enable seamless offline usability:

- **App Shell Pre-caching**: HTML, JavaScript bundles, CSS stylesheets, and web fonts (`Inter`, `Merriweather`, `Material Symbols`) are pre-cached on install.
- **Runtime Caching**:
  - Identity and user profile routes (`/api/identity/me`).
  - System settings (`/api/system/settings`).
- **Offline Indicator**: Surfaces an amber badge in the status bar when network connectivity is lost while maintaining local editing and auto-save capabilities.
