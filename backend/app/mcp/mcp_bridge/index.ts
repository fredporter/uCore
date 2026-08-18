#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

declare const process: {
  env: Record<string, string | undefined>;
  on(event: string, handler: () => void | Promise<void>): void;
  exit(code?: number): never;
};

const UCORE_BASE = process.env.UCORE_URL || "http://localhost:8484";

async function apiGet(path: string): Promise<any> {
  const res = await fetch(`${UCORE_BASE}${path}`, {
    signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) throw new Error(`uCore ${path} -> ${res.status}`);
  return res.json();
}

async function apiPost(
  path: string,
  body: Record<string, unknown>,
): Promise<any> {
  const res = await fetch(`${UCORE_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30000),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(
      `uCore POST ${path} -> ${res.status}: ${text.slice(0, 200)}`,
    );
  }
  return res.json();
}

// ─── Tool definitions ─────────────────────────────────────────────

const TOOLS = [
  {
    name: "ucore_ecosystem_audit",
    description:
      "Run a full uCore ecosystem health audit. Returns health percentage, working/broken/orphaned counts across all 54 skills, surfaces, MCP servers, and tests.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_list_skills",
    description:
      "List all registered uCore skills (currently 54). Returns id, name, description, category, and parameters for each skill.",
    inputSchema: {
      type: "object",
      properties: {
        search: {
          type: "string",
          description:
            "Optional search term to filter skills by name or description",
        },
      },
    },
  },
  {
    name: "ucore_run_skill",
    description:
      "Execute a named uCore skill by its ID. Skills include: ecosystem-audit, file_edit_enhancer, surface-registry, mcp_self_heal, dev-mode-executor, vault_discovery, and 48 more.",
    inputSchema: {
      type: "object",
      properties: {
        skill_id: {
          type: "string",
          description:
            "The skill ID to run (e.g. 'ecosystem-audit', 'surface-registry', 'file_edit_enhancer')",
        },
        params: {
          type: "object",
          description: "Optional parameters to pass to the skill",
        },
      },
      required: ["skill_id"],
    },
  },
  {
    name: "ucore_surface_registry",
    description:
      "List all registered uCore surfaces (Groovebox, Developer, Server, System, Workflow, etc.) with their status, port, and health.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_ollama_status",
    description:
      "Check Ollama LLM server status — online status, model count, and available models.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_list_agents",
    description:
      "List all configured AI agents with their specializations, models, and capabilities.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_chat",
    description:
      "Send a message through the uCore LLM chat pipeline. Routes through the provider router based on complexity.",
    inputSchema: {
      type: "object",
      properties: {
        message: {
          type: "string",
          description: "The message to send",
        },
        model: {
          type: "string",
          description: "Optional model override",
        },
      },
      required: ["message"],
    },
  },
  {
    name: "ucore_search_knowledge",
    description:
      "Search the uCore vault knowledge base for documents matching a query.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search query",
        },
        workspace_id: {
          type: "string",
          description: "Optional workspace ID to scope the search",
        },
      },
      required: ["query"],
    },
  },
  {
    name: "ucore_autonomy_state",
    description:
      "Get the latest autonomy engine health state (from the overnight cron). Includes overall health %, Ollama status, and last audit timestamp.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_list_secrets",
    description:
      "List all stored secrets in the uCore secret store (names only, values are never exposed).",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_workflow_status",
    description:
      "Get current user workflow status — active tasks, missions, binder state.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_config",
    description:
      "Get the current uCore configuration — server settings, budget limits, enabled features.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_list_repos",
    description:
      "List developer repositories tracked by the Developer surface — Groovebox, SonicScrewdriver, uConnect, etc.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "ucore_capability_preflight",
    description:
      "Run strict readiness check for one capability key (for example: wordpress_gateway, google_ai_bridge, dreamscape_orchestration).",
    inputSchema: {
      type: "object",
      properties: {
        capability: {
          type: "string",
          description: "Capability key to evaluate",
        },
      },
      required: ["capability"],
    },
  },
  {
    name: "ucore_capabilities_readiness",
    description:
      "Run batch readiness for capability keys. Defaults to WordPress, Google, and Dreamscape when omitted.",
    inputSchema: {
      type: "object",
      properties: {
        capabilities: {
          type: "array",
          description: "Optional list of capability keys",
          items: { type: "string" },
        },
      },
      required: [],
    },
  },
];

// ─── Server ────────────────────────────────────────────────────────

const server = new Server(
  {
    name: "ucore-bridge",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "ucore_ecosystem_audit": {
        const data = await apiPost("/api/skills/ecosystem-audit/run", {
          action: "assess",
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_list_skills": {
        const search = args?.search as string | undefined;
        let data = await apiGet("/api/skills");
        if (search && data.skills) {
          const q = search.toLowerCase();
          data.skills = data.skills.filter(
            (s: any) =>
              s.id?.toLowerCase().includes(q) ||
              s.name?.toLowerCase().includes(q) ||
              s.description?.toLowerCase().includes(q),
          );
          data.count = data.skills.length;
        }
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_run_skill": {
        const skillId = args?.skill_id as string;
        const params = (args?.params as Record<string, unknown>) || {};
        const data = await apiPost(`/api/skills/${skillId}/run`, params);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_surface_registry": {
        const data = await apiPost("/api/skills/surface-registry/run", {});
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_ollama_status": {
        const data = await apiGet("/api/ollama/status");
        const models = await apiGet("/api/ollama/models/available");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ ...data, models }, null, 2),
            },
          ],
        };
      }

      case "ucore_list_agents": {
        const data = await apiGet("/api/agents");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_chat": {
        const message = args?.message as string;
        const model = args?.model as string | undefined;
        const body: Record<string, unknown> = { message };
        if (model) body.model = model;
        const data = await apiPost("/api/chat", body);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_search_knowledge": {
        const query = args?.query as string;
        const workspaceId = args?.workspace_id as string | undefined;
        const params = new URLSearchParams({ q: query });
        if (workspaceId) params.set("workspace_id", workspaceId);
        const data = await apiGet(`/api/knowledge/search?${params.toString()}`);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_autonomy_state": {
        const data = await apiGet("/api/autonomy/state");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_list_secrets": {
        const data = await apiGet("/api/secrets");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_workflow_status": {
        const data = await apiGet("/api/user/workflow/status");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_config": {
        const data = await apiGet("/api/config");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_list_repos": {
        const data = await apiGet("/api/developer/repos");
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_capability_preflight": {
        const capability = String(args?.capability || "").trim();
        if (!capability) {
          throw new Error("capability is required");
        }
        const data = await apiGet(
          `/api/capabilities/${encodeURIComponent(capability)}/preflight`,
        );
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "ucore_capabilities_readiness": {
        const defaults = [
          "wordpress_gateway",
          "google_ai_bridge",
          "dreamscape_orchestration",
        ];
        const list = Array.isArray(args?.capabilities)
          ? (args?.capabilities as unknown[])
              .map((c) => String(c))
              .filter(Boolean)
          : defaults;
        const csv = encodeURIComponent(list.join(","));
        const data = await apiGet(
          `/api/capabilities/readiness?capabilities=${csv}`,
        );
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      default:
        return {
          content: [
            {
              type: "text",
              text: `Unknown tool: ${name}`,
            },
          ],
          isError: true,
        };
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `uCore bridge error: ${error.message || String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

server.onerror = (error) => console.error("[ucore-bridge MCP Error]", error);
process.on("SIGINT", async () => {
  await server.close();
  process.exit(0);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ucore-bridge MCP server running on stdio");
}

main().catch(console.error);
