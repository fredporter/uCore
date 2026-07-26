/**
 * @module api/base
 * @description Single source of truth for uCore API base URLs.
 *
 * All stores and API clients should import from here instead of
 * declaring per-file `const X = import.meta.env.VITE_... || fallback`.
 *
 * Supported env vars:
 *   VITE_SNACKBAR_URL  – Snackbar container host (default: localhost:8484)
 *   VITE_UCORE_URL     – uCore backend host (falls back to VITE_SNACKBAR_URL)
 *   VITE_OLLAMA_URL    – Ollama LLM inference host (default: localhost:11434)
 */

/** Base URL for the Snackbar container orchestrator. */
export const SNACKBAR_BASE: string =
  import.meta.env.VITE_SNACKBAR_URL || 'http://localhost:8484'

/** Base URL for the uCore backend API. */
export const UCORE_BASE: string =
  import.meta.env.VITE_UCORE_URL || SNACKBAR_BASE

/** Base URL for Ollama local LLM inference. */
export const OLLAMA_BASE: string =
  import.meta.env.VITE_OLLAMA_URL || 'http://localhost:11434'

/** Backward-compatible aliases (prefer the *_BASE names above). */
export const SNACKBAR_API = SNACKBAR_BASE
export const UCORE_API = UCORE_BASE
export const OLLAMA_API = OLLAMA_BASE