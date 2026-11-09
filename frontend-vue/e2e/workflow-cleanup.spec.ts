import { expect, test } from '@playwright/test';

// Intercept every API request: never populate the user's live workspace.
for (const width of [1280, 390]) {
  test(`shared Binder navigation and Editor at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    const task = { id: 'fixture-task', title: 'Plan planting', board: 'apple-family', binder: 'garden', status: 'todo', priority: 'medium', tags: [], body: 'Keep source links', source: 'user' };
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      if (!path.startsWith('/api/')) { await route.continue(); return; }
      let data: unknown = {};
      if (path === '/api/binder/list') data = { binders: [{ id: 'garden', title: 'Garden' }] };
      else if (path === '/api/workflow/tasks') data = { tasks: [task] };
      else if (path === '/api/workflow/lists') data = { boards: [{ name: 'apple-family', count: 1 }] };
      else if (path === '/api/workflows') data = { workflows: [] };
      else if (path.endsWith('/runs')) data = { runs: [] };
      else if (path === '/api/connections') data = { setup: { completed: true }, connections: [], collections: {} };
      else if (path.includes('/settings')) data = { settings: {} };
      else if (path.includes('/capabilities')) data = { ready: true, repair: [] };
      else if (path.includes('/tree')) data = { tree: [] };
      else if (path.includes('/search')) data = { results: [] };
      else if (path.includes('/workspaces')) data = { workspaces: [] };
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    await page.goto('/workflow?tab=tasks&binder=garden');
    await expect(page.getByRole('heading', { name: 'Tasks', exact: true })).toBeVisible({ timeout: 20000 });
    const finder = page.getByTitle('Finder', { exact: true });
    await finder.focus();
    await page.keyboard.press('Enter');
    const sidebar = page.locator('.app-sidebar');
    await expect(sidebar).toBeVisible();
    await sidebar.locator('.sidebar-mode button').filter({ hasText: 'Binders' }).click();
    await expect(sidebar.getByRole('button', { name: /Plan planting/ })).toBeVisible();
    await sidebar.getByRole('button', { name: /Plan planting/ }).focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/tab=editor/);
    await expect(page.locator('.app-sidebar')).toHaveCount(1);
    await expect(page.locator('.workflow-workspace-tree')).toHaveCount(0);
    await finder.click();
    await expect(sidebar).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
  });
}
