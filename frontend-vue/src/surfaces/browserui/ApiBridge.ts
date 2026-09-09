/**
 * @module browserui/ApiBridge
 * @description Unified API client for BrowserUI research and binder operations.
 */
import { SNACKBAR_BASE } from "../../api/base"

const BASE = SNACKBAR_BASE

export interface ResearchJob {
  id: string
  url: string
  binder: string
  tags: string[]
  mode: string
  state: string
  progress: number
  result: string | null
  error: string | null
  created: string
  started: string | null
  completed: string | null
}

export interface BinderMeta {
  name: string
  description: string
  created: string
  updated: string
  score: number
  tags: string[]
  sources: { url: string; title: string; date: string }[]
}

export interface ScrapedContent {
  title: string
  description: string
  url: string
  text?: string
  html?: string
}

// ── Research ─────────────────────────────────────────────────────

export async function startResearch(url: string, binder: string, tags: string[] = [], mode = "summarise"): Promise<{ job_id: string }> {
  const res = await fetch(`${BASE}/api/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, binder, tags, mode }),
    signal: AbortSignal.timeout(5000),
  })
  if (!res.ok) throw new Error(`Research start failed (HTTP ${res.status})`)
  return res.json()
}

export async function searchResearch(query: string): Promise<Array<{ title: string; url: string; description: string }>> {
  const res = await fetch(`${BASE}/api/research/search?q=${encodeURIComponent(query)}`, {
    signal: AbortSignal.timeout(15000),
  })
  if (!res.ok) throw new Error(`Web search failed (HTTP ${res.status})`)
  const data = await res.json()
  return data.results || []
}

export async function getResearchStatus(jobId: string): Promise<ResearchJob> {
  const res = await fetch(`${BASE}/api/research/status?job_id=${jobId}`, {
    signal: AbortSignal.timeout(3000),
  })
  return res.json()
}

export async function listResearchJobs(state?: string, binder?: string): Promise<ResearchJob[]> {
  const params = new URLSearchParams()
  if (state) params.set("state", state)
  if (binder) params.set("binder", binder)
  const res = await fetch(`${BASE}/api/research/list?${params}`, {
    signal: AbortSignal.timeout(3000),
  })
  const data = await res.json()
  return data.jobs || []
}

export async function processNextJob(): Promise<{ processed: boolean; job?: ResearchJob }> {
  const res = await fetch(`${BASE}/api/research/process`, {
    method: "POST",
    signal: AbortSignal.timeout(30000),
  })
  return res.json()
}

// ── Binder ───────────────────────────────────────────────────────

export async function listBinders(): Promise<BinderMeta[]> {
  const res = await fetch(`${BASE}/api/binder/list`, {
    signal: AbortSignal.timeout(3000),
  })
  const data = await res.json()
  return data.binders || []
}

export async function addBinder(name: string, description = "", tags: string[] = []): Promise<BinderMeta> {
  const res = await fetch(`${BASE}/api/binder/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description, tags }),
  })
  const data = await res.json()
  return data.binder
}

export async function updateBinder(name: string, updates: Partial<BinderMeta>): Promise<BinderMeta> {
  const res = await fetch(`${BASE}/api/binder/update`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, ...updates }),
  })
  const data = await res.json()
  return data.binder
}

export async function setBinderScore(name: string, score: number): Promise<void> {
  await fetch(`${BASE}/api/binder/score`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, score: Math.max(0, Math.min(5, score)) }),
  })
}

// ── Scrape ───────────────────────────────────────────────────────

export async function fetchScrape(url: string): Promise<ScrapedContent | null> {
  try {
    const res = await fetch(`${BASE}/api/editor/scrape-web`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(10000),
    })
    if (res.ok) return await res.json()
  } catch { /* offline */ }
  return null
}

// ── Google Frontier / Nano Banana Bridge ──────────────────────────

export interface GroundedCitation {
  index: number
  title: string
  uri: string
  snippet: string
}

export interface GroundedSearchResult {
  status: string
  query: string
  session_id?: string
  model: string
  summary: string
  citations: GroundedCitation[]
  live_grounded?: boolean
}

export interface BananaAssetResult {
  status: string
  model: string
  style_preset: string
  asset_id: string
  prompt: string
  aspect_ratio?: string
  local_path?: string
  mock?: boolean
  bytes_base64?: string
  error?: string
}

export interface DriveVaultSyncResult {
  status: string
  vault_path?: string
  scanned: number
  updated: number
  unchanged: number
  total_records: number
  reason?: string
}

export interface DriveVaultStatusResult {
  status: string
  vault_path?: string
  total_files: number
  mirrored_count: number
  modified_count: number
  unmirrored_count: number
  files: Record<string, { status: "mirrored" | "modified_locally" | "unmirrored"; revision: number; checksum: string }>
}

