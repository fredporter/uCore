# Sonic / HomeNest / HA revival session handover

Consolidated 12 September 2026. This index connects the three product handovers;
it does not replace their implementation contracts or create another backlog.

## Start here

1. [Sonic Gemini handover](../../SonicScrewdriver/docs/GEMINI-HANDOVER.md): implement the read-only foundation first.
2. [HomeNest Gemini handover](../../HomeNest/docs/GEMINI-HANDOVER.md): successor product sprint, standalone Steam gaming plus media.
3. [HA/Matter Gemini handover](../../udos-home-assistant/docs/GEMINI-HANDOVER.md): independent adapter and uihub card; can progress independently of media.
4. [uCore distribution boundary](DISTRIBUTION_AND_SONIC_PATHWAY.md): existing ecosystem ownership and discovery gates.

## Session decisions that apply across repositories

- Sonic revives hardware; uCode revives software. Python/Linux baseline, no Go
  rewrite. Sonic can run standalone and install optional uCore/uCode components.
- HomeNest is an independent Steam/media product, not uCode3. HA/Matter is a
  separate product integration, not HomeNest's automation subsystem.
- uCore owns host identity/secrets/module lifecycle; uFlow owns cross-product
  durable workflows; uCode/GridCore owns shared rendering/program contracts;
  uKnowledge owns document indexing. Do not duplicate these services.
- Sonic's Global Devices collection must cover manuals/specifications/driver
  references and reviewed recipes. Keep public model knowledge separate from
  private physical-instance data. Downloading scripts never executes them.
- Preserve Beacon, public/password/local portals and guide/game/time-capsule,
  crypt/tomb scenarios. These are later evidence-gated milestones, not discarded
  ideas or permission to advertise universal device support.
- Keep three media outputs distinct: multiboot toolkit, live/persistent Sonic
  USB, and OS installed on an internal disk. Classic Modern Mint's theory stays;
  its failed implementation does not. Test a reversible desktop profile first.
- macOS uihub control does not establish native macOS disk-writing support.
- Products release independently. Sonic installs the same artifact that manual
  standalone installation consumes; do not require sibling editable checkouts.

## Shared implementation coordination

Compare HomeNest installer plan/staging/promotion/health with uCore lifecycle
before Sonic adds execution. Assign generic device application to Sonic and
application payload/migrations to HomeNest. Record actual adopted paths, versions
and tests. Do not copy an executor and maintain it in both products.

Register separate Sonic, HomeNest and HA cards through existing host contracts.
Reuse GridCore terminal/teletext and fonts rather than another reader engine.
The proposed API names in plans require checking against current registrations;
they are not evidence that routes are installed.

A movie-night workflow belongs in uFlow: observe HomeNest playback, request HA
scene, record partial failure. HomeNest must still work if HA/uDOS is absent.
HA owns local home rules and upstream Matter owns commissioning/protocols.

## Vendor intake and maintenance

[Vendor process](../../Vendor/README.md) and
[manifest](../../Vendor/VENDOR_MANIFEST.yaml) govern all third-party intake.
Session research clones: Ventoy, mint-themes, esptool, kiwix-tools, Home Assistant
Core and Matter.js Server. Existing GridCore/font/teletext sources should be
reused. RAW remains pristine with upstream origin; recorded commits are research
pins, not approved deployed versions. No remote product forks were created.
Create a fork only for a concrete reviewed patch in the owning product repo.
Steam is an upstream proprietary dependency, not an open-source payload to copy.

## Decisions still requiring implementation evidence

- Exact Linux base, reference hardware and disposable VM/USB test environment.
- Base-linux packaging owner/contract and supported host/target matrix.
- Channel publisher, signing-key custody and production trust/update policy.
- Global Devices edition packaging within the existing knowledge-vault system.
- HomeNest canonical backend/console after isolated characterization.
- Tested upstream HA/Matter/Jellyfin/Steam versions and deployment profiles.

These do not block read-only development or characterization. Do not invent
credentials, hardware support, release destinations or successful test results.

## Evidence, cleanup and checkout state

Sonic's latest source suite: 31 passed. Fresh wheel verification remains pending
in the current environment; earlier temporary build tooling no longer exists.
HomeNest/HA pre-work verified documentation links/provenance, not runtime behavior.
No physical writes, VM boot, Steam/media playback or HA/Matter session was tested.

Sonic removed obsolete prototypes with cleanup inventories; HomeNest archived
ten superseded documents with redirects. Runtime HomeNest duplicates remain for
characterization (79 corresponding backend files, 75 byte-identical). Similar
contents alone do not authorize mechanical deletion of a runtime path.

All product changes accumulated during this session remain uncommitted. Preserve
them and include newly visible Sonic Python files when creating reviewed commits.
The separate HA repository has planning files and no published remote/runtime.
No Gemini message or external publication was sent. Handover documents are the
transfer artifact; /private/tmp is not durable provenance or a release channel.

## First action for the receiving implementer

Read workspace instructions and each repository's current Git status. Follow the
product handovers, verify environment/dependencies, and record tests and unmet
gates in the owning repository. Recheck current code before acting on historical
findings. No remaining product decision is intentionally left only in the chat.
