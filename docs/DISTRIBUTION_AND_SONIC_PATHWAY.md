# uCore Distribution and SonicScrewdriver Pathway

**Status:** Planned — begins after the Dev Mode release gates
**Owners:** uCore host, uCode runtime, SonicScrewdriver distribution companion

## Product direction

uCore is the installed platform and lifecycle authority. uCode supplies portable
GridCore, Terminal, Teletext, code, and rendering/runtime contracts.
SonicScrewdriver is a separately useful installer, recovery, and device tool
that consumes those contracts; it does not become a competing platform core.

The intended invitation path for a nontechnical tester is a signed download,
guided installation, first-run validation, and a safe example workspace. GitHub
remains the source and developer channel rather than the primary onboarding UI.

The browser PWA is an optional shell installation. It is not evidence that the
backend, runtimes, extensions, offline libraries, or service supervision have
been installed.

## Adjacent product boundaries

### HomeNest — media and layback computing

HomeNest owns the household media experience: the decentralized media server
and library, discovery and metadata, playback, queues and handoff, live TV/EPG
and recording where supported, remote-friendly clients, and the ten-foot or
"layback computing" interface. It may consume shared identity, Feed, Prose,
Story, knowledge, and uCode rendering contracts without becoming their owner.

HomeNest does not own general home automation, a device registry, a rules
engine for the whole home, or a replacement implementation of Home Assistant
or Matter. Media-aware automations such as "dim lights when playback starts"
cross the boundary through an integration contract: HomeNest emits playback
state or intent; the automation authority decides and executes the device
action.

### Home/device orchestration — separate integration lane

Home and device orchestration is a separate future lane spanning:

- uCore for installation, identity, secrets, capability policy, health, and
  integration lifecycle;
- uFlow for durable routines, schedules, approvals, and execution evidence;
- uCode for grid/terminal/teletext device views and portable interaction;
- SonicScrewdriver for device discovery, provisioning, diagnostics, recovery,
  and explicitly confirmed firmware or media writes;
- Home Assistant as an integrated automation platform rather than code to
  recreate; and
- Matter as an adopted interoperability standard/SDK boundary rather than a
  new uDOS protocol implementation.

This lane requires adapter contracts, version/support policy, credential and
network trust boundaries, capability discovery, and safe degraded behavior.
It must not absorb HomeNest's media library or player responsibilities.

## Mandatory HomeNest discovery gate

HomeNest is partially developed and requires the same evidence discipline as
SonicScrewdriver. Before substantial new HomeNest development or extraction:

1. Preserve the current dirty working tree and inventory active and historical
   plans, reset documents, APIs, clients, services, installer code, and runtime
   claims.
2. Verify media browsing, Jellyfin integration, playback control/handoff,
   TV/EPG, recording, decentralized library, and ten-foot client behavior
   against the working tree.
3. Inventory every automation view, rules engine, Home Assistant gateway,
   device schema, Matter concept, provisioning flow, and duplicated service.
4. Classify each artifact as `retain in HomeNest`, `extract to device lane`,
   `replace with upstream integration`, `adapt`, `archive`, or `delete after
   evidence`, with dependencies and migration notes.
5. Reconcile stale uCode3/uCode2 naming and ownership claims against the active
   uCore/uCode boundaries.
6. Confirm the smallest standalone HomeNest product journey and its external
   Jellyfin or other media-server dependencies before implementation resumes.

No extraction should begin by moving files mechanically. First define stable
media events and device-automation adapter contracts, add characterization
tests, and then migrate behavior without creating a second HA or Matter stack.

## Mandatory SonicScrewdriver discovery gate

No new SonicScrewdriver implementation sprint may begin until this gate is
reviewed and explicitly confirmed:

1. Inventory the live SonicScrewdriver repository, roadmap, active development
   plan, USB/device documentation, bootloader taxonomy, MCP manifest, CLI,
   recovery tools, and release metadata.
2. Inventory previous plans and archived specifications. Preserve strong
   concepts even when their original implementation or ownership model is no
   longer current.
3. Test claims in those documents against the working tree and supported target
   hardware. A historical completion label is not runtime proof.
4. Classify every relevant specification as `active`, `adopt`, `adapt`,
   `superseded`, `defer`, or `reject`, with a short rationale and replacement
   link where applicable.
5. Reconcile ownership against the active uCore/uCode boundaries and the
   canonical uFlow, uKnowledge, Skills, MCP/ACP, Feed, and Server authorities.
6. Identify safety gates for disk writes, device flashing, credential recovery,
   boot changes, downloads, privileged execution, rollback, and data recovery.
7. Confirm the resulting scope, supported platforms, first distributable user
   journey, and destructive-operation policy before implementation begins.

The output is a signed-off SonicScrewdriver specification reconciliation and a
small acceptance matrix. Development must not silently select whichever older
document is easiest to implement.

## Sequenced distribution program

### D0 — Release contract and packaging foundation

- Define a signed ecosystem release manifest with exact component versions,
  compatibility, checksums, licenses, channels, and rollback metadata.
- Separate PWA, desktop, developer-source, and portable/offline installation.
- Make clean-machine install, upgrade, uninstall, and rollback release gates.

### D1 — Friendly uCore desktop distribution

- Ship a signed macOS package first, followed by explicitly scoped platforms.
- Bundle or clearly acquire the host, frontend, Python/runtime dependencies, and
  required extensions.
- Provide guided first run, workspace creation, diagnostics, demo content, and
  complete removal.

### D2 — Updates, repair, and offline packs

- Add signed stable/beta/developer update channels and atomic rollback.
- Drive install, health, update, repair, and rollback from the same manifest.
- Support portable configuration plus signed offline knowledge/resource packs.

### D3 — SonicScrewdriver standalone companion

- Companion mode installs, inspects, updates, backs up, or repairs uCore.
- Portable/device mode creates verified media, provisions supported devices,
  loads offline libraries, and provides recovery workflows.
- Use uCode GridCore for deterministic layout, Terminal for execution, Teletext
  for offline help and the Universal Device Library, Story for guided forms, and
  Feed for status and audit evidence.
- Require exact target identity, previews, checksums, confirmation, and recovery
  guidance for every device-writing operation.

### D4 — Portable communication and workspace formats

- Standardize Prose messages, Story forms, Feed envelopes, governed MCP/ACP
  adapters, signed Library bundles, and portable Workspace capsules.
- Keep schemas transport-neutral and renderer-independent so SonicScrewdriver,
  uCore, and other approved hosts can share them without duplicating authority.

## Entry conditions

The distribution program may begin design and evidence gathering during the
final Dev Mode release sprint. Product implementation starts after the current
ACP/MCP Developer Workbench lane and remaining Dev Mode test, documentation,
and release gates are closed or explicitly deferred with owners and rationale.
