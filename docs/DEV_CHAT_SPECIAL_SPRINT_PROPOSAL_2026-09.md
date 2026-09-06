# Special Sprint 3A — Conversational Dev Mode

Status: Approved — 2026-09-06; implementation in progress
Proposed position: after Sprint 3, before Sprint 4
Owner: uCore; related authorities: Server runtime policy, uFlow tasks

## Proposed outcome

Make Dev Mode a working conversational coding experience inside the existing
global chat. A user describes an outcome, the assistant inspects the repository,
plans or proposes changes, applies reviewed changes, runs checks, and continues
refining the result in the same conversation.

Keep one chat interface with two clearly distinguished scopes: regular User
Chat and advanced Developer Chat. Both use Ask, Plan, and Act. Users should not
need to choose an agent, know the execution engine, or issue API commands.

This is the approved sprint contract, not a new task store. Execution tasks
belong in uFlow. Sprint 4's existing scope
remains unchanged; this proposal adds a readiness checkpoint ahead of it.

## Evidence and the gap

The September long-sprint plan records Sprint 3 complete for governed construction
and repository review. Code inspection on 2026-09-06 identifies an integration
gap beyond those gates:

- `backend/app/api/developer_api.py` supplies endpoint descriptions to an ordinary
  model completion. It executes only a few hard-coded read intents and does not
  connect general chat requests to Developer operations. Its streaming route
  splits an already completed response into words rather than streaming execution.
- `frontend-vue/src/skills/organisms/OverlayLayer.vue` holds Dev messages in a
  separate component-local array. Its Dev request omits the selected repository
  and Ask/Plan/Act intent, and includes the current message in history as well as
  sending it separately.
- `DeveloperOperationsPanel.vue` provides a separate action selector and request
  composer. The underlying operation manager already supports NanoCoder ACP,
  isolated proposals, review/application, cancellation, and durable evidence.
- The chat component labels its current modes Chat, Research, Act, and Workflow;
  historical specifications describe additional surfaces and selectors that no
  longer agree with the intended single global chat.
- Construction currently selects the configured Ollama model independently of
  chat selection. Each operation opens and closes its own ACP session.

These are source findings, not proof that the installed engine and provider work
end to end. Real runtime verification is a release gate for this sprint.

## Product model

Two choices have different jobs:

| Choice | Values | Meaning |
| --- | --- | --- |
| Scope | User / Developer | Which resources and capabilities the conversation can use |
| Intent | Ask / Plan / Act | Whether to explain, prepare a proposal, or execute authorized work |

User is the default. Developer becomes available when global Dev Mode is enabled.
The global toggle unlocks Developer capabilities; it does not silently change an
existing conversation's scope or authorize writes. Selecting Developer in chat
requires no additional agent or model-mode selection.

The same chat component, composer, history interface, and activity cards serve
both scopes. Conversations retain an explicit scope and isolated context.
Switching scope opens or resumes a conversation in that scope; it does not
reinterpret the existing transcript or copy its attachments automatically.
Opening the Developer surface supplies a repository suggestion, not an automatic
scope switch. An explicit “Discuss in Developer” action can open that context.

## Ask / Plan / Act contract

| Intent | User Chat | Developer Chat | Execution boundary |
| --- | --- | --- | --- |
| Ask | Explain, discuss, summarize, and research permitted user material | Inspect code, search, explain behavior, inspect status and existing diagnostics | Read-only tools; no content changes or arbitrary test/build execution |
| Plan | Draft an approach for documents, research, or workflow | Inspect relevant files and produce an implementation and verification plan | Read-only investigation; no repository changes or automatic task creation |
| Act | Execute supported user-content and workflow actions through their owning services | Propose a fix, apply reviewed changes, run governed checks, and iterate | Execute only capabilities authorized for the scope and request |

Ask is the normal conversational entry point; it supports casual conversation as
well as questions. Research and Workflow become contextual suggestions or tools,
not extra top-level modes. Rename the visible Chat label to Ask and Research to
Plan; audit existing User behavior so the new labels reflect enforced semantics.

