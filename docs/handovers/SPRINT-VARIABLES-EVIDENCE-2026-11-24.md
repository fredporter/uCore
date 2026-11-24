# Sprint — Variables and Recipe Surfaces: Release Evidence

- Sprint: variables API, recipe/UI surfaces, audit parser repair
- Status: 9 gates green, 2 pending (browser and live UX)
- Owner: developer-lane
- Branch: `sprint/variables-and-recipe-surfaces`
- Code state evidenced: **`6338d74`** (five commits on `16849b9`, the head of PR #56)
- Base: `3399120`; `origin/main` is an ancestor of the branch
- Captured: 2026-11-24T03:07:06Z
- Governance: evidence recorded against a commit, not a working tree

## Scope

| Commit | Purpose |
| --- | --- |
| `91e270d` | Variable registry (`vars.def`), kind enforcement, store lock, packaging guard |
| `db2c90e` | Recipe fixtures and surface iconography, including the accessible-label test |
| `0074091` | Action audit parses templates with the DOM parser |
| `ad6c92f` | Regenerated action inventory, committed separately (stale baseline) |
| `6338d74` | Settings, surface and workflow task documentation |

Versions in scope: backend `4.0.3`, frontend `3.0.1`, `@udos/usx-tokens` `3.2.0`.

## Gates

All measurements taken after the commits above, on a clean tree.

| Gate | Command | Result |
| --- | --- | --- |
| Backend suite | `./.venv/bin/python -m pytest backend/tests -q` | **847 passed**, 8 warnings, exit 0 |
| Backend variables | `pytest backend/tests/test_variables_api.py backend/tests/test_variables_packaging.py -q` | **9 passed** |
| Frontend suite | `npx vitest run` | **185 passed**, 53 files, exit 0 |
| Frontend recipes/surfaces | 3 focused suites | **14 passed** |
| Frontend build | `npm run build` (vue-tsc + vite) | **exit 0** |
| Action audit | `npm run audit:actions` | **1006 controls, 0 missing, 0 unresolved**, exit 0 |
| Content contract | `python3 scripts/check_content_contract.py` | **0 errors**, 17 retro warnings |
| Lint | `ruff check` on changed backend files | clean |
| Path policy | `git diff 3399120...HEAD \| scripts/check_home_path_policy.py --diff-stdin` | OK |

Three `F841` findings remain in unrelated test files (`test_binder_api.py`,
`test_bitchat_store.py`, `test_chat_history_store.py`); they pre-date this sprint
and are untouched.

## Packaging proof

```
cd backend && uv build --wheel -o /tmp/wheelout
  -> /tmp/wheelout/ucore-4.0.3-py3-none-any.whl   294 files
  -> app/core/vars.def present (2,894 bytes, sha256 fe42ed9a7ea6792a)

uv venv /tmp/wheelenv --python 3.12
uv pip install --python /tmp/wheelenv/bin/python --no-deps <wheel>
uv pip install --python /tmp/wheelenv/bin/python aiohttp
```

Smoke check from `/tmp`, outside the checkout, against the wheel rebuilt from
`6338d74`:

```
module    : .../site-packages/app/api/variables_api.py
vars.def  : .../site-packages/app/core/vars.def | exists: True
variables : 114
domains   : address, basic, communication, identity, internal, organization,
            page, personal, scratch, system, workflow
kinds     : $USERNAME string, $TASKPRI number, $TASKDONE boolean
coercion  : $USRFLG1 "yes" -> "true"; "high" on a number -> rejected
```

Two things this proves that the source tree cannot:

- The registry resolves from **site-packages**, so `vars.def` genuinely ships in
  the wheel rather than being read from the checkout.
- `requires-python = ">=3.12,<3.13"` is enforced: installing into a default 3.14
  environment is refused.

Byte-identical rebuilds are not guaranteed because wheel archives embed timestamps;
content identity was verified instead — the same 294 file paths and an identical
`vars.def` digest across two builds.

## Variables contract

| Property | Evidence |
| --- | --- |
| Canonical names win over legacy aliases | `_canonicalize({'username':'Alice','$USERNAME':'Bob'})['$USERNAME'] == 'Bob'`; `_user_view` mirrors aliases only after canonical values are set |
| Invalid values leave storage unchanged | 400 paths assert the store file is byte-identical; unreadable stores are preserved and reported as 503 |
| First-read seeding | File absent → first read creates defaults (`$INSTALLD`, `$LOCATION`, `$ROLE`, …); second read returns an equal document |
| Kind enforcement | Numbers must match `-?\d+(\.\d+)?`; booleans normalise `true/1/yes/on` and `false/0/no/off`; anything else is rejected with the expected kind named |

### Concurrency guarantee, stated precisely

- **Within one process and event loop:** `_STORE_LOCK` serialises the
  read-merge-write in `handle_update_user_variables`, so concurrent coroutines
  cannot interleave in that critical section.
- **Across processes:** no guarantee. `_write_object` is atomic per file
  (temporary file plus `replace()`), so readers never observe a partial document,
  but read→merge→write is not atomic across processes; two writers sharing one
  store would be last-writer-wins.

**Boundary checked:** `app/core/snackbar.py:577` calls
`web.run_app(app, host=..., port=...)` with no `workers` argument — a single
aiohttp process. No systemd unit, Dockerfile or compose file exists in the
repository that could introduce replicas. One process is therefore the only writer
today, and the lock is sufficient.

**If that boundary changes** — multiple workers, a second daemon, or a CLI writing
the same store — the correct fix is an OS-level lock (`fcntl.flock` on a file
beside `variables.json`) spanning the whole read-merge-write, not a larger asyncio
lock. Not applied, because it addresses a condition that does not yet exist.

## Decisions this round

1. **The action inventory is its own commit.** Measured without the line column, the
   regenerated inventory is `+211 / −127` across 44 files, but only 7 of those files
   are ones this sprint touched: the committed inventory was stale before the parser
   fix made regeneration possible. Folding it into the recipe commit would have
   implied the sprint rewrote 44 surfaces.
2. **The audit parser fix is its own commit.** It repairs tooling, not behaviour;
   mixing it into a UI feature would hide it.
3. **The accessible-label test ships with its template.** `AuthoringRecipeView.vue`
   and `AuthoringRecipeView.test.ts` are in the same commit, because the icon-only
   markup moved the label into `aria-label` and the test queries that label.
4. **Mixed-hunk colour leftovers were included here.** `AuthoringRecipeView.vue`
   still carried 60 colour-related changed lines that PR #56 did not take (they
   shared hunks with template edits). They are committed with the file rather than
   left dangling.

