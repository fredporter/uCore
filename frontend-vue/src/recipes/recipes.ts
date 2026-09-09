/**
 * @module recipes/recipes
 * @description Canonical declarative recipe definitions for USX and GridCore.
 *
 * Models and engines do not write ad-hoc CSS. They emit structured recipe parameters
 * which are translated predictably into validated layout structures.
 */

export type RecipeParadigm = 'usx' | 'gridcore'

export interface BaseRecipe {
  id: string
  recipe: string
  paradigm: RecipeParadigm
  title: string
  description: string
  version: number
}

// ─── 1. USX: Task List Recipe ──────────────────────────────────────
export interface TaskListItem {
  id: string
  title: string
  subtitle?: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  badge?: string
  tags?: string[]
  timestamp?: string
}

export interface TaskListRecipe extends BaseRecipe {
  recipe: 'task-list'
  paradigm: 'usx'
  columns: 1
  collapsibleHistory: boolean
  items: TaskListItem[]
}

// ─── 2. USX: Prose Document Recipe ────────────────────────────────
export interface ProseDocumentRecipe extends BaseRecipe {
  recipe: 'prose-document'
  paradigm: 'usx'
  frontmatter: Record<string, string | number | boolean>
  title: string
  intro: string
  callouts: Array<{
    type: 'note' | 'tip' | 'important' | 'warning' | 'caution'
    title: string
    body: string
  }>
  tableData: {
    headers: string[]
    rows: string[][]
  }
  codeSnippet: {
    language: string
    code: string
  }
}

// ─── 3. USX: Card Matrix Recipe ───────────────────────────────────
export interface CardMatrixItem {
  id: string
  title: string
  description: string
  icon: string
  metric?: string
  tag?: string
  accent?: string
  actions?: Array<{ label: string; primary?: boolean }>
}

export interface CardMatrixRecipe extends BaseRecipe {
  recipe: 'card-matrix'
  paradigm: 'usx'
  cards: CardMatrixItem[]
}

// ─── 4. USX: Settings Form Recipe ─────────────────────────────────
export interface FormField {
  id: string
  label: string
  type: 'toggle' | 'select' | 'slider'
  value: boolean | string | number
  options?: string[]
  min?: number
  max?: number
  helpText?: string
}

export interface SettingsSection {
  id: string
  title: string
  fields: FormField[]
}

export interface SettingsFormRecipe extends BaseRecipe {
  recipe: 'settings-form'
  paradigm: 'usx'
  sections: SettingsSection[]
}

// ─── 5. USX: Story Format (Typeform Style) Recipe ────────────────
export interface StoryOption {
  id: string
  label: string
  shortcut?: string
  description?: string
}

export interface StoryQuestion {
  id: string
  headline: string
  subtext?: string
  type: 'single-choice' | 'multi-choice' | 'text' | 'scale'
  options?: StoryOption[]
  placeholder?: string
  required?: boolean
}

export interface StoryRecipe extends BaseRecipe {
  recipe: 'story-form'
  paradigm: 'usx'
  questions: StoryQuestion[]
  submitLabel?: string
}

// ─── 6. USX: System Page (S100 Diagnostic) Recipe ────────────────
export interface SystemPageRecipe extends BaseRecipe {
  recipe: 'system-page'
  paradigm: 'usx'
  code: string // e.g. "S100", "S101", "S300", "S500"
  icon: string
  heading: string
  summary: string
  steps: string[]
  suggestions: Array<{ label: string; to: string }>
  actions: Array<{ label: string; variant?: 'primary' | 'secondary' | 'danger'; action: string }>
  footnote: string
}

// ─── 7. USX: Alerts & Notification Suite Recipe ──────────────────
export interface AlertsRecipe extends BaseRecipe {
  recipe: 'alerts-suite'
  paradigm: 'usx'
  curtain: {
    visible: boolean
    severity: 'info' | 'warning' | 'critical' | 'success'
    title: string
    message: string
    actionLabel?: string
    dismissible: boolean
  }
  inlineAlerts: Array<{
    id: string
    severity: 'info' | 'warning' | 'critical' | 'success'
    title: string
    message: string
  }>
  toasts: Array<{
    id: string
    type: 'info' | 'success' | 'warning' | 'error'
    message: string
    actionLabel?: string
  }>
  dialog: {
    type: 'info' | 'warning' | 'critical' | 'success'
    title: string
    message: string
    confirmLabel: string
    cancelLabel?: string
  }
}

