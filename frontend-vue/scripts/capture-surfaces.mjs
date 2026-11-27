// Visual-review captures for named surfaces. Writes images only; asserts nothing.
//
// Safari preference: `--engine webkit` uses Playwright's WebKit build, which is
// Safari's rendering engine, not Safari itself. Font smoothing, overlay
// scrollbars, backdrop-filter, form controls and installed-PWA behaviour still
// need a pass in Safari by hand. Treat these captures as an engine-accurate
// proxy, not as proof of Safari rendering.
//
// Requires a running dev server and backend (see DEV_ENGINEERING.md):
//   cd ~/Code/uCore && pnpm dev:backend          # :8484
//   cd ~/Code/uCore/frontend-vue && pnpm dev     # :5175
//
// Usage:
//   node scripts/capture-surfaces.mjs
//   node scripts/capture-surfaces.mjs --engine chromium
//   node scripts/capture-surfaces.mjs --only engineering,documentation
//   node scripts/capture-surfaces.mjs --base http://localhost:5176 --full-page
import { chromium, webkit } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

const ENGINE_BROWSERS = { chromium, webkit };
const ENGINE_HINTS = {
  chromium: 'pnpm exec playwright install chromium',
  webkit: 'pnpm exec playwright install webkit',
};

// /recovery is intentionally absent: RecoverySurface is the not-found component,
// not a route.
const ROUTES = [
  { name: 'dashboard', path: '/' },
  { name: 'engineering', path: '/engineering' },
  { name: 'documentation', path: '/documentation' },
  { name: 'workflow', path: '/workflow' },
  { name: 'snackbar', path: '/snackbar' },
  { name: 'system', path: '/system' },
];

// The narrow viewport matches the e2e NARROW constant (390x844).
const VIEWPORTS = [
  { label: 'desktop', width: 1280, height: 800 },
  { label: 'narrow', width: 390, height: 844 },
];

const root = path.resolve(import.meta.dirname, '..');

function parseArgs(argv) {
  const options = { engine: 'webkit', base: process.env.UCORE_BASE_URL || 'http://localhost:5175', only: null, fullPage: false };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === '--engine') {
      if (!(value in ENGINE_BROWSERS)) throw new Error(`--engine must be one of ${Object.keys(ENGINE_BROWSERS).join(', ')}`);
      options.engine = value;
      index += 1;
    } else if (flag === '--base') {
      if (!value) throw new Error('--base requires a URL');
      options.base = value;
      index += 1;
    } else if (flag === '--only') {
      options.only = new Set(String(value || '').split(',').map(name => name.trim()).filter(Boolean));
      index += 1;
    } else if (flag === '--full-page') {
      options.fullPage = true;
    } else {
      throw new Error(`Unknown argument: ${flag}`);
    }
  }
  return options;
}

function today() {
  const now = new Date();
  const pad = value => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

async function checkServer(base) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(base, { signal: controller.signal });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

let options;
try {
  options = parseArgs(process.argv.slice(2));
} catch (error) {
  console.error(JSON.stringify({ error: error.message, engines: Object.keys(ENGINE_BROWSERS), routes: ROUTES.map(route => route.name) }));
  process.exit(2);
}
const routes = ROUTES.filter(route => !options.only || options.only.has(route.name));
if (!routes.length) {
  console.error(JSON.stringify({ error: 'no routes matched --only', known: ROUTES.map(route => route.name) }));
  process.exit(2);
}

if (!(await checkServer(options.base))) {
  console.error(JSON.stringify({
    error: `dev server unreachable at ${options.base}`,
    hint: 'Start it first: cd ~/Code/uCore/frontend-vue && pnpm dev (override the port with VITE_PORT)',
  }));
  process.exit(2);
}

const output = path.join(root, 'test-results', 'visual', today());
mkdirSync(output, { recursive: true });

const files = [];
const failed = [];
let browser;
try {
  browser = await ENGINE_BROWSERS[options.engine].launch();
} catch (error) {
  console.error(JSON.stringify({
    error: `cannot launch ${options.engine}: ${error.message.split('\n')[0]}`,
    hint: `Install the browser: ${ENGINE_HINTS[options.engine]}`,
  }));
  process.exit(2);
}

for (const viewport of VIEWPORTS) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  for (const route of routes) {
    const file = path.join(output, `${route.name}-${viewport.label}-${options.engine}.png`);
    try {
      await page.goto(`${options.base}${route.path}`, { waitUntil: 'networkidle', timeout: 20000 });
      // Settle late async mounts and transition end states before capturing.
      await page.waitForTimeout(250);
      await page.screenshot({ path: file, fullPage: options.fullPage });
      files.push(path.relative(root, file));
    } catch (error) {
      failed.push({ route: route.name, viewport: viewport.label, error: error.message.split('\n')[0] });
    }
  }
  await context.close();
}
await browser.close();

console.log(JSON.stringify({
  engine: options.engine,
  base: options.base,
  viewports: VIEWPORTS.map(viewport => `${viewport.width}x${viewport.height}`),
  captured: files.length,
  failed: failed.length,
  output: path.relative(root, output),
  files,
  failures: failed,
}, null, 2));
process.exitCode = failed.length ? 1 : 0;
