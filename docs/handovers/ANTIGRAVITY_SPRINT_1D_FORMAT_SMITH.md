# Sprint 1D · Format Smith handover

22 November 2026 · Perth

Fred Porter coordinates the Format Smith follow-up in uCore. The review used the
`main` baseline at `c575c14`, an isolated backend, and the installed
`format-smith:latest` Ollama model.

## Verification

The Format Smith tab was visible and selectable in Chrome at 1280 × 900 and
420 × 800. At both sizes the composer displayed “Paste notes to format as
Markdown…” and the assistant preserved the fixture's date, names, amounts and
uncertainty. Direct Ollama inference preserved the same facts.

**Rendering remains open.** The model wrapped the answer in a Markdown code
fence in both browser runs and in the direct Ollama run. The UI displayed the
answer as a code block. The screenshots also show Material Symbols rendered as
icon names in this browser session.

- [Desktop screenshot](../../browser_sandbox/screenshots/sprint1d_desktop.png)
- [Narrow screenshot](../../browser_sandbox/screenshots/sprint1d_narrow.png)
- [Direct Ollama output](../../browser_sandbox/screenshots/sprint1d_ollama.txt)

The synthetic input was the same for all three runs.

```markdown
# Budget review
- 18 November 2026: Alice estimated $1,250 (approx).
- Bob proposed $1,500, maybe.
- Approval: TBD.
```

## Follow-up

- [ ] Render Format Smith output as formatted Markdown when the model wraps the answer in a Markdown fence.
- [ ] Recheck Material Symbols and draft recovery in the review browser.
- [ ] Verify static-site discovery and serving against the legacy fallback and configured `doc-sites/` root.
- [ ] Refresh the documentation inventory after changes.

## References

- [Sprint 1A](ANTIGRAVITY_SPRINT_1A_FORMAT_SMITH.md), [Sprint 1B](ANTIGRAVITY_SPRINT_1B_FORMAT_SMITH.md), and [Sprint 1C PR](https://github.com/fredporter/uCore/pull/51)
- [Documentation ownership guide](../DOCUMENTATION_OWNERSHIP.md)
