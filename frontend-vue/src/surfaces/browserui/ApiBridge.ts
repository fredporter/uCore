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
  return res.json()
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
