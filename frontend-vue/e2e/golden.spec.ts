import { expect, test } from "@playwright/test";

/**
 * Golden-image verification for the GridCore character catalogue renderer.
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
  await page.goto("/ucode/");
  await page
    .locator(".surface-tab-nav__link")
    .filter({ hasText: "Glyphs" })
    .click();
  await page.waitForTimeout(600);
}

async function openTeletextPage(
  page: import("@playwright/test").Page,
  pageNumber: number,
) {
  await page.addInitScript(() => {
    const FixedDate = class extends Date {
      constructor(...args: ConstructorParameters<typeof Date>) {
        super(...(args.length ? args : ["2026-08-28T09:30:00+08:00"]));
      }
      static now() {
        return new Date("2026-08-28T09:30:00+08:00").valueOf();
      }
    };
    window.Date = FixedDate as DateConstructor;
  });
  await page.goto("/ucode/?tab=teletext");
  const viewport = page.getByRole("region", { name: "uCode — Teletext viewport" });
  for (const digit of String(pageNumber)) await viewport.press(digit);
  await page.waitForTimeout(300);
}

async function mockTeletextCatalogue(page: import("@playwright/test").Page) {
  await page.route("**/api/library/search**", (route) => {
    const source = new URL(route.request().url()).searchParams.get("source");
    const results = source === "public"
      ? [
          { path: "docs/guide.md", filename: "guide.md", tags: ["doc-sites"], preview: "Guide preview", extension: "md" },
          { path: "learning/lesson.md", filename: "lesson.md", tags: ["learning"], preview: "Lesson preview", extension: "markdown" },
        ]
      : [{ path: "knowledge/overview.md", filename: "overview.md", tags: [], preview: "Knowledge preview", extension: "md" }];
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ results }) });
  });
  await page.route("**/api/library/file?path=docs%2Fguide.md", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        content: Array.from({ length: 14 }, (_, index) => `Page line ${index + 1}`).join("\n"),
      }),
    }),
  );
}

function visibleCanvasText(page: import("@playwright/test").Page) {
  return page.locator("gridui-canvas").filter({ visible: true }).first().evaluate((host: HTMLElement & {
    buffer?: Array<Array<{ char: string }>>;
  }) => {
    return host.buffer?.flat().map((cell) => cell.char).join("") ?? "";
  });
}

test("character catalogue renders the square terminal register", async ({ page }) => {
  await openGlyphsTab(page);
  // Default font is Terminal 8×8 (pressstart2p).
  await expect(visibleCanvas(page)).toHaveScreenshot("glyphs-terminal.png");
});

test("character catalogue renders the rectangular reading register", async ({ page }) => {
  await openGlyphsTab(page);
  await page
    .getByRole("button", { name: "Teletext", exact: true })
    .click();
  await page.waitForTimeout(600);
  await expect(visibleCanvas(page)).toHaveScreenshot("glyphs-bedstead.png");
});

test("BOB catalogue artwork opens as a deterministic two-frame Pixel asset", async ({ page }) => {
  await openGlyphsTab(page);
  await page.getByRole("combobox", { name: "Character category" }).selectOption("bob");
  await page.getByRole("button", { name: "Arrow BOB" }).click();
  await expect(page.getByRole("region", { name: /Pixel editor canvas/ })).toContainText("ink 20×20");
  await expect(page.getByRole("button", { name: "1", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "2", exact: true })).toBeVisible();
});

for (const [pageNumber, image] of [
  [102, "teletext-data.png"],
  [103, "teletext-map.png"],
  [104, "teletext-graphics.png"],
] as const) {
  test(`Teletext page ${pageNumber} matches its editorial golden`, async ({ page }) => {
    await openTeletextPage(page, pageNumber);
    await expect(visibleCanvas(page)).toHaveScreenshot(image);
  });
}