// ─── 8. GridCore: Teletext Mode 7 Recipe ──────────────────────────
export interface TeletextRecipe extends BaseRecipe {
  recipe: 'teletext-mode7'
  paradigm: 'gridcore'
  pageNumber: string
  magazine: string
  headerBanner: string
  lines: string[] // 24 lines of 40 columns
}

// ─── 9. GridCore: Terminal ANSI Recipe ────────────────────────────
export interface TerminalRecipe extends BaseRecipe {
  recipe: 'terminal-ansi'
  paradigm: 'gridcore'
  cols: number
  rows: number
  statusBar: string
  splitPanes: Array<{
    title: string
    width: string
    lines: string[]
  }>
}

export type AnyRecipe =
  | TaskListRecipe
  | ProseDocumentRecipe
  | CardMatrixRecipe
  | SettingsFormRecipe
  | StoryRecipe
  | SystemPageRecipe
  | AlertsRecipe
  | TeletextRecipe
  | TerminalRecipe

// ─── Sample Canonical Payloads ─────────────────────────────────────

export const SAMPLE_TASK_LIST: TaskListRecipe = {
  id: 'recipe-task-list-sample',
  recipe: 'task-list',
  paradigm: 'usx',
  version: 1,
  title: 'Active Workflow Missions',
  description: 'Strict single-column layout with status badges and collapsible history',
  columns: 1,
  collapsibleHistory: true,
  items: [
    {
      id: 'task-01',
      title: 'Dev Mode Readiness Gate Validation',
      subtitle: 'Enforce ExecutionContext, fail-closed executor selector, and budget reservations',
      status: 'completed',
      badge: 'Sprint 4A',
      tags: ['security', 'core'],
      timestamp: 'Just now',
    },
    {
      id: 'task-02',
      title: 'USX & GridCore Recipe Catalogue Showcase',
      subtitle: 'Build interactive surface gallery for Material 3 and Teletext layouts',
      status: 'in_progress',
      badge: 'Sprint 4B',
      tags: ['ui', 'recipes'],
      timestamp: 'In progress',
    },
    {
      id: 'task-03',
      title: 'Bangle Authoring & Frontmatter Round-Trip',
      subtitle: 'Validate YAML frontmatter parsing and responsive toolbar',
      status: 'pending',
      badge: 'Sprint 4C',
      tags: ['authoring', 'bangle'],
      timestamp: 'Queued',
    },
    {
      id: 'task-04',
      title: 'Host PIM Bridge & Snackbar Spool Migration',
      subtitle: 'Migrate reply spool to UDOS_HOME and prove Apple Notes sync slice',
      status: 'pending',
      badge: 'Sprint 4D',
      tags: ['snacks', 'macos'],
      timestamp: 'Queued',
    },
  ],
}

export const SAMPLE_PROSE_DOCUMENT: ProseDocumentRecipe = {
  id: 'recipe-prose-sample',
  recipe: 'prose-document',
  paradigm: 'usx',
  version: 1,
  title: 'Local-First Execution Contract Specification',
  description: 'GitHub-flavored typography with frontmatter metadata, callouts, tables, and code',
  frontmatter: {
    status: 'draft',
    owner: 'uCore',
    lane: 'everyday',
    cloudAllowed: false,
    version: '1.2.0',
  },
  intro: 'uDOS enforces deterministic execution first. Models interpret intent and propose structured recipes, but cannot execute arbitrary code or bypass boundaries.',
  callouts: [
    {
      type: 'note',
      title: 'Local-First Invariant',
      body: 'User scope tasks have a hard-zero cloud allowance. If Ollama is offline, language tasks fail closed without cloud fallback.',
    },
    {
      type: 'tip',
      title: 'Predictable Recipes',
      body: 'Never let models generate freeform CSS. Emit typed JSON recipe arguments referencing approved USX tokens.',
    },
    {
      type: 'important',
      title: 'Three Separate Permissions',
      body: 'Model permission, network permission, and file write permission are strictly decoupled in ExecutionContext.',
    },
  ],
  tableData: {
    headers: ['Lane', 'Default Engine', 'Network Scope', 'Cloud Spend'],
    rows: [
      ['Everyday Chat', 'Ollama (Local)', 'Offline', 'Denied ($0.00)'],
      ['Markdown / Binder', 'Parsers / Formatters', 'Local files only', 'Denied ($0.00)'],
      ['uCode BASIC', 'GridSmith / BBCSDL', 'Offline', 'Denied ($0.00)'],
      ['Dev Mode Workbench', 'NanoCoder ACP + Ollama', 'Scoped Git / Repo', 'Eligible with cap'],
    ],
  },
  codeSnippet: {
    language: 'typescript',
    code: `const context = new ExecutionContext({
  taskId: "mission-441",
  scope: "user",
  lane: "everyday",
  permittedPaths: ["docs/*.md"]
});

// Guaranteed $0.00 spend
await executorSelector.select(context);`,
  },
}

