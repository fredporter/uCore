# Engineering toolchain — installation and standalone app guide

**Tag: Advanced Users / Engineering.** Entries under this tag install
machine-level tools, open localhost listeners, or change the host trust store.
They are optional for ordinary uDOS use and must be reviewed before they run.

Owner: Engineering (Cline rounds, `ucdev` launcher). Lifecycle: development
hosts only. Budget: no paid services, no cloud resources. Removal: see
[Removal and rollback](#removal-and-rollback).

The workspace-level summary lives in
[DEV_ENGINEERING.md](../../DEV_ENGINEERING.md#advanced-users--engineering). This
document is the repo-owned detail: what gets installed, how it is verified, and
how the Safari standalone runtime is produced.

## Relationship to the external development rules

Development stays external. You write and review code in VS Code with Copilot or
Cline, or drive Cline CLI from macOS Terminal. uCore hosts surfaces, services and
contracts; it does not become an IDE, and nothing here reintroduces the retired
in-app Dev Mode.

Every tool below is an adjunct to that setup — the terminal-side equivalent of an
editor extension. `cline` and `kanban` are the Cline clients, `fzf` is the
selector behind `uc`/`ucdev`/`ucusr`, Playwright is the capture/test harness, and
`mkcert` only exists so the installed runtime can be reviewed over HTTPS. None of
them edits source on its own or holds state that belongs to uFlow.

## What the toolchain provides

| Tool | Purpose | Floor | Verify | Removal |
| --- | --- | --- | --- | --- |
| Node.js | Vite, Playwright, CLI clients | 22 | `node -v` | Remove via nvm or `brew uninstall node` |
| pnpm | Workspace install and scripts | 9 | `pnpm -v` | `corepack disable pnpm` or `npm uninstall -g pnpm` |
| Cline CLI | Reviewed multi-step development rounds | 3.x | `cline --version` | `npm uninstall -g cline` |
| Cline Kanban | Local board on `127.0.0.1:3484` | 0.1.x | `kanban --version` | `npm uninstall -g kanban` |
| fzf | Selector used by `ucmd.py` (`uc`, `ucdev`, `ucusr`) | 0.40 | `fzf --version` | `brew uninstall fzf` / `apt remove fzf` |
| Playwright browsers | WebKit captures and Chromium e2e | matches `@playwright/test` | `pnpm exec playwright --version` | `pnpm exec playwright uninstall --all` |
| mkcert + local CA | Trusted HTTPS for the standalone app | 1.4 | `mkcert -CAROOT` | `mkcert -uninstall`, then `brew uninstall mkcert` |

Playwright browsers are installed per project into
`~/Library/Caches/ms-playwright`; the golden baselines stay on Chromium because
that is where they were captured.

## Quick start

```sh
cd ~/Code/uCore

# Report what is present and what is missing. Changes nothing.
bash scripts/install-engineering-toolchain.sh --check

# Install only what is missing.
bash scripts/install-engineering-toolchain.sh
```

| Flag | Effect |
| --- | --- |
| `--check` | Report only. Exits non-zero when a required tool is missing. |
| `--dry-run` | Print the commands that would run, without running them. |
| `--no-https` | Skip `mkcert` and the local CA. Use when the standalone app is not needed. |
| `--help` | Usage. |

The script is idempotent: every step is guarded by a presence test, so running
it twice is safe. It never writes credentials and never edits a repository.

## Verification

Each line below is an observation, not a claim that the tool works:

```sh
node -v                     # v22.x or newer
pnpm -v                     # 9.x or newer
cline --version             # 3.x
kanban --version            # 0.1.x
fzf --version               # 0.4x
cd frontend-vue && pnpm exec playwright --version
mkcert -CAROOT              # prints the CA directory
security find-certificate -c mkcert /Library/Keychains/System.keychain
```

Then exercise the reviewed catalogue:

```sh
python3 ~/Code/uCore/scripts/ucmd.py --mode dev --list
python3 ~/Code/uCore/scripts/ucmd.py --mode dev --select check-toolchain
```


## Standalone web app (Safari Add to Dock)

Safari installs a web app only from a **secure origin**. Measured on this host:
`File → Add to Dock…` is disabled on `http://localhost:5175` and enabled on
`https://localhost:5176` for the same page and manifest. A manifest and an
active service worker are necessary but not sufficient.

```sh
bash scripts/enable-engineering-https.sh start
open -a Safari 'https://localhost:5176/engineering'
```

Then in Safari: **File → Add to Dock…**, accept the name, and launch the app from
`~/Applications`. The menu item is greyed out until the service worker controls
the page, so load the route, wait a second, then **reload** before opening the
menu. Verify inside the app, not in Safari:

- the window has no address bar or tab strip (standalone chrome);
- it resizes to 390 px wide — Safari windows clamp at roughly 574 px, the web app
  does not;
- the same route renders and its navigation works.

Stop and clean up when finished:

```sh
bash scripts/enable-engineering-https.sh status   # listener and certificate state
bash scripts/enable-engineering-https.sh stop     # stops the HTTPS instance
rm -rf ~/Applications/uCore.app                    # removes the installed app
```

Certificates live under `${UDOS_HOME:-$HOME/Code/.udos}/runtime/engineering-https`
and are never committed. Delete that directory to force regeneration.

Safari also records the origin as installed. Deleting the app bundle does not
clear that record, and Add to Dock stays disabled for that origin afterwards —
restarting Safari does not help. Install from a fresh port when reinstalling:

```sh
UCORE_HTTPS_PORT=5181 bash scripts/enable-engineering-https.sh start
```

Repeated install/remove cycles under the same app name eventually leave Add to
Dock disabled even on a fresh port; Safari has been observed refusing new
installs after several cycles. Remove the app through Finder or Launchpad rather
than deleting the bundle, and reinstall only when the icons or manifest have
actually changed.

### Known limitation: mixed content

The page is served over HTTPS while the uCore backend remains
`http://localhost:8484`. Safari blocks those requests, so the app shows
`Local backend unavailable — queued workspace saves will retry when it returns`.
Layout, navigation and the tab strip are valid evidence in this mode; API-backed
state is not. A permanent standalone install needs an HTTPS backend or a
same-origin proxy, which is a separate change.

## Manifest and service worker

`vite-plugin-pwa` serves `/manifest.webmanifest`, injects the manifest link and
registers a service worker **only when `UCORE_PWA_DEV=1`**. Normal development
runs without a worker, because a worker in the dev loop serves stale assets after
edits. `scripts/enable-engineering-https.sh` sets the flag, which is why the
standalone install path still works:

```sh
UCORE_PWA_DEV=1 bash scripts/enable-engineering-https.sh start
```

Without the flag, `GET /manifest.webmanifest` returns the SPA HTML and Safari has
nothing to install — that is expected, not a fault.

- The manifest declares `display: "standalone"` and a 192/512/1024 icon set.
- The icon is a faceted brilliant-cut diamond: a flat table, angled crown, girdle
  and a four-facet pavilion converging on the culet, drawn in `#58a6ff`
  (dark-theme primary) on `#111318` (surface) with facet lines in the surface
  colour. `frontend-vue/public/icon.svg` is the vector source; the PNGs are
  rendered from it, and `favicon.svg` plus `icon-180.png` serve the tab and the
  pinned tile.
- No `maskable` variant is shipped: macOS applies its own squircle to web app
  icons, and a maskable icon (with its 80% safe zone) rendered noticeably small
  in the Dock.
- If a reload looks stale during a standalone check, unregister the worker in
  Safari → Develop → Service Workers.

## Removal and rollback

| Item | Removal |
| --- | --- |
| `devOptions` / manifest icons | Revert the hunk in `frontend-vue/vite.config.ts` |
| HTTPS instance | `bash scripts/enable-engineering-https.sh stop` |
| Certificates | `rm -rf "${UDOS_HOME:-$HOME/Code/.udos}/runtime/engineering-https"` |
| Local CA | `mkcert -uninstall` (admin approval) |
| Installed web app | `rm -rf ~/Applications/uCore.app` |
| Toolchain tools | See the removal column in [What the toolchain provides](#what-the-toolchain-provides) |

Nothing here writes to `$HOME` outside standard tool locations, `~/Applications`
for the web app, and `UDOS_HOME` for certificates. Neither script adds a launchd
job.

## Related

- [Development Engineering guide](../../DEV_ENGINEERING.md) — workflow, launcher, visual review
- [Gate C Matter pilot](plans/GATE_C_MATTER_PILOT.md) — hardware gate that stays queued
- `frontend-vue/scripts/capture-surfaces.mjs` — the WebKit capture used as review evidence
- `config/engineering-commands.json` — reviewed `ucdev` entries