test("Teletext touch keypad resolves and dismisses a page number", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 760 });
  await openTeletextPage(page, 100);
  await page.getByRole("button", { name: "Controls" }).click();
  await page.getByRole("button", { name: "Keypad" }).click();
  await page.getByRole("button", { name: "Enter page digit 1" }).click();
  await page.getByRole("button", { name: "Enter page digit 0" }).click();
  await page.getByRole("button", { name: "Enter page digit 3" }).click();
  await expect(page.locator("#teletext-keypad")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Reader" })).toHaveCount(0);
});

test("Teletext renders a loaded catalogue list and document page", async ({ page }) => {
  await mockTeletextCatalogue(page);
  await page.goto("/ucode/?tab=teletext");
  const viewport = page.getByRole("region", { name: "uCode — Teletext viewport" });
  await expect.poll(() => visibleCanvasText(page)).toContain("DOCUMENTATION");

  await viewport.press("F2");
  await expect.poll(() => visibleCanvasText(page)).toContain("guide");

  for (const digit of "250") await viewport.press(digit);
  await expect.poll(() => visibleCanvasText(page)).toContain("Page line 1");
  await viewport.press("n");
  await expect.poll(() => visibleCanvasText(page)).toContain("Page line 14");
});

test("Teletext renders an empty catalogue shelf", async ({ page }) => {
  await page.route("**/api/library/search**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ results: [] }) }),
  );
  await page.goto("/ucode/?tab=teletext");
  const viewport = page.getByRole("region", { name: "uCode — Teletext viewport" });
  for (const digit of "200") await viewport.press(digit);
  await expect.poll(() => visibleCanvasText(page)).toContain("This shelf is empty.");
});

test("Teletext renders an error when the catalogue response is malformed", async ({ page }) => {
  await page.route("**/api/library/search**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ results: "invalid" }) }),
  );
  await page.goto("/ucode/?tab=teletext");
  await expect.poll(() => visibleCanvasText(page)).toContain("Vault unavailable");
});

test("Developer editor loads the authoritative repository diff baseline", async ({ page }) => {
  await page.route("**/api/developer/repos", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        repos: [{ name: "uCore", branch: "main", status: "modified", path: "/workspace/uCore", kind: "core" }],
      }),
    }),
  );
  await page.route("**/api/developer/repos/uCore/github", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ configured: false }) }),
  );
  await page.route("**/api/developer/repos/uCore/files", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ files: [{ name: "README.md", type: "md" }] }),
    }),
  );
  await page.route("**/api/developer/repos/uCore/file-preview?path=README.md", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ content: "Working copy\n" }),
    }),
  );
  await page.route("**/api/developer/repos/uCore/diff?path=README.md", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "modified", hasDiff: true, baseline: "Git baseline\n" }),
    }),
  );

  await page.goto("/developer");
  await page.locator(".dev-repo-card").filter({ hasText: "uCore" }).click();
  await page.locator(".surface-tab-nav__link").filter({ hasText: "Editor" }).click();
  await page.getByRole("button", { name: "Diff" }).click();

  await expect(page.locator(".diff-editor-panel__label--original")).toHaveText("Git baseline");
  await expect(page.locator(".diff-editor-panel__label--modified")).toHaveText("Working copy");
});

test("Workflow workspace loads, filters, and opens persistent files", async ({ page }) => {
  const node = { id: "Notes/Today.md", name: "Today.md", type: "file", path: "/Notes/Today.md", extension: "md" };
  await page.route("**/api/editor/workspace?source=user", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ tree: [node] }) }),
  );
  await page.route("**/api/editor/files?source=user&path=**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ path: node.path, content: "# Today\n\nPersistent content.\n" }) }),
  );

  await page.goto("/workflow?tab=editor");
  const filter = page.getByRole("searchbox", { name: "Filter workspace files" });
  await expect(page.getByText("Today.md", { exact: true })).toBeVisible();
  await filter.fill("missing");
  await expect(page.getByText("Today.md", { exact: true })).toHaveCount(0);
  await filter.fill("today");
  await page.getByText("Today.md", { exact: true }).click();

  await expect(page.getByRole("heading", { name: "Today", exact: true }).first()).toBeVisible();
});