## Pending

| Item | Why it is not green |
| --- | --- |
| Browser verification of Authoring Recipe, Settings Form, Recipe Gallery and Workflow Tasks | Playwright 1.62.1 with 33 specs is configured, but no browser binaries are installed (`~/Library/Caches/ms-playwright` is absent). Enable with `npx playwright install chromium`, then `npm run test:golden`. |
| Live UX at 720p–2160p | No display access during this round. |

Manual checklist while browsers are unavailable — disposable data, no saves:

| Flow | Focus | Icon labels | Narrow (390px) |
| --- | --- | --- | --- |
| Authoring Recipe | Tab through the toolbar; every button shows a visible ring | Confirm "Rendered" and "Markdown Source" are announced | Mode row wraps without clipping |
| Settings Form | fieldset → label → control order; required submit shows the message | n/a (text buttons) | Fields stack; label and variable chip do not collide |
| Recipe Gallery | Tab into controls; arrow between recipes; theme switch keeps layout | Card labels are text | Stage reflows without horizontal scroll |
| Workflow Tasks | Row → state control → editor button | Row actions keep accessible names | 3→2 column collapse; destinations ≥28px with clear focus |

## Deferred, deliberately

- **Ollama tool-call support in the Cline CLI.** Local `qwen2.5-coder:3b` and
  `7b-instruct-q4_K_M` both emit tool calls as fenced JSON, so sessions complete
  without executing anything. This is provider wiring tracked as its own workstream;
  the cheapest experiment is pointing the provider at the OpenAI-compatible endpoint
  (`cline auth ollama -b http://127.0.0.1:11434/v1`).
- **PR #56 integration and local `main`.** `main` still sits at `ba88a14`, which
  carries the pre-rewrite duplicate of the variables work. Reconcile after the PR
  integration strategy is agreed; take `git tag archive/pre-rewrite ba88a14` first.

## Reproduction

```sh
cd ~/Code/uCore
git switch sprint/variables-and-recipe-surfaces   # 6338d74
./.venv/bin/python -m pytest backend/tests -q
./.venv/bin/python -m pytest backend/tests/test_variables_api.py backend/tests/test_variables_packaging.py -q
cd frontend-vue && npx vitest run && npm run build && npm run audit:actions
cd .. && python3 scripts/check_content_contract.py
cd backend && uv build --wheel -o /tmp/wheelout && unzip -l /tmp/wheelout/*.whl | grep vars.def
```