export const SAMPLE_CARD_MATRIX: CardMatrixRecipe = {
  id: 'recipe-card-matrix-sample',
  recipe: 'card-matrix',
  paradigm: 'usx',
  version: 1,
  title: 'Ecosystem Specialist Surfaces',
  description: 'Material 3 tonal elevation cards with icon badges, state layers, and action triggers',
  cards: [
    {
      id: 'surface-ucode',
      title: 'uCode Studio',
      description: 'Lattice algebra, BASIC/AMOS runtime, GridCore matrix canvas, and capsule packager.',
      icon: 'grid_view',
      metric: '188 Tests',
      tag: 'Core Product',
      actions: [{ label: 'Launch', primary: true }],
    },
    {
      id: 'surface-flow',
      title: 'uFlow Missions',
      description: 'Durable task workflows, approval checkpoints, and execution run receipts.',
      icon: 'account_tree',
      metric: 'Active',
      tag: 'Authority',
      actions: [{ label: 'Inspect', primary: true }],
    },
    {
      id: 'surface-knowledge',
      title: 'uKnowledge Vault',
      description: 'Filesystem-first Markdown vault, local semantic search, and citation provenance.',
      icon: 'menu_book',
      metric: 'Indexed',
      tag: 'Storage',
      actions: [{ label: 'Open', primary: true }],
    },
    {
      id: 'surface-snacks',
      title: 'Snackbar Native',
      description: 'macOS host integrations: Notes, Reminders, Mail VIP, and TCC permissions.',
      icon: 'storefront',
      metric: '8 Snacks',
      tag: 'Integrations',
      actions: [{ label: 'Configure', primary: false }],
    },
  ],
}

export const SAMPLE_SETTINGS_FORM: SettingsFormRecipe = {
  id: 'recipe-settings-sample',
  recipe: 'settings-form',
  paradigm: 'usx',
  version: 1,
  title: 'Ecosystem Runtime Preferences',
  description: 'Segmented controls, grouped toggles, and contextual disclosure',
  sections: [
    {
      id: 'sec-privacy',
      title: 'Local-First Privacy & Network',
      fields: [
        {
          id: 'opt-cloud-tier',
          label: 'Enable Frontier Cloud Inference',
          type: 'toggle',
          value: false,
          helpText: 'Strictly restricted to Developer Mode tasks with an explicit budget cap.',
        },
        {
          id: 'opt-network-mode',
          label: 'Default Network Policy',
          type: 'select',
          value: 'local_only',
          options: ['offline', 'local_only', 'named_connector', 'dev_scoped'],
          helpText: 'Controls socket and outbound HTTP requests across all runners.',
        },
      ],
    },
    {
      id: 'sec-display',
      title: 'Surface Display & Theme',
      fields: [
        {
          id: 'opt-theme',
          label: 'Theme Selection',
          type: 'select',
          value: 'Dark',
          options: ['Dark', 'Light', 'Teletext Mode 7', 'C64 Vintage', 'High Contrast'],
        },
        {
          id: 'opt-docked-hud',
          label: 'Docked Developer HUD Tab',
          type: 'toggle',
          value: true,
          helpText: 'Keep collapsible developer drawer docked to the viewport edge.',
        },
      ],
    },
  ],
}

