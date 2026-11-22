# Sprint 1F – Format Smith Automation Hand‑over

**Date:** $(date +%Y-%m-%d)

## Goal
Automate verification of fenced Format Smith replies, add regression tests, and integrate continuous‑integration checks for the new markdown rendering.

## Owner
- **Fred Porter** (<fredporter@users.noreply.github.com>)

## Tasks
- [ ] Add unit tests for `renderMarkdown` handling of fenced blocks (nested markdown).
- [ ] Create an end‑to‑end Cypress test that:
  - Starts the OK Assistant UI (`npm run dev`).
  - Enables **Show Advanced** and selects **GitHub** in System Settings.
  - Sends a sample fenced reply and verifies the rendered HTML contains the expected markdown.
- [ ] Update CI workflow (`.github/workflows/ci.yml`) to run the new Cypress tests on each PR.
- [ ] Capture screenshots of the UI after the Cypress run as artifacts.
- [ ] Update this hand‑over with verification screenshots and test results.
- [ ] Open a PR for Sprint 1F and ensure CI passes.

## Verification (TODO)
- Cypress test results and screenshots will be attached after the automated run.

## References
- Sprint 1E hand‑over: [ANTIGRAVITY_SPRINT_1E_FORMAT_SMITH.md](../handovers/ANTIGRAVITY_SPRINT_1E_FORMAT_SMITH.md)
- Markdown renderer: `frontend-vue/src/composables/useMarkdown.ts`
- CI configuration: `.github/workflows/ci.yml`