A change request received in Ask or Plan produces a clear “Continue in Act”
action. It carries forward the reviewed intent and context without requiring the
user to retype the request. There is no silent escalation. Entering Act alone
does not execute work: a submitted request or explicit continuation does.
An explicit implementation request can start in Act without a mandatory Plan step.

## Minimal interface

The header shows User or Developer. The composer shows Ask / Plan / Act. Developer
conversations also show their repository and optional active file/selection as
removable context chips. Context details show what will be sent before submission.

No additional agent, engine, persona, or System/Project selector appears in chat.
Repository classification remains policy metadata and can appear as a badge when
it affects permissions. Model/provider defaults and budgets remain in Server;
chat shows effective runtime status and a settings link, rather than another picker.

The conversation renders actual activity: files inspected, current plan step,
proposed changes, approval requests, check output, errors, and Stop. Long output
is expandable. The workbench's editor and review panel stay available for detailed
inspection and reflect the same operation state.

Replace the separate Developer Operations request composer with activity/review
for the active conversation. Existing shortcuts such as Explain selection and
Diagnose failure populate or submit an appropriately scoped chat request. They
do not open another assistant or maintain another transcript.

## Review and permission experience

Preserve the existing isolated-proposal design. Reads proceed within the selected
scope. For construction, one concrete request approval covers the bounded vendor
operation; show its repository and intended work. Generated changes then receive
one reviewable “Apply changes” decision for the proposed set, with per-file review
available. This replaces repetitive per-file approval as the default.

The backend must reject stale proposals, preserve existing user changes, and
report partial application honestly. Prefer prevalidating the whole selected
change set and applying it together. A follow-up request stays in the same
conversation but receives fresh scope checks; old approval is not unlimited
authority for new work.

Governed test/build/lint actions may run when covered by the submitted Act request
or an explicit Run checks action. They execute through the existing command
supervisor. Commit, push, merge, deployment, destructive actions, and broader
repository access require specific user intent; an approved fix is not blanket
authorization for those operations.

Turning Dev Mode off blocks new Developer tool calls and cancels active work;
already applied changes remain visible for review. Switching the visible chat
scope does not silently cancel work: show a running-operation indicator and Stop.

## Implementation approach

Use the existing global chat as the presentation layer and the existing Developer
operation manager as the construction authority. NanoCoder remains an internal
engine behind ACP; this sprint does not introduce another agent runtime.

Introduce a shared conversation/turn contract carrying conversation ID, scope,
intent, repository reference, bounded context, and operation references. Resolve
repository paths and permissions on the server. The client cannot grant access
by changing a field, and conversation history cannot supply authorization.

Connect Dev requests to bounded read tools and the governed construction adapter.
Use structured dispatch and capability validation, not an expanding list of
phrase matches or execution of endpoint text generated by the model. Route User
requests to their existing owning services. Share UI and event types without
merging resource permissions or unnecessarily replacing both API families.

Server resolves the effective provider/model/budget for each operation. For the
initial supported NanoCoder configuration, expose the actual local runtime and
its limits honestly. Do not imply that an arbitrary chat-selected model powers
construction. Expanding provider support is outside this sprint unless required
to make the agreed local path work.

Stream real message, plan, tool, proposal, approval, check, and lifecycle events
with stable IDs. Reconnection must not repeat writes. Persist conversation links
and execution evidence under the existing uCore-owned UDOS_HOME storage; keep
uFlow as the task authority. Bound transcript/context size and retention, and
make records removable through the existing history lifecycle. Define the exact
storage extension and migration before adding files or schemas.

Support continuity through durable conversation context and operation references;
a vendor process need not remain running between turns. On restart, restore
history and proposals, and label interrupted work accurately. Never automatically
replay a write to resume a conversation.

## Proposed delivery slices

1. **Freeze the interaction contract.** Review this proposal; inventory chat entry
   points, context sources, mode semantics, storage, and policy enforcement. Verify
   the installed engine/provider before relying on it. Reconcile stale specs.
