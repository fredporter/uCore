# MCP Architecture Audit — 2026-08-19

Status: accepted implementation basis

## Decision

MCP is an external adapter boundary, not the internal uDos service bus.

uCore, uFlow, uKnowledge, and uCode continue to communicate through their
owned Python/HTTP/package contracts. One SDK-backed `udos-mcp` gateway exposes
a deliberately small subset of those contracts to local external developer
clients over stdio. A future remote deployment may add Streamable HTTP at one
`/mcp` endpoint only after authentication, Origin validation, authorization,
rate limiting, and audit evidence exist.

External vendor MCP servers connect directly to the MCP host/client. uCore does
not proxy, mesh, re-export, self-heal, or supervise third-party MCP servers.

## Evidence

### Working candidate

`backend/app/mcp/mcp_bridge` uses the official TypeScript MCP SDK. A direct
protocol probe successfully completed:

- `initialize` with protocol revision `2025-06-18`;
- capability negotiation with `tools` declared;
- `notifications/initialized`;
- `tools/list` returning twelve tool definitions;
- a tool call returning a standard MCP error result when the uCore API was
  unavailable.

This is the only current implementation that demonstrated MCP lifecycle and
tool discovery through an MCP SDK.

### Non-canonical and broken paths

| Path | Finding | Disposition |
|---|---|---|
| `backend/app/api/mcp.py` and `mcp_handlers/` | Bespoke GET/POST REST facade that resembles JSON-RPC but has no MCP initialization, session, or transport lifecycle | Remove after the gateway uses owned APIs directly |
| `backend/app/services/mcp/` | Custom peer mesh with hard-coded machines, `/v1/health`, and legacy Snackmachine JSONL transport | Remove |
| `backend/app/snackbar/modules/mcp_bridge.py` | Second API facade mixing peer calls, providers, and chat under `/api/mcp/*` | Remove |
| `backend/mcp/mcp_diagnostics.py` | Static file-existence check with tool names already removed from the bridge | Replace with a real gateway protocol smoke test |
| `skill_mcp_self_heal.py` and MCP guardrails | Validate and repair the bespoke Python facade, not an MCP transport | Remove with that facade |
| HiveMind/feed/TOON naming | Independent HTTP services described as MCP without a compliant MCP transport | Rename as services or expose selected operations through the gateway |
| uCode `config/mcp_config.json` | Registers the uCore web app, Ollama, HiveMind, and feed processes as MCP servers although they do not speak MCP over stdio | Remove |
| uCode GridSmith MCP server | Hand-rolled 2024-11-05 HTTP JSON-RPC; POST-only, permissive CORS, no standard Streamable HTTP lifecycle/auth | Replace with a domain adapter registered in `udos-mcp` |
| uCode BASIC “MCP” | Mostly means Mini Control Protocol, not Model Context Protocol | Rename to avoid protocol collision; keep internal to uCode if still required |

uFlow and uKnowledge contain no independent tracked MCP server, which is the
correct baseline. Their tools should be contributed through owned gateway
adapters without introducing servers or state stores in those repositories.

## Canonical architecture

```text
External MCP host/client
  |-- local: stdio
  `-- remote later: authenticated Streamable HTTP /mcp
              |
          udos-mcp gateway
          |-- protocol lifecycle and schema validation
          |-- caller scopes and tool filtering
          |-- confirmation/risk metadata
          |-- timeout, rate limit, and audit record
          `-- owned adapters
              |-- uCore: health, Developer repository reads
              |-- uFlow: task reads and approved task writes
              |-- uKnowledge: scoped search/read; publishing excluded
              `-- uCode: GridCore/BASIC operations within uCode contracts

