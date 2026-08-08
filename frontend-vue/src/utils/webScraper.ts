/**
 * @module utils/webScraper
 * @description Create research documents from web URLs with auto-populated frontmatter.
 */
import { SNACKBAR_BASE } from "../api/base";

export interface ScrapedContent {
  title: string;
  description: string;
  url: string;
  html?: string;
  text?: string;
}

export interface ResearchDocument {
  filename: string;
  content: string; // full markdown with frontmatter
}

/** Convert a URL hostname into a readable source name */
function sourceLabel(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

/** Slugify a title into a safe filename */
function toFilename(title: string): string {
  return (
    title
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-")
      .slice(0, 60) + ".md"
  );
}

/** Attempt to fetch and extract article content via backend scraper */
export async function fetchScrape(url: string): Promise<ScrapedContent | null> {
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/editor/scrape-web`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
      signal: AbortSignal.timeout(8000),
    });
    if (res.ok) return await res.json();
  } catch {
    // Backend scraper unavailable — fall back to card metadata
  }
  return null;
}

/** Build a research document markdown string from card metadata (no scrape needed) */
export function buildResearchDocument(
  card: { title: string; description: string; url: string; tags?: string[] },
  scraped?: ScrapedContent | null,
): ResearchDocument {
  const title = scraped?.title || card.title;
  const description = scraped?.description || card.description;
  const tags = card.tags ?? [];
  const today = new Date().toISOString().slice(0, 10);
  const source = sourceLabel(card.url);

  const frontmatter = [
    `---`,
    `title: "${title.replace(/"/g, '\\"')}"`,
    `source: "${card.url}"`,
    `site: "${source}"`,
    `date: "${today}"`,
    `type: research`,
    `status: draft`,
    tags.length ? `tags: [${tags.join(", ")}]` : null,
    `---`,
  ]
    .filter(Boolean)
    .join("\n");

  const body = scraped?.text
    ? `# ${title}\n\n> Source: [${source}](${card.url})\n\n${scraped.text}`
    : `# ${title}\n\n> Source: [${source}](${card.url})\n\n${description}\n\n---\n\n_Open original for full content._`;

  return {
    filename: toFilename(title),
    content: `${frontmatter}\n\n${body}`,
  };
}