2. **Unify chat controls and context.** Deliver User/Developer plus Ask/Plan/Act,
   one history interface, repository/file context, and Server-owned runtime status.
   Preserve existing conversations and map legacy mode values explicitly.
3. **Connect investigation and planning.** Real repository reads and structured
   plans from chat, with honest activity events and enforced read-only behavior.
4. **Complete the coding loop.** Connect Act to proposals, request approval,
   reviewed application, governed checks, cancellation, and follow-up correction.
   Fold the operations composer into the shared conversation journey.
5. **Prove readiness and retire duplication.** Run real browser journeys and failure
   cases; remove superseded composers/state, update contracts and closure evidence.

Proposed timebox: two weeks, subject to the initial runtime and storage audit.
This is an estimate, not a completion claim. If a release gate fails, record the
remaining scope and reassess before beginning Sprint 4.

## Acceptance and evidence

The primary journey runs against a disposable repository through the actual UI
and installed NanoCoder/provider: Ask about a bug; Plan the fix; continue in Act;
inspect proposed changes; apply the reviewed set; run a relevant check; request a
follow-up correction in the same conversation. The final report identifies real
changed files and check results. No endpoint typing or separate agent selector
is needed.

Additional required evidence:

- User Chat remains usable with Dev Mode off. Forged Developer requests and
  cross-scope attachments cannot bypass server policy; User retrieval does not
  silently ingest core repository content.
- Ask and Plan cannot write or launch write-capable commands, including through
  nested tools. Changing intent does not execute a pending request by itself.
- Repository/file context is accurate; changing the workbench repository does
  not silently retarget an existing operation. No current user message is doubled.
- Missing engine, unavailable provider, budget exhaustion, rejected approval,
  cancellation, timeout, and failed checks appear as actual states and never as
  successful completion. The editor and ordinary User Chat remain usable.
- Existing dirty files and external edits survive proposal creation and review;
  stale application is rejected. Reconnect and repeated Apply cannot duplicate work.
- Refresh/restart retains transcript and operation references, distinguishes
  interrupted work, and supports follow-up without replaying prior writes.
- Keyboard and narrow-window journeys expose scope, intent, context, review, and
  Stop accessibly. Only one chat composer exists in the active journey.
- Focused backend contracts and frontend component tests, type-check, production
  build, and a recorded real-engine browser journey pass. Mock ACP tests alone do
  not establish completion. Re-run broader affected suites before closure.

## Scope limits

This sprint integrates and validates conversational development. It does not add
another IDE, agent marketplace, multi-agent selector, arbitrary terminal service,
autonomous Git publication, or general provider migration. It adds the minimum
history durability required for Dev continuity; broader history and offline-shell
work remains in Sprint 5. Sprint 4 retains its authoring and research scope.

## Decisions proposed for review

1. Adopt one shared chat interface with two scopes, User and Developer, and the
   same three intents, Ask / Plan / Act.
2. Keep model and engine configuration in Server; display effective status in chat.
3. Preserve scoped construction approval and reviewed application, with one
   change-set application decision by default.
4. Make the real conversational coding journey a prerequisite for Sprint 4.

## Related documents

- [Long-sprint sequence](DEV_MODE_LONG_SPRINTS_2026-09.md)
- [Developer Surface](DEVELOPER_SURFACE.md)
- [Historical chat lane separation](FEATURE_SPEC_ASSISTUI_DEVELOPER_CHAT_LANE_SEPARATION.md)
- [Existing Ask/Plan/Act specification](FEATURE_SPEC_OPENROUTER_ASK_PLAN_ACT.md)

On approval, update the active surface and mode specifications to this contract;
retain older completion notes as historical evidence rather than current UX guidance.

## Subsequent scope clarification — 2026-09-06

Apply the [Zen ecosystem contract](ZEN_ECOSYSTEM_CONTRACT.md) throughout this
sprint. Audit the backend services behind Dev Chat and fix dependencies that
block its local coding loop. Broader host-app integration, browser choices, and
surface simplification enter Sprint 4's pathway; they do not replace Dev Mode
completion or add another chat/agent selector.
