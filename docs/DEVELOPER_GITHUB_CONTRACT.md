# Developer GitHub Contract

**Status:** Canonical pre-release contract
**Updated:** 2026-08-19

Developer is the repository, code, editor, review, and GitHub handoff surface.
It does not own tasks, providers, agent configuration, or operational dashboards.

For each local repository, Developer exposes local branch/worktree state and a
read-only GitHub summary from the repository's configured `origin`: repository
identity, the open pull request for the current branch, and recent Actions runs.
The `gh` CLI is the single authenticated transport. Tokens are never accepted
from frontend query parameters or returned to the browser.

Mutation follows the review sequence: edit, inspect diff, stage, test, commit,
push, open PR, observe required Actions, then merge. Push, PR, review, rerun,
merge, release, and ruleset changes are external writes and require explicit
authorization. GitHub is the remote source of truth; uFlow owns durable task and
evidence state.

Core CI tests uCore with uFlow, uKnowledge, and uCode from their `main` branches.
Temporary stabilization branches are not valid pre-release dependencies.

The retired SnackMachine self-hosted smoke workflow was not a reliable CI gate:
it referenced a deleted validator and depended on a pre-running workstation.
Future extension integration tests must create their own reproducible fixtures
or run in the owning extension repository.

The standalone `/api/github/*` automation API is retired. It duplicated the
Developer workflow and exposed unrelated release, repo-sync, issue-healing,
retry, approval, and merge mutations behind one generic trigger endpoint.