test("Terminal reconnects after an unexpected runtime disconnect and flushes queued input", async ({ page }) => {
  await page.addInitScript(() => {
    const runtime = window as typeof window & {
      __terminalSockets?: MockTerminalSocket[];
      __terminalSends?: string[];
    };
    runtime.__terminalSockets = [];
    runtime.__terminalSends = [];
    class MockTerminalSocket extends EventTarget {
      static CONNECTING = 0;
      static OPEN = 1;
      static CLOSING = 2;
      static CLOSED = 3;
      readyState = MockTerminalSocket.CONNECTING;
      constructor(public url: string) {
        super();
        runtime.__terminalSockets!.push(this);
        window.setTimeout(() => {
          this.readyState = MockTerminalSocket.OPEN;
          this.dispatchEvent(new Event("open"));
          this.dispatchEvent(new MessageEvent("message", {
            data: JSON.stringify({ type: "ready", runtime: "shell+bbc-basic" }),
          }));
        }, 0);
      }
      send(data: string) {
        runtime.__terminalSends!.push(String(data));
      }
      close() {
        this.readyState = MockTerminalSocket.CLOSED;
        this.dispatchEvent(new CloseEvent("close"));
      }
      drop() {
        this.readyState = MockTerminalSocket.CLOSED;
        this.dispatchEvent(new CloseEvent("close", { code: 1006 }));
      }
      emitOutput(data: string) {
        this.dispatchEvent(new MessageEvent("message", {
          data: JSON.stringify({ type: "output", data }),
        }));
      }
    }
    Object.defineProperty(window, "WebSocket", { value: MockTerminalSocket });
  });
  await page.goto("/ucode/?tab=terminal");
  await expect.poll(() => page.evaluate(() => (window as any).__terminalSockets?.length)).toBeGreaterThan(0);
  const baselineSocketCount = await page.evaluate(() => (window as any).__terminalSockets.length);
  await page.evaluate(() => (window as any).__terminalSockets.at(-1).drop());
  await page.getByRole("textbox", { name: "Terminal keyboard input" }).fill("queued while reconnecting");
  await expect.poll(() => page.evaluate(() => (window as any).__terminalSockets?.length))
    .toBe(baselineSocketCount + 1);
  await expect.poll(() => page.evaluate(() => (window as any).__terminalSends?.join("\n")))
    .toContain("queued while reconnecting");

  const output = Array.from({ length: 36 }, (_, index) => `SCROLL-${String(index).padStart(2, "0")}`).join("\n");
  await page.evaluate((data) => (window as any).__terminalSockets.at(-1).emitOutput(`${data}\n`), output);
  const canvas = page.locator("gridui-canvas").filter({ visible: true }).first();
  const canvasText = () => canvas.evaluate((element: any) =>
    element.buffer.flat().map((cell: { char: string }) => cell.char).join(""));
  await expect.poll(canvasText).toContain("SCROLL-35");
  const input = page.getByRole("textbox", { name: "Terminal keyboard input" });
  await input.press("PageUp");
  await expect.poll(canvasText).toContain("SCROLL-05");
  await input.press("PageDown");
  await expect.poll(canvasText).toContain("SCROLL-35");
});

const softwareCatalogueFixture = {
  format: "ucode-library/1",
  titles: [
    {
      id: "apple-panic",
      title: "Apple Panic",
      summary: "A compact platform game adapted for experimentation.",
      year: 1981,
      platform: "uCode / BBC BASIC",
      status: "configured",
      treatment: "adapted",
      runtime: "bbc-console",
      entry: "programs/apple-panic/src/apple_panic.bbc",
      mediaPolicy: "catalogue-owned",
      lensCoverage: "state-observed",
      skins: ["retro-pixel", "teletext-classic"],
      controls: ["keyboard", "pointer", "touch-equivalent"],
      available: true,
      launchable: true,
    },
    {
      id: "elite",
      title: "Elite",
      summary: "A legacy-capsule research record.",
      year: 1984,
      platform: "BBC Micro",
      status: "research",
      treatment: "enhanced",
      runtime: "bbc-emulator",
      entry: "programs/elite/elite.ssd",
      mediaPolicy: "user-supplied",
      lensCoverage: "state-observed",
      skins: ["original", "corrected", "enhanced-wireframe"],
      controls: ["bbc-keyboard", "modern-gamepad"],
      available: false,
      launchable: false,
    },
  ],
};

