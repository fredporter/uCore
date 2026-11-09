/** Compatibility links: gallery layouts now belong to working product surfaces. */
export function recipeDestination(recipe: string): string {
  const destinations: Record<string, string> = {
    'task-list': '/workflow?tab=tasks',
    'authoring-workbench': '/workflow?tab=editor',
    'prose-document': '/documentation?tab=wiki',
    'card-matrix': '/',
    'settings-form': '/system?tab=preferences',
    'story-form': '/setup',
    'system-page': '/server',
    'alerts-suite': '/workflow?tab=queue',
    'teletext-mode7': '/ucode?tab=teletext',
    'terminal-ansi': '/ucode?tab=terminal',
  };
  return destinations[recipe] || '/';
}
