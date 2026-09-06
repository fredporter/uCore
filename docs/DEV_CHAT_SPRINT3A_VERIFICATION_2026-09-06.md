# Dev Chat Sprint 3A verification — 2026-09-06

Status updated 2026-09-07: acceptance incomplete; development paused at user request.
Next steps: [remaining gate and backlog](NEXT_SPRINT_AND_BACKLOG_2026-09-07.md).
This report distinguishes verified capabilities from remaining ecosystem work.
The [approved proposal](DEV_CHAT_SPECIAL_SPRINT_PROPOSAL_2026-09.md) remains the
acceptance contract; the [Zen contract](ZEN_ECOSYSTEM_CONTRACT.md) governs reuse
and surface design.

## Supported local path

One global chat presents User/Developer scope and Ask/Plan/Act intent. Developer
history, repository context, tool results, construction approval, reviewed change
sets, cancellation, and check output use existing repository/operation contracts.
The server owns conversation context and enforces write boundaries. Reconnecting
to events cannot submit another mutation.

The verified construction configuration uses installed NanoCoder 1.30.0 via ACP,
local Ollama, and `qwen2.5-coder:7b-instruct-q4_K_M`. NanoCoder's existing JSON
tool protocol handles this model's tool-shaped responses. Native tool calling was
not reliable with the full request on the installed Mistral model; a minimal
native-tool probe alone was insufficient evidence. HTTP is the Ollama transport;
JSON carries tool calls, and ACP carries the coding-engine session. These are
complementary layers, not interchangeable alternatives.

Corrections found through real execution:

- ACP session mode must be set explicitly after session creation.
- The pinned Vendor patch routes all tools through uCore permission checks and
  prevents preapproval file reads while generating edit metadata.
- macOS temporary-path aliases must resolve before repository-boundary comparison.
- Proposal construction includes new files and reports failure when no diff exists.
- Streaming CORS headers must be present before the response is prepared.
- Construction receives bounded actual repository paths; follow-up context uses
  operation status and proposals instead of replaying raw engine output.
- Named OpenRouter providers must use their configured transport and credentials.

## Backend audit disposition

| Capability | Evidence and disposition |
| --- | --- |
| Ollama | Installed models discovered; real read/edit proposal verified against local service. Chat errors surface rather than claiming completion. |
| NanoCoder | Real tool calls read and edit an isolated Git copy; approved diff application remains uCore-owned. Shell, network, and delegation are excluded from this construction policy. |
| Hivemind | Historical endpoint on port 8490 was unavailable during the local audit. No healthy integration or execution claimed. Reconcile ownership and lifecycle before enabling. |
| Roundtable | Historical endpoint on port 4891 was unavailable. Not a prerequisite for the supported single-engine local path. |
| Budget | uCore uses its shared manager; session windows and local accounting corrected. Legacy `udos-budget` plugin still represents a separate authority/path and needs reconciliation. Paid end-to-end enforcement is not certified by local zero-cost tests. |
| Agents | Seven configured definitions discovered. Configured status replaces fabricated active/healthy metrics; no live multi-agent execution claimed. |
| Skills | Thirty catalogue entries discovered. Catalogue visibility does not certify every skill's execution. |
| MCP | Canonical read-only stdio gateway protocol tests pass (3). No new gateway or parallel tool registry introduced. |

Broader native app integration and simplification belong to Sprint 4's updated
pathway. macOS remains the active implementation host. Safari and historical
Linux Zen Browser guidance are preserved in the architecture contract; no Linux
implementation or verification is claimed here.

## Automated evidence

- Full backend suite: 487 passed, 6 warnings before the final streaming fix.
- Focused conversation suite after streaming fix: 6 passed, including real HTTP
  headers and read-only event retrieval.
- Frontend: 65 tests passed across 20 files.
- Frontend type-check and production build passed.
- Canonical MCP build/protocol: 3 passed.
- Home path policy passed.
- Proposal regression verifies new files, full-set Apply, repeated Apply, and
  permission rejection outside the repository or for shell execution.

## Browser acceptance record

Disposable Git repository `demo` contains an addition function incorrectly using
subtraction and a repository-defined test. Isolated frontend port 5176 and backend
port 8486 keep this check separate from the user's running installation.

Ask correctly identified `add(2, 3) == -1`; Plan retained that context and described
the operator fix without editing. Conversation survived backend/browser reload.
Act created awaiting-approval requests, and explicit approval started the isolated
coding engine. Browser cancellation and cross-scope View/Stop were verified.
The latest chat-created construction attempt still returned no file changes.
Direct isolated engine runs produced correct diffs, but this did not establish a
reliable full conversation journey. No live fixture proposal was applied.
Apply/check/follow-up acceptance remains open; the sprint is not complete.

Later context/acknowledgement/check-discovery edits are present in source, but
their final combined runtime acceptance has not been completed. Test counts above
are dated evidence, not certification of every subsequent edit.
