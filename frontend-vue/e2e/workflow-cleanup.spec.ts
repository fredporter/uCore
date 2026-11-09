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

test('objective leads a task into Queue and survives reload at narrow width', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const missions: any[] = [], tasks: any[] = [];
  await page.route('**/api/**', async route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (!path.startsWith('/api/')) return route.continue();
    let data: unknown = {};
    if (path === '/api/workflow/missions') {
      if (request.method() === 'POST') {
        const mission = { id: 'mission-fixture', title: request.postDataJSON().title, status: 'active', binder: '' };
        missions.push(mission); data = { mission };
      } else data = { missions };
    } else if (path === '/api/workflow/tasks') {
      if (request.method() === 'POST') {
        const task = { ...request.postDataJSON(), id: 'task-fixture', status: 'todo', priority: 'medium', tags: [], source: 'user' };
        tasks.push(task); data = { updated: task };
      } else data = { tasks };
    } else if (path === '/api/binder/list') data = { binders: [] };
    else if (path === '/api/workflows') data = { workflows: [] };
    else if (path.endsWith('/runs')) data = { runs: [] };
    else if (path.includes('/capabilities')) data = { ready: true, repair: [] };
    else if (path === '/api/connections') data = { setup: { completed: true }, connections: [], collections: {} };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
  });
  await page.goto('/workflow?tab=mission-control');
  await page.getByLabel('Your objective').fill('Plan a garden');
  await page.getByRole('button', { name: /Set mission/ }).click();
  await expect(page.getByRole('heading', { name: 'Plan a garden', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Plan a garden', exact: true })).toBeVisible();
  await page.getByRole('button', { name: /Tasks/ }).click();
  page.once('dialog', dialog => dialog.accept('Choose seeds'));
  await page.getByRole('button', { name: /New Task/ }).click();
  await expect(page).toHaveURL(/tab=editor/);
  expect(tasks[0].mission).toBe('mission-fixture');
  await page.locator('.surface-tab-nav__link').filter({ hasText: 'Queue' }).click();
  await expect(page.getByRole('region', { name: 'Mission task queue' })).toContainText('Choose seeds');
  expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
});
