import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import http from "node:http";
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";

const requests = [];
const fixtures = {
  "/api/health/full": { status: "ok" },
  "/api/developer/repos": { repos: ["uCore"], count: 1 },
  "/api/developer/repos/uCore/status": { repo: "uCore", clean: true },
  "/api/workflow/tasks?scope=all": { tasks: [], count: 0, scope: "all" },
  "/api/knowledge/search?q=mcp&limit=5": { results: [], count: 0 },
  "/api/gridsmith/tools": { tools: ["grid.create"] },
};

let api;
let client;

before(async () => {
  api = http.createServer((request, response) => {
    requests.push(request.url);
    const body = fixtures[request.url];
    response.writeHead(body ? 200 : 404, { "content-type": "application/json" });
    response.end(JSON.stringify(body ?? { error: "not found" }));
  });
  await new Promise((resolve) => api.listen(0, "127.0.0.1", resolve));
  const address = api.address();
  client = new Client({ name: "udos-mcp-test", version: "1.0.0" });
  await client.connect(new StdioClientTransport({
    command: process.execPath,
    args: ["build/index.js"],
    env: { ...process.env, UCORE_URL: `http://127.0.0.1:${address.port}` },
    stderr: "inherit",
  }));
});

after(async () => {
  await client?.close();
  await new Promise((resolve) => api?.close(resolve));
});

test("advertises only the approved read-only surface", async () => {
  const { tools } = await client.listTools();
  assert.deepEqual(tools.map(({ name }) => name).sort(), [
    "code.grid.tools.list",
    "developer.repositories.list",
    "developer.repository.status",
    "flow.tasks.list",
    "knowledge.search",
    "system.health.get",
  ]);
});

test("calls each backing API with bounded encoded arguments", async () => {
  const calls = [
    ["system.health.get", {}],
    ["developer.repositories.list", {}],
    ["developer.repository.status", { repository: "uCore" }],
    ["flow.tasks.list", { scope: "all" }],
    ["knowledge.search", { query: "mcp", limit: 5 }],
    ["code.grid.tools.list", {}],
  ];
  for (const [name, args] of calls) {
    const response = await client.callTool({ name, arguments: args });
    assert.notEqual(response.isError, true, name);
  }
  assert.deepEqual(requests, Object.keys(fixtures));
});

test("schema validation rejects unsafe repository names", async () => {
  const response = await client.callTool({
    name: "developer.repository.status",
    arguments: { repository: "" },
  });
  assert.equal(response.isError, true);
});
