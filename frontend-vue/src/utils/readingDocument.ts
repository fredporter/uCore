import { parseDocument, parseYaml, type Frontmatter } from './frontmatterParser';

/** Read-only presentation of frontmatter; the original Markdown is never changed. */
export function parseReadingDocument(markdown: string) {
  const normalized = markdown.replace(/^\uFEFF/, '');
  const document = parseDocument(normalized);
  if (document.hasFrontmatter) {
    const header = normalized.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)?.[1] || '';
    let listKey = '';
    for (const line of header.split(/\r?\n/)) {
      const field = line.match(/^([\w-]+):\s*$/);
      if (field) { listKey = field[1]; continue; }
      const item = line.match(/^\s+-\s+(.+)$/);
      if (item && listKey) {
        const values = document.frontmatter[listKey];
        document.frontmatter[listKey] = [...(Array.isArray(values) ? values : []), parseYaml(`value: ${item[1]}`).value];
      } else if (line.trim() && !line.trim().startsWith('#')) listKey = '';
    }
  }
  return document;
}
export function readingProperties(frontmatter: Frontmatter) {
  return Object.entries(frontmatter).flatMap(([key, value]) => (Array.isArray(value) ? value : [value])
    .filter(item => item !== '' && item !== null && item !== undefined)
    .map(item => ({ key, value: typeof item === 'object' ? JSON.stringify(item) : String(item) })));
}

export function containReaderKeys(event: KeyboardEvent, root: HTMLElement | null, fullscreen: boolean, exit: () => void) {
  if (!fullscreen || !root) return;
  if (event.key === 'Escape') { event.preventDefault(); exit(); return; }
  if (event.key !== 'Tab') return;
  const controls = [...root.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input, select, textarea, [tabindex="0"]')].filter(element => element.getClientRects().length);
  const first = controls[0], last = controls.at(-1);
  if (first && (event.shiftKey ? document.activeElement === first : document.activeElement === last)) {
    event.preventDefault(); (event.shiftKey ? last : first)?.focus();
  }
}
