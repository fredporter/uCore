import { expect, test } from "@playwright/test";

/**
 * Sprint verification: the four flows the evidence record lists as pending,
 * plus the ten-foot display profile measured at its four target resolutions.
 *
 * The recipe fixtures render from disposable gallery data, so no backend is
 * required. Each flow is opened from the gallery tab that hosts it.
 */

const NARROW = { width: 390, height: 844 };
const GALLERY = "/engineering?section=recipes";

async function noHorizontalOverflow(page: import("@playwright/test").Page) {
  return page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1,
  );
}

async function openRecipe(page: import("@playwright/test").Page, tab: string) {
  await page.goto(GALLERY);
  const button = page.locator(".recipe-tab-btn").filter({ hasText: tab });
  await expect(button).toBeVisible();
  // The gallery mounts asynchronously and may reset the selection once while it
  // resolves, so retry until the tab reports itself as pressed.
  await expect(async () => {
    await button.click();
    await expect(button).toHaveAttribute("aria-pressed", "true", { timeout: 1000 });
  }).toPass({ timeout: 15000 });
}

test.describe("authoring recipe", () => {
  test("mode buttons expose accessible labels and toggle", async ({ page }) => {
    await openRecipe(page, "Authoring Workbench");

    const rendered = page.locator('[aria-label="Rendered"]');
    const source = page.locator('[aria-label="Markdown Source"]');
    await expect(rendered).toBeVisible();
    await expect(source).toBeVisible();

    await source.click();
    await expect(page.locator(".markdown-textarea")).toBeVisible();

    await rendered.click();
    await expect(page.locator(".prose-content")).toBeVisible();
  });

  test("keyboard focus is visible on the mode control", async ({ page }) => {
    await openRecipe(page, "Authoring Workbench");
    const rendered = page.locator('[aria-label="Rendered"]');
    await expect(rendered).toBeVisible();

    let reached = false;
    for (let press = 0; press < 80 && !reached; press += 1) {
      await page.keyboard.press("Tab");
      reached = await page.evaluate(
        () => document.activeElement?.getAttribute("aria-label") === "Rendered",
      );
    }
    expect(reached).toBe(true);

    // .usx-btn transitions `all`, so the ring settles over ~150ms; poll rather
    // than sampling the in-flight value.
    await expect
      .poll(
        () => rendered.evaluate((element) => parseFloat(getComputedStyle(element).outlineWidth)),
        { timeout: 2000 },
      )
      .toBeGreaterThan(0);

    const ring = await rendered.evaluate((element) => {
      const style = getComputedStyle(element);
      return { style: style.outlineStyle, color: style.outlineColor };
    });
    expect(ring.style).toBe("solid");
    expect(ring.color).not.toBe("rgba(0, 0, 0, 0)");
  });

  test("reflows at 390px without horizontal overflow", async ({ page }) => {
    await page.setViewportSize(NARROW);
    await openRecipe(page, "Authoring Workbench");
    await expect(page.locator(".prose-content")).toBeVisible();
    expect(await noHorizontalOverflow(page)).toBe(true);
  });
});

test.describe("settings form recipe", () => {
  test("renders labelled fields and reports a required-field error", async ({ page }) => {
    await openRecipe(page, "Settings Form");
    const form = page.locator("form.settings-preview");
    await expect(form).toBeVisible();

    expect(await form.locator("input, select").count()).toBeGreaterThan(0);

    const labelled = await form.evaluate((element) => {
      const fields = [...element.querySelectorAll("input, select")];
      return fields.every((field) => {
        const id = field.getAttribute("id");
        return !id || Boolean(element.querySelector(`label[for="${id}"]`));
      });
    });
    expect(labelled).toBe(true);

    const required = form.locator("[required]");
    if ((await required.count()) > 0) {
      await form.locator('button[type="submit"]').click();
      await expect(form.locator('[role="status"]')).not.toBeEmpty();
    }
  });
});