export interface CodeExecutionResult {
  status: string
  language: string
  code: string
  output: string
  outcome: string
  live_execution: boolean
}

export interface HostCapabilitiesResult {
  os: string
  platform: string
  host_native: Record<string, any>
  capabilities: {
    browser_intake?: boolean
    notes_export?: boolean
    notes_intake?: boolean
    reminders_export?: boolean
    reminders_intake?: boolean
    mail_bridge?: boolean
    notifications?: boolean
    speech_tts?: boolean
  }
}

export interface SafariTabResult {
  ok: boolean
  running: boolean
  url?: string
  title?: string
  error?: string
}

export interface SafariIntakeResult {
  ok: boolean
  url?: string
  title?: string
  card?: Record<string, any>
  error?: string
}

export interface HostExportResult {
  ok: boolean
  title?: string
  folder?: string
  list?: string
  app?: string
  error?: string
}

export interface HostReminderItem {
  id: string
  title: string
  notes?: string
  due_date?: string | null
  completed?: boolean
  list?: string
}

export interface HostRemindersIntakeResult {
  ok: boolean
  items: HostReminderItem[]
  error?: string
}

export interface HostNoteItem {
  id: string
  title: string
  body?: string
  modification_date?: string | null
  folder?: string
}

export interface HostNotesIntakeResult {
  ok: boolean
  items: HostNoteItem[]
  error?: string
}

export async function searchGrounded(query: string, sessionId = "browserui"): Promise<GroundedSearchResult> {
  const res = await fetch(`${BASE}/api/google/grounded-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId }),
    signal: AbortSignal.timeout(25000),
  })
  if (!res.ok) throw new Error(`Grounded search failed (HTTP ${res.status})`)
  return res.json()
}

export async function generateBananaAsset(
  prompt: string,
  stylePreset = "mono_teletext",
  aspectRatio = "1:1"
): Promise<BananaAssetResult> {
  const res = await fetch(`${BASE}/api/google/image/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, style_preset: stylePreset, aspect_ratio: aspectRatio }),
    signal: AbortSignal.timeout(30000),
  })
  if (!res.ok) throw new Error(`Banana asset generation failed (HTTP ${res.status})`)
  return res.json()
}

export async function syncGoogleDriveVault(vaultPath?: string): Promise<DriveVaultSyncResult> {
  const res = await fetch(`${BASE}/api/google/drive/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vault_path: vaultPath }),
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`Google Drive vault sync failed (HTTP ${res.status})`)
  return res.json()
}

export async function getDriveSyncStatus(vaultPath?: string): Promise<DriveVaultStatusResult> {
  const params = vaultPath ? `?vault_path=${encodeURIComponent(vaultPath)}` : ""
  const res = await fetch(`${BASE}/api/google/drive/status${params}`, {
    signal: AbortSignal.timeout(5000),
  })
  if (!res.ok) throw new Error(`Google Drive status failed (HTTP ${res.status})`)
  return res.json()
}

export async function executeGoogleCode(code: string, language = "python"): Promise<CodeExecutionResult> {
  const res = await fetch(`${BASE}/api/google/code/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language }),
    signal: AbortSignal.timeout(35000),
  })
  if (!res.ok) throw new Error(`Google Code execution failed (HTTP ${res.status})`)
  return res.json()
}

// ── Host-Native PIM & Automation (macOS / Zen Host) ──────────────────

export async function getHostCapabilities(): Promise<HostCapabilitiesResult> {
  const res = await fetch(`${BASE}/api/host/capabilities`, {
    signal: AbortSignal.timeout(5000),
  })
  if (!res.ok) throw new Error(`Host capabilities query failed (HTTP ${res.status})`)
  return res.json()
}

export async function getActiveSafariTab(): Promise<SafariTabResult> {
  const res = await fetch(`${BASE}/api/host/safari/active`, {
    signal: AbortSignal.timeout(8000),
  })
  if (!res.ok) throw new Error(`Active Safari tab query failed (HTTP ${res.status})`)
  return res.json()
}

export async function intakeSafariTab(notes = ""): Promise<SafariIntakeResult> {
  const res = await fetch(`${BASE}/api/host/safari/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`Safari tab intake failed (HTTP ${res.status})`)
  return res.json()
}

export async function exportToAppleNotes(
  title: string,
  body: string,
  folder?: string
): Promise<HostExportResult> {
  const res = await fetch(`${BASE}/api/host/notes/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, body, folder }),
    signal: AbortSignal.timeout(12000),
  })
  if (!res.ok) throw new Error(`Export to Apple Notes failed (HTTP ${res.status})`)
  return res.json()
}

