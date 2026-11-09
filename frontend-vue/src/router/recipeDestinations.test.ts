import { expect, it } from 'vitest';
import { recipeDestination } from './recipeDestinations';
it('routes former gallery layouts into working surfaces, never sample state', () => {
  expect(recipeDestination('terminal-ansi')).toBe('/ucode?tab=terminal');
  expect(recipeDestination('task-list')).toBe('/workflow?tab=tasks');
  expect(recipeDestination('story-form')).toBe('/setup');
  expect(recipeDestination('authoring-workbench')).toBe('/workflow?tab=editor');
  expect(recipeDestination('unknown')).toBe('/');
});