test.describe("recipe gallery", () => {
  test("preview controls are labelled and switch the theme", async ({ page }) => {
    await page.goto(GALLERY);
    const stage = page.locator(".gallery-stage");
    await expect(stage).toBeVisible();

    const controls = page.locator(".gallery-controls button");
    expect(await controls.count()).toBeGreaterThan(0);
    const unlabelled = await controls.evaluateAll(
      (nodes) => nodes.filter((node) => !node.getAttribute("aria-label")).length,
    );
    expect(unlabelled).toBe(0);

    const theme = page.locator('.gallery-controls button[aria-label^="Switch"]');
    if ((await theme.count()) > 0) {
      const before = await stage.getAttribute("data-preview-theme");
      await theme.first().click();
      expect(await stage.getAttribute("data-preview-theme")).not.toBe(before);
    }

    expect(await noHorizontalOverflow(page)).toBe(true);
  });

  test("stage reflows at 390px", async ({ page }) => {
    await page.setViewportSize(NARROW);
    await page.goto(GALLERY);
    await expect(page.locator(".gallery-stage")).toBeVisible();
    expect(await noHorizontalOverflow(page)).toBe(true);
  });
});

test.describe("workflow tasks", () => {
  test("task lanes render and the view control is keyboard reachable", async ({ page }) => {
    await openRecipe(page, "Task List");
    expect(await page.locator(".lane").count()).toBeGreaterThan(0);
    expect(await page.locator(".task-card").count()).toBeGreaterThan(0);

    // The rows/board toggle is the interactive control in this preview.
    const rows = page.getByRole("button", { name: /rows/i }).first();
    await rows.focus();
    expect(await rows.evaluate((element) => element === document.activeElement)).toBe(true);
    await rows.click();
    expect(await page.locator(".lanes--rows").count()).toBe(1);

    await page.setViewportSize(NARROW);
    expect(await noHorizontalOverflow(page)).toBe(true);
  });
});

test.describe("ten-foot display profile", () => {
  const expectations = [
    { width: 1280, height: 720, font: 18 },
    { width: 1920, height: 1080, font: 18 },
    { width: 2560, height: 1440, font: 24 },
    { width: 3840, height: 2160, font: 36 },
  ];

  for (const target of expectations) {
    test(`root scale is ${target.font}px at ${target.width}x${target.height}`, async ({ page }) => {
      await page.setViewportSize({ width: target.width, height: target.height });
      await page.goto("/");
      await page.evaluate(() => document.documentElement.setAttribute("data-display", "ten-foot"));

      const measured = await page.evaluate(() => ({
        font: parseFloat(getComputedStyle(document.documentElement).fontSize),
        touch: getComputedStyle(document.documentElement).getPropertyValue("--usx-touch-min").trim(),
      }));

      expect(Math.round(measured.font)).toBe(target.font);
      expect(measured.touch).toBe("64px");
    });
  }
});

test.describe("surface tab strip", () => {
  test("reveals the selected tab and keeps every tab reachable at 390px", async ({ page }) => {
    await page.setViewportSize(NARROW);
    await page.goto("/engineering?section=grid-recipes");

    const strip = page.locator(".surface-tab-nav__scroll");
    await expect(strip).toBeVisible();

    const active = page.locator(".surface-tab-nav__link--active");
    await expect(active).toHaveAttribute("aria-current", "page");
    await expect(active).toContainText("Grid Recipes");

    // The selected tab must sit inside the strip rather than clipped at the edge.
    await expect(async () => {
      const visible = await active.evaluate((link) => {
        const scroller = link.closest(".surface-tab-nav__scroll");
        if (!scroller) return false;
        const linkBox = link.getBoundingClientRect();
        const stripBox = scroller.getBoundingClientRect();
        return linkBox.left >= stripBox.left - 1 && linkBox.right <= stripBox.right + 1;
      });
      expect(visible).toBe(true);
    }).toPass({ timeout: 5000 });

    // Arrow keys walk the strip and the focused tab follows into view.
    const links = page.locator(".surface-tab-nav__link");
    await links.first().focus();
    await page.keyboard.press("End");
    await expect(links.last()).toBeFocused();
    await page.keyboard.press("Home");
    await expect(links.first()).toBeFocused();

    // Pinned actions stay outside the scroller, and the page never scrolls sideways.
    expect(await page.locator(".surface-tab-nav__scroll .surface-tab-nav__actions").count()).toBe(0);
    expect(await noHorizontalOverflow(page)).toBe(true);
  });
});
