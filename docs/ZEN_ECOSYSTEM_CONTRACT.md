> Direction update — 12 September 2026: the [product refactor plan](UDOS_PRODUCT_REFACTOR_PLAN_2026-09-12.md) and [Gemini handover](HANDOVER_GEMINI_PRODUCT_REFACTOR_2026-09-12.md) govern future work. Preserve useful features, UI and historical evidence below. Internal IDE/Dev Mode priorities and requirements to finish that program before independent product releases are superseded; current implementation descriptions are not target architecture or new release certification.

# uDOS Zen ecosystem contract

Status: User-confirmed architecture direction — 2026-09-06
Scope: All uDOS applications, UI surfaces, runtime services, and ecosystem repositories

uDOS is a calm, cohesive workspace over macOS and Linux. It uses the host's
capabilities and reviewed open-source software to provide a clear, distraction-free,
full-screen experience. The user's work is the product; the machinery is supporting
infrastructure.

## Reuse before construction

Before implementing a capability, inspect the host tools, existing ecosystem
contracts, and reviewed Vendor inventory. Prefer, in order:

1. A suitable host capability on macOS or Linux.
2. An existing ecosystem service or integration.
3. A maintained open-source component admitted through the Vendor process.
4. Small custom integration code for the remaining gap.

Do not recreate a terminal, search engine, source-control implementation, task
store, model router, agent runtime, or editor when an existing authority can do the
work. Protocol adapters, policy checks, and presentation are legitimate integration
work. For any new component, identify its owner, lifecycle, resource cost, and
removal path before implementation.

A suitable macOS tool may have a different Linux counterpart. Keep that choice
behind an explicit platform adapter and capability discovery; do not assume Linux
has Homebrew or that macOS has systemd. Detect availability and choose approved
alternatives automatically within the user's scope, budget, and preferences.

## Simple controls, capable execution

All tabs and surfaces expose only controls that serve a user's immediate goal,
meaningful preference, or required decision. Use contextual defaults and progressive
disclosure. Advanced configuration belongs in the owning settings surface.

The everyday flow should show the goal, relevant context, current outcome or
progress, and an action only when it needs user attention. Hide routine tool
selection, plumbing, lifecycle management, and implementation details. Preserve
accessible status, cancellation, and inspectable evidence without surrounding the
user with permanent panels and selectors.

For chat this means one global interface, User or Developer scope, and Ask / Plan /
Act intent. Agents, providers, skills, orchestration, and model selection are
internal capabilities or Server preferences, not competing assistants to manage.

## Automation with accountability

Automate routine choices only within established authorization and resource policy.
A model suggestion is not permission to install software, expand repository access,
spend money, or publish work. Make meaningful decisions concrete and reviewable;
reuse authorization for the bounded work it covers.

Availability, execution, and completion are different states. Installed software is
not proof of a healthy service; a configured agent is not a running process; an API
response is not proof a requested change happened. Show actual outcomes and retain
bounded evidence. Surface failures clearly, with a useful next step.

## Review gate

Each change should answer: What already exists? Why is this integration needed?
Which controls can disappear? Which user decision remains? How is the result
verified on the supported host? Record unsupported or unverified paths honestly.

This contract guides all surfaces. It does not imply that every existing surface
has already been reconciled with it. Reconciliation belongs in the owning uFlow
work and implementation evidence.

## Host-service examples and Snackbar

Snackbar connects host services to the uDOS workspace. Prefer supported macOS
capabilities for Siri, dictation, voice, notifications, and iCloud-backed content,
and supported app integrations for Mail, Messages, Notes, and Reminders. Inventory
actual access and consent requirements; the existence of an app is not proof it
exposes a general-purpose automation API.

A unified messaging surface can aggregate connected sources through these
adapters. Delivery, authoritative storage, and synchronization remain with the
source applications and services. Show which sources are connected and retain
source identity when presenting or sending content. Sending still requires the
user's intent; aggregation is not authorization to contact people.

Browser preference: Safari on macOS; a quiet Firefox-based browser surface on
Linux. Resolve Zen Browser versus a managed Firefox profile through Sprint 4
intake, with compatibility, maintenance, privacy, and supported integration
contracts verified before adoption. Browser-specific plumbing stays below the
uDOS surface.

## Existing evidence to reconcile

This restores prior direction rather than introducing a separate product vision:

- [Feed System Specification](FEED_SYSTEM_SPEC.md) describes Safari, Mail.app,
  iMessage, notifications, calendar, and clipboard as input sources.
- [Snacks System Specification](SNACKS_SYSTEM_SPEC.md) describes restoring the
  original macOS tray workflow, including reminders and VIP mail.
- [Mac clipboard addendum](archived/ADDENDUM_MAC_CLIPBOARD_BUFFER.md) records
  native clipboard capture/paste and Snackbar integration.
- [Zen/Playwright notes](archived/ZEN_PLAYWRIGHT_AUTOMATION_TOOLCHAIN.md) and
  [workspace setup](USER_SETUP_VAULT_MCP_WORKSPACES.md) identify Zen Browser as
  the historical Firefox-based shell. Treat old installation and automation
  claims as intake evidence to reverify, not current compatibility guarantees.

Current priority is macOS. Preserve Linux's platform boundary and historical Zen
Browser direction, without adding Linux implementation work to Sprint 3A.

## Local-first execution boundary

Normal work uses deterministic Skills/Snacks and local Ollama inference. Cloud
models and premium APIs are eligible only for explicitly authorized Developer
work; Dev Mode alone is not a spending grant. BrowserUI may access the web with
local synthesis, and named Snacks may sync connected services without inheriting
cloud-model access. See the [execution lanes brief](LOCAL_FIRST_EXECUTION_LANES_BRIEF_2026-09-08.md)
for the proposed enforcement contract, research interpretation and Sprint 4 slices.
This boundary is user-directed; runtime enforcement remains implementation work.