async function mockSoftwareLibrary(page: import("@playwright/test").Page) {
  await page.addInitScript(() => localStorage.setItem("ucore-dev-mode", "off"));
  await page.route("**/api/ucode/info", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        format: "ucode-runtime/1",
        revision: "test",
        capabilities: ["software-library.title-detail"],
      }),
    }),
  );
  await page.route("**/api/ucode/library", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(softwareCatalogueFixture) }),
  );
  await page.route("**/api/ucode/library/apple-panic/launch", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        launchable: true,
        runtime: "terminal",
        protocol: "ucode-session/1",
        session: "capsule",
        titleId: "apple-panic",
      }),
    }),
  );
  for (const title of softwareCatalogueFixture.titles) {
    await page.route(`**/api/ucode/library/${title.id}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          format: "ucode-library-title/1",
          title,
          source: title.id === "apple-panic" ? { path: title.entry, available: true, text: "10 PRINT \"APPLE PANIC\"" } : null,
          learning: [],
          evidence: null,
          media: title.id === "elite"
            ? {
                policy: "user-supplied",
                state: "edition-required",
                acceptedExtensions: [".ssd", ".dsd"],
                licenceNotice: "Original Elite media is not distributed by uCode.",
                nextStep: "Select one exact edition before import is enabled.",
              }
            : { policy: "catalogue-owned", state: "ready" },
        }),
      }),
    );
  }
}

test("Software Library distinguishes configured capsules from protected legacy media", async ({ page }) => {
  await mockSoftwareLibrary(page);
  await page.goto("/ucode/?tab=library");
  await expect(page.getByRole("option", { name: /Apple Panic/ })).toHaveAttribute("aria-selected", "true");

  await page.getByRole("option", { name: /Elite/ }).click();
  await expect(page.getByRole("button", { name: "Launch in Terminal" })).toBeDisabled();
  await expect(page.getByText("Original media is required and is not distributed by uCode.")).toBeVisible();
  await expect(page.getByText("Media guide · edition-required")).toBeVisible();
});

test("Software Library search and readiness filters remain keyboard accessible", async ({ page }) => {
  await mockSoftwareLibrary(page);
  await page.goto("/ucode/?tab=library");
  await page.getByRole("searchbox", { name: "Search software titles" }).fill("elite");
  await expect(page.getByRole("option", { name: /Elite/ })).toBeVisible();
  await expect(page.getByRole("option", { name: /Apple Panic/ })).toHaveCount(0);
  await page.getByRole("searchbox", { name: "Search software titles" }).fill("");
  await page.getByRole("combobox", { name: "Filter by readiness" }).selectOption("configured");
  await expect(page.getByRole("option", { name: /Apple Panic/ })).toBeVisible();
  await expect(page.getByRole("option", { name: /Elite/ })).toHaveCount(0);
});

test("Software Library supports narrow pointer/touch-equivalent selection and unified Terminal launch", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 760 });
  await mockSoftwareLibrary(page);
  await page.goto("/ucode/?tab=library");
  const devHudClose = page.locator(".devhud-close");
  if (await devHudClose.isVisible()) await devHudClose.click();

  await page.getByRole("option", { name: /Apple Panic/ }).click();
  await page.getByRole("button", { name: "Launch in Terminal" }).click();
  const terminalViewport = page.getByRole("region", { name: "uCode — Terminal viewport" });
  await expect(terminalViewport).toBeVisible();
  await terminalViewport.dispatchEvent("pointerdown", { pointerType: "touch", pointerId: 1 });
  await expect(page.getByRole("textbox", { name: "Terminal keyboard input" })).toBeFocused();
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", 430);
});
