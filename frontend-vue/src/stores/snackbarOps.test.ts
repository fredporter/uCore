// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useSnackbarOpsStore } from './snackbarOps';

beforeEach(() => {
  setActivePinia(createPinia());
  vi.spyOn(document, 'hidden', 'get').mockReturnValue(false);
});
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

it('does not overlap health requests and resumes after completion', async () => {
  let finish!: (value: Response) => void;
  const request = vi.fn(() => new Promise<Response>(resolve => { finish = resolve; }));
  vi.stubGlobal('fetch', request);
  const store = useSnackbarOpsStore();
  const first = store.pollHealthWithAlerts();
  await store.pollHealthWithAlerts();
  expect(request).toHaveBeenCalledTimes(1);
  finish(new Response(JSON.stringify({ services: [], up: 0, degraded: 0, down: 0, health_pct: 100 })));
  await first;
  const next = store.pollHealthWithAlerts();
  expect(request).toHaveBeenCalledTimes(2);
  finish(new Response('', { status: 503 }));
  await next;
});

it('does not poll an inactive tab', async () => {
  vi.spyOn(document, 'hidden', 'get').mockReturnValue(true);
  const request = vi.fn();
  vi.stubGlobal('fetch', request);
  await useSnackbarOpsStore().pollHealthWithAlerts();
  expect(request).not.toHaveBeenCalled();
});
