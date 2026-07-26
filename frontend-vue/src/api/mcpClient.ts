/**
 * @module api/mcpClient
 * @description Shared MCP bridge client for frontend stores.
 * Talks to the uCore backend HTTP API which is the same surface
 * the MCP stdio bridge wraps. This gives the UI the same tools
 * Cline uses.
 */
import { SNACKBAR_API } from "./base";

const BASE = SNACKBAR_API;

async function mcpGet(path: string): Promise<any> {
  const res = await fetch(`${BASE}${path}`, { signal: AbortSignal.timeout(10000) });
  if (!res.ok) throw new Error(`MCP GET ${path} -> ${res.status}`);
  return res.json();
}

async function mcpPost(path: string, body: Record<string, unknown> = {}): Promise<any> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30000),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`MCP POST ${path} -> ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

export const mcpBridge = {
  /** Run the ecosystem health audit */
  ecosystemAudit: () => mcpPost("/api/skills/ecosystem-audit/run", { action: "assess" }),

  /** List all available skills */
  listSkills: (search?: string) => mcpGet("/api/skills"),

  /** Run a named skill */
  runSkill: (skillId: string, params?: Record<string, unknown>) =>
    mcpPost(`/api/skills/${skillId}/run`, params || {}),

  /** Get surface registry */
  surfaceRegistry: () => mcpPost("/api/skills/surface-registry/run", {}),

  /** Ollama status */
  ollamaStatus: () => mcpGet("/api/ollama/status"),

  /** List agents */
  listAgents: () => mcpGet("/api/agents"),

  /** List repos */
  listRepos: () => mcpGet("/api/developer/repos"),

  /** List secrets */
  listSecrets: () => mcpGet("/api/secrets"),

  /** Workflow status */
  workflowStatus: () => mcpGet("/api/user/workflow/status"),

  /** Config */
  getConfig: () => mcpGet("/api/config"),

  /** Autonomy state */
  autonomyState: () => mcpGet("/api/autonomy/state"),

  /** Control panel aggregated status */
  controlStatus: () => mcpGet("/api/control/status"),

  /** Search knowledge */
  searchKnowledge: (query: string) =>
    mcpGet(`/api/knowledge/search?q=${encodeURIComponent(query)}`),
};