export const SAMPLE_TELETEXT: TeletextRecipe = {
  id: 'recipe-teletext-sample',
  recipe: 'teletext-mode7',
  paradigm: 'gridcore',
  version: 1,
  title: 'Teletext Mode 7 (40x25 Matrix)',
  description: 'Fixed-pitch character cell grid with 7-color BBC Micro palette and block sixels',
  pageNumber: 'P100',
  magazine: 'uDOS CEEFAX',
  headerBanner: 'uDOS CEEFAX 100  Wed 09 Sep  17:55/26',
  lines: [
    '                                        ',
    ' \x1b[33m\x1b[1muDOS SYSTEM TELEMETRY INDEX\x1b[0m            ',
    ' \x1b[36m======================================\x1b[0m ',
    '                                        ',
    ' \x1b[32m101\x1b[0m \x1b[37mSYSTEM HEALTH & LOCAL RUNTIMES\x1b[0m    ',
    ' \x1b[32m102\x1b[0m \x1b[37mDEVELOPER WORKBENCH REVISIONS\x1b[0m    ',
    ' \x1b[32m103\x1b[0m \x1b[37mBUDGET & OLLAMA LOCAL INFERENCE\x1b[0m  ',
    ' \x1b[32m104\x1b[0m \x1b[37muCODE BASIC & AMOS CAPSULES\x1b[0m     ',
    '                                        ',
    ' \x1b[31m[HEADLINE]\x1b[0m                             ',
    ' \x1b[37mSPRINT 4B SURFACE SYSTEM ONLINE.\x1b[0m       ',
    ' \x1b[37mPREDICTABLE RECIPES LOCK DESIGN STYLE\x1b[0m  ',
    ' \x1b[37mACROSS ALL EXTENSIONS & CORE REPOS.\x1b[0m    ',
    '                                        ',
    ' \x1b[34m--------------------------------------\x1b[0m ',
    ' \x1b[33mSTATUS:\x1b[0m \x1b[32mALL 4 CANONICAL REPOS SYNCED\x1b[0m   ',
    ' \x1b[33mGATE:\x1b[0m   \x1b[32mDEV READINESS ACCEPTED (10/10)\x1b[0m ',
    '                                        ',
    '                                        ',
    '                                        ',
    ' \x1b[35mSELECT PAGE NUMBER OR PRESS RED/GREEN\x1b[0m  ',
    ' \x1b[31m[RED: INDEX]\x1b[0m \x1b[32m[GRN: NEXT]\x1b[0m \x1b[33m[YEL: HELP]\x1b[0m \x1b[36m[CYN: QUIT]\x1b[0m',
  ],
}

export const SAMPLE_TERMINAL: TerminalRecipe = {
  id: 'recipe-terminal-sample',
  recipe: 'terminal-ansi',
  paradigm: 'gridcore',
  version: 1,
  title: 'Terminal ANSI (80x25 Split-Curses)',
  description: 'Fixed 80-column monospace grid with box-drawing borders and split panes',
  cols: 80,
  rows: 25,
  statusBar: ' [uDOS-v3.0]  WORKSPACE: /Users/fredbook/Code  MODE: READINESS-VERIFIED',
  splitPanes: [
    {
      title: 'FILES (30 COLS)',
      width: '35%',
      lines: [
        '┌────────────────────────────┐',
        '│ 📁 uCore/                  │',
        '│   📄 execution_context.py  │',
        '│   📄 executor_selector.py  │',
        '│   📄 budget_manager.py     │',
        '│   📄 developer_chat.py     │',
        '│   📄 devMode.ts            │',
        '│ 📁 uCode/                  │',
        '│   📁 viewport-renderer/    │',
        '│   📁 gridcore/             │',
        '│ 📁 HomeNest/               │',
        '│   📄 RESET_PLAN.md         │',
        '└────────────────────────────┘',
      ],
    },
    {
      title: 'OPERATIONS LOG (50 COLS)',
      width: '65%',
      lines: [
        '┌──────────────────────────────────────────────┐',
        '│ [17:52:19] uCore: test_dev_readiness_gate: OK│',
        '│ [17:52:20] Provider selector: OLLAMA HEALTHY │',
        '│ [17:52:21] Budget check: user lane $0.00 OK  │',
        '│ [17:52:22] Commit 8a1237f: Clean tree anchor │',
        '│ [17:55:00] USX recipe catalogue initialized  │',
        '│ [17:55:02] Material 3 tonal elevation active │',
        '│ [17:55:04] GitHub prose typography loaded    │',
        '│ [17:55:06] Teletext Mode 7 sixel grid ready  │',
        '│ [17:55:08] Awaiting browser review inspection│',
        '└──────────────────────────────────────────────┘',
      ],
    },
  ],
}

