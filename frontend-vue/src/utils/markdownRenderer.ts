/**
 * @module utils/markdownRenderer
 * @description Format-aware markdown → HTML renderer with native SVG, diagram,
 * and math capabilities. Supports Prose, Story (Marp), Mermaid, Declarative Charts,
 * GridCore/Teletext mosaics, and KaTeX math.
 */
import { Marked, type TokenizerExtension, type RendererExtension } from "marked";
import DOMPurify from "dompurify";
import katex from "katex";
import { parseDocument } from "./frontmatterParser";
import { renderSvgChart } from "./svgChartRenderer";

export type MarkdownFormat = "prose" | "story" | "game" | "publish" | "print";

export interface RenderResult {
  html: string;
  format: MarkdownFormat;
  frontmatter: Record<string, unknown>;
  slideCount?: number; // story format only
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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

// ─── Math Extensions (KaTeX) ─────────────────────────────────────────

const inlineMathExtension: TokenizerExtension & RendererExtension = {
  name: "inlineMath",
  level: "inline",
  start(src: string) {
    return src.indexOf("$");
  },
  tokenizer(src: string) {
    const match = src.match(/^\$([^\$\n]+?)\$/);
    if (match) {
      const content = match[1].trim();
      // Guard against currency numbers like $100 or $5.99
      if (/^\d+(\.\d+)?$/.test(content)) return;
      return {
        type: "inlineMath",
        raw: match[0],
        text: content,
      };
    }
  },
  renderer(token: { text?: string; raw?: string }) {
    if (!token.text) return token.raw || "";
    try {
      return katex.renderToString(token.text, {
        displayMode: false,
        throwOnError: false,
      });
    } catch {
      return `<code>${escapeHtml(token.raw || "")}</code>`;
    }
  },
};

const blockMathExtension: TokenizerExtension & RendererExtension = {
  name: "blockMath",
  level: "block",
  start(src: string) {
    return src.indexOf("$$");
  },
  tokenizer(src: string) {
    const match = src.match(/^\$\$([\s\S]+?)\$\$/);
    if (match) {
      return {
        type: "blockMath",
        raw: match[0],
        text: match[1].trim(),
      };
    }
  },
  renderer(token: { text?: string; raw?: string }) {
    if (!token.text) return token.raw || "";
    try {
      return katex.renderToString(token.text, {
        displayMode: true,
        throwOnError: false,
      });
    } catch {
      return `<pre class="katex-error"><code>${escapeHtml(token.raw || "")}</code></pre>`;
    }
  },
};

// ─── Prose renderer ──────────────────────────────────────────────────

const marked = new Marked({
  gfm: true,
  breaks: false,
});

marked.use({
  extensions: [blockMathExtension, inlineMathExtension],
  renderer: {
    code({ text, lang }: { text: string; lang?: string }) {
      const language = (lang || "").trim().toLowerCase();

      if (language === "mermaid") {
        return `<div class="md-diagram md-diagram--mermaid" data-diagram="mermaid"><pre class="mermaid">${escapeHtml(text)}</pre></div>\n`;
      }

      if (language === "chart") {
        const svg = renderSvgChart(text);
        return `<div class="md-diagram md-diagram--chart" data-diagram="chart" data-chart-raw="${encodeURIComponent(text)}">${svg}</div>\n`;
      }

      if (language === "teletext" || language === "gridcore") {
        return `<div class="md-diagram md-diagram--teletext" data-diagram="teletext"><pre class="teletext-screen"><code>${escapeHtml(text)}</code></pre></div>\n`;
      }

      if (language === "vector") {
        return `<div class="md-diagram md-diagram--vector" data-diagram="vector" data-vector-spec="${encodeURIComponent(text)}"><pre class="vector-spec"><code>${escapeHtml(text)}</code></pre></div>\n`;
      }

      if (language === "math" || language === "latex" || language === "katex") {
        try {
          return katex.renderToString(text.trim(), {
            displayMode: true,
            throwOnError: false,
          });
        } catch {
          return `<pre class="katex-error"><code>${escapeHtml(text)}</code></pre>\n`;
        }
      }

      return false; // Fall back to default code block renderer
    },
  },
});

/** Transform > [!NOTE] / [!WARNING] / [!TIP] / [!CAUTION] callout syntax */
function applyCallouts(html: string): string {
  return html.replace(
    /<blockquote>\s*<p>\[!(NOTE|TIP|WARNING|CAUTION|IMPORTANT)\]\s*([\s\S]*?)<\/p>([\s\S]*?)<\/blockquote>/gi,
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

export function sanitize(html: string): string {
  if (typeof window === "undefined") return html; // SSR guard
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true, svg: true, svgFilters: true, mathMl: true },
    ADD_TAGS: [
      "use",
      "math",
      "semantics",
      "mrow",
      "mi",
      "mo",
      "mn",
      "msup",
      "msub",
      "mfrac",
      "mtext",
      "mspace",
      "annotation",
      "foreignObject",
      "defs",
      "linearGradient",
      "stop",
      "animate",
    ],
    ADD_ATTR: [
      "class",
      "role",
      "data-slide",
      "data-diagram",
      "data-chart-raw",
      "data-vector-spec",
      "href",
      "src",
      "alt",
      "title",
      "viewBox",
      "xmlns",
      "d",
      "fill",
      "stroke",
      "stroke-width",
      "stroke-linecap",
      "stroke-linejoin",
      "stroke-dasharray",
      "transform",
      "cx",
      "cy",
      "r",
      "rx",
      "ry",
      "x",
      "y",
      "x1",
      "y1",
      "x2",
      "y2",
      "width",
      "height",
      "points",
      "font-family",
      "font-size",
      "font-weight",
      "text-anchor",
      "opacity",
      "preserveAspectRatio",
      "aria-label",
      "tabindex",
      "target",
      "marker-end",
      "marker-start",
      "attributeName",
      "from",
      "to",
      "dur",
    ],
  });
}
