import { fetchScrape } from "./webScraper";

export type CitationFormat = "APA" | "MLA" | "Chicago";
export type PublicationType = "article" | "blog" | "documentation" | "video" | "webpage";

export interface CitationMetadata {
  url: string;
  title?: string;
  author?: string;
  site?: string;
  published?: string;
  accessed?: string;
  type?: PublicationType;
}

export function detectPublicationType(url: string): PublicationType {
  const value = url.toLowerCase();
  if (/youtube\.com|youtu\.be|vimeo\.com/.test(value)) return "video";
  if (/\/docs?\/|developer\.|readthedocs|docs\./.test(value)) return "documentation";
  if (/\/blog\/|medium\.com|substack\.com/.test(value)) return "blog";
  if (/\/articles?\/|\/news\//.test(value)) return "article";
  return "webpage";
}

function host(url: string): string {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return url; }
}

function dateLabel(value?: string): string {
  if (!value) return "n.d.";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleDateString("en", { year: "numeric", month: "long", day: "numeric" });
}

export function citationGenerator(metadata: CitationMetadata, format: CitationFormat): string {
  const author = metadata.author?.trim() || metadata.site?.trim() || host(metadata.url);
  const title = metadata.title?.trim() || "Untitled web page";
  const site = metadata.site?.trim() || host(metadata.url);
  const published = dateLabel(metadata.published);
  const accessed = dateLabel(metadata.accessed || new Date().toISOString());
  if (format === "APA") return `${author}. (${published === "n.d." ? "n.d." : published}). ${title}. ${site}. ${metadata.url}`;
  if (format === "MLA") return `${author}. “${title}.” ${site}, ${published}, ${metadata.url}. Accessed ${accessed}.`;
  return `${author}. “${title}.” ${site}. ${published}. ${metadata.url}.`;
}

export async function generateCitation(metadata: CitationMetadata, format: CitationFormat): Promise<string> {
  const scraped = await fetchScrape(metadata.url);
  return citationGenerator({
    ...metadata,
    title: metadata.title || scraped?.title,
    site: metadata.site || host(metadata.url),
    type: metadata.type || detectPublicationType(metadata.url),
  }, format);
}
