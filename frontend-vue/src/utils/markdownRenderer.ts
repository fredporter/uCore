/**
 * @module utils/markdownRenderer
 * @description Format-aware markdown → HTML renderer.
 * Detects format from frontmatter or file extension and routes to the right engine.
 */
import { Marked } from "marked";
import DOMPurify from "dompurify";
import { parseDocument } from "./frontmatterParser";

export type MarkdownFormat = "prose" | "story" | "game" | "publish" | "print";

export interface RenderResult {
  html: string;
  format: MarkdownFormat;
  frontmatter: Record<string, unknown>;
  slideCount?: number; // story format only
}

// ─── Format detection ────────────────────────────────────────────────

const EXT_FORMAT: Record<string, MarkdownFormat> = {
  "slide.md": "story",
  "story.md": "story",
  "game.md": "game",
  "publish.md": "publish",
  "print.md": "print",
};

export function detectFormat(
  frontmatter: Record<string, unknown>,
  filename?: string,
): MarkdownFormat {
  if (frontmatter.format) return frontmatter.format as MarkdownFormat;
  if (filename) {
    for (const [ext, fmt] of Object.entries(EXT_FORMAT)) {
      if (filename.endsWith(ext)) return fmt;
    }
  }
  return "prose";
}

// ─── Prose renderer ──────────────────────────────────────────────────

const marked = new Marked({
  gfm: true,
  breaks: false,
});

/** Transform > [!NOTE] / [!WARNING] / [!TIP] / [!CAUTION] callout syntax */
function applyCallouts(html: string): string {
  return html.replace(
    /<blockquote>\s*<p>\[!(NOTE|TIP|WARNING|CAUTION|IMPORTANT)\](.*?)<\/p>([\s\S]*?)<\/blockquote>/gi,
    (_, type, rest, body) => {
      const t = type.toLowerCase();
      const iconMap: Record<string, string> = {
        note: "info",
        tip: "lightbulb",
        warning: "warning",
        caution: "error",
        important: "priority_high",
      };
      const icon = iconMap[t] ?? "info";
      return `<div class="md-callout md-callout--${t}" role="note">
  <div class="md-callout__label">
    <span class="material-symbols-outlined">${icon}</span>
    <strong>${type}</strong>
  </div>
  <div class="md-callout__body">${rest}${body}</div>
</div>`;
    },
  );
}

function renderProse(body: string): string {
  const raw = marked.parse(body) as string;
  return applyCallouts(raw);
}

// ─── Story renderer (Marp) ───────────────────────────────────────────

let marpInstance: any = null;

async function getMarp() {
  if (marpInstance) return marpInstance;
  try {
    const { Marp } = await import("@marp-team/marp-core");
    marpInstance = new Marp({ html: false });
    return marpInstance;
  } catch {
    return null;
  }
}

export async function renderStory(
  markdown: string,
): Promise<{ html: string; slideCount: number }> {
  const marp = await getMarp();
  if (!marp) {
    // Graceful fallback: treat each --- as a slide div
    const slides = markdown.split(/^---$/m).filter(Boolean);
    const html = slides
      .map(
        (s, i) =>
          `<section class="marp-slide" data-slide="${i + 1}">${renderProse(s)}</section>`,
      )
      .join("\n");
    return { html, slideCount: slides.length };
  }
  const { html } = marp.render(markdown);
  const slides = (html.match(/<section/g) ?? []).length;
  return { html, slideCount: Math.max(1, slides) };
}

// ─── Public API ──────────────────────────────────────────────────────

/** Render markdown to HTML, auto-detecting format from frontmatter/filename */
export async function renderDocument(
  markdown: string,
  filename?: string,
): Promise<RenderResult> {
  const { frontmatter, body } = parseDocument(markdown);
  const format = detectFormat(frontmatter, filename);

  if (format === "story" || format === "print") {
    const { html, slideCount } = await renderStory(markdown);
    return { html: sanitize(html), format, frontmatter, slideCount };
  }

  const rawHtml = renderProse(body);
  return { html: sanitize(rawHtml), format, frontmatter };
}

/** Synchronous prose-only render (for inline previews where async isn't needed) */
export function renderProseFast(markdown: string): string {
  const { body } = parseDocument(markdown);
  return sanitize(renderProse(body));
}

function sanitize(html: string): string {
  if (typeof window === "undefined") return html; // SSR guard
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    // Allow class/style on known callout/slide elements
    ALLOWED_ATTR: [
      "class",
      "role",
      "data-slide",
      "href",
      "src",
      "alt",
      "title",
    ],
  });
}
