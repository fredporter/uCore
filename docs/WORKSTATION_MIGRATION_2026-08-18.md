<!-- path-policy: allow-literals -->
# Workstation Migration — 2026-08-18

**Status:** Completed with compatibility links

**Host:** fredbook
**Canonical runtime:** `/Users/fredbook/Code/.udos`

## Result

- Current uCore state moved from `~/.ucore` to `~/Code/.udos`.
- Historical uDOS, Snackbar, uCode, HomeNest and related state roots preserved
  beneath `~/Code/.udos/legacy-home-roots`.
- Colima data moved beneath `~/Code/.udos/runtimes/colima` and verified healthy.
- Ollama models moved beneath `~/Code/.udos/runtimes/ollama`; eight models were
  visible after restart.
- Developer SDKs, environments and caches moved beneath
  `~/Code/.udos/toolchains/home-roots`.
- Obsolete VS Code and external-agent data moved to
  `~/Code/ARCHIVED/cleanup-2026-08-18` for a rollback window.
- Docker and Kubernetes configuration were restored physically to `~/.docker`
  and `~/.kube` because they contain external-integration credentials/context.
- User vaults were not modified.

## Intentionally retained home state

The remaining directories are owned by macOS, Codex, credentials, or installed
applications rather than uDOS: `.codex`, `.config`, `.ssh`, `.docker`, `.kube`,
`.adobe`, `.cups`, `.dropbox`, `.slack`, `.swiftbar-plugin-state`, `.swiftpm`,
`.homebrew`, `.zsh_sessions`, and `.Trash`.

GitHub CLI authentication remains in `~/.config/gh`; SSH and Git identity remain
in their standard locations. These paths are excluded from uDOS destruction.

## Temporary compatibility links

Compatibility links remain for historical consumers, including `.ucore`,
`.udos`, `.colima`, `.ollama`, `.local`, `.nvm`, `.npm`, `.cache`, `.android`,
language tool caches and old virtual environments. Their data resides physically
under `~/Code/.udos`. New code must not use these links as canonical paths.

They can be removed individually after repository scans report no active
consumer and launch/login tests pass without them.

## Verification

- uCore backend `/api/health`: healthy, version 4.0.5.
- uCore frontend: HTTP 200 on port 5175.
- Menu, server and frontend launch jobs: running.
- Menu launch policy: start at login, restart unsuccessful exits, respect clean
  user Quit until the next login/restart.
- Colima: running with Docker runtime under Virtualization.Framework.
- Ollama: service running with eight migrated models visible.
- Node 20.20.2 and npm 10.8.2 resolve through compatibility paths.