export const SAMPLE_STORY_FORM: StoryRecipe = {
  id: 'recipe-story-sample',
  recipe: 'story-form',
  paradigm: 'usx',
  version: 1,
  title: 'Mission Intake Questionnaire (Typeform Style)',
  description: 'High-focus single-question slide layout with keyboard navigation and progress tracking',
  submitLabel: 'Launch Mission',
  questions: [
    {
      id: 'q1',
      headline: 'What is the primary target repository for this task?',
      subtext: 'uDOS boundaries enforce single-repo scope per execution context.',
      type: 'single-choice',
      required: true,
      options: [
        { id: 'ucore', label: 'uCore', shortcut: '1', description: 'UI & Service Host (Aiohttp + Vue 3)' },
        { id: 'uflow', label: 'uFlow', shortcut: '2', description: 'Workflow & Task State Authority' },
        { id: 'ucode', label: 'uCode', shortcut: '3', description: 'GridCore Matrix & BASIC Runtime' },
        { id: 'uknowledge', label: 'uKnowledge', shortcut: '4', description: 'Local Markdown Knowledge Vault' },
      ],
    },
    {
      id: 'q2',
      headline: 'Which execution lane should be assigned?',
      subtext: 'Lane controls provider eligibility, budget caps, and network boundaries.',
      type: 'single-choice',
      required: true,
      options: [
        { id: 'everyday', label: 'Everyday (User Scope)', shortcut: 'A', description: 'Hard-zero cloud spend, local Ollama only, offline-safe' },
        { id: 'dev', label: 'Developer Mode', shortcut: 'B', description: 'Permits atomic budget reservations up to $0.10/task' },
      ],
    },
    {
      id: 'q3',
      headline: 'Specify non-goals and explicit boundaries for this execution',
      subtext: 'These constraints are injected directly into the LLM system prompt to prevent scope creep.',
      type: 'text',
      placeholder: 'e.g. Do NOT touch database migrations, do NOT introduce new top-level directories...',
      required: false,
    },
  ],
}

export const SAMPLE_SYSTEM_PAGE: SystemPageRecipe = {
  id: 'recipe-system-page-sample',
  recipe: 'system-page',
  paradigm: 'usx',
  version: 1,
  title: 'S100 System Diagnostic Fallback',
  description: 'Canonical system error, diagnostic status, and specification sheet pattern',
  code: 'S100',
  icon: 'search_off',
  heading: 'Resource Specification Not Found',
  summary: 'The requested system capability or route is unavailable in the current runtime state.',
  steps: [
    'Confirm the owning service is running under uCore supervision on port 8484.',
    'Check local-first boundaries: user scope denies external network requests.',
    'Review recent commits or configuration manifests in the developer workbench.',
  ],
  suggestions: [
    { label: 'System Overview', to: '/system' },
    { label: 'Developer Workbench', to: '/developer' },
    { label: 'Service Health Monitor', to: '/system/s500' },
    { label: 'Surfaces & Recipes', to: '/recipes' },
  ],
  actions: [
    { label: 'Go Back', variant: 'secondary', action: 'back' },
    { label: 'Retry Diagnosis', variant: 'primary', action: 'retry' },
    { label: 'Return Home', variant: 'secondary', action: 'home' },
  ],
  footnote: 'Error S100. Diagnostic fallback generated locally without network dependencies.',
}

export const SAMPLE_ALERTS_SUITE: AlertsRecipe = {
  id: 'recipe-alerts-sample',
  recipe: 'alerts-suite',
  paradigm: 'usx',
  version: 1,
  title: 'USX Alerts & Notification Suite',
  description: 'Comprehensive notification patterns: Slide-down Curtain, Toasts, Inline Banners, and Modal Dialogs',
  curtain: {
    visible: true,
    severity: 'warning',
    title: 'Developer Mode Active',
    message: 'Local Ollama is operating. Paid frontier models require an active task reservation.',
    actionLabel: 'Review Budget',
    dismissible: true,
  },
  inlineAlerts: [
    {
      id: 'alert-info',
      severity: 'info',
      title: 'Local First Invariant',
      message: 'User scope tasks have a hard-zero cloud allowance and run strictly offline.',
    },
    {
      id: 'alert-success',
      severity: 'success',
      title: 'Dev Readiness Gate Cleared',
      message: 'All 10 boundary tests passed. Path traversal and provider escalation blocked.',
    },
    {
      id: 'alert-warning',
      severity: 'warning',
      title: 'Budget Reservation Limit Approaching',
      message: 'Active session spend is at $0.08 of the $0.10 task cap.',
    },
    {
      id: 'alert-critical',
      severity: 'critical',
      title: 'Out-of-Scope Write Attempt Blocked',
      message: 'Write request outside permittedPaths was intercepted and rejected.',
    },
  ],
  toasts: [
    { id: 't1', type: 'success', message: 'Recipe changes compiled cleanly', actionLabel: 'View' },
    { id: 't2', type: 'info', message: 'Vite dev server active on port 5175' },
    { id: 't3', type: 'warning', message: 'High contrast theme preview enabled' },
  ],
  dialog: {
    type: 'warning',
    title: 'Confirm Operation Authorization',
    message: 'Are you sure you want to promote this patch to the main branch? This action cannot be undone.',
    confirmLabel: 'Apply Proposal',
    cancelLabel: 'Cancel',
  },
}
