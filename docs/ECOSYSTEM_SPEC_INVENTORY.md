# Ecosystem Specification and Plan Inventory

**Status:** Planned continuous audit
**Initial estate snapshot:** 2026-09-04

## Purpose

The ecosystem contains useful ideas in active, partial, superseded, archived,
and never-started plans. This audit preserves that design value without making
old documents authoritative or restarting abandoned implementations by
accident.

Every active repository, archived repository, and planned project concept must
be inventoried for specifications, plans, roadmaps, task ledgers, architectural
decisions, prototypes, and claimed-but-unverified completion.

## Initial repository estate

The first filesystem pass found these active Git repositories under the shared
code root:

| Lane | Repositories |
| --- | --- |
| Core authorities | `uCore`, `uCode`, `uFlow`, `uKnowledge` |
| Shared/runtime capabilities | `uVector`, `SnackMachine` |
| Domain products | `HomeNest`, `SonicScrewdriver`, `Groovebox` |
| Extensions | `udos-agents`, `udos-budget`, `udos-identity`, `udos-publishing`, `udos-vaults` |
| Personal/site project requiring classification | `fredporter` |
| Archived estate | repositories and snapshots under `ARCHIVED/` |

This is a baseline discovery result, not a closed registry. The audit must also
inspect remote repositories, extension manifests, workspace references, links
inside specifications, and named planned projects that have no local checkout
or repository.

## Required inventory record

Each discovered document or coherent concept receives a durable record with:

- source repository, path, revision, date, and original status claim;
- short concept summary and intended user outcome;
- implementation evidence: `none`, `prototype`, `partial`, `implemented`, or
  `unverified claim`;
- present relevance and dependencies;
- overlap or conflict with current authorities and contracts;
- security, privacy, licensing, hardware, data-migration, and destructive-action
  implications;
- decision: `retain`, `complete`, `adopt`, `adapt`, `extract`, `merge concept`,
  `defer`, `supersede`, or `archive`;
- destination repository or future project lane, accountable owner, rationale,
  and links to replacement specifications or backlog items;
- validation evidence and review date.

Source documents remain immutable evidence. The inventory points to them; it
does not silently edit history to match a new architecture.

## Audit sequence

### E0 — Registry and provenance

1. Reconcile local Git repositories, remotes, archived trees, extension
   manifests, package workspaces, and cross-repository links.
2. Create stable repository and concept identifiers.
3. Record dirty branches and preserve user work before any inspection that
   could lead to migration.

### E1 — Document and implementation discovery

1. Locate active and historical specs, plans, roadmaps, tasks, handovers,
   decision records, prototypes, and release claims.
2. Trace every claim to code, tests, artifacts, runtime proof, or an explicit
   absence of evidence.
3. Capture valuable independent concepts even when their enclosing plan is
   obsolete.

### E2 — Boundary and duplication review

1. Compare each concept with the active uCore, uCode, uFlow, uKnowledge,
   Server, Skills, Feed, MCP/ACP, extension, and distribution authorities.
2. Identify duplicate engines, gateways, stores, schemas, UIs, installers,
   automation systems, and service ownership.
3. Recommend one owner and explicit adapter boundaries; do not consolidate code
   merely because names appear similar.

### E3 — Value recovery and project incubation

1. Group retained concepts into current backlog candidates, extraction work,
   or named future project briefs.
2. Require a user outcome, owner, dependencies, acceptance evidence, and reason
   the work belongs in that destination.
3. Keep speculative concepts in an incubation register rather than creating
   empty repositories or product surfaces.

### E4 — Confirmation and scheduling

1. Review adopt/adapt/extract decisions with the product owner.
2. Promote only confirmed items into canonical backlogs.
3. Link superseded documents to their active replacements and retain the audit
   trail.

## Operating rules

1. Historical text is evidence, not instruction and not proof of completion.
2. No concept is revived solely because substantial code already exists.
3. No repository is merged, renamed, split, archived, or deleted during the
   inventory phase.
4. Dirty working trees are preserved and reported before project-level work.
5. Upstream products and standards are integrated where appropriate rather
   than reimplemented without a documented reason.
6. Potentially valuable fragments can be retained independently of the larger
   plan that contained them.
7. The inventory is continuous: every new spec must identify its authority,
   lifecycle state, owner, and supersession relationship.

## Relationship to current programs

The Dev Mode release remains the active delivery program. Its Developer
Workbench should eventually make this inventory searchable and allow approved
concepts to become uFlow task references. Distribution, SonicScrewdriver, and
HomeNest discovery gates consume the inventory rather than maintaining separate
archaeology systems.