export async function exportToAppleReminders(
  title: string,
  notes = "",
  listName?: string,
  dueDate?: string
): Promise<HostExportResult> {
  const res = await fetch(`${BASE}/api/host/reminders/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, notes, list_name: listName, due_date: dueDate }),
    signal: AbortSignal.timeout(12000),
  })
  if (!res.ok) throw new Error(`Export to Apple Reminders failed (HTTP ${res.status})`)
  return res.json()
}

export async function intakeAppleReminders(options?: {
  listName?: string
  limit?: number
  completed?: boolean
}): Promise<HostRemindersIntakeResult> {
  const params = new URLSearchParams()
  if (options?.listName) params.set("list", options.listName)
  if (options?.limit) params.set("limit", String(options.limit))
  if (options?.completed !== undefined) params.set("completed", String(options.completed))

  const qs = params.toString() ? `?${params.toString()}` : ""
  const res = await fetch(`${BASE}/api/host/reminders/intake${qs}`, {
    signal: AbortSignal.timeout(12000),
  })
  if (!res.ok) throw new Error(`Apple Reminders intake failed (HTTP ${res.status})`)
  return res.json()
}

export async function intakeAppleNotes(options?: {
  folder?: string
  limit?: number
  search?: string
}): Promise<HostNotesIntakeResult> {
  const params = new URLSearchParams()
  if (options?.folder) params.set("folder", options.folder)
  if (options?.limit) params.set("limit", String(options.limit))
  if (options?.search) params.set("search", options.search)

  const qs = params.toString() ? `?${params.toString()}` : ""
  const res = await fetch(`${BASE}/api/host/notes/intake${qs}`, {
    signal: AbortSignal.timeout(12000),
  })
  if (!res.ok) throw new Error(`Apple Notes intake failed (HTTP ${res.status})`)
  return res.json()
}

export async function sendHostNotification(
  title: string,
  message: string,
  subtitle = ""
): Promise<{ ok: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/host/notify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, message, subtitle }),
    signal: AbortSignal.timeout(5000),
  })
  if (!res.ok) throw new Error(`Host notification failed (HTTP ${res.status})`)
  return res.json()
}

export async function sendHostSay(
  text: string,
  voice?: string
): Promise<{ ok: boolean; error?: string }> {
  const res = await fetch(`${BASE}/api/host/say`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`Host speech failed (HTTP ${res.status})`)
  return res.json()
}

// ── Dreamscape & Dreambeans API ───────────────────────────────────────

export interface DreamBeanPayload {
  energy: number
  focus: number
  friction?: string
  reflections?: string
  intent?: string
  date?: string
}

export interface DreamBeanResult {
  status: string
  bean: Record<string, any>
  message?: string
}

export interface DailyBriefingResult {
  status: string
  briefing: {
    today?: string[]
    next?: string[]
    watch?: string[]
    focus_recommendation?: string
    horizon?: string
  }
}

export interface MissionResult {
  status: string
  mission: {
    interest: string
    intent: string
    horizon?: string
    priority?: string
    id?: string
  }
}

export async function captureDreamBean(payload: DreamBeanPayload): Promise<DreamBeanResult> {
  const res = await fetch(`${BASE}/api/dreamscape/bean/capture`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`DreamBean capture failed (HTTP ${res.status})`)
  return res.json()
}

export async function getDreamBean(date?: string): Promise<DreamBeanResult> {
  const endpoint = date ? `/api/dreamscape/bean/${encodeURIComponent(date)}` : `/api/dreamscape/bean/today`
  const res = await fetch(`${BASE}${endpoint}`, {
    signal: AbortSignal.timeout(8000),
  })
  if (!res.ok) throw new Error(`Get DreamBean failed (HTTP ${res.status})`)
  return res.json()
}

export async function getDailyBriefing(date?: string): Promise<DailyBriefingResult> {
  const query = date ? `?date=${encodeURIComponent(date)}` : ""
  const res = await fetch(`${BASE}/api/dreamscape/briefing/generate${query}`, {
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`Daily briefing failed (HTTP ${res.status})`)
  return res.json()
}

export async function createMission(interest: string, intent: string): Promise<MissionResult> {
  const res = await fetch(`${BASE}/api/dreamscape/missions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ interest, intent }),
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`Create mission failed (HTTP ${res.status})`)
  return res.json()
}

export async function getDreamscapeContract(): Promise<any> {
  const res = await fetch(`${BASE}/api/dreamscape/contract`, {
    signal: AbortSignal.timeout(5000),
  })
  if (!res.ok) throw new Error(`Dreamscape contract failed (HTTP ${res.status})`)
  return res.json()
}




