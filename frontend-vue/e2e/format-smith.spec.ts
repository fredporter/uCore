import { expect, test } from "@playwright/test";

for (const width of [1280, 390]) {
  test(`Format Smith renders a reviewed reply at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 844 });
    await page.route("**/api/**", async route => {
      const path = new URL(route.request().url()).pathname;
      if (!path.startsWith("/api/")) { await route.continue(); return; }
      if (path === "/api/assistant/chat") {
        expect(route.request().postDataJSON()).toMatchObject({
          specialist: "format-smith",
          messages: [{ role: "user", content: "Format the workshop notes" }],
        });
        await route.fulfill({ json: {
          content: "```markdown\n# Workshop notes\n- Keep the source links\n```",
        } });
        return;
      }
      const json = path === "/api/connections"
        ? { setup: { completed: true }, connections: [], collections: {} }
        : {};
      await route.fulfill({ json });
    });
    await page.goto("/");
    await page.getByRole("button", { name: "Open assistant" }).click();
    await page.getByRole("combobox", { name: "Assistant specialist" }).selectOption("format-smith");
    await page.getByRole("textbox", { name: "OK Assistant" }).fill("Format the workshop notes");
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(page.getByRole("heading", { name: "Workshop notes" })).toBeVisible();
    await expect(page.getByText("Keep the source links")).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath("format-smith.png") });
  });
}

test("OK Assistant shows the local fallback for a selected cloud model", async ({ page }) => {
  await page.route("**/api/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (!path.startsWith("/api/")) { await route.continue(); return; }
    if (path === "/api/chat/stream") {
      expect(route.request().postDataJSON()).toEqual({
        model: "fixture/cloud-model", message: "Draft a heading", history: [],
      });
      await route.fulfill({
        contentType: "text/event-stream",
        body: 'data: {"system":"OpenRouter unavailable. Switching to a local model."}\n\ndata: {"token":"# Local heading"}\n\ndata: [DONE]\n\n',
      });
      return;
    }
    const json = path === "/api/models/cloud"
      ? { models: [{ id: "fixture/cloud-model", provider: "openrouter" }] }
      : path === "/api/connections"
        ? { setup: { completed: true }, connections: [], collections: {} }
        : {};
    await route.fulfill({ json });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Open assistant" }).click();
  await page.getByRole("combobox", { name: "Assistant model" }).selectOption("fixture/cloud-model");
  await page.getByRole("textbox", { name: "OK Assistant" }).fill("Draft a heading");
  await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByText("OpenRouter unavailable. Switching to a local model.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Local heading" })).toBeVisible();
});
