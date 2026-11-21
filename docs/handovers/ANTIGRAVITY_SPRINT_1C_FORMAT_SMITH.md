# Sprint 1C · Format Smith verification handover

22 November 2026 · Perth

Fred Porter coordinates Sprint 1C in uCore on
`sprint/ok-assistant-format-smith-1c`. Start from the
[Sprint 1B handover](ANTIGRAVITY_SPRINT_1B_FORMAT_SMITH.md) and the
[documentation ownership guide](../DOCUMENTATION_OWNERSHIP.md).

## Review and close out Sprint 1B

Record the review checkout, commit, local Ollama model and browser URL before
testing. Use a review instance and sample notes containing a heading, a date,
an amount and an uncertain detail.

| Task | Owner | Evidence |
| --- | --- | --- |
| Verify Format Smith end to end | UI verifier, coordinated by Fred Porter | Select Format Smith in OK Assistant. Confirm Markdown rendering and preservation of names, dates, amounts and uncertainty. Save desktop and narrow-width screenshots. |
| Verify offline inference and draft recovery | UI verifier, coordinated by Fred Porter | Use an installed Ollama model with external access disabled. Exercise a missing model or timed-out request and confirm the draft remains editable. Record which cases used live Ollama and which used fixtures. |
| Close the static-site regression and inventory follow-up | uCore documentation maintainer | Confirm that discovery and serving ignore the legacy checkout and still accept a generated site under the configured `doc-sites/` root. Add missing coverage and record the canonical sources in the inventory. |
| Record release evidence | Fred Porter | Link the GitHub checks, exact test commands and counts, browser evidence, and any items still awaiting verification. |

Keep changes within the existing OK Assistant and documentation contracts.
File any confirmed regression with the reproduction steps and the owning
repository. The sprint closes when the results are recorded and each open
item has an owner.
