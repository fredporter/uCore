# Repository cleanup

## uCode+ rename

The active `uCodePlus` checkout tracks `fredporter/uVector`. Its cached remote includes the spatial migration at `70953d4`. On a GitHub-connected host, check whether `fredporter/uCodePlus` already exists and confirm the source repository. Rename uVector in place to uCodePlus. Verify the new remote resolves to the same repository before changing the local origin. Preserve the dirty checkout. Keep uCode2 as historical source and compare its CLI, fixtures and consumers with the migrated implementation before retiring any remaining references.

## Public extension preparation

| Extension | Local evidence | Remaining |
| --- | --- | --- |
| SnackMachine | Three tests passed on the committed snapshot. Wheel built offline and installed in a fresh Python 3.12 environment. `smx --help` worked. | Review the uncommitted launcher change separately. Confirm licence notice and review tracked content for private material. |
| uCore-Google | Eight tests passed after isolating the mirror ledger per test. Wheel built offline and installed in a fresh Python 3.12 environment. Service import and construction worked. | Confirm licence notice, review private data and OAuth configuration, and qualify live integration separately. |

A redacted Gitleaks scan of all locally available refs returned no findings for either extension. Remote-only refs and non-secret private materials still need review. Both packages declare MIT and neither checkout tracks a standalone LICENSE file. Publish from a reviewed revision after completing those checks.

## Legacy ownership

| Repository | Current owner or next check |
| --- | --- |
| uFlow | uCore registers bundled `app.flow`. Review archived cross-product workflow recipes before marking the standalone repository retired. |
| uKnowledge | uCore registers bundled `app.knowledge`. Keep the separate global-knowledge content corpus active. Check legacy indexing and contribution coverage. |
| udos-identity | uCore registers bundled `app.identity`. Verify profile variables, story forms and WordPress role mapping before retiring legacy code. |
| udos-budget | Review metering, limits and reconciliation with uCore's OpenRouter budget work. |
| udos-vaults | Compare Obsidian setup and vault verification with current uCore seed and configuration flows. |
| udos-agents | Check active package consumers and retain any unique contracts or tests. |
| wpmudev-agent | Keep private and review deployment access material independently. |

GitHub API access from Codex was unavailable. Remote naming, visibility, archive status and dependencies need live confirmation before changing settings.
