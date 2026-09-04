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

