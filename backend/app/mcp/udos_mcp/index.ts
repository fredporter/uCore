#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";
import * as z from "zod/v4";

const UCORE_BASE = process.env.UCORE_URL || "http://localhost:8484";

async function apiGet(path: string): Promise<unknown> {
  const response = await fetch(`${UCORE_BASE}${path}`, {
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) {
    const detail = (await response.text()).slice(0, 200);
    throw new Error(`uCore GET ${path} -> ${response.status}: ${detail}`);
  }
  return response.json();
}

function result(data: unknown) {
  return { content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }] };
}

function failure(error: unknown) {
  const message = error instanceof Error ? error.message : String(error);
  return {
    content: [{ type: "text" as const, text: `uDOS MCP error: ${message}` }],
    isError: true,
  };
}

async function read(path: string) {
  try {
    return result(await apiGet(path));
  } catch (error) {
    return failure(error);
  }
}

export function createServer(): McpServer {
  const server = new McpServer({ name: "udos-mcp", version: "2.0.0" });

  server.registerTool(
    "system.health.get",
    { description: "Read the current uCore system health report.", inputSchema: z.object({}) },
    async () => read("/api/health/full"),
  );

  server.registerTool(
    "developer.repositories.list",
    {
      description: "List repositories visible to the uCore Developer surface.",
      inputSchema: z.object({
        scope: z.enum(["code", "ecosystem"]).optional(),
        excludeSystem: z.boolean().optional(),
      }),
    },
    async ({ scope, excludeSystem }) => {
      const query = new URLSearchParams();
      if (scope) query.set("scope", scope);
      if (excludeSystem !== undefined) query.set("exclude_system", String(excludeSystem));
      return read(`/api/developer/repos${query.size ? `?${query}` : ""}`);
    },
  );

  server.registerTool(
    "developer.repository.status",
    {
      description: "Read staged and unstaged status for one named repository.",
      inputSchema: z.object({ repository: z.string().min(1).max(100) }),
    },
    async ({ repository }) => read(`/api/developer/repos/${encodeURIComponent(repository)}/status`),
  );

  server.registerTool(
    "developer.repository.search",
    {
      description: "Search text in one approved Developer repository using bounded literal matching.",
      inputSchema: z.object({
        repository: z.string().min(1).max(100),
        query: z.string().min(1).max(500),
        limit: z.number().int().min(1).max(100).optional(),
      }),
    },
    async ({ repository, query: term, limit }) => {
      const query = new URLSearchParams({ q: term });
      if (limit !== undefined) query.set("limit", String(limit));
      return read(`/api/developer/repos/${encodeURIComponent(repository)}/search?${query}`);
    },
  );

  server.registerTool(
    "developer.actions.list",
    {
      description: "List governed ACP actions and NanoCoder readiness for the Developer Workbench.",
      inputSchema: z.object({}),
    },
    async () => read("/api/developer/operations/capabilities"),
  );

  server.registerTool(
    "developer.operations.list",
    {
      description: "Read recent governed Developer operations. Execution and approval remain in uCore.",
      inputSchema: z.object({ repository: z.string().min(1).max(100).optional() }),
    },
    async ({ repository }) => {
      const query = repository ? `?repository=${encodeURIComponent(repository)}` : "";
      return read(`/api/developer/operations${query}`);
    },
  );

  server.registerTool(
    "developer.commands.list",
    {
      description: "List approved repository-defined checks. Execution remains in the Developer Workbench.",
      inputSchema: z.object({ repository: z.string().min(1).max(100) }),
    },
    async ({ repository }) => read(`/api/developer/repos/${encodeURIComponent(repository)}/actions`),
  );

  server.registerTool(
    "developer.command-runs.list",
    {
      description: "Read recent bounded command status and audit metadata for one repository.",
      inputSchema: z.object({ repository: z.string().min(1).max(100) }),
    },
    async ({ repository }) => read(`/api/developer/command-runs?repository=${encodeURIComponent(repository)}`),
  );

  server.registerTool(
    "flow.tasks.list",
    {
      description: "List workflow tasks using the canonical uFlow-backed task store.",
      inputSchema: z.object({
        scope: z.enum(["user", "all"]).optional(),
        board: z.string().max(100).optional(),
        tag: z.string().max(100).optional(),
      }),
    },
    async ({ scope, board, tag }) => {
      const query = new URLSearchParams();
      if (scope) query.set("scope", scope);
      if (board) query.set("board", board);
      if (tag) query.set("tag", tag);
      return read(`/api/workflow/tasks${query.size ? `?${query}` : ""}`);
    },
  );

  server.registerTool(
    "knowledge.search",
    {
      description: "Search indexed Markdown through the canonical uKnowledge route.",
      inputSchema: z.object({
        query: z.string().min(1).max(500),
        workspaceId: z.string().max(100).optional(),
        limit: z.number().int().min(1).max(50).optional(),
      }),
    },
    async ({ query: term, workspaceId, limit }) => {
      const query = new URLSearchParams({ q: term });
      if (workspaceId) query.set("workspace_id", workspaceId);
      if (limit !== undefined) query.set("limit", String(limit));
      return read(`/api/knowledge/search?${query}`);
    },
  );

  server.registerTool(
    "code.grid.tools.list",
    { description: "List the read-only GridSmith tool catalogue exposed by uCode.", inputSchema: z.object({}) },
    async () => read("/api/gridsmith/tools"),
  );

  return server;
}

const handle = serveStdio(createServer);
console.error("udos-mcp server running on stdio");

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => void handle.close());
}
