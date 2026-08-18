# Vue Surface Wiring Audit — 2026-08-18

## Navigation rule

uCore navigation follows user intentions, not implementation inventory. A capability
gets a top-level surface only when it represents a durable user activity. Tools,
providers, agents, and runtime details remain contextual actions or operational
views inside the owning surface.

## Canonical surface set

| Surface | User intention | Current tabs | Decision |
| --- | --- | --- | --- |
| Dashboard | Start and resume work | Dashboard, Workflow, Intelligence, Snackbar, System | Keep as the small primary switchboard. Optional extensions remain cards, not permanent tabs. |
| Workflow | Plan, track, edit, automate, and publish work | Workflow, Tasks, Automation, Editor, Publish | Keep. Editor is a contextual full-workspace state reached from a task or document, even though it is represented as a routable tab. uFlow is the authority. |
| Intelligence | Ask, plan, inspect cost, and review history | Chat, Settings, Models, Budget, History | Keep provisionally. Agent selection was removed: HiveMind/provider routing chooses execution. Models remain visible while automatic routing and policy controls mature. |
| uCode | Use the compact user runtime | Terminal, Teletext, Pixel, Grid, Layer, Glyphs | Keep as work modes within one runtime surface. They are not ecosystem navigation destinations. |
| Snackbar | Observe and administer runtime capabilities | Dashboard, Services, Agents, Feeds, Skills, Snacks, Extensions, Logs, MCP | Keep for the current operations pass, but treat this as an operator surface. Next simplification should group inventory views under Dashboard without creating more tabs. |
| System | Configure identity, variables, secrets, and recovery | Pages, Variables, Secrets, Global, User | Keep. Runtime diagnostics stay in Snackbar. |
| Documentation | Read guides, knowledge, learning, and publishing output | Guide & Docs, Knowledge, Learning, Publishing | Keep for now. Reconcile Publishing with Workflow Publish after their backend contracts are compared; do not add another publishing surface. |
| Developer | Inspect repositories and edit real code | Code, Repository, Editor | Keep. Repository and Editor are contextual states selected from Code, not a replacement for uCode user tasks. |

## Contextual and compatibility surfaces

- BrowserUI is the user-owned knowledge acquisition/research workbench and should be
  invoked by Intelligence or Workflow actions. It writes to user/add-on vaults and
  may package contributions; Global Knowledge remains read-only outside authorized
  Dev/maintainer workflows. Its current sample data and standalone tab model are not
  ready for primary navigation.
- Groovebox is a project/add-on built on top of the core. Its route may remain
  stable, but it appears only as a project card when available.
- SonicScrewdriver is a standalone GridCore-based device toolkit: a device library,
  reflashing/build tooling, and a path to create USB-hosted uDos runtimes for older
  Linux-first machines. It is not a uCore extension or permanent core tab.
- `/assistui`, `/server`, `/snackmachine`, `/gridui`, `/userver`, `/teletext`, and
  `/terminal` are compatibility routes and must resolve into a canonical surface.
- The retired uDev name may remain only as saved extension compatibility data.

## Wiring contract

Every visible tab must have all of the following before it is described as wired:

1. A canonical surface owner and a valid `?tab=` deep link.
2. A rendered Vue panel with loading, empty, success, and error behaviour appropriate
   to its contract.
3. A registered backend API or an explicitly local-only state contract.
4. No dependency on retired uDev, VS Code, Cline autonomy, or direct provider choice.
5. A build/test gate that fails when its imported contract drifts.

This pass repaired query-tab synchronization for Intelligence, Documentation, and
uCode. It also made the historical Intelligence Agents link resolve to Snackbar
Agents rather than presenting agent choice to the user.

## Reconciliation queue

1. Replace the Intelligence workflow placeholder with a contextual link/summary
   from uFlow, rather than duplicating Workflow controls.
2. Compare Documentation Publishing and Workflow Publish contracts, then merge the
   user journey into Workflow if they perform the same lifecycle.
3. Consolidate Snackbar's inventory-only tabs into dashboard sections or contextual
   detail views; retain direct compatibility links during the transition.
4. Replace BrowserUI sample stacks with vault-backed research state before exposing
   it through user workflows.
5. After the core repositories are stable on `main`, revisit or rebuild
   SonicScrewdriver as the first standalone GridCore proving project.

## Release sequence

1. Stabilize, reconcile, and merge uCore, uCode, uKnowledge, and uFlow.
2. Prove that repository work, task state, budgets, and internal tools can be managed
   clearly through uCore's Developer and Workflow surfaces.
3. Revisit SonicScrewdriver using the settled uCode/GridCore contracts.
4. Complete Docs Libraries, the Global Knowledge bank, and the Learning Pathway as
   the new-user onboarding layer.
5. Expand into downstream projects and add-ons such as Groovebox.

SonicScrewdriver is also the first **pull product** for the ecosystem: a concrete,
easy-to-explain reason to discover uDos before a new user understands that they want
the wider platform. Its device revival and portable-runtime journey should lead into
uCode, GridCore, vault workflows, documentation, and learning without making Sonic
itself part of uCore.

The Global Knowledge bank and Sonic device library have separate ownership and
packaging contracts; see `UKNOWLEDGE_OFFLINE_LIBRARY_ARCHITECTURE.md`.
