# Sprint 1B · Format Smith follow-up

21 November 2026 · Perth

Fred Porter owns this sprint in uCore. The branch is
`sprint/ok-assistant-format-smith-1b`. This is the Format Smith follow-up
from the Antigravity handover. The independent uCode Assist model remains a
separate lane in the assistant delivery plan.

## Start here

Confirm that [PR #49](https://github.com/fredporter/uCore/pull/49) is on main
before testing Format Smith. Confirm the reader and static-site cleanup on
[PR #48](https://github.com/fredporter/uCore/pull/48). Bring the sprint branch
up to date with main once those prerequisites land. Link this handover from
`docs/DOCUMENTATION_OWNERSHIP.md` once that guide is on main.

| Task | Owner | Evidence |
| --- | --- | --- |
| Verify the Format Smith selector on the Mac review build at `http://localhost:5185` | UI verifier, coordinated by Fred Porter | Select Format Smith in OK Assistant, send sample notes, check rendered Markdown and source fidelity, then simulate an Ollama failure and verify draft retention. Record checkout, commit and screenshots. |
| Add a regression test for static-site fallback removal | uCore documentation maintainer | A legacy Public checkout is ignored by site discovery and serving. A generated site under the configured `doc-sites/` root remains discoverable and readable. |
| Refresh the documentation inventory after changing pages | Documentation maintainer | Record current sources and affected links in the existing inventory. |
| Run documentation tests and review hosted CI | Fred Porter | Run the wiki tree, mirror and publishing tests. The prior targeted baseline was 25 tests. Record the new count alongside the hosted PR checks. |

CI already runs on pull requests targeting main. Feature branch pushes alone
do not trigger this workflow. Review the PR once hosted checks and live browser
verification are available. Tag the confirmed Sprint 1A commit as
`sprint-1a-format-smith` after verifying PR #49's final commit.