Internal ecosystem calls remain owned APIs/packages, never MCP hops.
Third-party MCP servers connect to the external host directly.
```

## Base standard

- Use an official MCP SDK; do not implement JSON-RPC or transports by hand.
- Local transport is stdio, launched by the client with no daemon or port.
- Remote transport, if later required, is Streamable HTTP on one `/mcp`
  endpoint. Legacy HTTP+SSE is not supported.
- Bind remote/local HTTP only to explicitly configured interfaces; localhost is
  the default. Validate `Origin` and require authentication for remote use.
- Tool lists are deterministic, unique, schema-valid, and filtered by caller
  authorization.
- Read-only tools are the initial surface. Write, external, destructive, secret,
  publishing, provider-selection, and arbitrary-path tools are excluded until a
  tested host confirmation and authorization contract exists.
- MCP does not select models, own budgets, store tasks, store knowledge, launch
  services, or repair itself.
- Every tool has one repository owner and delegates to that owner's canonical
  contract. Gateway code contains no duplicate domain implementation.
- Tool inputs, outputs, duration, caller, authorization result, and errors are
  logged without secrets or private content.

The transport and lifecycle rules follow the official MCP specification:

- https://modelcontextprotocol.io/specification/draft/basic/transports
- https://modelcontextprotocol.io/specification/2025-06-18/architecture
- https://modelcontextprotocol.io/specification/2025-11-25/server/tools

## Initial supported surface

The first release should expose only a small, proven read-only set:

- `system.health.get`
- `developer.repositories.list`
- `developer.repository.status`
- `flow.tasks.list`
- `flow.task.get`
- `knowledge.search`
- `knowledge.document.get`
- `code.grid.tools.list`

Names are stable external contracts. Internal filenames, Skill IDs, providers,
models, local paths, and service topology are not exposed as tool contracts.

## Approved Vendor shortlist

The following upstream repositories are cloned under `~/Code/Vendor/01-RAW`.
RAW means provenance-preserved and under review, not integrated.

| Component | Role | Adoption decision |
|---|---|---|
| `modelcontextprotocol/typescript-sdk` | Official Tier-1 SDK | Use the pinned stable v2 server package; do not fork initially |
| `modelcontextprotocol/inspector` | Protocol CLI/UI/TUI and conformance client | Use the pinned published CLI in development and CI; do not embed its UI |
| `modelcontextprotocol/servers` | Official reference implementations | Study and use fixtures/patterns only; do not bulk-integrate servers |
| `modelcontextprotocol/registry` | Registry schema and publisher | Consume hosted metadata/publisher; do not operate a local registry |
| `github/github-mcp-server` | Official GitHub MCP integration | Connect directly from external hosts; do not duplicate it in uCore |

Existing `ollama-mcp-bridge` and `openrouter-mcp-multimodal` Vendor clones are
not approved runtime components. They duplicate provider routing and budget
authority and should move from `03-INTEGRATED` to archive after provenance is
recorded. The Cline Kanban clone is unrelated to the selected MCP architecture.

Vendor intake rules are tightened for this work:

- `origin` always remains upstream;
- record an immutable intake commit, license, purpose, and disposition;
- a fork remote is created only when a reviewed product patch is actually
  required, not for every research clone;
- RAW and STUDIED clones are never product runtime dependencies;
- prefer pinned published packages/binaries over copied source;
- no generated dependencies, build outputs, credentials, or local product
  modifications live in Vendor clones;
- promotion to INTEGRATED requires a real consuming path and passing tests;
- stale “integrated” labels are corrected rather than treated as evidence.

## Implementation sequence

1. Upgrade the existing TypeScript bridge to the official stable v2 server
   package, add an Inspector-backed protocol smoke test, and rename the
   package/server to `udos-mcp`.
2. Replace the bridge's ad-hoc endpoint list with the eight read-only owned
   adapters above, including input/output schemas and timeouts.
3. Remove Python `api/mcp.py`, `mcp_handlers`, MCP guardrails/self-heal, the
   custom peer mesh, duplicate Snackbar routes, stale diagnostics, launchers,
   manifests, and UI claims that enumerate non-MCP services.
4. Remove uCode's invalid MCP configuration; migrate selected GridSmith reads
   behind the uCode adapter and rename Mini Control Protocol symbols/docs.
5. Publish one client configuration example for the stdio gateway and prove it
   with Codex plus one second MCP client.
6. Consider remote Streamable HTTP only as a separately reviewed release item.

## Acceptance gate

- A clean checkout builds one MCP server package.
- An SDK client test proves initialize, list, call, error, cancellation, and
  shutdown behavior without starting any duplicate MCP daemon.
- Every advertised tool succeeds against a fixture or returns a structured,
  bounded error when its owned service is unavailable.
- No invalid MCP server remains in active configuration or current docs.
- No arbitrary filesystem path, provider/model selector, secret value, general
  Skill executor, or destructive action is externally discoverable.
- All removals and the new gateway pass protected repository checks.
