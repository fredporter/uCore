# Local-first recovery and qualification

This runbook accompanies the [local-first delivery plan](LOCAL_FIRST_LIBRARY_DELIVERY.md).
Use the same Git baseline, fixture and acceptance criteria in Antigravity and
Codex. Confirm each command result before marking a step complete.

## Story 1 · The merge is ready, but GitHub is unreachable

1. The release owner opens the uCore checkout and records HEAD, branch status
   and the remote. The last delivery commit is `6acb8e8`, present on local
   `main` and `dev-clean`. Against the last fetched refs, the branches are
   five and one commits ahead respectively.
2. Run `git ls-remote origin refs/heads/main refs/heads/dev-clean`. A hostname
   resolution failure occurs before GitHub can authenticate the request.
   Record “GitHub unreachable”. Keep the local commits and queue a handoff to
   Antigravity or the host terminal with working GitHub access.
3. From that host, retry the read-only probe. Once DNS and HTTPS work, distinguish
   authentication failure, permission denial, branch protection, and history
   divergence using the actual response. A GitHub CLI status message from a
   network-blocked session cannot establish that a token has expired.
4. After access works, run `git fetch origin` and inspect both branch ranges
   with `git rev-list --left-right --count origin/main...main` and the equivalent
   for dev-clean. If the remote moved, review its commits and integrate before
   pushing. Use `git push --atomic origin main dev-clean` for this delivery.
   If main is protected, use a review branch and the repository's PR workflow.
5. Run the read-only remote probe again. Compare remote hashes with the
   intended local commits and attach the result to the handover.

## Story 2 · GitHub responds and asks for credentials

1. The operator checks which client failed. Command-line Git uses the
   configured transport and credential helper. The uCore Secret Store entry
   is an integration credential. Its presence indicates storage only.
2. On a reachable host, check `gh auth status --hostname github.com`.
   If an environment-provided credential overrides the expected CLI account,
   test the stored account with
   `env -u GH_TOKEN -u GITHUB_TOKEN gh auth status --hostname github.com`.
3. For a confirmed CLI authentication problem, the account owner completes
   `gh auth login --hostname github.com --web` and, if they intend to use gh
   as the HTTPS credential helper, `gh auth setup-git --hostname github.com`.
   Retry the read-only Git probe before resuming the push.
4. For an integration credential change, the owner enters the replacement
   directly through System → Configuration → Secret Store. uCore masks the
   stored value and reports whether the save succeeded. Validate the intended
   integration with a read-only check. Retire the old credential once its
   replacement works and its other consumers have been accounted for.
5. Automate presence checks, masked save feedback and read-only post-update
   verification where there is an identified integration consumer. Account
   consent, token issue and revocation, changes to the host credential helper,
   and administrative recovery belong to the account or host owner. An agent
   can prepare the steps and resume verification once the owner completes them.

## Story 3 · A task needs an action outside uDOS

1. The operator starts the action in its owning surface. A failed operation
   reports the attempted action, visible reason and routes back into the app.
2. The agent checks whether the named capability is local, delegated, configured
   or unavailable. It can retry a bounded read, reopen the last good state or
   save a local draft. An uncertain external write needs receipt reconciliation
   before another attempt.
3. For a host or provider action, create a handoff with the exact command or
   destination, authority required, evidence expected, and the step to resume.
   Use an explicit user transfer for interactive sign-in. Keep secrets out of
   prompts, screenshots and task notes.
4. Keep the user in context. Unknown routes go to a recovery page with a safe
   destination. An unavailable screen offers a retry and a route back. For
   partial failures, use inline feedback and retain the last good data where
   possible. A denied action should identify the permission or setup step.

## Story 4 · A saved feed item becomes a task

1. Open Workflow → Feeds with a disposable profile. Import the shared
   fictional RSS fixture or a standalone item. The item appears for review.
2. Reimport the same item. Confirm that the activity resolves once for the
   owning profile. Confirm another profile cannot see or promote it.
3. Use Add to tasks and follow Open task. Compare activity and task IDs in
   the response with the visible task. A fulfilled promotion produces one
   logical task on retry.
4. Follow the Spool receipt when available and find the event in the Spool
   reader. Preserve the distinction between a committed task and a failed
   log write. Verify the API and visual path separately, including a fresh
   reload and empty or unavailable states.

## Story 5 · Setup starts with absent or damaged seed data

1. In a disposable settings root, inspect the installed seed and default
   variable state. Check that unset values are distinguishable from valid
   user overrides.
2. Exercise valid, missing and malformed seed inputs. The setup surface must
   show the missing requirement and a path to recovery. Preserve user values
   and canonical inputs when reading or rebuilding seed-derived state.
3. Update one local variable, reopen the Settings panel, and verify the
   resolved value. Simulate a failed save and confirm that the old state
   remains available and the UI explains what to retry.
4. Record the settings source, owner, test data and reload outcome. Use
   settings-resolved paths and run the home-path policy check for path changes.

## Antigravity and Codex prompts

**Antigravity coordinator**

> Read ~/Code/AGENTS.md and this runbook. Record HEAD, the worktree state and
> assigned file ownership. Split work into host Git delivery, recovery UI,
> Feeds/Spool acceptance, and seed/variables. Give each worker the baseline,
> disposable fixture and expected outcome. Start with a read-only Git probe.
> Record any host or account action for the user and continue independent work.
> Return commands, observed output, changed files, UI screenshots where
> available, and one verdict per story. Preserve existing working changes.

**Codex integration and verification**

> Compare the Antigravity handoff with the checked-out source. Verify findings
> against the owning API and Vue screen, run focused tests, and resolve clear
> dead ends in the assigned scope. Record browser observations separately from
> mocked tests and builds. For blocked Git delivery, preserve local history
> and report the exact failing stage. Resume at remote hash verification only
> after an authorised host push succeeds.

Give each Antigravity worker the coordinator prompt plus its assignment:

| Worker | Assignment and evidence |
| --- | --- |
| Host delivery | Follow Stories 1 and 2 in order. Return the first failed command and its redacted result or the verified remote hashes for both branches. |
| Recovery UI | Open an unknown route, navigate back from the recovery page, and exercise a simulated render failure and retry. Record the route, rendered state, and any loop. |
| Feeds and Spool | Follow Story 4 through the UI and compare the response identifiers with the task and local log. Test a failed list refresh and an already reviewed reimport. Record where profile scoping ends. |
| Seeds and variables | Use a disposable setup root to exercise Story 5. Compare readiness, saved overrides and recovery feedback before and after reload. |

## Current handoff

- Git probes and the atomic push failed at hostname resolution in Codex.
  Keep the verified local merge. The host delivery worker resumes at the
  read-only remote check. No credential rotation was performed.
- Feeds now distinguishes an already reviewed import from an inbox item.
  A failed task-list refresh keeps the promotion receipt and offers a
  read-only retry. Spool single and batch writes preserve existing history.
  Generic Spool history is host-wide. A profile-scoped receipt lookup remains
  open, so the feed panel displays the receipt without a deep link.
- The app has USX recovery for unknown routes and routed render failures.
  The retry remounts the affected surface and Mission Control is the exit.
- Setup validates seed structure and reports failed checks separately from
  unavailable seeds. Local variable updates replace complete JSON files and
  preserve unreadable stores for recovery. Device details load separately.
  Seed validation is structural and local variables remain installation-wide.
- Live browser verification is pending for these changes. The Codex process
  could not connect to the local backend. Use a disposable profile for the
  Feeds round trip and record any API-to-UI mismatch.
