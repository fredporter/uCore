/**
 * @module api/client
 * @description Centralized API client for all backend communication.
 * Replaces scattered fetch() calls from the React frontend.
 */

import { SNACKBAR_API, UCORE_API, OLLAMA_API } from "./base";

export interface ApiResponse<T> {
  data: T;
  status: number;
  ok: boolean;
}

async function request<T>(
  url: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data = response.ok ? await response.json() : null;
  return { data, status: response.status, ok: response.ok };
}

/**
 * @description Snackbar API — clipboard, maintenance, workflows, skills
 */
export const snackbarApi = {
  baseUrl: SNACKBAR_API,
  status: () => request(`${SNACKBAR_API}/api/status`),
  clipboard: {
    list: () => request(`${SNACKBAR_API}/api/snacks/clipboard`),
    capture: (body: unknown) =>
      request(`${SNACKBAR_API}/api/snacks/clipboard/capture`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    cleanup: () =>
      request(`${SNACKBAR_API}/api/snacks/clipboard/cleanup`, {
        method: "DELETE",
      }),
    pin: (id: string) =>
      request(`${SNACKBAR_API}/api/snacks/clipboard/${id}/pin`, {
        method: "POST",
      }),
    delete: (id: string) =>
      request(`${SNACKBAR_API}/api/snacks/clipboard/${id}`, {
        method: "DELETE",
      }),
  },
  system: {
    maintenance: () =>
      request(`${SNACKBAR_API}/api/system/maintenance`, { method: "POST" }),
    workflow: (body: unknown) =>
      request(`${SNACKBAR_API}/api/system/workflow`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },
  skills: {
    taskerSync: () =>
      request(`${SNACKBAR_API}/api/skills/tasker_sync/run`, { method: "POST" }),
    vaultSync: () =>
      request(`${SNACKBAR_API}/api/skills/vault_sync/run`, { method: "POST" }),
  },
  docker: {
    ps: () => request(`${SNACKBAR_API}/v1/docker/ps`),
  },
  exec: (command: string) =>
    request(`${SNACKBAR_API}/v1/exec`, {
      method: "POST",
      body: JSON.stringify({ command }),
    }),
};

/**
 * @description uCore backend API — knowledge, surfaces, health, library, vault
 */
export const ucoreApi = {
  baseUrl: UCORE_API,
  health: () => request(`${UCORE_API}/health`),
  userWorkflow: {
    importMarkdown: (body: {
      content: string;
      source_format?: string;
      title?: string;
      filename?: string;
      binder?: string;
      vault_layer?: string;
      relative_dir?: string;
      overwrite?: boolean;
      metadata?: Record<string, unknown>;
    }) =>
      request(`${UCORE_API}/api/user/workflow/import-markdown`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    publishJekyll: (body: {
      content: string;
      title?: string;
      slug?: string;
      collection?: string;
      vault_layer?: string;
      relative_dir?: string;
      binder?: string;
      tags?: string[] | string;
      layout?: string;
      publish_mode?: "local" | "cloud";
      target_repo?: string;
      target_branch?: string;
      execute_git?: boolean;
      commit_message?: string;
      overwrite?: boolean;
    }) =>
      request(`${UCORE_API}/api/user/workflow/publish-jekyll`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },
  knowledge: {
    list: () => request(`${UCORE_API}/api/knowledge`),
    search: (query: string) =>
      request(
        `${UCORE_API}/api/knowledge/search?q=${encodeURIComponent(query)}`,
      ),
    workspaces: () => request(`${UCORE_API}/api/knowledge/workspaces`),
  },
  library: {
    build: () => request(`${UCORE_API}/api/library/build`, { method: "POST" }),
    search: (query: string, source?: string, limit?: number) => {
      let url = `${UCORE_API}/api/library/search?q=${encodeURIComponent(query)}`;
      if (source) url += `&source=${source}`;
      if (limit) url += `&limit=${limit}`;
      return request(url);
    },
    file: (path: string) =>
      request(`${UCORE_API}/api/library/file?path=${encodeURIComponent(path)}`),
    stats: () => request(`${UCORE_API}/api/library/stats`),
    workspaces: () => request(`${UCORE_API}/api/library/workspaces`),
    addWorkspace: (body: { path: string; name?: string }) =>
      request(`${UCORE_API}/api/library/workspaces`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    browse: (path?: string) =>
      request(
        `${UCORE_API}/api/library/browse?path=${encodeURIComponent(path || "")}`,
      ),
  },
  vault: {
    /** Fetch vault layer topology from the plate system */
    topology: () => request(`${UCORE_API}/api/vault/topology`),
    /** Get vault layer details */
    layers: () => request(`${UCORE_API}/api/vault/layers`),
    /** Trigger a vault sync */
    sync: (source?: string) =>
      request(`${UCORE_API}/api/knowledge/sync`, {
        method: "POST",
        body: JSON.stringify(source ? { source } : {}),
      }),
  },
};

/**
 * @description Ollama local LLM API
 */
export const ollamaApi = {
  baseUrl: OLLAMA_API,
  models: () => request(`${OLLAMA_API}/api/tags`),
};

export const api = {
  snackbar: snackbarApi,
  ucore: ucoreApi,
  ollama: ollamaApi,
};

export default api;
