import { defineConfig } from "@playwright/test";

/**
 * Golden-image regression harness for the GridCore renderer.
 *
 * Captures deterministic screenshots of the terminal + glyph inspector and
 * diffs them against committed baselines in `test/golden/`.
 *
 *   pnpm test:golden                      # run diffs
 *   pnpm test:golden --update-snapshots   # regenerate baselines
 *
 * Requires a Chromium build: `pnpm exec playwright install chromium`.
 */
export default defineConfig({
  testDir: "./e2e",
  snapshotDir: "./test/golden",
  snapshotPathTemplate: "{snapshotDir}/{arg}{ext}",
  timeout: 30_000,
  expect: {
    toHaveScreenshot: {
      threshold: 0.1,
      maxDiffPixels: 0,
    },
  },
  use: {
    baseURL: "http://localhost:5175",
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5175",
    reuseExistingServer: true,
    timeout: 60_000,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
