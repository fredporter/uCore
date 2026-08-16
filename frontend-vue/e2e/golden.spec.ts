import { expect, test } from "@playwright/test";

/**
 * Golden-image verification for the GridCore glyph renderer.
 *
 * Each test navigates to the uCode surface, opens the Glyphs tab, and
 * screenshots the visible `<gridui-canvas>`. Baselines live in
 * `test/golden/` (see `playwright.config.ts` `snapshotDir`).
 */

function visibleCanvas(page: import("@playwright/test").Page) {
  return page
    .locator("gridui-canvas")
    .filter({ visible: true })
    .first()
    .locator("canvas");
}

async function openGlyphsTab(page: import("@playwright/test").Page) {
  await page.goto("/ucode");
  await page
    .locator(".surface-tab-nav__link")
    .filter({ hasText: "Glyphs" })
    .click();
  await page.waitForTimeout(600);
}

test("glyph inspector renders the terminal (8x8) font", async ({ page }) => {
  await openGlyphsTab(page);
  // Default font is Terminal 8×8 (pressstart2p).
  await expect(visibleCanvas(page)).toHaveScreenshot("glyphs-terminal.png");
});

test("glyph inspector renders the teletext (12x16) font", async ({ page }) => {
  await openGlyphsTab(page);
  await page.getByRole("button", { name: "Teletext 12×16" }).click();
  await page.waitForTimeout(600);
  await expect(visibleCanvas(page)).toHaveScreenshot("glyphs-teletext.png");
});
