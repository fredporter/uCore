# Dev Chat Sprint 3A verification — 2026-09-06

Status updated 2026-09-07: supported local conversational coding checkpoint complete.
Next steps: [Sprint 4 and remaining backlog](NEXT_SPRINT_AND_BACKLOG_2026-09-07.md).
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

- Full backend suite: 489 passed, 6 warnings after the conversation and file-context fixes.
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
coding engine. Earlier attempts correctly failed without touching the live fixture.
The final handoff carried `context.file = math.js` from actual read evidence.
Construction then produced this reviewed change:

```diff
-export function add(a, b) { return a - b; }
+export function add(a, b) { return a + b; }
```

The live fixture still contained subtraction immediately before Apply. The browser
then showed `math.js · applied`. A follow-up request, “Run the repository test now
and tell me the result,” dispatched the repository-defined `test` action:

```text
npm run test
> node check.js
addition passed
exitCode: 0
status: passed
```

Chat visibly reported the passing test. The conversation used ID
`0a472be080ef441fb7e3f5ba3b5f0cc2`; the verified check was
`3e1d697462d64d5cb298c813809a8335`. Browser cancellation, restored history,
cross-scope View/Stop, and review/Apply at 480px width were exercised. Automated
contracts cover full-set/new-file/repeated/stale Apply and read/write boundaries.
Temporary fixture artifacts are disposable; this record retains the observed result.

## Closure boundary

This is a supported local integration checkpoint, not certification of every model
or service. Existing local models can still return failed proposals; the UI must
show failure and preserve the repository. Paid budget enforcement, service/skill
execution breadth, full product accessibility/performance audit, and clean-installed
release verification remain in the next-sprint/release backlog. The normal running
installation was not restarted as part of this repository merge.

## Branch reconciliation

All existing local and remote branch tips were incorporated into local `main`.
The stabilization tree exactly matched squash commit `51f1cac`; the runtime/feed
branch exactly matched the previous main tree. Their ancestry was recorded without
reapplying old content. The teletext recovery branch is an ancestor of stabilization.
The current authoring/Dev Mode branch was merged normally. No open pull requests
were reported by GitHub at reconciliation time. Final push verification is recorded
in the completion response.

## UI review closure

Dev HUD now docks on the right and collapses to a labelled edge tab with an inline task count. Identity remains in Settings → Identity; its separate toolbar button is removed. Dreamscape, Google Studio and Banana Studio are dashboard cards only. Extension launchers sharing an existing dashboard route are suppressed, including Google Bridge and Dreamscape. Vault Topology is a distinct backend capability, but has no dedicated UI surface. The full Active Extensions audit removes route-less launchers and routes already represented by main cards (including Server/Settings tabs). Budget and Agents resolve to Server → AI; Identity resolves to Settings → Identity. Publishing, Vault Topology and HomeNest remain in the extension catalogue without misleading dashboard launchers. Only running extensions with distinct routes appear in Active Extensions.

Studio review fixes remove the Amber CRT preset, left-align Banana presets, use shared theme tokens in Banana/Google, and normalize Google navigation icons. The Server health ring has additional spacing around its percentage.
