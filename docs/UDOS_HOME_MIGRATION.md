# uDOS Runtime Home Migration
<!-- path-policy: allow-literals -->

**Status:** Approved architecture; migration not yet executed  
**Updated:** 2026-08-18

## Boundary

`~/Code/.udos` is the canonical `UDOS_HOME`. It contains mutable application
state that should travel with, or be destroyed with, the uDOS installation:
configuration, logs, caches, indexes, service state, secrets, model metadata,
shared Python environments and compatibility data.

User documents remain portable and outside the runtime home:

| Root | Ownership |
| --- | --- |
| `~/Vault` | Primary private user vault |
| `~/Shared` | Add-on/shared vaults |
| `~/Public` | Public and publishable vaults |

These roots must never be folded into `UDOS_HOME` by an automated migration.

## Legacy inputs

The current workstation has used four runtime roots over time:

- `~/.ucore`
- `~/.udos`
- `~/.config/udos`
- `~/.local/share/udos`

They may contain overlapping names with different meanings. Migration therefore
requires a manifest, collision classification and backup; it is not a recursive
merge.

## Safe sequence

1. Stop uDOS services and record their launch configuration.
2. Run `python scripts/audit_udos_home.py --json` and save the inventory.
3. Classify every collision as canonical, mergeable, obsolete or quarantined.
4. Back up all four legacy roots with a checksum manifest.
5. Stage runtime data into `~/Code/.udos` without deleting the sources.
6. Point services at `UDOS_HOME=~/Code/.udos` and run health/integration tests.
7. Retain legacy roots through a rollback window; archive or remove only after
   explicit approval.

The audit script is deliberately read-only. A separate migration command should
be implemented only after the collision manifest has been reviewed.

## Compatibility phase

uCore currently selects an explicit `UDOS_HOME` first. Without one, it continues
to use an existing `~/.ucore` installation until `~/Code/.udos` exists. Fresh
installs default to `~/Code/.udos`. This prevents a code deployment from silently
switching the live state directory before migration is complete.
