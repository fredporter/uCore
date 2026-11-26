# Sprint 1F · Format Smith operator test

From `uCore/frontend-vue`, run the operator scenarios with Playwright and open the HTML report.

```sh
pnpm exec playwright install chromium
pnpm exec playwright test e2e/format-smith.spec.ts --reporter=html
pnpm exec playwright show-report
```

On a Mac with Chrome installed, set `UCORE_PLAYWRIGHT_CHANNEL=chrome` on the test command to use that browser. The harness starts Vite on port 5175 or reuses the listener there. It uses fixed replies and writes screenshots under `test-results/`. The frontend CI job uploads them as `format-smith-browser`.

| Scenario | What to check on screen |
| --- | --- |
| Local Format Smith at 1280 px and 390 px | The specialist selector and composer remain usable. The reply displays a **Workshop notes** heading and a list item. |
| Cloud unavailable before output | The message explains the switch to a local model and shows the local heading. |
| Cloud interrupted after output | The cloud draft remains visible with an interruption message. |

For a live check, open the dashboard and select **Open assistant**, then **Format Smith (Markdown)**. Paste synthetic notes with a date, a name, and an estimated amount. Check that the reply preserves those facts and uncertainty. In **General Assistant**, select **OpenRouter Free Models** and send a short synthetic prompt. Confirm a streamed reply or a visible local fallback. Record the model, result, and any provider error in card `80696`.

[Development board](http://127.0.0.1:3484/ucore)
